#!/usr/bin/env python3
"""Cherry-pick all Gerrit changes sharing a topic into an AOSP/repo workspace.

Usage:
    gerrit_topic_pick.py TOPIC [--gerrit HOST] [--status open|merged|any]
                               [--branch BRANCH] [--dry-run] [--continue-on-fail]

Requirements:
    - python3 (stdlib only)
    - run anywhere inside a `repo` workspace (a `.repo/` ancestor must exist)
    - `repo`, `git`, `ssh` in PATH

Queries Gerrit over SSH (`ssh -p 29418 <host> gerrit query --format=JSON`),
so it only needs the same ssh key / account that `repo sync` already uses.
Verify access with: ssh -p 29418 <host> gerrit version

Gerrit host resolution order: --gerrit flag > GERRIT_URL env var > first
`review="..."` attribute found in `repo manifest -o -`. Accepted forms:
`host`, `user@host:port`, `ssh://user@host:29418`, or an http(s) URL
(only the hostname is used; ssh port defaults to 29418).

The script is idempotent: changes whose Change-Id already appears in the
target project's history are skipped, so after resolving a conflict
(`git cherry-pick --continue`) just re-run the same command.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse


DEFAULT_SSH_PORT = 29418


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def find_repo_root():
    d = os.getcwd()
    while True:
        if os.path.isdir(os.path.join(d, ".repo")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def detect_gerrit(root):
    try:
        out = subprocess.run(
            ["repo", "manifest", "-o", "-"],
            cwd=root, capture_output=True, text=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    m = re.search(r'review="([^"]+)"', out)
    return m.group(1) if m else None


def parse_ssh_target(s):
    """Normalize host / user@host:port / ssh:// / http(s):// into (dest, port)."""
    s = s.strip().rstrip("/")
    if "://" in s:
        u = urllib.parse.urlparse(s)
        if not u.hostname:
            die(f"cannot parse Gerrit target {s!r}")
        dest = (u.username + "@" if u.username else "") + u.hostname
        port = u.port if (u.scheme == "ssh" and u.port) else DEFAULT_SSH_PORT
        return dest, port
    m = re.match(r"^(?:(?P<user>[^@/]+)@)?(?P<host>[^:/]+)(?::(?P<port>\d+))?$", s)
    if not m:
        die(f"cannot parse Gerrit target {s!r}")
    dest = (m.group("user") + "@" if m.group("user") else "") + m.group("host")
    return dest, int(m.group("port") or DEFAULT_SSH_PORT)


def ssh_query(dest, port, terms):
    cmd = ["ssh", "-p", str(port), dest,
           "gerrit", "query", "--format=JSON", "--current-patch-set"] + terms
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        die(f"ssh gerrit query failed ({' '.join(cmd)}):\n{r.stderr.strip()}")
    changes = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if obj.get("type") == "stats":
            continue
        changes.append(normalize(obj))
    return changes


def normalize(raw):
    ps = raw.get("currentPatchSet")
    if not ps:
        die(f"change {raw.get('number')} has no currentPatchSet in query output")
    return {
        "number": int(raw["number"]),
        "patchset": int(ps["number"]),
        "revision": ps["revision"],
        "parents": ps.get("parents", []),
        "project": raw["project"],
        "subject": raw.get("subject", ""),
        "change_id": raw["id"],
        "status": raw.get("status", ""),
    }


def order_changes(changes):
    """Topological order: within a relation chain, parents first.

    A change depends on another if that other change's current revision is a
    parent commit of this change's current patch set. Ties break by ascending
    change number.
    """
    by_rev = {c["revision"]: c for c in changes}
    ordered, visiting, done = [], set(), set()

    def visit(c):
        num = c["number"]
        if num in done or num in visiting:
            return
        visiting.add(num)
        for sha in c["parents"]:
            parent = by_rev.get(sha)
            if parent is not None:
                visit(parent)
        visiting.discard(num)
        done.add(num)
        ordered.append(c)

    for c in sorted(changes, key=lambda c: c["number"]):
        visit(c)
    return ordered


