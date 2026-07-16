#!/usr/bin/env python3
"""Cherry-pick all Gerrit changes sharing a topic into an AOSP/repo workspace.

Usage:
    gerrit_topic_pick.py TOPIC [--gerrit URL] [--status open|merged|any]
                               [--branch BRANCH] [--dry-run] [--continue-on-fail]

Requirements:
    - python3 (stdlib only)
    - run anywhere inside a `repo` workspace (a `.repo/` ancestor must exist)
    - `repo` and `git` in PATH

Gerrit base URL resolution order: --gerrit flag > GERRIT_URL env var >
first `review="..."` attribute found in `repo manifest -o -`.

Auth: tries authenticated `/a/` endpoint if ~/.netrc has an entry for the
Gerrit host (generate the password at Gerrit web UI: Settings > HTTP
Credentials), otherwise falls back to anonymous access:

    machine <gerrit-host> login <username> password <http-password>

The script is idempotent: changes whose Change-Id already appears in the
target project's history are skipped, so after resolving a conflict
(`git cherry-pick --continue`) just re-run the same command.
"""

import argparse
import base64
import json
import netrc
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request


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
    if not m:
        return None
    url = m.group(1)
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url.rstrip("/")


def gerrit_get(base, path):
    host = urllib.parse.urlparse(base).hostname
    auth = None
    try:
        auth = netrc.netrc().authenticators(host)
    except (FileNotFoundError, netrc.NetrcParseError):
        pass

    prefixes = (["/a", ""] if auth else [""])
    last_err = None
    for prefix in prefixes:
        req = urllib.request.Request(base + prefix + path)
        if prefix == "/a":
            token = base64.b64encode(f"{auth[0]}:{auth[2]}".encode()).decode()
            req.add_header("Authorization", "Basic " + token)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode()
            if body.startswith(")]}'"):
                body = body.split("\n", 1)[1]
            return json.loads(body)
        except urllib.error.HTTPError as e:
            last_err = e
        except urllib.error.URLError as e:
            die(f"cannot reach {base}: {e.reason}")
    die(f"gerrit query failed: {last_err}")


def query_changes(base, topic, status, branch):
    q = f'topic:"{topic}"'
    if status != "any":
        q += f" status:{status}"
    if branch:
        q += f' branch:"{branch}"'
    path = ("/changes/?q=" + urllib.parse.quote(q)
            + "&o=CURRENT_REVISION&o=CURRENT_COMMIT&n=500")
    return gerrit_get(base, path)


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


def order_changes(changes):
    """Topological order: within a relation chain, parents first.

    A change depends on another if that other change's current revision is a
    parent commit of this change's current revision. Ties break by ascending
    change number.
    """
    by_rev = {c["current_revision"]: c for c in changes}
    ordered, visiting, done = [], set(), set()

    def visit(c):
        num = c["_number"]
        if num in done or num in visiting:
            return
        visiting.add(num)
        commit = c["revisions"][c["current_revision"]]["commit"]
        for p in commit.get("parents", []):
            parent = by_rev.get(p["commit"])
            if parent is not None:
                visit(parent)
        visiting.discard(num)
        done.add(num)
        ordered.append(c)

    for c in sorted(changes, key=lambda c: c["_number"]):
        visit(c)
    return ordered


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
    ap.add_argument("--gerrit", help="Gerrit base URL, e.g. https://gerrit.example.com")
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

    gerrit = args.gerrit or os.environ.get("GERRIT_URL") or detect_gerrit(root)
    if not gerrit:
        die("cannot determine Gerrit URL; pass --gerrit or set GERRIT_URL")
    gerrit = gerrit.rstrip("/")

    print(f"repo root : {root}")
    print(f"gerrit    : {gerrit}")
    changes = query_changes(gerrit, args.topic, args.status, args.branch)
    if not changes:
        die(f"no changes found for topic {args.topic!r} (status={args.status})")
    print(f"topic     : {args.topic} ({len(changes)} changes)\n")

    paths = project_paths(root)
    failures, skipped_projects = [], []

    for c in order_changes(changes):
        proj = c["project"]
        num = c["_number"]
        ps = c["revisions"][c["current_revision"]]["_number"]
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
