#!/usr/bin/env python3
"""Read and write Epic/story issue bodies on GitHub or Gitea.

  tracker.py get    REF [-o FILE]              print (or save) the issue body
  tracker.py put    REF FILE                   replace the issue body with FILE
  tracker.py create --title T --body-file F    open an issue; prints its number
  tracker.py comment REF --body TEXT           add a comment

REF is `#13`, `13`, or a full issue URL. The forge comes from the `origin`
remote: github.com uses the `gh` CLI (already authenticated); anything else is
treated as Gitea and uses its REST API with `GITEA_TOKEN` (or `TEA_TOKEN`).
Set `TRACKER=github|gitea` to override detection.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


def sh(*cmd: str, stdin: str | None = None) -> str:
    try:
        out = subprocess.run(cmd, input=stdin, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        sys.exit(f"tracker: {cmd[0]} is not installed")
    except subprocess.CalledProcessError as exc:
        sys.exit(f"tracker: {' '.join(cmd[:3])} failed: {exc.stderr.strip()}")
    return out.stdout


def remote() -> tuple[str, str, str]:
    """(host, owner, repo) from the origin remote."""
    url = sh("git", "remote", "get-url", "origin").strip()
    m = re.match(r"^(?:https?://(?:[^@/]+@)?|ssh://(?:[^@/]+@)?|[^@]+@)([^/:]+)(?::\d+)?[:/](.+?)/(.+?)(?:\.git)?/?$", url)
    if not m:
        sys.exit(f"tracker: cannot parse origin remote {url!r}")
    return m.group(1), m.group(2), m.group(3)


def number(ref: str) -> str:
    m = re.search(r"(\d+)\s*$", ref.strip())
    if not m:
        sys.exit(f"tracker: {ref!r} is not an issue reference")
    return m.group(1)


class GitHub:
    def get(self, n: str) -> str:
        return json.loads(sh("gh", "issue", "view", n, "--json", "body"))["body"]

    def put(self, n: str, body: str) -> None:
        sh("gh", "issue", "edit", n, "--body-file", "-", stdin=body)

    def create(self, title: str, body: str) -> str:
        url = sh("gh", "issue", "create", "--title", title, "--body-file", "-", stdin=body).strip()
        return number(url)

    def comment(self, n: str, body: str) -> None:
        sh("gh", "issue", "comment", n, "--body-file", "-", stdin=body)


class Gitea:
    def __init__(self, host: str, owner: str, repo: str):
        base = os.environ.get("GITEA_URL") or f"https://{host}"
        self.api = f"{base.rstrip('/')}/api/v1/repos/{owner}/{repo}"
        self.token = os.environ.get("GITEA_TOKEN") or os.environ.get("TEA_TOKEN")
        if not self.token:
            sys.exit("tracker: set GITEA_TOKEN (or TEA_TOKEN) for Gitea")

    def call(self, method: str, path: str, payload: dict | None = None) -> dict:
        req = urllib.request.Request(
            self.api + path, method=method,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={"Authorization": f"token {self.token}", "Content-Type": "application/json",
                     "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as exc:
            sys.exit(f"tracker: Gitea {method} {path} -> {exc.code} {exc.reason}")

    def get(self, n: str) -> str:
        return self.call("GET", f"/issues/{n}").get("body") or ""

    def put(self, n: str, body: str) -> None:
        self.call("PATCH", f"/issues/{n}", {"body": body})

    def create(self, title: str, body: str) -> str:
        return str(self.call("POST", "/issues", {"title": title, "body": body})["number"])

    def comment(self, n: str, body: str) -> None:
        self.call("POST", f"/issues/{n}/comments", {"body": body})


def forge():
    kind = os.environ.get("TRACKER")
    host, owner, repo = remote()
    if kind == "github" or (kind is None and host == "github.com"):
        return GitHub()
    return Gitea(host, owner, repo)


def main() -> int:
    ap = argparse.ArgumentParser(description="Read and write Epic/story issue bodies (GitHub or Gitea).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("get"); p.add_argument("ref"); p.add_argument("-o", "--output")
    p = sub.add_parser("put"); p.add_argument("ref"); p.add_argument("file")
    p = sub.add_parser("create"); p.add_argument("--title", required=True); p.add_argument("--body-file", required=True)
    p = sub.add_parser("comment"); p.add_argument("ref"); p.add_argument("--body", required=True)
    args = ap.parse_args()
    f = forge()
    if args.cmd == "get":
        body = f.get(number(args.ref))
        if args.output:
            Path(args.output).write_text(body, encoding="utf-8")
            print(args.output)
        else:
            print(body)
    elif args.cmd == "put":
        f.put(number(args.ref), Path(args.file).read_text(encoding="utf-8"))
        print(f"updated #{number(args.ref)}")
    elif args.cmd == "create":
        print("#" + f.create(args.title, Path(args.body_file).read_text(encoding="utf-8")))
    elif args.cmd == "comment":
        f.comment(number(args.ref), args.body)
        print(f"commented on #{number(args.ref)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
