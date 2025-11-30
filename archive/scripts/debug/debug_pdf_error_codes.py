#!/usr/bin/env python3
"""Quick diagnostic helper to inspect error codes in a PDF document."""

import argparse
import re
from collections import defaultdict
from pathlib import Path

import fitz  # PyMuPDF


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect error codes in a PDF")
    parser.add_argument("pdf", type=Path, help="Path to the PDF file")
    parser.add_argument(
        "--pattern",
        default=r"\b\d{2}\.\d{2,3}\.\d{2}\b",
        help="Regex pattern to match error codes (default: HP style)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional limit on pages to scan for faster debugging",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=20,
        help="Number of sample codes to print (default: 20)",
    )
    parser.add_argument(
        "--ignore-spaces",
        action="store_true",
        help="Normalize whitespace by removing spaces before matching (helps with hidden spaces)",
    )
    return parser.parse_args()


def normalize_text(text: str, ignore_spaces: bool) -> str:
    if not ignore_spaces:
        return text
    return text.replace(" ", "")


def main() -> None:
    args = parse_args()
    if not args.pdf.exists():
        raise SystemExit(f"PDF not found: {args.pdf}")

    doc = fitz.open(args.pdf)
    pattern = re.compile(args.pattern)

    matches: dict[str, set[int]] = defaultdict(set)

    page_limit = args.max_pages if args.max_pages is not None else len(doc)

    for page_index in range(min(page_limit, len(doc))):
        page = doc[page_index]
        text = normalize_text(page.get_text(), args.ignore_spaces)
        for code in pattern.findall(text):
            matches[code].add(page_index + 1)  # Convert to 1-based page number

    total_codes = len(matches)
    total_occurrences = sum(len(pages) for pages in matches.values())

    print(f"PDF: {args.pdf}")
    print(f"Pattern: {pattern.pattern}")
    print(f"Pages scanned: {min(page_limit, len(doc))}/{len(doc)}")
    print(f"Unique codes: {total_codes}")
    print(f"Total occurrences: {total_occurrences}")

    if total_codes == 0:
        return

    print("\nSample codes:")
    for code, pages in sorted(matches.items())[: args.sample]:
        page_list = ", ".join(str(p) for p in sorted(pages))
        print(f"  {code} -> pages {page_list}")


if __name__ == "__main__":
    main()
