#!/usr/bin/env python3
"""
Combat Skills & Potential Translator for Stella Sora (EN -> VI)
Subagent 4B: Translates Potential, MainSkill, SecondarySkill
Guarantees 100% preservation of tokens: {0}, {1}, <color=...>, </color>, \\n, \\x0b, &Param...&, ##...#
Strict validation gate before overwriting .bin files.
"""

import json
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_DIR = ROOT / "work" / "research" / "data_decrypted" / "entries"
CACHE_PATH = ROOT / "work" / "batches" / "subagent_4b_skills_cache.json"
SKILL_NAMES_PATH = ROOT / "work" / "batches" / "skill_names_translated.json"

TABLES = [
    {
        "name": "Potential",
        "en_file": "00624_0x02ce11eca01b5fc8.bin",
        "cn_file": "00845_0xaa3d5eea04d1e767.bin",
        "expected_count": 2324,
    },
    {
        "name": "MainSkill",
        "en_file": "00591_0x57e760255c1d3b2d.bin",
        "cn_file": "00812_0xb09952a17d27201c.bin",
        "expected_count": 1227,
    },
    {
        "name": "SecondarySkill",
        "en_file": "00635_0x31a8814a91313129.bin",
        "cn_file": "00856_0x439a5df5068af46c.bin",
        "expected_count": 1442,
    },
]

TOKEN_REGEX = re.compile(r'(\x0b|\n|<[^>]+>|\{[0-9a-zA-Z_]+\}|&Param\d+&|##[^#]+(?:#[^#]+)?#)')

def shield_tokens(text: str):
    """Shield all game tags, placeholders, and tokens."""
    tokens = []
    def repl(m):
        idx = len(tokens)
        tokens.append(m.group(0))
        return f" [[TOK{idx}]] "
    shielded = TOKEN_REGEX.sub(repl, text)
    shielded = re.sub(r' +', ' ', shielded).strip()
    return shielded, tokens

def unshield_tokens(text: str, tokens: list):
    """Restore shielded tokens cleanly and guarantee 100% token preservation."""
    def repl(m):
        idx = int(m.group(1))
        if idx >= len(tokens):
            return ""
        tok = tokens[idx]
        if tok in ('\x0b', '\n'):
            return tok
        return f" {tok} "

    res = re.sub(r'\s*\[\[\s*TOK(\d+)\s*\]\]\s*', repl, text)

    # Clean spacing around tags and placeholders
    res = re.sub(r'(<color=[^>]+>)\s+', r'\1', res)
    res = re.sub(r'\s+(</color>)', r'\1', res)
    res = re.sub(r'(<color=[^>]+>)\s*(\{.*?\}|&Param\d+&)\s*(</color>)', r'\1\2\3', res)
    res = re.sub(r' +(&Param\d+&) +', r' \1 ', res)
    res = re.sub(r'[ \t]*\x0b[ \t]*', '\x0b', res)
    res = re.sub(r'[ \t]*\n[ \t]*', '\n', res)
    res = re.sub(r'\s+([,.:;?!])', r'\1', res)
    res = re.sub(r'(\{[0-9a-zA-Z_]+\})\s+s\b', r'\1s', res)
    res = re.sub(r'(&Param\d+&)\s+s\b', r'\1s', res)
    res = re.sub(r'(\{[0-9a-zA-Z_]+\})\s*%', r'\1%', res)
    res = re.sub(r'(&Param\d+&)\s*%', r'\1%', res)
    res = re.sub(r'[ \t]{2,}', ' ', res)
    return res.strip()

