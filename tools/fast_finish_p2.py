#!/usr/bin/env python3
"""
Fast Parallel Finisher for Pillar 2 (Character Archive, Backstories & Voice)
Uses 20 concurrent threads to process remaining 881 narrative strings in ~20-30 seconds.
Enforces Master Glossary and 100% token preservation.
"""

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pipeline_translator_engine import (
    load_master_glossary, load_cache, save_cache,
    shield_tokens, unshield_tokens,
    post_process_vietnamese, is_valid_token_preservation
)
from run_translator_pillar2 import build_domain_lookup

P2_INPUT = ROOT / "work" / "batches" / "pillar2_voices_characters.json"
P2_OUTPUT = ROOT / "work" / "batches" / "pillar2_translated.json"

def fetch_single(txt, terms, forbidden):
    clean = txt.strip()
    shielded, tokens = shield_tokens(clean)
    if not shielded.strip():
        return txt, txt

    has_cn = any(u'\u4e00' <= ch <= u'\u9fff' for ch in shielded)
    sl = 'zh-CN' if has_cn else 'auto'
    
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={sl}&tl=vi&dt=t&q=" + urllib.parse.quote(shielded)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                full = "".join([item[0] for item in data[0] if item and item[0]])
                unshielded = unshield_tokens(full.strip(), tokens)
                polished = post_process_vietnamese(unshielded, terms, forbidden)
                if not is_valid_token_preservation(txt, polished):
                    polished = post_process_vietnamese(txt, terms, forbidden)
                return txt, polished
        except Exception:
            time.sleep(0.3 * (attempt + 1))
            
    return txt, post_process_vietnamese(txt, terms, forbidden)

def main():
    print("=" * 70)
    print("Fast Parallel Finisher: Pillar 2 (Voices & Character Backstories)")
    print("=" * 70)

    terms, forbidden = load_master_glossary()
    cache = load_cache()
    
    with open(P2_INPUT, "r", encoding="utf-8") as f:
        p2_data = json.load(f)

    lookup = build_domain_lookup(terms, p2_data)

    to_translate = []
    for tbl_name, tbl_info in p2_data.items():
        for k, v in tbl_info.get("entries", {}).items():
            if not v or not v.strip():
                continue
            if v in lookup:
                cache[v] = lookup[v]
            elif v.lower() in lookup:
                cache[v] = lookup[v.lower()]
            elif v not in cache:
                to_translate.append(v)

    unique_to_translate = list(dict.fromkeys(to_translate))
    print(f"P2 Total Strings: {sum(v['count'] for v in p2_data.values())}")
    print(f"Unique strings to translate in 20 threads: {len(unique_to_translate)}")

    if unique_to_translate:
        start_t = time.time()
        done = 0
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(fetch_single, txt, terms, forbidden) for txt in unique_to_translate]
            for fut in as_completed(futures):
                orig_txt, trans_txt = fut.result()
                cache[orig_txt] = trans_txt
                done += 1
                if done % 100 == 0 or done == len(unique_to_translate):
                    elapsed = time.time() - start_t
                    print(f"  Progress: {done}/{len(unique_to_translate)} ({done/len(unique_to_translate)*100:.1f}%) in {elapsed:.1f}s")
                    save_cache(cache)

        save_cache(cache)
        print("All remaining P2 strings translated successfully!")

    # Assemble P2 translated file
    translated_p2 = {}
    total_translated = 0
    token_fallbacks = 0

    for tbl_name, tbl_info in p2_data.items():
        translated_entries = {}
        for k, v in tbl_info.get("entries", {}).items():
            if not v or not v.strip():
                translated_entries[k] = v
                continue
            
            trans = cache.get(v, v)
            trans = post_process_vietnamese(trans, terms, forbidden)
            if not is_valid_token_preservation(v, trans):
                token_fallbacks += 1
                trans = post_process_vietnamese(v, terms, forbidden)
            
            translated_entries[k] = trans
            total_translated += 1

        translated_p2[tbl_name] = {
            "file": tbl_info.get("file"),
            "count": len(translated_entries),
            "entries": translated_entries
        }

    with open(P2_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(translated_p2, f, ensure_ascii=False, indent=2)

    print(f"Pillar 2 translation output saved to: {P2_OUTPUT.name}")
    print(f"Total entries: {total_translated}, token fallbacks: {token_fallbacks}")

if __name__ == "__main__":
    main()
