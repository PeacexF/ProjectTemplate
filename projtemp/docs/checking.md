# Checking the templates

```sh
projtemp check
```

Audits the templates and the pool. Writes nothing, exits 0 when clean:

```
/Users/you/Workspace/Projects/ProjectTemplate
  ok — 6 types, 16 pieces
```

and exits 1 with a line per problem otherwise:

```
/Users/you/Workspace/Projects/ProjectTemplate
  portfolio               missing .gitignore
  open-source/docs/x.md   marker [YOUR NAME] is not one the CLI can fill
  paid/NOTICE             copyright line will not be rewritten: Copyright 2019 Someone Else
```

`CONTRIBUTING.md` asks contributors to copy a template into a scratch repo and
check it still works. This is the part of that a machine can do.

## The three rules

### Required files

Every template must hold `LICENSE`, `README.md` and `.gitignore`.

`LICENSE` is the one that really matters, because it is also the marker that
makes a directory a template. Lose it and the type silently disappears from
`projtemp list` and starts reporting as unknown — no error anywhere, just a type
that stopped existing. That failure mode is the reason this command exists.

The other two are there because every template ships them today and a project
scaffolded without either is a project someone has to fix by hand.

Pool pieces are exempt: a piece is a fragment, not a project.

### Markers the CLI cannot fill

Markdown files are scanned for `[...]` markers, and anything that looks like a
placeholder must be one the substitution pass knows — `[repo name]` or `[DATE]`.
Anything else is a marker that would ship to a real project unfilled.

"Looks like a placeholder" is the judgement call. A bracket in markdown is
usually something else entirely, so the rule is deliberately narrow: a marker
counts when it is ALL CAPS, or when it contains one of *name, owner, author,
email, url, year, date, yyyy, todo*. Markdown links (`[text](url)`), reference
definitions (`[text]:`) and reference links (`[text][ref]`) are excluded by the
pattern itself.

That vocabulary is the same one `placeholders.UNFILLED_RE` uses for the
end-of-run report, which is the point — the two should agree about what a
placeholder is.

Against the current repo it passes `[Unreleased]` in the changelog and
`[Keep a Changelog](...)`, and catches `[YOUR NAME]` or `[org name]`. Only
markdown is scanned, because outside it brackets are syntax: `branches: [main]`
in YAML, `[lint]` in TOML, `[Makefile]` in editorconfig.

### Copyright lines that would not be rewritten

Every line starting with `Copyright` at column 0 must match the pattern the
placeholder pass rewrites:

```python
^Copyright \(c\) \d{4}(?:-\d{4})? .*$
```

A line that does not match is a name the scaffolder will carry into somebody
else's project untouched — `Copyright 2019 Someone Else`, or a stray `(C)`.
Unlike the marker rule this reads every file, not just markdown, since the
line lives in `LICENSE`.

## The verbatim exemption

`apache-2.0/LICENSE` and `agplv3/LICENSE` are upstream license text and are
skipped by both content rules. Their boilerplate — `Copyright [yyyy] [name of
copyright owner]`, `Copyright (C) <year>  <name of author>` — would fail both,
and correctly so if it were ours. It isn't, and editing it is not something a
scaffolder should do. See [placeholders.md](placeholders.md).

The exemption is by file name within those two types, so anything else they add
is still checked.

## CI

`.github/workflows/templates.yml` at the repo root runs the audit on every push
and pull request, then goes further than the audit can:

1. `projtemp check`
2. scaffold every type from `projtemp list --plain`, with `--readme --no-git
   --no-open`, failing on any `Still to fill in by hand` line or any missing
   required file
3. overlay every piece from `projtemp list --pool --plain` onto `open-source`

Step 2 is the end-to-end version of the required-files rule: it asserts the
files exist *after* a scaffold rather than before, which also catches anything
the copy itself drops. Step 3 catches a piece whose contents stopped landing
where they should.

Both loops pass `--author CI`, because a runner has no `git config user.name`
and the author lookup fails without one. `--no-git --no-open` keeps the job off
the network and out of an editor.

This is a repo-level workflow, like `gitleaks.yml` and `links.yml` beside it —
it tests the templates, and is not something a template ships.

## Extending it

`check.py` returns `list[tuple[str, str]]` — where, and what is wrong — and
prints nothing, like every module that isn't `cli.py`. A new rule is a function
returning more of those pairs, plus a call in `run`.

Worth knowing before adding one: the rules here are the ones that hold for
*every* template. `SECURITY.md` parity is the obvious next candidate and is
deliberately absent, because `paid` and `private` lack that file on purpose.
Whether that becomes a rule, a pool piece or a per-template manifest entry is
the open composition question in `notes/FEATURES.md`, not a checker question.
