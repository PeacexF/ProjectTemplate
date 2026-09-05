# Install

From the repo root — not from `projtemp/`:

```sh
uv tool install --editable .
```

`pipx install -e .` works the same way. Either puts a `projtemp` executable on
your PATH.

Editable is the point. The templates and the CLI live in the same checkout, so
an editable install means pulling this repo updates both at once, with no
reinstall and no config to keep in sync — the CLI finds the templates by walking
up from its own source file. See [configuration.md](configuration.md).

## Why the manifest is at the root

`pyproject.toml` sits at the repo root rather than in `projtemp/`, which looks
misplaced until you try it the other way round.

An editable install needs the package directory importable under its own name.
With the manifest at the root, the project directory is the parent of
`projtemp/`, so `import projtemp` resolves. Move the manifest into `projtemp/`
and the package directory becomes the project directory itself — the modules
would have to import as `git`, `config`, `templates` and so on, colliding with
the standard library and with each other.

The root placement also keeps `templates.resolve_root`'s last-resort lookup
honest: `Path(__file__).parents[1]` from inside the installed source is the
checkout root, which is where the template directories are.

```toml
[project.scripts]
projtemp = "projtemp.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["projtemp"]
```

## Non-editable installs

A wheel ships `projtemp/` alone, so the last-resort lookup lands in
site-packages, which holds no templates. Pin the checkout once:

```sh
projtemp config --set-templates ~/Workspace/Projects/ProjectTemplate
```

## Requirements

- Python 3.9+
- `click>=8.1` — the only dependency
- `git` on PATH for the git steps; `--no-git` skips all of them
- an editor command on PATH for the open step; `--no-open` skips it

`projtemp/.venv/` in this directory is a scratch venv for working on the CLI. It
is not what the installed tool runs from, and it is gitignored.