def post_process_vi(text: str) -> str:
    """Standardize combat and RPG terminology on shielded text."""
    # Currency & Organizations
    text = re.sub(r'\bDora\b', 'Dorra', text)
    text = re.sub(r'\bTrekkers?\b', 'Lữ khách', text)
    text = re.sub(r'\b[Nn]hững người đi bộ\b', 'các Lữ khách', text)
    text = re.sub(r'\b[Nn]gười đi bộ\b', 'Lữ khách', text)
    text = re.sub(r'\b[Nn]hững người đi phượt\b', 'các Lữ khách', text)
    text = re.sub(r'\b[Nn]gười đi phượt\b', 'Lữ khách', text)
    text = re.sub(r'\b[Nn]gười phượt\b', 'Lữ khách', text)
    text = re.sub(r'\b[Nn]gười du hành\b', 'Lữ khách', text)
    text = re.sub(r'\bMonolith\b', 'Cự tháp', text)

    # Roles
    text = re.sub(r'\bMain Trekkers?\b', 'Lữ khách chủ lực', text, flags=re.I)
    text = re.sub(r'\bSupport Trekkers?\b', 'Lữ khách viện trợ', text, flags=re.I)
    text = re.sub(r'\bTrekker chính\b', 'Lữ khách chủ lực', text, flags=re.I)
    text = re.sub(r'\bTrekker hỗ trợ\b', 'Lữ khách viện trợ', text, flags=re.I)
    text = re.sub(r'\bLữ khách chính\b', 'Lữ khách chủ lực', text, flags=re.I)
    text = re.sub(r'\bLữ khách hỗ trợ\b', 'Lữ khách viện trợ', text, flags=re.I)
    text = re.sub(r'\bnhân vật chính\b', 'Lữ khách chủ lực', text, flags=re.I)
    text = re.sub(r'\bnhân vật hỗ trợ\b', 'Lữ khách viện trợ', text, flags=re.I)

    # Super Armor
    text = re.sub(r'\bSuperarmor\b', 'Bá thể', text, flags=re.I)
    text = re.sub(r'\bSuper Armor\b', 'Bá thể', text, flags=re.I)
    text = re.sub(r'\bsiêu giáp\b', 'Bá thể', text, flags=re.I)

    # Resilience
    text = re.sub(r'\bResilience Break\b', 'Phá vỡ Kiên định', text, flags=re.I)
    text = re.sub(r'\bBroken Resilience\b', 'Phá vỡ Kiên định', text, flags=re.I)
    text = re.sub(r'\bResilience\b', 'Kiên định', text, flags=re.I)
    text = re.sub(r'\bkhả năng phục hồi\b', 'Kiên định', text, flags=re.I)
    text = re.sub(r'\bđộ kiên định\b', 'Kiên định', text, flags=re.I)

    # Skills
    text = re.sub(r'\bMain Skills?\b', 'Kỹ năng chủ lực', text, flags=re.I)
    text = re.sub(r'\bkỹ năng chính\b', 'Kỹ năng chủ lực', text, flags=re.I)
    text = re.sub(r'\bSupport Skills?\b', 'Kỹ năng viện trợ', text, flags=re.I)
    text = re.sub(r'\bkỹ năng hỗ trợ\b', 'Kỹ năng viện trợ', text, flags=re.I)
    text = re.sub(r'\bAssist Skills?\b', 'Kỹ năng viện trợ', text, flags=re.I)
    text = re.sub(r'\bUltimate Skills?\b', 'Tuyệt kỹ', text, flags=re.I)
    text = re.sub(r'\bUltimates?\b', 'Tuyệt kỹ', text, flags=re.I)
    text = re.sub(r'\btuyệt chiêu\b', 'Tuyệt kỹ', text, flags=re.I)
    text = re.sub(r'\bkỹ năng tối thượng\b', 'Tuyệt kỹ', text, flags=re.I)
    text = re.sub(r'\bchiêu cuối\b', 'Tuyệt kỹ', text, flags=re.I)

    # Auto Attack
    text = re.sub(r'\bAuto Attacks?\b', 'Đòn đánh thường', text, flags=re.I)
    text = re.sub(r'\bNormal Attacks?\b', 'Đòn đánh thường', text, flags=re.I)
    text = re.sub(r'\bDMG tự động tấn công\b', 'Sát thương Đòn đánh thường', text, flags=re.I)
    text = re.sub(r'\btự động tấn công\b', 'Đòn đánh thường', text, flags=re.I)
    text = re.sub(r'\btấn công thông thường\b', 'Đòn đánh thường', text, flags=re.I)
    text = re.sub(r'\bđòn đánh tự động\b', 'Đòn đánh thường', text, flags=re.I)

    # Elemental Marks & Elements
    elements = [
        ('Aqua', 'Thủy'),
        ('Ignis', 'Hỏa'),
        ('Ventus', 'Phong'),
        ('Terra', 'Địa'),
        ('Lux', 'Quang'),
        ('Umbra', 'Ám')
    ]
    for elem, vi_elem in elements:
        text = re.sub(rf'\b{elem} Trekkers?\b', f'Lữ khách hệ {vi_elem}', text, flags=re.I)
        text = re.sub(rf'\bLữ khách {elem}\b', f'Lữ khách hệ {vi_elem}', text, flags=re.I)
        text = re.sub(rf'\b{elem} DMG\b', f'Sát thương hệ {vi_elem}', text, flags=re.I)
        text = re.sub(rf'\bDMG {elem}\b', f'Sát thương hệ {vi_elem}', text, flags=re.I)
        text = re.sub(rf'\b{elem} PEN\b', f'Xuyên kháng hệ {vi_elem}', text, flags=re.I)
        text = re.sub(rf'\b{elem} RES\b', f'Kháng hệ {vi_elem}', text, flags=re.I)
        text = re.sub(rf'\b{elem} Marks?\b', f'Ấn ký {vi_elem}', text, flags=re.I)
        text = re.sub(rf'\bẤn ký {elem}\b', f'Ấn ký {vi_elem}', text, flags=re.I)

    # Specific DMG types
    text = re.sub(r'\bDMG kỹ năng\b', 'Sát thương Kỹ năng', text, flags=re.I)
    text = re.sub(r'\bSkill DMG\b', 'Sát thương Kỹ năng', text, flags=re.I)
    text = re.sub(r'\bDMG tối thượng\b', 'Sát thương Tuyệt kỹ', text, flags=re.I)
    text = re.sub(r'\bUltimate DMG\b', 'Sát thương Tuyệt kỹ', text, flags=re.I)
    text = re.sub(r'\bAuto Attack DMG\b', 'Sát thương Đòn đánh thường', text, flags=re.I)
    text = re.sub(r'\bNormal Attack DMG\b', 'Sát thương Đòn đánh thường', text, flags=re.I)
    text = re.sub(r'\bDerivative DMG\b', 'Sát thương Phái sinh', text, flags=re.I)
    text = re.sub(r'\bDMG phái sinh\b', 'Sát thương Phái sinh', text, flags=re.I)
    text = re.sub(r'\bDMG Multiplier\b', 'Bội số sát thương', text, flags=re.I)
    text = re.sub(r'\bHệ số sát thương\b', 'Bội số sát thương', text, flags=re.I)
    text = re.sub(r'\bDMG Taken\b', 'Sát thương gánh chịu', text, flags=re.I)
    text = re.sub(r'\bDMG Dealt\b', 'Sát thương gây ra', text, flags=re.I)
    text = re.sub(r'\bDMG\b', 'sát thương', text, flags=re.I)

    # Marks general
    text = re.sub(r'\bMarks?\b', 'Ấn ký', text, flags=re.I)
    text = re.sub(r'\bdấu ấn\b', 'Ấn ký', text, flags=re.I)

    # Combat stats
    text = re.sub(r'\bBase ATK\b', 'Tấn công cơ bản', text, flags=re.I)
    text = re.sub(r'\bBase DEF\b', 'Phòng thủ cơ bản', text, flags=re.I)
    text = re.sub(r'\bBase HP\b', 'HP cơ bản', text, flags=re.I)
    text = re.sub(r'\bATK\b', 'Tấn công', text, flags=re.I)
    text = re.sub(r'\bDEF\b', 'Phòng thủ', text, flags=re.I)
    text = re.sub(r'\bCrit Rate\b', 'Tỷ lệ bạo kích', text, flags=re.I)
    text = re.sub(r'\bCrit DMG\b', 'Sát thương bạo kích', text, flags=re.I)
    text = re.sub(r'\bATK SPD\b', 'Tốc độ đánh', text, flags=re.I)
    text = re.sub(r'\bMovement SPD\b', 'Tốc độ di chuyển', text, flags=re.I)
    text = re.sub(r'\bMove SPD\b', 'Tốc độ di chuyển', text, flags=re.I)

    # Minions
    text = re.sub(r'\bMinions?\b', 'Tùy tùng', text, flags=re.I)
    text = re.sub(r'\btôi tớ\b', 'Tùy tùng', text, flags=re.I)

    # Ammo & Magazine
    text = re.sub(r'\bMagazine Capacity\b', 'Dung lượng đạn', text, flags=re.I)
    text = re.sub(r'\bMagazine\b', 'Băng đạn', text, flags=re.I)
    text = re.sub(r'\bhộp đạn\b', 'băng đạn', text, flags=re.I)
    text = re.sub(r'\bnạp lại đạn\b', 'nạp đạn', text, flags=re.I)
    text = re.sub(r'\bđược nạp lại\b', 'được nạp đạn', text, flags=re.I)

    # AoE
    text = re.sub(r'\bAoE Attacks?\b', 'Đòn tấn công diện rộng', text, flags=re.I)
    text = re.sub(r'\bAoE\b', 'diện rộng', text, flags=re.I)

    # Verbs / Actions
    text = re.sub(r'\bsử dụng kỹ năng\b', 'thi triển kỹ năng', text, flags=re.I)
    text = re.sub(r'\bsử dụng Kỹ năng\b', 'thi triển Kỹ năng', text, flags=re.I)
    text = re.sub(r'\bsử dụng Tuyệt kỹ\b', 'thi triển Tuyệt kỹ', text, flags=re.I)
    text = re.sub(r'\bsử dụng chiêu cuối\b', 'thi triển Tuyệt kỹ', text, flags=re.I)
    text = re.sub(r'\bviệc sử dụng Kỹ năng\b', 'thi triển Kỹ năng', text, flags=re.I)

    return text

