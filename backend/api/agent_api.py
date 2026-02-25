"""
KRAI AI Agent API
=================
LangGraph-based conversational agent for technical support.

Features:
- Error code search
- Spare parts search
- Video tutorials
- Semantic search over service manuals
- Persistent conversation memory per session
- Streaming responses
"""
import sys
import os
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Optional

import asyncpg
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# LangChain / LangGraph (requires langchain>=1.0.0, langgraph>=1.0.0)
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from services.db_pool import get_pool
from processors.env_loader import load_all_env_files

project_root = Path(__file__).parent.parent.parent
load_all_env_files(project_root)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class ChatMessage(BaseModel):
    """Chat message from user"""
    message: str = Field(..., description="User's message")
    session_id: str = Field(..., description="Unique session ID for conversation memory")
    stream: bool = Field(default=False, description="Enable streaming response")


class ChatResponse(BaseModel):
    """Chat response from agent"""
    response: str
    session_id: str
    timestamp: str


# ============================================================================
# Agent Tools
# ============================================================================

def create_tools(pool: asyncpg.Pool, ollama_base_url: str) -> list:
    """
    Create agent tools bound to the database pool.
    All tools are async and use the shared asyncpg pool.
    """

    @tool
    async def search_error_codes(query: str) -> str:
        """
        Search for printer/copier error codes in the KRAI database.
        Use this tool when the user asks about an error code or error message.
        Input: error code or search term (e.g. "C9402", "Fehler 10.00.33", "Error C-1005")
        Returns: JSON with error description, solution steps, source document and page number.
        """
        # Extract error code from natural-language query
        matches = re.findall(r'\b\d+(?:\.\d+)+\b', query, re.IGNORECASE)  # dots: 10.00.33
        if not matches:
            matches = re.findall(r'\b[A-Z]-?\d{3,}\b', query, re.IGNORECASE)  # letter+digits: C9402
        search_term = matches[0] if matches else query

        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT ec.error_code, ec.error_description, ec.solution_text,
                           ch.page_number, ec.severity_level, ec.confidence_score,
                           m.name  AS manufacturer_name,
                           d.filename AS document_filename
                    FROM   krai_intelligence.error_codes ec
                    LEFT JOIN krai_intelligence.chunks ch ON ec.chunk_id   = ch.id
                    LEFT JOIN krai_core.manufacturers  m  ON ec.manufacturer_id = m.id
                    LEFT JOIN krai_core.documents      d  ON ec.document_id = d.id
                    WHERE  ec.error_code ILIKE $1
                    ORDER  BY ec.confidence_score DESC
                    LIMIT  5
                    """,
                    f'%{search_term}%',
                )

            if not rows:
                return json.dumps(
                    {"found": False, "message": f"Fehlercode '{search_term}' nicht in der Datenbank gefunden."},
                    ensure_ascii=False,
                )

            results = [
                {
                    "error_code":         row["error_code"],
                    "error_description":  row["error_description"],
                    "solution_text":      row["solution_text"],
                    "manufacturer":       row["manufacturer_name"],
                    "document":           row["document_filename"],
                    "page_number":        row["page_number"],
                    "severity_level":     row["severity_level"],
                    "confidence_score":   float(row["confidence_score"]) if row["confidence_score"] else 0.0,
                }
                for row in rows
            ]
            return json.dumps({"found": True, "count": len(results), "error_codes": results}, ensure_ascii=False)

        except Exception as exc:
            logger.error("search_error_codes error: %s", exc)
            return json.dumps({"found": False, "error": str(exc)})

    @tool
    async def search_parts(query: str, manufacturer: Optional[str] = None) -> str:
        """
        Search for spare parts and components in the KRAI database.
        Use this tool when the user asks about spare parts, components or part numbers.
        Input: part name or part number (e.g. "Fuser Unit", "Toner", "A1234567").
               Optionally pass 'manufacturer' to narrow the results (e.g. "Lexmark").
        Returns: JSON with part number, name, description, manufacturer and price.
        """
        try:
            async with pool.acquire() as conn:
                if manufacturer:
                    rows = await conn.fetch(
                        """
                        SELECT p.part_number, p.part_name, p.description,
                               m.name AS manufacturer_name, p.price_usd
                        FROM   krai_parts.parts_catalog p
                        JOIN   krai_core.manufacturers m ON p.manufacturer_id = m.id
                        WHERE  (p.part_number ILIKE $1 OR p.part_name ILIKE $2 OR p.description ILIKE $3)
                          AND  m.name ILIKE $4
                        LIMIT  10
                        """,
                        f'%{query}%', f'%{query}%', f'%{query}%', f'%{manufacturer}%',
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT p.part_number, p.part_name, p.description,
                               m.name AS manufacturer_name, p.price_usd
                        FROM   krai_parts.parts_catalog p
                        JOIN   krai_core.manufacturers m ON p.manufacturer_id = m.id
                        WHERE  p.part_number ILIKE $1 OR p.part_name ILIKE $2 OR p.description ILIKE $3
                        LIMIT  10
                        """,
                        f'%{query}%', f'%{query}%', f'%{query}%',
                    )

            if not rows:
                return json.dumps(
                    {"found": False, "message": f"Keine Ersatzteile für '{query}' gefunden."},
                    ensure_ascii=False,
                )

            results = [
                {
                    "part_number":      row["part_number"],
                    "part_name":        row["part_name"],
                    "description":      row["description"],
                    "manufacturer":     row["manufacturer_name"],
                    "price_usd":        float(row["price_usd"]) if row.get("price_usd") else None,
                }
                for row in rows
            ]
            return json.dumps({"found": True, "count": len(results), "parts": results}, ensure_ascii=False)

        except Exception as exc:
            logger.error("search_parts error: %s", exc)
            return json.dumps({"found": False, "error": str(exc)})

    @tool
    async def search_videos(query: str) -> str:
        """
        Search for repair video tutorials in the KRAI database.
        Use this tool when the user asks for videos, step-by-step guides or tutorials.
        Input: search term (e.g. "Fuser austauschen", "Toner wechseln", "HP E877").
        Returns: JSON with video title, URL, description, duration and model series.
        """
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT v.title, v.video_url, v.description, v.duration,
                           v.model_series, m.name AS manufacturer_name
                    FROM   krai_content.videos v
                    LEFT JOIN krai_core.manufacturers m ON v.manufacturer_id = m.id
                    WHERE  v.title ILIKE $1 OR v.description ILIKE $2 OR v.model_series ILIKE $3
                    LIMIT  10
                    """,
                    f'%{query}%', f'%{query}%', f'%{query}%',
                )

            if not rows:
                return json.dumps(
                    {"found": False, "message": f"Keine Videos für '{query}' gefunden."},
                    ensure_ascii=False,
                )

            results = [
                {
                    "title":        row["title"],
                    "url":          row["video_url"],
                    "description":  row["description"],
                    "duration":     row["duration"],
                    "manufacturer": row["manufacturer_name"],
                    "model_series": row["model_series"],
                }
                for row in rows
            ]
            return json.dumps({"found": True, "count": len(results), "videos": results}, ensure_ascii=False)

        except Exception as exc:
            logger.error("search_videos error: %s", exc)
            return json.dumps({"found": False, "error": str(exc)})

    @tool
    async def semantic_search(query: str, limit: int = 5) -> str:
        """
        Semantic search over all service manual content using AI embeddings.
        Use this tool for general questions or when the other tools return no results.
        Finds relevant content even when exact keywords do not match.
        Input: natural language question (e.g. "Wie behebe ich Papier-Staus?", "Drucker druckt nicht").
        Returns: JSON with matching text passages and their similarity scores.
        """
        try:
            embed_model = os.getenv("OLLAMA_MODEL_EMBED", "nomic-embed-text")
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{ollama_base_url}/api/embeddings",
                    json={"model": embed_model, "prompt": query},
                )

            if resp.status_code != 200:
                return json.dumps({"found": False, "error": f"Embedding failed: {resp.text}"})

            query_embedding = resp.json()["embedding"]

            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT content, metadata, document_id, id AS chunk_id,
                           1 - (embedding <=> $1::vector) AS similarity
                    FROM   krai_intelligence.chunks
                    WHERE  embedding IS NOT NULL
                    ORDER  BY embedding <=> $1::vector
                    LIMIT  $2
                    """,
                    query_embedding,
                    limit,
                )

            if not rows:
                return json.dumps(
                    {"found": False, "message": f"Keine relevanten Inhalte für '{query}' gefunden."},
                    ensure_ascii=False,
                )

            results = [
                {
                    "content":     row["content"],
                    "similarity":  round(float(row["similarity"]), 4),
                    "metadata":    dict(row["metadata"]) if row.get("metadata") else {},
                    "document_id": str(row["document_id"]),
                    "chunk_id":    str(row["chunk_id"]),
                }
                for row in rows
            ]
            return json.dumps({"found": True, "count": len(results), "results": results}, ensure_ascii=False)

        except Exception as exc:
            logger.error("semantic_search error: %s", exc, exc_info=True)
            return json.dumps({"found": False, "error": str(exc)})

    return [search_error_codes, search_parts, search_videos, semantic_search]


