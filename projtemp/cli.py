"""The command line surface. The only module that prints."""

from __future__ import annotations

import datetime as _dt
import sys
from pathlib import Path

import click

from . import (
    ProjtempError,
    __version__,
    addons,
    check,
    config,
    editor,
    gh,
    git,
    github,
    placeholders,
    scaffold,
    templates,
)


def step(text: str) -> None:
    click.secho(f"  {text}", fg="green")


def warn(text: str) -> None:
    click.secho(f"  {text}", fg="yellow")


class DefaultGroup(click.Group):
    """Let `projtemp <type> <name>` work as shorthand for `projtemp new <type> <name>`."""

    default_command = "new"

    def resolve_command(self, ctx, args):
        try:
            return super().resolve_command(ctx, args)
        except click.UsageError:
            if not args or args[0].startswith("-"):
                raise
            return self.default_command, self.get_command(ctx, self.default_command), args

    def invoke(self, ctx):
        try:
            return super().invoke(ctx)
        except ProjtempError as exc:
            raise click.ClickException(str(exc)) from exc


@click.group(cls=DefaultGroup, invoke_without_command=True)
@click.version_option(__version__, prog_name="projtemp")
@click.pass_context
def main(ctx: click.Context) -> None:
    """Scatter a new project from the ProjectTemplate starting points.

    \b
      projtemp open-source my-thing      copy the open-source template into ./my-thing
      projtemp list                      show the available types
    """
    if ctx.invoked_subcommand is not None:
        return
    click.echo(ctx.get_help())
    try:
        root = templates.resolve_root(stored=config.load())
    except ProjtempError:
        return
    click.echo(f"\nTypes in {root}:")
    for name in templates.names(root):
        click.echo(f"  {name}")


@main.command("list")
@click.option("--templates", "templates_opt", default=None, help="Path to the ProjectTemplate checkout.")
@click.option("--pool", "pool_only", is_flag=True, help="List the --add pieces instead of the project types.")
@click.option("--plain", is_flag=True, help="Names only, one per line, for scripting.")
def list_cmd(templates_opt: str | None, pool_only: bool, plain: bool) -> None:
    """List the available project types, or the pieces in the shared pool."""
    root = templates.resolve_root(templates_opt, config.load())
    pool = addons.pool_root(root)

    if pool_only:
        pieces = addons.available(pool)
        if not pieces:
            raise ProjtempError(f"no pieces found in {pool}")
        if plain:
            for name in pieces:
                click.echo(name)
            return
        click.secho(f"{pool}  (--add)", fg="cyan")
        for name in pieces:
            click.echo(f"  {name:<22} {len(scaffold.files_in(pool / name))} files")
        return

    found = templates.names(root)
    if not found:
        raise ProjtempError(f"no templates found in {root}")
    if plain:
        for name in found:
            click.echo(name)
        return

    click.secho(str(root), fg="cyan")
    for name in found:
        click.echo(f"  {name:<22} {len(scaffold.files_in(root / name))} files")

    pieces = addons.available(pool)
    if pieces:
        click.secho(f"\n{pool}  (--add)", fg="cyan")
        for name in pieces:
            click.echo(f"  {name:<22} {len(scaffold.files_in(pool / name))} files")


@main.command("check")
@click.option("--templates", "templates_opt", default=None, help="Path to the ProjectTemplate checkout.")
def check_cmd(templates_opt: str | None) -> None:
    """Audit the templates for missing files and markers the CLI cannot fill."""
    root = templates.resolve_root(templates_opt, config.load())
    problems = check.run(root)
    click.secho(str(root), fg="cyan")

    if not problems:
        types = templates.names(root)
        pieces = addons.available(addons.pool_root(root))
        step(f"ok — {len(types)} types, {len(pieces)} pieces")
        return

    width = max(len(where) for where, _ in problems)
    for where, message in problems:
        click.secho(f"  {where:<{width}}", fg="yellow", nl=False)
        click.echo(f"  {message}")
    raise ProjtempError(f"{len(problems)} problem{'' if len(problems) == 1 else 's'} found")


