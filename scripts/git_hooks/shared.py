#!/usr/bin/env python3
"""Shared helpers for git hooks."""

from __future__ import annotations

import subprocess
import sys


def check_no_pycache_staged() -> int:
    """Block commits that stage Python cache artifacts."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=A"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"Warning: Could not inspect staged files: {exc}", file=sys.stderr)
        return 1

    offending_paths: list[str] = []
    for raw_path in result.stdout.splitlines():
        path = raw_path.strip()
        normalized = path.replace("\\", "/")
        if "__pycache__" in normalized or normalized.endswith((".pyc", ".pyo", ".pyd")):
            offending_paths.append(path)

    if offending_paths:
        print(
            "Error: Commit blocked. Staged cache artifacts are not allowed:",
            file=sys.stderr,
        )
        for path in offending_paths:
            print(f"  - {path}", file=sys.stderr)
        print(
            "Remove them from the index (e.g. `git rm --cached <path>`) and retry.",
            file=sys.stderr,
        )
        return 1

    return 0
