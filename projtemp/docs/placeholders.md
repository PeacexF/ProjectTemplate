# Placeholders

After the template and every piece are in place, one pass walks the whole
project and rewrites three things.

| Marker | Becomes | Where it lives |
| --- | --- | --- |
| `[repo name]` | the project name | `CONTRIBUTING.md` |
| `[DATE]` | today, ISO 8601 | `global/disclaimer/DISCLAIMER.md` |
| `^Copyright (c) <year> <name>` | `Copyright (c) <year> <author>` | `LICENSE` |

The run reports which files it touched:

```
  filled placeholders in 2 files
    CONTRIBUTING.md
    DISCLAIMER.md
```

## What gets scanned

Every file under the project, recursively, with four exclusions:

- anything under `.git/` — the pass runs before `git init`, but the guard means
  it is also safe to run over an existing repo
- symlinks, so a link out of the tree is never written through
- files over 2 MB
- anything that does not decode as UTF-8

A file that cannot be read is skipped rather than failing the run.

## The copyright line

```python
re.compile(r"^Copyright \(c\) \d{4}(?:-\d{4})? .*$", re.MULTILINE)
```

Anchored at column 0, and matching lowercase `(c)` only. Both constraints are
load-bearing. The Apache and AGPL license files carry their own boilerplate:

```
   Copyright [yyyy] [name of copyright owner]        apache-2.0/LICENSE:189
    Copyright (C) <year>  <name of author>           agplv3/LICENSE:633
```

Both are indented, and the AGPL one uses a capital `C`, so neither is matched
and neither is rewritten. That is the intended outcome — those files are
verbatim license text, and editing them is not something a scaffolder should do.
A run of either type says so at the end:

```
Note: apache-2.0/LICENSE is verbatim license text and was left untouched.
```

Year ranges match too, so a `Copyright (c) 2023-2025 Someone` line in a
hand-edited template is collapsed to the single current year.

The author comes from `--author`, then the stored `author`, then
`git config user.name`. With none of the three the run fails before writing
anything:

```
Error: no author name: set one with `git config --global user.name`,
`projtemp config --set-author 'Your Name'`, or --author
```

## Leftovers

After everything else, `*.md` files are scanned for bracket markers the pass
does not know how to fill:

```python
re.compile(r"\[(?:yyyy|name of [^\]]+|repo name|DATE)\]")
```

Anything found is listed under `Still to fill in by hand:`. This is a reminder,
not an error — the exit code is unaffected.

Two limits worth knowing. It only reads `*.md`, so the `[yyyy]` in
`apache-2.0/LICENSE` never appears here (the verbatim-license note covers that
case instead). And the pattern is a fixed list, so a marker invented in a
template — `[owner]`, say — is neither filled nor reported. Adding one today
means editing `placeholders.py`; `notes/FEATURES.md` has a per-template manifest
parked as the fix.

## `--readme`

Separate from the substitution pass and off by default. It writes
`# <project name>` into `README.md`, but only when that file is missing or
blank, so it will not clobber a README with content in it — which is the case
that matters under `--force`. Templates ship an empty `README.md`, so on a fresh
scaffold it always fires.

## Checking a template's markers

`projtemp check` audits the templates for markers this pass could not fill,
before they ever reach a project. See [checking.md](checking.md).
