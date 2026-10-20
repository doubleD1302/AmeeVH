import json
import re
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
data_dec = os.path.join(viet_dir, r"work\research\data_decrypted\entries")

# Scan all entries in data_dec for calques like "bản dựng"
calque_counts = {}

CALQUE_REPLACEMENTS = [
    (r'\bMột bản dựng AoE\b', 'Lối chơi quét diện rộng'),
    (r'\bMột bản dựng DPS bền vững\b', 'Lối chơi duy trì sát thương'),
    (r'\bMột bản dựng DPS bùng nổ\b', 'Lối chơi bộc phá sát thương'),
    (r'\bBản dựng DPS bền vững\b', 'Lối chơi duy trì sát thương'),
    (r'\bBản dựng DPS bùng nổ\b', 'Lối chơi bộc phá sát thương'),
    (r'\bBản dựng\b', 'Lối chơi'),
    (r'\bbản dựng\b', 'lối chơi'),
    (r'\bgây ra DMG\b', 'gây sát thương'),
    (r'\bgây DMG\b', 'gây sát thương'),
    (r'\bthời gian sử dụng kỹ năng\b', 'thời gian duy trì kỹ năng'),
    (r'\btạo ra Bóng tối\b', 'tạo ra Phân Thân Ảo Ảnh'),
    (r'\bsử dụng liên tiếp\b', 'tung chiêu liên tục'),
    (r'\bkhắp chiến trường\.\s*kẻ địch\b', 'khắp chiến trường. Kẻ địch'),
    (r'\bchu vi của cô ấy\b', 'phạm vi quanh cô'),
    (r'\bnhanh nhẹn cho phép\b', 'linh hoạt giúp'),
    (r'\bgây sát thương cho kẻ thù\b', 'gây sát thương lên kẻ địch'),
    (r'\bkẻ thù\b', 'kẻ địch'),
    (r'\bphần thưởng chủ đề\b', 'phần thưởng chủ đề'),
    (r'\bVượt qua màn chơi\b', 'Vượt ải'),
]

fixed_total = 0
for fname in os.listdir(data_dec):
    if not fname.endswith(".bin"):
        continue
    fpath = os.path.join(data_dec, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        try:
            d = json.load(f)
        except Exception:
            continue
    if not isinstance(d, dict):
        continue
    
    modified = False
    for k, v in d.items():
        if not isinstance(v, str):
            continue
        orig = v
        for pat, repl in CALQUE_REPLACEMENTS:
            if re.search(pat, v, flags=re.IGNORECASE):
                v = re.sub(pat, repl, v, flags=re.IGNORECASE)
        if v != orig:
            d[k] = v
            modified = True
            fixed_total += 1
            if len(calque_counts) < 10:
                calque_counts[k] = (orig, v)

    if modified:
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)

print(f"Polished {fixed_total} strings across data_decrypted entries!")
print("Sample fixes:")
for k, (o, n) in calque_counts.items():
    print(f"  [{k}]")
    print(f"    - Before: {o}")
    print(f"    + After:  {n}")
