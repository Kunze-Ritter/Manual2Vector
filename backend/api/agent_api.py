"""
KRAI AI Agent API
=================
LangChain-based conversational agent for technical support.

Features:
- Error code search
- Parts search
- Video tutorials
- Service manual search
- Conversation memory
- Streaming responses
"""
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning, module='langchain')

from fastapi import FastAPI, HTTPException, Request, APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, AsyncGenerator
import logging
import json
from datetime import datetime

# LangChain imports
from langchain_ollama import ChatOllama
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import Tool
from langchain import hub
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# Import database adapter
import sys
import os
from pathlib import Path


sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import asyncpg
from services.db_pool import get_pool
from processors.env_loader import load_all_env_files

# Load consolidated environment configuration (supports legacy overrides)
project_root = Path(__file__).parent.parent.parent
load_all_env_files(project_root)

# Configure logging
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

class KRAITools:
    """Tools for the KRAI agent"""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.logger = logging.getLogger(__name__)
        self.logger.info('Agent tools initialized with asyncpg pool')
    
    async def search_error_codes(self, query: str) -> str:
        """
        Search for error codes in the database.
        
        Args:
            query: Error code or search query (e.g., "C9402", "Fehler 10.00.33")
        
        Returns:
            JSON string with error code information
        """
        try:
            self.logger.info(f"Tool called: search_error_codes with query='{query}'")
            
            # Extract error code using the same logic as search_api
            import re
            
            # Priority 1: Patterns with dots (like 10.00.33, 100.01)
            error_code_pattern = r'\b\d+(?:\.\d+)+\b'
            matches = re.findall(error_code_pattern, query, re.IGNORECASE)
            
            # Priority 2: Letter + optional dash + digits (like C-1005, C9402)
            if not matches:
                error_code_pattern = r'\b[A-Z]-?\d{3,}\b'  # At least 3 digits
                matches = re.findall(error_code_pattern, query, re.IGNORECASE)
            
            search_term = matches[0] if matches else query
            
            self.logger.info(f"Extracted error code: '{search_term}' from query: '{query}'")
            
            # Query using direct krai tables with JOIN
            async with self.pool.acquire() as conn:
                error_codes = await conn.fetch(
                    """SELECT ec.error_code, ec.error_description, ec.solution_text, de.page_number, 
                              ec.severity_level, ec.confidence_score, ec.manufacturer_id, ec.document_id
                       FROM krai_intelligence.error_codes ec
                       LEFT JOIN krai_intelligence.chunks de ON ec.chunk_id = de.id
                       WHERE ec.error_code ILIKE $1
                       ORDER BY ec.confidence_score DESC
                       LIMIT 5""",
                    f'%{search_term}%'
                )
            
            if not error_codes:
                return json.dumps({
                    "found": False,
                    "message": f"Fehlercode '{search_term}' nicht in der Datenbank gefunden."
                }, ensure_ascii=False)
            
            # Get manufacturer and document names using array params
            manufacturer_ids = list(set([row['manufacturer_id'] for row in error_codes if row.get('manufacturer_id')]))
            document_ids = list(set([row['document_id'] for row in error_codes if row.get('document_id')]))
            
            manufacturers = {}
            if manufacturer_ids:
                async with self.pool.acquire() as conn:
                    mfr_results = await conn.fetch(
                        "SELECT id, name FROM krai_core.manufacturers WHERE id = ANY($1)",
                        manufacturer_ids
                    )
                manufacturers = {row['id']: row['name'] for row in mfr_results}
            
            documents = {}
            if document_ids:
                async with self.pool.acquire() as conn:
                    doc_results = await conn.fetch(
                        "SELECT id, filename FROM krai_core.documents WHERE id = ANY($1)",
                        document_ids
                    )
                documents = {row['id']: row['filename'] for row in doc_results}
            
            # Format results
            results = []
            for row in error_codes:
                results.append({
                    'error_code': row.get('error_code'),
                    'error_description': row.get('error_description'),
                    'solution_text': row.get('solution_text'),
                    'manufacturer_name': manufacturers.get(row.get('manufacturer_id'), 'Unknown'),
                    'document_filename': documents.get(row.get('document_id'), 'Unknown'),
                    'page_number': row.get('page_number'),
                    'severity_level': row.get('severity_level'),
                    'confidence_score': float(row['confidence_score']) if row['confidence_score'] else 0.0
                })
            
            return json.dumps({
                "found": True,
                "count": len(results),
                "error_codes": results
            }, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"Error in search_error_codes: {e}")
            return json.dumps({
                "found": False,
                "error": str(e)
            })
    
    async def search_parts(self, query: str, manufacturer: Optional[str] = None) -> str:
        """
        Search for spare parts in the database.
        
        Args:
            query: Part name or number
            manufacturer: Optional manufacturer filter
        
        Returns:
            JSON string with parts information
        """
        try:
            self.logger.info(f"Tool called: search_parts with query='{query}', manufacturer='{manufacturer}'")
            
            # Build query with optional manufacturer filter using JOIN
            async with self.pool.acquire() as conn:
                if manufacturer:
                    parts = await conn.fetch(
                        """SELECT p.part_number, p.part_name, p.description, m.name as manufacturer_name, 
                                  p.manufacturer_code, p.price_usd
                           FROM krai_parts.parts_catalog p
                           JOIN krai_core.manufacturers m ON p.manufacturer_id = m.id
                           WHERE (p.part_number ILIKE $1 OR p.part_name ILIKE $2 OR p.description ILIKE $3)
                             AND m.name ILIKE $4
                           LIMIT 10""",
                        f'%{query}%', f'%{query}%', f'%{query}%', f'%{manufacturer}%'
                    )
                else:
                    parts = await conn.fetch(
                        """SELECT p.part_number, p.part_name, p.description, m.name as manufacturer_name, 
                                  p.manufacturer_code, p.price_usd
                           FROM krai_parts.parts_catalog p
                           JOIN krai_core.manufacturers m ON p.manufacturer_id = m.id
                           WHERE p.part_number ILIKE $1 OR p.part_name ILIKE $2 OR p.description ILIKE $3
                           LIMIT 10""",
                        f'%{query}%', f'%{query}%', f'%{query}%'
                    )
            
            if not parts:
                return json.dumps({
                    "found": False,
                    "message": f"Keine Ersatzteile für '{query}' gefunden."
                }, ensure_ascii=False)
            
            # Format results
            results = []
            for row in parts:
                results.append({
                    'part_number': row.get('part_number'),
                    'part_name': row.get('part_name'),
                    'description': row.get('description'),
                    'manufacturer_name': row.get('manufacturer_name'),
                    'price_usd': row.get('price_usd')
                })
            
            return json.dumps({
                "found": True,
                "count": len(results),
                "parts": results
            }, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"Error in search_parts: {e}")
            return json.dumps({
                "found": False,
                "error": str(e)
            })
    
    async def semantic_search(self, query: str, limit: int = 5) -> str:
        """
        Semantic search across all content using embeddings.
        Finds relevant information even if exact keywords don't match.
        
        Args:
            query: Search query in natural language
            limit: Maximum number of results (default: 5)
        
        Returns:
            JSON string with search results
        """
        try:
            self.logger.info(f"Tool called: semantic_search with query='{query}', limit={limit}")
            
            # 1. Generate embedding for query using Ollama
            import requests
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            embedding_model = os.getenv("OLLAMA_MODEL_EMBEDDING", "nomic-embed-text:latest")
            
            self.logger.info(f"Generating embedding with {embedding_model}")
            
            embedding_response = requests.post(
                f"{ollama_url}/api/embeddings",
                json={
                    "model": embedding_model,
                    "prompt": query
                }
            )
            
            if embedding_response.status_code != 200:
                return json.dumps({
                    "found": False,
                    "error": f"Embedding generation failed: {embedding_response.text}"
                })
            
            query_embedding = embedding_response.json()['embedding']
            
            # 2. Search using direct PostgreSQL vector similarity
            async with self.pool.acquire() as conn:
                results_data = await conn.fetch(
                    """
                    SELECT content, metadata, document_id, id as chunk_id,
                           1 - (embedding <=> $1::vector) as similarity
                    FROM krai_intelligence.chunks
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> $1::vector
                    LIMIT $2
                    """,
                    query_embedding,
                    limit
                )
            
            if not results_data:
                return json.dumps({
                    "found": False,
                    "message": f"Keine relevanten Informationen für '{query}' gefunden."
                }, ensure_ascii=False)
            
            # 3. Format results
            results = []
            for row in results_data:
                results.append({
                    'content': row.get('content'),
                    'similarity': round(row.get('similarity', 0), 4),
                    'metadata': row.get('metadata', {}),
                    'document_id': str(row.get('document_id', '')),
                    'chunk_id': str(row.get('chunk_id', ''))
                })
            
            self.logger.info(f"Found {len(results)} semantic search results")
            
            return json.dumps({
                "found": True,
                "count": len(results),
                "results": results
            }, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"Error in semantic_search: {e}", exc_info=True)
            return json.dumps({
                "error": str(e),
                "found": False
            })
    
    async def search_videos(self, query: str) -> str:
        """
        Search for repair video tutorials.
        
        Args:
            query: Search query for videos
        
        Returns:
            JSON string with video information
        """
        try:
            self.logger.info(f"Tool called: search_videos with query='{query}'")
            
            # Query using direct krai table
            async with self.pool.acquire() as conn:
                videos = await conn.fetch(
                    """SELECT title, url, description, duration, manufacturer_id, model_series
                       FROM krai_content.videos 
                       WHERE title ILIKE $1 OR description ILIKE $2 OR model_series ILIKE $3
                       LIMIT 10""",
                    f'%{query}%', f'%{query}%', f'%{query}%'
                )
            
            if not videos:
                return json.dumps({
                    "found": False,
                    "message": f"Keine Videos für '{query}' gefunden."
                }, ensure_ascii=False)
            
            # Get manufacturer names using array param or subquery
            manufacturer_ids = list(set([row['manufacturer_id'] for row in videos if row.get('manufacturer_id')]))
            manufacturers = {}
            if manufacturer_ids:
                async with self.pool.acquire() as conn:
                    mfr_results = await conn.fetch(
                        "SELECT id, name FROM krai_core.manufacturers WHERE id = ANY($1)",
                        manufacturer_ids
                    )
                manufacturers = {row['id']: row['name'] for row in mfr_results}
            
            # Format results
            results = []
            for row in videos:
                results.append({
                    'title': row.get('title'),
                    'url': row.get('url'),
                    'description': row.get('description'),
                    'duration': row.get('duration'),
                    'manufacturer': manufacturers.get(row.get('manufacturer_id')),
                    'model_series': row.get('model_series')
                })
            
            return json.dumps({
                "found": True,
                "count": len(results),
                "videos": results
            }, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"Error in search_videos: {e}")
            return json.dumps({
                "found": False,
                "error": str(e)
            })
    
    def get_tools(self) -> List[Tool]:
        """Get all tools for the agent"""
        return [
            Tool(
                name="search_error_codes",
                func=lambda x: x,  # Placeholder for sync signature
                coroutine=self.search_error_codes,  # Actual async implementation
                description="""
                Suche nach Fehlercodes in der Datenbank.
                Verwende dieses Tool wenn der Benutzer nach einem Fehlercode fragt.
                
                Eingabe: Fehlercode oder Suchbegriff (z.B. "C9402", "Fehler 10.00.33", "Error C-1005")
                
                Das Tool extrahiert automatisch den Fehlercode und sucht in der Datenbank.
                """
            ),
            Tool(
                name="search_parts",
                func=lambda x: x,  # Placeholder for sync signature
                coroutine=self.search_parts,  # Actual async implementation
                description="""
                Suche nach Ersatzteilen in der Datenbank.
                Verwende dieses Tool wenn der Benutzer nach Ersatzteilen, Komponenten oder Teilenummern fragt.
                
                Eingabe: Teilename oder Teilenummer (z.B. "Fuser Unit", "Toner", "A1234567")
                """
            ),
            Tool(
                name="search_videos",
                func=lambda x: x,  # Placeholder for sync signature
                coroutine=self.search_videos,  # Actual async implementation
                description="""
                Suche nach Reparatur-Videos und Tutorials.
                Verwende dieses Tool wenn der Benutzer nach Videos, Anleitungen oder Tutorials fragt.
                
                Eingabe: Suchbegriff (z.B. "Fuser austauschen", "Toner wechseln", "HP E877")
                """
            ),
            Tool(
                name="semantic_search",
                func=lambda x: x,  # Placeholder for sync signature
                coroutine=self.semantic_search,  # Actual async implementation
                description="""
                Semantische Suche über alle Inhalte mit KI-Embeddings.
                Verwende dieses Tool für allgemeine Fragen oder wenn die anderen Tools keine Ergebnisse liefern.
                Findet relevante Informationen auch wenn die genauen Keywords nicht übereinstimmen.
                
                Eingabe: Natürlichsprachige Frage (z.B. "Wie behebe ich Papier-Staus?", "Drucker druckt nicht")
                """
            )
        ]


