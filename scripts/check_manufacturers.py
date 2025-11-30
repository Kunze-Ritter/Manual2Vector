#!/usr/bin/env python3
"""Check manufacturers in database using the async database adapter."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.migration_helpers import (  # type: ignore[import]
    create_connected_adapter,
    pg_fetch_all,
    run_async,
)


async def main() -> None:
    """List manufacturers and check for Lexmark via PostgreSQLAdapter."""

    try:
        adapter = await create_connected_adapter(database_type="postgresql")
    except Exception as e:
        print(f"❌ Failed to create database adapter: {e}")
        sys.exit(1)

    manufacturers = await pg_fetch_all(
        adapter,
        "SELECT id, name FROM public.vw_manufacturers ORDER BY name",
    )

    print("\n" + "=" * 80)
    print("MANUFACTURERS IN DATABASE")
    print("=" * 80)

    for m in manufacturers:
        print(f"  - {m.get('name')} (ID: {m.get('id')})")

    print(f"\nTOTAL: {len(manufacturers)}")
    print("=" * 80)

    # Check for Lexmark specifically
    lexmark = [m for m in manufacturers if (m.get("name") or "").lower().find("lexmark") != -1]
    if lexmark:
        first = lexmark[0]
        print(f"\n✅ Lexmark found: {first.get('name')} (ID: {first.get('id')})")
    else:
        print("\n❌ Lexmark NOT found in database!")
        print("\n💡 Need to create Lexmark manufacturer!")


if __name__ == "__main__":
    run_async(main())
