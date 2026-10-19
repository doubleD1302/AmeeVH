#!/usr/bin/env python3
"""Inspect breakdown categories and files for the user request."""
import json
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    breakdown_file = root / "work" / "research" / "detailed_localization_breakdown.json"
    with open(breakdown_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    categories = data.get("categories", [])
    
    target_names = [
        "ActivityLevelsLevel", "InfinityTowerLevel", "MonsterManual", 
        "StarTowerEventOptionAction", "StarTowerBookEventReward", "TowerDefensePotential",
        "CharacterArchiveVoice", "CharacterArchiveContent", "CharacterArchiveBaseInfo",
        "CharacterDes", "TrialCharacter", "CharacterSkin", "CharacterCG",
        "Plot", "DatingStartEndEvent", "EventOptions", "VampireSurvivorQuest",
        "AssistQuest", "TourGuideQuest", "DiscIP", "CharGetLines", "ErrorCode",
        "GachaType", "Gacha", "MallShop"
    ]

    print("=== EXACT MATCHES ===")
    exact_matches = {}
    for cat in categories:
        name = cat["category"]
        for t in target_names:
            if t.lower() == name.lower():
                exact_matches[name] = cat
                print(f"Matched: {cat['category']} -> count={cat['count']}, file={cat.get('file')}")

    print("\n=== SEARCHING FOR 4 PILLARS ACROSS ALL CATEGORIES ===")
    # Let's inspect categories by keywords
    p1_kw = ["level", "tower", "monster", "boss", "dungeon", "defense", "startower"]
    p2_kw = ["character", "voice", "skin", "cg", "profile", "trial", "des"]
    p3_kw = ["plot", "dating", "eventoption", "vampire", "quest", "tourguide"]
    p4_kw = ["disc", "charget", "error", "gacha", "mall", "shop"]

    # Check how categories in detailed_localization_breakdown are grouped
    # and what total strings they have.
    print(f"Total categories in breakdown: {len(categories)}")
    
if __name__ == "__main__":
    main()
