# -*- coding: utf-8 -*-
"""
Builder and QA-verifier for Campaign 16 Partition A:
STev_09 (8 scenes, 764 lines), STev_10 (9 scenes, 913 lines) = 1,676 lines.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/event_stories_part4_editorial_20261025_r01"
SOURCE_A = CAMPAIGN_DIR / "PARTITION_A_SOURCE.json"
PROP_A = CAMPAIGN_DIR / "PROPOSALS_PARTITION_A.jsonl"
RESULT_A = CAMPAIGN_DIR / "RESULT_PARTITION_A.json"

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

# 3 lines in Part A that have unclosed <size=XX> tags in EN source:
UNCLOSED_SIZE_IDS_A = {
    'STev_10_03.118',
    'STev_10_06.271',
    'STev_10_07.184'
}

def check_tokens(src_tokens, dst_text):
    dst_tokens = TAG_PATTERN.findall(dst_text)
    return sorted(src_tokens) == sorted(dst_tokens), src_tokens, dst_tokens

def check_control_chars(src_text, dst_text):
    src_ctrls = [c for c in src_text if ord(c) < 32 and c not in '\r\n\t']
    dst_ctrls = [c for c in dst_text if ord(c) < 32 and c not in '\r\n\t']
    return src_ctrls == dst_ctrls, src_ctrls, dst_ctrls

with open(SOURCE_A, 'r', encoding='utf-8') as f:
    items = json.load(f)

print(f"Loaded {len(items)} items from Partition A.")

REPLACEMENTS_PART_A = [
    # 1. Banned machine translation calques
    ("Lũ Bọ Cạp Sa Mạc chết tiệt! Tại sao luôn là họ?", "Lũ Bọ Cạp Sa Mạc khốn kiếp! Tại sao lúc nào cũng là chúng chứ?"),
    ("Tên phó đội trưởng chết tiệt đó... Vứt bỏ tôi tất cả công việc rác rưởi này...", "Tên phó đội trưởng đáng ghét đó... Đùn đẩy hết mớ việc rác rưởi này cho tôi..."),
    ("Chết tiệt! Buông ra! Tôi đang báo cáo bạn với Vệ binh Hoàng gia", "Khốn thật! Buông ra mau! Ta sẽ tố cáo các người với Cận Vệ Hoàng Gia"),
    ("Chết tiệt! Cảnh báo những người khác! Nhóm Mèo Trắng đang ở đây!", "Khốn kiếp! Mau báo động cho mọi người! Băng Mèo Trắng đang ở đây!"),
    ("Chết tiệt! Cậu đã chơi chúng tôi ngay từ đầu...", "Khốn thật! Ngươi đã gài bẫy bọn ta ngay từ đầu..."),
    ("Chết tiệt! Kasimira, thức dậy đi!", "Khốn thật! Kasimira, tỉnh dậy mau!"),
    ("Hả? Cậu đang nói về cái quái gì vậy?", "Hả? Cậu đang lảm nhảm chuyện gì thế hả?"),
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

    # 2. Master Glossary terms in Part A
    ("Hội Ngôi Sao Mới", "Lữ Đoàn Tân Tinh"),
    ("Hiệp hội Ngôi sao Mới", "Lữ Đoàn Tân Tinh"),
    ("Vệ binh Hoàng gia", "Cận Vệ Hoàng Gia"),
    ("vệ binh hoàng gia", "cận vệ hoàng gia"),
    ("City of a Thousand Monoliths", "Thành Phố Ngàn Cự Tháp"),
    ("Thành phố ngàn khối đá", "Thành Phố Ngàn Cự Tháp"),
    ("Trekker Association", "Hiệp Hội Du Hành"),
    ("Hiệp hội Du hành", "Hiệp Hội Du Hành"),
    ("Trekker", "Du Hành Giả"),
    ("Monolith", "Cự Thạch"),
    ("các Archon", "các Chấp Chính Quan"),
    ("Archon", "Chấp Chính Quan"),

    # 3. Act titles in Part A
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

SPECIFIC_OVERRIDES_A = {
    'STev_09_02.264': 'Hướng 10 giờ!==W== Thêm hai tên nữa đang lao tới!',
    'STev_09_07.354': 'Chaton!==W== Chúng đang lao tới đấy!',
    'STev_10_04.306': 'Mặc kệ đi, tiên hạ thủ vi cường!==W== Mọi người, xông lên bắt lấy chúng!',
    'STev_10_05.262': 'Đứng lại mau!==W== Mau trả lại chỗ nước uống cho tôi!',
}

proposals = []
blockers = []
majors = []

for it in items:
    iid = it['id']
    en = it['en']
    cur_vi = it.get('current_vi', en)
    src_tokens = it['tokens']

    if iid in SPECIFIC_OVERRIDES_A:
        vi_final = SPECIFIC_OVERRIDES_A[iid]
    elif it.get('is_tech'):
        vi_final = en
    else:
        vi = cur_vi

        # Clean tags corrupted by translation
        vi = re.sub(r'<kích thước=(\d+)>', r'<size=\1>', vi)
        vi = re.sub(r'<màu=([^>]+)>', r'<color=\1>', vi)
        vi = vi.replace('</kích thước>', '</size>').replace('</màu>', '</color>')

        # Unclosed tag protection
        if iid in UNCLOSED_SIZE_IDS_A:
            # Ensure it does NOT have </size>
            if '</size>' in vi:
                vi = vi.replace('</size>', '')
        else:
            if '</size>' not in en and '</size>' in vi:
                vi = vi.replace('</size>', '')

        if '</color>' not in en and '</color>' in vi:
            vi = vi.replace('</color>', '')

        # Apply standardized replacements
        for old, new in REPLACEMENTS_PART_A:
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

print(f"Partition A generated {len(proposals)} proposals.")
print(f"Blockers: {len(blockers)}, Majors: {len(majors)}")

if blockers:
    for b in blockers[:10]:
        print(" ", b)

# Write output
with open(PROP_A, 'w', encoding='utf-8') as f:
    for p in proposals:
        f.write(json.dumps(p, ensure_ascii=False) + '\n')

with open(RESULT_A, 'w', encoding='utf-8') as f:
    json.dump({
        "partition": "A",
        "total": len(proposals),
        "blockers": len(blockers),
        "majors": len(majors)
    }, f, indent=2)

print("Saved Partition A proposals successfully!")
