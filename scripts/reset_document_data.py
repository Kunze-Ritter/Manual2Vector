#!/usr/bin/env python3
"""
reset_document_data.py — Delete all processed document data, preserve videos/products/manufacturers.

Usage:
    python scripts/reset_document_data.py --confirm

PRESERVES: manufacturers, products, product_series, videos, video_products, users
DELETES: documents, chunks, error_codes, solutions, images, links, parts, stage tracking
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from processors.env_loader import load_all_env_files
load_all_env_files(Path(__file__).parent.parent)

import asyncpg

DELETE_STEPS = [
    # Intelligence (depends on chunks/documents)
    ("krai_intelligence.error_codes",    "DELETE FROM krai_intelligence.error_codes"),
    ("krai_intelligence.solutions",      "DELETE FROM krai_intelligence.solutions"),
    ("krai_intelligence.chunks",         "DELETE FROM krai_intelligence.chunks"),
    # Content (except videos)
    ("krai_content.images",              "DELETE FROM krai_content.images"),
    ("krai_content.links",               "DELETE FROM krai_content.links"),
    # Parts
    ("krai_parts.parts_catalog",         "DELETE FROM krai_parts.parts_catalog"),
    # System state
    ("krai_system.stage_tracking",       "DELETE FROM krai_system.stage_tracking"),
    ("krai_system.completion_markers",   "DELETE FROM krai_system.completion_markers"),
    ("krai_system.retries",              "DELETE FROM krai_system.retries"),
    # Documents last
    ("krai_core.documents",              "DELETE FROM krai_core.documents"),
]

PRESERVED = [
    "krai_core.manufacturers",
    "krai_core.products",
    "krai_core.product_series",
    "krai_content.videos",
    "krai_content.video_products",
    "krai_users.*",
]


async def run_reset(dsn: str) -> None:
    conn = await asyncpg.connect(dsn)
    print("\n⚠️  PRESERVED (untouched):")
    for t in PRESERVED:
        print(f"  ✓ {t}")

    print("\n🗑️  Deleting tables in order:")
    try:
        for label, sql in DELETE_STEPS:
            try:
                result = await conn.execute(sql)
                # asyncpg returns "DELETE N" string
                count = result.split()[-1] if result else "?"
                print(f"  ✓ {label}: {count} rows deleted")
            except Exception as e:
                print(f"  ⚠  {label}: {e} (skipping — table may not exist)")
    finally:
        await conn.close()

    print("\n✅ Reset complete. Re-upload documents to reprocess.\n")


def main():
    parser = argparse.ArgumentParser(description="Reset KRAI document data (preserves videos/products/manufacturers)")
    parser.add_argument("--confirm", action="store_true", help="Required flag to execute deletion")
    args = parser.parse_args()

    if not args.confirm:
        print("Dry run — add --confirm to execute.\n")
        print("Will DELETE:")
        for label, _ in DELETE_STEPS:
            print(f"  - {label}")
        print("\nWill PRESERVE:")
        for t in PRESERVED:
            print(f"  - {t}")
        sys.exit(0)

    dsn = os.getenv("DATABASE_URL") or (
        f"postgresql://{os.getenv('POSTGRES_USER','krai')}:{os.getenv('POSTGRES_PASSWORD','krai')}"
        f"@{os.getenv('POSTGRES_HOST','localhost')}:{os.getenv('POSTGRES_PORT','5432')}"
        f"/{os.getenv('POSTGRES_DB','krai')}"
    )

    print(f"Connecting to: {dsn.split('@')[-1]}")  # hide credentials in output
    asyncio.run(run_reset(dsn))


if __name__ == "__main__":
    main()
