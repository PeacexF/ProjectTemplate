# ProjectTemplate

My starting points for new repos, so I don't set the same things up every time.

Each directory is one project type. Copy the one needed into a new repo and start writing code.

```sh
cp -R ProjectTemplate/<type>/. proj/
cd proj && git init && git add . && git commit -m "init" && code .
```

Most files in there are empty on purpose — the structure exists so nothing gets forgotten, the content gets written per project. Before the first commit: fix the copyright line, swap out placeholders, write the README.

`projtemp/` is my own CLI for doing all of the above — copy, fill the placeholders, init, and push if the remote is already there. It lives here because the templates do, not because it's ready for anyone else to use. Personal tooling, not a product.

The workflows at the root of this repo are for this repo only.
