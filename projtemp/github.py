"""GitHub naming conventions. Nothing here talks to the network."""

from __future__ import annotations

HOSTS = frozenset({"github.com", "www.github.com"})

# Types whose repos should not be public by default.
PRIVATE_TYPES = frozenset({"private", "paid"})


def repo_url(owner: str, name: str) -> str:
    return f"https://github.com/{owner}/{name}"


def host(url: str) -> str:
    """The hostname of an https, ssh or scp-style git URL, lowercased."""
    trimmed = url.strip()
    if "://" in trimmed:
        authority = trimmed.split("://", 1)[1].split("/", 1)[0]
        return authority.rsplit("@", 1)[-1].split(":", 1)[0].lower()
    if "@" in trimmed and ":" in trimmed:
        return trimmed.split("@", 1)[1].split(":", 1)[0].lower()
    return ""


def is_github(url: str) -> bool:
    return host(url) in HOSTS


def slug(url: str) -> str:
    """owner/name from a GitHub URL, for display and for gh."""
    trimmed = url.strip().rstrip("/")
    if trimmed.endswith(".git"):
        trimmed = trimmed[: -len(".git")]
    if "://" not in trimmed and ":" in trimmed:
        trimmed = trimmed.split(":", 1)[1]  # scp-style git@host:owner/name
    return "/".join(trimmed.split("/")[-2:])


def default_private(type_: str) -> bool:
    """Visibility a type should get when nothing was asked for explicitly."""
    return type_ in PRIVATE_TYPES


def create_hint(url: str, private: bool = False) -> str:
    visibility = "--private" if private else "--public"
    return f"gh repo create {slug(url)} {visibility} --source . --push"
