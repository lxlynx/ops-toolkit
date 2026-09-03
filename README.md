# ops-toolkit

Three scripts I had rewritten from memory on enough machines to justify keeping them
somewhere. Nothing here needs a package manager: bash, coreutils, git and Python 3.8 are
the entire dependency list, because these are the tools you want on the box that is
already having a bad day.

| Script | What it does |
| --- | --- |
| `rotate-logs.sh` | Size-based log rotation where logrotate isn't installed or isn't allowed |
| `repo-health.py` | Reports which git repos on a machine hold work that exists nowhere else |
| `json-reconcile.py` | Diffs two JSON exports on a key field and exits nonzero if they disagree |

## Install

```bash
git clone https://github.com/lxlynx/ops-toolkit.git
chmod +x ops-toolkit/*.sh ops-toolkit/*.py
```

## rotate-logs.sh

```bash
./rotate-logs.sh --keep 3 --size 5120 --dry-run /var/log/myapp
```

Keeps `app.log.1.gz` through `app.log.N.gz`, then truncates the original in place rather
than renaming it. That detail matters: a process holding an open file descriptor keeps
writing to the same inode, so nothing needs a restart or a SIGHUP to find its log again.
Always run it once with `--dry-run`.

## repo-health.py

```bash
./repo-health.py ~/src --depth 3 --problems
./repo-health.py ~/src --json | jq '.[] | select(.ahead > 0) | .path'
```

Walks a directory for git repos and prints branch, age of the last commit, and anything
worth knowing before you wipe the disk: uncommitted changes, unpushed commits, stashes,
missing remote. `--problems` hides the repos that are fine.

## json-reconcile.py

```bash
./json-reconcile.py invoices.json ledger.json --key invoice_id \
  --fields amount,currency,status --tolerance 0.01
```

Joins two exports on a key and reports what is only on one side plus any field-level
disagreements. `--tolerance` exists because floating point money from two systems is
rarely bit-identical. Exit status is 1 when the sides disagree, which makes it usable as
a cron or CI check without parsing the output.

## Licence

MIT, see [LICENSE](LICENSE).
