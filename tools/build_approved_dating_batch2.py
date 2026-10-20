import json
import re
import sys
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "work" / "batches"))

from part1_untrans_char import PART1_UNTRANS_CHAR
from part2_untrans_landmarks import PART2_UNTRANS_LANDMARKS

BATCH2_PATH = ROOT / "work" / "batches" / "dialogue_batch2_dating_events.json"
APPROVED_PATH = ROOT / "work" / "batches" / "dialogue_batch2_dating_approved.json"

data = json.loads(BATCH2_PATH.read_text(encoding="utf-8"))
print(f"Total entries in Batch 2: {len(data)}")

# Phrasing polish rules for existing translated items
STIFF_REPLACEMENTS = [
    (r"\bsự kiện xổ số\b", "chương trình rút thăm may mắn"),
    (r"\bcửa hàng tráng miệng\b", "tiệm đồ ngọt"),
    (r"\bHiệp sĩ Vệ binh Hoàng gia\b", "Cận Vệ Hoàng Gia"),
    (r"\bVệ binh Hoàng gia\b", "Cận Vệ Hoàng Gia"),
    (r"\bcó tư tưởng công lý\b", "tôn sùng chính nghĩa"),
    (r"\bngười đàn ông có vẻ ngoài lén lút\b", "gã đàn ông dáng vẻ lấm lét"),
    (r"\bbước đi nhanh nhẹn\b", "thoăn thoắt bước đi"),
    (r"\bsuýt khiến bạn mất thăng bằng\b", "suýt chút nữa làm bạn ngã nhào"),
    (r"\blãng phí thời gian của tôi\b", "lãng phí thời gian quý báu"),
    (r"\bkết nạp vào đội của bạn\b", "kết nạp vào đội ngũ"),
    (r"\bđội của bạn\b", "đội ngũ"),
    (r"\bngạc nhiên trước sự lựa chọn của bạn\b", "tròn mắt ngạc nhiên trước lựa chọn của bạn"),
    (r"\btrong khi khám phá hang động với Kasimira\b", "trong chuyến thám hiểm hang động cùng Kasimira"),
    (r"\bcô ấy đã hộ tống bạn một cách an toàn\b", "cô ấy đã cẩn thận hộ tống bạn sang bờ bên kia an toàn"),
    (r"\bkhông thể không cảm thấy\b", "bất giác cảm thấy"),
    (r"\bở một mức độ nào đó\b", "phần nào đó"),
    (r"\bFirstlight Noya\b", "Noya - Khải Minh"),
    (r"\bNoya Sơ Quang\b", "Noya - Khải Minh"),
    (r"\bSơ Quang\b", "Khải Minh"),
    (r"\bhoa hồng\b", "nhiệm vụ ủy thác"),
    (r"\bdanh sách giặt ủi\b", "danh sách dài dằng dặc"),
    (r"\bmã thông báo\b", "tín vật"),
    (r"\bnốt ruồi\b", "tai mắt"),
]

def polish_existing_vi(text: str) -> str:
    res = text
    for pat, rep in STIFF_REPLACEMENTS:
        res = re.sub(pat, rep, res, flags=re.IGNORECASE)
    return res

approved_list = []
untrans_fixed = 0
stiff_polished = 0

for item in data:
    k = item["key"]
    orig_en = item["en"]
    cur_vi = item["current_vi"]
    
    # 1. Check if in Part 1 (Untranslated Character Events)
    if k in PART1_UNTRANS_CHAR:
        new_vi = PART1_UNTRANS_CHAR[k]
        untrans_fixed += 1
        reason = "Việt hóa mới sự kiện hẹn hò nhân vật ngọt ngào, hóm hỉnh chuẩn anime"
    # 2. Check if in Part 2 (Untranslated Landmark Events)
    elif k in PART2_UNTRANS_LANDMARKS:
        new_vi = PART2_UNTRANS_LANDMARKS[k]
        untrans_fixed += 1
        reason = "Việt hóa mới tương tác hẹn hò tại các địa danh lãng mạn"
    # 3. Existing translation -> polish stiff phrases
    else:
        new_vi = polish_existing_vi(cur_vi)
        if new_vi != cur_vi:
            stiff_polished += 1
            reason = "Trau chuốt văn phong hẹn hò thuần Việt, tự nhiên, duyên dáng"
        else:
            reason = "Giữ nguyên bản dịch hẹn hò đã đạt chuẩn"
            
    # Verify token preservation
    en_tokens = re.findall(r"==[A-Z0-9_]+==|\{[0-9]+\}", orig_en)
    vi_tokens = re.findall(r"==[A-Z0-9_]+==|\{[0-9]+\}", new_vi)
    if en_tokens != vi_tokens:
        print(f"Warning: Token mismatch in {k}: EN={en_tokens} vs VI={vi_tokens}")
        
    approved_list.append({
        "table": item["table"],
        "file": item["file"],
        "key": k,
        "en": orig_en,
        "cn": item.get("cn", ""),
        "current_vi": cur_vi,
        "vi": new_vi,
        "reason": reason,
        "agent": "Dating Dialogue Specialist Subagent"
    })

print(f"Summary: Untranslated fixed = {untrans_fixed}, Stiff polished = {stiff_polished}")
print(f"Total approved items: {len(approved_list)}")

APPROVED_PATH.write_text(json.dumps(approved_list, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Saved {APPROVED_PATH.name} ({APPROVED_PATH.stat().st_size:,} bytes)")
