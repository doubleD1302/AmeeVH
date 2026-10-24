#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Package Campaign 5 Deliverable: Act 3 Story & Allies Phone (3,333 lines).
Outputs: dist/StellaSora_Act3_Story_LightNovel_VI_20261024_r01.zip
"""

import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
RUN_ID = "act3_story_editorial_20261024_r01"
EDITORIAL_DIR = ROOT / "work/editorial" / RUN_ID
QA_DIR = ROOT / "work/subagents" / RUN_ID / "qa_reviewer_act3"
DIST_DIR = ROOT / "dist"
OUTPUT_ZIP = DIST_DIR / "StellaSora_Act3_Story_LightNovel_VI_20261024_r01.zip"

def sha256_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def main():
    print(f"=== PACKAGING DELIVERABLE FOR {RUN_ID} ===")
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    
    files_to_pack = [
        EDITORIAL_DIR / "UNIFIED_ACT3_PROPOSALS.jsonl",
        QA_DIR / "QA_FINDINGS.json",
        QA_DIR / "REVIEW_REPORT.md",
        QA_DIR / "RESULT.json"
    ]
    
    with zipfile.ZipFile(OUTPUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for f in files_to_pack:
            if f.exists():
                zf.write(f, arcname=f.name)
                print(f"  Added {f.name}")
            else:
                print(f"  Warning: {f.name} does not exist yet")
                
    size = OUTPUT_ZIP.stat().st_size
    sha = sha256_file(OUTPUT_ZIP)
    print(f"\nCreated {OUTPUT_ZIP.name}:")
    print(f"  Size: {size:,} bytes ({size / 1024:.2f} KB)")
    print(f"  SHA256: {sha}")

if __name__ == "__main__":
    main()
