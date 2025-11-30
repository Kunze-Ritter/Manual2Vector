from __future__ import annotations

from scripts.migration_helpers import create_connected_adapter, run_async


async def main() -> None:
    adapter = await create_connected_adapter()
    ok = await adapter.test_connection()
    status = "OK" if ok else "FAILED"
    print(f"Database connection test: {status}")


if __name__ == "__main__":
    run_async(main())

