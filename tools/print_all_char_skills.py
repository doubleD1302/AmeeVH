#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")

def dump_all_unique():
    p = ROOT / "work" / "batches" / "unique_character_skills_audit.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    
    print(f"=== ALL {len(data)} CHARACTER SKILLS ===")
    for i, s in enumerate(data):
        print(f"{i+1:3d}. [{s['key']}] EN: {s['en']:<35} | VI: {s['vi']}")

if __name__ == "__main__":
    dump_all_unique()
