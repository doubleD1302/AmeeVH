#!/usr/bin/env python3
"""Upload StellaSora_Gacha_Assets folder tree to an existing Google Drive folder using gdrive CLI."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Dict, List, Tuple

GDRIVE_BIN = shutil.which("gdrive") or "gdrive"
LOCAL_ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\dist\StellaSora_Gacha_Assets")
DRIVE_ROOT_ID = "1OEqOJtzxkcDL8_v0yTJHVhee7-Y_R7Xv"
FOLDER_MIME = "application/vnd.google-apps.folder"


def run_gdrive(args: List[str], retries: int = 4) -> str:
    delay = 1.5
    last_err = ""
    for attempt in range(retries):
        proc = subprocess.run(
            [GDRIVE_BIN, *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode == 0:
            return proc.stdout.strip()
        last_err = (proc.stderr or proc.stdout).strip()
        if attempt < retries - 1:
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"gdrive {' '.join(args)} failed: {last_err}")


def list_folder(folder_id: str) -> Dict[str, Dict]:
    out = run_gdrive(["readonly", "ls", folder_id, "--json"])
    items = json.loads(out) if out else []
    return {item["name"]: item for item in items}


def ensure_folder(name: str, parent_id: str, existing: Dict[str, Dict]) -> str:
    if name in existing and existing[name].get("mimeType") == FOLDER_MIME:
        return existing[name]["id"]
    out = run_gdrive(["mutate", "mkdir", name, "--parent", parent_id])
    m = re.search(r"\(ID:\s*([A-Za-z0-9_-]+)\)", out)
    if not m:
        # Refresh listing as fallback
        refreshed = list_folder(parent_id)
        if name in refreshed:
            return refreshed[name]["id"]
        raise RuntimeError(f"Could not parse folder ID from: {out}")
    return m.group(1)


def main() -> None:
    subfolders = ["01_Videos", "02_Gacha_Covers", "03_Gacha_UI_And_FX", "04_Banners_Tabs_And_Outfit_Cards"]

    # Step 1: Mirror directory tree & collect upload tasks
    # Each task: (local_file, drive_parent_id)
    upload_tasks: List[Tuple[Path, str]] = []
    skipped = 0

    def walk_dir(local_dir: Path, drive_parent_id: str) -> None:
        nonlocal skipped
        existing = list_folder(drive_parent_id)
        dirs = sorted([p for p in local_dir.iterdir() if p.is_dir()])
        files = sorted([p for p in local_dir.iterdir() if p.is_file()])

        for f in files:
            if f.name in existing and existing[f.name].get("mimeType") != FOLDER_MIME:
                skipped += 1
            else:
                upload_tasks.append((f, drive_parent_id))

        for d in dirs:
            sub_id = ensure_folder(d.name, drive_parent_id, existing)
            walk_dir(d, sub_id)

    root_existing = list_folder(DRIVE_ROOT_ID)
    for sub in subfolders:
        local_sub = LOCAL_ROOT / sub
        if not local_sub.exists():
            continue
        sub_id = ensure_folder(sub, DRIVE_ROOT_ID, root_existing)
        print(f"Prepared tree for {sub} (ID: {sub_id})...", flush=True)
        walk_dir(local_sub, sub_id)

    print(f"Tree ready. Pending uploads: {len(upload_tasks)}, already present: {skipped}", flush=True)
    if not upload_tasks:
        return

    done = 0
    errors: List[str] = []

    def upload_one(item: Tuple[Path, str]) -> str:
        fpath, pid = item
        run_gdrive(["mutate", "upload", str(fpath), "--parent", pid], retries=5)
        return str(fpath.relative_to(LOCAL_ROOT))

    with ThreadPoolExecutor(max_workers=6) as pool:
        futs = [pool.submit(upload_one, t) for t in upload_tasks]
        for fut in as_completed(futs):
            try:
                fut.result()
                done += 1
                if done % 50 == 0 or done == len(upload_tasks):
                    print(f"Uploaded {done}/{len(upload_tasks)}", flush=True)
            except Exception as exc:
                errors.append(str(exc))
                print(f"ERROR: {exc}", flush=True)

    print(f"FINISHED: uploaded={done}, skipped={skipped}, errors={len(errors)}", flush=True)
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
