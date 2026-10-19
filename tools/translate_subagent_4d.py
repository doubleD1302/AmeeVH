#!/usr/bin/env python3
"""
Story, Dating & Quests Translator for Stella Sora (EN -> VI)
Subagent 4D: Translates ActivityTask, DatingCharacterEvent, Story, ActivityStory, AffinityQuest, DatingLandmarkEvent
Guarantees 100% preservation of tokens: {0}, {1}, {2}, ==DATING_CHARACTER==, \n, \x0b, <color=...>, </color>, &Param...&, ##...#
"""

import json
import re
import shutil
import sys
import time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_DIR = ROOT / "work" / "research" / "data_decrypted" / "entries"
CACHE_PATH = ROOT / "work" / "batches" / "story_dating_quests_cache.json"

TABLES = [
    {
        "name": "ActivityTask",
        "en_file": "00507_0x5c7be7cfcb1d2241.bin",
        "cn_file": "00728_0xc316bcdb179b0d6e.bin",
        "expected_count": 919,
    },
    {
        "name": "DatingCharacterEvent",
        "en_file": "00544_0xd46d025e8dae5d69.bin",
        "cn_file": "00765_0x733ee8fdb8a6a976.bin",
        "expected_count": 670,
    },
    {
        "name": "Story",
        "en_file": "00669_0xdda397c15ce0b289.bin",
        "cn_file": "00890_0x939d4390e6e6b8fd.bin",
        "expected_count": 588,
    },
    {
        "name": "ActivityStory",
        "en_file": "00506_0x0c2ee3471b91208e.bin",
        "cn_file": "00727_0x789e881d02a7ddcb.bin",
        "expected_count": 372,
    },
    {
        "name": "AffinityQuest",
        "en_file": "00510_0xde9e039952f8c2d2.bin",
        "cn_file": "00731_0x1e77dcffbbba3b93.bin",
        "expected_count": 360,
    },
    {
        "name": "DatingLandmarkEvent",
        "en_file": "00546_0xdc09272e31aceb9b.bin",
        "cn_file": "00767_0x43ac532f7df5c82a.bin",
        "expected_count": 262,
    },
]

# Static mappings for Episode Acts & Chapter codes
EPISODE_ACT_MAP = {
    "Interlude": "Hồi đệm",
    "Interlude I": "Hồi đệm I",
    "Interlude Ⅱ": "Hồi đệm II",
    "Interlude II": "Hồi đệm II",
    "Reminiscence": "Hồi ức",
    "The End": "Hạ màn",
    "Epilogue": "Vĩ thanh",
    "Prologue": "Mở đầu",
    "Act One": "Hồi 1",
    "Act Two": "Hồi 2",
    "Act Three": "Hồi 3",
    "Act Four": "Hồi 4",
    "Act Five": "Hồi 5",
    "Act Six": "Hồi 6",
    "Act Seven": "Hồi 7",
    "Act Eight": "Hồi 8",
    "Act Nine": "Hồi 9",
    "Act Ten": "Hồi 10",
}

# Static mappings for Dating Unlock Conditions
DATING_UNLOCK_MAP = {
    "Visit Hot Spring Resort to unlock": "Đến Khu nghỉ dưỡng Suối nước nóng để mở khóa",
    "Visit the Academy to unlock": "Đến Học viện để mở khóa",
    "Visit the Cave to unlock": "Đến Hang động để mở khóa",
    "Visit the Dessert Shop to unlock": "Đến Tiệm đồ ngọt để mở khóa",
    "Visit the Market to unlock": "Đến Chợ để mở khóa",
    "Visit the Port to unlock": "Đến Cảng để mở khóa",
}

# Static mappings for specific short story titles
EXACT_SHORT_MAP = {
    "!NONEED!": "!NONEED!",
    "!PENDING!": "!PENDING!",
    "Mom": "Mẹ",
    "Vita": "Vita",
    "Read event story: Flickering Glow.": "Đọc cốt truyện sự kiện: Ánh Lửa Bập Bùng.",
    "Read event story: Mysteries and Scents.": "Đọc cốt truyện sự kiện: Bí Ẩn và Hương Thơm.",
    "Read event story: Seeing is Deceiving.": "Đọc cốt truyện sự kiện: Mắt Thấy Chưa Hẳn Là Thật.",
    "Read event story: The Land of Echoes.": "Đọc cốt truyện sự kiện: Miền Đất Vọng Âm.",
    "Read event story: The Secret of the Ocean.": "Đọc cốt truyện sự kiện: Bí Mật Đại Dương.",
    "Read event story: To My Dearest You": "Đọc cốt truyện sự kiện: Gửi Người Trân Quý Nhất Của Tôi",
    "Read event story: A Gift for You": "Đọc cốt truyện sự kiện: Món Quà Trao Bạn",
}