# ============================================================================
# Agent Setup
# ============================================================================

class KRAIAgent:
    """KRAI conversational agent"""
    
    def __init__(self, pool: asyncpg.Pool, ollama_base_url: str = None):
        self.pool = pool
        
        # Get Ollama URL from environment
        if ollama_base_url is None:
            ollama_base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        
        self.ollama_base_url = ollama_base_url
        self.logger = logging.getLogger(__name__)
        self.logger.info('Agent initialized with asyncpg pool')
        
        # Store for chat histories (session_id -> InMemoryChatMessageHistory)
        self.chat_histories = {}
        
        # Initialize LLM
        # Use OLLAMA_MODEL_CHAT for agent (better at conversation)
        # Fallback to OLLAMA_MODEL_TEXT for backwards compatibility
        ollama_model = os.getenv("OLLAMA_MODEL_CHAT") or os.getenv("OLLAMA_MODEL_TEXT", "llama3.2:latest")
        self.logger.info(f"Connecting to Ollama at: {ollama_base_url}")
        self.logger.info(f"Using Ollama model for chat: {ollama_model}")
        
        self.llm = ChatOllama(
            model=ollama_model,
            base_url=ollama_base_url,
            temperature=0.0,  # No creativity - only facts
            num_ctx=16384  # Balanced context (16k) - 32k was too much for GPU
        )
        
        # Initialize tools
        self.tools_manager = KRAITools(pool)
        self.tools = self.tools_manager.get_tools()
        
        # Create prompt for tool-calling agent (simpler, works better with Ollama)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Du bist ein Datenbank-Assistent. Du gibst NUR zurück was in den Tool-Ergebnissen steht.

