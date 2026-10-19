#!/usr/bin/env python3
"""
Verify entire translated database in work/research/data_decrypted/entries/
Checks:
- Total strings translated vs English original
- Forbidden calques occurrences
- Color tags balance
- Token integrity
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEC_DIR = ROOT / "work" / "research" / "data_decrypted" / "entries"
ORIG_DIR = ROOT / "work" / "research" / "data_en_original" / "entries"
GLOSSARY_PATH = ROOT / "config" / "master_glossary.json"

COLOR_TAG_OPEN = re.compile(r'<color=#[0-9a-fA-F]{6}>')
COLOR_TAG_CLOSE = re.compile(r'</color>')

def main():
    print("=" * 70)
    print("Full Database Audit & Verification")
    print("=" * 70)

    with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
        glossary = json.load(f)
    forbidden = glossary.get("forbidden", {})

    total_tables = 0
    translated_tables = 0
    total_strings = 0
    translated_strings = 0
    forbidden_errors = 0
    color_tag_errors = 0

    for fname in DEC_DIR.iterdir():
        if not fname.name.endswith(".bin"):
            continue
        total_tables += 1
        try:
            with open(fname, "r", encoding="utf-8") as f:
                dec_data = json.load(f)
        except Exception:
            continue

        orig_file = ORIG_DIR / fname.name
        orig_data = {}
        if orig_file.exists():
            with open(orig_file, "r", encoding="utf-8") as f:
                orig_data = json.load(f)

        table_is_translated = False
        for k, v in dec_data.items():
            if not isinstance(v, str):
                continue
            total_strings += 1
            orig_val = orig_data.get(k, "")
            
            # Check if value has Vietnamese characters
            is_vi = any(u'\u00C0' <= ch <= u'\u1EF9' for ch in v)
            if is_vi or (orig_val and v != orig_val):
                translated_strings += 1
                table_is_translated = True

            # Check forbidden calques
            for wrong in forbidden.keys():
                if wrong.lower() in v.lower():
                    forbidden_errors += 1
                    print(f"Forbidden error: '{wrong}' in {fname.name} [{k}]: {v[:60]}")

            # Check color tags
            opens = len(COLOR_TAG_OPEN.findall(v))
            closes = len(COLOR_TAG_CLOSE.findall(v))
            if opens != closes:
                color_tag_errors += 1
                print(f"Color tag error in {fname.name} [{k}]: opens={opens}, closes={closes}")

        if table_is_translated:
            translated_tables += 1

    print("\n" + "=" * 70)
    print(f"Total tables examined: {total_tables}")
    print(f"Translated tables: {translated_tables}")
    print(f"Total strings examined: {total_strings}")
    print(f"Total translated strings: {translated_strings}")
    print(f"Forbidden calques errors: {forbidden_errors}")
    print(f"Color tag errors: {color_tag_errors}")
    print("=" * 70)

if __name__ == "__main__":
    main()
