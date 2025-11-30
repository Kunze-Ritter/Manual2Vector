from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Optional

from scripts._env import load_env


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.database_factory import create_database_adapter  # type: ignore[import]
from services.database_adapter import DatabaseAdapter  # type: ignore[import]


async def create_connected_adapter(database_type: Optional[str] = None) -> DatabaseAdapter:
    """Load env, create a database adapter via the factory, connect it and return it.

    This is the central entry point for scripts that want to talk to the database
    without dealing with Supabase clients directly.
    """

    # Load all configured .env files (including legacy .env.database if present)
    load_env(extra_files=[".env.database"])

    adapter = create_database_adapter(database_type=database_type)
    await adapter.connect()
    return adapter


def run_async(coro: Any) -> Any:
    """Small convenience wrapper so scripts can call async entrypoints easily."""

    return asyncio.run(coro)


async def ensure_postgresql_adapter(adapter: DatabaseAdapter) -> DatabaseAdapter:
    """Ensure that the given adapter supports the PostgreSQL helper methods.

    The current implementation relies on ``execute_query``/``fetch_all`` which are
    provided by ``PostgreSQLAdapter`` but not part of the base interface.
    """

    if not hasattr(adapter, "execute_query"):
        raise RuntimeError(
            "This operation requires a PostgreSQLAdapter with execute_query support."
        )
    return adapter


async def pg_fetch_all(
    adapter: DatabaseAdapter,
    query: str,
    params: Optional[Any] = None,
) -> Any:
    """Helper to run a SELECT statement via PostgreSQLAdapter and return all rows."""

    adapter = await ensure_postgresql_adapter(adapter)
    return await adapter.fetch_all(query, params)  # type: ignore[attr-defined]


async def pg_execute(
    adapter: DatabaseAdapter,
    query: str,
    params: Optional[Any] = None,
) -> Any:
    """Helper to execute arbitrary SQL via PostgreSQLAdapter.execute_query."""

    adapter = await ensure_postgresql_adapter(adapter)
    return await adapter.execute_query(query, params)  # type: ignore[attr-defined]

