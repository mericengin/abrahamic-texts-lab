#!/usr/bin/env python3
"""Fetch raw source texts listed in data/sources.toml into data/raw/<id>/.

Safe by default: with no flags it only prints a plan and downloads nothing.
Use --phase 1 or --phase 2 to limit the plan to one project phase.
Pass --execute to actually fetch. Only sources whose status is "ready" are
fetched; "verify", "manual" and "blocked" sources are reported and skipped.

Each fetched source gets data/raw/<id>/MANIFEST.json recording the URL, UTC
retrieval time, license, and a SHA-256 (files) or commit hash (git).
Standard library only. No retries, no credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tomllib
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "sources.toml"
RAW = ROOT / "data" / "raw"
USER_AGENT = "abrahamic-texts-lab/0.1 (non-profit research; polite single requests)"


def load_sources() -> list[dict]:
    with MANIFEST.open("rb") as fh:
        return tomllib.load(fh)["source"]


def describe(src: dict) -> str:
    return f"{src['id']:<22} P{src['phase']} {src['status']:<8} {src['kind']:<6} {src['license']}"


def file_list(src: dict) -> list[dict]:
    """Files of a kind="file" source: the `files` list, or the single url/filename pair."""
    return src.get("files") or [{"url": src["url"], "filename": src["filename"]}]


def fetch_file(src: dict, dest: Path) -> dict:
    dest.mkdir(parents=True, exist_ok=True)
    records = []
    for item in file_list(src):
        req = urllib.request.Request(item["url"], headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310 (https URLs from our own manifest)
            data = resp.read()
        (dest / item["filename"]).write_bytes(data)
        records.append({"url": item["url"], "file": item["filename"], "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        print(f"    {item['filename']}: {len(data):,} bytes")
    return {"files": records}


def run(cmd: list[str], cwd: Path | None = None) -> str:
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def fetch_git(src: dict, dest: Path) -> dict:
    paths = src.get("paths", [])
    cmd = ["git", "clone", "--depth", "1"]
    if paths:
        cmd += ["--filter=blob:none", "--sparse"]
    run(cmd + [src["url"], str(dest)])
    if paths:
        run(["git", "sparse-checkout", "set", *paths], cwd=dest)
    return {"commit": run(["git", "rev-parse", "HEAD"], cwd=dest), "paths": paths or "all"}


def fetch(src: dict) -> None:
    dest = RAW / src["id"]
    if (dest / "MANIFEST.json").exists():
        print(f"  skip {src['id']}: already fetched")
        return
    result = fetch_file(src, dest) if src["kind"] == "file" else fetch_git(src, dest)
    record = {
        "id": src["id"],
        "status_at_fetch": src["status"],
        "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "license": src["license"],
        "license_url": src["license_url"],
        "attribution": src["attribution"],
        **result,
    }
    (dest / "MANIFEST.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"  fetched {src['id']}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*", help="source ids to act on (default: all)")
    ap.add_argument("--phase", type=int, choices=(1, 2), help="only act on sources planned for this project phase")
    ap.add_argument("--execute", action="store_true", help="actually download (default is a dry-run plan)")
    ap.add_argument("--allow-unverified", action="store_true", help='also fetch "verify" sources, but only ones named explicitly by id (owner-approved downloads)')
    args = ap.parse_args()

    sources = load_sources()
    known = {s["id"] for s in sources}
    unknown = [i for i in args.ids if i not in known]
    if unknown:
        print(f"unknown ids: {', '.join(unknown)}", file=sys.stderr)
        return 2
    chosen = [
        s for s in sources
        if (not args.ids or s["id"] in args.ids) and (args.phase is None or s["phase"] == args.phase)
    ]

    allowed = {"ready"} | ({"verify"} if args.allow_unverified and args.ids else set())
    print(("EXECUTE" if args.execute else "DRY RUN (nothing will be downloaded)") + "\n")
    for src in chosen:
        print(describe(src))
        if src["status"] not in allowed or src["kind"] == "manual":
            print(f"  not fetched: status is '{src['status']}', kind is '{src['kind']}'. {src['notes'][:200]}")
            continue
        if args.execute:
            fetch(src)
        elif src["kind"] == "file":
            for item in file_list(src):
                print(f"  would fetch {item['url']} -> data/raw/{src['id']}/{item['filename']}")
        else:
            print(f"  would fetch {src['url']} -> data/raw/{src['id']}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
