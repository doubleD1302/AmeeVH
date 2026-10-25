#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")

def check_discs():
    p = ROOT / "work" / "batches" / "all_104_discs_survey.json"
    if not p.exists():
        print("Discs survey not found")
        return
    discs = json.loads(p.read_text(encoding="utf-8"))
    print(f"=== ALL {len(discs)} DISCS ===")
    for d in discs:
        en = d.get('en_name', '')
        zh = d.get('zh_name', '')
        vi_discip = d.get('cur_discip_name', '')
        vi_item = d.get('cur_item_name', '')
        print(f"ID {d.get('id')}: EN='{en}' | ZH='{zh}' | DiscIP_VI='{vi_discip}' | Item_VI='{vi_item}'")

if __name__ == "__main__":
    check_discs()


def check_skills():
    mainskill_path = ROOT / "work" / "polish" / "unique_mainskill.json"
    secskill_path = ROOT / "work" / "polish" / "unique_secskill.json"
    
    if mainskill_path.exists():
        data = json.loads(mainskill_path.read_text(encoding="utf-8"))
        print(f"\n=== UNIQUE MAIN SKILL ({len(data)} items) ===")
        for it in data[:30]:
            print(f"[{it.get('key')}] EN='{it.get('en')}' | CN='{it.get('cn')}' | VI='{it.get('vi_current')}'")
            
    if secskill_path.exists():
        data = json.loads(secskill_path.read_text(encoding="utf-8"))
        print(f"\n=== UNIQUE SECONDARY SKILL ({len(data)} items) ===")
        for it in data[:30]:
            print(f"[{it.get('key')}] EN='{it.get('en')}' | CN='{it.get('cn')}' | VI='{it.get('vi_current')}'")

if __name__ == "__main__":
    check_skills()


def check_skill_table():
    dataset_path = ROOT / "work" / "polish" / "phase2a_dataset.json"
    if dataset_path.exists():
        data = json.loads(dataset_path.read_text(encoding="utf-8"))['Skill']
        print(f"\n=== SKILL TABLE SAMPLES ({len(data)} items) ===")
        # check unique names
        names = {}
        for it in data:
            key = it.get('key', '')
            en = it.get('en', '')
            vi = it.get('vi_current', '')
            if key.endswith('.2'): # often skill name in Skill table
                names[en] = (key, vi)
        print(f"Total unique names ending with .2 in Skill table: {len(names)}")
        for en, (k, vi) in list(names.items())[:25]:
            print(f"[{k}] EN='{en}' | VI='{vi}'")

if __name__ == "__main__":
    check_skill_table()
