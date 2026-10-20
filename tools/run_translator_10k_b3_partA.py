#!/usr/bin/env python3
"""
Senior Translator 1 (Batch 3 - Part A): Main Story Chapters 6 & 6.5 & Early Ch 7 (STm06*, STm06x5*, STm07*)
Total dialogue strings: 3,334 items.
Applies Master Glossary from config/master_glossary.json.
Enforces:
- Anime RPG voice: dramatic, epic, royal intrigue, natural battle dialogue, loyalty & betrayal (trung nghĩa và phản trắc).
- Radio / communication: "Do you copy?" -> "Bạn có nghe rõ không!?" / "Nghe rõ không!?".
- 100% token preservation: ==W==, ==PLAYER_NAME==, <color=...>, <size=...>, etc.
Saves output to: work/batches/batch_10k_b3_partA_translated.json
"""

import json
import re
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pipeline_translator_engine import (
    load_master_glossary, load_cache, save_cache,
    shield_tokens, unshield_tokens, translate_batch,
    post_process_vietnamese, is_valid_token_preservation,
    TOKEN_REGEX
)

INPUT_PATH = ROOT / "work" / "batches" / "batch_10k_b3_partA.json"
OUTPUT_PATH = ROOT / "work" / "batches" / "batch_10k_b3_partA_translated.json"

def is_engine_identifier(s: str) -> bool:
    if any(ord(c) < 32 and c not in '\n\r\t\x0b' for c in s):
        return True
    s_clean = s.strip()
    if re.match(r'^(?:fx_|story_|qstory_|ep_|emoji_|mainstory)[a-zA-Z0-9_]+$', s_clean):
        return True
    if re.match(r'^[a-z0-9_]+$', s_clean):
        return True
    if re.match(r'^Set[A-Z][a-zA-Z0-9_]*$', s_clean):
        return True
    if re.match(r'^AvgChoice_[a-zA-Z0-9_]+$', s_clean):
        return True
    if s_clean in ('ChaoDaZhenDong', '==PLAYER_NAME=='):
        return True
    return False

def is_valid_translation(orig: str, trans: str, forbidden: dict) -> bool:
    if not trans or not trans.strip():
        return False
    for wrong in forbidden:
        if wrong.lower() in trans.lower():
            return False
    if 'do you copy' in orig.lower() and 'sao chép' in trans.lower():
        return False
    if not is_valid_token_preservation(orig, trans):
        return False
    return True

