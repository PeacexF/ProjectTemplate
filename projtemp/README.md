# projtemp

Scatters a new project from the templates in this repo.

```sh
projtemp <type> <project_name>
```

`<type>` is one of the top-level template directories (`projtemp list` shows them),
`<project_name>` is the directory to create in the current working directory.

Longer form — every flag, how the pool resolves, the placeholder rules, the
four remote states, the module map — in [`docs/`](docs/README.md).

## What it does

1. Copies `<type>/` into `./<project_name>/`, hidden files included.
2. Overlays any `--add` pieces from `global/` on top.
3. Fills the placeholders:
   - `[repo name]` → the project name (`CONTRIBUTING.md`)
   - `[DATE]` → today (`DISCLAIMER.md`)
   - `Copyright (c) <year> <name>` → the current year and your `git config user.name`
4. `git init` on `main`, `git add -A`, and an initial commit.
5. Checks whether `https://github.com/PeacexF/<project_name>` actually exists.
   Only if it does is `origin` added — no dangling remotes. If the repo is
   empty, the initial commit is pushed; if it already has commits, the remote is
   attached but nothing is pushed. If it doesn't exist, you get the
   `gh repo create` line to run.
6. Opens the new directory in `code`.

`apache-2.0/LICENSE` and `agplv3/LICENSE` are verbatim license text, so their
`[yyyy]` / `<name of author>` boilerplate is deliberately left alone. Everything
else the templates leave empty stays empty on purpose.

## Install

From the repo root:

```sh
uv tool install --editable .
```

Editable, so pulling this repo updates the CLI with no reinstall. `pipx install -e .`
works the same way. The build manifest is the repo-root `pyproject.toml`: an editable
install needs the package directory importable under its own name, which is why that
one file sits at the root rather than in here.

The templates root is found in this order: `--templates`, `$PROJTEMP_TEMPLATES`,
the config file, then the checkout the installed source lives in. If you install
non-editably, pin it once:

```sh
projtemp config --set-templates ~/Workspace/Projects/ProjectTemplate
```

## The shared pool

`global/` holds pieces that any project can take, whatever its type:

```sh
projtemp open-source python-checker --add ci/python,disclaimer
```

The pool is a plain filesystem and `--add` takes literal paths into it. A piece's
contents land at the project root keeping their internal structure, so
`global/ci/python/.github/workflows/python.yml` arrives as
`.github/workflows/python.yml`.

What's in there: `ci/` (python, go, node, docker, gitleaks, links), `docker/`
(python, go), `editor/` (editorconfig, vscode), `github/` (issues, dependabot,
codeowners), `python/ruff`, `changelog`, `disclaimer`.

A directory is a piece once it holds a file or a dotted entry; above that it is
just a grouping level. `ci/python` is a piece, `ci` is the group — `projtemp list`
shows what is addable. Pieces are copied before the placeholder pass, so they get
`[DATE]` and the copyright line filled too. A piece that collides with a template
file wins, and the overwrite is reported.

## Options

| Flag | Effect |
| --- | --- |
| `-C, --into DIR` | Create the project under `DIR` instead of the cwd |
| `-a, --author NAME` | Name for the copyright line |
| `-y, --year YEAR` | Year for the copyright line |
| `--add PIECE,...` | Pieces from `global/` to overlay (repeatable) |
| `--name NAME` | Value for `[repo name]` if it differs from the directory name |
| `--owner OWNER` | GitHub owner for `origin` |
| `--remote URL` | Full `origin` URL, overriding `--owner` |
| `--no-remote` | Skip the remote entirely |
| `--no-push` | Add `origin` but do not push |
| `--force-remote` | Add `origin` without checking that the repo exists |
| `--no-git` | Skip init, commit, remote and push |
| `-m, --message MSG` | Initial commit message (default `init`) |
| `--no-open` | Do not open an editor |
| `--editor CMD` | Editor command (default `code`) |
| `--readme` | Seed the empty `README.md` with the project name as an H1 |
| `--force` | Copy into a target directory that already has files |
| `-n, --dry-run` | Print the plan, write nothing |

`projtemp config` shows the stored defaults and can set `--set-templates`,
`--set-author`, `--set-owner` and `--set-editor`.

## Layout

One job per file. Only `cli.py` imports click or prints anything; every other
module returns values and raises `ProjtempError`, so the logic can be used or
tested without going through the command line.

| File | Job |
| --- | --- |
| `cli.py` | Command surface, flags, and all output |
| `templates.py` | Where the templates root is, and what counts as a template |
| `scaffold.py` | Destination checks and copying the tree |
| `placeholders.py` | `[repo name]`, `[DATE]`, and the copyright line |
| `git.py` | `init`, `commit`, `remote add`, `push`, and probing a remote |
| `github.py` | GitHub URL and slug conventions — no network |
| `addons.py` | Resolving and overlaying `--add` pieces |
| `editor.py` | Opening the finished project |
| `config.py` | Stored defaults |
| `__init__.py` | Version and `ProjtempError` |