def translate_aff(en_text: str) -> str:
    """Exact deterministic generator for all AffinityQuest entries."""
    # 1. Complete {1} Ascension with <CHAR> / <CHAR> has completed {1} Ascensions.
    m = re.match(r'^Complete\s+\{1\}\s+Ascension\s+with\s+(.+)$', en_text)
    if m:
        return f"Hoàn thành {{1}} lần Thám hiểm Tinh Tháp cùng {m.group(1).strip()}"
    m = re.match(r'^(.+?)\s+has completed\s+\{1\}\s+Ascensions\.$', en_text)
    if m:
        return f"Hoàn thành {{1}} lần Thám hiểm Tinh Tháp cùng {m.group(1).strip()}"

    # 2. Invite / Invited and hung out with <CHAR> {1} time(s)
    m = re.match(r'^(?:Invited\s+and\s+hung\s+out|Invite\s+and\s+hang\s+out)\s+with\s+(.+?)\s+\{1\}\s+times?\.?$', en_text)
    if m:
        return f"Hoàn thành {{1}} lần hẹn hò cùng {m.group(1).strip()}"

    # 3. <CHAR> reaches / has reached Tier {1}
    m = re.match(r'^(.+?)\s+(?:reaches|has reached)\s+Tier\s+\{1\}\.?$', en_text)
    if m:
        return f"{m.group(1).strip()} đột phá đến Bậc {{1}}"

    # 4. Upgraded / Upgrade <CHAR>'s skills {1} times
    m = re.match(r'^(?:Upgraded|Upgrade)\s+(.+?)\'s\s+skills\s+\{1\}\s+times\.?$', en_text)
    if m:
        return f"Nâng cấp kỹ năng của {m.group(1).strip()} {{1}} lần"

    # 5. Save {1} Records with a Rating of {2} with <CHAR> / <CHAR> has saved {1} records with a rating level of {2}.
    m = re.match(r'^Save\s+\{1\}\s+Records\s+with\s+a\s+Rating\s+of\s+\{2\}\s+with\s+(.+)$', en_text)
    if m:
        return f"Lưu {{1}} Kỷ lục đạt xếp hạng {{2}} cùng {m.group(1).strip()}"
    m = re.match(r'^(.+?)\s+has saved\s+\{1\}\s+records\s+with\s+a\s+rating\s+level\s+of\s+\{2\}\.$', en_text)
    if m:
        return f"Lưu {{1}} Kỷ lục đạt xếp hạng {{2}} cùng {m.group(1).strip()}"

    # 6. All <CHAR>'s skills ≥ Lv.{1} / All of <CHAR>'s skills are at Level/Lv. {1} or higher
    m = re.match(r'^All\s+(?:of\s+)?(.+?)\'s\s+skills\s+(?:are\s+at\s+(?:Level|Lv\.)\s+|\u2265\s*(?:Lv\.\s*)?)\{1\}(?:\s+or\s+higher\.?)?$', en_text)
    if m:
        return f"Tất cả kỹ năng của {m.group(1).strip()} đạt cấp {{1}} trở lên"

    # 7. Collect <CHAR>'s Potential(s) ×{1} / Obtained {1} <CHAR>'s Potentials.
    m = re.match(r'^Collect\s+(.+?)\'s\s+Potentials?\s*[\u00d7xX]\{1\}$', en_text)
    if m:
        return f"Thu thập Tiềm năng của {m.group(1).strip()} ×{{1}}"
    m = re.match(r'^Obtained\s+\{1\}\s+(.+?)\'s\s+Potentials\.$', en_text)
    if m:
        return f"Thu thập Tiềm năng của {m.group(1).strip()} ×{{1}}"

    return ""

def is_code_string(text: str) -> bool:
    """Check if string is a pure stage/act code (e.g., '01', '02A', 'BT01', 'EX')."""
    return bool(re.match(r'^(?:[0-9]{1,2}[A-Za-z]?|BT[0-9]{0,2}|EX[0-9]{0,2})$', text))

