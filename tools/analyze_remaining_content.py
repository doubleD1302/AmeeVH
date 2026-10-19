#!/usr/bin/env python3
"""Analyze translated vs remaining categories across the whole game."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    
    with open(root / 'CHECKPOINT.json', 'r', encoding='utf-8') as f:
        ckpt = json.load(f)

    completed_ids = ckpt.get('completed_translation_ids', [])
    completed_cats = set()
    for cid in completed_ids:
        parts = cid.split('::')
        if len(parts) >= 2:
            completed_cats.add(parts[1])

    with open(root / 'work' / 'research' / 'detailed_localization_breakdown.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    categories = data.get('categories', [])

    translated = []
    remaining = []

    for c in categories:
        cat_name = c['category']
        if cat_name in completed_cats:
            translated.append(c)
        else:
            remaining.append(c)

    trans_str_count = sum(c['count'] for c in translated)
    rem_str_count = sum(c['count'] for c in remaining)
    total_str_count = trans_str_count + rem_str_count

    print(f"Total categories: {len(categories)}")
    print(f"Translated categories: {len(translated)} ({trans_str_count} strings, {trans_str_count/total_str_count*100:.1f}%)")
    print(f"Remaining categories: {len(remaining)} ({rem_str_count} strings, {rem_str_count/total_str_count*100:.1f}%)")

    # Group remaining categories by theme/domain
    domains = {
        "1. Lồng Tiếng & Hồ Sơ Nhân Vật (Voice & Character Archive)": [
            'CharacterArchiveVoice', 'CharacterVoice', 'Character', 'CharacterSkin', 'CharacterProfile', 
            'CharacterArchive', 'CharacterSkinVoice', 'HeroAudio', 'HeroSound'
        ],
        "2. Màn Chơi, Dungeon & Bản Đồ (Levels, Stages, Dungeons & Towers)": [
            'ActivityLevelsLevel', 'Dungeon', 'Stage', 'Tower', 'TowerFloor', 'Level', 'Chapter', 
            'Map', 'WorldMap', 'DungeonLevel', 'Maze', 'Boss', 'Monster', 'Enemy', 'HardStage'
        ],
        "3. Hoạt Động & Sự Kiện (Events & Seasonal Activities)": [
            'Activity', 'ActivitySign', 'ActivityPass', 'ActivityTurntable', 'ActivityExchange',
            'ActivityDaily', 'ActivityChallenge', 'ActivityBoss', 'ActivityRank', 'ActivityQuest'
        ],
        "4. Cốt Truyện AVG & Đối Thoại (AVG Story Dialogues & Quests)": [
            'AVG', 'AvgDialogue', 'Dialogue', 'StoryBranch', 'MainStory', 'SubStory', 'BranchQuest',
            'Mission', 'Task', 'Quest', 'GuideQuest'
        ],
        "5. Trang Bị, Ấn Ký, Di Vật & Cơ Chế Chiến Đấu (Gear, Sigils, Relics & Combat Mechanics)": [
            'Equip', 'Equipment', 'Artifact', 'Relic', 'Rune', 'Gem', 'Badge', 'Buff', 'State',
            'PassiveSkill', 'SkillUpgrade', 'BattleField'
        ],
        "6. Hướng Dẫn Tân Thủ, Hệ Thống & Cài Đặt (Tutorials, Guide & System Settings)": [
            'Guide', 'Tutorial', 'Help', 'Setting', 'Tips', 'Notice', 'System', 'Shop', 'DrawCard',
            'Gacha', 'Recharge', 'VIP', 'VipLevel'
        ]
    }

    # Grouping
    classified = {d: [] for d in domains}
    unclassified = []

    for c in remaining:
        matched = False
        cat_lower = c['category'].lower()
        for d, keywords in domains.items():
            for kw in keywords:
                if kw.lower() in cat_lower:
                    classified[d].append(c)
                    matched = True
                    break
            if matched:
                break
        if not matched:
            unclassified.append(c)

    print("\n" + "="*80)
    print("PHÂN NHÓM CÁC HẠNG MỤC CÒN LẠI CẦN VIỆT HÓA")
    print("="*80)

    for d, cats in classified.items():
        sub_count = sum(c['count'] for c in cats)
        print(f"\n### {d} — {len(cats)} bảng ({sub_count:,} chuỗi):")
        # Sort descending by count
        cats.sort(key=lambda x: x['count'], reverse=True)
        for c in cats[:8]:
            ex = c.get('example_value', '')[:40].replace('\n', ' ')
            print(f"  * **{c['category']}** ({c['count']:,} chuỗi): \"{ex}\"")
        if len(cats) > 8:
            print(f"  * ... và {len(cats)-8} bảng nhỏ khác.")

    unclass_count = sum(c['count'] for c in unclassified)
    print(f"\n### 7. Các bảng hệ thống/tính năng phụ khác — {len(unclassified)} bảng ({unclass_count:,} chuỗi):")
    unclassified.sort(key=lambda x: x['count'], reverse=True)
    for c in unclassified[:10]:
        ex = c.get('example_value', '')[:40].replace('\n', ' ')
        print(f"  * **{c['category']}** ({c['count']:,} chuỗi): \"{ex}\"")
    if len(unclassified) > 10:
        print(f"  * ... và {len(unclassified)-10} bảng vi mô khác.")

if __name__ == '__main__':
    main()
