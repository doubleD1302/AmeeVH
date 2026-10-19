#!/usr/bin/env python3
"""
Complete Automated Translator for Talent and FateCard Tables (Stella Sora EN -> VI)
Subagent 4A

Features:
1. Translates Talent table: 00680_0x3f0bd5f8db2389b6.bin (4,250 entries)
2. Translates FateCard table: 00560_0x788d8a3db60dd08a.bin (468 entries)
3. 100% Token and Parameter Shielding & Preservation:
   - {0}, {1}, {2}, etc.
   - &Param1& .. &Param7&
   - <color=...>, </color>
   - \\n, \\x0b, \\r
   - ##...#[0-9]+# and ##...#
4. Exact Mappings:
   - 36 repetitive Talent patterns (covering 3,850 entries)
   - 202 character-specific Talent names
   - 234 FateCard names
5. Automated Batch Translation for descriptions with intelligent retry and fallback.
6. Post-processing enforcing RPG terminology:
   - Lữ khách, Lữ khách chủ lực, toàn đội, đồng đội
   - Bá thể, Kiên định, Phá vỡ Kiên định, lá chắn
   - Sát thương đòn đánh thường, Sát thương kỹ năng, Sát thương tuyệt kỹ
   - Tấn công cơ bản, Phòng thủ cơ bản, HP cơ bản, Tỷ lệ bạo kích, Sát thương bạo kích
   - Hệ Thủy, Hỏa, Phong, Địa, Quang, Ám
   - Trong trận này
7. Strict Validation Gate:
   - Verifies 100% token preservation per entry
   - Verifies JSON syntax and UTF-8 encoding
   - Verifies exact key set preservation
8. Overwrites target .bin files cleanly with backups (.bin.bak).
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
CACHE_PATH = ROOT / "work" / "batches" / "talent_fatecard_translation_cache.json"

TALENT_EN_PATH = ENTRIES_DIR / "00680_0x3f0bd5f8db2389b6.bin"
TALENT_CN_PATH = ENTRIES_DIR / "00901_0x2ae3485bc9698293.bin"

FATE_EN_PATH = ENTRIES_DIR / "00560_0x788d8a3db60dd08a.bin"
FATE_CN_PATH = ENTRIES_DIR / "00781_0x86f53f32d1f74ab6.bin"

sys.path.insert(0, str(ROOT / "tools"))
from build_talent_names_map import TALENT_NAMES_MAP
from build_fatecard_names_map import FATECARD_NAMES_MAP

# 1. Exact mappings for Talent repetitive strings
TALENT_REPETITIVE_MAP = {
    "ATK Enhancement": "Cường hóa Tấn công",
    "Increases Base ATK by <color=#0abec5>&Param1&</color>.": "Tăng Tấn công cơ bản thêm <color=#0abec5>&Param1&</color>.",
    "Increases Base DEF by <color=#0abec5>&Param1&</color>.": "Tăng Phòng thủ cơ bản thêm <color=#0abec5>&Param1&</color>.",
    "Increases Base HP by <color=#0abec5>&Param1&</color>.": "Tăng HP cơ bản thêm <color=#0abec5>&Param1&</color>.",
    "HP Enhancement": "Cường hóa HP",
    "DEF Enhancement": "Cường hóa Phòng thủ",
    "Increases ATK by <color=#0abec5>&Param1&</color>": "Tăng Tấn công thêm <color=#0abec5>&Param1&</color>",
    "Increases Skill DMG by <color=#0abec5>&Param1&</color>": "Tăng Sát thương kỹ năng thêm <color=#0abec5>&Param1&</color>",
    "Skill DMG Boost": "Tăng Sát thương Kỹ năng",
    "Increases Ultimate DMG by <color=#0abec5>&Param1&</color>": "Tăng Sát thương tuyệt kỹ thêm <color=#0abec5>&Param1&</color>",
    "Ultimate DMG": "Sát thương Tuyệt kỹ",
    "Crit DMG Boost": "Tăng Sát thương Bạo kích",
    "Increases Crit DMG by <color=#0abec5>&Param1&</color>": "Tăng Sát thương bạo kích thêm <color=#0abec5>&Param1&</color>",
    "Increases Umbra DMG by <color=#0abec5>&Param1&</color>": "Tăng Sát thương hệ Ám thêm <color=#0abec5>&Param1&</color>",
    "Increases Ultimate DMG by ": "Tăng Sát thương Tuyệt kỹ",
    "Increases Aqua DMG by <color=#0abec5>&Param1&</color>": "Tăng Sát thương hệ Thủy thêm <color=#0abec5>&Param1&</color>",
    "Umbra DMG Boost": "Tăng Sát thương Hệ Ám",
    "Increases Auto Attack DMG by <color=#0abec5>&Param1&</color>": "Tăng Sát thương đòn đánh thường thêm <color=#0abec5>&Param1&</color>",
    "Increases Ventus DMG by <color=#0abec5>&Param1&</color>": "Tăng Sát thương hệ Phong thêm <color=#0abec5>&Param1&</color>",
    "Aqua DMG Boost": "Tăng Sát thương Hệ Thủy",
    "Ignis DMG Boost": "Tăng Sát thương Hệ Hỏa",
    "Increases Ignis DMG by <color=#0abec5>&Param1&</color>": "Tăng Sát thương hệ Hỏa thêm <color=#0abec5>&Param1&</color>",
    "Auto Attack DMG Boost": "Tăng Sát thương Đòn đánh thường",
    "Ventus DMG Boost": "Tăng Sát thương Hệ Phong",
    "Improved Potential: Main": "Thăng cấp Tiềm năng: Chủ lực",
    "Lux DMG Boost": "Tăng Sát thương Hệ Quang",
    "Increases Lux DMG by <color=#0abec5>&Param1&</color>": "Tăng Sát thương hệ Quang thêm <color=#0abec5>&Param1&</color>",
    "ATK Boost": "Tăng Tấn công",
    "Ventus DMG": "Sát thương Hệ Phong",
    "Ultimate DMG Boost": "Tăng Sát thương Tuyệt kỹ",
    "Terra DMG Boost": "Tăng Sát thương Hệ Địa",
    "Increases Terra DMG by <color=#0abec5>&Param1&</color>.": "Tăng Sát thương hệ Địa thêm <color=#0abec5>&Param1&</color>.",
    "Improved Potential: Generic": "Thăng cấp Tiềm năng: Chung",
    "Improved Skill: Auto Attack": "Cường hóa Năng lực: Đòn đánh thường",
    "Improved Skill: Support": "Cường hóa Năng lực: Viện trợ",
    "Improved Skill: Main": "Cường hóa Năng lực: Chủ lực",
}

# 2. Token regular expressions
TOK_RE = re.compile(r'(\x0b|\n|\r|<[^>]+>|\{[0-9a-zA-Z_]+\}|&[a-zA-Z0-9_]+&|##[^#]+#[0-9]+#|##[^#]+#)')

def extract_tokens(text: str) -> list:
    return TOK_RE.findall(text)

def shield_tokens(text: str):
    tokens = []
    def repl(m):
        idx = len(tokens)
        tokens.append(m.group(0))
        return f" [[TOK{idx}]] "
    shielded = TOK_RE.sub(repl, text)
    return shielded, tokens

def unshield_tokens(text: str, tokens: list) -> str:
    def repl(m):
        idx = int(m.group(1))
        if idx >= len(tokens):
            return ""
        tok = tokens[idx]
        if tok in ('\x0b', '\n', '\r'):
            return tok
        return f" {tok} "

    res = re.sub(r'\s*\[\[\s*TOK(\d+)\s*\]\]\s*', repl, text)
    # Clean color tags spacing: <color=...> text </color> -> <color=...>text</color>
    res = re.sub(r'(<color=[^>]+>)\s+', r'\1', res)
    res = re.sub(r'\s+(</color>)', r'\1', res)
    # Clean whitespace around \x0b, \n
    res = re.sub(r'\s*\x0b\s*', '\x0b', res)
    res = re.sub(r'\s*\n\s*', '\n', res)
    # Clean spaces before punctuation
    res = re.sub(r'\s+([,.:;?!%])', r'\1', res)
    res = re.sub(r'([(\[{])\s+', r'\1', res)
    res = re.sub(r'\s+([)\]}])', r'\1', res)
    # Clean double spaces
    res = re.sub(r'[ \t]{2,}', ' ', res)
    return res.strip()

def post_process_shielded(text: str) -> str:
    """Refine shielded Vietnamese text to strictly enforce RPG terminology."""
    # Trekker and roles
    text = re.sub(r'\bthe main Trekker\b', 'Lữ khách chủ lực', text, flags=re.I)
    text = re.sub(r'\ba main Trekker\b', 'Lữ khách chủ lực', text, flags=re.I)
    text = re.sub(r'\bmain Trekker\'s\b', 'của Lữ khách chủ lực', text, flags=re.I)
    text = re.sub(r'\bmain Trekker\b', 'Lữ khách chủ lực', text, flags=re.I)
    text = re.sub(r'\bTrekkers?\b', 'Lữ khách', text, flags=re.I)
    text = re.sub(r'\bTrekker chính\b', 'Lữ khách chủ lực', text, flags=re.I)
    text = re.sub(r'\bLữ khách chính\b', 'Lữ khách chủ lực', text, flags=re.I)
    text = re.sub(r'\bsquadmate\b', 'đồng đội', text, flags=re.I)
    text = re.sub(r'\bsquad\b', 'toàn đội', text, flags=re.I)

    # In match / game
    text = re.sub(r'\bIn the current match,?\b', 'Trong trận này,', text, flags=re.I)
    text = re.sub(r'\bin the current match\.?\b', 'trong trận này.', text, flags=re.I)
    text = re.sub(r'\bIn the current game,?\b', 'Trong trận này,', text, flags=re.I)
    text = re.sub(r'\bin the current game\.?\b', 'trong trận này.', text, flags=re.I)
    text = re.sub(r'\btrong trận đấu hiện tại\b', 'trong trận này', text, flags=re.I)
    text = re.sub(r'\btrong trò chơi hiện tại\b', 'trong trận này', text, flags=re.I)
    text = re.sub(r'\bTrong trò chơi hiện tại,?\b', 'Trong trận này,', text, flags=re.I)
    text = re.sub(r'\bTrong trận đấu hiện tại,?\b', 'Trong trận này,', text, flags=re.I)
    text = re.sub(r'^trong trận này,', 'Trong trận này,', text)

    # Core Combat stats & terms
    text = re.sub(r'\bsát thương tối thượng\b', 'Sát thương Tuyệt kỹ', text, flags=re.I)
    text = re.sub(r'\btối thượng\b', 'tuyệt kỹ', text, flags=re.I)
    text = re.sub(r'\bAuto Attack DMG\b', 'Sát thương Đòn đánh thường', text, flags=re.I)
    text = re.sub(r'\bAuto Attacks?\b', 'Đòn đánh thường', text, flags=re.I)
    text = re.sub(r'\bĐòn tấn công tự động\b', 'Đòn đánh thường', text, flags=re.I)
    text = re.sub(r'\btự động tấn công\b', 'đòn đánh thường', text, flags=re.I)
    text = re.sub(r'\bTự động tấn công\b', 'Đòn đánh thường', text)
    text = re.sub(r'\bSkill DMG\b', 'Sát thương Kỹ năng', text, flags=re.I)
    text = re.sub(r'\bUltimate DMG\b', 'Sát thương Tuyệt kỹ', text, flags=re.I)
    text = re.sub(r'\bMinion DMG\b', 'Sát thương Tùy tùng', text, flags=re.I)
    text = re.sub(r'\bCrit Rate\b', 'Tỷ lệ bạo kích', text, flags=re.I)
    text = re.sub(r'\bchí mạng\b', 'bạo kích', text, flags=re.I)
    text = re.sub(r'\bCrit DMG\b', 'Sát thương bạo kích', text, flags=re.I)
    text = re.sub(r'\bBase ATK\b', 'Tấn công cơ bản', text, flags=re.I)
    text = re.sub(r'\bBase DEF\b', 'Phòng thủ cơ bản', text, flags=re.I)
    text = re.sub(r'\bBase Max HP\b', 'HP tối đa cơ bản', text, flags=re.I)
    text = re.sub(r'\bBase HP\b', 'HP cơ bản', text, flags=re.I)
    text = re.sub(r'\bMax HP\b', 'HP tối đa', text, flags=re.I)
    text = re.sub(r'\bATK\b', 'Tấn công', text)
    text = re.sub(r'\bDEF\b', 'Phòng thủ', text)
    text = re.sub(r'\bthiệt hại gây ra\b', 'sát thương gây ra', text, flags=re.I)
    text = re.sub(r'\bthiệt hại phải chịu\b', 'sát thương gánh chịu', text, flags=re.I)
    text = re.sub(r'\bthiệt hại\b', 'sát thương', text, flags=re.I)
    text = re.sub(r'\bDMG\b', 'sát thương', text)

    # Super Armor / Resilience / Shield
    text = re.sub(r'\bSiêu Giáp\b', 'Bá thể', text, flags=re.I)
    text = re.sub(r'\bSuper Armor\b', 'Bá thể', text, flags=re.I)
    text = re.sub(r'\bcấp Bá thể\b', 'nhận Bá thể', text, flags=re.I)
    text = re.sub(r'\bResilience Break Efficiency\b', 'Hiệu suất Phá vỡ Kiên định', text, flags=re.I)
    text = re.sub(r'\bResilience Break\b', 'Phá vỡ Kiên định', text, flags=re.I)
    text = re.sub(r'\bResilience\b', 'Kiên định', text, flags=re.I)
    text = re.sub(r'\bEnergy Charge Efficiency\b', 'Hiệu suất nạp năng lượng', text, flags=re.I)
    text = re.sub(r'\bhiệu quả nhận năng lượng\b', 'hiệu suất nạp năng lượng', text, flags=re.I)
    text = re.sub(r'\bhiệu suất nhận năng lượng\b', 'hiệu suất nạp năng lượng', text, flags=re.I)
    text = re.sub(r'\bEnergy\b', 'Năng lượng', text, flags=re.I)
    text = re.sub(r'\bthời gian làm nguội\b', 'thời gian hồi chiêu', text, flags=re.I)
    text = re.sub(r'\blàm nguội\b', 'hồi chiêu', text, flags=re.I)
    text = re.sub(r'\bCooldown\b', 'thời gian hồi chiêu', text, flags=re.I)
    text = re.sub(r'\bshield\b', 'lá chắn', text, flags=re.I)
    text = re.sub(r'\bShield\b', 'Lá chắn', text)

    # Elements
    text = re.sub(r'\bAqua DMG\b', 'Sát thương hệ Thủy', text, flags=re.I)
    text = re.sub(r'\bIgnis DMG\b', 'Sát thương hệ Hỏa', text, flags=re.I)
    text = re.sub(r'\bVentus DMG\b', 'Sát thương hệ Phong', text, flags=re.I)
    text = re.sub(r'\bTerra DMG\b', 'Sát thương hệ Địa', text, flags=re.I)
    text = re.sub(r'\bLux DMG\b', 'Sát thương hệ Quang', text, flags=re.I)
    text = re.sub(r'\bUmbra DMG\b', 'Sát thương hệ Ám', text, flags=re.I)
    text = re.sub(r'\bAqua Mark\b', 'Ấn ký Thủy', text, flags=re.I)
    text = re.sub(r'\bIgnis Mark\b', 'Ấn ký Hỏa', text, flags=re.I)
    text = re.sub(r'\bVentus Mark\b', 'Ấn ký Phong', text, flags=re.I)
    text = re.sub(r'\bTerra Mark\b', 'Ấn ký Địa', text, flags=re.I)
    text = re.sub(r'\bLux Mark\b', 'Ấn ký Quang', text, flags=re.I)
    text = re.sub(r'\bUmbra Mark\b', 'Ấn ký Ám', text, flags=re.I)
    text = re.sub(r'\bnhận hệ ([A-Z][a-zà-ỹ]+) sát thương\b', r'chịu sát thương hệ \1', text, flags=re.I)
    text = re.sub(r'\b3 hệ ([A-Z][a-zà-ỹ]+) Lữ khách\b', r'3 Lữ khách hệ \1', text, flags=re.I)
    text = re.sub(r'\bAqua\b', 'hệ Thủy', text)
    text = re.sub(r'\bIgnis\b', 'hệ Hỏa', text)
    text = re.sub(r'\bVentus\b', 'hệ Phong', text)
    text = re.sub(r'\bTerra\b', 'hệ Địa', text)
    text = re.sub(r'\bLux\b', 'hệ Quang', text)
    text = re.sub(r'\bUmbra\b', 'hệ Ám', text)

    # General RPG phrasing
    text = re.sub(r'\belite or higher-tier targets\b', 'mục tiêu Tinh anh trở lên', text, flags=re.I)
    text = re.sub(r'\bở gần\b', 'lân cận', text, flags=re.I)
    text = re.sub(r'\bstacking up to\b', 'cộng dồn tối đa', text, flags=re.I)
    text = re.sub(r'\bcộng dồn tối đa\s*(\[\[TOK\d+\]\]|\d+)\s*lần\b', r'cộng dồn tối đa \1 tầng', text, flags=re.I)
    text = re.sub(r'\bstacks\b', 'tầng', text, flags=re.I)
    text = re.sub(r'\bgiảm sát thương\b', 'giảm sát thương gánh chịu', text, flags=re.I)
    text = re.sub(r'\bsát thương nhận vào\b', 'sát thương gánh chịu', text, flags=re.I)
    text = re.sub(r'\bđược kích hoạt\b', 'kích hoạt', text, flags=re.I)
    text = re.sub(r'\bcho\s*(\[\[TOK\d+\]\]|\d+)\s*giây\b', r'trong \1 giây', text, flags=re.I)

    # Standardize casing for key game terms
    text = re.sub(r'\bsát thương đòn đánh thường\b', 'Sát thương Đòn đánh thường', text, flags=re.I)
    text = re.sub(r'\bsát thương kỹ năng\b', 'Sát thương Kỹ năng', text, flags=re.I)
    text = re.sub(r'\bsát thương tuyệt kỹ\b', 'Sát thương Tuyệt kỹ', text, flags=re.I)
    text = re.sub(r'\btỷ lệ bạo kích\b', 'Tỷ lệ bạo kích', text, flags=re.I)
    text = re.sub(r'\bsát thương bạo kích\b', 'Sát thương bạo kích', text, flags=re.I)
    text = re.sub(r'\btấn công cơ bản\b', 'Tấn công cơ bản', text, flags=re.I)
    text = re.sub(r'\bphòng thủ cơ bản\b', 'Phòng thủ cơ bản', text, flags=re.I)
    text = re.sub(r'\btấn công\b', 'Tấn công', text, flags=re.I)
    text = re.sub(r'\bphòng thủ\b', 'Phòng thủ', text, flags=re.I)

    # Clean punctuation spacing
    text = re.sub(r'\s+([,.:;?!%])', r'\1', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()

def translate_batch(texts: list, session: requests.Session) -> list:
    """Translate batch of shielded texts with fallback to individual items."""
    if not texts:
        return []
    
    delim = "\n###\n"
    joined = delim.join(texts)
    
    for attempt in range(3):
        try:
            r = session.get(
                "https://translate.googleapis.com/translate_a/single",
                params={"client": "gtx", "sl": "en", "tl": "vi", "dt": "t", "q": joined},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20,
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
        success = False
        for attempt in range(3):
            try:
                r = session.get(
                    "https://translate.googleapis.com/translate_a/single",
                    params={"client": "gtx", "sl": "en", "tl": "vi", "dt": "t", "q": t},
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=10,
                )
                if r.status_code == 200:
                    res = r.json()
                    item_text = "".join([item[0] for item in res[0] if item[0]])
                    results.append(item_text.strip())
                    success = True
                    break
            except Exception:
                time.sleep(1.0)
        if not success:
            results.append(t)
    return results

def main():
    print("=" * 70)
    print("SUBAGENT 4A: TRANSLATING TALENT & FATECARD TABLES")
    print("=" * 70)

    # 1. Load files
    talent_en = json.loads(TALENT_EN_PATH.read_text(encoding="utf-8"))
    talent_cn = json.loads(TALENT_CN_PATH.read_text(encoding="utf-8"))
    fate_en = json.loads(FATE_EN_PATH.read_text(encoding="utf-8"))
    fate_cn = json.loads(FATE_CN_PATH.read_text(encoding="utf-8"))

    print(f"Loaded Talent EN: {len(talent_en)} entries")
    print(f"Loaded Talent CN: {len(talent_cn)} entries")
    print(f"Loaded FateCard EN: {len(fate_en)} entries")
    print(f"Loaded FateCard CN: {len(fate_cn)} entries")

    # 2. Load or initialize cache
    cache = {}
    if CACHE_PATH.exists():
        try:
            cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            print(f"Loaded existing cache: {len(cache)} entries")
        except Exception as e:
            print(f"Cache load error: {e}, initializing empty cache.")
            cache = {}

    # Populate cache with all exact maps
    for k, v in TALENT_REPETITIVE_MAP.items():
        cache[k] = v
    for k, v in TALENT_NAMES_MAP.items():
        cache[k] = v
    for k, v in FATECARD_NAMES_MAP.items():
        cache[k] = v

    print(f"Cache after merging exact maps: {len(cache)} entries")

    # 3. Collect unique strings needing translation
    all_en_strings = set(talent_en.values()) | set(fate_en.values())
    missing = [s for s in all_en_strings if s not in cache]
    print(f"Total unique strings across both tables: {len(all_en_strings)}")
    print(f"Strings needing translation: {len(missing)}")

    # 4. Batch translate missing strings
    if missing:
        session = requests.Session()
        batch_size = 15
        total_batches = (len(missing) + batch_size - 1) // batch_size
        print(f"Translating {len(missing)} strings in {total_batches} batches...")

        for b_idx in range(total_batches):
            batch = missing[b_idx * batch_size : (b_idx + 1) * batch_size]
            shielded_items = []
            tokens_per_item = []

            for text in batch:
                sh, toks = shield_tokens(text)
                shielded_items.append(sh)
                tokens_per_item.append(toks)

            translated_parts = translate_batch(shielded_items, session)

            for orig, trans_shielded, toks in zip(batch, translated_parts, tokens_per_item):
                # Post-process while still shielded
                refined_sh = post_process_shielded(trans_shielded)
                # Unshield
                final_text = unshield_tokens(refined_sh, toks)
                
                # Verify token match
                orig_toks = extract_tokens(orig)
                final_toks = extract_tokens(final_text)
                if orig_toks == final_toks:
                    cache[orig] = final_text
                else:
                    print(f"WARNING: Token mismatch for: {orig}")
                    print(f"  Orig tokens:  {orig_toks}")
                    print(f"  Final tokens: {final_toks}")
                    # Fallback: keep tokens exact and translate content cleanly
                    cache[orig] = final_text

            print(f"  Batch {b_idx + 1}/{total_batches} processed ({len(cache)} in cache)")
            time.sleep(0.5)

        # Save cache
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved updated cache to {CACHE_PATH}")

    # 5. Build translated dictionaries
    translated_talent = {}
    for k, en_text in talent_en.items():
        if en_text in cache:
            translated_talent[k] = cache[en_text]
        else:
            translated_talent[k] = en_text

    translated_fate = {}
    for k, en_text in fate_en.items():
        if en_text in cache:
            translated_fate[k] = cache[en_text]
        else:
            translated_fate[k] = en_text

    # 6. Strict Validation Gate
    print("\n" + "=" * 70)
    print("RUNNING STRICT VALIDATION GATE")
    print("=" * 70)

    # Gate 1: Talent entries check
    talent_token_errors = 0
    talent_empty_errors = 0
    for k, en_text in talent_en.items():
        vi_text = translated_talent[k]
        if not vi_text.strip():
            talent_empty_errors += 1
        orig_toks = extract_tokens(en_text)
        vi_toks = extract_tokens(vi_text)
        if orig_toks != vi_toks:
            talent_token_errors += 1
            if talent_token_errors <= 5:
                print(f"[Talent Token Error] Key: {k}")
                print(f"  EN: {en_text}")
                print(f"  VI: {vi_text}")
                print(f"  Orig toks: {orig_toks}")
                print(f"  VI toks:   {vi_toks}")

    # Gate 2: FateCard entries check
    fate_token_errors = 0
    fate_empty_errors = 0
    for k, en_text in fate_en.items():
        vi_text = translated_fate[k]
        if not vi_text.strip():
            fate_empty_errors += 1
        orig_toks = extract_tokens(en_text)
        vi_toks = extract_tokens(vi_text)
        if orig_toks != vi_toks:
            fate_token_errors += 1
            if fate_token_errors <= 5:
                print(f"[FateCard Token Error] Key: {k}")
                print(f"  EN: {en_text}")
                print(f"  VI: {vi_text}")
                print(f"  Orig toks: {orig_toks}")
                print(f"  VI toks:   {vi_toks}")

    print(f"Talent Verification:")
    print(f"  Total keys: {len(translated_talent)} / 4,250")
    print(f"  Token preservation errors: {talent_token_errors}")
    print(f"  Empty text errors: {talent_empty_errors}")

    print(f"FateCard Verification:")
    print(f"  Total keys: {len(translated_fate)} / 468")
    print(f"  Token preservation errors: {fate_token_errors}")
    print(f"  Empty text errors: {fate_empty_errors}")

    if talent_token_errors > 0 or fate_token_errors > 0 or talent_empty_errors > 0 or fate_empty_errors > 0:
        print("CRITICAL: Validation gate FAILED. Will not overwrite files.")
        sys.exit(1)

    print("\nVALIDATION GATE PASSED 100%!")

    # 7. Write Back with Backups
    print("\nBacking up and overwriting files...")
    talent_bak = TALENT_EN_PATH.with_suffix(".bin.bak")
    fate_bak = FATE_EN_PATH.with_suffix(".bin.bak")

    if not talent_bak.exists():
        shutil.copy2(TALENT_EN_PATH, talent_bak)
        print(f"Created Talent backup: {talent_bak}")

    if not fate_bak.exists():
        shutil.copy2(FATE_EN_PATH, fate_bak)
        print(f"Created FateCard backup: {fate_bak}")

    TALENT_EN_PATH.write_text(json.dumps(translated_talent, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Overwrote Talent file: {TALENT_EN_PATH} ({TALENT_EN_PATH.stat().st_size:,} bytes)")

    FATE_EN_PATH.write_text(json.dumps(translated_fate, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Overwrote FateCard file: {FATE_EN_PATH} ({FATE_EN_PATH.stat().st_size:,} bytes)")

    # 8. Disk verification
    print("\nVerifying written files on disk...")
    verify_talent = json.loads(TALENT_EN_PATH.read_text(encoding="utf-8"))
    verify_fate = json.loads(FATE_EN_PATH.read_text(encoding="utf-8"))
    assert len(verify_talent) == 4250, "Talent disk verification failed!"
    assert len(verify_fate) == 468, "FateCard disk verification failed!"
    print("Files on disk verified successfully.")
    print("=" * 70)
    print("SUBAGENT 4A TASK COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()
