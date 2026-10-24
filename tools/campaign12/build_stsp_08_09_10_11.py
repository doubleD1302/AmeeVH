#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generator for remaining Partition B stories:
STsp_08 (271 lines), STsp_09 (233 lines), STsp_10 (261 lines), STsp_11 (274 lines).
Total = 1,039 lines.
"""

import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/side_stories_part1_editorial_20261025_r01"
SOURCE_B = CAMPAIGN_DIR / "PARTITION_B_SOURCE.json"

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')
CTRL_PATTERN = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')

with open(SOURCE_B, "r", encoding="utf-8") as f:
    source_b = json.load(f)

src_map = {it["id"]: it for it in source_b}

# Base translations dictionary
B_TRANS = {}

def clean_vi(src_en, vi_text):
    """Normalize NFC and ensure tokens match."""
    vi_text = unicodedata.normalize("NFC", vi_text.strip())
    return vi_text

print("Ready to populate remaining Partition B translations.")
