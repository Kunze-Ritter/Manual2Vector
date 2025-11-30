"""Simple PostgreSQL connection test for KRAI Engine.

Uses the shared DatabaseService adapter so it works with both
PostgreSQLAdapter (local Postgres) and SupabaseAdapter (with direct
Postgres URL configured).
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List
from urllib.parse import urlparse, urlunparse

# Ensure project root is on sys.path so ``scripts._env`` can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts._env import load_env
from backend.services.database_service import DatabaseService


async def main() -> None:
    print("=" * 70)
    print("KRAI PostgreSQL Connection Test")
    print("=" * 70)

    loaded_files: List[str] = load_env()
    if loaded_files:
        print(f"Loaded env files: {', '.join(loaded_files)}")
    else:
        print("No env files explicitly loaded via loader (falling back to process env).")

    # Prefer PostgreSQL; Supabase remains optional via DATABASE_TYPE override
    database_type = os.getenv("DATABASE_TYPE", "postgresql").lower()
    if database_type != "postgresql":
        print(f"DATABASE_TYPE is set to '{database_type}' (override). Using that for adapter factory.")
    else:
        print("Using PostgreSQL adapter (DATABASE_TYPE=postgresql).")

    # Let the factory resolve the actual connection URL from env
    # DATABASE_CONNECTION_URL / POSTGRES_URL / DATABASE_URL
    postgres_url = (
        os.getenv("DATABASE_CONNECTION_URL")
        or os.getenv("POSTGRES_URL")
        or os.getenv("DATABASE_URL")
    )

    original_postgres_url = postgres_url

    # When running this script on the host (outside Docker), the Docker
    # hostname "krai-postgres" is not resolvable. Map it to localhost so
    # the test connects to the forwarded port on the host instead.
    if postgres_url:
        parsed = urlparse(postgres_url)
        host = parsed.hostname

        # Simple Docker detection: /.dockerenv exists inside containers
        running_in_docker = os.path.exists("/.dockerenv") or os.getenv("KRAI_IN_DOCKER") == "1"

        if host in ("krai-postgres", "postgres") and not running_in_docker:
            userinfo = ""
            if parsed.username:
                if parsed.password:
                    userinfo = f"{parsed.username}:{parsed.password}@"
                else:
                    userinfo = f"{parsed.username}@"

            port_str = f":{parsed.port}" if parsed.port else ""
            netloc = f"{userinfo}127.0.0.1{port_str}"
            parsed = parsed._replace(netloc=netloc)
            postgres_url = urlunparse(parsed)

            print(
                "Overriding Postgres host for local test: "
                f"{original_postgres_url!r} -> {postgres_url!r}"
            )

    print(f"Effective POSTGRES URL: {repr(postgres_url)[:80] if postgres_url else 'None'}")

    db = DatabaseService(
        supabase_url=None,
        supabase_key=None,
        postgres_url=postgres_url,
        database_type="postgresql" if database_type == "postgresql" else database_type,
    )

    print("Connecting to database ...")
    await db.connect()
    print("✅ Connection established.")

    # Simple sanity query
    rows = await db.execute_query("SELECT 1 AS test")
    print(f"SELECT 1 result: {rows}")

    # Check KRAI schemas and a few key tables
    schemas = await db.execute_query(
        "SELECT schema_name FROM information_schema.schemata "
        "WHERE schema_name LIKE 'krai_%' ORDER BY schema_name"
    )
    print("\nAvailable KRAI schemas:")
    for row in schemas:
        print(f"  - {row.get('schema_name')}")

    docs_count_rows = await db.execute_query(
        "SELECT COUNT(*) AS cnt FROM krai_core.documents"
    )
    docs_count = docs_count_rows[0]["cnt"] if docs_count_rows else 0
    print(f"\nDocument count in krai_core.documents: {docs_count}")

    print("\nConnection test finished.\n")


if __name__ == "__main__":
    asyncio.run(main())
