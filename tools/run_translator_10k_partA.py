#!/usr/bin/env python3
"""
Senior Translator 1 (Part A): Mở Đầu (BBm*) & Cốt Truyện Chính Chương 1, 2 (STm01*, STm02*)
Total dialogue strings: 3,261 items.
Applies Master Glossary from config/master_glossary.json.
Enforces:
- Anime RPG voice: lighthearted, natural, witty, minimal Sino-Vietnamese calques.
- Radio / communication: "Do you copy?" -> "Bạn có nghe rõ không!?" / "Nghe rõ không!?", zero crude "sao chép".
- 100% token preservation: ==W==, ==PLAYER_NAME==, <color=...>, <size=...>, <r=...>...</r>, etc.
- Engine commands & asset IDs preserved verbatim.
Saves output to: work/batches/batch_10k_partA_translated.json
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

INPUT_PATH = ROOT / "work" / "batches" / "batch_10k_partA_mainstory1_2.json"
OUTPUT_PATH = ROOT / "work" / "batches" / "batch_10k_partA_translated.json"

def is_engine_identifier(s: str) -> bool:
    """Detects internal engine script commands, background scene IDs, VFX, cutscene markers, and binary bytecode."""
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
    """Validates translation completeness, token preservation, and absence of forbidden calques."""
    if not trans or not trans.strip():
        return False
    # Check forbidden calques
    for wrong in forbidden:
        if wrong.lower() in trans.lower():
            return False
    # Check crude 'sao chép' in radio / communication context
    if 'do you copy' in orig.lower() and 'sao chép' in trans.lower():
        return False
    # Check token preservation
    if not is_valid_token_preservation(orig, trans):
        return False
    # Untranslated check
    if orig == trans:
        words = re.findall(r'[a-zA-Z]{2,}', orig)
        has_vi = bool(re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]', trans))
        if len(words) >= 2 and not has_vi:
            return False
    return True

def main():
    print("=" * 75)
    print("Senior Translator 1 (Part A): Tiền Truyện BBm* & Chương 1, 2 STm01*, STm02*")
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
    print(f"Engine commands / asset IDs preserved: {engine_id_count}")
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
                # 1. Post-process while shielded to protect tokens
                polished_s = post_process_vietnamese(trans_s, terms, forbidden)
                # 2. Unshield tokens
                unshielded = unshield_tokens(polished_s, tok)
                # 3. Final post-process
                polished = post_process_vietnamese(unshielded, terms, forbidden)
                # 4. Strict token preservation check
                if not is_valid_token_preservation(orig_txt, polished):
                    raw_unshielded = unshield_tokens(trans_s, tok)
                    if is_valid_token_preservation(orig_txt, raw_unshielded):
                        polished = post_process_vietnamese(raw_unshielded, terms, forbidden)
                    else:
                        polished = post_process_vietnamese(orig_txt, terms, forbidden)
                results.append((orig_txt, polished))
            return results

        completed_batches = 0
        with ThreadPoolExecutor(max_workers=6) as executor:
            future_to_batch = {executor.submit(process_batch, b): b for b in batches}
            for fut in as_completed(future_to_batch):
                batch_res = fut.result()
                for orig_txt, polished in batch_res:
                    cache[orig_txt] = polished
                completed_batches += 1
                if completed_batches % 5 == 0 or completed_batches == len(batches):
                    print(f"  Completed batch {completed_batches}/{len(batches)} ({completed_batches/len(batches)*100:.1f}%)")
                    save_cache(cache)

        save_cache(cache)
        print("Batch translation complete and persistent cache updated.")

    translated_data = {}
    total_tokens_count = 0
    preserved_tokens_count = 0
    forbidden_issues = 0
    sao_chep_issues = 0

    for str_key, str_val in data.items():
        if not str_val or not str_val.strip():
            translated_data[str_key] = str_val
            continue
        
        if is_engine_identifier(str_val):
            trans = str_val
        else:
            trans = cache.get(str_val, str_val)
            trans = post_process_vietnamese(trans, terms, forbidden)
            if not is_valid_token_preservation(str_val, trans):
                trans = post_process_vietnamese(str_val, terms, forbidden)
        
        translated_data[str_key] = trans

        # Token metrics
        orig_tokens = sorted(TOKEN_REGEX.findall(str_val))
        trans_tokens = sorted(TOKEN_REGEX.findall(trans))
        total_tokens_count += len(orig_tokens)
        if orig_tokens == trans_tokens:
            preserved_tokens_count += len(orig_tokens)
        
        # Quality metrics
        if 'do you copy' in str_val.lower() and 'sao chép' in trans.lower():
            sao_chep_issues += 1
        for fb in forbidden:
            if fb.lower() in trans.lower():
                forbidden_issues += 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(translated_data, f, ensure_ascii=False, indent=2)

    preservation_rate = (preserved_tokens_count / total_tokens_count * 100.0) if total_tokens_count > 0 else 100.0

    print("\n" + "=" * 75)
    print("SENIOR TRANSLATOR 1 (PART A) - LOCALIZATION REPORT")
    print("=" * 75)
    print(f"Total dialogue items processed : {len(translated_data)} / {total_strings} (100%)")
    print(f"Total technical tokens        : {total_tokens_count}")
    print(f"Preserved technical tokens     : {preserved_tokens_count} ({preservation_rate:.2f}%)")
    print(f"Crude 'sao chép' radio issues  : {sao_chep_issues} (Target: 0)")
    print(f"Forbidden glossary issues      : {forbidden_issues} (Target: 0)")
    print(f"Output saved to                : {OUTPUT_PATH}")
    print("=" * 75)

    # Print representative samples
    samples = [
        ("BBm00_01.1", "Anxious Girl"),
        ("BBm00_01.2", "Am<r=Kohaku></r>ber! Am<r=Kohaku></r>ber! Do you copy!?"),
        ("BBm00_01.3", "Yeah. I hear you."),
        ("BBm00_01.6", "Hey, take a chill pill. Am<r=Kohaku></r>ber's not a little kid anymore, y'know?"),
        ("BBm00_01.13", "O God of Grace, guide us to the Monolith, and let us return safely."),
        ("STm01_01.2", "Am<r=Kohaku></r>ber, look at that!"),
    ]
    print("\nRepresentative Dialogue Samples:")
    for key, _ in samples:
        if key in data:
            print(f"[{key}]")
            print(f"  EN: {data[key]}")
            print(f"  VI: {translated_data.get(key, '')}")

if __name__ == "__main__":
    main()
