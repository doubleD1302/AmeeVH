import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
SRC = ROOT / "work/editorial/final_cg_npc_and_disc_editorial_20261025_r01/UNIFIED_CAMPAIGN_18_PROPOSALS.jsonl"
STAGING_DIR = ROOT / "staging/campaign18_final_cg_npc_and_disc"
STAGING_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = STAGING_DIR / "CAMPAIGN_18_VERIFIED_PROPOSALS.jsonl"

print("Staging Campaign 18 verified proposals...")
items = []
with open(SRC, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            items.append(json.loads(line))

with open(OUT_FILE, "w", encoding="utf-8") as f:
    for it in items:
        f.write(json.dumps(it, ensure_ascii=False) + "\n")

# Summary by scene
scenes = {}
for it in items:
    sc = it.get("scene_id") or it["id"].split(".")[0]
    scenes[sc] = scenes.get(sc, 0) + 1

meta = {
    "campaign": "Campaign 18 (Đợt 10 - FINAL CAMPAIGN OF ENTIRE GAME)",
    "scope": "Final CG NPC Stories & Disc Memory Stories",
    "total_scenes": len(scenes),
    "total_lines": len(items),
    "scenes_breakdown": scenes
}

with open(STAGING_DIR / "METADATA.json", "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

print(f"Staged {len(items)} items across {len(scenes)} scenes to {STAGING_DIR}")
