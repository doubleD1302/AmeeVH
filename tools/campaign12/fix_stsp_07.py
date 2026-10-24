import json
from pathlib import Path
import re
import sys

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/side_stories_part1_editorial_20261025_r01"
sys.path.append(str(CAMPAIGN_DIR))

from trans_STsp_07 import TRANS_STSP_07

with open(CAMPAIGN_DIR / "PARTITION_B_SOURCE.json", "r", encoding="utf-8") as f:
    source_b = json.load(f)

src_s07 = {it["id"]: it for it in source_b if it["scene_id"].startswith("STsp_07")}

# Fix the mismatches in s07_03
TRANS_STSP_07["STsp_07_03.28"] = "Chuyện là thế đấy. Tôi đã liên lạc với mẹ của Annie, nhưng cô ấy đã hủy bàn từ trước mất rồi. Tôi cứ ngỡ đến xếp hàng sớm thì sẽ giành được chỗ, ai ngờ tối nay quán đã kín bàn từ lâu."
TRANS_STSP_07["STsp_07_03.74"] = "Khác hẳn với những mùa lễ lạnh lẽo, cô quạnh của những năm trước đây... Mình đã may mắn và hạnh phúc lắm rồi."
TRANS_STSP_07["STsp_07_03.75"] = "Donna... Teresa... Giờ này hai cậu đang ở đâu rồi nhỉ?"

for extra_k in ["STsp_07_03.31", "STsp_07_03.47", "STsp_07_03.66"]:
    if extra_k in TRANS_STSP_07:
        del TRANS_STSP_07[extra_k]

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

errors = []
for iid, it in src_s07.items():
    if iid not in TRANS_STSP_07:
        errors.append(f"Missing ID: {iid}")
        continue
    vi = TRANS_STSP_07[iid]
    st = sorted(TAG_PATTERN.findall(it["en"]))
    dt = sorted(TAG_PATTERN.findall(vi))
    if st != dt:
        errors.append(f"Token mismatch in {iid}: src={st} vs dst={dt}")

print(f"STsp_07 validation: {len(errors)} errors out of {len(src_s07)} items.")
if errors:
    for e in errors[:10]:
        print(" ", e)
else:
    # Save clean trans_STsp_07.py
    with open(CAMPAIGN_DIR / "trans_STsp_07_clean.json", "w", encoding="utf-8") as f:
        json.dump(TRANS_STSP_07, f, ensure_ascii=False, indent=2)
    print("Saved trans_STsp_07_clean.json!")
