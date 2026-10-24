import json
from pathlib import Path
import re

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/tutorial_and_character_cg_editorial_20261025_r01"

with open(ROOT / "work/character_context_20261023_r02/CHARACTER_VOICE_PROFILES.json", "r", encoding="utf-8") as f:
    profiles = json.load(f)

for cid in ['149', '155', '156', '157', '158', '159', '160', '162']:
    p = profiles.get(cid, {})
    print(f"char:{cid} -> {p.get('character_name', 'unknown')} ({p.get('character_title', '')})")

with open(CAMPAIGN_DIR / "PARTITION_B_SOURCE.json", "r", encoding="utf-8") as f:
    items = json.load(f)

print(f"\nTotal Partition B items: {len(items)}")

# Check banned patterns in Partition B
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
    (r"\bKỵ Sĩ Hoàng Gia\b", "Kỵ Sĩ Hoàng Gia"),
    (r"\bTrọng Tài Chạng Vạng\b", "Trọng Tài Chạng Vạng"),
]

hits = []
for it in items:
    vi = it.get('current_vi', '')
    for pat, label in BANNED_PATTERNS:
        if re.search(pat, vi, re.IGNORECASE):
            hits.append((it['id'], label, vi[:70]))

print(f"Total banned hits in Partition B current_vi: {len(hits)}")
for h in hits[:25]:
    print(f"  [{h[0]}] {h[1]}: {repr(h[2])}")
