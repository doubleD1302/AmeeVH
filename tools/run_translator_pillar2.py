#!/usr/bin/env python3
"""
Senior Translator 2: Lồng Tiếng & Hồ Sơ Nhân Vật (Pillar 2)
Translates 9 tables (6,188 strings) with high-speed batching, 100% token preservation,
anime slice-of-life natural dialogue tone, and Master Glossary enforcement.
"""

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pipeline_translator_engine import (
    load_master_glossary, load_cache, save_cache,
    shield_tokens, unshield_tokens, translate_batch,
    post_process_vietnamese, is_valid_token_preservation
)

P2_INPUT = ROOT / "work" / "batches" / "pillar2_voices_characters.json"
P2_OUTPUT = ROOT / "work" / "batches" / "pillar2_translated.json"

def build_domain_lookup(terms, p2_data):
    lookup = {k.lower(): v for k, v in terms.items()}
    lookup.update(terms)

    # 1. Voice Cues (89 standardized anime RPG cues)
    voice_cues = {
        'Affirmative': 'Đồng Ý',
        'Angry': 'Tức Giận',
        'Appreciating the Gift 1': 'Nhận Quà 1',
        'Appreciating the Gift 2': 'Nhận Quà 2',
        'Appreciating the Gift 3': 'Nhận Quà 3',
        'Character Down 1': 'Nhân Vật Gục Ngã 1',
        'Character Down 2': 'Nhân Vật Gục Ngã 2',
        'Confused': 'Bối Rối',
        'Defeated 1': 'Thất Bại 1',
        'Defeated 2': 'Thất Bại 2',
        'Disagreeing': 'Không Đồng Ý',
        'Entering Combat 1': 'Vào Trận 1',
        'Entering Combat 2': 'Vào Trận 2',
        'Entering Combat 3': 'Vào Trận 3',
        'Entering Combat 4': 'Vào Trận 4',
        'Excited': 'Phấn Khích',
        'First Meeting': 'Lần Đầu Gặp Gỡ',
        'Greetings 1': 'Lời Chào 1',
        'Greetings 2': 'Lời Chào 2',
        'Greetings 3': 'Lời Chào 3',
        'Greetings 4': 'Lời Chào 4',
        'Greetings 5': 'Lời Chào 5',
        'Happy': 'Vui Vẻ',
        'Meeting Again': 'Tái Ngộ',
        'Memory Snapshot Unlocked': 'Mở Khóa Khoảnh Khắc Hồi Ức',
        'Monolith Shop': 'Cửa Hàng Cự Tháp',
        'Monolith: Ascension Begins (New Difficulty)': 'Cự Tháp: Bắt Đầu Thăng Tiến (Độ Khó Mới)',
        'Monolith: Ascension Begins (New Type)': 'Cự Tháp: Bắt Đầu Thăng Tiến (Loại Mới)',
        'Monolith: Ascension Begins 1': 'Cự Tháp: Bắt Đầu Thăng Tiến 1',
        'Monolith: Ascension Begins 2': 'Cự Tháp: Bắt Đầu Thăng Tiến 2',
        'Monolith: Ascension Begins 3': 'Cự Tháp: Bắt Đầu Thăng Tiến 3',
        'Monolith: Ascension Begins 4': 'Cự Tháp: Bắt Đầu Thăng Tiến 4',
        'Monolith: Ascension Begins 5': 'Cự Tháp: Bắt Đầu Thăng Tiến 5',
        'Monolith: Battle Ended 1': 'Cự Tháp: Trận Đánh Kết Thúc 1',
        'Monolith: Battle Ended 2': 'Cự Tháp: Trận Đánh Kết Thúc 2',
        'Monolith: Battle Ended 3': 'Cự Tháp: Trận Đánh Kết Thúc 3',
        'Monolith: Event': 'Cự Tháp: Biến Cố',
        'Monolith: Safe Room': 'Cự Tháp: Phòng Nghỉ An Toàn',
        'Motto 1': 'Phương Châm 1',
        'Motto 2': 'Phương Châm 2',
        'Motto 3': 'Phương Châm 3',
        'Motto 4': 'Phương Châm 4',
        'Motto 5': 'Phương Châm 5',
        'New Stance Unlocked': 'Mở Khóa Dáng Vẻ Mới',
        'Potential Acquired 1': 'Khai Mở Tiềm Năng 1',
        'Potential Acquired 2': 'Khai Mở Tiềm Năng 2',
        'Potential Acquired 3': 'Khai Mở Tiềm Năng 3',
        'Potential Acquired 4': 'Khai Mở Tiềm Năng 4',
        'Potential Acquired 5': 'Khai Mở Tiềm Năng 5',
        'Questioning': 'Nghi Hoặc',
        'Reach Affinity Lv. 10': 'Đạt Cấp Thân Mật 10',
        'Reach Affinity Lv. 15': 'Đạt Cấp Thân Mật 15',
        'Reach Affinity Lv. 25': 'Đạt Cấp Thân Mật 25',
        'Reach Affinity Lv. 30': 'Đạt Cấp Thân Mật 30',
        'Sad': 'Buồn Bã',
        'Sigh': 'Thở Dài',
        'Significant Trekker Growth': 'Lữ Khách Trưởng Thành Vượt Bậc',
        'Trekker Development': 'Phát Triển Lữ Khách',
        'Ultimate Battle Cry 1': 'Tuyên Ngôn Tuyệt Kỹ 1',
        'Ultimate Battle Cry 2': 'Tuyên Ngôn Tuyệt Kỹ 2',
        'Victory 1': 'Thắng Trận 1',
        'Victory 2': 'Thắng Trận 2'
    }
    for i in range(1, 16):
        voice_cues[f'Home Screen Interaction {i}'] = f'Tương Tác Màn Hình Chính {i}'
    for i in [10, 15, 20, 25, 30]:
        voice_cues[f'Home Screen Interaction: Affinity {i}'] = f'Tương Tác Thân Mật {i}'
    voice_cues['Home Screen Interaction: Idle 1'] = 'Tương Tác Chờ 1'
    voice_cues['Home Screen Interaction: Idle 2'] = 'Tương Tác Chờ 2'
    voice_cues['Home Screen Interaction: Inactive'] = 'Tương Tác Treo Máy Lâu'
    voice_cues['Home Screen Interaction: Repeated Input 1'] = 'Tương Tác Nhấp Liên Tục 1'
    voice_cues['Home Screen Interaction: Repeated Input 2'] = 'Tương Tác Nhấp Liên Tục 2'
    voice_cues['Listen to a Common Runic Disc'] = 'Nghe Đĩa Cổ Ngữ Thường'
    voice_cues['Listen to a Unique Runic Disc'] = 'Nghe Đĩa Cổ Ngữ Đặc Biệt'
    lookup.update(voice_cues)

    # 2. Base Info Labels & Story Headers
    lookup.update({
        'Name': 'Tên',
        'Birthday': 'Sinh Nhật',
        'Affiliation': 'Trực Thuộc',
        'Skills': 'Sở Trường',
        'Address': 'Địa Chỉ',
        'Experience': 'Kinh Nghiệm',
        'Weapon': 'Vũ Khí',
        'Rate': 'Thù Lao',
        'Basic Info': 'Thông Tin Cơ Bản',
        'Reason for Becoming a Trekker': 'Lý Do Trở Thành Lữ Khách',
        'Null': 'Không',
        '???': '???'
    })
    for i in range(1, 10):
        lookup[f'CV Excerpt {i}'] = f'Trích Đoạn Hồ Sơ {i}'

    # 3. Durations
    lookup.update({
        '1 year': '1 năm',
        '1-2 years': '1-2 năm',
        '2 years': '2 năm',
        '2.5 years': '2.5 năm',
        '3 years': '3 năm',
        '8 Years': '8 năm',
        'Above 3 years': 'Trên 3 năm',
        '3+ years': 'Trên 3 năm'
    })

    # 4. CV Voice Actor Names (Preserve original romanized names)
    cd = p2_data.get('CharacterDes', {}).get('entries', {})
    for k, v in cd.items():
        if k.endswith('.1') or k.endswith('.8'):
            lookup[v] = v

    # 5. Dates
    months = {
        'January': 'tháng 1', 'February': 'tháng 2', 'March': 'tháng 3', 'April': 'tháng 4',
        'May': 'tháng 5', 'June': 'tháng 6', 'July': 'tháng 7', 'August': 'tháng 8',
        'September': 'tháng 9', 'October': 'tháng 10', 'November': 'tháng 11', 'December': 'tháng 12'
    }
    date_pattern = re.compile(r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d+)(?:st|nd|rd|th)?$')

    # 6. Structured Patterns across all tables
    for tbl, info in p2_data.items():
        for k, v in info.get('entries', {}).items():
            if not v or not v.strip():
                continue
            # Date
            m_date = date_pattern.match(v)
            if m_date:
                lookup[v] = f'Ngày {m_date.group(2)} {months[m_date.group(1)]}'
                continue
            # CG pattern
            if v.endswith(' - Memory Snapshots'):
                char_name = v[:-len(' - Memory Snapshots')].strip()
                vi_char = lookup.get(char_name, char_name)
                lookup[v] = f'{vi_char} - Khoảnh Khắc Hồi Ức'
                continue
            # Skin Default/Awakened pattern
            m_skin = re.match(r'^(.+?):\s*(Default|Awakened)$', v)
            if m_skin:
                char_name, stype = m_skin.group(1).strip(), m_skin.group(2)
                vi_char = lookup.get(char_name, char_name)
                vi_type = 'Mặc Định' if stype == 'Default' else 'Thức Tỉnh'
                lookup[v] = f'{vi_char}: {vi_type}'
                continue
            # Build pattern
            m_bld = re.match(r'^(?:(?P<name>.+?):\s*)?(?P<type>Main Build|Support Build)\s+(?P<num>\d+)$', v)
            if m_bld:
                bname = m_bld.group('name')
                btype = 'Lối Chơi Chính' if m_bld.group('type') == 'Main Build' else 'Lối Chơi Viện Trợ'
                num = m_bld.group('num')
                if bname:
                    vi_bname = lookup.get(bname.strip(), bname.strip())
                    lookup[v] = f'{vi_bname}: {btype} {num}'
                else:
                    lookup[v] = f'{btype} {num}'
                continue

    return lookup

