#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import fitz


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("needle")
    parser.add_argument("--page", type=int, default=6)
    args = parser.parse_args()

    doc = fitz.open(args.pdf)
    text = doc[args.page - 1].get_text()

    idx = text.find(args.needle)
    if idx == -1:
        print(f"Needle '{args.needle}' not found in plain text")
        surrounding = text[:200]
        print(f"First 200 chars: {surrounding}")
        return

    snippet = text[idx:idx + len(args.needle)]
    print(f"Found at index {idx}: {repr(snippet)}")
    print("Code points:")
    for ch in snippet:
        print(f"  {ch!r} -> U+{ord(ch):04X}")


if __name__ == "__main__":
    main()
