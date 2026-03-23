# RAG Improvements Design
**Date:** 2026-03-23
**Status:** Approved
**Scope:** Backend — Agent, Search, Evaluation

## Background

KRAI's retrieval stack (LangGraph + pgvector + Ollama) is solid but has three concrete gaps:

1. Agent tools use `ILIKE %query%` keyword matching instead of vector search, limiting semantic recall.
2. No reranking step — pgvector cosine-similarity is used as the final ranking signal.
3. No systematic way to measure whether retrieval or prompt changes improve answer quality.

This spec covers targeted fixes for all three. LlamaIndex was evaluated and rejected: the project already uses LangChain/LangGraph for the agent layer, has a domain-specific `SmartChunker` that no generic framework can replace, and a custom pgvector schema that doesn't map cleanly to LlamaIndex abstractions.

---

## Rollout Order

> **Area 3 (Evaluation) is built first** to capture a quality baseline before any retrieval changes land. Areas 1 and 2 are then measured against this baseline.

1. **Ragas evaluation script** — establish baseline.
2. **Vector search in agent tools** — highest impact on RAG quality.
3. **Reranking** — builds on the expanded candidate set from step 2.

---

## Area 1: Vector Search in Agent Tools

### Problem

`search_error_codes`, `search_videos`, `_fetch_related_documents`, and `_fetch_related_videos` in `agent_api.py` use `ILIKE %query%` as the primary lookup.

> **`semantic_search` is NOT in scope for Area 1.** It already performs full pgvector similarity search via a direct `httpx` call to the Ollama embeddings API (lines 523–612 of `agent_api.py`). It uses `ch.text_chunk AS content` and returns results with a `"content"` key. No changes needed.

### Design

Each affected **tool entry point** (`search_error_codes`, `search_videos`) runs a vector seed step **before** any existing ILIKE passes:

```
query → AIService.generate_embeddings() → pgvector similarity → [chunk_ids, document_ids, product_ids]
      → inject as WHERE/AND predicates into existing SQL
      → if vector returns 0 results: fall through to existing ILIKE paths unchanged
```

The vector step runs **once per tool call**, producing shared `matched_chunk_ids`, `matched_document_ids`, and `matched_product_ids` that are forwarded to all internal helpers within that call.

### Dependency Injection

`KRAIAgent.__init__` gains two new optional parameters:

```python
def __init__(
    self,
    pool: asyncpg.Pool,
    ollama_base_url: str | None = None,
    ai_service: AIService | None = None,          # NEW
    reranking_service: RerankingService | None = None,  # NEW (Area 2)
) -> None:
```

These are forwarded to `create_tools()`:

```python
# complete updated signature:
def create_tools(
    pool: asyncpg.Pool,
    ollama_base_url: str,
    ai_service: AIService | None = None,
    reranking_service: RerankingService | None = None,
) -> list:
```

`app.py` constructs `AIService` and `RerankingService` and passes them to `KRAIAgent(pool, ollama_base_url, ai_service, reranking_service)`. Both parameters are optional with `None` defaults so existing callers without the new services continue to work (graceful degradation to ILIKE).

### SQL Predicates by Tool

| Tool / Helper | Vector seed predicate |
|---------------|-----------------------|
| `search_error_codes` | `AND ec.chunk_id = ANY($n::uuid[])` |
| `_fetch_related_documents` | `AND d.id = ANY($n::uuid[])` |
| `_fetch_related_videos` | Uses existing `matched_document_ids` / `matched_product_ids` params (already in helper signature) |

**`search_error_codes` two-pass logic:** Vector seed is computed once at tool entry. If results are found, `AND ec.chunk_id = ANY($n::uuid[])` is added to both the exact-match WHERE clause and the broad ILIKE WHERE clause. If vector returns zero results, both ILIKE passes run unchanged.

### What Does Not Change

- `build_scope_filters`, scope system, serialisation format
- LangGraph agent structure
- `SmartChunker`, pipeline processors, pgvector schema
- `semantic_search` tool

---

## Area 2: Reranking

### Problem

pgvector returns Top-K by cosine similarity — good first-pass, but a CrossEncoder that reads query and document together is more accurate.

### Design

```
query → pgvector (top-20 candidates) → CrossEncoder rerank → top-5 → LLM
```

### `RerankingService` Interface

```python
class RerankingService:
    def rerank(self, query: str, texts: list[str], top_n: int = 5) -> list[str]:
        """
        texts: list of plain text strings (chunk content only, no metadata)
        returns: top_n strings sorted by CrossEncoder score, descending
        When ENABLE_RERANKING=false: returns texts[:top_n] unchanged (no-op)
        """
```

Callers extract the text field before calling `rerank()` and re-attach metadata after. This keeps the service free of schema knowledge.

### Text Field Names

