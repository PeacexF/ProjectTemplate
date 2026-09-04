# projtemp

Scatters a new project from the templates in this repo.

```sh
projtemp <type> <project_name>
```

`<type>` is one of the top-level template directories (`projtemp list` shows them),
`<project_name>` is the directory to create in the current working directory.

## What it does

1. Copies `<type>/` into `./<project_name>/`, hidden files included.
2. Fills the placeholders:
   - `[repo name]` → the project name (`CONTRIBUTING.md`)
   - `[DATE]` → today (`DISCLAIMER.md`)
   - `Copyright (c) <year> <name>` → the current year and your `git config user.name`
3. `git init` on `main`, `git add -A`, and an initial commit.
4. Adds `origin` pointing at `https://github.com/PeacexF/<project_name>` (nothing is pushed).
5. Opens the new directory in `code`.

`apache-2.0/LICENSE` and `agplv3/LICENSE` are verbatim license text, so their
`[yyyy]` / `<name of author>` boilerplate is deliberately left alone — put your
copyright in a `NOTICE` file or in source headers instead. Everything else the
templates leave empty stays empty on purpose.

## Install

```sh
uv tool install --editable projtemp
```

Editable, so pulling this repo updates the CLI. `pipx install -e projtemp`
works the same way.

The templates root is found in this order: `--templates`, `$PROJTEMP_TEMPLATES`,
the config file, then the checkout the installed source lives in. If you install
non-editably, pin it once:

```sh
projtemp config --set-templates ~/Workspace/Projects/ProjectTemplate
```

## Options

| Flag | Effect |
| --- | --- |
| `-C, --into DIR` | Create the project under `DIR` instead of the cwd |
| `-a, --author NAME` | Name for the copyright line |
| `-y, --year YEAR` | Year for the copyright line |
| `--name NAME` | Value for `[repo name]` if it differs from the directory name |
| `--owner OWNER` | GitHub owner for `origin` |
| `--remote URL` | Full `origin` URL, overriding `--owner` |
| `--no-remote` | Skip the remote |
| `--no-git` | Skip init, commit and remote |
| `-m, --message MSG` | Initial commit message (default `init`) |
| `--no-open` | Do not open an editor |
| `--editor CMD` | Editor command (default `code`) |
| `--readme` | Seed the empty `README.md` with the project name as an H1 |
| `--force` | Copy into a target directory that already has files |
| `-n, --dry-run` | Print the plan, write nothing |

`projtemp config` shows the stored defaults and can set `--set-templates`,
`--set-author`, `--set-owner` and `--set-editor`.
