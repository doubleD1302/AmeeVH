#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scan key data tables for forbidden terms and glossary alignment:
Item, Talent, MainSkill, SecondarySkill, Skill, MonsterManual, FateCard, UIText, Word.
"""

import json
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
entries_dir = ROOT / "work/research/data_200_decrypted/entries"

def main():
    with open(ROOT / "config/master_glossary.json", "r", encoding="utf-8") as f:
        gloss = json.load(f)

    forbidden = gloss.get("forbidden", {})

    check_tables = {
        "UIText": "00789_0x87cc29ac0defc2d9.bin",
        "Word": "00798_0x78b1aa32bbcf433e.bin",
        "Item": "00653_0xe60634348b826f41.bin",
        "Talent": "00764_0x3f0bd5f8db2389b6.bin",
        "MainSkill": "00667_0x57e760255c1d3b2d.bin",
        "SecondarySkill": "00715_0x31a8814a91313129.bin",
        "Skill": "00716_0x998f849a64309b25.bin",
        "MonsterManual": "00685_0x6509b9fe31bc8029.bin",
        "FateCard": "00633_0x788d8a3db60dd08a.bin",
        "MailTemplate": "00676_0x54636f01f0fa23ae.bin",
        "DictionaryDiagram": "00611_0xd46d025e8dae5d69.bin",
        "DatingLandmarkEvent": "00860_0x43ac532f7df5c82a.bin",
        "CharacterArchiveContent": "00840_0x4a3c44844ee817d1.bin"
    }

    total_banned = 0
    results = {}

    for name, fname in check_tables.items():
        p = entries_dir / fname
        if not p.exists():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        banned = []
        for k, v in data.items():
            if not isinstance(v, str):
                continue
            for pat, desc in forbidden.items():
                if re.search(r"\b" + re.escape(pat) + r"\b", v, re.IGNORECASE):
                    banned.append((k, pat, desc, v))

        results[name] = banned
        total_banned += len(banned)
        print(f"Table {name} ({len(data)} rows): {len(banned)} forbidden matches")
        for k, pat, desc, v in banned[:8]:
            print(f"  [{k}] '{pat}' ({desc}) -> {repr(v)[:80]}")

    print(f"\nTOTAL FORBIDDEN TERM MATCHES ACROSS UI TABLES: {total_banned}")

if __name__ == "__main__":
    main()
