#!/usr/bin/env python3
"""Group all categories in detailed_localization_breakdown into the exact 4 pillars."""
import json
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    breakdown_file = root / "work" / "research" / "detailed_localization_breakdown.json"
    with open(breakdown_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    categories = data.get("categories", [])
    
    ckpt_file = root / "CHECKPOINT.json"
    with open(ckpt_file, "r", encoding="utf-8") as f:
        ckpt = json.load(f)
    
    completed_cats = set()
    for cid in ckpt.get("completed_translation_ids", []):
        parts = cid.split("::")
        if len(parts) >= 2:
            completed_cats.add(parts[1])

    # Note: DiscIP is in completed_cats
    # Let's inspect remaining categories
    remaining_cats = [c for c in categories if c["category"] not in completed_cats or c["category"] == "DiscIP"]
    
    # Pillar 2: Lồng Tiếng & Hồ Sơ Nhân Vật
    p2_exact = [
        'CharacterArchiveVoice', 'CharacterArchiveContent', 'CharacterArchiveBaseInfo',
        'CharacterDes', 'TrialCharacter', 'CharacterSkin', 'CharacterCG',
        'CharacterAudio', 'CharacterArchiveStory', 'CharacterTag', 'BreakOutCharacter',
        'CharacterStory'
    ]

    # Pillar 3: Cốt Truyện Phụ, Đối Thoại Hẹn Hò & Nhiệm Vụ Sự Kiện
    p3_exact = [
        'Plot', 'DatingStartEndEvent', 'EventOptions', 'VampireSurvivorQuest',
        'AssistQuest', 'TourGuideQuest', 'DatingBranch', 'DatingLandmark',
        'NPCAffinityPlot', 'NPCConfig', 'StoryPreview', 'StoryRolePersonality',
        'StoryPersonality', 'StorySetChapter', 'StoryChapter', 'StorySetTab',
        'ActivityAvgLevel', 'MiningQuest', 'MiningQuestGroup', 'PeriodicQuestControl',
        'DailyQuest', 'WeeklyQuest'
    ]

    p1_candidates = []
    p2_candidates = []
    p3_candidates = []
    p4_candidates = []

    for c in remaining_cats:
        cat_name = c["category"]
        if cat_name in p2_exact or (cat_name.startswith("Character") and "Voice" in cat_name):
            p2_candidates.append(c)
        elif cat_name in p3_exact:
            p3_candidates.append(c)
        elif any(k in cat_name.lower() for k in [
            'level', 'tower', 'monster', 'boss', 'startower', 'defense', 'soldier', 
            'jointdrill', 'penguincardfloor', 'penguincardendless', 'travelerduel', 'instance', 'drill'
        ]) and cat_name not in ['ActivityAvgLevel']:
            p1_candidates.append(c)
        else:
            p4_candidates.append(c)

    p1_str = sum(c['count'] for c in p1_candidates)
    p2_str = sum(c['count'] for c in p2_candidates)
    p3_str = sum(c['count'] for c in p3_candidates)
    p4_str = sum(c['count'] for c in p4_candidates)

    print(f"Pillar 1: {len(p1_candidates)} tables, {p1_str} strings")
    print(f"Pillar 2: {len(p2_candidates)} tables, {p2_str} strings")
    print(f"Pillar 3: {len(p3_candidates)} tables, {p3_str} strings")
    print(f"Pillar 4: {len(p4_candidates)} tables, {p4_str} strings")
    print(f"Total: {len(p1_candidates)+len(p2_candidates)+len(p3_candidates)+len(p4_candidates)} tables, {p1_str+p2_str+p3_str+p4_str} strings")

    # Let's save the grouping to a json file for our subagent pipelines
    grouping = {
        "pillar1_dungeons_monsters": p1_candidates,
        "pillar2_voices_characters": p2_candidates,
        "pillar3_story_dating_quests": p3_candidates,
        "pillar4_system_gacha_shops": p4_candidates
    }
    with open(root / "work" / "batches" / "pillars_grouping.json", "w", encoding="utf-8") as f:
        json.dump(grouping, f, ensure_ascii=False, indent=2)
    print("Saved grouping to work/batches/pillars_grouping.json")

if __name__ == "__main__":
    main()
