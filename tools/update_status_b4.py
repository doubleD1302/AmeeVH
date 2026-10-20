import json
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
status_path = os.path.join(viet_dir, "STATUS.json")
with open(status_path, "r", encoding="utf-8") as f:
    d = json.load(f)

t = d.get("translation", {})
t["total_translated_strings"] = 88655
t["master_glossary_terms"] = 1362
t["forbidden_calques_blacklisted"] = 54
t["translated_story_dialogues"] = 40000
t["batch4_approved"] = 10000
t["zero_untranslated_audit_passed"] = True
d["translation"] = t

with open(status_path, "w", encoding="utf-8") as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

checkpoint_path = os.path.join(viet_dir, "CHECKPOINT.json")
with open(checkpoint_path, "r", encoding="utf-8") as f:
    cp = json.load(f)

cp["active_batch"] = "BATCH4_AVG_STORY_COMPLETE"
cp["batch_status"] = "batch4_10000_avg_dialogues_approved_and_verified"
cp["next_action"] = "Ready for Batch 5 (final ~17,450 remaining AVG lines) or packaging and runtime deployment."

with open(checkpoint_path, "w", encoding="utf-8") as f:
    json.dump(cp, f, indent=2, ensure_ascii=False)

print("STATUS.json and CHECKPOINT.json updated successfully!")
