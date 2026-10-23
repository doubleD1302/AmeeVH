import json
import os
import hashlib

def sha256_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

base_dir = "StellaSora_VietHoa/work/subagents/lightnovel_editorial_20261024_r02"
cat_dir = os.path.join(base_dir, "catalog_engineer")

with open(os.path.join(cat_dir, "PARTITION_A_CANDIDATES.json"), "r", encoding="utf-8") as f:
    part_a = json.load(f)
with open(os.path.join(cat_dir, "PARTITION_B_CANDIDATES.json"), "r", encoding="utf-8") as f:
    part_b = json.load(f)

# Partition A1: Prologue + Act 1
scenes_a1 = [s for s in part_a["scenes"] if "Act 2" not in s.get("chapter", "")]
# Partition A2: Act 2
scenes_a2 = [s for s in part_a["scenes"] if "Act 2" in s.get("chapter", "")]

# Partition B1: Dating, Star Tower, Dossier, Narrative
scenes_b1 = [s for s in part_b["scenes"] if not s.get("chapter", "").startswith("Character Story:")]
# Partition B2: Character Stories
scenes_b2 = [s for s in part_b["scenes"] if s.get("chapter", "").startswith("Character Story:")]

def make_partition_dict(pid, desc, role, scenes):
    return {
        "schema": "stella_sora.editorial_partition_candidates.v2",
        "partition_id": pid,
        "run_id": "lightnovel_editorial_20261024_r02",
        "assigned_role": role,
        "scope_description": desc,
        "total_scenes": len(scenes),
        "total_lines": sum(len(s.get("lines", [])) for s in scenes),
        "scenes": scenes
    }

p_a1 = make_partition_dict("PARTITION_A1", "Main Story Prologue & Act 1 (Amber & Iris Awakening)", "TRANSLATOR_MAIN_STORY_1", scenes_a1)
p_a2 = make_partition_dict("PARTITION_A2", "Main Story Act 2 (Tilia, Treant & Monolith Expedition)", "TRANSLATOR_MAIN_STORY_2", scenes_a2)
p_b1 = make_partition_dict("PARTITION_B1", "Dating Events, Star Tower & Character Dossiers", "TRANSLATOR_DATING_STAR_TOWER", scenes_b1)
p_b2 = make_partition_dict("PARTITION_B2", "Character Heroine CG Stories (Kasimira, Jinglin, Noya, Minova, Laru, Shia)", "TRANSLATOR_CHARACTER_STORIES", scenes_b2)

splits = [
    ("PARTITION_A1_CANDIDATES.json", p_a1, "translator_main_1"),
    ("PARTITION_A2_CANDIDATES.json", p_a2, "translator_main_2"),
    ("PARTITION_B1_CANDIDATES.json", p_b1, "translator_dating_star"),
    ("PARTITION_B2_CANDIDATES.json", p_b2, "translator_char_stories")
]

for fname, data, sub_dir in splits:
    out_dir = os.path.join(base_dir, sub_dir)
    os.makedirs(out_dir, exist_ok=True)
    fpath = os.path.join(out_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    s_hash = sha256_file(fpath)
    print(f"Created {fname} in {sub_dir}: {data['total_scenes']} scenes, {data['total_lines']} lines. SHA256: {s_hash[:16]}...")
