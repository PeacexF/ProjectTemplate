"""The GitHub CLI. The only module that creates anything on GitHub."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

AUTH_TIMEOUT = 20
CREATE_TIMEOUT = 120


def unusable() -> str | None:
    """Why `gh` cannot create a repo, or None if it can."""
    if shutil.which("gh") is None:
        return "gh is not on PATH (https://cli.github.com)"
    try:
        proc = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            check=False,
            timeout=AUTH_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "could not run `gh auth status`"
    if proc.returncode != 0:
        return "gh is not logged in (run: gh auth login)"
    return None


def create_args(slug: str, private: bool, push: bool) -> list[str]:
    """The gh invocation, kept separate so it can be shown and tested."""
    args = ["gh", "repo", "create", slug, "--private" if private else "--public", "--source", "."]
    if push:
        args.append("--push")
    return args


def create_repo(slug: str, private: bool, push: bool, cwd: Path) -> str | None:
    """Create the repo and let gh wire up origin. Returns None or why it failed."""
    try:
        proc = subprocess.run(
            create_args(slug, private, push),
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=CREATE_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return f"gh repo create timed out after {CREATE_TIMEOUT}s"
    except OSError as exc:
        return str(exc)
    if proc.returncode == 0:
        return None
    lines = (proc.stderr or proc.stdout).strip().splitlines()
    return lines[-1] if lines else "unknown error"
