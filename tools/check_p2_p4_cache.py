#!/usr/bin/env python3
import json

with open("work/batches/pillars_translation_cache.json", "r", encoding="utf-8") as f:
    cache = json.load(f)

for p_name, f_name in [("P2", "pillar2_voices_characters.json"), ("P4", "pillar4_system_gacha_shops.json")]:
    with open(f"work/batches/{f_name}", "r", encoding="utf-8") as f:
        data = json.load(f)
    total = sum(v["count"] for v in data.values())
    in_cache = 0
    missing = 0
    for tbl in data.values():
        for str_val in tbl.get("entries", {}).values():
            if str_val in cache:
                in_cache += 1
            else:
                missing += 1
    print(f"{p_name}: total {total} strings -> {in_cache} in cache ({in_cache/total*100:.1f}%), {missing} missing")
