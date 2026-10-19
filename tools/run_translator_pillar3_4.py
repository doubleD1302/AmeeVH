#!/usr/bin/env python3
"""
Senior Translator 3: Cốt Truyện Phụ, Đối Thoại Hẹn Hò, Nhiệm Vụ & Hệ Thống Phụ, Gacha, Cửa Hàng (Pillars 3 & 4)
Translates 105 tables (5,869 strings) with high-speed batching, 100% token preservation & Master Glossary enforcement.
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
    post_process_vietnamese, is_valid_token_preservation,
    fix_token_edges
)

P3_INPUT = ROOT / "work" / "batches" / "pillar3_story_dating_quests.json"
P3_OUTPUT = ROOT / "work" / "batches" / "pillar3_translated.json"

P4_INPUT = ROOT / "work" / "batches" / "pillar4_system_gacha_shops.json"
P4_OUTPUT = ROOT / "work" / "batches" / "pillar4_translated.json"

def process_pillar(input_path, output_path, pillar_title, terms, forbidden, cache):
    print("=" * 70)
    print(f"Senior Translator 3: {pillar_title}")
    print("=" * 70)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_strings = sum(v["count"] for v in data.values())
    print(f"Total tables: {len(data)}, Total strings: {total_strings}")

    exact_lookup = {k.lower(): v for k, v in terms.items()}
    exact_lookup.update(terms)

    to_translate = []
    for tbl_name, tbl_info in data.items():
        for str_key, str_val in tbl_info.get("entries", {}).items():
            if not str_val or not str_val.strip():
                continue
            if tbl_name == "DiscIP" or any(u'\u00C0' <= ch <= u'\u1EF9' for ch in str_val):
                cache[str_val] = str_val
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
                polished = fix_token_edges(orig_txt, polished)
                if not is_valid_token_preservation(orig_txt, polished):
                    polished = fix_token_edges(orig_txt, post_process_vietnamese(orig_txt, terms, forbidden))
                cache[orig_txt] = polished

            if (i // batch_size) % 10 == 0 or (i + batch_size) >= len(unique_to_translate):
                print(f"  Translated {min(i + batch_size, len(unique_to_translate))}/{len(unique_to_translate)} ({min(i + batch_size, len(unique_to_translate))/len(unique_to_translate)*100:.1f}%)")
                save_cache(cache)

        save_cache(cache)

    translated_data = {}
    total_translated = 0
    token_errors = 0

    for tbl_name, tbl_info in data.items():
        translated_entries = {}
        for str_key, str_val in tbl_info.get("entries", {}).items():
            if not str_val or not str_val.strip():
                translated_entries[str_key] = str_val
                continue
            
            if tbl_name == "DiscIP":
                translated_entries[str_key] = str_val
                total_translated += 1
                continue

            trans = cache.get(str_val, str_val)
            trans = post_process_vietnamese(trans, terms, forbidden)
            trans = fix_token_edges(str_val, trans)
            
            if not is_valid_token_preservation(str_val, trans):
                token_errors += 1
                trans = fix_token_edges(str_val, post_process_vietnamese(str_val, terms, forbidden))
                
            translated_entries[str_key] = trans
            total_translated += 1

        translated_data[tbl_name] = {
            "file": tbl_info.get("file"),
            "count": len(translated_entries),
            "entries": translated_entries
        }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(translated_data, f, ensure_ascii=False, indent=2)

    print(f"{pillar_title} translation finished: {total_translated} strings, {token_errors} token fallbacks.")
    print(f"Saved to {output_path}")

def main():
    terms, forbidden = load_master_glossary()
    cache = load_cache()
    print(f"Loaded master glossary ({len(terms)} terms, {len(forbidden)} forbidden rules).")
    
    process_pillar(P3_INPUT, P3_OUTPUT, "Pillar 3: Cốt Truyện Phụ & Hẹn Hò", terms, forbidden, cache)
    process_pillar(P4_INPUT, P4_OUTPUT, "Pillar 4: Hệ Thống Phụ, Gacha & Cửa Hàng", terms, forbidden, cache)

if __name__ == "__main__":
    main()
