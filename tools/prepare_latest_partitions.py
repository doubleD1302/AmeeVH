import json
import os
import sys

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
sys.path.insert(0, os.path.join(viet_dir, "tools"))
from find_truly_untranslated import truly_untranslated

p1_cats = {
    "VampireSurvivor", "ScoreBossGetControl", "SoldierPartnerGroup", "PenguinCardBuff",
    "TowerDefenseCharacter", "TraceHuntLogEntryTemplate", "PenguinCardFloor",
    "SoldierCharacter", "SoldierSkin", "DailyInstance", "DailyInstanceRewardGroup",
    "BreakOutCharacter", "PenguinCardAide", "StarTowerEventOptionAction",
    "TowerDefenseLevel", "LevelQuestTarget", "ActivityShop"
}

p2_cats = {
    "CharacterDes", "TrialCharacter", "CharacterArchiveBaseInfo", "BoardNPC",
    "Character", "ActivityGoods", "CharacterArchiveContent", "NPCConfig", "Item"
}

p1_data = {}
p2_data = {}
p3_data = {}

for t in truly_untranslated:
    cat = t["category"]
    fname = t["file"]
    entries = t["entries"]
    key = f"{cat}___{fname}"
    
    table_obj = {
        "file": fname,
        "category": cat,
        "count": len(entries),
        "entries": entries
    }
    
    if cat in p1_cats:
        p1_data[key] = table_obj
    elif cat in p2_cats:
        p2_data[key] = table_obj
    else:
        p3_data[key] = table_obj

p1_path = os.path.join(viet_dir, r"work\batches\partition1_minigames_modes.json")
p2_path = os.path.join(viet_dir, r"work\batches\partition2_characters_tactics.json")
p3_path = os.path.join(viet_dir, r"work\batches\partition3_story_quests_ui.json")

with open(p1_path, "w", encoding="utf-8") as f:
    json.dump(p1_data, f, indent=2, ensure_ascii=False)

with open(p2_path, "w", encoding="utf-8") as f:
    json.dump(p2_data, f, indent=2, ensure_ascii=False)

with open(p3_path, "w", encoding="utf-8") as f:
    json.dump(p3_data, f, indent=2, ensure_ascii=False)

total_p1 = sum(v['count'] for v in p1_data.values())
total_p2 = sum(v['count'] for v in p2_data.values())
total_p3 = sum(v['count'] for v in p3_data.values())

print(f"Partition 1 (Minigames & Modes): {len(p1_data)} tables, {total_p1} strings")
print(f"Partition 2 (Characters, Profiles, Tactics & Items): {len(p2_data)} tables, {total_p2} strings")
print(f"Partition 3 (Story, Quests, Dialogues, Skills & UI): {len(p3_data)} tables, {total_p3} strings")
print(f"TOTAL: {len(p1_data) + len(p2_data) + len(p3_data)} tables, {total_p1 + total_p2 + total_p3} strings")
