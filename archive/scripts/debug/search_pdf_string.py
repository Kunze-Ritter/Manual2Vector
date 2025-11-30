#!/usr/bin/env python3
"""Search for a literal string in a PDF using PyMuPDF search_for."""

import argparse
from pathlib import Path
import fitz


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search for a literal string in a PDF")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("needle", help="String to search for")
    parser.add_argument("--max-pages", type=int, default=None, help="Limit pages to scan")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.pdf.exists():
        raise SystemExit(f"PDF not found: {args.pdf}")

    doc = fitz.open(args.pdf)
    limit = args.max_pages if args.max_pages is not None else len(doc)

    found_any = False
    for page_index in range(min(limit, len(doc))):
        page = doc[page_index]
        rects = page.search_for(args.needle)
        if rects:
            found_any = True
            print(f"Found '{args.needle}' on page {page_index + 1} ({len(rects)} occurrence(s))")

    if not found_any:
        print(f"'{args.needle}' not found in first {min(limit, len(doc))} pages")


if __name__ == "__main__":
    main()
