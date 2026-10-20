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

# Sample scenes across chapters
chapters = ['STm06_00', 'STm06_02_a', 'STm06_05_a', 'STm06_10', 'STm06x5_01', 'STm06x5_05', 'STm06x5_10', 'STm07_01']
for ch in chapters:
    keys = [k for k in src if k.startswith(ch)]
    print(f"\n================ CHAPTER {ch} ({len(keys)} lines) ================")
    for k in keys[:5]:
        print(f"[{k}] EN: {src[k][:100]}")
        print(f"       VI: {dst.get(k, '')[:100]}")
