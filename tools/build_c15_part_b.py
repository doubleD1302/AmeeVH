# -*- coding: utf-8 -*-
"""
Builder and QA-verifier for Campaign 15 Partition B:
STev_07_04..09 (6 scenes, 674 lines), STev_08_01..08 (8 scenes, 855 lines) = 1,529 lines.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/event_stories_part3_editorial_20261025_r01"
SOURCE_B = CAMPAIGN_DIR / "PARTITION_B_SOURCE.json"
PROP_B = CAMPAIGN_DIR / "PROPOSALS_PARTITION_B.jsonl"
RESULT_B = CAMPAIGN_DIR / "RESULT_PARTITION_B.json"

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

# 18 lines in Part B that have unclosed <size=XX> tags in EN source:
UNCLOSED_SIZE_IDS_B = {
    'STev_07_06.396', 'STev_07_08.171',
    'STev_08_01.233', 'STev_08_01.239', 'STev_08_01.348',
    'STev_08_03.101', 'STev_08_03.118', 'STev_08_03.308', 'STev_08_03.312',
    'STev_08_04.45', 'STev_08_04.75', 'STev_08_04.77', 'STev_08_04.201',
    'STev_08_04.222', 'STev_08_04.290', 'STev_08_05.60', 'STev_08_05.133',
    'STev_08_05.364'
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
    ("Chết tiệt cô ấy!", "Khốn thật!"),
    ("Chết tiệt. Chúng ta phải đưa gì vào báo cáo?", "Chết thật. Chúng ta phải viết gì vào báo cáo đây?"),
    ("Chết tiệt... Con của tôi đã bị nổ tung thành từng mảnh...", "Khốn kiếp... Cục cưng của tôi đã bị nổ tung thành từng mảnh rồi..."),
    ("Chết tiệt!", "Khốn thật!"),
    ("Chết tiệt", "Khốn thật"),
    ("chết tiệt", "chết thật"),
    ("Cái-==W==tên ngốc đó đang làm cái quái gì vậy?!", "Cái-==W==tên ngốc đó đang làm cái trò gì thế hả?!"),
    ("cái quái gì", "chuyện quái gì"),
    ("Làm sao mà tôi lại nghẹn ngào thế này vào thời điểm này...", "Sao tôi lại luống cuống vào đúng lúc này cơ chứ..."),
    ("làm sao mà", "sao có thể"),
    ("bạn biết đấy", "cậu biết đấy"),
    ("khoảng không quảng cáo", "kho đồ"),
    ("chụp nhanh bộ nhớ", "hồi ức đặc tả"),
    ("Ma Vương", "Bạo Chúa"),
    ("Bạo Quân", "Bạo Chúa"),
    ("Viên đá Linh hồn", "Hồn Thạch"),
    ("viên đá Linh hồn", "Hồn Thạch"),
    ("đá Linh hồn", "Hồn Thạch"),
    ("Hổ phách", "Amber"),
    ("Hoa diên vĩ", "Iris"),
    ("Diên vĩ", "Iris"),

    # 2. Master Glossary terms in Part B
    ("Hội Ngôi Sao Mới", "Lữ Đoàn Tân Tinh"),
    ("Hiệp hội Ngôi sao Mới", "Lữ Đoàn Tân Tinh"),
    ("Lucky Oasis", "Ốc Đảo May Mắn"),
    ("Lucky Oasis's", "Ốc Đảo May Mắn"),
    ("CEO of Boss Accord", "CEO của Hiệp Ước Boss"),
    ("Boss Accord", "Hiệp Ước Boss"),
    ("Emor's Monolith", "Cự Thạch Emor"),
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
    ("Hồi Một", "Hồi 1"),
    ("Hồi Hai", "Hồi 2"),
    ("Hồi Ba", "Hồi 3"),
    ("Hồi Bốn", "Hồi 4"),
    ("Hồi Năm", "Hồi 5"),
    ("Hồi Sáu", "Hồi 6"),
    ("Hồi Bảy", "Hồi 7"),
    ("Hồi Tám", "Hồi 8"),
]

SPECIFIC_OVERRIDES_B = {
    'STev_08_01.163': 'Vâng. Hồn Thạch của mọi người đều đã cạn kiệt hoàn toàn Ân Điển. Có nghĩa là...==W== Loxy sẽ không thể khởi động được nữa!!',
    'STev_08_03.224': 'Iris & Amber',
    'STev_08_05.143': 'Chúng ta tiêu đời rồi... Sao tôi lại luống cuống thế này vào đúng lúc dầu sôi lửa bỏng nhất chứ?!==W== Cậu có biết bây giờ là mấy giờ rồi không?! Hội nghị sẽ bắt đầu sau ba giờ nữa đấy!!',
}

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
