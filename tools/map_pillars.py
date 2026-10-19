#!/usr/bin/env python3
"""Map all 221 categories to the 4 pillars."""
import json
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    breakdown_file = root / "work" / "research" / "detailed_localization_breakdown.json"
    with open(breakdown_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    categories = data.get("categories", [])
    
    # Check already completed categories from CHECKPOINT.json
    ckpt_file = root / "CHECKPOINT.json"
    with open(ckpt_file, "r", encoding="utf-8") as f:
        ckpt = json.load(f)
    
    completed_cats = set()
    for cid in ckpt.get("completed_translation_ids", []):
        parts = cid.split("::")
        if len(parts) >= 2:
            completed_cats.add(parts[1])

    print(f"Total categories: {len(categories)}")
    print(f"Already completed categories ({len(completed_cats)}): {sorted(completed_cats)}")

    # Let's inspect the categories that are NOT completed
    remaining_cats = [c for c in categories if c["category"] not in completed_cats]
    print(f"Remaining categories: {len(remaining_cats)}")

    # Pillar definitions based on user description:
    # Pillar 1: Màn Chơi, Dungeon, Tháp Sao & Quái Vật (8,475 chuỗi — 57 bảng)
    # Pillar 2: Lồng Tiếng & Hồ Sơ Nhân Vật (6,297 chuỗi — 12 bảng)
    # Pillar 3: Cốt Truyện Phụ, Đối Thoại Hẹn Hò & Nhiệm Vụ Sự Kiện (780 chuỗi — 22 bảng)
    # Pillar 4: Tính Năng Hệ Thống Phụ, Gacha & Cửa Hàng (6,348 chuỗi — 107 bảng vi mô)

    p2_names = {
        'CharacterArchiveVoice', 'CharacterArchiveContent', 'CharacterArchiveBaseInfo',
        'CharacterDes', 'TrialCharacter', 'CharacterSkin', 'CharacterCG',
        'CharacterAudio', 'CharacterArchiveStory', 'CharacterVoice', 'CharacterSkinVoice',
        'CharacterSound'
    }

    p3_names = {
        'Plot', 'DatingStartEndEvent', 'EventOptions', 'VampireSurvivorQuest',
        'AssistQuest', 'TourGuideQuest', 'Dating', 'EventOption', 'GuideQuest'
    }

    # Let's print out all remaining categories with their string counts and category name
    for c in sorted(remaining_cats, key=lambda x: x['count'], reverse=True):
        print(f"{c['category']:<35} | {c['count']:>5} | {c.get('file', '')}")

if __name__ == "__main__":
    main()
