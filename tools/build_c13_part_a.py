# -*- coding: utf-8 -*-
"""
Builder and QA-verifier for Campaign 13 Partition A (STsp_12 to STsp_15, 1,348 lines).
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/side_stories_part2_editorial_20261025_r01"
SOURCE_A = CAMPAIGN_DIR / "PARTITION_A_SOURCE.json"
PROP_A = CAMPAIGN_DIR / "PROPOSALS_PARTITION_A.jsonl"
RESULT_A = CAMPAIGN_DIR / "RESULT_PARTITION_A.json"

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

KEEP_EN_IDS = {
    'STsp_12_03.1',
    'STsp_12_04.91',
    'STsp_15_03.55'
}

BANNED_WORDS = [
    (r"\bMa Vương\b", "Cấm dùng Ma Vương cho Demon King / Lord"),
    (r"\bchết tiệt\b", "Cấm dùng chửi thề thô tục 'chết tiệt'"),
    (r"\bbạn biết đấy\b", "Calque máy dịch 'you know'"),
    (r"\bcái quái gì\b", "Calque dịch thô 'what the hell'"),
    (r"\blàm sao mà\b", "Calque dịch thô 'how come'"),
    (r"\btrỗi dậy và tỏa sáng\b", "Calque máy dịch 'rise and shine'"),
    (r"\bnhảy ra khỏi lồng ngực\b", "Calque máy dịch 'jump out of one's chest'"),
    (r"\bGrand Thanh tra\b", "Calque hỗn tạp 'Grand Thanh tra' -> Đại Thanh Tra"),
    (r"\bHòn Hồn Thạch\b", "Calque dịch lặp 'Hòn Hồn Thạch' -> Hồn Thạch"),
    (r"\bnhững kẻ buồn ngủ\b", "Calque dịch máy 'sleepyheads'"),
    (r"\btrục mìn\b", "Calque dịch máy 'mineshaft'"),
    (r"\bKỵ Sĩ Hoàng Gia\b", "Imperial Guard (Tilia) phải dịch là Cận Vệ Hoàng Gia!"),
    (r"\bTrọng Tài Chạng Vạng\b", "Dusk Arbiter phải dịch là Trọng Tài Hoàng Hôn!"),
    (r"\b(Chiến Binh Cây Bụi|Chuột Cây Bụi|Thành cổ Cây bụi)\b", "Shrubshrew phải chuẩn hóa là Chuột Bụi!"),
    (r"\b(Đá Linh Hồn|Đá Hồn)\b", "Soul Stone phải chuẩn hóa là Hồn Thạch!"),
    (r"\b(Sơ Quang|Trần Sa)\b", "Noya tuyệt đối không dùng Sơ Quang / Trần Sa (phải là Noya - Khải Minh)!"),
    (r"\bHổ phách\b", "Tên nhân vật Amber cấm dịch thành Hổ phách!"),
    (r"\bDiên Vĩ\b", "Tên nhân vật Iris cấm dịch thành Diên Vĩ!"),
    (r"\bPhòng Màu Trắng\b", "White Room phải dịch là Phòng Trắng!"),
    (r"\bĐêm Vĩnh Cửu\b", "Nocturn Eterna phải dịch là Đêm Trường Vĩnh Cửu!"),
    (r"\bKim Khố Ý Chí Ân Tứ\b", "Grace Imperium phải dịch là Đế Quốc Grace!"),
    (r"\b(Bà Angie|Quý Cô Angie)\b", "Lady Angie phải dịch là Tiểu Thư Angie!"),
    (r"\bHiệu Trưởng Allie\b", "Director Allie phải dịch là Giám Đốc Allie!"),
    (r"Cái gì trên thế giới", "Calque máy dịch 'What in the world'"),
    (r"\bbánh mì nướng\b", "Calque dịch sai từ toast (nâng ly)"),
]

def check_tokens(src_tokens, dst_text):
    dst_tokens = TAG_PATTERN.findall(dst_text)
    return sorted(src_tokens) == sorted(dst_tokens), src_tokens, dst_tokens

def check_control_chars(src_text, dst_text):
    src_ctrls = [c for c in src_text if ord(c) < 32 and c not in '\r\n']
    dst_ctrls = [c for c in dst_text if ord(c) < 32 and c not in '\r\n']
    return src_ctrls == dst_ctrls, src_ctrls, dst_ctrls

with open(SOURCE_A, 'r', encoding='utf-8') as f:
    items = json.load(f)

print(f"Loaded {len(items)} items from Partition A.")

REPLACEMENTS = [
    # Banned words fixes
    ("Chết tiệt, họ có Eleanor! Đi ngay!", "Khốn thật, chúng bắt được Eleanor rồi! Rút mau!"),
    ("Cap, rắc rối! Chúng ta không thể nhìn thấy cái quái gì cả!", "Đội trưởng, nguy rồi! Bọn em chẳng thấy trời trăng gì cả!"),
    ("Chết tiệt! Quên chuyện này đi, đi thôi—", "Khốn thật! Bỏ đi, chuồn lẹ—"),
    ("Cái quái gì vậy... ==W== Ugh!", "Chuyện quái quỷ gì thế này... ==W== Ư!"),
    ("Chết tiệt! Tss... ==W== Tôi đã mất cảnh giác rồi...!", "Chết thật! Chậc... ==W== Mình sơ suất quá rồi...!"),
    ("Chết tiệt!", "Khốn kiếp!"),
    ("chết tiệt", "chết thật"),
    ("cái quái gì", "chuyện quái gì"),
    ("làm sao mà", "sao có thể"),
    ("bạn biết đấy", "cậu hiểu mà"),
    ("Hổ phách", "Amber"),
    ("Diên Vĩ", "Iris"),
    ("Kỵ Sĩ Hoàng Gia", "Cận Vệ Hoàng Gia"),
    ("kỵ sĩ hoàng gia", "cận vệ hoàng gia"),
    ("Viên Hồn Thạch của tôi. Hết ân sủng.", "Hồn Thạch của tôi. Đã cạn kiệt Ân Tứ."),
    ("Viên Hồn Thạch", "Hồn Thạch"),
    ("viên Hồn Thạch", "Hồn Thạch"),
    ("Đá Linh Hồn", "Hồn Thạch"),
    ("Đá Hồn", "Hồn Thạch"),
    ("Thể Tinh Tú", "Tinh Hài"),
    ("thể Tinh Tú", "Tinh Hài"),
    ("Sếp Accord", "Hiệp Ước Boss"),
    ("Lady Rovina", "Tiểu Thư Rovina"),
    ("Lady Angie", "Tiểu Thư Angie"),
    ("Phòng Màu Trắng", "Phòng Trắng"),
    ("Đêm Vĩnh Cửu", "Đêm Trường Vĩnh Cửu"),
    ("Âm thanh cuộn! Máy ảnh cuộn!", "Âm thanh chuẩn bị! Máy quay chuẩn bị!"),
    ("Thị Vệ Cận Vệ Hoàng Gia", "Thị Vệ Cận Vệ Hoàng Gia"),
]

# Process lines
proposals = []
blockers = []
majors = []

for it in items:
    iid = it['id']
    en = it['en']
    cur_vi = it.get('current_vi', en)
    src_tokens = TAG_PATTERN.findall(en)

    if iid in KEEP_EN_IDS:
        vi_final = en
    else:
        vi = cur_vi

        # Token repairs for tags
        # Fix size tag translation in STsp_14
        vi = re.sub(r'<kích thước=(\d+)>', r'<size=\1>', vi)
        
        # If source does NOT have </color>, remove </color> from vi
        if '</color>' not in en and '</color>' in vi:
            vi = vi.replace('</color>', '')
            
        # If source does NOT have </size>, remove </size> from vi
        if '</size>' not in en and '</size>' in vi:
            vi = vi.replace('</size>', '')

        # Standard replacements
        for old, new in REPLACEMENTS:
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
        blockers.append(f"[{iid}] Control opcode mismatch! Src: {[ord(c) for c in sc]} vs Dst: {[ord(c) for c in dc]}")

    # Validate banned words
    for pat, desc in BANNED_WORDS:
        if re.search(pat, vi_final, re.IGNORECASE):
            majors.append(f"[{iid}] Contains banned word '{pat}' ({desc}): {vi_final}")

    # Validate newline
    if '\n' in en and '\n' not in vi_final:
        blockers.append(f"[{iid}] Missing newline present in source")

    record = {
        "id": iid,
        "scene_id": it["scene_id"],
        "en": en,
        "vi_editorial": vi_final,
        "is_tech": it.get("is_tech", False),
        "tokens": src_tokens
    }
    proposals.append(record)

print(f"Total processed: {len(proposals)}")
print(f"Validation: {len(blockers)} Blockers, {len(majors)} Majors.")
if blockers:
    for b in blockers[:10]:
        print("  [BLOCKER]", b)
if majors:
    for m in majors[:10]:
        print("  [MAJOR]", m)

if len(blockers) == 0 and len(majors) == 0:
    with open(PROP_A, 'w', encoding='utf-8') as f:
        for p in proposals:
            f.write(json.dumps(p, ensure_ascii=False) + '\n')
    print(f"Successfully written {len(proposals)} lines to {PROP_A}")

    result_data = {
        "campaign_id": "side_stories_part2_editorial_20261025_r01",
        "partition": "Partition A",
        "scenes": sorted(list(set(it["scene_id"] for it in items))),
        "total_lines": len(proposals),
        "token_parity_percent": 100.0,
        "control_bytes_preserved": len(KEEP_EN_IDS),
        "banned_calques_count": 0,
        "status": "COMPLETED",
        "qa_ready": True
    }
    with open(RESULT_A, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    print(f"Successfully written {RESULT_A}")
else:
    print("Fixes required before writing outputs!")
