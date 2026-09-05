# Configuration

Two things need resolving before a run: where the templates are, and what the
defaults are.

## The templates root

Checked in this order, first source that is set wins:

1. `--templates PATH` on `new` or `list`
2. `$PROJTEMP_TEMPLATES`
3. `templates` in the config file
4. the checkout the installed source lives in — `parents[1]` of `templates.py`

A set source that turns out to be wrong is an error, not a reason to fall
through. If `$PROJTEMP_TEMPLATES` points at a directory that does not exist, or
at one holding no templates, the run stops and names the source:

```
Error: templates root from $PROJTEMP_TEMPLATES does not exist: /nope
```

That is deliberate: silently falling back after you explicitly pointed the tool
somewhere would scaffold from the wrong place without saying so.

Step 4 is why an editable install needs no configuration at all — the source
sits in the checkout, and the checkout is the templates root. It is also why a
non-editable install needs `--set-templates`, since site-packages holds no
templates. See [install.md](install.md).

"Holds templates" means: contains at least one non-hidden subdirectory, other
than `global/`, containing a `LICENSE` file. See
[templates-and-pool.md](templates-and-pool.md).

If nothing resolves, the error lists the three ways to fix it. One line of it is
stale — it suggests `projtemp --templates <path> ...`, but `--templates` is a
per-command option, so the working forms are `projtemp new --templates <path>
TYPE NAME` and `projtemp list --templates <path>`.

## The config file

`~/.config/projtemp/config.json`, or `$XDG_CONFIG_HOME/projtemp/config.json`
when that is set. Written only by `projtemp config --set-*`, which creates the
parent directory as needed.

```json
{
  "author": "Peace",
  "editor": "code",
  "owner": "PeacexF",
  "templates": "/Users/you/Workspace/Projects/ProjectTemplate"
}
```

All four keys are optional. A missing file is not an error — it reads as empty
defaults, and `projtemp config` says `(none yet)`. A file that exists but cannot
be parsed *is* an error, so a corrupt config gets reported rather than silently
ignored. A file holding valid JSON that isn't an object reads as empty.

Unknown keys are preserved on write; the file round-trips through a plain dict.

## Default lookup

| Value | Order |
| --- | --- |
| templates root | `--templates` → `$PROJTEMP_TEMPLATES` → config → the checkout |
| author | `--author` → config `author` → `git config user.name` → error |
| year | `--year` → the current year |
| `[repo name]` | `--name` → the destination directory name |
| owner | `--owner` → config `owner` → `PeacexF` |
| remote URL | `--remote` → `https://github.com/<owner>/<dir name>` |
| editor | `--editor` → config `editor` → `code` |
| commit message | `--message` → `init` |

Author is the only one that can fail the run. The rest all bottom out in a
usable default.

Two defaults are compiled in rather than read from a file: `DEFAULT_OWNER =
"PeacexF"` and `DEFAULT_EDITOR = "code"` in `config.py`. Anyone else using this
should set both once:

```sh
projtemp config --set-owner your-github-name --set-editor nvim
```

Note that the remote URL is built from the *destination directory name*, not
from `--name`. `--name` only feeds the `[repo name]` placeholder, so a project
in `./my-thing` with `--name "My Thing"` still targets
`https://github.com/PeacexF/my-thing`.
