"""
OpenAI-Compatible API Wrapper for KRAI
=======================================
Exposes ``/v1/chat/completions`` and ``/v1/models`` so that OpenWebUI
(or any OpenAI client) can talk to the KRAI agent without modification.

Fast-Path (no LLM needed):
  Exact error-code patterns (e.g. 99.00.02, C-2801, SC542) are detected in
  the user message and resolved directly via a SQL query — response in < 50 ms.
  Only open-ended / conversational messages go through the LangGraph agent.

Supported backends (env LLM_BACKEND):
  ollama  — local Ollama (default, model via OLLAMA_MODEL_CHAT)
  openai  — OpenAI API  (model via OPENAI_MODEL, key via OPENAI_API_KEY)

Vision / Image Analysis
  When the request contains image_url content parts the images are forwarded
  directly to the LLM (llava on Ollama, gpt-4o on OpenAI).  The KRAI agent
  then uses its tools to enrich the response with DB lookups.

Session Management
  OpenWebUI sends the full message history on every request.  We derive a
  stable session_id from the content of the first user message so that
  LangGraph's MemorySaver maintains continuity across turns.
  Callers may also pass a custom session id via the ``user`` field.
"""

import asyncio
import hashlib
import httpx
import json
import logging
import os
import re
import time
import uuid
from urllib.parse import urlparse
from typing import AsyncGenerator, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.middleware.auth_middleware import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["OpenAI Compatible"])

# Public base URL for MinIO image bucket — used to rewrite internal storage URLs.
# Set OBJECT_STORAGE_PUBLIC_URL_IMAGES in .env, e.g.:
#   http://localhost:9000/images          (local)
#   https://minio.example.com/images     (production)
# Falls back to OBJECT_STORAGE_PUBLIC_URL (without bucket path) if not set.
_MINIO_IMAGES_PUBLIC = (
    os.getenv('OBJECT_STORAGE_PUBLIC_URL_IMAGES') or
    os.getenv('OBJECT_STORAGE_PUBLIC_URL', '')
).rstrip('/')


def _rewrite_storage_url(url: str) -> str:
    """Replace the internal MinIO host:port with the configured public URL.

    This lets the same DB data work locally (127.0.0.1:9000) and in
    production (https://minio.example.com) without re-processing images.
    The path portion (/images/<hash>) is always preserved.
    """
    if not _MINIO_IMAGES_PUBLIC or not url:
        return url
    parsed = urlparse(url)
    internal_origin = f"{parsed.scheme}://{parsed.netloc}"
    public_origin = urlparse(_MINIO_IMAGES_PUBLIC).scheme + "://" + urlparse(_MINIO_IMAGES_PUBLIC).netloc
    return url.replace(internal_origin, public_origin, 1)


# ---------------------------------------------------------------------------
# Pydantic models (OpenAI request/response format)
# ---------------------------------------------------------------------------

class ImageUrl(BaseModel):
    url: str  # "data:image/jpeg;base64,..." or https URL


class ContentPart(BaseModel):
    type: str                          # "text" | "image_url"
    text: Optional[str] = None
    image_url: Optional[ImageUrl] = None


class OAIMessage(BaseModel):
    role: str                                        # system | user | assistant
    content: Union[str, list[ContentPart]]


class ChatCompletionRequest(BaseModel):
    model: str = "krai"
    messages: list[OAIMessage]
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    user: Optional[str] = None          # treated as session_id hint when set


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _session_id(messages: list[OAIMessage], user: Optional[str]) -> str:
    """Return a stable session identifier for this conversation thread.

    Priority: explicit ``user`` field → hash of first user message content.
    """
    if user:
        return user[:64]
    for msg in messages:
        if msg.role == "user":
            text = msg.content if isinstance(msg.content, str) else json.dumps(
                [p.model_dump() for p in msg.content]  # type: ignore[union-attr]
            )
            return "oai_" + hashlib.sha256(text.encode()).hexdigest()[:32]
    return "oai_" + uuid.uuid4().hex


def _extract_last_user_content(
    messages: list[OAIMessage],
) -> tuple[Union[str, list], list[str]]:
    """Extract text and image URLs from the last user message.

    Returns ``(content, image_urls)`` where *content* is either a plain
    string or a list of OpenAI-style content dicts when images are present.
    """
    for msg in reversed(messages):
        if msg.role != "user":
            continue
        if isinstance(msg.content, str):
            return msg.content, []
        text_parts: list[str] = []
        image_urls: list[str] = []
        for part in msg.content:
            if part.type == "text" and part.text:
                text_parts.append(part.text)
            elif part.type == "image_url" and part.image_url:
                image_urls.append(part.image_url.url)
        if image_urls:
            # Build multi-modal content list for the LLM
            content: list = [{"type": "text", "text": " ".join(text_parts)}]
            content += [
                {"type": "image_url", "image_url": {"url": url}}
                for url in image_urls
            ]
            return content, image_urls
        return " ".join(text_parts), []
    return "", []


