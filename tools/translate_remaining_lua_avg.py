# -*- coding: utf-8 -*-
"""
Phase 2: Translate & Polish all remaining unique dialogue strings in Lua AVG files (20,601 strings).
Uses pipeline_translator_engine with multi-threaded batch translation, domain rotation,
persistent disk cache, and de-formalization post-processing.
"""

import json
from pathlib import Path
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))

from test_lua_roundtrip import Lua53Chunk
from pipeline_translator_engine import translate_batch
from deformalize_text import deformalize_text

CACHE_FILE = ROOT / "work" / "batches" / "remaining_lua_avg_cache.json"
OUTPUT_FILE = ROOT / "work" / "batches" / "dialogue_remaining_avg_approved.json"

def extract_strings_from_proto(pr):
    res = []
    for ktype, val in pr['constants']:
        if ktype in (4, 20):
            tag, s_bytes = val
            try:
                s = s_bytes.decode('utf-8')
                res.append(s)
            except Exception:
                pass
    for child in pr['protos']:
        res.extend(extract_strings_from_proto(child))
    return res

def is_genuine_dialogue(s: str) -> bool:
    s_strip = s.strip()
    if len(s_strip) < 2 or not any(c.isalpha() for c in s_strip):
        return False
    # Skip engine IDs, file paths, tags
    prefixes = (
        'Game/', 'vo_', 'emoji_', 'Avg', 'ep_', 'item_', 'icon_', 'eff_', 'btn_',
        'bgm_', 'bgs_', 'fx_', 'story_', 'qstory_', 'city_', 'hotel_', 'wog_',
        'luckyoasis_', 'Set', 'Play', 'res_', 'prefab_', 'spine_', 'ttc_',
        'img_', 'tex_', 'snd_', 'cam_', 'ui_', 'tiao2', 'xingshi', 'lengzhan'
    )
    if s_strip.startswith(prefixes):
        return False
    if s_strip in ('SetGroupId', 'SetBubbleUIType', 'SetBubble', 'SetTalk', 'SetBg',
                   'SetBgm', 'PlayVoice', 'PlaySound', 'SetCamera', 'SetTransition',
                   'SetWait', 'True', 'False', 'SetPhoneMsg', 'SetPhoneMsgChoiceBegin',
                   'SetPhoneMsgChoiceJumpTo', 'SetPhoneMsgChoiceEnd', 'cmd', 'param'):
        return False
    # Single identifier without space or punctuation
    if re.match(r'^[a-zA-Z0-9_]+$', s_strip) and ' ' not in s_strip:
        return False
    return ' ' in s_strip or len(s_strip) > 12

import re

def main():
    # 1. Load existing approved dictionaries to avoid re-translating
    batches = [
        "batch_10000_avg_clean.json", "batch_10000_avg_clean_b2.json",
        "batch_10000_avg_clean_b3.json", "batch_10000_avg_clean_b4.json"
    ]
    appr_batches = [
        "batch_10k_approved.json", "batch_10k_b2_approved.json",
        "batch_10k_b3_approved.json", "batch_10k_b4_approved.json"
    ]

    master_en_to_vi = {}
    for en_f, vi_f in zip(batches, appr_batches):
        en_p = ROOT / "work" / "batches" / en_f
        vi_p = ROOT / "work" / "batches" / vi_f
        if en_p.exists() and vi_p.exists():
            en_d = json.load(open(en_p, encoding="utf-8"))
            vi_d = json.load(open(vi_p, encoding="utf-8"))
            for k, en in en_d.items():
                if k in vi_d:
                    master_en_to_vi[en.strip()] = vi_d[k].strip()

    print(f"Loaded {len(master_en_to_vi)} existing translated pairs from batches 1-4.")

    # 2. Load cache if exists
    cache = {}
    if CACHE_FILE.exists():
        try:
            cache = json.load(open(CACHE_FILE, encoding="utf-8"))
            print(f"Loaded {len(cache)} cached items.")
        except Exception:
            pass

    # 3. Extract all strings from all 626 files
    mapping = json.load(open(ROOT / "work" / "research" / "avg_file_to_entry.json", encoding="utf-8"))
    lua_dir = ROOT / "work" / "research" / "lua_tree" / "Game" / "UI" / "Avg" / "_en" / "Config"

    needed_to_translate = set()
    for fname in mapping:
        p = lua_dir / fname
        if not p.exists():
            continue
        try:
            raw = p.read_bytes()
            chunk = Lua53Chunk(raw)
            chunk.read_bytes(34)
            proto = chunk.parse_proto()
            all_s = extract_strings_from_proto(proto)
            for s in all_s:
                s_strip = s.strip()
                if is_genuine_dialogue(s_strip):
                    if s_strip not in master_en_to_vi and s_strip not in cache:
                        needed_to_translate.add(s_strip)
        except Exception as e:
            print(f"Error parsing {fname}: {e}")

    needed_list = sorted(needed_to_translate)
    print(f"Total unique strings requiring translation: {len(needed_list)}")

    if not needed_list:
        print("All strings already translated and cached!")
    else:
        # 4. Batch translate with ThreadPoolExecutor
        batch_size = 50
        batches_list = [needed_list[i : i + batch_size] for i in range(0, len(needed_list), batch_size)]
        print(f"Starting translation of {len(needed_list)} strings in {len(batches_list)} batches...")

        def process_batch(b):
            res = translate_batch(b)
            return list(zip(b, res))

        completed = 0
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=6) as executor:
            future_to_batch = {executor.submit(process_batch, b): b for b in batches_list}
            for fut in as_completed(future_to_batch):
                try:
                    pairs = fut.result()
                    for en, vi in pairs:
                        # De-formalize and polish into lively anime style
                        vi_polished = deformalize_text(vi)
                        cache[en] = vi_polished
                    completed += len(pairs)
                    if completed % 500 < batch_size or completed == len(needed_list):
                        elapsed = time.time() - t0
                        speed = completed / elapsed if elapsed > 0 else 0
                        print(f"Progress: {completed}/{len(needed_list)} ({completed/len(needed_list)*100:.1f}%) - {speed:.1f} strings/sec")
                        # Periodic save
                        with open(CACHE_FILE, "w", encoding="utf-8") as f:
                            json.dump(cache, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    print(f"Batch error: {e}")

        # Final cache save
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        print("Completed all translations and saved to cache!")

    # 5. Build full approved remaining output
    output_dict = {}
    for en, vi in cache.items():
        output_dict[en] = deformalize_text(vi)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_dict, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(output_dict)} items to {OUTPUT_FILE}!")

if __name__ == "__main__":
    main()
