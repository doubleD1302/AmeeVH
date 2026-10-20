import json
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
data = json.loads((ROOT / "work" / "batches" / "audit_batch1_dating_char.json").read_text(encoding="utf-8"))

print(f"Total items: {len(data)}")

# 1. Check for pure English
pure_en = []
for d in data:
    txt = d["current_vi"].strip()
    # If text is longer than 5 chars and has no Vietnamese accented characters
    if len(txt) > 5 and not re.search(r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]", txt, re.IGNORECASE):
        # Ignore purely numbers or tokens or Latin names that should be Latin
        if not re.match(r"^[0-9\s\.,\-\/]+$", txt) and len(txt.split()) > 2:
            pure_en.append(d)

print(f"Pure English / untranslated items: {len(pure_en)}")
for d in pure_en[:5]:
    print(f"  [{d['table']}][{d['key']}] EN: {d['en']} | VI: {d['current_vi']}")

# 2. Check forbidden glossary terms
forbidden = [
    ("Hổ phách", "Amber"),
    ("Sao nhổ", "Đoạt Sao"),
    ("Cuộc chinh phục sao nhổ", "Chinh Phục Đoạt Sao"),
    ("mất khả năng lao động", "bị tê liệt / không thể hành động"),
    ("bị gây ra bởi", "kích hoạt từ / gây ra bởi"),
    ("thời gian hồi phục", "thời gian hồi chiêu"),
    ("Sơ Quang", "Khải Minh"),
    ("Kỵ Sĩ Hoàng Gia", "Cận Vệ Hoàng Gia"),
    ("Vệ binh Hoàng gia", "Cận Vệ Hoàng Gia"),
    ("Bạn có sao chép", "Nghe rõ không!?"),
    ("sao chép không", "nghe rõ không!?"),
    ("Hội Ngôi sao mới", "Lữ Đoàn Tân Tinh"),
    ("Lữ đoàn Blank", "Lữ Đoàn Tân Tinh"),
    ("Đá Linh Hồn", "Hồn Thạch"),
    ("Trại Mồ Côi Daisy", "Mái Ấm Hoa Cúc"),
    ("Bà Angie", "Tiểu Thư Angie"),
    ("Hiệu Trưởng Allie", "Giám Đốc Allie"),
]

for term, suggestion in forbidden:
    matches = [d for d in data if re.search(r"\b" + re.escape(term) + r"\b", d["current_vi"], re.IGNORECASE)]
    if matches:
        print(f"Forbidden term: '{term}' ({len(matches)} occurrences) -> suggest '{suggestion}'")
        for m in matches[:2]:
            print(f"    [{m['key']}] {m['current_vi'][:120]}")

# 3. Check MT markers
mt_markers = [
    r"\bcủa bạn\b",
    r"\bcủa tôi\b",
    r"\bcủa mình\b",
    r"\bcủa cô ấy\b",
    r"\bcô ấy\b",
    r"\banh ấy\b",
    r"\btrong khi\b",
    r"\bở một mức độ\b",
    r"\bkhông thể không\b",
    r"\bmột cách\b",
    r"\bbắt đầu\b",
    r"\bđược coi là\b",
    r"\bvề cơ bản\b",
    r"\bchắc chắn là\b",
    r"\btrở nên\b",
    r"\bcó thể thấy\b",
    r"\bđiều này làm cho\b",
    r"\bđiều đó làm cho\b",
    r"\bkhiến bạn\b",
    r"\bnhìn vào\b",
    r"\blắng nghe\b",
    r"\bthực hiện một\b",
    r"\btiến hành\b",
]

print("\n=== MT MARKERS SUMMARY ===")
for p in mt_markers:
    matches = [d for d in data if re.search(p, d["current_vi"], re.IGNORECASE)]
    print(f"Pattern '{p}': {len(matches)} matches")
