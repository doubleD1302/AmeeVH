import json
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
breakdown_file = os.path.join(viet_dir, r"work\batches\latest_resources_breakdown.json")

# Let's inspect find_truly_untranslated.py output
from find_truly_untranslated import truly_untranslated

print(f"Total truly untranslated tables: {len(truly_untranslated)}")
print(f"Total strings: {sum(t['untranslated_count'] for t in truly_untranslated)}")

# Group into 3 partitions:
# Partition 1: Gameplay Modes, Minigames & Challenges
# (PenguinCardBuff, PenguinCardFloor, PenguinCardAide, VampireSurvivor, ScoreBossGetControl,
#  SoldierPartnerGroup, SoldierCharacter, SoldierSkin, TowerDefenseCharacter,
#  TraceHuntLogEntryTemplate, DailyInstance, DailyInstanceRewardGroup, BreakOutCharacter, StarTowerEventOptionAction, etc.)

# Partition 2: Characters, Tactics, Profiles & Items
# (CharacterDes, TrialCharacter, CharacterArchiveBaseInfo, Character, CharacterArchiveContent,
#  BoardNPC, NPCConfig, Item, ActivityGoods, etc.)

# Partition 3: Quests, Events, Story, Dialogues, UI & Mechanics
# (StarTowerTalk, StarTowerBookFateCardQuest, EventOptions, Story, ActivityStory, Plot,
#  UIText, Word, Skill, etc.)

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

p1_tables = []
p2_tables = []
p3_tables = []

for t in truly_untranslated:
    cat = t["category"]
    if cat in p1_cats:
        p1_tables.append(t)
    elif cat in p2_cats:
        p2_tables.append(t)
    else:
        p3_tables.append(t)

print(f"Partition 1 (Minigames & Combat Modes): {len(p1_tables)} tables, {sum(t['untranslated_count'] for t in p1_tables)} strings")
print(f"Partition 2 (Characters, Profiles & Items): {len(p2_tables)} tables, {sum(t['untranslated_count'] for t in p2_tables)} strings")
print(f"Partition 3 (Story, Quests, Dialogues & UI): {len(p3_tables)} tables, {sum(t['untranslated_count'] for t in p3_tables)} strings")
