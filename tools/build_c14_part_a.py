# -*- coding: utf-8 -*-
"""
Builder and QA-verifier for Campaign 14 Partition A:
DP_* (305 lines), STev_02 (1,007 lines), STev_03_01..03 (282 lines) = 1,594 lines.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/event_stories_part2_editorial_20261025_r01"
SOURCE_A = CAMPAIGN_DIR / "PARTITION_A_SOURCE.json"
PROP_A = CAMPAIGN_DIR / "PROPOSALS_PARTITION_A.jsonl"
RESULT_A = CAMPAIGN_DIR / "RESULT_PARTITION_A.json"

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

# 3 lines in Part A that have unclosed <size=XX> tags in EN source:
UNCLOSED_SIZE_IDS_A = {
    'STev_02_02.53',
    'STev_02_04_a.60',
    'STev_02_05.78'
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
    ("Chúng tôi đánh một lễ hội Loong", "Chúng ta đến đúng dịp Lễ Hội Tầm Xuân của Tộc Long"),
    ("đánh một lễ hội", "đến đúng dịp lễ hội"),
    ("Chúng tôi đóng đinh nó! Chúng ta về nhà thôi!", "Thành công mỹ mãn rồi! Về nhà thôi nào!"),
    ("Chúng tôi đóng đinh nó!", "Thành công mỹ mãn rồi!"),
    ("đóng đinh nó", "làm tốt lắm"),
    ("Chúng tôi thực sự đã đi trước một chút!", "Tính ra tụi mình còn kiếm được chút lời đấy chứ!"),
    ("đã đi trước một chút", "còn kiếm được chút lời"),
    ("Các bạn thật là ngu ngốc!", "Mấy người thật là mất hứng quá đi à!"),
    ("thật là ngu ngốc", "thật là mất hứng"),
    ("Gương mặt quen thuộc trong một triệu", "Người Quen Trong Vạn Người"),
    ("Một lối vào ngoạn mục", "Màn Xuất Hiện Ngoạn Mục"),
    ("Lễ hội tuyết vui vẻ!", "Chúc mừng Lễ Hội Mùa Tuyết!"),
    ("Lễ hội tuyết vui vẻ", "Lễ Hội Mùa Tuyết an lành"),
    ("Chết tiệt!", "Khốn thật!"),
    ("chết tiệt", "chết thật"),
    ("cái quái gì", "chuyện quái gì"),
    ("làm sao mà", "sao có thể"),
    ("bạn biết đấy", "cậu biết đấy"),
    ("khoảng không quảng cáo", "túi đồ"),
    ("chụp nhanh bộ nhớ", "hồi ức đặc tả"),
    ("Ma Vương", "Bạo Chúa"),

    # 2. Master Glossary terms in Part A
    ("Hội Ngôi Sao Mới", "Lữ Đoàn Tân Tinh"),
    ("Hiệp hội Ngôi sao Mới", "Lữ Đoàn Tân Tinh"),
    ("Thần cây tuyết", "Tinh Linh Cây Tuyết"),
    ("Thần Tuyết Thụ", "Tinh Linh Cây Tuyết"),
    ("Tinh thần cây tuyết", "Tinh Linh Cây Tuyết"),
    ("thần cây tuyết", "Tinh Linh Cây Tuyết"),
    ("Cô Linh", "Tiểu Tinh Linh"),
    ("Thần Cây", "Tinh Linh Cây Tuyết"),
    ("Cây Snowish", "Cây Tuyết"),
    ("Lễ Hội Snowish", "Lễ Hội Mùa Tuyết"),
    ("Lễ hội Snowish", "Lễ Hội Mùa Tuyết"),
    ("Bạo Quân", "Bạo Chúa"),
    ("Bạo chúa Lễ Hội Mùa Tuyết", "Bạo Chúa Lễ Hội Mùa Tuyết"),
    ("Cangwu", "Thương Ngô"),
    ("người Loong", "người Tộc Long"),
    ("tộc Loong", "Tộc Long"),
    ("Loong", "Tộc Long"),
    ("Sprite", "Tiểu Tinh Linh"),
    ("Gia Tộc Tàn Phong", "Bộ Tộc Tàn Phong"),
    ("Pep Pep Juice", "Nước Ép Năng Lượng Pep Pep"),

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
    ("Màn mười", "Hồi 10"),
    ("Màn Mười", "Hồi 10"),
    ("màn mười", "Hồi 10"),
    ("Màn mười một", "Hồi 11"),
    ("Màn Mười Một", "Hồi 11"),
    ("màn mười một", "Hồi 11"),
    ("Hồi Một", "Hồi 1"),
    ("Hồi Hai", "Hồi 2"),
    ("Hồi Ba", "Hồi 3"),
    ("Hồi Bốn", "Hồi 4"),
    ("Hồi Năm", "Hồi 5"),
    ("Hồi Sáu", "Hồi 6"),
    ("Hồi Bảy", "Hồi 7"),
    ("Hồi Tám", "Hồi 8"),
    ("Hồi Chín", "Hồi 9"),
    ("Hồi Mười Một", "Hồi 11"),
    ("Hồi Mười", "Hồi 10"),
]

proposals = []
blockers = []
majors = []

for it in items:
    iid = it['id']
    en = it['en']
    cur_vi = it.get('current_vi', en)
    src_tokens = it['tokens']

    # Special handling for opcode line: STev_02_02.86
    if iid == 'STev_02_02.86':
        # Preserve control byte \x143 and \x04\x0fSetCho
        vi_final = "\x143Không có gì đâu ạ~ Chúc mọi người có một Lễ Hội Mùa Tuyết ngập tràn niềm vui!\x04\x0fSetChoice"
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