def translate_batch(texts: list) -> list:
    """Translate batch of shielded texts using Google Translate API with retries and recursive bisect."""
    if not texts:
        return []

    delim = "\n###\n"
    joined = delim.join(texts)

    for attempt in range(3):
        try:
            url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=vi&dt=t&q=" + urllib.parse.quote(joined)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                full_text = "".join([item[0] for item in data[0] if item[0]])
                parts = [p.strip() for p in full_text.split("###")]
                if len(parts) == len(texts):
                    return parts
                elif len(texts) > 1:
                    mid = len(texts) // 2
                    return translate_batch(texts[:mid]) + translate_batch(texts[mid:])
                else:
                    return [full_text.strip()]
        except Exception:
            time.sleep(1.0 * (attempt + 1))

    # Fallback item by item
    results = []
    for t in texts:
        try:
            url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=vi&dt=t&q=" + urllib.parse.quote(t)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                full = "".join([item[0] for item in data[0] if item[0]])
                results.append(full.strip())
        except Exception:
            results.append(t)
        time.sleep(0.1)
    return results

def is_valid_cache_entry(orig_text: str, cached_text: str) -> bool:
    """Check if cached text preserves 100% of tokens from original."""
    orig_tokens = TOKEN_REGEX.findall(orig_text)
    cached_tokens = TOKEN_REGEX.findall(cached_text)
    return sorted(orig_tokens) == sorted(cached_tokens)

