"""Substituting the markers the templates leave behind."""

from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path

# Anchored at column 0 so the indented boilerplate in the Apache/AGPL license
# text is never rewritten.
COPYRIGHT_RE = re.compile(r"^Copyright \(c\) \d{4}(?:-\d{4})? .*$", re.MULTILINE)

UNFILLED_RE = re.compile(r"\[(?:yyyy|name of [^\]]+|repo name|DATE)\]")

MAX_SCAN_BYTES = 2 * 1024 * 1024


def fill(root: Path, name: str, author: str, year: int) -> list[Path]:
    """Rewrite [repo name], [DATE] and the copyright line. Returns changed files."""
    today = _dt.date.today().isoformat()
    changed: list[Path] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink() or ".git" in path.parts:
            continue
        try:
            if path.stat().st_size > MAX_SCAN_BYTES:
                continue
            original = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        updated = original.replace("[repo name]", name).replace("[DATE]", today)
        updated = COPYRIGHT_RE.sub(f"Copyright (c) {year} {author}", updated)

        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed.append(path.relative_to(root))

    return changed


def unfilled(root: Path) -> list[str]:
    """Report bracket placeholders we did not know how to fill."""
    found: set[str] = set()
    for path in sorted(root.rglob("*.md")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for match in UNFILLED_RE.findall(text):
            found.add(f"{path.relative_to(root)}: {match}")
    return sorted(found)
