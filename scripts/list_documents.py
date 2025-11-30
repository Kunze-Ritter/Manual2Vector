"""List all documents with their data counts using the async database adapter."""

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
    """List all documents with their data counts via PostgreSQLAdapter."""

    try:
        adapter = await create_connected_adapter(database_type="postgresql")
    except Exception as e:
        print(f"❌ Failed to create database adapter: {e}")
        sys.exit(1)

    print("=" * 100)
    print("All Documents in Database")
    print("=" * 100)

    # Fetch documents via public view mapped to krai_core.documents
    documents = await pg_fetch_all(
        adapter,
        (
            "SELECT id, filename, original_filename, manufacturer, created_at "
            "FROM public.vw_documents "
            "ORDER BY created_at DESC"
        ),
    )

    if not documents:
        print("\n❌ No documents found in database!")
        return

    print(f"\nFound {len(documents)} documents:\n")

    for idx, doc in enumerate(documents, 1):
        doc_id = doc.get("id")
        filename = doc.get("filename") or doc.get("original_filename") or "Unknown"
        manufacturer = doc.get("manufacturer") or "Unknown"
        created_raw = doc.get("created_at")
        created = str(created_raw)[:19] if created_raw is not None else "Unknown"

        print(f"{idx}. {filename}")
        print(f"   ID: {doc_id}")
        print(f"   Manufacturer: {manufacturer}")
        print(f"   Created: {created}")

        if not doc_id:
            print("   ⚠️  No document ID found, skipping data counts")
            print()
            continue

        try:
            counts = {}

            # Error codes via public view
            ec_rows = await pg_fetch_all(
                adapter,
                (
                    "SELECT COUNT(*) AS count "
                    "FROM public.vw_error_codes "
                    "WHERE document_id = :document_id"
                ),
                {"document_id": doc_id},
            )
            counts["error_codes"] = ec_rows[0]["count"] if ec_rows else 0

            # Chunks from documented table
            chunk_rows = await pg_fetch_all(
                adapter,
                (
                    "SELECT COUNT(*) AS count "
                    "FROM krai_intelligence.chunks "
                    "WHERE document_id = :document_id"
                ),
                {"document_id": doc_id},
            )
            counts["chunks"] = chunk_rows[0]["count"] if chunk_rows else 0

            # Products via documented core table
            prod_rows = await pg_fetch_all(
                adapter,
                (
                    "SELECT COUNT(*) AS count "
                    "FROM krai_core.document_products "
                    "WHERE document_id = :document_id"
                ),
                {"document_id": doc_id},
            )
            counts["products"] = prod_rows[0]["count"] if prod_rows else 0

            print(
                "   Data: {ec} error codes, {chunks} chunks, {prod} products".format(
                    ec=counts["error_codes"],
                    chunks=counts["chunks"],
                    prod=counts["products"],
                )
            )
        except Exception as e:
            print(f"   ⚠️  Could not count data: {e}")

        print()


if __name__ == "__main__":
    run_async(main())