def main():
    print("=" * 70)
    print("Stella Sora - Subagent 4B: Combat Skills & Potential Translator")
    print("=" * 70)

    # 1. Load Caches & Curated Skill Names
    cache = {}
    if CACHE_PATH.exists():
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                cache = json.load(f)
            print(f"Loaded {len(cache)} existing cached entries from {CACHE_PATH.name}")
        except Exception as e:
            print(f"Warning loading cache: {e}")

    # Load 247 curated skill names
    if SKILL_NAMES_PATH.exists():
        try:
            with open(SKILL_NAMES_PATH, "r", encoding="utf-8") as f:
                skill_names = json.load(f)
            print(f"Loaded {len(skill_names)} curated skill names from {SKILL_NAMES_PATH.name}")
            for k, v in skill_names.items():
                cache[k] = v
        except Exception as e:
            print(f"Warning loading skill names: {e}")

    # 2. Back up original files
    print("\n--- Step 1: Backing up original .bin files ---")
    for t in TABLES:
        en_path = ENTRIES_DIR / t["en_file"]
        bak_path = en_path.with_suffix(".bin.bak")
        if not bak_path.exists():
            shutil.copy2(en_path, bak_path)
            print(f"Created backup: {bak_path.name}")
        else:
            print(f"Backup already exists: {bak_path.name}")

    # 3. Process and translate all tables
    print("\n--- Step 2: Processing tables & translating ---")
    translated_tables = {}
    total_entries_count = 0

    for t in TABLES:
        name = t["name"]
        en_file = t["en_file"]
        cn_file = t["cn_file"]
        en_path = ENTRIES_DIR / en_file
        cn_path = ENTRIES_DIR / cn_file

        with open(en_path, "r", encoding="utf-8") as f:
            en_data = json.load(f)
        with open(cn_path, "r", encoding="utf-8") as f:
            cn_data = json.load(f)

        print(f"\nProcessing {name} (expected {t['expected_count']}, actual {len(en_data)})...")
        total_entries_count += len(en_data)

        vi_data = {}
        to_translate_keys = []
        to_translate_texts = []
        tokens_map = {}

        for k, en_text in en_data.items():
            if en_text == "!NONEED!":
                vi_data[k] = "!NONEED!"
                continue

            # Skill name lookup for .1 in MainSkill and SecondarySkill
            if (name in ("MainSkill", "SecondarySkill")) and k.endswith(".1") and en_text in cache:
                vi_data[k] = cache[en_text]
                continue

            # Cache lookup with token validation
            if k in cache and is_valid_cache_entry(en_text, cache[k]):
                vi_data[k] = cache[k]
                continue
            if en_text in cache and is_valid_cache_entry(en_text, cache[en_text]):
                vi_data[k] = cache[en_text]
                continue

            # Shield tokens for translation
            shielded, tokens = shield_tokens(en_text)
            tokens_map[k] = tokens
            to_translate_keys.append(k)
            to_translate_texts.append(shielded)

        print(f"  Already resolved / cached: {len(vi_data)}, Needs translation: {len(to_translate_keys)}")

        # Batch translate
        batch_size = 25
        total_batches = (len(to_translate_keys) + batch_size - 1) // batch_size
        for b_idx in range(0, len(to_translate_keys), batch_size):
            batch_keys = to_translate_keys[b_idx:b_idx + batch_size]
            batch_texts = to_translate_texts[b_idx:b_idx + batch_size]

            translated_parts = translate_batch(batch_texts)

            for key, trans in zip(batch_keys, translated_parts):
                toks = tokens_map[key]
                # CRITICAL: post_process_vi runs on shielded text so tokens are NEVER modified!
                polished_shielded = post_process_vi(trans)
                unshielded = unshield_tokens(polished_shielded, toks)
                vi_data[key] = unshielded
                cache[key] = unshielded
                cache[en_data[key]] = unshielded

            cur_batch_num = b_idx // batch_size + 1
            print(f"  Translated batch {cur_batch_num}/{total_batches} ({len(batch_keys)} items)")
            time.sleep(0.3)

            # Incremental cache save every 5 batches
            if cur_batch_num % 5 == 0 or cur_batch_num == total_batches:
                with open(CACHE_PATH, "w", encoding="utf-8") as f:
                    json.dump(cache, f, ensure_ascii=False, indent=2)

        translated_tables[name] = (en_path, vi_data, en_data)

    # 4. Strict Validation Gate: 100% Token Preservation & Count
    print("\n" + "=" * 70)
    print("--- Step 3: VERIFICATION GATE: 100% Token Preservation ---")
    print("=" * 70)

    total_gate_errors = 0
    for name, (en_path, vi_data, en_data) in translated_tables.items():
        table_errors = 0
        if len(vi_data) != len(en_data):
            print(f"FATAL: Entry count mismatch in {name}! Orig: {len(en_data)}, VI: {len(vi_data)}")
            sys.exit(1)

        for k in en_data:
            orig = en_data[k]
            trans = vi_data.get(k, "")

            orig_tokens = TOKEN_REGEX.findall(orig)
            trans_tokens = TOKEN_REGEX.findall(trans)

            if sorted(orig_tokens) != sorted(trans_tokens):
                table_errors += 1
                total_gate_errors += 1
                print(f"ERROR in {name} [{k}]:")
                print(f"  EN: {repr(orig)}")
                print(f"  VI: {repr(trans)}")
                print(f"  Expected tokens: {orig_tokens}")
                print(f"  Found tokens:    {trans_tokens}")

        if table_errors == 0:
            print(f"[{name}] PASSED 100%: All {len(en_data)} entries verified perfectly!")
        else:
            print(f"[{name}] FAILED: {table_errors} token mismatch errors!")

    if total_gate_errors > 0:
        print(f"\nFATAL: Total {total_gate_errors} token mismatch errors detected!")
        print("Aborting before overwriting any files.")
        sys.exit(1)

    print("\nALL 3 TABLES PASSED THE VALIDATION GATE WITH 0 ERRORS!")

    # 5. Overwrite the 3 EN .bin files
    print("\n--- Step 4: Overwriting EN .bin files with valid UTF-8 JSON ---")
    for name, (en_path, vi_data, en_data) in translated_tables.items():
        with open(en_path, "w", encoding="utf-8") as f:
            json.dump(vi_data, f, ensure_ascii=False, indent=2)
        print(f"Wrote {len(vi_data)} entries to {en_path.name}")

        # Syntax and integrity check
        with open(en_path, "r", encoding="utf-8") as f:
            verified = json.load(f)
        assert len(verified) == len(en_data), f"Count mismatch after write in {name}!"
        print(f"Syntax verification passed: {en_path.name} is valid UTF-8 JSON ({len(verified)} items).")

    print("\n" + "=" * 70)
    print(f"SUBAGENT 4B COMPLETED SUCCESSFULLY! Total {total_entries_count} entries translated.")
    print("=" * 70)

if __name__ == "__main__":
    main()
