#!/usr/bin/env python3
"""Report the state of every git repository under a directory.

Answers the question you ask yourself before wiping a laptop or a build box:
which of these repos has work in it that exists nowhere else?

Standard library only. Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

SKIP_DIRS = {"node_modules", "vendor", ".venv", "venv", "__pycache__", ".cache"}


def git(repo: Path, *args: str) -> Optional[str]:
    """Run a git command in repo, returning stripped stdout or None on failure."""
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return proc.stdout.strip() if proc.returncode == 0 else None


def find_repos(root: Path, max_depth: int) -> List[Path]:
    """Walk root looking for .git, without descending into repos we already found."""
    found: List[Path] = []
    stack = [(root, 0)]
    while stack:
        current, depth = stack.pop()
        if (current / ".git").exists():
            found.append(current)
            continue  # nested repos are somebody else's problem
        if depth >= max_depth:
            continue
        try:
            children = sorted(p for p in current.iterdir() if p.is_dir())
        except PermissionError:
            continue
        for child in children:
            if child.name in SKIP_DIRS or child.name.startswith("."):
                continue
            stack.append((child, depth + 1))
    return sorted(found)


def inspect(repo: Path) -> Dict[str, object]:
    branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD") or "?"
    status = git(repo, "status", "--porcelain") or ""
    dirty = len([line for line in status.splitlines() if line.strip()])
    has_remote = bool(git(repo, "remote"))

    ahead = behind = 0
    counts = git(repo, "rev-list", "--left-right", "--count", "@{upstream}...HEAD")
    if counts:
        parts = counts.split()
        if len(parts) == 2:
            behind, ahead = int(parts[0]), int(parts[1])

    last_epoch = git(repo, "log", "-1", "--format=%ct")
    age_days = int((time.time() - int(last_epoch)) // 86400) if last_epoch else -1

    stash = git(repo, "stash", "list") or ""
    stashes = len([line for line in stash.splitlines() if line.strip()])

    notes = []
    if dirty:
        notes.append(f"dirty:{dirty}")
    if ahead:
        notes.append(f"ahead:{ahead}")
    if behind:
        notes.append(f"behind:{behind}")
    if stashes:
        notes.append(f"stash:{stashes}")
    if not has_remote:
        notes.append("no-remote")

    return {
        "path": str(repo),
        "branch": branch,
        "dirty": dirty,
        "ahead": ahead,
        "behind": behind,
        "stashes": stashes,
        "has_remote": has_remote,
        "age_days": age_days,
        "needs_attention": bool(notes),
        "notes": notes or ["ok"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", nargs="?", default=".", help="directory to scan")
    parser.add_argument("--depth", type=int, default=3, help="max search depth")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument(
        "--problems", action="store_true", help="only print repos needing attention"
    )
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 1

    reports = [inspect(repo) for repo in find_repos(root, args.depth)]
    if args.problems:
        reports = [r for r in reports if r["needs_attention"]]

    if args.as_json:
        print(json.dumps(reports, indent=2))
        return 0

    if not reports:
        print("nothing to report")
        return 0

    width = max(len(Path(str(r["path"])).name) for r in reports)
    for r in reports:
        name = Path(str(r["path"])).name
        age = f"{r['age_days']}d" if r["age_days"] >= 0 else "-"
        print(f"{name:<{width}}  {str(r['branch']):<20} {age:>5}  {' '.join(r['notes'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
