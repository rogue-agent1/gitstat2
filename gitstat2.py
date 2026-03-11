#!/usr/bin/env python3
"""gitstat2 - Git repository statistics and contributor analysis.

Single-file, zero-dependency CLI.
"""

import sys
import argparse
import subprocess
import re
from collections import defaultdict


def run(cmd, cwd=None):
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL, cwd=cwd).strip()
    except subprocess.CalledProcessError:
        return ""


def cmd_summary(args):
    cwd = args.repo
    commits = int(run("git rev-list --count HEAD", cwd) or 0)
    authors = len(set(run("git log --format='%ae'", cwd).split("\n"))) if commits else 0
    branches = len(run("git branch -a", cwd).split("\n")) if commits else 0
    tags = len([t for t in run("git tag", cwd).split("\n") if t])
    first = run("git log --reverse --format='%ai' | head -1", cwd)
    last = run("git log -1 --format='%ai'", cwd)
    files = int(run("git ls-files | wc -l", cwd) or 0)
    loc = int(run("git ls-files | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}'", cwd) or 0)

    print(f"  Commits:   {commits:,}")
    print(f"  Authors:   {authors}")
    print(f"  Branches:  {branches}")
    print(f"  Tags:      {tags}")
    print(f"  Files:     {files:,}")
    print(f"  Lines:     {loc:,}")
    if first: print(f"  First:     {first[:10]}")
    if last: print(f"  Latest:    {last[:10]}")


def cmd_authors(args):
    cwd = args.repo
    out = run(f"git shortlog -sne HEAD", cwd)
    if not out:
        print("  No commits"); return
    lines = out.strip().split("\n")
    for line in lines[:args.limit]:
        line = line.strip()
        m = re.match(r'(\d+)\s+(.*)', line)
        if m:
            count, author = int(m.group(1)), m.group(2)
            bar = "█" * min(count, 30)
            print(f"  {count:5d}  {bar}  {author}")


def cmd_activity(args):
    cwd = args.repo
    out = run("git log --format='%ai' | cut -c1-7 | sort | uniq -c | sort -k2", cwd)
    if not out:
        print("  No commits"); return
    lines = out.strip().split("\n")
    max_count = max(int(l.strip().split()[0]) for l in lines) if lines else 1
    for line in lines[-args.months:]:
        parts = line.strip().split()
        count, month = int(parts[0]), parts[1]
        bar_len = int(count / max_count * 30)
        bar = "█" * bar_len
        print(f"  {month}  {count:4d}  {bar}")


def cmd_files(args):
    """Top files by commit frequency."""
    cwd = args.repo
    out = run("git log --pretty=format: --name-only | sort | uniq -c | sort -rn | head -20", cwd)
    if not out:
        print("  No data"); return
    for line in out.strip().split("\n")[:args.limit]:
        parts = line.strip().split(None, 1)
        if len(parts) == 2:
            print(f"  {int(parts[0]):5d}  {parts[1]}")


def main():
    p = argparse.ArgumentParser(prog="gitstat2", description="Git repo statistics")
    p.add_argument("-r", "--repo", default=".")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("summary", aliases=["s"], help="Repo summary")
    s = sub.add_parser("authors", aliases=["a"], help="Top authors")
    s.add_argument("-n", "--limit", type=int, default=15)
    s = sub.add_parser("activity", help="Monthly activity")
    s.add_argument("-m", "--months", type=int, default=24)
    s = sub.add_parser("files", help="Most-changed files")
    s.add_argument("-n", "--limit", type=int, default=20)
    args = p.parse_args()
    if not args.cmd: p.print_help(); return 1
    cmds = {"summary": cmd_summary, "s": cmd_summary, "authors": cmd_authors,
            "a": cmd_authors, "activity": cmd_activity, "files": cmd_files}
    return cmds[args.cmd](args) or 0


if __name__ == "__main__":
    sys.exit(main())