def _make_response(content: str, model: str) -> dict:
    """Build a non-streaming OpenAI chat.completion response object."""
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


async def _sse_stream(
    token_gen: AsyncGenerator[str, None],
    model: str,
) -> AsyncGenerator[str, None]:
    """Wrap a KRAI token generator as OpenAI-format Server-Sent Events."""
    cmpl_id = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())
    async for chunk in token_gen:
        payload = {
            "id": cmpl_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{"index": 0, "delta": {"content": chunk}, "finish_reason": None}],
        }
        yield f"data: {json.dumps(payload)}\n\n"
    # Final chunk
    payload = {
        "id": cmpl_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    yield f"data: {json.dumps(payload)}\n\n"
    yield "data: [DONE]\n\n"


# ---------------------------------------------------------------------------
# Fast-path: direct DB lookup for error codes (no LLM required)
# ---------------------------------------------------------------------------

# Matches: 99.00.02 / 50.FF.02 / C-2801 / C2801 / SC542 / 541-011 / E001
_ERROR_CODE_RE = re.compile(
    r'\b([A-Z0-9]{1,4}(?:[.\-][A-Z0-9]{1,4}){1,5})\b'   # dotted/dashed: 99.00.02, 50.FF.02, C-2801
    r'|\b([A-Z]{1,3}[-]?\d{3,6})\b',                      # alpha+digits:  SC542, C9402, E001
    re.IGNORECASE,
)

# HP/Konica/Ricoh model patterns: M507, E50045, MFP 8601, bizhub 308, Aficio MP201
_MODEL_RE = re.compile(
    r'\b(E\d{4,6}|M\d{3,4}|P\d{4,6}|bizhub\s*\d{3,4}|Aficio\s*\w+|'
    r'MFP\s*\d{4,5}|MP\s*\d{3,4}|C\d{3,4}(?:dn|dw|n)?|LaserJet\s*\w+|'
    r'\w+[-]\d{3,5}(?:dn|dw|n|i|f)?)\b',
    re.IGNORECASE,
)

_FAST_PATH_SQL = """
    SELECT ec.error_code, ec.error_description,
           ec.solution_customer_text, ec.solution_agent_text, ec.solution_technician_text,
           ec.page_number, ec.severity_level, ec.confidence_score,
           m.name     AS manufacturer_name,
           d.filename AS document_filename,
           d.models   AS document_models,
           d.manufacturer AS document_manufacturer
    FROM   krai_intelligence.error_codes ec
    LEFT JOIN krai_core.manufacturers m  ON ec.manufacturer_id = m.id
    LEFT JOIN krai_core.documents      d  ON ec.document_id    = d.id
    WHERE  ec.is_category IS NOT TRUE
      AND  ec.error_code ILIKE $1
    ORDER  BY ec.confidence_score DESC
    LIMIT  50
"""

_FAST_PATH_MODEL_SQL = """
    SELECT ec.error_code, ec.error_description,
           ec.solution_customer_text, ec.solution_agent_text, ec.solution_technician_text,
           ec.page_number, ec.severity_level, ec.confidence_score,
           m.name     AS manufacturer_name,
           d.filename AS document_filename,
           d.models   AS document_models,
           d.manufacturer AS document_manufacturer
    FROM   krai_intelligence.error_codes ec
    LEFT JOIN krai_core.manufacturers m  ON ec.manufacturer_id = m.id
    LEFT JOIN krai_core.documents      d  ON ec.document_id    = d.id
    WHERE  ec.is_category IS NOT TRUE
      AND  ec.error_code ILIKE $1
      AND  array_to_string(d.models, ',') ILIKE $2
    ORDER  BY ec.confidence_score DESC
    LIMIT  10
"""

# Fallback: search chunks when all 3 solution columns are still NULL.
# NOTE: Only ASCII-safe ILIKE patterns — asyncpg can misparse non-ASCII string literals.
_CHUNK_SOLUTION_SQL = """
    SELECT c.text_chunk, d.filename, c.page_start
    FROM   krai_intelligence.chunks c
    JOIN   krai_core.documents d ON c.document_id = d.id
    WHERE  c.text_chunk ILIKE $1
      AND  c.text_chunk ILIKE $2
    ORDER  BY c.page_start
    LIMIT  3
"""

# Full solution: fetch the chunk containing the error code PLUS all consecutive
# chunks from the same document on the same and immediately following pages.
# Uses DISTINCT ON to deduplicate chunks from multiple processing runs.
_FULL_SOLUTION_SQL = """
    WITH code_chunk AS (
        SELECT c.id, c.document_id, c.page_start
        FROM   krai_intelligence.chunks c
        JOIN   krai_core.documents d ON c.document_id = d.id
        WHERE  d.filename = $1
          AND  c.text_chunk ILIKE $2
          AND  c.page_start > 20
        ORDER  BY
            CASE WHEN c.text_chunk ILIKE '%Recommended action%' THEN 0 ELSE 1 END,
            c.page_start
        LIMIT  1
    ),
    deduped AS (
        SELECT DISTINCT ON (c.text_chunk) c.text_chunk, c.page_start
        FROM   krai_intelligence.chunks c
        JOIN   code_chunk cc ON c.document_id = cc.document_id
        WHERE  c.page_start BETWEEN cc.page_start - 2 AND cc.page_start + 20
        ORDER  BY c.text_chunk, c.page_start, c.id
    )
    SELECT text_chunk, page_start FROM deduped
    ORDER BY page_start
    LIMIT  40
"""

# Images for a document + error code, grouped by page for inline insertion.
_IMAGE_BY_DOC_PAGE_SQL = """
    SELECT DISTINCT ON (img.page_number)
        img.storage_url, img.page_number, img.image_type, img.ai_description
    FROM krai_content.images img
    JOIN krai_core.documents d ON d.id = img.document_id
    WHERE d.filename = $1
      AND $2 = ANY(img.related_error_codes)
      AND img.storage_url LIKE 'http%'
    ORDER BY img.page_number,
             CASE img.image_type WHEN 'diagram' THEN 0 WHEN 'photo' THEN 1 ELSE 2 END
    LIMIT 6
"""


def _format_solution_text(text: str) -> str:
    """Clean up PDF-extraction artifacts and produce clean Markdown.

    Fixes:
    - Bullet "●" joined as proper "- " list items
    - Numbered steps split across lines: "1.\\nText" → "1. Text"
    - Section headers like "Recommended action" → **bold**
    - Excessive blank lines collapsed
    """
    if not text:
        return text
    # Bullet char: ensure each item starts on its own line
    text = re.sub(r'●\s*\n\s*', '\n- ', text)
    text = re.sub(r'●\s+', '\n- ', text)
    # Numbered step split across lines: "1.\n  Text" → "1. Text"
    text = re.sub(r'(\d+)\.\s*\n\s*([A-Z\(])', r'\1. \2', text)
    # Numbered steps inline without newline: "..sentence.1. Next" → "..sentence.\n1. Next"
    text = re.sub(r'([a-z\.])(\d+)\.\s+([A-Z])', r'\1\n\2. \3', text)
    # Sub-steps "a.\n", "b.\n" → join with next line
    text = re.sub(r'\n([a-z])\.\s*\n\s*([A-Z\(])', r'\n\1. \2', text)
    # Bold "Recommended action" section headers (single-pass regex, avoids double-bolding)
    text = re.sub(
        r'Recommended action(?:\s+for\s+(?:HP\s+service|service\s+or\s+support|customers|(?:call-center\s+)?agents(?:\s+and\s+technicians)?|onsite\s+technicians))?',
        lambda m: f'\n\n**{m.group(0).strip()}**\n\n',
        text,
    )
    # Remove HP catch-all variant lines like "13.B9.Dz" (standalone lines, also at end)
    text = re.sub(r'(?:^|\n)[0-9A-Fa-f]{2}\.[0-9A-Fa-f]{2}\.[A-Za-z][a-z]?\s*(?=\n|$)', '', text)
    # Remove PDF chapter/section headings that slip into solution text
    text = re.sub(r'\n?Chapter\s+\d+[^\n]*\n?', '\n', text)
    text = re.sub(r'\nENWW\n', '\n', text)
    # Remove PDF table header artefacts (pre-boot menu tables etc.)
    text = re.sub(r'\nTable\s+\d+[-–]\d+[^\n]*\n', '\n', text)
    text = re.sub(r'\n(?:Menu option|First level|Second level|Third level|Description)\n', '\n', text)
    # Remove lonely "Administrator" / "Administrator (continued)" lines from HP pre-boot tables
    text = re.sub(r'\nAdministrator(?:\s*\(continued\))?\n', '\n', text)
    # Collapse 3+ blank lines → one blank line
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _extract_solution_from_chunk(chunk_text: str, error_code: str) -> Optional[str]:
    """Pull the solution/recommended-action block for ``error_code`` out of a raw chunk."""
    # Find the section starting at the error code
    idx = chunk_text.upper().find(error_code.upper())
    if idx == -1:
        return None
    section = chunk_text[idx:]
    # Look for "Recommended action" / "Empfohlene" / numbered steps
    for marker in ("Recommended action", "Empfohlene", "Lösung:", "Solution:"):
        m = section.find(marker)
        if m != -1:
            # Grab up to 1200 chars from that marker
            block = section[m : m + 1200].strip()
            # Stop at the next error-code heading (e.g. "99.00.03 ...")
            stop = re.search(r'\n\d+\.\d+\.\d+\s', block)
            if stop:
                block = block[: stop.start()].strip()
            return block if len(block) > 20 else None
    # No explicit marker — return numbered steps if any
    steps = re.findall(r'\n\d+\.\s+[^\n]{10,}', section[:1200])
    if steps:
        return "\n".join(steps[:6]).strip()
    return None


def _extract_levels_from_combined(combined_text: str, error_code: str) -> dict:
    """
    Extract HP solution levels from a concatenation of deduplicated consecutive chunks.

    Finds where error_code starts and extracts all three HP solution levels from
    that point onwards, stopping at the next different error-code heading.

    Note: HP service manuals sometimes place shared "family" steps (1–N) before
    the individual error code entries.  Those shared steps are NOT included here —
    only the code-specific section is extracted.
    """
    from backend.utils.hp_solution_filter import extract_all_hp_levels

    idx = combined_text.upper().find(error_code.upper())
    if idx == -1:
        block = combined_text
    else:
        block = combined_text[idx:]
        # Stop at the next DIFFERENT error-code heading on its own line
        stop = re.search(
            r'\n[A-Z0-9]{1,4}[.\-][A-Z0-9]{1,4}[.\-][A-Z0-9]{1,4}\s+[A-Z]',
            block[len(error_code):],
            re.IGNORECASE,
        )
        if stop:
            block = block[:len(error_code) + stop.start()]

    return extract_all_hp_levels(block)


async def _fast_path_lookup(pool, text: str) -> Optional[str]:
    """Try an instant DB lookup if ``text`` contains an error code.

    Also detects a model number in the query (e.g. "M507", "E50045", "bizhub 308")
    and filters results to documents that cover that model.

    Returns:
        - Formatted Markdown with results (filtered by model when detected).
        - A "not found" message when a code is detected but absent from DB.
        - ``None`` when no error-code pattern is detected.
    """
    m = _ERROR_CODE_RE.search(text)
    if not m:
        return None

    raw_code = (m.group(1) or m.group(2)).upper()
    variants = [raw_code]
    no_dash = raw_code.replace('-', '')
    if no_dash != raw_code:
        variants.append(no_dash)

    # Detect optional model number in user message (ignore the error code itself)
    text_without_code = text[:m.start()] + text[m.end():]
    model_match = _MODEL_RE.search(text_without_code)
    raw_model = model_match.group(0).strip() if model_match else None

    try:
        async with pool.acquire() as conn:
            rows = None
            for v in variants:
                if raw_model:
                    # Try model-filtered query first
                    rows = await conn.fetch(_FAST_PATH_MODEL_SQL, f'%{v}%', f'%{raw_model}%')
                if not rows:
                    rows = await conn.fetch(_FAST_PATH_SQL, f'%{v}%')
                if rows:
                    break
    except Exception as exc:
        logger.warning("fast_path_lookup DB error: %s", exc)
        return None

    # Code pattern detected but nothing in DB → return immediately, skip LLM
    if not rows:
        return (
            f"**Fehlercode `{raw_code}` nicht in der KRAI-Datenbank gefunden.**\n\n"
            "Mögliche Ursachen:\n"
            "- Dieser Code wurde noch nicht aus den Service-Handbüchern extrahiert\n"
            "- Prüfe die Schreibweise (z.B. `C-2801` statt `C2801`)\n"
            "- Wende dich an den Hersteller-Support oder öffne das zugehörige Service-Manual direkt"
        )

    # ── Group by (code, description) — collect unique sources with model info ──
    groups: dict[str, dict] = {}
    for row in rows:
        key = f"{row['error_code']}|{row['error_description']}"
        row_tech = row["solution_technician_text"] or ""
        row_agent = row["solution_agent_text"] or ""
        row_cust = row["solution_customer_text"] or ""
        if key not in groups:
            groups[key] = {
                "code": row["error_code"],
                "desc": row["error_description"] or "—",
                "sol_customer":   row_cust,
                "sol_agent":      row_agent,
                "sol_technician": row_tech,
                "mfr":  row["manufacturer_name"] or row.get("document_manufacturer") or "",
                "sources": [],  # list of (filename, page, models_list)
            }
        else:
            # Keep the longest (best) solution text across all matching rows
            if len(row_tech) > len(groups[key]["sol_technician"]):
                groups[key]["sol_technician"] = row_tech
            if len(row_agent) > len(groups[key]["sol_agent"]):
                groups[key]["sol_agent"] = row_agent
            if len(row_cust) > len(groups[key]["sol_customer"]):
                groups[key]["sol_customer"] = row_cust
        fn  = row["document_filename"]
        pg  = row["page_number"]
        mdl = list(row["document_models"] or [])
        src_key = f"{fn}:{pg}"
        if fn and src_key not in {f"{s[0]}:{s[1]}" for s in groups[key]["sources"]}:
            groups[key]["sources"].append((fn, pg, mdl))

    # ── Fetch full multi-chunk solution for each unique document source ───────
    # Also collects images linked to the error code for inline display.
    full_solutions: dict[str, dict] = {}  # filename → {customer, agent, technician, images}
    try:
        async with pool.acquire() as conn:
            seen_docs: set[str] = set()
            for group in groups.values():
                for fn, pg, mdl in group["sources"]:
                    if fn in seen_docs:
                        continue
                    seen_docs.add(fn)

                    # Always fetch images — independent of solution text quality
                    img_rows = await conn.fetch(_IMAGE_BY_DOC_PAGE_SQL, fn, raw_code)
                    seen_urls: set[str] = set()
                    image_md_list: list[str] = []
                    for ir in img_rows:
                        url = _rewrite_storage_url(ir['storage_url'])
                        if url not in seen_urls:
                            seen_urls.add(url)
                            caption = ir['ai_description'] or ir['image_type'] or 'Bild'
                            image_md_list.append(f"![{caption}]({url})")

                    # Only fetch chunks when DB solution columns are short/missing
                    db_tech_len = len(group["sol_technician"] or "")
                    if db_tech_len < 200:
                        chunk_rows = await conn.fetch(_FULL_SOLUTION_SQL, fn, f'%{raw_code}%')
                        if chunk_rows:
                            combined = '\n'.join(row['text_chunk'] for row in chunk_rows)
                            levels = _extract_levels_from_combined(combined, raw_code)
                            new_tech_len = len(levels.get("technician") or "")
                            if any(levels.values()) and new_tech_len >= max(db_tech_len, 100):
                                full_solutions[fn] = {**levels, 'images': image_md_list}
                                continue

                    # DB solution is good — just store images (no text override)
                    if image_md_list and fn not in full_solutions:
                        full_solutions[fn] = {'images': image_md_list}
    except Exception as exc:
        logger.warning("full_solution_lookup error: %s", exc)

    # ── Chunk fallback only when ALL three DB columns are empty ───────────────
    solution_from_chunk: Optional[str] = None
    first_group = next(iter(groups.values()))
    has_db_solution = bool(
        first_group["sol_technician"] or first_group["sol_agent"] or first_group["sol_customer"]
    )

    if not has_db_solution:
        try:
            async with pool.acquire() as conn:
                chunk_rows = await conn.fetch(
                    _CHUNK_SOLUTION_SQL,
                    f'%{raw_code}%',
                    '%Recommended action%',
                )
            for cr in chunk_rows:
                sol = _extract_solution_from_chunk(cr["text_chunk"], raw_code)
                if sol:
                    solution_from_chunk = sol
                    break
        except Exception as exc:
            logger.warning("chunk_solution_lookup error: %s", exc)

    # ── Format output ─────────────────────────────────────────────────────────
    parts: list[str] = []
    for group in groups.values():
        code    = group["code"]
        desc    = group["desc"]
        sol_c   = group["sol_customer"]
        sol_a   = group["sol_agent"]
        sol_t   = group["sol_technician"]
        mfr     = group["mfr"]
        sources = group["sources"]

        # Strip leading punctuation/spaces from description (PDF extraction artifact)
        desc = re.sub(r'^[\s,;:\-–—]+', '', desc).strip() or "—"
        header = f"### Fehler `{code}` – {desc}"
        if mfr:
            header += f"  *({mfr})*"
        if raw_model:
            header += f"  🖨️ gefiltert für **{raw_model}**"
        parts.append(header)

        # Use full multi-chunk solution when available, fall back to DB column.
        # Prefer the source document whose solution contains inline images (![...]).
        first_src_fn = sources[0][0] if sources else None
        full = {}
        for fn, _pg, _mdl in sources:
            candidate = full_solutions.get(fn, {})
            if not candidate:
                continue
            # Prefer any candidate that has images
            if candidate.get('images'):
                full = candidate
                break
            if not full:
                full = candidate
        sol_t_full = _format_solution_text(full.get('technician') or sol_t or "")
        sol_a_full = _format_solution_text(full.get('agent') or sol_a or "")
        sol_c_full = _format_solution_text(full.get('customer') or sol_c or "")
        images_md: list[str] = full.get('images') or []

        # Solution: technician preferred → agent → customer → chunk fallback
        if sol_t_full:
            parts.append("\n**🔧 Techniker-Lösung:**\n")
            parts.append(sol_t_full)
            if images_md:
                parts.append("\n\n**🖼️ Bilder aus dem Service-Manual:**\n")
                parts.extend(images_md)
            if sol_c_full:
                parts.append("\n---\n**👤 Anwender-Kurzlösung:**\n")
                parts.append(sol_c_full)
        elif sol_a_full:
            parts.append("\n**📞 2nd-Level-Lösung:**\n")
            parts.append(sol_a_full)
            if images_md:
                parts.append("\n\n**🖼️ Bilder aus dem Service-Manual:**\n")
                parts.extend(images_md)
            if sol_c_full:
                parts.append("\n---\n**👤 Anwender-Kurzlösung:**\n")
                parts.append(sol_c_full)
        elif sol_c_full:
            parts.append("\n**👤 Anwender-Lösung:**\n")
            parts.append(sol_c_full)
        elif solution_from_chunk:
            parts.append("\n**Lösung** *(aus Service-Manual)*:\n")
            parts.append(_format_solution_text(solution_from_chunk))
        else:
            parts.append("\n⚠️ *Keine Lösung in der Datenbank hinterlegt.*")

        # Sources with model coverage
        if sources:
            parts.append("")
            if raw_model:
                parts.append(f"**📄 Quelle für {raw_model}:**")
            else:
                parts.append(f"**📄 Quellen** ({len(sources)} Dokumente):")
            for fn, pg, mdl in sources:
                src = f"- `{fn}`"
                if pg:
                    src += f", Seite {pg}"
                if mdl and not raw_model:
                    shown = ", ".join(mdl[:6])
                    if len(mdl) > 6:
                        shown += f" +{len(mdl)-6} weitere"
                    src += f"\n  *Modelle: {shown}*"
                parts.append(src)

        if not raw_model and len(sources) > 1:
            parts.append(
                f"\n> 💡 Nenne dein Modell für eine gefilterte Antwort — z.B. `{code} M507`"
            )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Guided-path: direct SQL for parts / video queries (no LLM)
# ---------------------------------------------------------------------------

_PARTS_KEYWORDS = re.compile(
    r'\b(ersatzteil|spare.?part|part.?number|teilenummer|bauteil|fuser|drum|toner|'
    r'roller|belt|kit|assembly|unit|motor|sensor|board|pcb)\b',
    re.IGNORECASE,
)

_VIDEO_KEYWORDS = re.compile(
    r'\b(video|youtube|tutorial|anleitung|howto|how.?to|reparatur|repair|'
    r'wartung|maintenance|replace|austausch|einbau|installation)\b',
    re.IGNORECASE,
)

_PARTS_SQL = """
    SELECT pc.part_number, pc.part_name, pc.part_description, pc.part_category,
           pc.unit_price_usd, m.name AS manufacturer_name
    FROM   krai_parts.parts_catalog pc
    LEFT JOIN krai_core.manufacturers m ON pc.manufacturer_id = m.id
    WHERE  pc.part_number ILIKE $1
       OR  pc.part_name   ILIKE $1
    ORDER  BY pc.part_number
    LIMIT  8
"""

_VIDEO_SQL = """
    SELECT v.title, v.video_url, v.description, v.duration, v.channel_title,
           m.name AS manufacturer_name
    FROM   krai_content.videos v
    LEFT JOIN krai_core.manufacturers m ON v.manufacturer_id = m.id
    WHERE  v.title       ILIKE $1
       OR  v.description ILIKE $1
    ORDER  BY v.published_at DESC NULLS LAST
    LIMIT  5
"""

_SEMANTIC_SQL = """
    SELECT c.text_chunk, c.page_start, d.filename, d.original_filename
    FROM   krai_intelligence.chunks c
    JOIN   krai_core.documents d ON c.document_id = d.id
    WHERE  c.embedding IS NOT NULL
      AND  c.processing_status = 'completed'
    ORDER  BY c.embedding <=> $1
    LIMIT  5
"""


async def _parts_lookup(pool, text: str) -> Optional[str]:
    """Return spare-parts results when query mentions part-related keywords."""
    if not _PARTS_KEYWORDS.search(text):
        return None
    # Extract longest token as search term
    tokens = [t for t in re.findall(r'\b\w[\w\-\.]{2,}\b', text) if not re.match(r'^(was|ist|wie|gibt|es|der|die|das|und|oder|ich|du|wir|sie|ein|für|mit|von|bei|nach|auf|an|im|zur|zum)$', t, re.I)]
    term = max(tokens, key=len) if tokens else text[:40]
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(_PARTS_SQL, f'%{term}%')
            if not rows and len(term) > 6:
                # Retry with shorter stem
                rows = await conn.fetch(_PARTS_SQL, f'%{term[:6]}%')
    except Exception as exc:
        logger.warning("parts_lookup DB error: %s", exc)
        return None
    if not rows:
        return f"**Kein Ersatzteil für `{term}` gefunden.**\n\nTipp: Suche nach Teilenummer oder Gerätebezeichnung."
    lines = ["## 🔧 Ersatzteile\n"]
    for r in rows:
        price = f" — ${r['unit_price_usd']:.2f}" if r['unit_price_usd'] else ""
        mfr = f" *({r['manufacturer_name']})*" if r['manufacturer_name'] else ""
        lines.append(f"**{r['part_number']}** – {r['part_name']}{mfr}{price}")
        if r['part_description']:
            lines.append(f"  _{r['part_description'][:120]}_")
    return "\n".join(lines)


async def _video_lookup(pool, text: str) -> Optional[str]:
    """Return video results when query mentions video/tutorial keywords."""
    if not _VIDEO_KEYWORDS.search(text):
        return None
    tokens = [t for t in re.findall(r'\b\w[\w\-\.]{2,}\b', text) if not re.match(r'^(video|tutorial|anleitung|repair|replace|youtube|howto|wie|kann|ich|das|die|der|ein|für)$', t, re.I)]
    term = max(tokens, key=len) if tokens else text[:40]
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(_VIDEO_SQL, f'%{term}%')
    except Exception as exc:
        logger.warning("video_lookup DB error: %s", exc)
        return None
    if not rows:
        return f"**Kein Video für `{term}` gefunden.**\n\nTipp: Suche nach Gerätemodell oder Reparaturtyp."
    lines = ["## 🎬 Videos\n"]
    for r in rows:
        dur = f" ({r['duration']//60}:{r['duration']%60:02d})" if r['duration'] else ""
        ch = f" — {r['channel_title']}" if r['channel_title'] else ""
        lines.append(f"**[{r['title']}]({r['video_url']})**{dur}{ch}")
        if r['description']:
            lines.append(f"  _{r['description'][:120]}_\n")
    return "\n".join(lines)


async def _semantic_fast_lookup(pool, text: str) -> Optional[str]:
    """Embedding-based semantic search — no LLM, uses pgvector directly (~1.5 s)."""
    ollama_url = os.getenv("OLLAMA_URL", "http://krai-ollama-prod:11434")
    embed_model = os.getenv("OLLAMA_MODEL_EMBEDDING", "nomic-embed-text:latest")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{ollama_url}/api/embed",
                json={"model": embed_model, "input": text},
            )
            resp.raise_for_status()
            embedding = resp.json()["embeddings"][0]
    except Exception as exc:
        logger.warning("semantic_fast_lookup embed error: %s", exc)
        return None

    # Format embedding as pgvector literal
    vec_literal = "[" + ",".join(f"{x:.6f}" for x in embedding) + "]"
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(_SEMANTIC_SQL, vec_literal)
    except Exception as exc:
        logger.warning("semantic_fast_lookup DB error: %s", exc)
        return None

    if not rows:
        return "**Keine relevanten Inhalte in den Service-Handbüchern gefunden.**"

    lines = [f"## 🔍 Suchergebnisse für: _{text[:80]}_\n"]
    for i, r in enumerate(rows, 1):
        doc = r['original_filename'] or r['filename'] or "Unbekanntes Dokument"
        page = f", Seite {r['page_start']}" if r['page_start'] else ""
        lines.append(f"### Ergebnis {i} — 📄 {doc}{page}")
        lines.append(r['text_chunk'][:600].strip())
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/models")
async def list_models(
    current_user: dict = Depends(require_permission("agent:chat")),
) -> dict:
    """List available KRAI models in OpenAI format."""
    llm_backend = os.getenv("LLM_BACKEND", "ollama").lower()
    if llm_backend == "openai":
        backend_model = os.getenv("OPENAI_MODEL", "gpt-4o")
    else:
        backend_model = (
            os.getenv("OLLAMA_MODEL_CHAT")
            or os.getenv("OLLAMA_MODEL_TEXT", "llama3.2:latest")
        )
    return {
        "object": "list",
        "data": [
            {
                "id": "krai",
                "object": "model",
                "created": 1700000000,
                "owned_by": "krai",
                "description": (
                    f"KRAI AI Agent — error codes, spare parts, service manuals "
                    f"(powered by {backend_model})"
                ),
            }
        ],
    }


