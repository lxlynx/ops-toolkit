<div align="center">

# ops-toolkit

**Three scripts I had rewritten from memory on enough machines to justify keeping them somewhere.**

[![shell](https://img.shields.io/badge/shell-bash-black?style=flat-square&logo=gnubash)](#quick-start)
[![deps](https://img.shields.io/badge/dependencies-bash%20%7C%20coreutils%20%7C%20git%20%7C%20python3-lightgrey?style=flat-square)](#quick-start)
[![license](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

</div>

## About

These are the tools you want already present on a host you have just SSH'd
into for the first time, which is why the dependency list stops at bash,
coreutils, git, and the system Python. Each script is self-contained: no shared
library, no install step, so copying one file to a host is a complete
deployment.

## Quick start

```bash
git clone https://github.com/lxlynx/ops-toolkit
cd ops-toolkit
ls bin/
# each script has its own -h; nothing is installed globally
```

## Configuration

| Key | Description |
| --- | --- |
| `bin/` | the scripts themselves, each runnable standalone |
| `python 3.8+` | the only interpreter dependency, already on most hosts |
| `bash / coreutils / git` | everything else — no package manager needed |
## Roadmap

- [ ] `install` subcommand that symlinks into `~/.local/bin`
- [ ] shellcheck in CI
- [ ] Per-script man pages

## Contributing

Issues and pull requests are welcome. Please keep changes small and focused,
and add a test for any behaviour change — every repository here ships with a
runnable test suite and no third-party dependencies, so CI is just
`python3 -m unittest` / `bash test_*.sh`.

## License

[MIT](LICENSE)
