# -*- coding: utf-8 -*-
"""
Builder and QA-verifier for Campaign 14 Partition B:
STev_03_04..09 (562 lines), STev_04_01..10 (1,058 lines) = 1,620 lines.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/event_stories_part2_editorial_20261025_r01"
SOURCE_B = CAMPAIGN_DIR / "PARTITION_B_SOURCE.json"
PROP_B = CAMPAIGN_DIR / "PROPOSALS_PARTITION_B.jsonl"
RESULT_B = CAMPAIGN_DIR / "RESULT_PARTITION_B.json"

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

# 19 lines in Part B that have unclosed <size=XX> tags in EN source:
UNCLOSED_SIZE_IDS_B = {
    'STev_03_04.128', 'STev_03_04.142', 'STev_03_04.151', 'STev_03_05.96',
    'STev_03_05.309', 'STev_03_06.280', 'STev_03_06.310', 'STev_03_06.324',
    'STev_03_07.332', 'STev_04_01.91', 'STev_04_07.58', 'STev_04_07.136',
    'STev_04_07.281', 'STev_04_07.306', 'STev_04_09.100', 'STev_04_09.271',
    'STev_04_09.340', 'STev_04_10.365', 'STev_04_10.381'
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
    # 1. Critical machine translation calques in Part B
    ("Một lưỡi dao sắc bén đứng trước mặt tôi. Một giọng nói bên trong hứa rằng nếu tôi uống nó, cơn đau sẽ chấm dứt.",
     "Một lưỡi kiếm sắc lạnh cắm sững trước mắt tôi. Thanh âm từ đáy lòng thì thầm rằng chỉ cần nắm lấy nó, mọi nỗi đau sẽ tan biến."),
    ("nếu tôi uống nó, cơn đau sẽ chấm dứt", "chỉ cần nắm lấy nó, mọi nỗi đau sẽ tan biến"),
    ("uống nó", "nắm lấy nó"),
    ("Tôi đã tự tay hái từng quả pháo này.", "Từng phong pháo này đều do chính tay tôi cẩn thận lựa chọn đấy."),
    ("tự tay hái từng quả pháo", "tự tay lựa từng phong pháo"),
    ("tự tay hái", "tự tay chọn"),
    ("Xe ngựa và bóng ma... Hai Archon", "Chiến Xa và U Linh... Hai Chấp Chính Quan"),
    ("Xe ngựa và bóng ma", "Chiến Xa và U Linh"),
    ("Tàn tích đông lạnh", "Tàn Tích Băng Giá"),
    ("tàn tích đông lạnh", "Tàn Tích Băng Giá"),
    ("Đêm Vĩnh Cửu", "Đêm Trường Vĩnh Cửu"),
    ("Vệ binh bình minh", "Vệ Binh Rạng Đông"),
    ("Vệ Binh Bình Minh", "Vệ Binh Rạng Đông"),
    ("Thành phố ngàn khối đá", "Thành Phố Ngàn Cự Tháp"),
    ("thành phố ngàn khối đá", "Thành Phố Ngàn Cự Tháp"),
    ("Do đó thiếu ngủ", "Thế nên mới mất ngủ đấy"),
    ("Lấy làm tiếc", "Thứ lỗi nhé"),
    ("Chết tiệt!", "Khốn thật!"),
    ("chết tiệt", "chết thật"),
    ("cái quái gì", "chuyện quái gì"),
    ("làm sao mà", "sao có thể"),
    ("bạn biết đấy", "cậu biết đấy"),
    ("khoảng không quảng cáo", "kho đồ"),
    ("chụp nhanh bộ nhớ", "hồi ức đặc tả"),
    ("Ma Vương", "Bạo Chúa"),

    # 2. Master Glossary terms in Part B
    ("Hội Ngôi Sao Mới", "Lữ Đoàn Tân Tinh"),
    ("Hiệp hội Ngôi sao Mới", "Lữ Đoàn Tân Tinh"),
    ("các Archon", "các Chấp Chính Quan"),
    ("Archon", "Chấp Chính Quan"),
    ("người Loong", "người Tộc Long"),
    ("tộc Loong", "Tộc Long"),
    ("Loong", "Tộc Long"),
    ("Cangwu", "Thương Ngô"),
    ("Nian", "Niên Thú"),
    ("Lucky", "Lai Phúc"),
    ("Trigger of Dawn", "Phát Súng Rạng Đông"),
    ("Bạo Quân", "Bạo Chúa"),
    ("tầng lớp ưu tú", "Lớp Tinh Anh"),
    ("Lớp ưu tú", "Lớp Tinh Anh"),

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
    ("Màn mười", "Hồi 10"),
    ("Màn Mười", "Hồi 10"),
    ("màn mười", "Hồi 10"),
    ("Hồi Một", "Hồi 1"),
    ("Hồi Hai", "Hồi 2"),
    ("Hồi Ba", "Hồi 3"),
    ("Hồi Bốn", "Hồi 4"),
    ("Hồi Năm", "Hồi 5"),
    ("Hồi Sáu", "Hồi 6"),
    ("Hồi Bảy", "Hồi 7"),
    ("Hồi Tám", "Hồi 8"),
    ("Hồi Chín", "Hồi 9"),
    ("Hồi Mười", "Hồi 10"),
]

# Specific handcrafted overrides for perfect token and Light Novel parity
SPECIFIC_OVERRIDES_B = {
    'STev_03_09.357': '... là để chúng ta==W== năm nào cũng được cùng nhau đứng dưới bầu trời đêm này, tràn đầy hy vọng về một năm mới sắp tới.',
    'STev_04_01.91': '<color=#bd3059><size=78><r=•>Đó</r> <r=•>chính</r> <r=•>là</r> <r=•>những</r> <r=•>gì</r> <r=•>chúng</r> đáng phải nhận.',
    'STev_04_02.305': 'Chịu trói đi!==W== Giờ thì ngươi hết đường chạy thoát rồi nhé!',
    'STev_04_04.231': '"Khi chiến tranh khép lại, các ngài đã gửi gắm hòa bình cho nhân loại rồi trở về==RT==với Cự Thạch, để con người tự tay gìn giữ lấy nền thái bình ấy."',
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
