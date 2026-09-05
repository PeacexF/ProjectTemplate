"""Local git plumbing and remote probing. Returns results, never prints."""

from __future__ import annotations

import enum
import os
import subprocess
from pathlib import Path

from . import ProjtempError

PROBE_TIMEOUT = 20


class RemoteState(enum.Enum):
    EMPTY = "empty"
    NONEMPTY = "nonempty"
    ABSENT = "absent"
    UNKNOWN = "unknown"


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )


def _first_error(proc: subprocess.CompletedProcess) -> str:
    lines = (proc.stderr or proc.stdout).strip().splitlines()
    return lines[-1] if lines else "unknown error"


def user_name() -> str | None:
    try:
        proc = _run(["config", "--get", "user.name"])
    except OSError:
        return None
    return proc.stdout.strip() or None


def init(dest: Path, branch: str = "main") -> None:
    proc = _run(["init", "-b", branch], dest)
    if proc.returncode != 0:
        # git < 2.28 has no -b
        proc = _run(["init"], dest)
        if proc.returncode != 0:
            raise ProjtempError(f"git init failed: {_first_error(proc)}")
        _run(["symbolic-ref", "HEAD", f"refs/heads/{branch}"], dest)


def commit_all(dest: Path, message: str) -> str | None:
    added = _run(["add", "-A"], dest)
    if added.returncode != 0:
        raise ProjtempError(f"git add failed: {_first_error(added)}")
    proc = _run(["commit", "-m", message], dest)
    return None if proc.returncode == 0 else _first_error(proc)


def add_remote(dest: Path, url: str, name: str = "origin") -> str | None:
    proc = _run(["remote", "add", name, url], dest)
    return None if proc.returncode == 0 else _first_error(proc)


def remote_url(dest: Path, name: str = "origin") -> str | None:
    """The URL git actually has for a remote, or None if there isn't one."""
    proc = _run(["remote", "get-url", name], dest)
    return proc.stdout.strip() or None if proc.returncode == 0 else None


def push(dest: Path, branch: str = "main", remote: str = "origin") -> str | None:
    proc = _run(["push", "-u", remote, branch], dest)
    return None if proc.returncode == 0 else _first_error(proc)


def remote_state(url: str) -> RemoteState:
    """Whether a remote exists, and whether it already has refs."""
    env = {
        **os.environ,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_SSH_COMMAND": os.environ.get("GIT_SSH_COMMAND", "ssh -oBatchMode=yes"),
    }
    try:
        probe = subprocess.run(
            ["git", "ls-remote", url],
            capture_output=True,
            text=True,
            check=False,
            env=env,
            timeout=PROBE_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired):
        return RemoteState.UNKNOWN

    if probe.returncode == 0:
        return RemoteState.NONEMPTY if probe.stdout.strip() else RemoteState.EMPTY
    stderr = probe.stderr.lower()
    if "not found" in stderr or "does not exist" in stderr:
        return RemoteState.ABSENT
    return RemoteState.UNKNOWN
