"""Stored defaults in ~/.config/projtemp/config.json."""

from __future__ import annotations

import json
import os
from pathlib import Path

from . import ProjtempError

DEFAULT_OWNER = "PeacexF"
DEFAULT_EDITOR = "code"

PATH = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "projtemp" / "config.json"


def load() -> dict:
    try:
        with PATH.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as exc:
        raise ProjtempError(f"unreadable config {PATH}: {exc}") from exc
    return data if isinstance(data, dict) else {}


def save(data: dict) -> None:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    with PATH.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
