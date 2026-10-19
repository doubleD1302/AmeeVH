import json
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
src_p = ROOT / "work" / "batches" / "pillar1_dungeons_monsters.json"
dst_p = ROOT / "work" / "batches" / "pillar1_translated.json"

src = json.load(open(src_p, encoding="utf-8"))
dst = json.load(open(dst_p, encoding="utf-8"))

calque_patterns = [
    r'\bXóa Cự Tháp\b',
    r'\bXóa ải\b',
    r'\bXóa tầng\b',
    r'\bHãy là khách của tôi\b',
    r'\bđối xử với Lữ Khách\b',
    r'\bmã thông báo\b',
    r'\btruyền trực tuyến\b',
    r'\bĐiện thoại trò chơi\b',
    r'\bThẻ giao dịch\b',
    r'\bRất nhiều như vậy\b',
    r'\bĐừng giữ lại!\b',
    r'\bnghiện ảnh\b',
    r'\bMột phát súng sắp tới\b',
    r'\bquấy rầy tôi vì những bức ảnh\b',
    r'\bBạn muốn bắn không\b',
    r'\bLần này bắn bao nhiêu\b',
    r'\bĐã kết nối chưa\b',
    r'\bkhá thể thao\b',
    r'\bngười đi bộ\b',
    r'\bngười du hành\b',
    r'\bLữ Khách của bạn\b',
    r'\bđược gánh chịu\b',
    r'\bthực hiện đòn đánh\b',
    r'\bnhững người đi bộ\b',
    r'\bsiêu giáp\b',
    r'\bbột chắc chắn\b',
    r'\bchiến binh bụi rậm\b',
    r'\bthành cổ cây bụi\b',
    r'\bSao nhổ\b',
    r'\bmất khả năng lao động\b',
    r'\bvết rách không gian\b',
    r'\bsát thương dẫn xuất\b',
    r'\btổng lực chiến\b',
    r'\bxếp hạng sức mạnh\b',
    r'\bthời gian hồi phục\b',
    r'\bphá vỡ độ dẻo dai\b',
    r'\bSPD chuyển động\b',
]

findings = {}
for p in calque_patterns:
    findings[p] = []

for tbl, tdata in dst.items():
    s_entries = src.get(tbl, {}).get("entries", {})
    for k, d_val in tdata.get("entries", {}).items():
        s_val = s_entries.get(k, "")
        for pat in calque_patterns:
            if re.search(pat, d_val, re.IGNORECASE):
                findings[pat].append((tbl, k, s_val, d_val))

for pat, hits in findings.items():
    if hits:
        print(f"Pattern '{pat}': {len(hits)} matches")
        for tbl, k, s, d in hits[:5]:
            print(f"  [{tbl}.{k}]")
            print(f"    EN: {s}")
            print(f"    VI: {d}")