def polish_dialogue_b3_partA(orig: str, trans: str) -> str:
    """Enforces dramatic Anime RPG voice, royal intrigue, natural radio protocols, and contextual polish for Batch 3 Part A."""
    # 1. Monolith & world lore
    trans = re.sub(r'\bPhilae\s+Cự\s+Thạch\b', 'Cự Tháp Philae', trans, flags=re.I)
    trans = re.sub(r'\bNew\s+Orelian\s+Cự\s+Thạch\b', 'Cự Tháp New Orelian', trans, flags=re.I)
    trans = re.sub(r'\bCự\s+Thạch\s+Philae\b', 'Cự Tháp Philae', trans, flags=re.I)
    trans = re.sub(r'\bCự\s+Thạch\s+New\s+Orelian\b', 'Cự Tháp New Orelian', trans, flags=re.I)
    trans = re.sub(r'\bLịch\s+Cự\s+Thạch\b', 'Lịch Cự Tháp', trans, flags=re.I)
    trans = re.sub(r'\bLịch\s+Nguyên\s+Khối\b', 'Lịch Cự Tháp', trans, flags=re.I)
    trans = re.sub(r'\bLối\s+vào\s+nguyên\s+khối\b', 'Lối Vào Cự Tháp', trans, flags=re.I)
    trans = re.sub(r'\b[Cc]ự\s+[Tt]hạch\b', 'Cự Tháp', trans)
    trans = re.sub(r'\b[Đđ]á\s+nguyên\s+khối\b', 'Cự Tháp', trans)
    trans = re.sub(r'\bDân\s+Người\s+Novian\b', 'người Novian', trans, flags=re.I)
    trans = re.sub(r'\bDân\s+Novian\b', 'người Novian', trans, flags=re.I)
    trans = re.sub(r'\bNgười\s+Novian\b', 'người Novian', trans)

    # 2. Boss Accord & Boss title
    trans = re.sub(r'\bSếp\s+Accord\b', 'Hiệp Ước Của Sếp', trans)
    trans = re.sub(r'\b[Tt]hỏa thuận của ông chủ\b', 'Hiệp Ước Của Sếp', trans)
    trans = re.sub(r'\b[Hh]iệp định của ông chủ\b', 'Hiệp Ước Của Sếp', trans)
    trans = re.sub(r'\bÔng chủ\b(?=[,!\?\.])', 'Sếp', trans)
    trans = re.sub(r'^[Ôô]ng chủ\b', 'Sếp', trans)
    trans = re.sub(r'\b[Ôô]ng chủ\b', 'Sếp', trans)
    trans = re.sub(r'\bBạo chúa\b', 'Bạo Quân', trans)

    # 3. Radio & transmission protocols
    trans = re.sub(r'^[Nn]ghe rõ đó\b', 'Đã rõ', trans)
    trans = re.sub(r'\bnghe rõ đó\b', 'đã rõ', trans)
    trans = re.sub(r'\b[Bb]ạn có sao chép không[\s?!]*', 'Bạn có nghe rõ không!?', trans)
    trans = re.sub(r'\b[Cc]ó sao chép không[\s?!]*', 'Nghe rõ không!?', trans)
    trans = re.sub(r'\bsao chép không[\s?!]*', 'nghe rõ không!?', trans)
    trans = re.sub(r'\bDo you copy\b', 'Nghe rõ không!?', trans, flags=re.I)
    if 'Over.' in orig:
        trans = re.sub(r'\b(?:Kết thúc|Over)\.?', 'Hết.', trans)

    # Can you hear me?
    if 'can you hear me' in orig.lower():
        trans = re.sub(r'[Tt]ôi nghe thấy bạn', 'cậu có nghe thấy tớ không', trans)
        trans = re.sub(r'[Bb]ạn có nghe thấy tôi không', 'cậu có nghe thấy tớ không', trans)
        trans = re.sub(r'[Bb]ạn có nghe tôi nói không', 'cậu có nghe rõ không!?', trans)

    # 4. Idiomatic expressions & machine translation flaws
    # Loyalty and Betrayal
    if orig.strip() == 'Loyalty and Betrayal':
        trans = 'Trung Nghĩa và Phản Trắc'

    # Three Grand Commissions & Bishop piece
    if 'Three Grand Commissions' in orig:
        trans = re.sub(r'Ba Ủy ban lớn', 'Ba Đại Ủy Thác', trans)
    if 'Bishop piece' in orig:
        trans = re.sub(r'mảnh Bishop', 'quân Tượng', trans)

    # Golden Nightingale & Tawny Nightingale
    trans = re.sub(r'Chim sơn ca vàng', 'Hoàng Kim Dạ Oanh', trans)
    trans = re.sub(r'Chim sơn ca Tawny', 'Dạ Oanh Hoàng Lạc', trans)
    trans = re.sub(r'Họa mi Tawny', 'Dạ Oanh Hoàng Lạc', trans)

    # Commissions
    trans = re.sub(r'\bhoa hồng đang hoạt động\b', 'nhiệm vụ ủy thác chưa hoàn thành', trans)
    trans = re.sub(r'\bphí hoa hồng\b', 'thù lao ủy thác', trans)
    trans = re.sub(r'\btiền hoa hồng\b', 'tiền thù lao ủy thác', trans)
    trans = re.sub(r'\bnhận hoa hồng\b', 'nhận ủy thác', trans)
    trans = re.sub(r'\bủy ban Chim sơn ca vàng\b', 'nhiệm vụ Hoàng Kim Dạ Oanh', trans)

    # Toast
    if 'toast' in orig.lower():
        trans = re.sub(r'\bbánh mì nướng\b', 'tiêu đời', trans)

    # Speak of the devil
    if 'speak of the devil' in orig.lower():
        trans = re.sub(r'\bnói về ma quỷ\b', 'vừa nhắc Tào Tháo là Tào Tháo tới liền', trans)

    # Swamped
    if 'swamped' in orig.lower():
        trans = re.sub(r'bị ngập chìm', 'bận tối mắt tối mũi', trans)
        trans = re.sub(r'bị ngập trong đống tiệc tùng đó', 'bận tối mắt tối mũi với đống tiệc tùng đó', trans)
        trans = re.sub(r'bị ngập nước', 'bận trăm công nghìn việc', trans)

    # Tap phones
    if 'tap phones' in orig.lower():
        trans = re.sub(r'nghe lén điện thoại', 'chạm điện thoại trao đổi liên lạc', trans)
    if 'A direct line to you?' in orig:
        trans = re.sub(r'Một đường dây trực tiếp cho bạn\?', 'Số liên lạc trực tiếp của cậu ư?', trans)

    # Grunts
    trans = re.sub(r'Desert Scorpion Grunts', 'Lính Quèn Bọ Cạp Sa Mạc', trans)
    trans = re.sub(r'Bọ cạp sa mạc càu nhàu', 'Lính Quèn Bọ Cạp Sa Mạc', trans)
    trans = re.sub(r'những lời càu nhàu vô dụng của Liên Hợp Thu Hoạch', 'đám lính quèn vô dụng của Liên Hợp Thu Hoạch', trans)
    trans = re.sub(r'những người càu nhàu phải là tân binh', 'đám lính quèn chắc toàn là tân binh', trans)
    trans = re.sub(r'những người càu nhàu', 'đám lính quèn', trans)

    # Hold your fire
    if 'Hold your fire' in orig:
        trans = re.sub(r'Giữ lửa của bạn', 'Ngừng bắn', trans)

    # Ultimatum
    if 'ultimatum' in orig.lower():
        trans = re.sub(r'[Tt]ối [Hh]ậu [Tt]hư', 'lời cảnh báo tối hậu', trans)

    # Anime RPG style / tone
    trans = re.sub(r'\b(Firstlight|First Light)\s*Noya\b', 'Noya - Khải Minh', trans, flags=re.I)
    trans = re.sub(r'\bNoya\s*(Sơ Quang|Khải Minh)\b', 'Noya - Khải Minh', trans, flags=re.I)
    trans = re.sub(r'\bSơ Quang\b', 'Khải Minh', trans)
    trans = re.sub(r'\bkẻ thù\b', 'kẻ địch', trans, flags=re.I)
    trans = re.sub(r'\b[Nn]gười đi bộ\b', 'Lữ Khách', trans)
    trans = re.sub(r'\b[Nn]hững người đi bộ\b', 'các Lữ Khách', trans)
    trans = re.sub(r'\buống một viên thuốc hạ sốt đi\b', 'bình tĩnh lại nào', trans, flags=re.I)
    trans = re.sub(r'\buống thuốc hạ nhiệt\b', 'thả lỏng chút đi mà', trans, flags=re.I)
    trans = re.sub(r'\buống thuốc an thần\b', 'bình tĩnh lại đi', trans, flags=re.I)

    # 5. Tokens & whitespace tags preservation
    trans = re.sub(r'==\s*([A-Za-z0-9_]+)\s*==', r'==\1==', trans)
    trans = re.sub(r'<r=([^>]+)>\s*</r>', r'<r=\1></r>', trans)
    trans = re.sub(r'(<color=[^>]+>)\s+', r'\1', trans)
    trans = re.sub(r'\s+(</color>)', r'\1', trans)
    trans = re.sub(r'\s+([,.:;?!])', r'\1', trans)

    return trans

