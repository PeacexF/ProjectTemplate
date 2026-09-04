"""projtemp — copy one of the ProjectTemplate starting points into a new repo."""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import click

__version__ = "0.1.0"

# Anchored at column 0 so the indented boilerplate in the Apache/AGPL license
# text is never rewritten.
COPYRIGHT_RE = re.compile(r"^Copyright \(c\) \d{4}(?:-\d{4})? .*$", re.MULTILINE)

CONFIG_PATH = Path(
    os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
) / "projtemp" / "config.json"

DEFAULT_OWNER = "PeacexF"
DEFAULT_EDITOR = "code"

MAX_SCAN_BYTES = 2 * 1024 * 1024


def load_config() -> dict:
    try:
        with CONFIG_PATH.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as exc:
        click.secho(f"warning: ignoring unreadable config {CONFIG_PATH}: {exc}", fg="yellow", err=True)
        return {}
    return data if isinstance(data, dict) else {}


def save_config(data: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def is_template(path: Path) -> bool:
    """A template is a non-hidden top-level directory holding a LICENSE."""
    return (
        path.is_dir()
        and not path.name.startswith(".")
        and (path / "LICENSE").is_file()
    )


def list_templates(root: Path) -> list[str]:
    return sorted(p.name for p in root.iterdir() if is_template(p))


def _looks_like_root(path: Path) -> bool:
    try:
        return path.is_dir() and any(is_template(p) for p in path.iterdir())
    except OSError:
        return False


def resolve_templates_root(explicit: str | None, config: dict) -> Path:
    """--templates > $PROJTEMP_TEMPLATES > config > the checkout this file lives in."""
    candidates: list[tuple[str, Path]] = []
    if explicit:
        candidates.append(("--templates", Path(explicit)))
    if os.environ.get("PROJTEMP_TEMPLATES"):
        candidates.append(("$PROJTEMP_TEMPLATES", Path(os.environ["PROJTEMP_TEMPLATES"])))
    if config.get("templates"):
        candidates.append((f"{CONFIG_PATH}", Path(str(config["templates"]))))

    for source, candidate in candidates:
        candidate = candidate.expanduser()
        if not candidate.is_dir():
            raise click.ClickException(f"templates root from {source} does not exist: {candidate}")
        if not _looks_like_root(candidate):
            raise click.ClickException(
                f"templates root from {source} holds no templates: {candidate}\n"
                "A template is a non-hidden directory containing a LICENSE file."
            )
        return candidate.resolve()

    checkout = Path(__file__).resolve().parents[1]
    if _looks_like_root(checkout):
        return checkout

    raise click.ClickException(
        "could not find the templates root.\n"
        "Point projtemp at your ProjectTemplate checkout with one of:\n"
        "  projtemp config --set-templates ~/Workspace/Projects/ProjectTemplate\n"
        "  export PROJTEMP_TEMPLATES=~/Workspace/Projects/ProjectTemplate\n"
        "  projtemp --templates <path> ..."
    )


def git_user_name() -> str | None:
    try:
        out = subprocess.run(
            ["git", "config", "--get", "user.name"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    name = out.stdout.strip()
    return name or None


def fill_placeholders(root: Path, name: str, author: str, year: int) -> list[Path]:
    """Rewrite [repo name], [DATE] and the copyright line. Returns changed files."""
    today = _dt.date.today().isoformat()
    changed: list[Path] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        if ".git" in path.parts:
            continue
        try:
            if path.stat().st_size > MAX_SCAN_BYTES:
                continue
            original = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        updated = original.replace("[repo name]", name).replace("[DATE]", today)
        updated = COPYRIGHT_RE.sub(f"Copyright (c) {year} {author}", updated)

        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed.append(path.relative_to(root))

    return changed


def unfilled_markers(root: Path) -> list[str]:
    """Report bracket placeholders we did not know how to fill."""
    found: set[str] = set()
    pattern = re.compile(r"\[(?:yyyy|name of [^\]]+|repo name|DATE)\]")
    for path in sorted(root.rglob("*.md")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for match in pattern.findall(text):
            found.add(f"{path.relative_to(root)}: {match}")
    return sorted(found)


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )


def git_bootstrap(dest: Path, message: str, remote_url: str | None) -> list[str]:
    """git init + initial commit + optional origin. Returns human-readable steps done."""
    done: list[str] = []

    init = run_git(["init", "-b", "main"], dest)
    if init.returncode != 0:
        # git < 2.28 has no -b
        init = run_git(["init"], dest)
        if init.returncode != 0:
            raise click.ClickException(f"git init failed: {init.stderr.strip()}")
        run_git(["symbolic-ref", "HEAD", "refs/heads/main"], dest)
    done.append("git init (branch main)")

    add = run_git(["add", "-A"], dest)
    if add.returncode != 0:
        raise click.ClickException(f"git add failed: {add.stderr.strip()}")

    commit = run_git(["commit", "-m", message], dest)
    if commit.returncode == 0:
        done.append(f"initial commit ({message!r})")
    else:
        detail = (commit.stderr or commit.stdout).strip().splitlines()
        click.secho(
            "warning: initial commit failed: " + (detail[0] if detail else "unknown error"),
            fg="yellow",
            err=True,
        )

    if remote_url:
        remote = run_git(["remote", "add", "origin", remote_url], dest)
        if remote.returncode == 0:
            done.append(f"origin -> {remote_url}")
        else:
            click.secho(
                f"warning: could not add origin: {remote.stderr.strip()}", fg="yellow", err=True
            )

    return done


def open_editor(dest: Path, editor: str) -> bool:
    binary = editor.split()[0]
    if shutil.which(binary) is None:
        click.secho(
            f"warning: editor {binary!r} not found on PATH, not opening", fg="yellow", err=True
        )
        return False
    try:
        subprocess.Popen([*editor.split(), str(dest)])
    except OSError as exc:
        click.secho(f"warning: could not open editor: {exc}", fg="yellow", err=True)
        return False
    return True


class DefaultGroup(click.Group):
    """Let `projtemp <type> <name>` work as shorthand for `projtemp new <type> <name>`."""

    default_command = "new"

    def resolve_command(self, ctx, args):
        try:
            return super().resolve_command(ctx, args)
        except click.UsageError:
            if not args or args[0].startswith("-"):
                raise
            cmd = self.get_command(ctx, self.default_command)
            return self.default_command, cmd, args


@click.group(cls=DefaultGroup, invoke_without_command=True)
@click.version_option(__version__, prog_name="projtemp")
@click.pass_context
def main(ctx: click.Context) -> None:
    """Scatter a new project from the ProjectTemplate starting points.

    \b
      projtemp open-source my-thing      copy the open-source template into ./my-thing
      projtemp list                      show the available types
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        try:
            root = resolve_templates_root(None, load_config())
        except click.ClickException:
            return
        click.echo(f"\nTypes in {root}:")
        for name in list_templates(root):
            click.echo(f"  {name}")


@main.command("list")
@click.option("--templates", "templates_opt", default=None, help="Path to the ProjectTemplate checkout.")
def list_cmd(templates_opt: str | None) -> None:
    """List the available project types."""
    root = resolve_templates_root(templates_opt, load_config())
    names = list_templates(root)
    if not names:
        raise click.ClickException(f"no templates found in {root}")
    click.secho(str(root), fg="cyan")
    for name in names:
        entries = sum(1 for _ in (root / name).rglob("*") if _.is_file())
        click.echo(f"  {name:<22} {entries} files")


@main.command("config")
@click.option("--set-templates", "set_templates", default=None, help="Remember the ProjectTemplate checkout path.")
@click.option("--set-author", "set_author", default=None, help="Remember the name for copyright lines.")
@click.option("--set-owner", "set_owner", default=None, help="Remember the GitHub owner used for origin.")
@click.option("--set-editor", "set_editor", default=None, help="Remember the editor command (default: code).")
def config_cmd(
    set_templates: str | None,
    set_author: str | None,
    set_owner: str | None,
    set_editor: str | None,
) -> None:
    """Show or change the stored defaults."""
    config = load_config()
    changed = False

    if set_templates is not None:
        path = Path(set_templates).expanduser()
        if not _looks_like_root(path):
            raise click.ClickException(f"{path} holds no templates (a template is a dir with a LICENSE)")
        config["templates"] = str(path.resolve())
        changed = True
    for key, value in (("author", set_author), ("owner", set_owner), ("editor", set_editor)):
        if value is not None:
            config[key] = value
            changed = True

    if changed:
        save_config(config)
        click.secho(f"wrote {CONFIG_PATH}", fg="green")

    click.echo(f"config file : {CONFIG_PATH}{'' if CONFIG_PATH.exists() else ' (none yet)'}")
    try:
        click.echo(f"templates   : {resolve_templates_root(None, config)}")
    except click.ClickException as exc:
        click.secho(f"templates   : unresolved — {exc.format_message().splitlines()[0]}", fg="yellow")
    click.echo(f"author      : {config.get('author') or git_user_name() or '(unset)'}")
    click.echo(f"owner       : {config.get('owner', DEFAULT_OWNER)}")
    click.echo(f"editor      : {config.get('editor', DEFAULT_EDITOR)}")


@main.command("new")
@click.argument("type_")
@click.argument("project_name")
@click.option("-C", "--into", "into", default=".", help="Parent directory to create the project in.")
@click.option("--templates", "templates_opt", default=None, help="Path to the ProjectTemplate checkout.")
@click.option("-a", "--author", default=None, help="Name for the copyright line (default: git config user.name).")
@click.option("-y", "--year", type=int, default=None, help="Year for the copyright line (default: this year).")
@click.option("--name", "display_name", default=None, help="Name to substitute for [repo name] (default: the directory name).")
@click.option("--owner", default=None, help=f"GitHub owner for the origin remote (default: {DEFAULT_OWNER}).")
@click.option("--remote", "remote_url", default=None, help="Full origin URL, overriding --owner.")
@click.option("--no-remote", is_flag=True, help="Do not add an origin remote.")
@click.option("--no-git", is_flag=True, help="Do not run git init / commit / remote.")
@click.option("-m", "--message", default="init", show_default=True, help="Initial commit message.")
@click.option("--no-open", is_flag=True, help="Do not open the project in an editor.")
@click.option("--editor", "editor_opt", default=None, help=f"Editor command to open with (default: {DEFAULT_EDITOR}).")
@click.option("--readme", is_flag=True, help="Seed the empty README.md with the project name as an H1.")
@click.option("--force", is_flag=True, help="Copy into the target directory even if it already has files.")
@click.option("-n", "--dry-run", is_flag=True, help="Show what would happen without writing anything.")
def new_cmd(
    type_: str,
    project_name: str,
    into: str,
    templates_opt: str | None,
    author: str | None,
    year: int | None,
    display_name: str | None,
    owner: str | None,
    remote_url: str | None,
    no_remote: bool,
    no_git: bool,
    message: str,
    no_open: bool,
    editor_opt: str | None,
    readme: bool,
    force: bool,
    dry_run: bool,
) -> None:
    """Copy template TYPE into a new project directory PROJECT_NAME."""
    config = load_config()
    root = resolve_templates_root(templates_opt, config)

    available = list_templates(root)
    if type_ not in available:
        raise click.ClickException(
            f"unknown type {type_!r}. Available: {', '.join(available) or '(none)'}"
        )
    src = root / type_

    dest = (Path(into).expanduser() / project_name).resolve()
    if dest.exists():
        if not dest.is_dir():
            raise click.ClickException(f"{dest} exists and is not a directory")
        if any(dest.iterdir()) and not force:
            raise click.ClickException(f"{dest} already exists and is not empty (use --force)")
    if dest == root or root in dest.parents:
        raise click.ClickException(f"refusing to create a project inside the templates root: {dest}")

    name = display_name or dest.name
    author = author or config.get("author") or git_user_name()
    if not author:
        raise click.ClickException(
            "no author name: set one with `git config --global user.name`, "
            "`projtemp config --set-author 'Your Name'`, or --author"
        )
    year = year or _dt.date.today().year

    if no_remote:
        url = None
    elif remote_url:
        url = remote_url
    else:
        url = f"https://github.com/{owner or config.get('owner', DEFAULT_OWNER)}/{dest.name}"

    editor = editor_opt or config.get("editor", DEFAULT_EDITOR)

    click.secho(f"{src.name}", fg="cyan", nl=False)
    click.echo(f" -> {dest}")

    if dry_run:
        click.secho("dry run, nothing written", fg="yellow")
        files = sorted(p.relative_to(src) for p in src.rglob("*") if p.is_file())
        for rel in files:
            click.echo(f"  copy   {rel}")
        click.echo(f"  fill   [repo name] -> {name}")
        click.echo(f"  fill   [DATE] -> {_dt.date.today().isoformat()}")
        click.echo(f"  fill   copyright -> Copyright (c) {year} {author}")
        if not no_git:
            click.echo(f"  git    init, commit {message!r}" + (f", origin {url}" if url else ""))
        if not no_open:
            click.echo(f"  open   {editor}")
        return

    dest.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, dirs_exist_ok=True, symlinks=True)
    n_files = sum(1 for p in dest.rglob("*") if p.is_file())
    click.secho(f"  copied {n_files} files", fg="green")

    if readme:
        readme_path = dest / "README.md"
        if not readme_path.exists() or not readme_path.read_text(encoding="utf-8").strip():
            readme_path.write_text(f"# {name}\n", encoding="utf-8")
            click.secho("  seeded README.md", fg="green")

    changed = fill_placeholders(dest, name, author, year)
    if changed:
        click.secho(f"  filled placeholders in {len(changed)} files", fg="green")
        for rel in changed:
            click.echo(f"    {rel}")
    else:
        click.echo("  no placeholders to fill")

    if not no_git:
        for step in git_bootstrap(dest, message, url):
            click.secho(f"  {step}", fg="green")

    if not no_open and open_editor(dest, editor):
        click.secho(f"  opened in {editor.split()[0]}", fg="green")

    leftovers = unfilled_markers(dest)
    if leftovers:
        click.secho("\nStill to fill in by hand:", fg="yellow")
        for item in leftovers:
            click.echo(f"  {item}")
    if type_ in {"apache-2.0", "agplv3"}:
        click.secho(
            f"\nNote: {type_}/LICENSE is verbatim license text and was left untouched.\n"
            "Put your copyright in a NOTICE file or in source headers instead.",
            fg="yellow",
        )


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
