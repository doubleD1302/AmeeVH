#!/usr/bin/env python3
"""Rebuild the Android VN texture bundles on top of the CURRENT official Android *.en.unity3d bundles.

Same reason as rebuild_texture_bundles_on_official.py: a VN bundle replaces the official bundle of the same
name, so a VN bundle built from an older official file loses every asset the newer one added (white banners).
Reuses patch_single_bundle/collect_texture_map from build_android_bundles_clean_v107.py (ASTC encoding, atlas
handling and its exclusions: honor titles, skip button, cover_20162, cover_1001 stay original EN).

Writes only to --out. Does not touch dist/, manifests or zips.

  .venv\\Scripts\\python tools\\rebuild_android_bundles_on_official.py --source <official android .en.unity3d dir> \\
      --out staging\\android_rebuilt_<tag> [--only icon-0,icon-2,...]
"""
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_android_bundles_clean_v107 as b  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--only", default="", help="comma separated bundle stems (without .en.unity3d); default all with VN textures")
    a = ap.parse_args()
    b.SRC_DIR = a.source
    b.OUT_DIR = a.out
    a.out.mkdir(parents=True, exist_ok=True)
    by_bundle = b.collect_texture_map()
    if a.only:
        want = {f"{s.strip()}.en.unity3d" for s in a.only.split(",") if s.strip()}
        by_bundle = {k: v for k, v in by_bundle.items() if k in want}
        missing = want - set(by_bundle)
        if missing:
            print("no VN textures mapped for:", sorted(missing))
    done = bad = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(b.patch_single_bundle, n, items): n for n, items in by_bundle.items()}
        for f in as_completed(futs):
            try:
                n, patched, mism, msg = f.result()
                done += 1
                if mism:
                    bad += 1
                print(f"[{done}/{len(by_bundle)}] {n}: {msg}", flush=True)
            except Exception as e:
                bad += 1
                print("ERROR", futs[f], e, flush=True)
    print("bundles:", done, "problems:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
