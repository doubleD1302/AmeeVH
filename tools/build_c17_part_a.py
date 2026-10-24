# -*- coding: utf-8 -*-
"""
Builder and QA-verifier for Campaign 17 Partition A:
Non-CG scenes (19 scenes, 1,257 lines) + CG_149 (3 scenes, 257 lines) = 1,514 lines.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))

from translations_stm10001_slice1 import TRANSLATIONS_SLICE1
from translations_stm10001_slice2 import TRANSLATIONS_SLICE2
from translations_stm10001_slice3 import TRANSLATIONS_SLICE3
from translations_slice4 import TRANSLATIONS_SLICE4

TRANSLATIONS_ALL_SLICES = {}
TRANSLATIONS_ALL_SLICES.update(TRANSLATIONS_SLICE1)
TRANSLATIONS_ALL_SLICES.update(TRANSLATIONS_SLICE2)
TRANSLATIONS_ALL_SLICES.update(TRANSLATIONS_SLICE3)
TRANSLATIONS_ALL_SLICES.update(TRANSLATIONS_SLICE4)
print(f"Loaded {len(TRANSLATIONS_ALL_SLICES)} slice translations into Partition A.")

CAMPAIGN_DIR = ROOT / "work/editorial/tutorial_and_character_cg_editorial_20261025_r01"
SOURCE_A = CAMPAIGN_DIR / "PARTITION_A_SOURCE.json"
PROP_A = CAMPAIGN_DIR / "PROPOSALS_PARTITION_A.jsonl"
RESULT_A = CAMPAIGN_DIR / "RESULT_PARTITION_A.json"

TAG_PATTERN = re.compile(r'<[^>]+>|==[a-zA-Z0-9_.-]+==|\{[0-9]+\}|_NOT_IN_LOG_')

# 33 lines in Part A that have unclosed <size=XX> tags in EN source:
UNCLOSED_SIZE_IDS_A = {
    'STm10001_01.121', 'STm10001_01.249', 'STm10001_03.160', 'STm10001_03.317',
    'STm10001_03.410', 'STm10001_03.412', 'STm10001_03.441', 'STm10001_04.54',
    'STm10001_04.88', 'STm10001_05.274', 'STm10001_06.321', 'STm10001_08.343',
    'STm10001_09.313', 'STm10001_09.364', 'STm10001_09.366', 'STm10001_09.368',
    'STm10001_09.370',
    'CG_149_01.146', 'CG_149_01.279', 'CG_149_01.287', 'CG_149_01.307',
    'CG_149_02.200', 'CG_149_02.201', 'CG_149_02.230', 'CG_149_02.259',
    'CG_149_02.310', 'CG_149_02.326', 'CG_149_02.331',
    'CG_149_03.186', 'CG_149_03.196', 'CG_149_03.261', 'CG_149_03.264',
    'CG_149_03.266'
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
    ("Chết tiệt, cô ấy hoàn toàn gài bẫy tôi!", "Khốn thật, cô ta gài bẫy mình rồi!"),
    ("Lại là hành động đó—chết tiệt, cô ấy hoàn toàn mất trí rồi!", "Lại là trò đó—khốn kiếp, cô ta điên thật rồi!"),
    ("Cái quái gì thế này?!", "Chuyện quái gì thế này?!"),
    ("Chết tiệt! Đồ quái đản không biết xấu hổ!", "Khốn thật! Đồ biến thái không biết xấu hổ!"),
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
    ("Noya & Hổ phách & Hoa diên vĩ", "Noya & Amber & Iris"),
    ("Hổ phách", "Amber"),
    ("Hoa diên vĩ", "Iris"),
    ("Diên vĩ", "Iris"),
    ("Diên Vĩ", "Iris"),
    ("Số tiền còn lại cho Hội Ngôi Sao Mới: 3 Dorra", "Số ngân quỹ còn lại của Lữ Đoàn Tân Tinh: 3 Dorra"),
    ("Hội Ngôi Sao Mới", "Lữ Đoàn Tân Tinh"),
    ("Hiệp hội Ngôi sao Mới", "Lữ Đoàn Tân Tinh"),
    ("Sếp của Sếp Accord", "Sếp của Hiệp Ước Boss"),
    ("trọng tài hoàng hôn", "Trọng Tài Hoàng Hôn"),
    ("Trọng tài hoàng hôn", "Trọng Tài Hoàng Hôn"),
    ("Monolith", "Cự Thạch"),
    ("các Archon", "các Chấp Chính Quan"),
    ("Archon", "Chấp Chính Quan"),
    ("Grace Imperium", "Đế Quốc Grace"),
    ("Thiên Chúa Ân Sủng", "Mắt Ân Điển"),
    ("Cổ vật", "Di Vật"),
    ("cổ vật", "di vật"),
    ("Hộp điều ước", "Hộp Ước Nguyện"),
    ("tảng đá nguyên khối", "Cự Tháp"),
    ("màn một", "Hồi 1"),
    ("màn hai", "Hồi 2"),
    ("màn ba", "Hồi 3"),
    ("Màn một", "Hồi 1"),
    ("Màn hai", "Hồi 2"),
    ("Màn ba", "Hồi 3"),
    ("Trọng tài Hoàng hôn", "Phán Quan Hoàng Hôn"),
    ("Trọng tài hoàng hôn", "Phán Quan Hoàng Hôn"),
    ("Trọng Tài Hoàng Hôn", "Phán Quan Hoàng Hôn"),
    ("trọng tài hoàng hôn", "phán quan hoàng hôn"),
    ("Sếp của Sếp Accord", "Boss của Hiệp Ước Boss"),
]

SPECIFIC_OVERRIDES_A = {
    'STm00_01.266': 'Hỡi Mắt Ân Điển tối cao! Xin hãy ban cho chúng con dù chỉ một Di Vật mà chúng con có thể bán lấy một số tiền kếch xù thôi! Cầu xin Người đấy!',
    'STm00_01.304': 'Nhưng từ trước tới nay tất cả những gì chúng ta làm==W== chỉ là đi lang bạt khắp nơi như những Du Hành Giả thôi mà!==W== Đâu có đời nào tìm được việc dễ dàng đến thế chứ...==W== Đến đây là hết thật rồi!==W== Aaahhh!==W==',
    'STm00_02.177': 'Kìa, đừng có trêu người ta thế chứ!',
    'STm00_02.215': 'Các Du Hành Giả leo lên Cự Tháp, dâng lời nguyện cầu trước Hộp Ước Nguyện và nhận về những Di Vật hùng mạnh.==W== Nhưng đổi lại, Cự Tháp sẽ lấy đi một phần ký ức của họ.',
    'ST_sys_soldier_intro.98': 'Có vẻ Đế Quốc Grace đã dốc toàn lực cho lần xuất hiện này của Chấp Chính Quan.',
    'ST_sys_soldier_intro.156': 'Biệt Đội Phản Ứng Dị Thường Đế Quốc Grace',
    'ST_sys_soldier_intro.179': 'Đế Quốc Grace đã lập tức phái một đội tiên phong, nhưng họ lại vấp phải bức tường bế tắc.',
    'STm00_01.194': 'Noya, Amber và Iris',
    'CG_149_01.4': 'Hồi 1',
    'CG_149_01.242': 'Chà chà?==W====RT== Ái chà, chà chà chà...==W== Đây chẳng phải là Boss kính yêu sao? ♪',
    'CG_149_02.4': 'Hồi 2',
    'CG_149_03.4': 'Hồi 3',
}

proposals = []
blockers = []
majors = []

for it in items:
    iid = it['id']
    en = it['en']
    cur_vi = it.get('current_vi', en)
    src_tokens = TAG_PATTERN.findall(en)

    if iid in SPECIFIC_OVERRIDES_A:
        vi_final = SPECIFIC_OVERRIDES_A[iid]
    elif iid in TRANSLATIONS_ALL_SLICES:
        vi_final = TRANSLATIONS_ALL_SLICES[iid]
    elif it.get('is_tech'):
        vi_final = en
    else:
        vi = cur_vi

        # Clean tags corrupted by translation
        vi = vi.replace('== W==', '==W==')
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
