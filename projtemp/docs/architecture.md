# Architecture

One job per file, and one rule that shapes everything else: **only `cli.py`
imports click, and only `cli.py` prints.** Every other module takes arguments,
returns values, and raises `ProjtempError`. The scaffolding logic can be
imported and tested without going through a command line.

| Module | Job | Talks to |
| --- | --- | --- |
| `cli.py` | Commands, flags, ordering, all output | everything |
| `templates.py` | Where the templates root is, what counts as a template | `config` |
| `scaffold.py` | Destination checks, copying, README seeding | — |
| `addons.py` | Discovering, resolving and overlaying `--add` pieces | `templates` |
| `placeholders.py` | The substitution pass and the leftovers report | — |
| `check.py` | Auditing the templates themselves | `addons`, `placeholders`, `templates` |
| `git.py` | `init`, `commit`, `remote add`, `push`, remote probing | — |
| `github.py` | URL, slug and visibility conventions. No network | — |
| `gh.py` | Creating a repo through the `gh` CLI | — |
| `editor.py` | Launching the editor | — |
| `config.py` | Reading and writing stored defaults | — |
| `__init__.py` | `__version__` and `ProjtempError` | — |

The dependency graph is nearly flat. `templates` imports `config` for a path to
name in an error; `addons` imports `templates` for the `global` directory name;
`check` imports the three modules whose rules it is auditing against, which is
the whole point of it. Nothing else imports a sibling. `ProjtempError` lives in
`__init__.py` precisely so no module has to import another to raise it.

`github.py` and `gh.py` are split along the network line rather than by topic:
one holds the conventions — how a URL is built, which host counts as GitHub,
which types default to private — and never makes a call, the other shells out to
`gh` and never decides anything. That keeps the fiddly string handling testable
without a network and the network code trivial enough not to need testing.

## The two conventions

**Fatal versus recoverable.** A module raises `ProjtempError` when the user has
to fix something, and returns a message when the environment misbehaved. So
`git.init` raises, while `git.commit_all`, `git.add_remote`, `git.push` and
`editor.open_in` all return `str | None` — `None` for success, a one-line
explanation otherwise. `cli.py` renders the first as `Error:` and exits 1, and
the second as a yellow warning that does not stop the run.

The `_first_error` helper picks the *last* line of stderr, because git puts the
useful part at the bottom.

**Validate, then write.** `new_cmd` resolves the root, the type, every piece and
the destination before the first byte is copied. A typo in `--add` fails with
nothing on disk. After the copy nothing rolls back, so anything downstream that
can fail warns instead.

## Data flow through `new`

```
config.load()             stored defaults
templates.resolve_root()  --templates > $PROJTEMP_TEMPLATES > config > checkout
templates.names()         validate TYPE
addons.pool_root/parse/resolve   validate every --add, still nothing written
scaffold.check_destination()     dest is safe to write
── from here on, things exist on disk ──
scaffold.copy()           the template tree
addons.add()              each piece, in order, over the top
scaffold.seed_readme()    only if --readme
placeholders.fill()       one pass over everything, pieces included
git.init/commit_all       local repo
git.remote_state()        probe, then attach_remote() decides
gh.create_repo()          only on --create, and only when the repo is missing
editor.open_in()          fire and forget
placeholders.unfilled()   report what's left
```

The ordering is not incidental. Pieces are copied before the placeholder pass so
that `[DATE]` in `DISCLAIMER.md` gets filled; `--readme` runs before it too, so
a seeded README would get the same treatment.

`attach_remote` is the only real branching logic in `cli.py`, and it lives there
rather than in `git.py` because every branch ends in a message. `git.py` reports
a `RemoteState`; deciding what that means is a presentation concern. `--create`
hangs off the one branch that was previously a dead end, and `create_remote`
splits out beside it for the same reason — it is four failure messages and one
success path.

## Dry run

`--dry-run` re-derives the plan from the same functions the real run uses —
`scaffold.files_in` for the copy list, `addons.resolve` for the pieces — then
returns before `scaffold.copy`. It is a separate branch rather than a flag
threaded through the writers, which keeps the writers simple at the cost of the
plan being a second description of the work. The `name` shadowing described in
[placeholders.md](placeholders.md) is present in both branches, which is the
shape of bug that arrangement invites.

## Testing

There is no unit test suite. The modules are structured for one — every module
but `cli.py` is pure input/output with no printing — but what exists today is
end to end: `.github/workflows/templates.yml` runs `projtemp check`, scaffolds
every type, and overlays every piece on each push. See
[checking.md](checking.md).

The same thing by hand, and what `CONTRIBUTING.md` asks contributors to do:

```sh
projtemp check
cd "$(mktemp -d)"
projtemp open-source probe --add ci/python,disclaimer --no-git --no-open
grep -rn "\[DATE\]\|\[repo name\]" probe/
```

`--no-git --no-open` keeps it from touching the network or the editor.

The gap the CI cannot close is `--create`, since it would have to make a real
repo to exercise it. `gh.create_args` exists as a separate function so the
invocation can at least be asserted without running it.

## Extending it

**A new project type.** Add a directory with a `LICENSE` in it. No code change.

**A new pool piece.** Add a directory under `global/` laid out as a miniature
project root. It becomes addable as soon as it holds a file or a dotted entry.
No code change.

**A new placeholder.** `placeholders.py`, in two places — the substitution in
`fill` and the marker in `UNFILLED_RE`. This is the one extension that needs
code, and the per-template manifest in `notes/FEATURES.md` exists to remove it.

**A new flag.** `cli.py` for the option and the output, plus whichever module
does the work. Keep the printing on the `cli.py` side.

## Known sharp edges

- **`--force-remote` never pushes**, and rules out `--create`. Both key off a
  probe that was skipped. See [git-and-remote.md](git-and-remote.md).
- **`LICENSE` is load-bearing.** A template that loses it silently stops being a
  template.
- **Pool paths are literal.** `--add ci` keeps the group level in the
  destination path. Name the piece, not the group.
- **`scaffold.copy` counts the destination**, not what it wrote, so the "copied
  N files" line overcounts under `--force`.
- **`unfilled` reads only `*.md`**, so a marker in a non-markdown file is never
  reported.
- **Subcommand names shadow types.** A template named `new`, `list`, `check` or
  `config` would be unreachable by the `projtemp <type> <name>` shorthand.
- **`check`'s marker rule is a heuristic**, scoped to markdown and to a fixed
  vocabulary, because outside markdown a bracket is usually syntax. See
  [checking.md](checking.md).

`notes/FEATURES.md` is the parking lot for what's next — `--create --description`,
more `check` rules, a unit suite — and for the open question underneath several
of them: whether templates stay whole directories you can `cp -R`, or become
recipes declared in a manifest.
