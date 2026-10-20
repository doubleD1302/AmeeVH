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

term_checks = [
    ("Liên Hợp Thu Hoạch", "Nông Nghiệp Liên Hợp"),
    ("Thu Hoạch Liên Hợp", "Nông Nghiệp Liên Hợp"),
    ("Cự Thạch", "Cự Tháp"),
    ("Bang hội Ngôi sao", "Công Hội Tân Tinh"),
    ("Hội Ngôi sao", "Công Hội Tân Tinh"),
    ("Sơ Quang", "Khải Minh"),
    ("Người đi bộ", "Lữ Khách"),
    ("người đi bộ", "lữ khách"),
    ("kẻ thù", "kẻ địch"),
    ("bạn tình", "đồng đội / cộng sự"),
    ("bản dựng", "lối chơi"),
    ("Ông chủ", "Sếp"),
    ("ông chủ", "sếp"),
    ("sao chép", "nghe rõ / đã rõ"),
    ("Tầng nó", "Đạp lút ga / Nhấn hết ga"),
    ("tầng nó", "đạp lút ga"),
    ("vòng lặp", "tối cổ / mù tịt"),
    ("thả nó xuống", "thôi đi / đừng nhắc nữa"),
    ("bánh mì nướng", "tiêu đời / xong đời"),
    ("ngập trong nước", "bận ngập đầu"),
    ("giữ vững đường dây", "giữ vững phòng tuyến"),
    ("lạnh chân", "chùn bước"),
    ("gãy chân", "chúc may mắn"),
    ("nói về ma quỷ", "nhắc tào tháo"),
    ("lăn đi", "lên đường thôi"),
    ("lăn thôi", "lên đường thôi"),
    ("đánh vào chỗ", "đã quá"),
    ("người càu nhàu", "lính quèn"),
    ("dưới gầm bàn", "bán chui"),
    ("ủy ban", "ủy thác / ban chỉ huy"),
]

print("="*60)
print("AUDIT RESULTS FOR BATCH 3 PART A")
print("="*60)

total_found = 0
for term, suggestion in term_checks:
    matches = []
    pat = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
    for k, v in dst.items():
        if pat.search(v):
            matches.append((k, v, src.get(k, "")))
    if matches:
        total_found += len(matches)
        print(f"\n[FOUND {len(matches)}] '{term}' (Suggested: {suggestion})")
        for m in matches[:5]:
            print(f"  Key: {m[0]}")
            print(f"    SRC: {m[2]}")
            print(f"    DST: {m[1]}")

print(f"\nTotal occurrences found: {total_found}")
