#!/usr/bin/env python3
"""
Senior Translator 3: Cốt Truyện, Nhiệm Vụ Tháp Sao, Đối Thoại, Kỹ Năng & Giao Diện
Dịch 38 bảng (443 chuỗi) thuộc Partition 3 với validator chống dummy cache.
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
    post_process_vietnamese, is_valid_token_preservation
)

INPUT_PATH = ROOT / "work" / "batches" / "partition3_story_quests_ui.json"
OUTPUT_PATH = ROOT / "work" / "batches" / "partition3_translated.json"

def is_valid_translation(orig: str, trans: str) -> bool:
    if not trans or not trans.strip():
        return False
    if orig == trans:
        words = re.findall(r'[a-zA-Z]{2,}', orig)
        has_vi = bool(re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]', trans))
        if len(words) >= 2 and not has_vi:
            return False
    return True

def main():
    print("=" * 70)
    print("Senior Translator 3: Cốt Truyện, Nhiệm Vụ Tháp Sao, Đối Thoại, Kỹ Năng & Giao Diện")
    print("=" * 70)

    terms, forbidden = load_master_glossary()
    cache = load_cache()
    print(f"Loaded master glossary ({len(terms)} terms, {len(forbidden)} forbidden rules).")
    print(f"Existing translation cache: {len(cache)} entries.")

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_strings = sum(v["count"] for v in data.values())
    print(f"Total tables: {len(data)}, Total strings: {total_strings}")

    exact_lookup = {k.lower(): v for k, v in terms.items()}
    exact_lookup.update(terms)

    curated_terms = {
        "!NONEED!": "!NONEED!",
        "!PENDING!": "!PENDING!",
        "BT01": "BT01",
        "BT": "BT",
        "Portia": "Portia",
        "Stella Coin": "Xu Stella",
        "Giao Stella Coin.": "Giao Xu Stella.",
        "The Nimble yet Unbreakable Messenger": "Sứ Giả Nhanh Nhẹn Kiên Cường",
    }
    for k, v in curated_terms.items():
        exact_lookup[k] = v
        exact_lookup[k.lower()] = v

    to_translate = []
    for tbl_name, tbl_info in data.items():
        for str_key, str_val in tbl_info.get("entries", {}).items():
            if not str_val or not str_val.strip():
                continue
            if str_val in exact_lookup:
                cache[str_val] = exact_lookup[str_val]
            elif str_val.lower() in exact_lookup:
                cache[str_val] = exact_lookup[str_val.lower()]
            elif str_val in cache and is_valid_translation(str_val, cache[str_val]):
                continue
            else:
                to_translate.append(str_val)

    unique_to_translate = list(dict.fromkeys(to_translate))
    print(f"Strings to translate via API: {len(unique_to_translate)} (resolved: {len(cache)})")

    if unique_to_translate:
        batch_size = 20
        batches = [unique_to_translate[i : i + batch_size] for i in range(0, len(unique_to_translate), batch_size)]
        print(f"Processing {len(unique_to_translate)} strings across {len(batches)} batches...")

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
                unshielded = unshield_tokens(trans_s, tok)
                polished = post_process_vietnamese(unshielded, terms, forbidden)
                if not is_valid_token_preservation(orig_txt, polished):
                    polished = post_process_vietnamese(orig_txt, terms, forbidden)
                results.append((orig_txt, polished))
            return results

        completed_batches = 0
        with ThreadPoolExecutor(max_workers=5) as executor:
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
        print("Batch translation complete and saved to cache.")

    translated_data = {}
    total_translated = 0
    token_errors = 0

    for tbl_name, tbl_info in data.items():
        translated_entries = {}
        for str_key, str_val in tbl_info.get("entries", {}).items():
            if not str_val or not str_val.strip():
                translated_entries[str_key] = str_val
                continue
            
            trans = cache.get(str_val, str_val)
            trans = post_process_vietnamese(trans, terms, forbidden)
            if str_val.startswith('\x0b') and not trans.startswith('\x0b'):
                trans = '\x0b' + trans
            if str_val.endswith('\x0b') and not trans.endswith('\x0b'):
                trans = trans + '\x0b'
            
            if not is_valid_token_preservation(str_val, trans):
                token_errors += 1
                trans = post_process_vietnamese(str_val, terms, forbidden)
                
            translated_entries[str_key] = trans
            total_translated += 1

        translated_data[tbl_name] = {
            "file": tbl_info.get("file"),
            "category": tbl_info.get("category"),
            "count": len(translated_entries),
            "entries": translated_entries
        }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(translated_data, f, ensure_ascii=False, indent=2)

    print(f"Partition 3 translation finished: {total_translated} strings, {token_errors} token fallbacks.")
    print(f"Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
