# projtemp docs

`projtemp` copies one of this repo's template directories into a new project,
overlays optional pieces from `global/`, fills the placeholders, initialises git,
attaches a remote if the GitHub repo already exists, and opens an editor.

`../README.md` is the short version. These pages are the long one — what each
step actually does, and where the edges are.

| Page | What's in it |
| --- | --- |
| [install.md](install.md) | Installing, and why `pyproject.toml` sits at the repo root |
| [cli.md](cli.md) | Every command and flag, with what each one changes |
| [configuration.md](configuration.md) | Templates root resolution, the config file, default lookup order |
| [templates-and-pool.md](templates-and-pool.md) | What counts as a template, what counts as a piece, how `--add` overlays |
| [placeholders.md](placeholders.md) | The three substitutions, what is deliberately left alone |
| [git-and-remote.md](git-and-remote.md) | init, commit, the four remote states, and `--create` |
| [checking.md](checking.md) | `projtemp check`, its three rules, and the templates CI |
| [architecture.md](architecture.md) | Module map, invariants, how to extend, known sharp edges |

## Quickstart

```sh
uv tool install --editable .          # from the repo root
projtemp list                         # types, and pieces you can --add
projtemp open-source my-thing         # scaffold ./my-thing
projtemp check                        # audit the templates themselves
```

A run prints one line per step:

```
open-source -> /Users/you/Workspace/my-thing
  copied 9 files
  added ci/python (1 files)
    .github/workflows/python.yml
  filled placeholders in 1 files
    CONTRIBUTING.md
  git init (branch main)
  initial commit ('init')
  origin -> https://github.com/PeacexF/my-thing
  pushed main -> origin
  opened in code
```

Green lines are things that happened, yellow lines are things that didn't and
why. Nothing in the pipeline is fatal after the copy: a failed commit, an
unreachable remote or a missing editor each warn and the run continues.

## Two habits worth having

`-n` first when the invocation is unusual. It prints the full plan — every file,
every substitution, the git and editor steps — and writes nothing.

```sh
projtemp open-source my-thing --add ci/python,disclaimer -n
```

`--no-git --no-open` when you just want the files, e.g. scaffolding into a
directory you are going to move somewhere else.

`--create` when the GitHub repo does not exist yet. Without it a missing repo
prints the `gh repo create` line and stops; with it, that line gets run, with
visibility taken from the type.
