#!/usr/bin/env python3
"""Inspect rawdict spans for potential error codes."""

import argparse
import re
from pathlib import Path

import fitz

CODE_REGEX = re.compile(r"\d{2}[^\dA-Za-z]{0,5}[0-9A-Za-z]{2,3}[^\dA-Za-z]{0,5}[0-9A-Za-z]{2}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--page", type=int, default=6, help="1-based page")
    parser.add_argument("--limit", type=int, default=20, help="Max lines to show")
    args = parser.parse_args()

    doc = fitz.open(args.pdf)
    page = doc[args.page - 1]
    raw = page.get_text("rawdict")

    count = 0
    for block_idx, block in enumerate(raw.get("blocks", [])):
        if block.get("type") != 0:
            continue
        for line_idx, line in enumerate(block.get("lines", [])):
            spans = line.get("spans", [])
            if not spans:
                continue
            joined = "".join(span.get("text", "") for span in spans)
            if not joined.strip():
                continue
            compact = re.sub(r"\s+", "", joined)
            compact = compact.replace("·", ".")
            found = CODE_REGEX.findall(compact)
            if found:
                count += 1
                print(f"block {block_idx} line {line_idx} -> matches {found}")
                print(f"joined: {joined[:120]}")
                print(f"compact: {compact[:120]}")
                print("-")
                if count >= args.limit:
                    return


if __name__ == "__main__":
    main()
