#!/usr/bin/env python3
import json
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    breakdown_path = root / "work" / "research" / "detailed_localization_breakdown.json"
    data = json.loads(breakdown_path.read_text(encoding="utf-8"))
    cats = data["categories"]

    domains = {
        "1. Kỹ Năng, Thiên Phú & Chiến Đấu (Combat & Builds)": [
            "Talent", "Skill", "Potential", "SecondarySkill", "MainSkill", "TowerDefensePotential", "FateCard"
        ],
        "2. Giao Diện & Hệ Thống Cốt Lõi (UI & System)": [
            "UIText", "EffectDesc", "Word", "DictionaryDiagram", "MailTemplate"
        ],
        "3. Vật Phẩm, Cửa Hàng & Phần Thưởng (Items & Economy)": [
            "Item", "ActivityGoods", "MallPackage", "AffinityUpReward", "PenguinCard"
        ],
        "4. Cốt Truyện, Hẹn Hò & Lời Thoại (Story, Dating & Events)": [
            "DatingCharacterEvent", "Story", "ActivityStory", "DatingLandmarkEvent", "Plot", "StarTowerTalk",
            "ActivityTask", "AffinityQuest", "LevelQuestTarget", "StoryChapter", "StoryChapterTimeStamp",
            "StoryEvidence", "StoryPreview", "StorySetChapter", "StorySetSection", "StorySetTab"
        ],
        "5. Nhân Vật, Giọng Nói & Sổ Tay Quái Vật (Archive & Lore)": [
            "CharacterArchiveVoice", "CharacterArchiveContent", "CharacterArchiveBaseInfo", "CharacterDes",
            "MonsterManual", "StarTowerBookEventReward", "DiscIP"
        ],
        "6. Thành Tựu & Danh Hiệu (Achievements)": [
            "Achievement"
        ],
        "7. Cự Tháp, Vực Sâu & Hoạt Động (Monolith & Dungeons)": [
            "ActivityLevelsLevel", "InfinityTowerLevel", "TravelerDuelChallengeAffix", "InfinityTowerDifficulty",
            "InfinityTowerAffix", "StarTowerEventOptionAction", "StarTowerBookFateCard"
        ]
    }

    domain_stats = {d: {"count": 0, "items": []} for d in domains}
    other_count = 0
    other_items = []

    for c in cats:
        cat_name = c["category"]
        count = c["count"]
        matched = False
        for d, cat_list in domains.items():
            if cat_name in cat_list:
                domain_stats[d]["count"] += count
                domain_stats[d]["items"].append((cat_name, count))
                matched = True
                break
        if not matched:
            other_count += count
            other_items.append((cat_name, count))

    domain_stats["8. Các bảng cấu hình & dữ liệu khác (Other Tables)"] = {
        "count": other_count,
        "items": other_items
    }

    for d, info in domain_stats.items():
        c = info["count"]
        pct = round(c / 55144 * 100, 1)
        print(f"\n### {d}: {c:,} chuỗi ({pct}%)")
        for name, cnt in sorted(info["items"], key=lambda x: x[1], reverse=True)[:8]:
            print(f"  - `{name}`: {cnt:,} chuỗi")

if __name__ == "__main__":
    main()