REGELN:
1. Rufe das passende Tool auf
2. Kopiere die Daten aus dem Tool-Ergebnis 1:1
3. Erfinde NICHTS - keine Lösungen, keine Websites, keine Tipps
4. Wenn found=false: sage "Keine Informationen in der Datenbank gefunden"

BEISPIEL für Parts:
Tool gibt: {{"found": true, "parts": [{{"part_number": "41X5345", "part_name": "E-Teil", "manufacturer_name": "Lexmark"}}]}}
Du antwortest: Ersatzteil 41X5345 - E-Teil von Lexmark

BEISPIEL für Error Codes:
Tool gibt: {{"found": true, "error_codes": [{{"error_code": "C9402", "error_description": "LED Error", "solution_text": "1. Turn off 2. Check cable", "manufacturer_name": "Konica Minolta", "document_filename": "KM.pdf", "page_number": 450}}]}}
Du antwortest:
Fehler C9402 - LED Error (Konica Minolta)
Lösung:
1. Turn off
2. Check cable
Quelle: KM.pdf, Seite 450

Antworte auf Deutsch."""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create tool-calling agent (better for Ollama than ReAct)
        self.agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        self.logger.info("KRAI Agent initialized successfully")
    
    def get_chat_history(self, session_id: str) -> InMemoryChatMessageHistory:
        """Get or create chat history for a session (new LangChain API)"""
        if session_id not in self.chat_histories:
            self.chat_histories[session_id] = InMemoryChatMessageHistory()
        return self.chat_histories[session_id]
    
    def chat(self, message: str, session_id: str) -> str:
        """
        Process a chat message and return response
        
        Args:
            message: User's message
            session_id: Session ID for conversation memory
        
        Returns:
            Agent's response
        """
        try:
            self.logger.info(f"Processing message for session {session_id}: {message}")
            
            # Get chat history for this session
            chat_history = self.get_chat_history(session_id)
            
            # Build context with history
            context = ""
            if chat_history.messages:
                context = "\n\nVorherige Konversation:\n"
                for msg in chat_history.messages[-6:]:  # Last 3 exchanges
                    role = "User" if msg.type == "human" else "Assistant"
                    context += f"{role}: {msg.content}\n"
                context += "\nAktuelle Frage:\n"
            
            # Create agent executor (no memory parameter - deprecated!)
            agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=True,
                max_iterations=30,
                max_execution_time=300,
                handle_parsing_errors=True,
                return_intermediate_steps=False
            )
            
            # Run agent with context
            full_input = context + message if context else message
            response = agent_executor.invoke({"input": full_input})
            
            # Save to history (new API)
            chat_history.add_user_message(message)
            chat_history.add_ai_message(response['output'])
            
            self.logger.info(f"Agent response: {response['output']}")
            
            return response['output']
            
        except Exception as e:
            self.logger.error(f"Error in chat: {e}", exc_info=True)
            return f"Es ist ein Fehler aufgetreten: {str(e)}"
    
    async def chat_stream(self, message: str, session_id: str) -> AsyncGenerator[str, None]:
        """
        Process a chat message and stream response
        
        Args:
            message: User's message
            session_id: Session ID for conversation memory
        
        Yields:
            Chunks of the agent's response
        """
        try:
            self.logger.info(f"Streaming message for session {session_id}: {message}")
            
            # Get chat history for this session
            chat_history = self.get_chat_history(session_id)
            
            # Build context with history
            context = ""
            if chat_history.messages:
                context = "\n\nVorherige Konversation:\n"
                for msg in chat_history.messages[-6:]:  # Last 3 exchanges
                    role = "User" if msg.type == "human" else "Assistant"
                    context += f"{role}: {msg.content}\n"
                context += "\nAktuelle Frage:\n"
            
            # Create agent executor (no memory parameter - deprecated!)
            agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=True,
                max_iterations=30,
                max_execution_time=300,
                handle_parsing_errors=True,
                return_intermediate_steps=False
            )
            
            # Stream response with context
            full_input = context + message if context else message
            full_response = ""
            async for chunk in agent_executor.astream({"input": full_input}):
                if "output" in chunk:
                    full_response += chunk["output"]
                    yield chunk["output"]
            
            # Save to history after streaming completes
            chat_history.add_user_message(message)
            chat_history.add_ai_message(full_response)
            
        except Exception as e:
            self.logger.error(f"Error in chat_stream: {e}", exc_info=True)
            yield f"Es ist ein Fehler aufgetreten: {str(e)}"


# ============================================================================
# FastAPI Application
# ============================================================================

def create_agent_api(pool: asyncpg.Pool) -> APIRouter:
    """Create API router for the agent (to be included in main app)"""
    
    print("DEBUG: Creating Agent API router...")
    router = APIRouter(
        prefix="/agent",
        tags=["AI Agent"]
    )
    
    # Initialize agent
    agent = KRAIAgent(pool)
    
    @router.post("/chat", response_model=ChatResponse)
    async def chat(message: ChatMessage):
        """
        Chat with the AI agent
        
        Args:
            message: Chat message with session ID
        
        Returns:
            Agent's response
        """
        try:
            response = agent.chat(message.message, message.session_id)
            
            return ChatResponse(
                response=response,
                session_id=message.session_id,
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error in chat endpoint: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/chat/stream")
    async def chat_stream(message: ChatMessage):
        """
        Chat with the AI agent (streaming)
        
        Args:
            message: Chat message with session ID
        
        Returns:
            Streaming response
        """
        try:
            async def generate():
                async for chunk in agent.chat_stream(message.message, message.session_id):
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
            
        except Exception as e:
            logger.error(f"Error in chat_stream endpoint: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/health")
    async def health():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "agent": "KRAI AI Agent",
            "version": "1.0.0"
        }
    
    return router