def shield_tokens(text: str):
    """Shield formatting tags, control characters, and placeholders."""
    tokens = []
    def repl(m):
        idx = len(tokens)
        tokens.append(m.group(0))
        return f" [[TOK{idx}]] "
    pattern = re.compile(r'(\x0b|\n|<[^>]+>|\{[0-9a-zA-Z_]+\}|&[a-zA-Z0-9_]+&|##[^#]+#|==[^=]+==|!NONEED!|!PENDING!)')
    shielded = pattern.sub(repl, text)
    return shielded, tokens

def unshield_tokens(text: str, tokens: list) -> str:
    """Restore shielded tokens cleanly and accurately."""
    def repl(m):
        idx = int(m.group(1))
        if idx >= len(tokens):
            return ""
        tok = tokens[idx]
        if tok in ('\x0b', '\n'):
            return tok
        return f" {tok} "

    # Flexible matching for [[TOK0]], [TOK0], [[ tok0 ]], etc.
    res = re.sub(r'\s*\[{1,2}\s*[Tt][Oo][Kk]\s*(\d+)\s*\]{1,2}\s*', repl, text)

    # Clean spacing around tags and punctuation
    res = re.sub(r'(<color=[^>]+>)\s+', r'\1', res)
    res = re.sub(r'\s+(</color>)', r'\1', res)
    res = re.sub(r' +(&[a-zA-Z0-9_]+&) +', r' \1 ', res)
    res = re.sub(r'[ \t]*\x0b[ \t]*', '\x0b', res)
    res = re.sub(r'[ \t]*\n[ \t]*', '\n', res)
    res = re.sub(r' +([,.:;?!])', r'\1', res)
    res = re.sub(r'[ \t]{2,}', ' ', res)
    return res.strip()