# ============================================================================
# System Prompt
# ============================================================================

_SYSTEM_PROMPT = SystemMessage(content="""Du bist **KRAI** – der KI-Assistent für Drucker- und Kopierer-Servicetechniker.
Du hast Zugriff auf eine Datenbank mit Fehlercodes, Ersatzteilen, Videos und Servicehandbüchern.

## Deine Tools
- **search_error_codes**: Fehlercode oder Fehlerbeschreibung suchen → gibt Fehlercode, Beschreibung, Lösung, Quelle zurück
- **search_parts**: Ersatzteil nach Nummer oder Name suchen → gibt Teilenummer, Name, Hersteller zurück
- **search_videos**: Tutorial-Video nach Gerät oder Thema suchen → gibt Titel, URL zurück
- **semantic_search**: Freitextsuche in Servicehandbüchern für komplexe Fragen

## Regeln
1. Nutze **immer zuerst das passende Tool** – antworte nie aus dem Gedächtnis über Geräte oder Fehlercodes.
2. Gib **nur zurück was in den Tool-Ergebnissen steht** – erfinde keine Lösungen, Teilenummern oder Websiten.
3. Bei `found: false` → antworte: "Keine Informationen in der Datenbank gefunden."
4. Antworte immer auf **Deutsch**.
5. Nutze **Markdown** für strukturierte Antworten (Überschriften, Listen, Fettschrift).

## Antwortformat

### Fehlercode
**Fehler [CODE] – [Beschreibung]** *(Hersteller)*

**Lösung:**
1. Schritt 1
2. Schritt 2

📄 Quelle: [Dokument], Seite [X]

### Ersatzteil
**[Teilenummer] – [Name]** *(Hersteller)*
Kategorie: [Kategorie] | Kompatibel mit: [Modell]

### Video
🎬 **[Titel]**
[URL]

Antworte immer auf Deutsch.""")


