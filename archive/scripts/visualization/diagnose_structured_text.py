#!/usr/bin/env python3
"""Validate structured text extraction for a given PDF page."""

import argparse
from pathlib import Path
from uuid import uuid4
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.processors.text_extractor import TextExtractor


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--page", type=int, default=6, help="1-based page number to inspect")
    parser.add_argument("--snippet", type=int, default=400, help="Characters of plain text to show")
    args = parser.parse_args()

    extractor = TextExtractor()
    page_texts, _, structured_texts = extractor.extract_text(args.pdf, uuid4())

    target_page = args.page
    if target_page not in page_texts:
        raise SystemExit(f"Page {target_page} not found in extracted text (available: {sorted(page_texts.keys())[:10]} ...)")

    text = page_texts[target_page]
    print(f"Page {target_page} text length: {len(text)}")
    print("\n=== Plain text snippet ===")
    print(text[: args.snippet])

    structured = structured_texts.get(target_page)
    if structured:
        print("\n=== Structured section ===")
        print(structured.strip())
    else:
        print("\n(No structured section found on this page)")


if __name__ == "__main__":
    main()
