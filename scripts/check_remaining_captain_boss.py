import os, json, re

ROOT = r"C:\YostarGames\StellaSora_EN\StellaSora_VietHoa"

files_to_audit = [
    ("batch:batch_10k_approved.json", "work/batches/batch_10k_approved.json", "json_kv"),
    ("batch:batch_10k_b2_approved.json", "work/batches/batch_10k_b2_approved.json", "json_kv"),
    ("batch:batch_10k_b3_approved.json", "work/batches/batch_10k_b3_approved.json", "json_kv"),
    ("batch:batch_10k_b4_approved.json", "work/batches/batch_10k_b4_approved.json", "json_kv"),
    ("batch:remaining_lua_avg_cache.json", "work/batches/remaining_lua_avg_cache.json", "json_kv"),
    ("batch:dialogue_remaining_avg_approved.json", "work/batches/dialogue_remaining_avg_approved.json", "json_kv"),
    ("campaign:lightnovel_story", "work/editorial/lightnovel_editorial_20261024_r02/UNIFIED_STORY_PROPOSALS.jsonl", "jsonl"),
    ("campaign:act1_act2", "work/editorial/act1_act2_story_editorial_20261024_r01/UNIFIED_ACT1_ACT2_PROPOSALS.jsonl", "jsonl"),
    ("campaign:act2_climax", "work/editorial/act2_climax_story_editorial_20261024_r01/UNIFIED_ACT2_CLIMAX_PROPOSALS.jsonl", "jsonl"),
    ("campaign:act3", "work/editorial/act3_story_editorial_20261024_r01/UNIFIED_ACT3_PROPOSALS.jsonl", "jsonl"),
    ("campaign:act3_part1", "work/editorial/act3_part1_story_editorial_20261024_r01/UNIFIED_ACT3_PART1_PROPOSALS.jsonl", "jsonl"),
    ("campaign:act4_final", "work/editorial/act4_final_story_editorial_20261024_r01/UNIFIED_ACT4_STORY_PROPOSALS.jsonl", "jsonl"),
    ("campaign:side_stories_part1", "work/editorial/side_stories_part1_editorial_20261025_r01/UNIFIED_STSP_PART1_PROPOSALS.jsonl", "jsonl"),
    ("campaign:side_stories_part2", "work/editorial/side_stories_part2_editorial_20261025_r01/UNIFIED_CAMPAIGN13_PROPOSALS.jsonl", "jsonl"),
    ("campaign:event_stories_part2", "work/editorial/event_stories_part2_editorial_20261025_r01/UNIFIED_CAMPAIGN_14_PROPOSALS.jsonl", "jsonl"),
    ("campaign:event_stories_part3", "work/editorial/event_stories_part3_editorial_20261025_r01/UNIFIED_CAMPAIGN_15_PROPOSALS.jsonl", "jsonl"),
    ("campaign:event_stories_part4", "work/editorial/event_stories_part4_editorial_20261025_r01/UNIFIED_CAMPAIGN_16_PROPOSALS.jsonl", "jsonl"),
    ("campaign:campaign_19_polished", "work/editorial/campaign19_polish_remaining_20680_20261025_r01/UNIFIED_CAMPAIGN_19_POLISHED.jsonl", "jsonl_c19"),
]

captain_re = re.compile(r"Thuyền trưởng (Fuyuka|Nazuka|Nazuna|Gerie|Narida)", re.I)
boss_re = re.compile(r"\bông chủ\b", re.I)

for name, rel_path, ftype in files_to_audit:
    full_path = os.path.join(ROOT, rel_path)
    if not os.path.exists(full_path): continue
    if ftype == "json_kv":
        with open(full_path, "r", encoding="utf-8") as f:
            d = json.load(f)
        for k, v in d.items():
            if not isinstance(v, str): continue
            if captain_re.search(v):
                print(f"[Captain] {name} | {k}: {repr(v)}")
            if boss_re.search(v):
                print(f"[Boss] {name} | {k}: {repr(v)}")
    else:
        with open(full_path, "r", encoding="utf-8") as f:
            for lidx, l in enumerate(f):
                if not l.strip(): continue
                d = json.loads(l)
                k = d.get("id") or d.get("scene_id") or f"line_{lidx}"
                v = d.get("vi") or d.get("vi_editorial") or d.get("polished_vi") or ""
                if captain_re.search(v):
                    print(f"[Captain] {name} | {k}: {repr(v)}")
                if boss_re.search(v):
                    print(f"[Boss] {name} | {k}: {repr(v)}")
