"""Copying a template directory into a new project directory."""

from __future__ import annotations

import shutil
from pathlib import Path

from . import ProjtempError


def check_destination(dest: Path, templates_root: Path, force: bool) -> None:
    if dest.exists() and not dest.is_dir():
        raise ProjtempError(f"{dest} exists and is not a directory")
    if dest.is_dir() and any(dest.iterdir()) and not force:
        raise ProjtempError(f"{dest} already exists and is not empty (use --force)")
    if dest == templates_root or templates_root in dest.parents:
        raise ProjtempError(f"refusing to create a project inside the templates root: {dest}")


def files_in(root: Path) -> list[Path]:
    if root.is_file():
        return [Path(root.name)]
    return sorted(p.relative_to(root) for p in root.rglob("*") if p.is_file())


def copy(src: Path, dest: Path) -> int:
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, dirs_exist_ok=True, symlinks=True)
    return sum(1 for p in dest.rglob("*") if p.is_file())


def seed_readme(dest: Path, name: str) -> bool:
    readme = dest / "README.md"
    if readme.exists() and readme.read_text(encoding="utf-8").strip():
        return False
    readme.write_text(f"# {name}\n", encoding="utf-8")
    return True