def project_paths(root):
    out = subprocess.run(
        ["repo", "list"], cwd=root, capture_output=True, text=True, check=True,
    ).stdout
    mapping = {}
    for line in out.splitlines():
        if " : " in line:
            path, proj = line.split(" : ", 1)
            mapping[proj.strip()] = path.strip()
    return mapping


def already_applied(root, path, change_id):
    r = subprocess.run(
        ["git", "log", "--max-count=1", "--format=%H",
         "--grep", f"Change-Id: {change_id}", "HEAD"],
        cwd=os.path.join(root, path), capture_output=True, text=True,
    )
    return r.returncode == 0 and bool(r.stdout.strip())


def main():
    ap = argparse.ArgumentParser(
        description="Cherry-pick all Gerrit changes of a topic into a repo workspace.")
    ap.add_argument("topic", help="Gerrit topic name")
    ap.add_argument("--gerrit",
                    help="Gerrit host: host / user@host:port / ssh:// or http(s):// URL")
    ap.add_argument("--status", default="open", choices=["open", "merged", "any"],
                    help="filter changes by status (default: open)")
    ap.add_argument("--branch", help="only pick changes targeting this branch")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the pick plan without applying anything")
    ap.add_argument("--continue-on-fail", action="store_true",
                    help="keep going after a failed cherry-pick instead of stopping")
    args = ap.parse_args()

    root = find_repo_root()
    if not root:
        die("not inside a repo workspace (no .repo directory found in ancestors)")

    target = args.gerrit or os.environ.get("GERRIT_URL") or detect_gerrit(root)
    if not target:
        die("cannot determine Gerrit host; pass --gerrit or set GERRIT_URL")
    dest, port = parse_ssh_target(target)

    terms = [f'topic:"{args.topic}"']
    if args.status != "any":
        terms.append(f"status:{args.status}")
    if args.branch:
        terms.append(f'branch:"{args.branch}"')

    print(f"repo root : {root}")
    print(f"gerrit    : ssh://{dest}:{port}")
    changes = ssh_query(dest, port, terms)
    if not changes:
        die(f"no changes found for topic {args.topic!r} (status={args.status})")
    print(f"topic     : {args.topic} ({len(changes)} changes)\n")

    paths = project_paths(root)
    failures, skipped_projects = [], []

    for c in order_changes(changes):
        proj = c["project"]
        num = c["number"]
        ps = c["patchset"]
        label = f'{num}/{ps} [{proj}] "{c["subject"]}"'
        path = paths.get(proj)

        if path is None:
            print(f"SKIP {label}: project not in local manifest")
            skipped_projects.append(label)
            continue
        if already_applied(root, path, c["change_id"]):
            print(f"SKIP {label}: already applied in {path}")
            continue

        print(f"PICK {label} -> {path}")
        if args.dry_run:
            continue
        r = subprocess.run(
            ["repo", "download", "--cherry-pick", proj, f"{num}/{ps}"], cwd=root)
        if r.returncode != 0:
            failures.append(label)
            print(f"\ncherry-pick FAILED for {label}", file=sys.stderr)
            print(f"resolve it in: {os.path.join(root, path)}", file=sys.stderr)
            print("  git status                      # inspect conflicts",
                  file=sys.stderr)
            print("  git add <files> && git cherry-pick --continue",
                  file=sys.stderr)
            print("then re-run this script; applied changes are skipped "
                  "automatically.\n", file=sys.stderr)
            if not args.continue_on_fail:
                sys.exit(2)

    print()
    if args.dry_run:
        print("dry-run only, nothing applied.")
    if skipped_projects:
        print(f"{len(skipped_projects)} change(s) skipped: project missing locally.")
    if failures:
        die(f"{len(failures)} change(s) failed to apply", code=2)
    print("done.")


if __name__ == "__main__":
    main()