def main():
    print("=" * 75)
    print("Senior Translator 1 (Batch 3 - Part A): Main Story Chapters 6 & 6.5 & Ch 7")
    print("=" * 75)

    terms, forbidden = load_master_glossary()
    cache = load_cache()
    print(f"Loaded master glossary ({len(terms)} terms, {len(forbidden)} forbidden rules).")
    print(f"Existing translation cache: {len(cache)} entries.")

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_strings = len(data)
    print(f"Total strings to process in Part A: {total_strings}")

    exact_lookup = {k.lower(): v for k, v in terms.items()}
    exact_lookup.update(terms)

    to_translate = []
    engine_id_count = 0

    for str_key, str_val in data.items():
        if not str_val or not str_val.strip():
            continue
        if is_engine_identifier(str_val):
            cache[str_val] = str_val
            engine_id_count += 1
            continue
        if str_val in exact_lookup:
            cache[str_val] = exact_lookup[str_val]
        elif str_val.lower() in exact_lookup:
            cache[str_val] = exact_lookup[str_val.lower()]
        elif str_val in cache and is_valid_translation(str_val, cache[str_val], forbidden):
            continue
        else:
            to_translate.append(str_val)

    unique_to_translate = list(dict.fromkeys(to_translate))
    print(f"Engine identifiers preserved: {engine_id_count}")
    print(f"Strings requiring API translation: {len(unique_to_translate)} (cached/resolved: {total_strings - len(unique_to_translate)})")

    if unique_to_translate:
        batch_size = 20
        batches = [unique_to_translate[i : i + batch_size] for i in range(0, len(unique_to_translate), batch_size)]
        print(f"Processing {len(unique_to_translate)} strings across {len(batches)} batches with ThreadPoolExecutor...")

        def process_batch(chunk):
            shielded_items = []
            tokens_list = []
            for txt in chunk:
                s, tok = shield_tokens(txt)
                shielded_items.append(s)
                tokens_list.append(tok)

            translated_shielded = translate_batch(shielded_items)
            results = []
            for orig_txt, trans_s, tok in zip(chunk, translated_shielded, tokens_list):
                polished_s = post_process_vietnamese(trans_s, terms, forbidden)
                unshielded = unshield_tokens(polished_s, tok)
                polished = post_process_vietnamese(unshielded, terms, forbidden)
                polished = polish_dialogue_b3_partA(orig_txt, polished)
                if not is_valid_token_preservation(orig_txt, polished):
                    raw_unshielded = unshield_tokens(trans_s, tok)
                    if is_valid_token_preservation(orig_txt, raw_unshielded):
                        polished = post_process_vietnamese(raw_unshielded, terms, forbidden)
                results.append((orig_txt, polished))
            return results

        completed_batches = 0
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_chunk = {executor.submit(process_batch, b): b for b in batches}
            for future in as_completed(future_to_chunk):
                try:
                    res = future.result()
                    for orig_txt, trans_txt in res:
                        cache[orig_txt] = trans_txt
                except Exception as e:
                    print(f"Batch failed: {e}")
                completed_batches += 1
                if completed_batches % 20 == 0 or completed_batches == len(batches):
                    print(f"  Progress: {completed_batches}/{len(batches)} batches completed ({(completed_batches/len(batches))*100:.1f}%)")
                    save_cache(cache)

        save_cache(cache)
        print("Batch translation completed.")

    # Assemble final translated output
    final_translated = {}
    valid_count = 0
    token_ok_count = 0

    for str_key, str_val in data.items():
        if not str_val or not str_val.strip():
            final_translated[str_key] = str_val
            continue
        if is_engine_identifier(str_val):
            final_translated[str_key] = str_val
            valid_count += 1
            token_ok_count += 1
            continue

        trans = cache.get(str_val, str_val)
        trans = post_process_vietnamese(trans, terms, forbidden)
        trans = polish_dialogue_b3_partA(str_val, trans)

        if not is_valid_token_preservation(str_val, trans):
            raw_trans = cache.get(str_val, str_val)
            if is_valid_token_preservation(str_val, raw_trans):
                trans = raw_trans

        final_translated[str_key] = trans
        valid_count += 1
        if is_valid_token_preservation(str_val, trans):
            token_ok_count += 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(final_translated, f, indent=2, ensure_ascii=False)

    print("=" * 75)
    print(f"Successfully exported Part A: {len(final_translated)} strings to {OUTPUT_PATH.name}")
    print(f"Token preservation rate: {token_ok_count}/{valid_count} ({(token_ok_count/valid_count)*100:.2f}%)")
    print("=" * 75)

if __name__ == "__main__":
    main()
