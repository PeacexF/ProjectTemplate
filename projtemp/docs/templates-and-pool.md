# Templates and the shared pool

Two sources of files: a template, exactly one per run, and any number of pieces
from the pool overlaid on top.

## What counts as a template

A directory in the templates root is a template when all of these hold:

- it is a directory
- its name does not start with `.`
- its name is not `global`
- it contains a file named `LICENSE`

That's the whole rule. There is no registry and no manifest — adding a type
means adding a directory with a `LICENSE` in it, and `projtemp list` picks it up.

The flip side is that `LICENSE` is load-bearing. A template that loses that file
silently stops being a template: it vanishes from `list`, and `projtemp <type>`
starts reporting an unknown type. `notes/FEATURES.md` has a `projtemp check`
queued to catch exactly this.

Current types:

| Type | Ships |
| --- | --- |
| `open-source` | MIT, `CONTRIBUTING.md`, `SECURITY.md`, PR template, `docs/` |
| `apache-2.0` | Same shape, Apache 2.0 license text |
| `agplv3` | Same shape, AGPLv3 license text |
| `portfolio` | Same shape, tuned for a showcase repo |
| `paid` | Proprietary license, `docs/SETUP.md`, no contributing or security files |
| `private` | Proprietary license, `.github/notes/` for architecture, plan, roadmap |

Most of the files in a template are empty on purpose. The structure is the
point; the content gets written per project. `projtemp` does not fill them in,
and neither should anything else.

## Copying

`shutil.copytree` with `dirs_exist_ok=True` and `symlinks=True`, so hidden files
come across, directory structure is preserved, and symlinks are copied as links
rather than followed.

Empty directories survive because the templates keep a `.gitkeep` in them —
`.github/workflows/.gitkeep` is the one that matters, since the directory needs
to exist for a piece to drop a workflow into it.

## The pool

`global/` holds pieces that any project can take, whatever its type:

```
global/
  changelog/CHANGELOG.md
  ci/{python,go,node,docker,gitleaks,links}/.github/workflows/*.yml
  disclaimer/DISCLAIMER.md
  docker/{python,go}/{Dockerfile,.dockerignore}
  editor/editorconfig/.editorconfig
  editor/vscode/.vscode/{settings.json,extensions.json}
  github/{issues,dependabot,codeowners}/.github/...
  python/ruff/ruff.toml
```

A piece's contents land at the project root keeping their internal structure, so
`global/ci/python/.github/workflows/python.yml` arrives as
`.github/workflows/python.yml`. That is why the pool has those deep-looking
paths: each piece is a miniature project root.

### What counts as a piece

A directory becomes a piece as soon as it holds a file or a dotted entry.
Above that it is just a grouping level. So `ci/python` is a piece — it holds
`.github` — and `ci` is a group, because it holds only plain subdirectories.
A file sitting at the top of the pool would be a piece in its own right.

`projtemp list` prints exactly the set `--add` expects.

This is a heuristic, not a declaration, and it is the reason
`notes/FEATURES.md` keeps coming back to a manifest: the boundary is inferred
from the shape of the filesystem rather than stated anywhere.

### Passing pieces

```sh
projtemp open-source my-thing --add ci/python,disclaimer
projtemp open-source my-thing --add ci/python --add disclaimer   # same
```

Values are split on commas, trimmed, and de-duplicated with order preserved.
Leading and trailing slashes are stripped, so `--add /disclaimer/` works.

An unknown piece fails the whole run before anything is written, and lists what
is available. A `--add` that resolves outside the pool — `../../etc` and
friends — is refused.

### Groups resolve, with a caveat

`--add ci` is accepted, because `global/ci` exists. But paths in the pool are
literal, so the copy keeps the group level:

```
--add ci/python  →  .github/workflows/python.yml
--add ci         →  python/.github/workflows/python.yml
                    go/.github/workflows/go.yml
                    ...
```

which is almost never what you want. Name the piece, not the group. `-n` shows
the destination paths before anything is written.

### Collisions

A piece file that lands on an existing path overwrites it, and the overwrite is
reported:

```
  added ci/links (2 files)
    .github/workflows/links.yml
    .lycheeignore  (overwrote template file)
```

Pieces apply in the order given, so with two pieces claiming the same path the
last one wins. There is no `--no-overwrite`; `notes/FEATURES.md` has it parked
until it bites.

### Pieces get the placeholder pass

Pieces are copied before placeholders are filled, so `[DATE]` in
`global/disclaimer/DISCLAIMER.md` and any copyright line in a piece are
substituted the same as template files. That is the whole reason the ordering is
what it is. See [placeholders.md](placeholders.md).
