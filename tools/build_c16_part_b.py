# -*- coding: utf-8 -*-
"""
Builder and QA-verifier for Campaign 16 Partition B:
STev_11 (9 scenes, 858 lines), STev_12 (9 scenes, 906 lines) = 1,764 lines.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/event_stories_part4_editorial_20261025_r01"
SOURCE_B = CAMPAIGN_DIR / "PARTITION_B_SOURCE.json"
PROP_B = CAMPAIGN_DIR / "PROPOSALS_PARTITION_B.jsonl"
RESULT_B = CAMPAIGN_DIR / "RESULT_PARTITION_B.json"

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

# 18 lines in Part B that have unclosed <size=XX> tags in EN source:
UNCLOSED_SIZE_IDS_B = {
    'STev_11_02.167', 'STev_11_02.201', 'STev_11_02.318', 'STev_11_04.219',
    'STev_11_04.231', 'STev_11_04.277', 'STev_11_04.344', 'STev_11_04.379',
    'STev_11_05.128', 'STev_11_06.274', 'STev_11_06.299', 'STev_11_06.315',
    'STev_11_06.317', 'STev_11_07.184', 'STev_11_07.384', 'STev_11_08.203',
    'STev_12_05.58', 'STev_12_06.206'
}

def check_tokens(src_tokens, dst_text):
    dst_tokens = TAG_PATTERN.findall(dst_text)
    return sorted(src_tokens) == sorted(dst_tokens), src_tokens, dst_tokens

def check_control_chars(src_text, dst_text):
    src_ctrls = [c for c in src_text if ord(c) < 32 and c not in '\r\n\t']
    dst_ctrls = [c for c in dst_text if ord(c) < 32 and c not in '\r\n\t']
    return src_ctrls == dst_ctrls, src_ctrls, dst_ctrls

with open(SOURCE_B, 'r', encoding='utf-8') as f:
    items = json.load(f)

print(f"Loaded {len(items)} items from Partition B.")

REPLACEMENTS_PART_B = [
    # 1. Banned machine translation calques
    ("Chết tiệt!==W== Anh chàng này thật đáng giận!", "Khốn kiếp!==W== Tên này đáng ghét thật đấy!"),
    ("Chết tiệt, di chuyển đi!", "Khốn thật, mau tản ra!"),
    ("Chết tiệt, tên lừa đảo đó... Hắn đã thuê tất cả những vệ sĩ này...", "Khốn thật, tên bịp bợm đó... Hắn thuê chừng này vệ sĩ bảo vệ sao..."),
    ("Chết tiệt, họ đang bùng nổ! Cô gái đó chính là mồi nhử! Vào đây!", "Khốn kiếp, bọn chúng lao tới rồi! Con nhỏ đó chỉ là mồi nhử thôi! Vào đây mau!"),
    ("Chết tiệt... Chúng ta đang gặp rắc rối hả?", "Khốn thật... Tụi mình gặp rắc rối to rồi sao?"),
    ("Chết tiệt, cô ấy nằm ngoài tầm của chúng ta!", "Khốn kiếp, cô ta vượt ngoài tầm với của chúng ta rồi!"),
    ("Chết tiệt... Làm thế nào mà tất cả lại sụp đổ?", "Khốn thật... Rốt cuộc tại sao mọi chuyện lại đổ bể thế này?"),
    ("Chết tiệt!", "Khốn thật!"),
    ("Chết tiệt", "Khốn thật"),
    ("chết tiệt", "chết thật"),
    ("cái quái gì", "chuyện quái gì"),
    ("làm sao mà", "sao có thể"),
    ("bạn biết đấy", "cậu biết đấy"),
    ("khoảng không quảng cáo", "kho đồ"),
    ("chụp nhanh bộ nhớ", "hồi ức đặc tả"),
    ("Ma Vương", "Bạo Chúa"),
    ("Bạo Quân", "Bạo Chúa"),

    # 2. Master Glossary terms in Part B
    ("Hội Ngôi Sao Mới", "Lữ Đoàn Tân Tinh"),
    ("Hiệp hội Ngôi sao Mới", "Lữ Đoàn Tân Tinh"),
    ("Vệ binh Hoàng gia", "Cận Vệ Hoàng Gia"),
    ("vệ binh hoàng gia", "cận vệ hoàng gia"),
    ("Monolith", "Cự Thạch"),
    ("các Archon", "các Chấp Chính Quan"),
    ("Archon", "Chấp Chính Quan"),

    # 3. Act titles in Part B
    ("Màn một", "Hồi 1"),
    ("Màn Một", "Hồi 1"),
    ("màn một", "Hồi 1"),
    ("Màn hai", "Hồi 2"),
    ("Màn Hai", "Hồi 2"),
    ("màn hai", "Hồi 2"),
    ("Màn ba", "Hồi 3"),
    ("Màn Ba", "Hồi 3"),
    ("màn ba", "Hồi 3"),
    ("Màn bốn", "Hồi 4"),
    ("Màn Bốn", "Hồi 4"),
    ("màn bốn", "Hồi 4"),
    ("Màn năm", "Hồi 5"),
    ("Màn Năm", "Hồi 5"),
    ("màn năm", "Hồi 5"),
    ("Màn sáu", "Hồi 6"),
    ("Màn Sáu", "Hồi 6"),
    ("màn sáu", "Hồi 6"),
    ("Màn bảy", "Hồi 7"),
    ("Màn Bảy", "Hồi 7"),
    ("màn bảy", "Hồi 7"),
    ("Màn tám", "Hồi 8"),
    ("Màn Tám", "Hồi 8"),
    ("màn tám", "Hồi 8"),
    ("Màn chín", "Hồi 9"),
    ("Màn Chín", "Hồi 9"),
    ("màn chín", "Hồi 9"),
    ("Hồi Một", "Hồi 1"),
    ("Hồi Hai", "Hồi 2"),
    ("Hồi Ba", "Hồi 3"),
    ("Hồi Bốn", "Hồi 4"),
    ("Hồi Năm", "Hồi 5"),
    ("Hồi Sáu", "Hồi 6"),
    ("Hồi Bảy", "Hồi 7"),
    ("Hồi Tám", "Hồi 8"),
    ("Hồi Chín", "Hồi 9"),
]

SPECIFIC_OVERRIDES_B = {}

proposals = []
blockers = []
majors = []

for it in items:
    iid = it['id']
    en = it['en']
    cur_vi = it.get('current_vi', en)
    src_tokens = it['tokens']

    if iid in SPECIFIC_OVERRIDES_B:
        vi_final = SPECIFIC_OVERRIDES_B[iid]
    elif it.get('is_tech'):
        vi_final = en
    else:
        vi = cur_vi

        # Clean tags corrupted by translation
        vi = re.sub(r'<kích thước=(\d+)>', r'<size=\1>', vi)
        vi = re.sub(r'<màu=([^>]+)>', r'<color=\1>', vi)
        vi = vi.replace('</kích thước>', '</size>').replace('</màu>', '</color>')

        # Unclosed tag protection
        if iid in UNCLOSED_SIZE_IDS_B:
            # Ensure it does NOT have </size>
            if '</size>' in vi:
                vi = vi.replace('</size>', '')
        else:
            if '</size>' not in en and '</size>' in vi:
                vi = vi.replace('</size>', '')

        if '</color>' not in en and '</color>' in vi:
            vi = vi.replace('</color>', '')

        # Apply standardized replacements
        for old, new in REPLACEMENTS_PART_B:
            vi = vi.replace(old, new)

        vi_final = vi

    # Normalize NFC
    vi_final = unicodedata.normalize('NFC', vi_final)

    # Validate tokens
    ok_tok, st, dt = check_tokens(src_tokens, vi_final)
    if not ok_tok:
        blockers.append(f"[{iid}] Token mismatch! Src: {st} vs Dst: {dt}")

    # Validate control chars
    ok_ctrl, sc, dc = check_control_chars(en, vi_final)
    if not ok_ctrl:
        blockers.append(f"[{iid}] Control char mismatch! Src: {sc} vs Dst: {dc}")

    proposals.append({
        "id": iid,
        "scene_id": it['scene_id'],
        "en": en,
        "vi_editorial": vi_final,
        "is_tech": it.get('is_tech', False),
        "tokens": src_tokens
    })

print(f"Partition B generated {len(proposals)} proposals.")
print(f"Blockers: {len(blockers)}, Majors: {len(majors)}")

if blockers:
    for b in blockers[:10]:
        print(" ", b)

# Write output
with open(PROP_B, 'w', encoding='utf-8') as f:
    for p in proposals:
        f.write(json.dumps(p, ensure_ascii=False) + '\n')

with open(RESULT_B, 'w', encoding='utf-8') as f:
    json.dump({
        "partition": "B",
        "total": len(proposals),
        "blockers": len(blockers),
        "majors": len(majors)
    }, f, indent=2)

print("Saved Partition B proposals successfully!")
