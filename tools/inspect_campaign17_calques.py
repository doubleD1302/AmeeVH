# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/tutorial_and_character_cg_editorial_20261025_r01"

with open(CAMPAIGN_DIR / "CAMPAIGN_17_SOURCE_ALL.json", "r", encoding="utf-8") as f:
    items = json.load(f)

BANNED_PATTERNS = [
    (r"\bMa Vương\b", "Ma Vương"),
    (r"\bchết tiệt\b", "chết tiệt"),
    (r"\bbạn biết đấy\b", "bạn biết đấy"),
    (r"\bcái quái gì\b", "cái quái gì"),
    (r"\blàm sao mà\b", "làm sao mà"),
    (r"\bkhoảng không quảng cáo\b", "khoảng không quảng cáo"),
    (r"\bchụp nhanh bộ nhớ\b", "chụp nhanh bộ nhớ"),
    (r"\bHội Ngôi Sao Mới\b", "Hội Ngôi Sao Mới"),
    (r"\bHiệp hội Ngôi sao Mới\b", "Hiệp hội Ngôi sao Mới"),
    (r"\bBạo Quân\b", "Bạo Quân"),
    (r"\bHổ phách\b", "Hổ phách"),
    (r"\bDiên Vĩ\b|\bDiên vĩ\b", "Diên vĩ"),
    (r"\bđá Linh hồn\b|\bĐá Linh hồn\b|\bĐá Hồn\b", "Đá Hồn"),
]

findings = []
for it in items:
    vi = it.get('current_vi', '')
    for pat, label in BANNED_PATTERNS:
        if re.search(pat, vi, re.IGNORECASE):
            findings.append((it['id'], label, vi[:70]))

print(f"Total banned pattern hits in raw current_vi: {len(findings)}")
for iid, label, snippet in findings[:30]:
    print(f"  [{iid}] {label}: {repr(snippet)}")
