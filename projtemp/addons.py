"""The shared pool of pieces that can be dropped into any project."""

from __future__ import annotations

import shutil
from pathlib import Path

from . import ProjtempError
from .templates import POOL_DIR


def pool_root(templates_root: Path) -> Path:
    return templates_root / POOL_DIR


def available(pool: Path) -> list[str]:
    """Every piece in the pool, as you would pass it to --add.

    A directory is a piece once it holds a file or a dotted entry; until then it
    is just a grouping level, so ci/python is a piece and ci is not.
    """
    if not pool.is_dir():
        return []

    found: list[str] = []

    def walk(directory: Path, prefix: str) -> None:
        try:
            entries = sorted(directory.iterdir(), key=lambda entry: entry.name)
        except OSError:
            return
        if prefix and any(e.is_file() or e.name.startswith(".") for e in entries):
            found.append(prefix)
            return
        for entry in entries:
            if entry.is_dir():
                walk(entry, f"{prefix}/{entry.name}" if prefix else entry.name)
            elif not prefix:
                found.append(entry.name)

    walk(pool, "")
    return sorted(found)


def parse(values: tuple[str, ...]) -> list[str]:
    """--add ci/python,disclaimer and repeated --add both end up here."""
    names: list[str] = []
    for value in values:
        for part in value.split(","):
            part = part.strip()
            if part and part not in names:
                names.append(part)
    return names


def resolve(pool: Path, name: str) -> Path:
    if not pool.is_dir():
        raise ProjtempError(f"no shared pool at {pool}, nothing to --add")
    cleaned = name.strip().strip("/")
    if not cleaned:
        raise ProjtempError("empty --add entry")

    root = pool.resolve()
    piece = (pool / cleaned).resolve()
    if piece != root and root not in piece.parents:
        raise ProjtempError(f"--add {name!r} points outside the shared pool")
    if not piece.exists():
        raise ProjtempError(
            f"unknown piece {cleaned!r}. Available: {', '.join(available(pool)) or '(none)'}"
        )
    return piece


def add(piece: Path, dest: Path) -> tuple[list[Path], list[Path]]:
    """Overlay one piece onto the project. Returns (copied, overwritten)."""
    if piece.is_file():
        pairs = [(piece, dest / piece.name)]
    else:
        pairs = [
            (p, dest / p.relative_to(piece)) for p in sorted(piece.rglob("*")) if p.is_file()
        ]

    copied: list[Path] = []
    overwritten: list[Path] = []
    for source, target in pairs:
        rel = target.relative_to(dest)
        if target.exists():
            overwritten.append(rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(rel)
    return copied, overwritten
