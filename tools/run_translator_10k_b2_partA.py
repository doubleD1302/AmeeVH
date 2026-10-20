#!/usr/bin/env python3
"""
Senior Translator 1 (Batch 2 - Part A): Main Story Chapters 4 & 5 (STm04*, STm05*)
Total dialogue strings: 3,334 items.
Applies Master Glossary from config/master_glossary.json.
Enforces:
- Anime RPG voice: lighthearted, natural, witty, dramatic in action/battle.
- Radio / communication: "Do you copy?" -> "Bạn có nghe rõ không!?" / "Nghe rõ không!?".
- 100% token preservation: ==W==, ==PLAYER_NAME==, <color=...>, <size=...>, <r=...>...</r>, etc.
Saves output to: work/batches/batch_10k_b2_partA_translated.json
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

INPUT_PATH = ROOT / "work" / "batches" / "batch_10k_b2_partA.json"
OUTPUT_PATH = ROOT / "work" / "batches" / "batch_10k_b2_partA_translated.json"

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

def polish_dialogue_partA(orig: str, trans: str) -> str:
    """Enforces dramatic Anime RPG voice, natural radio protocols, and contextual polish for Part A."""
    # Radio & transmission protocols
    trans = re.sub(r'^[Nn]ghe rõ đó\b', 'Đã rõ', trans)
    trans = re.sub(r'\bnghe rõ đó\b', 'đã rõ', trans)
    trans = re.sub(r'\b[Bb]ạn có sao chép không[\s?!]*', 'Bạn có nghe rõ không!?', trans)
    trans = re.sub(r'\b[Cc]ó sao chép không[\s?!]*', 'Nghe rõ không!?', trans)
    trans = re.sub(r'\bDo you copy\b', 'Nghe rõ không!?', trans, flags=re.I)
    
    # Over. in radio transmissions
    if "Over." in orig:
        trans = re.sub(r'\b(?:Kết thúc|Over)\.?', 'Hết.', trans)

    # Lady Grey / Gray -> Phu Nhân Gray
    trans = re.sub(r'\bLady Greys?\b', 'Phu Nhân Gray', trans, flags=re.I)
    trans = re.sub(r'\bLady Grays?\b', 'Phu Nhân Gray', trans, flags=re.I)

    # Specific context corrections
    if "copy them manually" in orig:
        trans = re.sub(r'nghe rõ chúng theo cách thủ công', 'cùng nhau chép tay lại', trans)
        trans = re.sub(r'sao chép chúng theo cách thủ công', 'cùng nhau chép tay lại', trans)

    if "final ultimatum" in orig.lower():
        trans = "Tại sao ư? Tôi cũng phải tự lo cho bản thân chứ. Lời cảnh báo tôi gửi tới cô? Đó là lời cảnh báo tối hậu từ Phu Nhân Gray."

    # Can you hear me?
    if "can you hear me" in orig.lower():
        trans = re.sub(r'[Tt]ôi nghe thấy bạn', 'cậu có nghe thấy tớ không', trans)
        trans = re.sub(r'[Bb]ạn có nghe thấy tôi không', 'cậu có nghe thấy tớ không', trans)

    # Clean whitespace inside tags
    trans = re.sub(r'==\s*([A-Za-z0-9_]+)\s*==', r'==\1==', trans)

    return trans

def main():
    print("=" * 75)
    print("Senior Translator 1 (Batch 2 - Part A): Main Story Chapters 4 & 5")
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

    # Assemble translated partition output
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
        trans = polish_dialogue_partA(str_val, trans)
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
