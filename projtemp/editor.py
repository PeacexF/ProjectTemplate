"""Opening the finished project in an editor."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def open_in(dest: Path, command: str) -> str | None:
    """Returns None on success, or why it could not open."""
    parts = command.split()
    if not parts:
        return "no editor command configured"
    if shutil.which(parts[0]) is None:
        return f"{parts[0]!r} not found on PATH"
    try:
        subprocess.Popen([*parts, str(dest)])
    except OSError as exc:
        return str(exc)
    return None
