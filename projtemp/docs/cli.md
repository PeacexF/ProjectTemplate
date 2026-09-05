# Command reference

```
projtemp [COMMAND] [ARGS]...
```

Four commands: `new`, `list`, `check`, `config`. `new` is the default, so
`projtemp open-source my-thing` is shorthand for
`projtemp new open-source my-thing`.

The shorthand works by catching click's "no such command" error and retrying as
`new`, which has one consequence worth knowing: a template directory named
`new`, `list`, `check` or `config` would be shadowed by the subcommand and
unreachable by shorthand. Nothing in the repo is named that, and `projtemp new list my-thing`
would still work.

Running `projtemp` bare prints help followed by the available types.

## `projtemp new`

```
projtemp new [OPTIONS] TYPE PROJECT_NAME
```

`TYPE` is a template directory name (`projtemp list` shows them).
`PROJECT_NAME` is the directory to create, by default in the current directory.

The order of operations is fixed:

1. Resolve the templates root and validate `TYPE`.
2. Resolve every `--add` piece — an unknown piece fails here, before anything is
   written.
3. Check the destination.
4. Copy the template tree, hidden files included.
5. Overlay the pieces.
6. Seed `README.md` if `--readme`.
7. Fill placeholders across the whole project, pieces included.
8. `git init -b main`, `git add -A`, commit.
9. Probe the remote, attach `origin`, push if the remote is empty.
10. Open the editor.
11. Report any placeholder left unfilled.

Steps 1–3 are the validation phase; if anything is wrong the command exits 1
having written nothing. After step 4, failures downstream warn rather than abort
— a project half-set-up is more useful than one rolled back.

### Where it goes

| Flag | Effect |
| --- | --- |
| `-C, --into DIR` | Parent directory to create the project under. Default `.` |
| `--force` | Copy into a target that already exists and has files in it |

The destination is `DIR/PROJECT_NAME`, resolved to an absolute path. It is
refused if it exists and is not a directory, if it is a non-empty directory
without `--force`, or if it is inside the templates root — that last check stops
you scaffolding a project into the repo the templates come from.

`--force` merges into whatever is there; existing files with the same names are
overwritten, and the "copied N files" count is a count of everything in the
destination afterwards, not of what this run wrote.

### Naming and the copyright line

| Flag | Effect |
| --- | --- |
| `--name NAME` | Value for `[repo name]`. Default: the destination directory name |
| `-a, --author NAME` | Name for the copyright line |
| `-y, --year YEAR` | Year for the copyright line. Default: this year |

`--author` falls back to the stored `author`, then to `git config user.name`. If
none of the three produce a name the run fails before writing, telling you the
three ways to set one. See [placeholders.md](placeholders.md).

### Pieces

| Flag | Effect |
| --- | --- |
| `--add PIECE,...` | Overlay pieces from `global/`. Comma separated, and repeatable |

`--add ci/python,disclaimer` and `--add ci/python --add disclaimer` are the same
thing. Duplicates collapse, order is preserved, and pieces are applied in the
order given, so a later piece wins a collision with an earlier one. See
[templates-and-pool.md](templates-and-pool.md).

### Git and the remote

| Flag | Effect |
| --- | --- |
| `-m, --message MSG` | Initial commit message. Default `init` |
| `--owner OWNER` | GitHub owner for `origin`. Default: stored `owner`, else `PeacexF` |
| `--remote URL` | Full `origin` URL, overriding `--owner` |
| `--no-remote` | Skip the remote entirely; still init and commit |
| `--no-push` | Attach `origin`, do not push |
| `--force-remote` | Attach `origin` without checking the repo exists |
| `--create` | Create the repo through `gh` when the probe finds it missing |
| `--private` / `--public` | Visibility for `--create`. Default: from the type |
| `--no-git` | Skip init, commit, remote and push |

`--force-remote` also skips the push, because the push decision keys off what
the probe found and a skipped probe reports nothing.

`--create` closes the loop on the one case the probe used to just report:

```sh
projtemp private my-thing --create
```

Without it, a missing repo prints the `gh repo create` line and stops. With it,
that line is run. Visibility defaults from the type — `private` and `paid`
private, everything else public — and `--private` / `--public` override.

Three combinations are refused up front rather than silently doing nothing,
because each removes the very step `--create` hangs off:

```
Error: --create needs a repo to push from, drop --no-git
Error: --create needs a remote, drop --no-remote
Error: --create and --force-remote conflict: --force-remote skips the check that
would find the repo missing
```

See [git-and-remote.md](git-and-remote.md).

### Editor and output

| Flag | Effect |
| --- | --- |
| `--editor CMD` | Editor command. Default: stored `editor`, else `code` |
| `--no-open` | Do not open an editor |
| `--readme` | Write `# PROJECT_NAME` into `README.md` if it is empty |
| `-n, --dry-run` | Print the plan, write nothing |

The editor command may carry arguments (`--editor "code -n"`); the first word is
what gets looked up on PATH. It is launched without waiting, so the command
returns immediately.

`--readme` only writes when `README.md` is absent or blank — it will not
overwrite one with content, which matters under `--force`. Templates ship an
empty `README.md`, so on a fresh scaffold it always fires.

### Templates root

| Flag | Effect |
| --- | --- |
| `--templates PATH` | Path to the ProjectTemplate checkout |

Note this is a per-command option, not a group one: `projtemp new --templates …`
and `projtemp list --templates …` work, `projtemp --templates … list` does not.
See [configuration.md](configuration.md).

## `projtemp list`

```
projtemp list [--templates PATH] [--pool] [--plain]
```

Prints the resolved templates root, then each type with its file count, then the
pool root and each addable piece with its file count. The piece names are
exactly what `--add` takes.

| Flag | Effect |
| --- | --- |
| `--pool` | List the pool pieces instead of the project types |
| `--plain` | Names only, one per line — no counts, no headers, no colour |

`--plain` is there so shell loops can be written without parsing the pretty
output, which is what the templates workflow does:

```sh
for type in $(projtemp list --plain); do ... done
for piece in $(projtemp list --pool --plain); do ... done
```

Exits 1 if the root resolves but holds no templates, or with `--pool` if the
pool holds no pieces.

## `projtemp check`

```
projtemp check [--templates PATH]
```

Audits the templates and the pool without writing anything. Exits 0 and prints a
one-line summary when everything passes:

```
/Users/you/Workspace/Projects/ProjectTemplate
  ok — 6 types, 16 pieces
```

Otherwise it lists every problem and exits 1. See [checking.md](checking.md) for
what it actually looks at.

## `projtemp config`

```
projtemp config [--set-templates PATH] [--set-author NAME] [--set-owner OWNER] [--set-editor CMD]
```

With no flags it prints the current state — config file path, resolved templates
root, author, owner, editor — without writing anything. Any `--set-*` flag
writes `~/.config/projtemp/config.json` and then prints the new state.

`--set-templates` validates before storing: the path must hold at least one
template directory. The other three are stored as given.

The author line shows the effective value, so it reads `Peace` from
`git config user.name` even with nothing stored. If the templates root cannot be
resolved that line reports the reason in yellow instead of failing the command.

## Exit codes

`0` on success. `1` for anything the user has to fix — unknown type, unknown
piece, unresolvable templates root, blocked destination, no author name, a
contradictory `--create` combination, or any problem found by `check`.
Everything in that class is raised as `ProjtempError` and rendered as
`Error: <message>`.

Warnings — a failed commit, an unreachable remote, a missing editor — do not
change the exit code.