@router.post("/chat/completions")
async def chat_completions(
    body: ChatCompletionRequest,
    request: Request,
    current_user: dict = Depends(require_permission("agent:chat")),
):
    """OpenAI-compatible chat completions endpoint backed by the KRAI routing layer.

    Routing priority (fastest → slowest, all LLM-free except the last):
      1. Error-code pattern  → direct SQL on error_codes  (~300 ms)
      2. Parts keywords      → direct SQL on parts_catalog (~300 ms)
      3. Video keywords      → direct SQL on videos        (~300 ms)
      4. Everything else     → pgvector semantic search    (~1.5 s)
      5. Fallback            → LangGraph agent (needs LLM, with timeout)
    """
    agent = getattr(request.app.state, "krai_agent", None)

    session_id = _session_id(body.messages, body.user)
    content, images = _extract_last_user_content(body.messages)

    if not content:
        raise HTTPException(status_code=400, detail="No user message found in request")

    # ── Routing: SQL/embedding paths (no LLM, always fast) ──────────────────
    # Only applicable for plain-text, non-image messages.
    if not images and isinstance(content, str):
        pool = getattr(request.app.state, "db_pool", None)
        if pool is not None:
            # 1. Error-code pattern → instant SQL (~300 ms)
            result = await _fast_path_lookup(pool, content)
            if result is not None:
                logger.info("route=error_code for: %.60s", content)
                return _make_response(result, body.model)

            # 2. Spare-parts keywords → SQL parts_catalog (~300 ms)
            result = await _parts_lookup(pool, content)
            if result is not None:
                logger.info("route=parts for: %.60s", content)
                return _make_response(result, body.model)

            # 3. Video/tutorial keywords → SQL videos (~300 ms)
            result = await _video_lookup(pool, content)
            if result is not None:
                logger.info("route=video for: %.60s", content)
                return _make_response(result, body.model)

            # 4. Semantic search via pgvector (embed ~1 s + vector search ~0.5 s)
            result = await _semantic_fast_lookup(pool, content)
            if result is not None:
                logger.info("route=semantic for: %.60s", content)
                return _make_response(result, body.model)

    # ── Fallback: LangGraph agent (requires LLM — slow without GPU) ──────────
    if agent is None:
        return _make_response(
            "⚠️ KRAI Agent ist nicht verfügbar. Bitte versuche eine spezifischere "
            "Anfrage mit einem Fehlercode (z.B. `99.00.02`) oder Stichworten.",
            body.model,
        )

    _AGENT_TIMEOUT = int(os.getenv("KRAI_AGENT_TIMEOUT", "30"))

    if body.stream:
        async def _gen() -> AsyncGenerator[str, None]:
            try:
                async with asyncio.timeout(_AGENT_TIMEOUT):
                    async for token in agent.chat_stream(content, session_id):
                        yield token
            except TimeoutError:
                yield "\n\n⚠️ *Antwort-Timeout. Bitte stelle eine spezifischere Frage.*"

        return StreamingResponse(
            _sse_stream(_gen(), body.model),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    try:
        async with asyncio.timeout(_AGENT_TIMEOUT):
            response_text = await agent.chat(content, session_id)
    except TimeoutError:
        response_text = (
            "⚠️ **Timeout** — Die Anfrage hat zu lange gedauert.\n\n"
            "Versuche es mit einem Fehlercode (z.B. `99.00.02`), "
            "einem Ersatzteil-Stichwort oder einem Video-Begriff."
        )
    return _make_response(response_text, body.model)
