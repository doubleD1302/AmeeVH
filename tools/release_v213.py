#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publish GitHub Release v2.1.3 in the safe order from docs/RELEASE_ASSET_UPLOAD.md.

    python tools/release_v213.py draft     # create a DRAFT release and upload every asset (resumable)
    python tools/release_v213.py verify    # compare every uploaded asset's size + SHA256 with the local file
    python tools/release_v213.py publish   # make it public and "latest" (only after verify passes)

The token is read from GH_TOKEN, .secrets/github_token.txt, or `gh auth token` and is never printed.
Title = version number only, body <= 100 words (docs/GITHUB_RELEASE_RULES.md).
"""
from __future__ import annotations

import hashlib
import http.client
import json
import os
import re
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
REPO = "doubleD1302/AmeeVH"
TAG = "v2.1.3"
TITLE = "2.1.3"
NOTES = (ROOT / "work" / "release_v2.1.3" / "RELEASE_NOTES.md").read_text(encoding="utf-8").strip()
ASSETS = [
    "StellaSora-Windows_v2.1.3.exe",
    "StellaSora-Android_v2.1.3.apk",
    "StellaSora_AssetBundles_VI.zip",
    "StellaSora_Android_AssetBundles_VI.zip",
    "data_patched_vi.arcx",
    "lua_patched_vi.arcx",
    "patch_manifest.json",
    "android_patch_manifest.json",
    "android_localadb_launcher.json",
    "SHA256SUMS.txt",
]

_TOKEN_CACHE: str | None = None


def token() -> str:
    global _TOKEN_CACHE
    if _TOKEN_CACHE:
        return _TOKEN_CACHE
    env_tok = os.environ.get("GH_TOKEN", "").strip()
    if env_tok:
        _TOKEN_CACHE = env_tok
        return _TOKEN_CACHE
    p = ROOT / ".secrets" / "github_token.txt"
    value = p.read_text(encoding="utf-8").strip() if p.is_file() else ""
    if value:
        _TOKEN_CACHE = value
        return _TOKEN_CACHE
    try:
        gh_tok = subprocess.check_output(["gh", "auth", "token"], text=True, encoding="utf-8").strip()
        if gh_tok:
            _TOKEN_CACHE = gh_tok
            return _TOKEN_CACHE
    except Exception:
        pass
    sys.exit("Missing GitHub token (checked GH_TOKEN, .secrets/github_token.txt, gh auth token)")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def api(method: str, url: str, body: dict | None = None) -> dict | list:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        method=method,
        headers={
            "Authorization": f"Bearer {token()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "stellasora-release-script",
            **({"Content-Type": "application/json"} if body is not None else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
        return json.loads(raw.decode("utf-8")) if raw else {}


def validate_text() -> None:
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", TITLE):
        sys.exit("Title must be the version number only.")
    words = len(NOTES.split())
    if not 0 < words <= 100:
        sys.exit(f"Release notes have {words} words (limit 100).")
    print(f"release text ok: title={TITLE!r}, {words} words")


def find_release() -> dict | None:
    for rel in api("GET", f"https://api.github.com/repos/{REPO}/releases?per_page=30"):
        if rel.get("tag_name") == TAG:
            return rel
    return None


def upload(rel: dict, name: str) -> None:
    path = DIST / name
    size = path.stat().st_size
    want = sha256(path)
    existing = {a["name"]: a for a in rel.get("assets", [])}
    if name in existing:
        ex = existing[name]
        ex_digest = (ex.get("digest") or "").removeprefix("sha256:")
        if ex["size"] == size and (not ex_digest or ex_digest == want):
            print(f"  skip {name} (already uploaded, {size:,} bytes)")
            return
        api("DELETE", f"https://api.github.com/repos/{REPO}/releases/assets/{ex['id']}")
    base = rel["upload_url"].split("{")[0]
    parsed = urllib.parse.urlparse(base)
    query = urllib.parse.urlencode({"name": name})
    ctype = (
        "application/json"
        if name.endswith(".json")
        else "text/plain"
        if name.endswith(".txt")
        else "application/octet-stream"
    )
    print(f"  upload {name} ({size:,} bytes) ...", flush=True)
    t0 = time.time()
    conn = http.client.HTTPSConnection(parsed.netloc, timeout=600, context=ssl.create_default_context())
    conn.putrequest("POST", f"{parsed.path}?{query}")
    conn.putheader("Authorization", f"Bearer {token()}")
    conn.putheader("Accept", "application/vnd.github+json")
    conn.putheader("User-Agent", "stellasora-release-script")
    conn.putheader("Content-Type", ctype)
    conn.putheader("Content-Length", str(size))
    conn.endheaders()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            conn.send(chunk)
    resp = conn.getresponse()
    payload = resp.read()
    conn.close()
    if resp.status not in (200, 201):
        sys.exit(f"upload of {name} failed: HTTP {resp.status} {payload[:200]!r}")
    print(f"    done in {time.time() - t0:.0f}s")


def cmd_draft() -> None:
    validate_text()
    missing = [n for n in ASSETS if not (DIST / n).is_file()]
    if missing:
        sys.exit(f"Missing local assets: {missing}")
    rel = find_release()
    if rel and not rel.get("draft"):
        sys.exit(f"Release {TAG} is already public; refusing to touch it.")
    if rel is None:
        rel = api(
            "POST",
            f"https://api.github.com/repos/{REPO}/releases",
            {
                "tag_name": TAG,
                "target_commitish": "main",
                "name": TITLE,
                "body": NOTES,
                "draft": True,
                "prerelease": False,
            },
        )
        print(f"created draft release id={rel['id']}")
    else:
        print(f"reusing draft release id={rel['id']}")
    for name in ASSETS:
        rel = api("GET", f"https://api.github.com/repos/{REPO}/releases/{rel['id']}")
        upload(rel, name)
    print("draft ready; run verify next")


def cmd_verify() -> bool:
    rel = find_release()
    if rel is None:
        sys.exit(f"No {TAG} release found.")
    remote = {a["name"]: a for a in rel["assets"]}
    sums = {}
    sums_file = DIST / "SHA256SUMS.txt"
    for line in sums_file.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 2:
            sums[parts[1].lstrip("*")] = parts[0].lower()
    ok = True
    print(f"release id={rel['id']} draft={rel['draft']} title={rel['name']!r}")
    for name in ASSETS:
        local = DIST / name
        a = remote.get(name)
        if a is None:
            print(f"  MISSING {name}")
            ok = False
            continue
        digest = (a.get("digest") or "").removeprefix("sha256:")
        want = sha256(local)
        good = a["size"] == local.stat().st_size and digest == want
        listed = sums.get(name)
        if listed is not None and listed != want:
            good = False
            print(f"  SHA256SUMS.txt disagrees for {name}")
        print(f"  {'OK ' if good else 'BAD'} {name}  {a['size']:,} bytes")
        ok &= good
    extra = sorted(set(remote) - set(ASSETS))
    if extra:
        print(f"  unexpected extra assets: {extra}")
        ok = False
    if sum(1 for n in remote if n.endswith(".exe")) != 1:
        print("  release must contain exactly one .exe")
        ok = False
    print("VERIFY", "PASSED" if ok else "FAILED")
    return ok


def cmd_publish() -> None:
    if not cmd_verify():
        sys.exit("Refusing to publish: verification failed.")
    rel = find_release()
    api(
        "PATCH",
        f"https://api.github.com/repos/{REPO}/releases/{rel['id']}",
        {"draft": False, "prerelease": False, "make_latest": "true", "name": TITLE, "body": NOTES},
    )
    live = api("GET", f"https://api.github.com/repos/{REPO}/releases/tags/{TAG}")
    print(f"published: tag={live['tag_name']} title={live['name']!r} draft={live['draft']} url={live['html_url']}")


if __name__ == "__main__":
    {"draft": cmd_draft, "verify": cmd_verify, "publish": cmd_publish}.get(
        sys.argv[1] if len(sys.argv) > 1 else "", lambda: sys.exit(__doc__)
    )()
