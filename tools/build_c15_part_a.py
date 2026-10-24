# -*- coding: utf-8 -*-
"""
Builder and QA-verifier for Campaign 15 Partition A:
STev_05_01..08 (10 scenes, 1,092 lines), STev_07_01..03 (3 scenes, 302 lines) = 1,394 lines.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/event_stories_part3_editorial_20261025_r01"
SOURCE_A = CAMPAIGN_DIR / "PARTITION_A_SOURCE.json"
PROP_A = CAMPAIGN_DIR / "PROPOSALS_PARTITION_A.jsonl"
RESULT_A = CAMPAIGN_DIR / "RESULT_PARTITION_A.json"

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

# 7 lines in Part A that have unclosed <size=XX> tags in EN source:
UNCLOSED_SIZE_IDS_A = {
    'STev_05_03.260',
    'STev_05_03.266',
    'STev_05_03.274',
    'STev_05_03.277',
    'STev_05_04.133',
    'STev_05_04.254',
    'STev_05_07.225'
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
    ("Chết tiệt...! Bản đồ kho báu bên trong là của tôi! Bạn không lấy nó!!",
     "Khốn thật...! Tấm bản đồ kho báu bên trong là của ta! Đừng hòng cướp lấy nó!!"),
    ("Chết tiệt... Nó đánh rơi lá thư giữa chừng!", "Chết thật... Nó đánh rơi lá thư giữa đường rồi!"),
    ("Chết tiệt", "Khốn thật"),
    ("chết tiệt", "chết thật"),
    ("Cái gì thế này...", "Chuyện quái gì thế này..."),
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
    ("Post Haste", "Cấp Tốc Bưu Cục"),
    ("Port Bellin", "Cảng Bellin"),
    ("Emor's Monolith", "Cự Thạch Emor"),
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
    ("Hồi Một", "Hồi 1"),
    ("Hồi Hai", "Hồi 2"),
    ("Hồi Ba", "Hồi 3"),
    ("Hồi Bốn", "Hồi 4"),
    ("Hồi Năm", "Hồi 5"),
    ("Hồi Sáu", "Hồi 6"),
    ("Hồi Bảy", "Hồi 7"),
    ("Hồi Tám", "Hồi 8"),
]

SPECIFIC_OVERRIDES_A = {
    'STev_05_06.387': 'Hì hì, cái mũi thính của tôi đã đánh hơi được rồi!==W== Hết đường trốn thoát rồi nhé, tôi sẽ tóm gọn các người ngay đây!',
    'STev_05_07.315': 'Cho đến lúc đó, cảm ơn vì đã luôn giữ cho chúng tồn tại"...==W== Rốt cuộc chuyện này là thế nào chứ...?',
    'STev_05_08.152': 'Amber, Freesia! Chuyến hàng này đã chuẩn bị xong xuôi rồi. Bắt đầu quá trình giao thư thôi nào!',
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
