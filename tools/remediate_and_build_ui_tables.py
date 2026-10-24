#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI Remediation and Repack Tool:
1. Fixes all calques, literal MT phrases, and untranslated labels in UIText (00789)
2. Fixes terminology in Item (00653), MonsterManual (00685), DictionaryDiagram (00611), CharacterArchiveContent (00840)
3. Repacks dist/data_patched_vi.arcx
4. Dual-syncs data.arcx to Standalone and Steam installations
"""

import json
from pathlib import Path
import re
import shutil
import sys
import time
import unicodedata

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))

from arcx_adapter import repack_archive, ArcxArchive

ENTRIES_DIR = ROOT / "work/research/data_200_decrypted/entries"
DEC_DIR = ROOT / "work/research/data_200_decrypted"
OUTPUT_ARCX = ROOT / "dist" / "data_patched_vi.arcx"

# 1. Targeted UIText Fixes
UITEXT_FIXES = {
    # Funny calques
    "UIText.Shop_Stock.1": "Tồn kho: {0}",
    "UIText.Settings_Account_Gem.1": "Xác nhận số lượng {0} sở hữu",
    "UIText.CharacterRelation_CG_Reward.1": "Hồi Ức Đặc Tả",
    "UIText.Phone_Dating_Event_Window_Title.1": "Kỷ Niệm Hẹn Hò",
    "UIText.Guide_104_3.1": "Chọn ở đây để chuyển đổi chế độ hiển thị:\x0bChế độ minh họa: Hiển thị Hình minh họa của Lữ Khách đã chọn.\x0bChế độ Hồi Ức Đặc Tả: Hiển thị Hồi Ức Đặc Tả của Lữ Khách đã chọn.",
    "UIText.Guide_104_4.1": "Có thể thiết lập tối đa 5 hình ảnh màn hình chính khác nhau gồm Lữ Khách, Bí Văn Nhạc và Cốt Truyện CG. Vuốt để chuyển đổi giữa chúng.\x0bKéo biểu tượng để thay đổi thứ tự hiển thị.",
    "UIText.Equipment_AttrPreviewName_1.1": "Huy Hiệu Sơ Cấp: {0} {1}",
    "UIText.Equipment_AttrPreviewName_2.1": "Huy Hiệu Trung Cấp: {0} {1}",
    "UIText.Equipment_AttrPreviewName_3.1": "Huy Hiệu Cao Cấp: {0} {1}",
    "UIText.StarTower_Note_Yellow.1": "Vàng Ấm",
    "UIText.DepotPresents_Hint_DisassembleConfirm.1": "Tách Di Vật đã chọn sẽ nhận được các nguyên liệu sau.\nBạn có chắc muốn tiếp tục?",
    "UIText.DepotPresents_Hint_DisassembleWarning.1": "Di Vật sau khi tách không thể hoàn tác",
    "UIText.Presents_Crafting_Text.1": "Di Vật",

    # Untranslated English labels & Combat acronyms
    "UIText.EnemyInfo_Window_Property_1.1": "Điểm yếu",
    "UIText.T_Element_Weakness.1": "Điểm yếu",
    "UIText.EnemyInfo_Window_Property_2.1": "Kháng",
    "UIText.Hud_Resistance_Tip.1": "Kháng",
    "UIText.Hud_Missing_Tip.1": "Né tránh",
    "UIText.CharacterSkin_Portrait.1": "Chân dung 2D",
    "UIText.CharacterSkin_Preview.1": "Xem Trước",
    "UIText.TokenBuy_Confirm_TokenName.1": "Từ Nguyên",
    "UIText.Soldier_BossSkill_Active.1": "Chủ",
    "UIText.Soldier_BossSkill_Passive.1": "Bị",
    "UIText.InfinityTower_Layer.1": "Tầng",
    "UIText.Infinity_Diff.1": "Độ khó %s",
    "UIText.Gacha_NewBieSaveItemCurrent.1": "Hiện tại",

    # Countdown times & units
    "UIText.Depot_Item_LeftTime_Day.1": "ngày",
    "UIText.Depot_Item_LeftTime_Hour.1": "giờ",
    "UIText.Depot_LeftTime_Day.1": "ngày",
    "UIText.Depot_LeftTime_Hour.1": "giờ",
    "UIText.Depot_LeftTime_Hour2.1": "giờ",
    "UIText.Depot_LeftTime_LessThenMin.1": "< 1 phút",
    "UIText.TravelerDuel_Countdown_Day.1": "ngày",
    "UIText.TravelerDuel_Countdown_Hour.1": "giờ",
    "UIText.CommonTips_CDSec.1": "giây",
    "UIText.StarTower_Battle_Time_Sec.1": "giây",
    "UIText.Talent_Sec.1": "giây",
    "UIText.TowerDef_Text_Sec.1": "giây",
    "UIText.Shop_NextRefresh_Sec.1": "{0}<space=7>giây",
    "UIText.Energy_LeftTime_Day.1": "{0} ngày {1} giờ",
    "UIText.Energy_LeftTime_Hour.1": "{0} giờ {1} phút",
    "UIText.JointDrill_Challenge_Time_1.1": "{0} ngày {1} giờ",
    "UIText.JointDrill_Challenge_Time_2.1": "{0} giờ {1} phút",
    "UIText.StarTower_Reward_Refresh_Remain_Time_Day.1": "{0} ngày {1} giờ",
    "UIText.StarTower_Reward_Refresh_Remain_Time_Hour.1": "{0} giờ {1} phút",
    "UIText.BattlePassQusetWeekly.1": "({0} ngày {1} giờ)",
    "UIText.BattlePassQusetWeeklyHour.1": "({0} giờ)"
}

def clean_text(text: str) -> str:
    text = unicodedata.normalize('NFC', text)
    text = re.sub(r'\bCổ vật\b', 'Di Vật', text)
    text = re.sub(r'\bCổ Vật\b', 'Di Vật', text)
    text = re.sub(r'\bcổ vật\b', 'di vật', text)
    text = re.sub(r'\bCự Thạch\b', 'Cự Tháp', text)
    text = re.sub(r'\bĐá Linh Hồn\b', 'Hồn Thạch', text)
    text = re.sub(r'\bĐá Hồn\b', 'Hồn Thạch', text)
    text = re.sub(r'\bđá linh hồn\b', 'Hồn Thạch', text)
    text = re.sub(r'\bPhòng Màu Trắng\b', 'Phòng Trắng', text)
    text = re.sub(r'\bcăn phòng màu trắng\b', 'Phòng Trắng', text, flags=re.IGNORECASE)
    text = re.sub(r'\bLễ Hội Snowish\b', 'Lễ Hội Mùa Tuyết', text)
    text = re.sub(r'\bTrọng Tài Chạng Vạng\b', 'Thẩm Phán Hoàng Hôn', text)
    text = re.sub(r'\bTrọng Tài Hoàng Hôn\b', 'Thẩm Phán Hoàng Hôn', text)
    return unicodedata.normalize('NFC', text)

def main():
    print("=== STARTING UI TABLES COMPREHENSIVE REMEDIATION ===")

    # 1. Remediate UIText (00789)
    p_uitext = ENTRIES_DIR / "00789_0x87cc29ac0defc2d9.bin"
    uitext = json.loads(p_uitext.read_text(encoding="utf-8"))
    uitext_modified = 0

    for k, new_v in UITEXT_FIXES.items():
        if k in uitext:
            uitext[k] = unicodedata.normalize('NFC', new_v)
            uitext_modified += 1

    # Also clean general calques in UIText
    for k, v in uitext.items():
        if isinstance(v, str):
            cv = clean_text(v)
            if cv != v:
                uitext[k] = cv
                uitext_modified += 1

    p_uitext.write_text(json.dumps(uitext, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated UIText: {uitext_modified} entries modified.")

    # 2. Remediate Item (00653)
    p_item = ENTRIES_DIR / "00653_0xe60634348b826f41.bin"
    items_data = json.loads(p_item.read_text(encoding="utf-8"))
    item_mod = 0
    for k, v in items_data.items():
        if isinstance(v, str):
            cv = clean_text(v)
            if cv != v:
                items_data[k] = cv
                item_mod += 1
    p_item.write_text(json.dumps(items_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated Item table: {item_mod} entries modified.")

    # 3. Remediate MonsterManual (00685)
    p_monster = ENTRIES_DIR / "00685_0x6509b9fe31bc8029.bin"
    monster_data = json.loads(p_monster.read_text(encoding="utf-8"))
    mon_mod = 0
    for k, v in monster_data.items():
        if isinstance(v, str):
            cv = clean_text(v)
            if cv != v:
                monster_data[k] = cv
                mon_mod += 1
    p_monster.write_text(json.dumps(monster_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated MonsterManual table: {mon_mod} entries modified.")

    # 4. Remediate DictionaryDiagram (00611)
    p_dict = ENTRIES_DIR / "00611_0xd46d025e8dae5d69.bin"
    dict_data = json.loads(p_dict.read_text(encoding="utf-8"))
    dict_mod = 0
    for k, v in dict_data.items():
        if isinstance(v, str):
            cv = clean_text(v)
            if cv != v:
                dict_data[k] = cv
                dict_mod += 1
    p_dict.write_text(json.dumps(dict_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated DictionaryDiagram table: {dict_mod} entries modified.")

    # 5. Remediate CharacterArchiveContent (00840)
    p_arch = ENTRIES_DIR / "00840_0x4a3c44844ee817d1.bin"
    arch_data = json.loads(p_arch.read_text(encoding="utf-8"))
    arch_mod = 0
    for k, v in arch_data.items():
        if isinstance(v, str):
            cv = clean_text(v)
            if cv != v:
                arch_data[k] = cv
                arch_mod += 1
    p_arch.write_text(json.dumps(arch_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated CharacterArchiveContent table: {arch_mod} entries modified.")

    # 6. Repack data_patched_vi.arcx
    print(f"\nRepacking {DEC_DIR} into {OUTPUT_ARCX}...")
    t0 = time.time()
    repack_archive(DEC_DIR, OUTPUT_ARCX, encrypt_payload=True)
    elapsed = time.time() - t0

    arc = ArcxArchive(OUTPUT_ARCX)
    print(f"SUCCESS! Repacked {OUTPUT_ARCX} in {elapsed:.2f}s:")
    print(f"  Size: {OUTPUT_ARCX.stat().st_size:,} bytes")
    print(f"  Entries: {len(arc.entries)}")

    # 7. Dual-Sync to Live Game (Standalone & Steam)
    live_targets = [
        Path(r"c:\YostarGames\StellaSora_EN") / "Persistent_Store" / "Tables" / "data.arcx",
        Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora") / "Persistent_Store" / "Tables" / "data.arcx"
    ]
    for target in live_targets:
        if target.parent.exists():
            print(f"Syncing to: {target}...")
            shutil.copy2(OUTPUT_ARCX, target)
            print(f"SUCCESS! Synced to {target} ({target.stat().st_size:,} bytes)")

    print("\nUI TABLES REMEDIATION & DUAL-SYNC COMPLETED!")

if __name__ == "__main__":
    main()