def main():
    print("=" * 70)
    print("Senior Translator 2: Lồng Tiếng & Hồ Sơ Nhân Vật")
    print("=" * 70)

    terms, forbidden = load_master_glossary()
    cache = load_cache()
    print(f"Loaded master glossary ({len(terms)} terms, {len(forbidden)} forbidden rules).")
    print(f"Existing translation cache: {len(cache)} entries.")

    with open(P2_INPUT, "r", encoding="utf-8") as f:
        p2_data = json.load(f)

    total_strings = sum(v["count"] for v in p2_data.values())
    print(f"Total tables: {len(p2_data)}, Total strings: {total_strings}")

    exact_lookup = build_domain_lookup(terms, p2_data)
    print(f"Total domain/glossary exact mappings prepared: {len(exact_lookup)} entries.")

    to_translate = []
    for tbl_name, tbl_info in p2_data.items():
        for str_key, str_val in tbl_info.get("entries", {}).items():
            if not str_val or not str_val.strip():
                continue
            if str_val in exact_lookup:
                cache[str_val] = exact_lookup[str_val]
            elif str_val.lower() in exact_lookup:
                cache[str_val] = exact_lookup[str_val.lower()]
            elif str_val not in cache:
                to_translate.append(str_val)

    unique_to_translate = list(dict.fromkeys(to_translate))
    print(f"Strings to translate: {len(unique_to_translate)} (already cached/exact: {len(cache)})")

    if unique_to_translate:
        batch_size = 25
        print(f"Processing {len(unique_to_translate)} strings in batches of {batch_size}...")
        
        for i in range(0, len(unique_to_translate), batch_size):
            chunk = unique_to_translate[i : i + batch_size]
            shielded_items = []
            tokens_list = []
            
            for txt in chunk:
                s, tok = shield_tokens(txt)
                shielded_items.append(s)
                tokens_list.append(tok)
                
            translated_shielded = translate_batch(shielded_items)
            
            for orig_txt, trans_s, tok in zip(chunk, translated_shielded, tokens_list):
                unshielded = unshield_tokens(trans_s, tok)
                polished = post_process_vietnamese(unshielded, terms, forbidden)
                if not is_valid_token_preservation(orig_txt, polished):
                    polished = post_process_vietnamese(orig_txt, terms, forbidden)
                cache[orig_txt] = polished

            if (i // batch_size) % 5 == 0 or (i + batch_size) >= len(unique_to_translate):
                done_now = min(i + batch_size, len(unique_to_translate))
                print(f"  Translated {done_now}/{len(unique_to_translate)} ({done_now/len(unique_to_translate)*100:.1f}%)")
                save_cache(cache)

        save_cache(cache)
        print("Batch translation complete and saved to cache.")

    translated_p2 = {}
    total_translated = 0
    token_errors = 0

    for tbl_name, tbl_info in p2_data.items():
        translated_entries = {}
        for str_key, str_val in tbl_info.get("entries", {}).items():
            if not str_val or not str_val.strip():
                translated_entries[str_key] = str_val
                continue
            
            trans = cache.get(str_val, str_val)
            trans = post_process_vietnamese(trans, terms, forbidden)
            
            if not is_valid_token_preservation(str_val, trans):
                token_errors += 1
                trans = post_process_vietnamese(str_val, terms, forbidden)
                
            translated_entries[str_key] = trans
            total_translated += 1

        translated_p2[tbl_name] = {
            "file": tbl_info.get("file"),
            "count": len(translated_entries),
            "entries": translated_entries
        }

    with open(P2_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(translated_p2, f, ensure_ascii=False, indent=2)

    print(f"Pillar 2 translation finished: {total_translated} strings, {token_errors} token fallbacks.")
    print(f"Saved to {P2_OUTPUT}")

if __name__ == "__main__":
    main()
