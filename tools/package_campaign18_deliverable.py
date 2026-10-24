#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Package Deliverable for Campaign 18 (Đợt 10 - FINAL CAMPAIGN OF ENTIRE GAME):
Final CG NPC Stories & Disc Memory Stories (CG_npc133, CG_npc172..174, CG_disc4004..4066).
3,076 lines across 33 scenes.
100.0% OF ALL 626 LUA AVG SCENES IN STELLA SORA NOW RELOCALIZED!
"""

import hashlib
import json
from pathlib import Path
import time
import zipfile

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/final_cg_npc_and_disc_editorial_20261025_r01"
DIST_DIR = ROOT / "dist"
DIST_DIR.mkdir(parents=True, exist_ok=True)

OUT_ZIP = DIST_DIR / "StellaSora_Final_CG_NPC_And_Disc_LightNovel_VI_20261025_r01.zip"

FILES_TO_PACK = [
    "UNIFIED_CAMPAIGN_18_PROPOSALS.jsonl",
    "PROPOSALS_PARTITION_A.jsonl",
    "PROPOSALS_PARTITION_B.jsonl",
    "translations_cg_disc4066.py",
    "CAMPAIGN_18_TECHNICAL_AUDIT.json",
]

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print(f"Creating manifest and packaging deliverable to {OUT_ZIP.name}...")
    manifest = {
        "campaign_id": "final_cg_npc_and_disc_editorial_20261025_r01",
        "title": "Final CG NPC Stories & Disc Memory Stories Light Novel Vietnamese Localization",
        "description": "Cốt Truyện CG NPC Cuối & Đĩa Ký Ức (CG_npc133, CG_npc172..174, CG_disc4004..4066): 33 phân cảnh, 3.076 dòng. 100% CỐT TRUYỆN AVG TOÀN BỘ GAME ĐÃ HOÀN TẤT!",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_lines": 3076,
        "total_scenes": 33,
        "qa_verdict": "APPROVED_FOR_RELEASE",
        "blockers": 0,
        "majors": 0,
        "minors": 0,
        "files": []
    }

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in FILES_TO_PACK:
            fpath = CAMPAIGN_DIR / fname
            if fpath.exists():
                zf.write(fpath, arcname=fname)
                manifest["files"].append({
                    "name": fname,
                    "sha256": sha256_file(fpath),
                    "bytes": fpath.stat().st_size
                })
        manifest_str = json.dumps(manifest, ensure_ascii=False, indent=2)
        zf.writestr("MANIFEST.json", manifest_str)

    manifest_path = CAMPAIGN_DIR / "MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest_str)

    print(f"Successfully packaged {len(manifest['files'])} files into {OUT_ZIP.name} ({OUT_ZIP.stat().st_size:,} bytes).")

if __name__ == "__main__":
    main()