@main.command("config")
@click.option("--set-templates", "set_templates", default=None, help="Remember the ProjectTemplate checkout path.")
@click.option("--set-author", "set_author", default=None, help="Remember the name for copyright lines.")
@click.option("--set-owner", "set_owner", default=None, help="Remember the GitHub owner used for origin.")
@click.option("--set-editor", "set_editor", default=None, help="Remember the editor command.")
def config_cmd(
    set_templates: str | None,
    set_author: str | None,
    set_owner: str | None,
    set_editor: str | None,
) -> None:
    """Show or change the stored defaults."""
    stored = config.load()
    changed = False

    if set_templates is not None:
        path = Path(set_templates).expanduser()
        if not templates.holds_templates(path):
            raise ProjtempError(f"{path} holds no templates (a template is a dir with a LICENSE)")
        stored["templates"] = str(path.resolve())
        changed = True
    for key, value in (("author", set_author), ("owner", set_owner), ("editor", set_editor)):
        if value is not None:
            stored[key] = value
            changed = True

    if changed:
        config.save(stored)
        click.secho(f"wrote {config.PATH}", fg="green")

    click.echo(f"config file : {config.PATH}{'' if config.PATH.exists() else ' (none yet)'}")
    try:
        click.echo(f"templates   : {templates.resolve_root(stored=stored)}")
    except ProjtempError as exc:
        click.secho(f"templates   : unresolved — {str(exc).splitlines()[0]}", fg="yellow")
    click.echo(f"author      : {stored.get('author') or git.user_name() or '(unset)'}")
    click.echo(f"owner       : {stored.get('owner', config.DEFAULT_OWNER)}")
    click.echo(f"editor      : {stored.get('editor', config.DEFAULT_EDITOR)}")


def create_remote(dest: Path, url: str, push: bool, private: bool) -> None:
    """The --create path: make the repo, and let gh wire up origin itself."""
    if not github.is_github(url):
        warn(f"--create only works with github.com remotes, not {url}")
        return
    blocked = gh.unusable()
    if blocked:
        warn(f"cannot create the repo: {blocked}")
        warn(f"create it with: {github.create_hint(url, private)}")
        return

    slug = github.slug(url)
    failure = gh.create_repo(slug, private, push, dest)
    if failure:
        warn(f"gh repo create failed: {failure}")
        warn(f"try it by hand: {github.create_hint(url, private)}")
        return

    step(f"created {'private' if private else 'public'} repo {slug}")
    # gh picks the protocol from the user's git config, so report what landed.
    step(f"origin -> {git.remote_url(dest) or url}")
    if push:
        step("pushed main -> origin")


def attach_remote(dest: Path, url: str, push: bool, force: bool, create: bool, private: bool) -> None:
    state = git.RemoteState.UNKNOWN if force else git.remote_state(url)

    if not force and state is git.RemoteState.ABSENT:
        if create:
            create_remote(dest, url, push, private)
            return
        warn(f"{url} does not exist, origin not added")
        warn(f"create it with: {github.create_hint(url, private)}")
        return
    if not force and state is git.RemoteState.UNKNOWN:
        warn(f"could not reach {url}, origin not added")
        return

    failure = git.add_remote(dest, url)
    if failure:
        warn(f"could not add origin: {failure}")
        return
    step(f"origin -> {url}")

    if not push or state is not git.RemoteState.EMPTY:
        if push and state is git.RemoteState.NONEMPTY:
            warn("remote already has commits, not pushing")
        return

    failure = git.push(dest)
    if failure:
        warn(f"push failed: {failure}")
    else:
        step("pushed main -> origin")