| Integration point | Field to extract before rerank | Reattach by |
|-------------------|-------------------------------|-------------|
| `MultimodalSearchService` | `result['content']` | index-matching after rerank |
| `semantic_search` tool | `row["content"]` (aliased from `ch.text_chunk`) | index-matching after rerank |

### Configuration

| Env var | Default | Notes |
|---------|---------|-------|
| `ENABLE_RERANKING` | `true` | `false` → no-op passthrough |
| `RERANKING_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Configurable — swap for larger model as hardware improves |
| `RERANKING_TOP_N` | `5` | Results passed to LLM |
| `RERANKING_CANDIDATES` | `20` | Candidates fetched before reranking |

Model loaded once at startup, cached in memory.

### Integration Points

**`MultimodalSearchService.search_multimodal()`:**
- Inject `RerankingService` into `__init__()`.
- Fetch `RERANKING_CANDIDATES` instead of current limit.
- After retrieval: extract `result['content']`, call `rerank()`, re-attach metadata by index, return top `RERANKING_TOP_N`.

**`semantic_search` tool:**
- After fetching rows from pgvector: extract `row["content"]`, call `reranking_service.rerank()`, re-attach full row metadata by index, pass top-N to LLM context.
- `reranking_service` is available via closure from `create_tools()` (see injection pattern above).

### Known DB Bug — Fix Required Before Area 2

`database/migrations_postgresql/003_functions.sql` references `c.chunk_text` in the `match_multimodal` function (lines 164, 225), but the correct column name is `c.text_chunk` (confirmed in `001_core_schema.sql` rename path, seeds `01_schema.sql`, and `024_add_missing_indexes.sql`). This is documented in CLAUDE.md's known column name traps.

**This bug must be fixed as part of Area 2 implementation:** a corrective migration must update the `match_multimodal` function to use `c.text_chunk`. Without this fix, reranking will receive null/empty text for all text chunks.

### Dependencies

`sentence-transformers` is already in `requirements.txt`. No new packages needed.

---

## Area 3: RAG Evaluation with Ragas

### Problem

No systematic baseline exists to compare retrieval or answer quality across changes.

### Design

Standalone script `scripts/evaluate_rag.py` using Ragas (`pip install ragas` — no LlamaIndex dependency).

**Target Ragas version:** `>=0.1.0, <0.2.0`. In this version the `evaluate()` API accepts a `Dataset` with columns `question`, `answer`, `contexts` (list of strings), and `ground_truth` (string). The `ground_truth` string is sufficient for all three initial metrics.

**Metrics (initial set):**

| Metric | Requires |
|--------|---------|
| `faithfulness` | question, answer, contexts |
| `answer_relevancy` | question, answer |
| `context_precision` | question, contexts, ground_truth (string) |

> **`context_recall` excluded** — requires ground-truth context chunks as text, not derivable from document IDs. Can be added later when the dataset includes explicit reference chunks.

**Test dataset format** (`scripts/eval_dataset.json`):

```json
[
  {
    "question": "What causes error 13.B9.Az on the bizhub C450i?",
    "ground_truth": "Paper jam in the fuser area caused by worn separation claws.",
    "scope_document_id": "uuid-1"
  }
]
```

`scope_document_id` (optional) is passed as the `document_id` field in the `AgentScope` when calling the agent, narrowing retrieval to the relevant document. If absent, no scope is applied.

**Script flow:**

The agent chat endpoint returns the LLM's final answer only — it does not expose intermediate tool results or retrieved chunks. To get `contexts` for Ragas metrics, the script makes two parallel calls per question:

1. Load `eval_dataset.json`.
2. For each entry:
   a. **Agent call:** POST `/api/v1/agent/chat` with `{message: question, session_id: ..., scope: {document_id: scope_document_id}}` → captures `answer`.
   b. **Search call:** POST `/search/` with `{query: question, document_id: scope_document_id}` → captures the list of returned chunk texts as `contexts`.
3. Build Ragas `Dataset`: `{question, answer, contexts: [list of chunk texts], ground_truth}`.
4. Call `ragas.evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_precision])`.
5. Print summary table to stdout; write JSON report to `scripts/eval_results/YYYY-MM-DD-HH-MM.json`.

> The search call uses the same retrieval path the agent uses internally, so `contexts` is a faithful representation of what the agent had access to.

**Initial dataset:** ~20 questions covering error codes, parts, documents, and multimodal queries.

### New Dependency

```
ragas>=0.1.0,<0.2.0   # dev/CI only
```

Added to `requirements-dev.txt` (not `requirements.txt`).

### Constraints

- Runs manually or in CI — **never** in production.
- Requires running backend or test database snapshot.

---

## Out of Scope

- LlamaIndex adoption (evaluated and rejected — see Background).
- Changes to `SmartChunker` or any pipeline processor.
- Changes to the pgvector schema or migrations.
- Production monitoring / real-time quality dashboards.
- Ragas `context_recall` metric (future work).
