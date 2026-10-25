#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")

def audit_discs():
    p = ROOT / "work" / "batches" / "all_104_discs_survey.json"
    discs = json.loads(p.read_text(encoding="utf-8"))
    
    print(f"Total Discs: {len(discs)}")
    
    # Let's inspect each disc
    for i, d in enumerate(discs):
        did = d['id']
        zh = d['zh_name']
        en = d['en_name']
        vi = d['cur_discip_name']
        it_vi = d['cur_item_name']
        print(f"[{did}] ZH: {zh} | EN: {en} | Disc: {vi} | Item: {it_vi}")

if __name__ == "__main__":
    audit_discs()
