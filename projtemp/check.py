"""Auditing the templates themselves. Returns problems, never prints."""

from __future__ import annotations

import re
from pathlib import Path

from . import addons, placeholders, templates

REQUIRED = ("LICENSE", "README.md", ".gitignore")

# Their LICENSE is upstream text carrying its own boilerplate, which the
# placeholder pass deliberately leaves alone. See docs/placeholders.md.
VERBATIM_LICENSE_TYPES = frozenset({"apache-2.0", "agplv3"})

FILLABLE = frozenset({"[repo name]", "[DATE]"})

# A bracket in markdown is usually a link, a heading or changelog syntax. It is
# a placeholder when it shouts (ALL CAPS) or names one of the things a project
# has to fill in, which is the same vocabulary placeholders.UNFILLED_RE uses.
MARKER_RE = re.compile(r"\[[A-Za-z][^\[\]\n]{0,48}\](?![(\[:])")
PLACEHOLDER_WORDS = ("name", "owner", "author", "email", "url", "year", "date", "yyyy", "todo")

COPYRIGHT_LINE_RE = re.compile(r"^Copyright\b.*$", re.MULTILINE)


def looks_like_placeholder(marker: str) -> bool:
    inner = marker[1:-1]
    if inner.upper() == inner and any(c.isalpha() for c in inner):
        return True
    lowered = inner.lower()
    return any(word in lowered for word in PLACEHOLDER_WORDS)


def _text(path: Path) -> str | None:
    try:
        if path.stat().st_size > placeholders.MAX_SCAN_BYTES:
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def check_markers(root: Path, label: str, skip: frozenset = frozenset()) -> list[tuple[str, str]]:
    """Bracket markers in markdown that the placeholder pass cannot fill."""
    problems: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*.md")):
        if not path.is_file() or path.name in skip:
            continue
        text = _text(path)
        if text is None:
            continue
        for marker in sorted({m for m in MARKER_RE.findall(text) if looks_like_placeholder(m)}):
            if marker not in FILLABLE:
                problems.append((f"{label}/{path.relative_to(root)}", f"marker {marker} is not one the CLI can fill"))
    return problems


def check_copyright(root: Path, label: str, skip: frozenset = frozenset()) -> list[tuple[str, str]]:
    """A copyright line the placeholder pass would not rewrite leaks a name."""
    problems: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink() or path.name in skip:
            continue
        text = _text(path)
        if text is None:
            continue
        for line in COPYRIGHT_LINE_RE.findall(text):
            if not placeholders.COPYRIGHT_RE.fullmatch(line):
                problems.append(
                    (f"{label}/{path.relative_to(root)}", f"copyright line will not be rewritten: {line.strip()}")
                )
    return problems


def check_template(root: Path, name: str) -> list[tuple[str, str]]:
    problems = [(name, f"missing {req}") for req in REQUIRED if not (root / req).is_file()]
    # A verbatim license is exempt from both content checks, not just one.
    skip = frozenset({"LICENSE"}) if name in VERBATIM_LICENSE_TYPES else frozenset()
    problems += check_markers(root, name, skip)
    problems += check_copyright(root, name, skip)
    return problems


def run(root: Path) -> list[tuple[str, str]]:
    """Every problem across the templates and the shared pool."""
    problems: list[tuple[str, str]] = []

    found = templates.names(root)
    if not found:
        return [(str(root), "no templates here (a template is a directory holding a LICENSE)")]
    for name in found:
        problems += check_template(root / name, name)

    pool = addons.pool_root(root)
    for piece in addons.available(pool):
        label = f"{templates.POOL_DIR}/{piece}"
        problems += check_markers(pool / piece, label)
        problems += check_copyright(pool / piece, label)

    return problems
