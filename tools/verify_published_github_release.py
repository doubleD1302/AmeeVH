# -*- coding: utf-8 -*-
import json
import urllib.request
import re

url = "https://api.github.com/repos/doubleD1302/AmeeVH/releases/tags/v1.0.8"
req = urllib.request.Request(url, headers={"User-Agent": "Antigravity-Release-Verifier"})

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))

print(f"Tag: {data.get('tag_name')}")
print(f"Title: {repr(data.get('name'))}")
body = data.get('body', '')
word_count = len(body.split())
print(f"Body word count: {word_count}")
print(f"Body preview:\n{body}")

assert data.get('tag_name') == "v1.0.8"
assert data.get('name') == "1.0.8", f"Title must be '1.0.8', got {data.get('name')}"
assert word_count <= 100, f"Body has {word_count} words (> 100)"

assets = data.get('assets', [])
print(f"\nTotal assets on release: {len(assets)}")
for a in assets:
    print(f"  - {a['name']}: {a['size']:,} bytes ({a['browser_download_url']})")

expected_names = {
    "StellaSora-Windows_v1.0.8.exe",
    "StellaSora-Android_v1.0.8.apk",
    "android_localadb_launcher.json",
    "patch_manifest.json",
    "android_patch_manifest.json",
    "data_patched_vi.arcx",
    "lua_patched_vi.arcx",
    "StellaSora_AssetBundles_VI.zip",
    "StellaSora_Android_AssetBundles_VI.zip",
    "SHA256SUMS.txt",
}
actual_names = {a['name'] for a in assets}
missing = expected_names - actual_names
if missing:
    raise AssertionError(f"Missing assets: {missing}")

print("\n✓ ALL GITHUB RELEASE ASSETS AND RULES VERIFIED 100%!")
