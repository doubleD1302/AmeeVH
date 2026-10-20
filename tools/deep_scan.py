import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
orig = json.load(open(ROOT / "work" / "batches" / "batch_10k_b3_partC.json", encoding='utf-8'))
trans = json.load(open(ROOT / "work" / "batches" / "batch_10k_b3_partC_translated.json", encoding='utf-8'))

print("=== DEEP SCAN OF GLOSSARY & TEXTING ANOMALIES ===")

patterns = {
    "Hội Ngôi Sao Mới": re.compile(r'(?:Hiệp hội|Hội|Bang hội)\s*Ngôi\s*sao\s*Mới', re.IGNORECASE),
    "Đội Mèo Trắng": re.compile(r'(?:Đội|Đoàn|Nhóm|Bầy)\s*Mèo\s*Trắng', re.IGNORECASE),
    "Vệ Binh Hoàng Gia": re.compile(r'Vệ\s*binh\s*Hoàng\s*gia', re.IGNORECASE),
    "Hoa Hồng": re.compile(r'\bhoa\s*hồng\b', re.IGNORECASE),
    "Ông chủ": re.compile(r'\bông\s*chủ\b', re.IGNORECASE),
    "Họ thật chặt": re.compile(r'Họ\s*thật\s*chặt', re.IGNORECASE),
    "Sao chép": re.compile(r'\bsao\s*chép\b', re.IGNORECASE),
    "Sơ Quang": re.compile(r'\bSơ\s*Quang\b', re.IGNORECASE),
}

counts = {p: 0 for p in patterns}
samples = {p: [] for p in patterns}

for k, t in trans.items():
    o = orig[k]
    for p_name, pattern in patterns.items():
        if pattern.search(t):
            counts[p_name] += 1
            if len(samples[p_name]) < 5:
                samples[p_name].append((k, o, t))

for p_name, count in counts.items():
    print(f"\nPattern '{p_name}': {count} occurrences")
    for k, o, t in samples[p_name]:
        print(f"  [{k}] EN: {o}\n        VI: {t}")