# ============================================================================
# Agent
# ============================================================================

class KRAIAgent:
    """KRAI conversational agent using LangGraph create_react_agent."""

    def __init__(self, pool: asyncpg.Pool, ollama_base_url: str | None = None) -> None:
        if ollama_base_url is None:
            ollama_base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

        self.logger = logging.getLogger(__name__)

        ollama_model = (
            os.getenv("OLLAMA_MODEL_CHAT")
            or os.getenv("OLLAMA_MODEL_TEXT", "llama3.2:latest")
        )
        self.logger.info("Connecting to Ollama at %s, model: %s", ollama_base_url, ollama_model)

        llm = ChatOllama(
            model=ollama_model,
            base_url=ollama_base_url,
            temperature=0.0,
            num_ctx=16384,
        )

        tools = create_tools(pool, ollama_base_url)
        memory = MemorySaver()

        self.agent = create_react_agent(
            model=llm,
            tools=tools,
            checkpointer=memory,
            prompt=_SYSTEM_PROMPT,
        )

        self.logger.info("KRAI Agent (LangGraph) initialized successfully")

    async def chat(self, message: str, session_id: str) -> str:
        """Process a message and return the full response."""
        config = {"configurable": {"thread_id": session_id}}
        try:
            result = await self.agent.ainvoke(
                {"messages": [HumanMessage(content=message)]},
                config=config,
            )
            response: str = result["messages"][-1].content
            self.logger.info("Agent response (session=%s): %.120s", session_id, response)
            return response
        except Exception as exc:
            self.logger.error("chat error: %s", exc, exc_info=True)
            return f"Es ist ein Fehler aufgetreten: {exc}"

    async def chat_stream(self, message: str, session_id: str) -> AsyncGenerator[str, None]:
        """Process a message and stream the response token by token."""
        config = {"configurable": {"thread_id": session_id}}
        try:
            async for chunk, metadata in self.agent.astream(
                {"messages": [HumanMessage(content=message)]},
                config=config,
                stream_mode="messages",
            ):
                if (
                    hasattr(chunk, "content")
                    and chunk.content
                    and metadata.get("langgraph_node") == "agent"
                ):
                    yield chunk.content
        except Exception as exc:
            self.logger.error("chat_stream error: %s", exc, exc_info=True)
            yield f"Es ist ein Fehler aufgetreten: {exc}"


# ============================================================================
# FastAPI Router
# ============================================================================

def create_agent_api(pool: asyncpg.Pool) -> APIRouter:
    """Create and return the FastAPI router for the KRAI agent."""
    router = APIRouter(prefix="/agent", tags=["AI Agent"])
    agent = KRAIAgent(pool)

    @router.post("/chat", response_model=ChatResponse)
    async def chat(message: ChatMessage) -> ChatResponse:
        """Chat with the KRAI AI agent (single response)."""
        try:
            response = await agent.chat(message.message, message.session_id)
            return ChatResponse(
                response=response,
                session_id=message.session_id,
                timestamp=datetime.utcnow().isoformat(),
            )
        except Exception as exc:
            logger.error("chat endpoint error: %s", exc)
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @router.post("/chat/stream")
    async def chat_stream(message: ChatMessage) -> StreamingResponse:
        """Chat with the KRAI AI agent (Server-Sent Events streaming)."""
        async def generate() -> AsyncGenerator[str, None]:
            async for chunk in agent.chat_stream(message.message, message.session_id):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    @router.get("/health")
    async def health() -> dict:
        """Health check for the agent."""
        return {"status": "healthy", "agent": "KRAI AI Agent", "version": "2.0.0"}

    return router

