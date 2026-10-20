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

weird_patterns = [
    r'lão nguyên viện',
    r'Dân người Novian',
    r'người Dân người Novian',
    r'người Novian',
    r'Novian',
    r'cắn một miếng',
    r'nghe rõ đó',
    r'ở trên đó',
    r'bánh mì nướng',
    r'ngập trong',
    r'ngập chìm',
    r'kẻ gây hại',
    r'nghe lén',
    r'thoát khỏi vòng lặp',
    r'thả nó xuống',
    r'tầng nó',
    r'công nghệ cấp cao',
    r'sao chép',
    r'bạn tình',
    r'bản dựng',
    r'người đi bộ',
    r'Cự Thạch',
    r'Liên Hợp Thu Hoạch',
    r'Thu Hoạch Liên Hợp',
    r'Ông chủ',
    r'ông chủ',
    r'quân đội công ty',
    r'đại đội của chúng ta',
    r'đường dây',
    r'lăn',
    r'nâng cốc',
    r'sạc pin',
    r'sạc',
    r'gãy chân',
    r'lạnh chân',
    r'giật dây',
    r'gầm bàn',
    r'càu nhàu',
    r'vết cắn',
]

print("SCANNING FOR SUSPICIOUS PHRASES IN DST:")
for p in weird_patterns:
    regex = re.compile(r'\b' + p + r'\b' if not p.startswith(r'\b') else p, re.IGNORECASE)
    matches = []
    for k, v in dst.items():
        if regex.search(v):
            matches.append((k, src.get(k, ""), v))
    if matches:
        print(f"\n--- Pattern: '{p}' ({len(matches)} matches) ---")
        for m in matches[:5]:
            print(f"[{m[0]}]\n  SRC: {m[1]}\n  DST: {m[2]}")
