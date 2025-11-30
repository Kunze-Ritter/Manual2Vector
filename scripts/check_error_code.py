"""Check if error code exists in database"""

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
    """Search for an error code and print basic info plus related images."""

    # Determine error code from CLI or fallback default
    code = sys.argv[1] if len(sys.argv) > 1 else "66.60.30"

    try:
        adapter = await create_connected_adapter(database_type="postgresql")
    except Exception as e:
        print(f"❌ Failed to create database adapter: {e}")
        sys.exit(1)

    # Search for error code via documented view
    errors = await pg_fetch_all(
        adapter,
        (
            "SELECT error_code, error_description, manufacturer_id, "
            "document_id, page_number, chunk_id "
            "FROM public.vw_error_codes "
            "WHERE error_code ILIKE :pattern "
            "ORDER BY error_code"
        ),
        {"pattern": f"%{code}%"},
    )

    print(f"Suche nach Fehlercode: {code}")
    print(f"Gefunden: {len(errors)} Ergebnisse\n")

    for i, error in enumerate(errors[:3], 1):
        print(f"{i}. {error.get('error_code')}")
        print(f"   Beschreibung: {error.get('error_description', 'N/A')}")
        print(f"   Document ID: {error.get('document_id')}")
        print(f"   Seite: {error.get('page_number')}")
        print(f"   Chunk ID: {error.get('chunk_id')}")
        print()

    # Check for images for the first result
    if errors:
        first_error = errors[0]
        chunk_id = first_error.get("chunk_id")

        if chunk_id:
            print(f"Prüfe Bilder für Chunk ID: {chunk_id}")
            images = await pg_fetch_all(
                adapter,
                (
                    "SELECT image_url, image_type, page_number, caption "
                    "FROM public.vw_images "
                    "WHERE chunk_id = :chunk_id"
                ),
                {"chunk_id": chunk_id},
            )

            print(f"Gefundene Bilder: {len(images)}\n")
            for img in images:
                print(f"  - {img.get('image_type')}: {img.get('image_url')}")
                print(f"    Caption: {img.get('caption', 'N/A')}")
                print()


if __name__ == "__main__":
    run_async(main())