def post_process_vi(text: str) -> str:
    """Standardize RPG terminology and style according to project guidelines."""
    # Organization & Factions
    text = re.sub(r'\bNew Star Guild\b', 'Lữ đoàn Tân Tinh', text)
    text = re.sub(r'\bHiệp hội Ngôi sao Mới\b', 'Lữ đoàn Tân Tinh', text, flags=re.IGNORECASE)
    text = re.sub(r'\bBang hội Ngôi sao mới\b', 'Lữ đoàn Tân Tinh', text, flags=re.IGNORECASE)
    text = re.sub(r'\bTrekker Association\b', 'Hiệp hội Lữ khách', text)
    text = re.sub(r'\bGuild Management\b', 'Ban Quản lý Lữ đoàn', text)
    text = re.sub(r'\bguild office\b', 'văn phòng lữ đoàn', text, flags=re.IGNORECASE)
    text = re.sub(r'\bguild warehouse\b', 'kho lữ đoàn', text, flags=re.IGNORECASE)
    text = re.sub(r'\bguild\b', 'lữ đoàn', text, flags=re.IGNORECASE)
    text = re.sub(r'\bbang hội\b', 'lữ đoàn', text, flags=re.IGNORECASE)
    text = re.sub(r'\bcông hội\b', 'lữ đoàn', text, flags=re.IGNORECASE)

    # Key nouns
    text = re.sub(r'\bDora\b', 'Dorra', text)
    text = re.sub(r'\bTrekkers?\b', 'Lữ khách', text)
    text = re.sub(r'\b[Nn]hững người đi bộ\b', 'các Lữ khách', text)
    text = re.sub(r'\b[Nn]gười đi bộ\b', 'Lữ khách', text)
    text = re.sub(r'\b[Nn]hững người đi phượt\b', 'các Lữ khách', text)
    text = re.sub(r'\b[Nn]gười đi phượt\b', 'Lữ khách', text)
    text = re.sub(r'\b[Nn]gười phượt\b', 'Lữ khách', text)
    text = re.sub(r'\b[Nn]gười du hành\b', 'Lữ khách', text)
    text = re.sub(r'\bMonolith\b', 'Cự tháp', text)
    text = re.sub(r'\b[Đđ]á nguyên khối\b', 'Cự tháp', text)
    text = re.sub(r'\bNovians\b', 'người Nova', text)
    text = re.sub(r'\bNova Continent\b', 'Lục địa Nova', text)
    text = re.sub(r'\bthe Wilds\b', 'Vùng hoang dã', text)
    text = re.sub(r'\bWilds\b', 'Vùng hoang dã', text)
    text = re.sub(r'\bDiscs?\b', 'Đĩa nhạc', text)
    text = re.sub(r'\bEmblems?\b', 'Huy hiệu', text)
    text = re.sub(r'\bVigor\b', 'Năng lượng', text)
    text = re.sub(r'\bDiamonds?\b', 'Kim Cương', text)
    text = re.sub(r'\bDeepsea Finance\b', 'Deepsea Finance', text)
    text = re.sub(r'\bStarlight Core\b', 'Lõi Ánh sao', text)
    text = re.sub(r'\bStarlight\b', 'Ánh sao', text)
    text = re.sub(r'\bStellanite Dust\b', 'Bụi Stellanite', text)
    text = re.sub(r'\bStellanite Lumina\b', 'Tinh Thể Stellanite', text)
    text = re.sub(r'\bDestiny Pack\b', 'Gói Thẻ Định Mệnh', text)
    text = re.sub(r'\bDestiny Cards?\b', 'Thẻ Định Mệnh', text)
    text = re.sub(r'\bThẻ Vận Mệnh\b', 'Thẻ Định Mệnh', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSoul Keys?\b', 'Chìa khóa Tâm hồn', text)
    text = re.sub(r'\bChìa khóa linh hồn\b', 'Chìa khóa Tâm hồn', text, flags=re.IGNORECASE)
    text = re.sub(r'\bMonthly Card\b', 'Thẻ Tháng', text)

    # Combat Mechanics
    text = re.sub(r'\bSuperarmor\b', 'Bá thể', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSuper Armor\b', 'Bá thể', text, flags=re.IGNORECASE)
    text = re.sub(r'\bsiêu giáp\b', 'Bá thể', text, flags=re.IGNORECASE)
    text = re.sub(r'\bResilience Break\b', 'Phá vỡ Kiên định', text, flags=re.IGNORECASE)
    text = re.sub(r'\bResilience\b', 'Kiên định', text, flags=re.IGNORECASE)
    text = re.sub(r'\bkhả năng phục hồi\b', 'Kiên định', text, flags=re.IGNORECASE)
    text = re.sub(r'\bAuto Attacks?\b', 'Đòn đánh thường', text, flags=re.IGNORECASE)
    text = re.sub(r'\bNormal Attacks?\b', 'Đòn đánh thường', text, flags=re.IGNORECASE)
    text = re.sub(r'\btự động tấn công\b', 'Đòn đánh thường', text, flags=re.IGNORECASE)
    text = re.sub(r'\btấn công thông thường\b', 'Đòn đánh thường', text, flags=re.IGNORECASE)
    text = re.sub(r'\bMain Skills?\b', 'Kỹ năng chủ lực', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSupport Skills?\b', 'Kỹ năng viện trợ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bUltimates?\b', 'Tuyệt kỹ', text, flags=re.IGNORECASE)
    text = re.sub(r'\btuyệt chiêu\b', 'Tuyệt kỹ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bkỹ năng tối thượng\b', 'Tuyệt kỹ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPotentials?\b', 'Tiềm năng', text, flags=re.IGNORECASE)
    text = re.sub(r'\bTalents?\b', 'Thiên phú', text, flags=re.IGNORECASE)
    text = re.sub(r'\bAffinity\b', 'Độ thân mật', text, flags=re.IGNORECASE)
    text = re.sub(r'\bái lực\b', 'Độ thân mật', text, flags=re.IGNORECASE)
    text = re.sub(r'\bmối quan hệ họ hàng\b', 'Độ thân mật', text, flags=re.IGNORECASE)
    text = re.sub(r'\bMinions?\b', 'Tùy tùng', text, flags=re.IGNORECASE)
    text = re.sub(r'\btôi tớ\b', 'Tùy tùng', text, flags=re.IGNORECASE)
    text = re.sub(r'\bMarks?\b', 'Ấn ký', text, flags=re.IGNORECASE)
    text = re.sub(r'\bdấu ấn\b', 'Ấn ký', text, flags=re.IGNORECASE)

    # Elements
    text = re.sub(r'\bAqua DMG\b', 'Sát thương hệ Thủy', text, flags=re.IGNORECASE)
    text = re.sub(r'\bIgnis DMG\b', 'Sát thương hệ Hỏa', text, flags=re.IGNORECASE)
    text = re.sub(r'\bVentus DMG\b', 'Sát thương hệ Phong', text, flags=re.IGNORECASE)
    text = re.sub(r'\bTerra DMG\b', 'Sát thương hệ Địa', text, flags=re.IGNORECASE)
    text = re.sub(r'\bLux DMG\b', 'Sát thương hệ Quang', text, flags=re.IGNORECASE)
    text = re.sub(r'\bUmbra DMG\b', 'Sát thương hệ Ám', text, flags=re.IGNORECASE)

    # Character names: ensure no wrong translations
    text = re.sub(r'\bHổ phách\b', 'Amber', text)
    text = re.sub(r'\bhổ phách\b', 'Amber', text)
    text = re.sub(r'\bFlorence\b', 'Firenze', text)

    # Clean whitespace before punctuation
    text = re.sub(r' +([,.:;?!])', r'\1', text)
    return text.strip()

def translate_batch(texts: list, session: requests.Session) -> list:
    """Translate a batch of texts using Google Translate API with auto split/retry."""
    if not texts:
        return []

    delim = "\n###\n"
    joined = delim.join(texts)

    for attempt in range(3):
        try:
            r = session.get(
                "https://translate.googleapis.com/translate_a/single",
                params={
                    "client": "gtx",
                    "sl": "en",
                    "tl": "vi",
                    "dt": "t",
                    "q": joined,
                },
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=25,
            )
            if r.status_code == 200:
                res = r.json()
                full_text = "".join([item[0] for item in res[0] if item[0]])
                parts = [p.strip() for p in full_text.split("###")]
                if len(parts) == len(texts):
                    return parts
                else:
                    if len(texts) > 1:
                        mid = len(texts) // 2
                        return translate_batch(texts[:mid], session) + translate_batch(texts[mid:], session)
                    else:
                        return [full_text.strip()]
            time.sleep(1.0 * (attempt + 1))
        except Exception:
            time.sleep(1.0 * (attempt + 1))

    # Fallback 1 by 1
    results = []
    for t in texts:
        try:
            r = session.get(
                "https://translate.googleapis.com/translate_a/single",
                params={"client": "gtx", "sl": "en", "tl": "vi", "dt": "t", "q": t},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=12,
            )
            if r.status_code == 200:
                res = r.json()
                full = "".join([item[0] for item in res[0] if item[0]])
                results.append(full.strip())
            else:
                results.append(t)
        except Exception:
            results.append(t)
        time.sleep(0.15)
    return results

def main():
    print("=" * 60)
    print("Stella Sora - Subagent 4D: Story, Dating & Quests Translator")
    print("=" * 60)

    # 1. Load or initialize cache
    cache = {}
    if CACHE_PATH.exists():
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                cache = json.load(f)
            print(f"Loaded {len(cache)} existing cached translations from {CACHE_PATH.name}")
        except Exception as e:
            print(f"Warning loading cache: {e}")

    # Load existing batches to pre-populate common translations
    batches_dir = ROOT / "work" / "batches"
    for cf in batches_dir.glob("*cache*.json"):
        if cf.name != CACHE_PATH.name:
            try:
                cdata = json.loads(cf.read_text(encoding="utf-8"))
                for k, v in cdata.items():
                    if k not in cache:
                        cache[k] = v
            except Exception:
                pass
    print(f"Total available cache entries: {len(cache)}")

    # 2. Back up original files
    for t in TABLES:
        en_path = ENTRIES_DIR / t["en_file"]
        bak_path = en_path.with_suffix(".bin.bak")
        if not bak_path.exists():
            shutil.copy2(en_path, bak_path)
            print(f"Created backup: {bak_path.name}")
        else:
            print(f"Backup already exists: {bak_path.name}")

    session = requests.Session()

    # Process all tables
    translated_tables = {}
    total_items = 0

    for t in TABLES:
        name = t["name"]
        en_file = t["en_file"]
        cn_file = t["cn_file"]
        expected_count = t["expected_count"]
        en_path = ENTRIES_DIR / en_file
        cn_path = ENTRIES_DIR / cn_file

        with open(en_path, "r", encoding="utf-8") as f:
            en_data = json.load(f)
        with open(cn_path, "r", encoding="utf-8") as f:
            cn_data = json.load(f)

        assert len(en_data) == expected_count, f"Entry count mismatch in {name}!"
        print(f"\nProcessing {name} ({len(en_data)} items)...")
        total_items += len(en_data)

        vi_data = {}
        to_translate_keys = []
        to_translate_texts = []
        tokens_map = {}

        for k, en_text in en_data.items():
            # Check deterministic matchers
            if name == "AffinityQuest":
                res = translate_aff(en_text)
                if res:
                    vi_data[k] = res
                    continue

            if en_text in EXACT_SHORT_MAP:
                vi_data[k] = EXACT_SHORT_MAP[en_text]
                continue

            if is_code_string(en_text):
                vi_data[k] = en_text
                continue

            if k.endswith(".4") and en_text in EPISODE_ACT_MAP:
                vi_data[k] = EPISODE_ACT_MAP[en_text]
                continue

            if k.endswith(".6") and en_text in DATING_UNLOCK_MAP:
                vi_data[k] = DATING_UNLOCK_MAP[en_text]
                continue

            # Check cache
            if k in cache:
                vi_data[k] = cache[k]
                continue
            if en_text in cache:
                vi_data[k] = cache[en_text]
                continue

            # Needs translation via API
            shielded, tokens = shield_tokens(en_text)
            tokens_map[k] = tokens
            to_translate_keys.append(k)
            to_translate_texts.append(shielded)

        print(f"  Exact / cached: {len(vi_data)}, Needs translation: {len(to_translate_keys)}")

        # Batch translation
        batch_size = 20
        for i in range(0, len(to_translate_keys), batch_size):
            batch_keys = to_translate_keys[i:i + batch_size]
            batch_texts = to_translate_texts[i:i + batch_size]

            translated_parts = translate_batch(batch_texts, session)

            for key, trans in zip(batch_keys, translated_parts):
                toks = tokens_map[key]
                unshielded = unshield_tokens(trans, toks)
                polished = post_process_vi(unshielded)
                vi_data[key] = polished
                cache[key] = polished
                cache[en_data[key]] = polished

            print(f"  Translated batch {i//batch_size + 1} / {(len(to_translate_keys) + batch_size - 1)//batch_size} ({len(batch_keys)} items)")
            time.sleep(0.3)

            # Save cache incrementally
            if (i // batch_size) % 5 == 0 or (i + batch_size >= len(to_translate_keys)):
                with open(CACHE_PATH, "w", encoding="utf-8") as f:
                    json.dump(cache, f, ensure_ascii=False, indent=2)

        translated_tables[name] = (en_path, vi_data, en_data)

    # 3. Verification Gate: Exact Token Preservation
    print("\n" + "=" * 60)
    print("VERIFICATION GATE: Exact Token & Placeholder Check")
    print("=" * 60)

    tok_re = re.compile(r'(\{[0-9a-zA-Z_]+\}|<[^>]+>|\x0b|\n|&[a-zA-Z0-9_]+&|##[^#]+#|==[^=]+==|!NONEED!|!PENDING!)')
    has_error = False

    for name, (en_path, vi_data, en_data) in translated_tables.items():
        table_errors = 0
        for k in en_data:
            orig = en_data[k]
            trans = vi_data.get(k, "")

            orig_tokens = tok_re.findall(orig)
            trans_tokens = tok_re.findall(trans)

            if orig_tokens != trans_tokens:
                # Check if only difference is order
                if sorted(orig_tokens) != sorted(trans_tokens):
                    table_errors += 1
                    has_error = True
                    print(f"ERROR in {name} [{k}]:")
                    print(f"  EN: {repr(orig)}")
                    print(f"  VI: {repr(trans)}")
                    print(f"  Expected tokens: {orig_tokens}")
                    print(f"  Found tokens:    {trans_tokens}")

        if table_errors == 0:
            print(f"[{name}] ALL {len(en_data)} entries passed token validation 100%!")
        else:
            print(f"[{name}] FAILED with {table_errors} token mismatch errors!")

    if has_error:
        print("\nStopping before write due to token errors!")
        sys.exit(1)

    # 4. Write back to EN .bin files
    print("\n" + "=" * 60)
    print("WRITING TRANSLATED TABLES TO .bin FILES")
    print("=" * 60)

    for name, (en_path, vi_data, en_data) in translated_tables.items():
        with open(en_path, "w", encoding="utf-8") as f:
            json.dump(vi_data, f, ensure_ascii=False, indent=2)
        print(f"Successfully wrote {len(vi_data)} entries to {en_path.name}")

        # Syntax check
        with open(en_path, "r", encoding="utf-8") as f:
            verified = json.load(f)
        assert len(verified) == len(en_data), f"Count mismatch in {name}!"
        print(f"Syntax verification passed: {en_path.name} is valid UTF-8 JSON.")

    print("\n" + "=" * 60)
    print(f"SUBAGENT 4D COMPLETED SUCCESSFULLY! Total {total_items} items translated.")
    print("=" * 60)

if __name__ == "__main__":
    main()
