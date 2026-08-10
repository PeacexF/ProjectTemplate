# Contributing

This repo is my personal set of starting points for new repos. It's public because it may as well be, not because it's a community project. Contributions are welcome within that framing.

Practical consequence: I'll turn down changes that are fine in general but don't match how I work. That's not a judgement on the change, it just isn't mine to carry. Open an issue before doing real work so neither of us wastes it.

## What's useful

- Fixing something broken — a config that doesn't parse, a wrong path, a dead link, a stale flag.
- Bringing a template up to date with current tooling defaults.
- Removing files that no longer earn their place.
- Better ignore rules for `.gitignore`, `.gitleaksignore`, `.lycheeignore`.

## What probably isn't

- Filling in the empty files. They're empty on purpose — the structure exists so nothing gets forgotten, the content gets written per project.
- New project types. Ask first. I only add types I actually use.
- Opinion swaps — different formatter, different test runner, different layout — unless something is genuinely broken or unmaintained.
- Anything that makes a template assume more about a project than it has to.

## Ground rules

- One concern per pull request.
- Keep templates generic. No names, no personal URLs, no leftover placeholders that only make sense in my projects.
- A template's own files stay in that template's directory. Everything at the repo root — `.github/workflows`, `LICENSE`, this file — is for this repo only, so don't copy it into a template or wire it up as one.
- Say which templates you touched and why in the PR description. If the change is a version bump, say what breaks without it.
- Test it the way it gets used: copy the directory into a scratch repo, `git init`, and check the thing you changed actually works from a clean start.

## CI

Two workflows run on pull requests:

- **gitleaks** — scans for committed secrets. If it flags a placeholder or an example value, add a pattern to `.gitleaksignore` rather than reshaping the file around the scanner.
- **lychee** — checks links. Unreachable-by-design URLs (localhost, `example.com`, sites that block CI) belong in `.lycheeignore`.

Both need to pass. If one fails for a reason unrelated to your change, say so in the PR and I'll look.

## Licensing

The repo is MIT. By opening a pull request you're agreeing your contribution goes out under the same license. Don't paste in code you don't have the right to relicense.
