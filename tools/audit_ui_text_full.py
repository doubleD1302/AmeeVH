#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit all UI Text in Stella Sora:
1. Scan 00789_0x87cc29ac0defc2d9.bin (UIText - 4,751 entries)
2. Scan 00798_0x78b1aa32bbcf433e.bin (Word - 356 entries)
3. Scan 00553_0x5b0fc2f5fe45a572.bin (Achievement - 1,324 entries)
4. Scan 00840_0x4a3c44844ee817d1.bin (CharacterArchiveContent)
5. Scan 00860_0x43ac532f7df5c82a.bin (DatingLandmarkEvent)
"""

import json
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
ENTRIES_DIR = ROOT / "work/research/data_200_decrypted/entries"

FILES_TO_AUDIT = {
    "UIText": ("00789_0x87cc29ac0defc2d9.bin", "01036_0x363690c09b175230.bin"),
    "Word": ("00798_0x78b1aa32bbcf433e.bin", "01045_0x740d729a46a8d407.bin"),
    "Achievement": ("00553_0x5b0fc2f5fe45a572.bin", "00800_0x6193ff799986b4f7.bin"),
}

def main():
    with open(ROOT / "config/master_glossary.json", "r", encoding="utf-8") as f:
        master_gloss = json.load(f)

    forbidden = master_gloss.get("forbidden", {})

    for tbl_name, (en_file, cn_file) in FILES_TO_AUDIT.items():
        p_en = ENTRIES_DIR / en_file
        p_cn = ENTRIES_DIR / cn_file
        if not p_en.exists():
            print(f"Skipping {tbl_name}, not found.")
            continue

        d_en = json.loads(p_en.read_text(encoding="utf-8"))
        d_cn = json.loads(p_cn.read_text(encoding="utf-8")) if p_cn.exists() else {}

        print(f"\n==========================================")
        print(f"Auditing Table: {tbl_name} ({len(d_en)} entries)")
        print(f"==========================================")

        banned_found = []
        for k, v in d_en.items():
            if not isinstance(v, str):
                continue
            for pat, desc in forbidden.items():
                if re.search(r"\b" + re.escape(pat) + r"\b", v, re.IGNORECASE):
                    banned_found.append((k, pat, desc, v))

        print(f"Forbidden terms found: {len(banned_found)}")
        for k, pat, desc, v in banned_found[:15]:
            print(f"  [{k}] '{pat}' ({desc}) -> {repr(v)}")

        # Untranslated English
        untranslated = []
        for k, v in d_en.items():
            if not isinstance(v, str):
                continue
            cn_text = d_cn.get(k, "")
            clean_v = re.sub(r"\{[0-9]+\}|<[^>]+>|[0-9\W_]+", "", v)
            clean_cn = re.sub(r"\{[0-9]+\}|<[^>]+>|[0-9\W_]+", "", str(cn_text))
            if clean_v and all(ord(c) < 128 for c in clean_v) and clean_cn and any(ord(c) > 0x4e00 for c in clean_cn):
                if clean_v.upper() in ["EXP", "HP", "MP", "CD", "UID", "LV", "MAX", "VIP", "SP", "ID", "OK", "UI"]:
                    continue
                untranslated.append((k, v, cn_text))

        print(f"Untranslated English entries: {len(untranslated)}")
        for k, v, cn in untranslated[:15]:
            print(f"  [{k}] VN: {repr(v)} | CN: {repr(cn)}")

if __name__ == "__main__":
    main()
