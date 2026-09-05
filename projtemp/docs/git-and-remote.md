# Git and the remote

The git steps run last, after the files are final. `--no-git` skips all of them
and leaves a plain directory.

## Local

```sh
git init -b main
git add -A
git commit -m "init"
```

`git init -b` needs git 2.28+. On older git the `-b` fails, a bare `git init`
runs, and `git symbolic-ref HEAD refs/heads/main` sets the branch instead — same
result, one more call.

A failed `git init` is fatal. A failed commit is not: it warns and the run
continues to the remote and editor steps. That is the usual shape of the
failure — no `user.email` configured, or a commit hook refusing — and it leaves
you with an initialised repo and staged files to fix by hand.

The commit message defaults to `init`; `-m` changes it.

## The remote

The URL is `https://github.com/<owner>/<destination directory name>`, with
`--remote` overriding it wholesale and `--owner` overriding just the owner.
Note it is built from the directory name, not from `--name`.

Before touching `origin`, the remote is probed:

```sh
GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND='ssh -oBatchMode=yes' git ls-remote <url>
```

Both environment settings keep the probe non-interactive — a private repo you
lack credentials for fails immediately instead of hanging on a password prompt.
There is a 20 second timeout on top.

The result is one of four states, and each is handled differently:

| State | Probe result | What happens |
| --- | --- | --- |
| `EMPTY` | exit 0, no refs | `origin` added, initial commit pushed |
| `NONEMPTY` | exit 0, refs listed | `origin` added, nothing pushed, warns the remote already has commits |
| `ABSENT` | non-zero, `not found` or `does not exist` in stderr | with `--create`, the repo is created; otherwise no remote, and the `gh repo create` line is printed |
| `UNKNOWN` | any other failure, timeout, or `git` missing | no remote; warns it could not reach the URL |

The point of the probe is that `origin` only gets attached to something that
actually exists. A dangling remote that fails on the first push is worse than no
remote — that is what this replaced.

For `ABSENT` without `--create` you get the line to run:

```
  https://github.com/PeacexF/my-thing does not exist, origin not added
  create it with: gh repo create PeacexF/my-thing --public --source . --push
```

Run it from inside the new project; `--source .` and `--push` do the remote and
the push in one go.

`UNKNOWN` is the offline case, and also the private-repo-without-credentials
case. The conservative choice is the same either way: attach nothing.

## `--create`

`--create` runs that line instead of printing it. It only fires on `ABSENT` —
a repo that already exists is attached as usual, and an unreachable one is still
left alone, because "I could not tell" is not "it is missing".

```sh
projtemp private my-thing --create
```

```
  git init (branch main)
  initial commit ('init')
  created private repo PeacexF/my-thing
  origin -> https://github.com/PeacexF/my-thing
  pushed main -> origin
```

### Visibility

Defaults from the type: `private` and `paid` get a private repo, every other
type gets a public one. `--private` and `--public` override it either way, and
the choice also shows up in the printed hint when `--create` is not used, so the
line you are told to run matches what `--create` would have done.

The set lives in `github.PRIVATE_TYPES`, so a new type is public unless it is
added there.

### What it runs

```sh
gh repo create <owner>/<name> --public|--private --source . [--push]
```

`--source .` means `gh` creates the remote *and* wires up `origin` itself, so
`projtemp` does not call `git remote add` on this path. `gh` picks https or ssh
from the user's git config, which is why the reported URL is read back with
`git remote get-url origin` rather than assumed to be the https one that was
probed. `--no-push` drops `--push` and leaves the commit local.

### When it can't

Each of these warns and leaves the project otherwise finished — none of them
fail the run:

| Situation | What you get |
| --- | --- |
| `gh` not on PATH | `cannot create the repo: gh is not on PATH` plus the manual line |
| `gh` not logged in | `cannot create the repo: gh is not logged in (run: gh auth login)` plus the manual line |
| `--remote` points off GitHub | `--create only works with github.com remotes, not <url>` |
| `gh repo create` fails | the last line of its stderr, plus the manual line |

The host check accepts https, ssh and scp-style GitHub URLs, so
`--remote git@github.com:you/thing.git --create` works.

### Refused combinations

`--create` needs a commit to push and a URL to create, so these three are usage
errors caught before anything is written:

```
--create --no-git         no repo to push from
--create --no-remote      no URL to create
--create --force-remote   the probe that would find the repo missing is skipped
```

## Flags

| Flag | Effect |
| --- | --- |
| `--no-git` | No init, no commit, no remote, no push |
| `--no-remote` | Init and commit, but no probe and no `origin` |
| `--no-push` | Probe and attach `origin`, never push |
| `--force-remote` | Attach `origin` with no probe at all |
| `--remote URL` | Use this URL instead of the derived one |
| `--owner OWNER` | Use this owner in the derived URL |

`--force-remote` is the escape hatch for a host `ls-remote` cannot usefully
answer for. It skips the probe, which means the state is `UNKNOWN`, which means
**it never pushes** — the push decision keys off the remote being known-empty,
and a skipped probe knows nothing. Attach and push by hand:

```sh
projtemp private my-thing --force-remote
cd my-thing && git push -u origin main
```

`--remote` still gets probed. To skip both the probe and the push, combine
`--force-remote` with it.

## Failure handling

Everything after `git init` degrades rather than aborting. A failed remote add,
a failed push, an unreachable host — each prints a yellow line and the run
carries on. The exit code stays 0; these are warnings about the environment, not
about the request.
