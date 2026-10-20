#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path("c:/YostarGames/StellaSora_EN/StellaSora_VietHoa")
SRC_PATH = ROOT / "work/batches/batch_10k_b3_partA.json"
DST_PATH = ROOT / "work/batches/batch_10k_b3_partA_translated.json"

with open(SRC_PATH, "r", encoding="utf-8") as f:
    src = json.load(f)
with open(DST_PATH, "r", encoding="utf-8") as f:
    dst = json.load(f)

search_terms = [
    r'\bcopy\b',
    r'\bhear me\b',
    r'\bover\b',
    r'\btoast\b',
    r'\bswamp',
    r'\bhold the line\b',
    r'\bcold feet\b',
    r'\bbreak a leg\b',
    r'\bcall it a day\b',
    r'\bspeak of the devil\b',
    r'\bpipe down\b',
    r'\broll\b',
    r'\bhit the spot\b',
    r'\bgrunt\b',
    r'\bbig shot\b',
    r'\bunder the table\b',
    r'\bskeleton\b',
    r'\bfloor it\b',
    r'\bout of the loop\b',
    r'\bdrop it\b',
    r'\bgrab a bite\b',
    r'\bbite\b',
    r'\bspotted\b',
    r'\bcharge in\b',
    r'\bcharge\b',
    r'\bcommission\b',
    r'\bnightingale\b',
    r'\bblade of jade\b',
    r'\bgarden of parasite\b',
    r'\btyrant\b',
    r'\bboss accord\b',
    r'\bphilae\b',
    r'\bnyx\b',
    r'\bdarcia\b',
    r'\bfuyuka\b',
    r'\bpetal bloom\b',
    r'\bashwind\b',
    r'\bwhite owl\b',
    r'\biron wall\b',
    r'\btitan\b',
    r'\bsenate\b',
]

print("SEARCHING SOURCE DIALOGUES FOR NOTABLE IDIOMS & LORE TERMS:")
for pattern in search_terms:
    matches = []
    regex = re.compile(pattern, re.IGNORECASE)
    for k, text in src.items():
        if regex.search(text):
            matches.append((k, text, dst.get(k, "")))
    if matches:
        print(f"\n=== Pattern: {pattern} ({len(matches)} matches) ===")
        for m in matches[:6]:
            print(f"[{m[0]}]\n  SRC: {m[1]}\n  DST: {m[2]}")
