#!/usr/bin/env python3
"""Build polished translation mappings for MainSkill and SecondarySkill."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from phase2a_token_manager import shield_tokens, unshield_tokens, validate_token_preservation

with open(ROOT / 'work' / 'polish' / 'unique_mainskill.json', 'r', encoding='utf-8') as f:
    unique_main = json.load(f)

with open(ROOT / 'work' / 'polish' / 'unique_secskill.json', 'r', encoding='utf-8') as f:
    unique_sec = json.load(f)

print(f"Loaded {len(unique_main)} MainSkill and {len(unique_sec)} SecondarySkill unique entries.")
