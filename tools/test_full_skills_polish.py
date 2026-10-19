#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from polish_skills_module import polish_skill_text
from phase2a_token_manager import validate_token_preservation

with open(ROOT / 'work' / 'polish' / 'phase2a_dataset.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

for name in ['MainSkill', 'SecondarySkill']:
    items = d[name]
    changes = 0
    token_err = 0
    for it in items:
        orig = it['vi_current']
        if it['key'].endswith('.2'):
            pol = polish_skill_text(orig, it['en'])
        else:
            pol = orig
        valid, ot, vt = validate_token_preservation(it['en'], pol)
        if not valid:
            token_err += 1
            print(f"Error in {name} [{it['key']}]: {ot} vs {vt}")
        if pol != orig:
            changes += 1
    print(f"{name}: {len(items)} items, {changes} changed, {token_err} token errors.")
