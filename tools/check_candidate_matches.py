import json
import os

candidates_path = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\candidates_survey.json"
with open(candidates_path, "r", encoding="utf-8") as f:
    candidates = json.load(f)

# Load existing caches
batches_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches"
caches = {}
for cname in ["subagent_4b_skills_cache.json", "item_db_translation_cache.json", "system_tables_translation_cache.json", "talent_fatecard_translation_cache.json", "skill_names_translated.json"]:
    p = os.path.join(batches_dir, cname)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            caches[cname] = json.load(f)

print(f"Loaded {len(caches)} caches.")

# Check how many candidates have matches in caches
matched = {}
for en, info in candidates.items():
    found_vi = None
    for cname, cdata in caches.items():
        if isinstance(cdata, dict):
            if en in cdata:
                found_vi = cdata[en]
                break
    if found_vi:
        matched[en] = {"vi": found_vi, "cat": info["category"], "cn": info["cn"]}

print(f"Total candidates: {len(candidates)}")
print(f"Candidates already matched in existing caches: {len(matched)}")
for en, info in list(matched.items())[:20]:
    print(f"  {en:35} -> {info['vi']} (CN: {info['cn']}) [{info['cat']}]")
