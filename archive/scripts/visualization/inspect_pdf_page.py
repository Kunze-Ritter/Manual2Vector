#!/usr/bin/env python3
import argparse
from pathlib import Path
import fitz

parser = argparse.ArgumentParser(description="Inspect text of a PDF page")
parser.add_argument("pdf", type=Path)
parser.add_argument("--page", type=int, default=0, help="0-based page index")
parser.add_argument("--length", type=int, default=2000, help="Number of chars to print")
args = parser.parse_args()

if not args.pdf.exists():
    raise SystemExit(f"PDF not found: {args.pdf}")

doc = fitz.open(args.pdf)
if args.page < 0 or args.page >= len(doc):
    raise SystemExit(f"Page {args.page} out of range (0..{len(doc)-1})")

text = doc[args.page].get_text()
print(f"Page {args.page+1}/{len(doc)} text length: {len(text)}")
print(text[: args.length])
