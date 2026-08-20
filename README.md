# ProjectTemplate

My starting points for new repos, so I don't set the same things up every time.

Each directory is one project type. Copy the one needed into a new repo and start writing code.

```sh
cp -R ProjectTemplate/<type>/. proj/
cd proj && git init && git add . && git commit -m "init" && code .
```

Most files in there are empty on purpose — the structure exists so nothing gets forgotten, the content gets written per project. Before the first commit: fix the copyright line, swap out placeholders, write the README.

The workflows at the root of this repo are for this repo only.
