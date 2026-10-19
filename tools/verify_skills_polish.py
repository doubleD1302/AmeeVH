#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from polish_skills_module import polish_skill_text
from phase2a_token_manager import validate_token_preservation

with open(ROOT / 'work' / 'polish' / 'unique_mainskill.json', 'r', encoding='utf-8') as f:
    main_items = json.load(f)
with open(ROOT / 'work' / 'polish' / 'unique_secskill.json', 'r', encoding='utf-8') as f:
    sec_items = json.load(f)

for name, items in [('MainSkill', main_items), ('SecondarySkill', sec_items)]:
    descs = [it for it in items if it['key'].endswith('.2')]
    tok_err = 0
    for it in descs:
        pol = polish_skill_text(it['vi_current'], it['en'])
        valid, ot, vt = validate_token_preservation(it['en'], pol)
        if not valid:
            tok_err += 1
            print(f"Token mismatch in {name} [{it['key']}]:")
            print("  EN toks:", ot)
            print("  VT toks:", vt)
    print(f"{name}: {len(descs)} descs tested, {tok_err} token errors.")
