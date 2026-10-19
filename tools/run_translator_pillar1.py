#!/usr/bin/env python3
"""
Senior Translator 1: Màn Chơi, Dungeon, Tháp Sao & Quái Vật (Pillar 1)
Translates 83 tables (9,535 strings) with high-speed batching, 100% token preservation & master glossary enforcement.
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

P1_INPUT = ROOT / "work" / "batches" / "pillar1_dungeons_monsters.json"
P1_OUTPUT = ROOT / "work" / "batches" / "pillar1_translated.json"

def main():
    print("=" * 70)
    print("Senior Translator 1: Màn Chơi, Dungeon, Tháp Sao & Quái Vật")
    print("=" * 70)

    terms, forbidden = load_master_glossary()
    cache = load_cache()
    print(f"Loaded master glossary ({len(terms)} terms, {len(forbidden)} forbidden rules).")
    print(f"Existing translation cache: {len(cache)} entries.")

    with open(P1_INPUT, "r", encoding="utf-8") as f:
        p1_data = json.load(f)

    total_strings = sum(v["count"] for v in p1_data.values())
    print(f"Total tables: {len(p1_data)}, Total strings: {total_strings}")

    exact_lookup = {k.lower(): v for k, v in terms.items()}
    exact_lookup.update(terms)

    # Curated monster additions from Pillar 1 survey
    curated_p1_terms = {
        "Berry Cauldron Hammer": "Búa Nồi Quả Mọng",
        "Brave Treasure Hunter": "Kẻ Săn Kho Báu Dũng Cảm",
        "Chaton ???": "Mắt Mèo ???",
        "Cheerful Treasure Hunter": "Kẻ Săn Kho Báu Hoạt Bát",
        "Corrupted Wind Chime": "Chuông Gió Bị Xâm Thực",
        "Creamy Sweet Soup Pot": "Nồi Súp Kem Ngọt",
        "Dazzling Wing": "Cánh Lấp Lánh",
        "Desert Scorpion: Crimson Sand Swordsman": "Bọ Cạp Sa Mạc: Kiếm Sĩ Xích Sa",
        "Desert Scorpion: Dust Crossbowman": "Bọ Cạp Sa Mạc: Nỏ Vệ Hoàng Trần",
        "Firefly ???": "Đom Đóm ???",
        "Fresh Treasure Hunter": "Kẻ Săn Kho Báu Tươi Tắn",
        "Frosting Grumblegeist": "Quái Băng Đường Dudulu",
        "Furnace's Delirium": "Ảo Giác Lò Sưởi",
        "Gingerbread Mage": "Phù Thủy Bánh Gừng",
        "Gingerbread Marksman": "Xạ Thủ Bánh Gừng",
        "Gingerbread Vanguard": "Tiên Phong Bánh Gừng",
        "Greyhorn": "Greyhorn",
        "Hazana": "Hazana",
        "Hit me!": "Đánh Tôi Đi!",
        "Imperial Guard Captain": "Phân Đoàn Trưởng Vệ Đội Đế Quốc",
        "Imperial Guard Knight": "Kỵ Sĩ Vệ Đội Đế Quốc",
        "Imperial Guard Sergeant Major": "Trung Sĩ Trưởng Vệ Đội Đế Quốc",
        "Imperial Guard Squire": "Thị Tùng Vệ Đội Đế Quốc",
        "Iridescent Wing": "Cánh Cầu Vồng",
        "Mighty Treasure Hunter": "Kẻ Săn Kho Báu Uy Mãnh",
        "Muscular Treasure Hunter": "Kẻ Săn Kho Báu Vạm Vỡ",
        "Nanoha???": "Nanoha ???",
        "Ribbon Jar Spirit": "Linh Hồn Ấm Ruy Băng",
        "Sentinel of Dawn - Bladesman": "Đao Thủ Cận Vệ Bình Minh",
        "Sentinel of Dawn - Mage": "Pháp Sư Cận Vệ Bình Minh",
        "Smart Treasure Hunter": "Kẻ Săn Kho Báu Thông Minh",
        "Snoring Gift Pile": "Đống Quà Khò Khè",
        "Cataclysm Survivor Upgrade": "Nâng Cấp Người Sống Sót Sau Đại Họa",
        "Cataclysm Survivor Theme Reward": "Thưởng Chủ Đề Người Sống Sót Sau Đại Họa",
        "!NONEED!": "!NONEED!",
        "Clear the stage": "Vượt ải",
    }
    for k, v in curated_p1_terms.items():
        exact_lookup[k] = v
        exact_lookup[k.lower()] = v

    def match_rule_patterns(txt: str):
        # 1. InfinityTowerLevel: [Theme] Difficulty N
        m = re.match(r'^\[(.*?)\]\s*Difficulty\s*(\d+)$', txt)
        if m:
            theme_en = m.group(1).strip()
            diff_num = m.group(2).strip()
            theme_vi = exact_lookup.get(theme_en, exact_lookup.get(theme_en.lower(), theme_en))
            return f"[{theme_vi}] Độ Khó {diff_num}"

        # 2. Level clear times & objectives
        m = re.match(r'^Clear time\s*([≤<=]+)\s*(\d+s?)$', txt, re.IGNORECASE)
        if m:
            return f"Thời gian vượt ải {m.group(1)}{m.group(2)}"

        m = re.match(r'^Clear with\s*([>≥>=]+)\s*(\d+s?)\s*remaining$', txt, re.IGNORECASE)
        if m:
            return f"Vượt ải khi thời gian còn lại {m.group(1)}{m.group(2)}"

        m = re.match(r'^Clear with HP above\s*(\d+)$', txt, re.IGNORECASE)
        if m:
            return f"Vượt ải với HP trên {m.group(1)}"

        # 3. Kills and Defeats
        m = re.match(r'^(Kill|Defeat)\s+(\{Param2\})\s+[x×](\{Param1\})<space=7>$', txt, re.IGNORECASE)
        if m:
            return f"Tiêu diệt {m.group(2)} ×{m.group(3)}<space=7>"

        # 4. Cast character skills
        m = re.match(r"^Cast\s+(.+?)'s\s+(Main Skill|Support Skill|Ultimate Skill|Ultimate)\s+(\{Param\d+\})\s+(\{Param\d+\})\s+times(<space=7>|\.)?$", txt, re.IGNORECASE)
        if m:
            char = m.group(1).strip()
            sk_type = m.group(2).strip()
            p2 = m.group(3).strip()
            p1 = m.group(4).strip()
            sp = m.group(5) or ""
            if "Main" in sk_type:
                vi_sk = "Kỹ Năng Chủ Lực"
            elif "Support" in sk_type:
                vi_sk = "Kỹ Năng Viện Trợ"
            else:
                vi_sk = "Tuyệt Kỹ"
            return f"Thi triển {vi_sk} của {char} {p2} {p1} lần{sp}"

        return None

    to_translate = []
    for tbl_name, tbl_info in p1_data.items():
        for str_key, str_val in tbl_info.get("entries", {}).items():
            if not str_val or not str_val.strip():
                continue
            if str_val in exact_lookup:
                cache[str_val] = exact_lookup[str_val]
            elif str_val.lower() in exact_lookup:
                cache[str_val] = exact_lookup[str_val.lower()]
            elif str_val in cache:
                continue
            else:
                rule_res = match_rule_patterns(str_val)
                if rule_res:
                    cache[str_val] = rule_res
                else:
                    to_translate.append(str_val)

    # Unique list
    unique_to_translate = list(dict.fromkeys(to_translate))
    print(f"Strings to translate via API: {len(unique_to_translate)} (resolved by glossary/rules/cache: {len(cache)})")

    if unique_to_translate:
        batch_size = 20
        batches = [unique_to_translate[i : i + batch_size] for i in range(0, len(unique_to_translate), batch_size)]
        print(f"Processing {len(unique_to_translate)} strings across {len(batches)} batches with ThreadPoolExecutor...")

        from concurrent.futures import ThreadPoolExecutor, as_completed

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
                if completed_batches % 10 == 0 or completed_batches == len(batches):
                    print(f"  Completed batch {completed_batches}/{len(batches)} ({completed_batches/len(batches)*100:.1f}%)")
                    save_cache(cache)

        save_cache(cache)
        print("Batch translation complete and saved to cache.")

    translated_p1 = {}
    total_translated = 0
    token_errors = 0

    for tbl_name, tbl_info in p1_data.items():
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

        translated_p1[tbl_name] = {
            "file": tbl_info.get("file"),
            "count": len(translated_entries),
            "entries": translated_entries
        }

    with open(P1_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(translated_p1, f, ensure_ascii=False, indent=2)

    print(f"Pillar 1 translation finished: {total_translated} strings, {token_errors} token fallbacks.")
    print(f"Saved to {P1_OUTPUT}")

if __name__ == "__main__":
    main()
