"""Finding the templates root and the project types inside it."""

from __future__ import annotations

import os
from pathlib import Path

from . import ProjtempError
from . import config

MARKER = "LICENSE"


def is_template(path: Path) -> bool:
    """A template is a non-hidden top-level directory holding a LICENSE."""
    return path.is_dir() and not path.name.startswith(".") and (path / MARKER).is_file()


def names(root: Path) -> list[str]:
    return sorted(p.name for p in root.iterdir() if is_template(p))


def holds_templates(path: Path) -> bool:
    try:
        return path.is_dir() and any(is_template(p) for p in path.iterdir())
    except OSError:
        return False


def resolve_root(explicit: str | None = None, stored: dict | None = None) -> Path:
    """--templates > $PROJTEMP_TEMPLATES > config > the checkout this package lives in."""
    stored = stored if stored is not None else {}
    candidates: list[tuple[str, Path]] = []
    if explicit:
        candidates.append(("--templates", Path(explicit)))
    if os.environ.get("PROJTEMP_TEMPLATES"):
        candidates.append(("$PROJTEMP_TEMPLATES", Path(os.environ["PROJTEMP_TEMPLATES"])))
    if stored.get("templates"):
        candidates.append((str(config.PATH), Path(str(stored["templates"]))))

    for source, candidate in candidates:
        candidate = candidate.expanduser()
        if not candidate.is_dir():
            raise ProjtempError(f"templates root from {source} does not exist: {candidate}")
        if not holds_templates(candidate):
            raise ProjtempError(
                f"templates root from {source} holds no templates: {candidate}\n"
                f"A template is a non-hidden directory containing a {MARKER} file."
            )
        return candidate.resolve()

    checkout = Path(__file__).resolve().parents[1]
    if holds_templates(checkout):
        return checkout

    raise ProjtempError(
        "could not find the templates root.\n"
        "Point projtemp at your ProjectTemplate checkout with one of:\n"
        "  projtemp config --set-templates ~/Workspace/Projects/ProjectTemplate\n"
        "  export PROJTEMP_TEMPLATES=~/Workspace/Projects/ProjectTemplate\n"
        "  projtemp --templates <path> ..."
    )
