#!/usr/bin/env python3
import argparse
from pathlib import Path
import re
import fitz

parser = argparse.ArgumentParser()
parser.add_argument("pdf", type=Path)
parser.add_argument("pattern")
parser.add_argument("--page", type=int, default=0)
args = parser.parse_args()

doc = fitz.open(args.pdf)
text = doc[args.page].get_text()
print(f"Page {args.page+1} length {len(text)}")
print(text[:500])
regex = re.compile(args.pattern)
matches = regex.findall(text)
print(f"Matches found: {len(matches)}")
print(matches[:20])
