"""GitHub naming conventions. Nothing here talks to the network."""

from __future__ import annotations


def repo_url(owner: str, name: str) -> str:
    return f"https://github.com/{owner}/{name}"


def slug(url: str) -> str:
    """owner/name from a GitHub URL, for display."""
    trimmed = url.rstrip("/")
    if trimmed.endswith(".git"):
        trimmed = trimmed[: -len(".git")]
    return "/".join(trimmed.split("/")[-2:])


def create_hint(url: str) -> str:
    return f"gh repo create {slug(url)} --source . --push"
