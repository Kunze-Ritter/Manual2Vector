"""
Apply migration 011: rename alert_queue to alerts, create backward-compat view.
Uses POSTGRES_URL from environment (.env / env.database).
Run from project root: python scripts/apply_migration_011_alerts_table.py
"""
import asyncio
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.processors.env_loader import load_all_env_files
load_all_env_files(PROJECT_ROOT)

try:
    import asyncpg
except ImportError:
    print("asyncpg required: pip install asyncpg")
    sys.exit(1)

MIGRATION_FILE = PROJECT_ROOT / "database" / "migrations_postgresql" / "011_rename_alert_queue_to_alerts.sql"


def read_statements(path: Path) -> list:
    """Split SQL file into single statements."""
    text = path.read_text(encoding="utf-8")
    statements = []
    current = []
    depth = 0
    i = 0
    while i < len(text):
        c = text[i]
        if c == "(":
            depth += 1
            current.append(c)
        elif c == ")":
            depth -= 1
            current.append(c)
        elif c == ";" and depth == 0:
            stmt = "".join(current).strip()
            if stmt and not all(
                line.strip().startswith("--") or not line.strip()
                for line in stmt.splitlines()
            ):
                statements.append(stmt + ";")
            current = []
        else:
            current.append(c)
        i += 1
    if current:
        stmt = "".join(current).strip()
        if stmt:
            statements.append(stmt + ";")
    return statements


async def main():
    postgres_url = (
        os.getenv("POSTGRES_URL")
        or os.getenv("DATABASE_CONNECTION_URL")
        or os.getenv("DATABASE_URL")
    )
    if not postgres_url:
        print("POSTGRES_URL (or DATABASE_CONNECTION_URL / DATABASE_URL) not set.")
        sys.exit(1)

    if not MIGRATION_FILE.exists():
        print(f"Migration file not found: {MIGRATION_FILE}")
        sys.exit(1)

    statements = read_statements(MIGRATION_FILE)
    print(f"Applying {len(statements)} statement(s) from {MIGRATION_FILE.name} ...")

    conn = await asyncpg.connect(postgres_url)
    try:
        for i, stmt in enumerate(statements, 1):
            first_line = stmt.split("\n")[0][:60].strip()
            try:
                await conn.execute(stmt)
                print(f"  [{i}/{len(statements)}] OK: {first_line}")
            except asyncpg.PostgresError as e:
                # Idempotent: skip if alert_queue already renamed (now a view or missing)
                msg = str(e).lower()
                if ("alert_queue" in msg and "rename" in stmt.lower() and
                        ("is not a table" in msg or "does not exist" in msg)):
                    print(f"  [{i}/{len(statements)}] SKIP (already applied): {first_line}")
                else:
                    raise
        print("Migration 011 (alerts) applied successfully.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
