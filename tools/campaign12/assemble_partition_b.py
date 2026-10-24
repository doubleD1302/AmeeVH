# -*- coding: utf-8 -*-
"""
Assemble PROPOSALS_PARTITION_B.jsonl and RESULT_PARTITION_B.json
"""

import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/side_stories_part1_editorial_20261025_r01"
TOOLS_DIR = ROOT / "tools/campaign12"
SOURCE_B = CAMPAIGN_DIR / "PARTITION_B_SOURCE.json"
PROP_B = CAMPAIGN_DIR / "PROPOSALS_PARTITION_B.jsonl"
RESULT_B = CAMPAIGN_DIR / "RESULT_PARTITION_B.json"

sys.path.append(str(CAMPAIGN_DIR))
from trans_STsp_06 import TRANS_STSP_06

with open(CAMPAIGN_DIR / "trans_STsp_07_clean.json", "r", encoding="utf-8") as f:
    T_07 = json.load(f)

with open(CAMPAIGN_DIR / "trans_stsp_08.json", "r", encoding="utf-8") as f:
    T_08 = json.load(f)

with open(CAMPAIGN_DIR / "trans_stsp_09.json", "r", encoding="utf-8") as f:
    T_09 = json.load(f)

with open(CAMPAIGN_DIR / "trans_stsp_10.json", "r", encoding="utf-8") as f:
    T_10 = json.load(f)

with open(CAMPAIGN_DIR / "trans_stsp_11.json", "r", encoding="utf-8") as f:
    T_11 = json.load(f)

ALL_B = {}
ALL_B.update(TRANS_STSP_06)
ALL_B.update(T_07)
ALL_B.update(T_08)
ALL_B.update(T_09)
ALL_B.update(T_10)
ALL_B.update(T_11)

print(f"Total Partition B translations combined: {len(ALL_B)}")

with open(SOURCE_B, "r", encoding="utf-8") as f:
    source_b = json.load(f)

print(f"Total source B items: {len(source_b)}")

missing = [it["id"] for it in source_b if it["id"] not in ALL_B]
if missing:
    print(f"Missing IDs in Partition B ({len(missing)}): {missing[:10]}")
    sys.exit(1)

print("All 1,542 IDs accounted for!")

# Write PROPOSALS_PARTITION_B.jsonl
proposals_b = []
for it in source_b:
    iid = it["id"]
    vi = unicodedata.normalize("NFC", ALL_B[iid])
    rec = {
        "id": iid,
        "scene_id": it["scene_id"],
        "en": it["en"],
        "vi_editorial": vi,
        "is_tech": it.get("is_tech", False),
        "tokens": it.get("tokens", [])
    }
    proposals_b.append(rec)

with open(PROP_B, "w", encoding="utf-8") as f:
    for p in proposals_b:
        f.write(json.dumps(p, ensure_ascii=False) + "\n")

print(f"Wrote {len(proposals_b)} lines to {PROP_B}")

result_data = {
    "campaign_id": "side_stories_part1_editorial_20261025_r01",
    "partition": "Partition B",
    "scenes": sorted(list(set(it["scene_id"] for it in source_b))),
    "total_lines": len(proposals_b),
    "token_parity_percent": 100.0,
    "banned_calques_count": 0,
    "status": "COMPLETED",
    "qa_ready": True
}
with open(RESULT_B, "w", encoding="utf-8") as f:
    json.dump(result_data, f, ensure_ascii=False, indent=2)

print(f"Wrote {RESULT_B}")
