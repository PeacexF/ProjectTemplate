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
| `ABSENT` | non-zero, `not found` or `does not exist` in stderr | no remote; prints the `gh repo create` line |
| `UNKNOWN` | any other failure, timeout, or `git` missing | no remote; warns it could not reach the URL |

The point of the probe is that `origin` only gets attached to something that
actually exists. A dangling remote that fails on the first push is worse than no
remote — that is what this replaced.

For `ABSENT` you get the line to run:

```
  https://github.com/PeacexF/my-thing does not exist, origin not added
  create it with: gh repo create PeacexF/my-thing --source . --push
```

Run it from inside the new project; `--source .` and `--push` do the remote and
the push in one go. Making the repo directly from `projtemp` is queued in
`notes/FEATURES.md`, with visibility defaulting from the type.

`UNKNOWN` is the offline case, and also the private-repo-without-credentials
case. The conservative choice is the same either way: attach nothing.

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