@main.command("new")
@click.argument("type_", metavar="TYPE")
@click.argument("project_name", metavar="PROJECT_NAME")
@click.option("-C", "--into", default=".", help="Parent directory to create the project in.")
@click.option("--templates", "templates_opt", default=None, help="Path to the ProjectTemplate checkout.")
@click.option("-a", "--author", default=None, help="Name for the copyright line (default: git config user.name).")
@click.option("-y", "--year", type=int, default=None, help="Year for the copyright line (default: this year).")
@click.option("--name", "display_name", default=None, help="Name to substitute for [repo name] (default: the directory name).")
@click.option("--owner", default=None, help=f"GitHub owner for the origin remote (default: {config.DEFAULT_OWNER}).")
@click.option("--remote", "remote_url", default=None, help="Full origin URL, overriding --owner.")
@click.option("--no-remote", is_flag=True, help="Do not add an origin remote.")
@click.option("--no-push", is_flag=True, help="Add origin but do not push the initial commit.")
@click.option("--force-remote", is_flag=True, help="Add origin without checking that the repo exists.")
@click.option("--create", is_flag=True, help="Create the GitHub repo with gh when it does not exist yet.")
@click.option("--private/--public", "private", default=None, help="Visibility for --create (default: from the type).")
@click.option("--no-git", is_flag=True, help="Do not run git init / commit / remote / push.")
@click.option("-m", "--message", default="init", show_default=True, help="Initial commit message.")
@click.option("--no-open", is_flag=True, help="Do not open the project in an editor.")
@click.option("--editor", "editor_opt", default=None, help=f"Editor command to open with (default: {config.DEFAULT_EDITOR}).")
@click.option("--add", "add_opt", multiple=True, metavar="PIECE,...", help="Pieces from the shared pool to overlay, comma separated.")
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
    no_push: bool,
    force_remote: bool,
    create: bool,
    private: bool | None,
    no_git: bool,
    message: str,
    no_open: bool,
    editor_opt: str | None,
    add_opt: tuple[str, ...],
    readme: bool,
    force: bool,
    dry_run: bool,
) -> None:
    """Copy template TYPE into a new project directory PROJECT_NAME."""
    stored = config.load()
    root = templates.resolve_root(templates_opt, stored)

    available = templates.names(root)
    if type_ not in available:
        raise ProjtempError(f"unknown type {type_!r}. Available: {', '.join(available) or '(none)'}")
    src = root / type_

    pool = addons.pool_root(root)
    pieces = [(name, addons.resolve(pool, name)) for name in addons.parse(add_opt)]

    dest = (Path(into).expanduser() / project_name).resolve()
    scaffold.check_destination(dest, root, force)

    name = display_name or dest.name
    author = author or stored.get("author") or git.user_name()
    if not author:
        raise ProjtempError(
            "no author name: set one with `git config --global user.name`, "
            "`projtemp config --set-author 'Your Name'`, or --author"
        )
    year = year or _dt.date.today().year
    editor_cmd = editor_opt or stored.get("editor", config.DEFAULT_EDITOR)

    if no_remote:
        url = None
    else:
        url = remote_url or github.repo_url(owner or stored.get("owner", config.DEFAULT_OWNER), dest.name)

    private_repo = github.default_private(type_) if private is None else private
    if create and no_git:
        raise ProjtempError("--create needs a repo to push from, drop --no-git")
    if create and no_remote:
        raise ProjtempError("--create needs a remote, drop --no-remote")
    if create and force_remote:
        raise ProjtempError(
            "--create and --force-remote conflict: --force-remote skips the check "
            "that would find the repo missing"
        )

    click.secho(type_, fg="cyan", nl=False)
    click.echo(f" -> {dest}")

    if dry_run:
        click.secho("dry run, nothing written", fg="yellow")
        for rel in scaffold.files_in(src):
            click.echo(f"  copy   {rel}")
        for piece_name, piece in pieces:
            for rel in scaffold.files_in(piece) or [Path(piece.name)]:
                click.echo(f"  add    {rel}   ({piece_name})")
        click.echo(f"  fill   [repo name] -> {name}")
        click.echo(f"  fill   [DATE] -> {_dt.date.today().isoformat()}")
        click.echo(f"  fill   copyright -> Copyright (c) {year} {author}")
        if not no_git:
            plan = f"  git    init, commit {message!r}"
            if url:
                plan += f", verify + origin {url}"
                if not no_push:
                    plan += ", push"
            click.echo(plan)
            if url and create:
                click.echo(f"  create {github.create_hint(url, private_repo)}   (only if it is missing)")
        if not no_open:
            click.echo(f"  open   {editor_cmd}")
        return

    step(f"copied {scaffold.copy(src, dest)} files")

    for piece_name, piece in pieces:
        copied, overwritten = addons.add(piece, dest)
        step(f"added {piece_name} ({len(copied)} files)")
        for rel in copied:
            click.echo(f"    {rel}{'  (overwrote template file)' if rel in overwritten else ''}")

    if readme and scaffold.seed_readme(dest, name):
        step("seeded README.md")

    changed = placeholders.fill(dest, name, author, year)
    if changed:
        step(f"filled placeholders in {len(changed)} files")
        for rel in changed:
            click.echo(f"    {rel}")
    else:
        click.echo("  no placeholders to fill")

    if not no_git:
        git.init(dest)
        step("git init (branch main)")
        failure = git.commit_all(dest, message)
        if failure:
            warn(f"initial commit failed: {failure}")
        else:
            step(f"initial commit ({message!r})")
        if url:
            attach_remote(dest, url, not no_push, force_remote, create, private_repo)

    if not no_open:
        failure = editor.open_in(dest, editor_cmd)
        if failure:
            warn(f"not opening editor: {failure}")
        else:
            step(f"opened in {editor_cmd.split()[0]}")

    leftovers = placeholders.unfilled(dest)
    if leftovers:
        click.secho("\nStill to fill in by hand:", fg="yellow")
        for item in leftovers:
            click.echo(f"  {item}")
    if type_ in {"apache-2.0", "agplv3"}:
        click.secho(
            f"\nNote: {type_}/LICENSE is verbatim license text and was left untouched.",
            fg="yellow",
        )


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
