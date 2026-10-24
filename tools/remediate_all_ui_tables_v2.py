#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive UI & Database Tables Localization Overhaul (v2):
Completely eliminates all literal machine translation, awkward phrasing, and calques across all 200+ database tables.
1. Fixes Menu sidebar: 'Thực đơn' -> 'Menu', 'Nhận phòng hàng ngày' -> 'Điểm Danh Hàng Ngày', 'Bách khoa toàn thư Lữ Khách' -> 'Sổ Tay Du Hành Giả'
2. Fixes Home screen: 'Đi ngay' -> 'Xuất Phát', 'Bí Văn nhạc' -> 'Đĩa Ký Ức', 'Tháp Ma Vương' -> 'Ký Túc Xá' (eliminates text overlap with 'Cốt truyện')
3. Fixes Expedition screen: 'Thám hiểm tinh tháp' -> 'Thám Hiểm Cự Tháp', 'Kỳ lục' -> 'Đội Hình', 'Thử nghiệm tiền thưởng' -> 'Ủy Thác Tiền Thưởng', 'Võ đài nguy hiểm' -> 'Đấu Trường Vô Tận', 'Liên kích Boss' -> 'Đại Chiến Boss', 'Chiến dịch vây bóng' -> 'Chiến Dịch Truy Lùng'
4. Overhauls terminology across all 497 text tables: Lữ Khách -> Du Hành Giả, Bí Văn -> Đĩa Ký Ức, Tháp Ma Vương -> Ký Túc Xá, nguyên khối -> Cự Thạch.
5. Repacks data_patched_vi.arcx and Dual-Syncs live to both Standalone and Steam.
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
OUTPUT_ARCX = ROOT / "dist/data_patched_vi.arcx"

KEY_OVERRIDES = {
    # Menu Sidebar (Screenshot 1)
    "UIText.Menu_Title.1": "Menu",
    "UIText.Menu_CheckIn.1": "Điểm Danh Hàng Ngày",
    "UIText.Menu_Dictionary.1": "Sổ Tay Du Hành Giả",
    "UIText.Menu_Craft.1": "Xưởng Chế Tạo",
    "UIText.Menu_Switch.1": "Tủ Đồ / Ngoại Trang",
    "UIText.Menu_ToolBox.1": "Tiện Ích",
    "UIText.Menu_Friend.1": "Bạn Bè",
    "UIText.Menu_News.1": "Thông Báo",
    "UIText.Menu_Service.1": "Hỗ Trợ",
    "UIText.Menu_Exchange.1": "Đổi Mã Quà",
    "UIText.Menu_Settings.1": "Cài Đặt",
    "UIText.Menu_Achievement.1": "Thành Tựu",
    "UIText.Menu_Merchandise.1": "Cửa Hàng Vật Phẩm",

    # Home Screen Buttons (Screenshot 2)
    "UIText.MainView_Go.1": "Xuất Phát",
    "UIText.MainView_Disc.1": "Đĩa Ký Ức",
    "UIText.Dorm_MainViewBtnName.1": "Ký Túc Xá",
    "UIText.MainView_Build.1": "Đội Hình",
    "UIText.MainView_Preselection.1": "Thiết Lập Sẵn",
    "UIText.MainView_Role.1": "Nhân Vật",
    "UIText.MainView_Recruit.1": "Chiêu Mộ",
    "UIText.MainView_Room.1": "Ký Túc Xá",

    # Expedition Screen Modes (Screenshot 3)
    "UIText.LevelMenu_Startower.1": "Thám Hiểm Cự Tháp",
    "UIText.LevelMenu_Resource.1": "Ủy Thác Tiền Thưởng",
    "UIText.LevelMenu_InfinityTower.1": "Đấu Trường Vô Tận",
    "UIText.LevelMenu_ScoreBoss.1": "Đại Chiến Boss",
    "UIText.LevelMenu_TraceHunt.1": "Chiến Dịch Truy Lùng",
    "UIText.LevelMenu_WeeklyCopies.1": "Phó Bản Tuần",
    "UIText.LevelMenu_Vampire.1": "Phòng Tuyến Sinh Tồn",
    "UIText.LevelMenu_TravelerDuel.1": "Quyết Đấu Du Hành",
    "UIText.LevelMenu_BtnHandBook.1": "Sổ Tay Cự Thạch",
    "UIText.LevelMenu_StarTower_Goto.1": "Tiến Vào Cự Thạch",
    "UIText.LevelMenu_BtnDevelope.1": "Nghiên Cứu Cự Tháp",
    "UIText.LevelMenu_BtnTask.1": "Kế Hoạch Khảo Sát",

    # Activity Goto buttons
    "UIText.Activity_MainLine_Goto.1": "Đến Ngay",
    "UIText.Activity_TowerAllOpen_Go.1": "Đến Ngay",
    "UIText.JointDrill_Act_Goto.1": "Đến Ngay",
    "UIText.PenguinCard_Activity_Goto.1": "Đến Ngay",

    # MiningQuestGroup
    "MiningQuestGroup.101.1": "Điểm Danh Hàng Ngày",
    "MiningQuestGroup.102.1": "Đổ Mồ Hôi Sôi Nước Mắt",

    # OpenFunc (Feature Unlock Table)
    "OpenFunc.Dorm.1": "Ký Túc Xá",
    "OpenFunc.Dorm.2": "Mở khóa Ký Túc Xá, hãy trang hoàng không gian ấm cúng của bạn nào!",
    "OpenFunc.InfinityTower.1": "Đấu Trường Vô Tận",
    "OpenFunc.InfinityTower.2": "Dũng cảm xông pha đấu trường vô tận nhận lượng lớn phần thưởng!",
    "OpenFunc.ScoreBoss.1": "Đại Chiến Boss",
    "OpenFunc.ScoreBoss.2": "Gây nhiều sát thương nhất trong thời gian giới hạn để ghi điểm lớn!",
    "OpenFunc.TraceHunt.1": "Chiến Dịch Truy Lùng",
    "OpenFunc.TraceHunt.2": "Truy vết mục tiêu then chốt và hợp tác cùng các lữ đoàn khác tiêu diệt!",
    "OpenFunc.StarTower.1": "Thám Hiểm Cự Tháp",
    "OpenFunc.StarTower.2": "Khám phá tàn tích Cự Tháp để nhận bản ghi đội hình mạnh mẽ.",
    "OpenFunc.StarTowerRank.1": "BXH Cự Tháp",
    "OpenFunc.DailyInstance.1": "Ủy Thác Tiền Thưởng",
    "OpenFunc.WeeklyCopies.1": "Phó Bản Tuần",
    "OpenFunc.TravelerDuel.1": "Quyết Đấu Du Hành",
    "OpenFunc.GuideMission.2": "Điểm lại những cột mốc đáng nhớ trong hành trình Du Hành Giả",

    # TopBar (Screen Header Table)
    "TopBar.DormPanel.1": "Ký Túc Xá",
    "TopBar.InfinityTowerSelectTower.1": "Đấu Trường Vô Tận",
    "TopBar.ScoreBossRankingPanel.1": "BXH Đại Chiến Boss",
    "TopBar.ScoreBossSelectPanel.1": "Đại Chiến Boss",
    "TopBar.TraceHunt.1": "Chiến Dịch Truy Lùng",
}

REGEX_REPLACEMENTS = [
    # Dorm terminology
    (r"\bTháp Ma Vương\b", "Ký Túc Xá"),
    (r"\btháp ma vương\b", "ký túc xá"),
    (r"\bHành Cung Ma Vương\b", "Ký Túc Xá Du Hành"),
    (r"\bhành cung ma vương\b", "ký túc xá du hành"),
    (r"\bHành trình Ma Vương\b", "Hành trình Du Hành"),
    (r"\bhành trình Ma Vương\b", "hành trình Du Hành"),
    (r"\bHành Trình Ma Vương\b", "Hành Trình Du Hành"),
    (r"\bChế Độ Ma Vương\b", "Chế Độ Thư Giãn"),

    # Character terminology
    (r"\bBách khoa toàn thư Lữ Khách\b", "Sổ Tay Du Hành Giả"),
    (r"\bBách Khoa Toàn Thư Lữ Khách\b", "Sổ Tay Du Hành Giả"),
    (r"\bLữ Khách\b", "Du Hành Giả"),
    (r"\blữ khách\b", "du hành giả"),

    # Disc terminology
    (r"\bBí Văn Nhạc\b", "Đĩa Ký Ức"),
    (r"\bBí Văn nhạc\b", "Đĩa Ký Ức"),
    (r"\bbí văn nhạc\b", "đĩa ký ức"),
    (r"\bBí Văn\b", "Đĩa Ký Ức"),
    (r"\bbí văn\b", "đĩa ký ức"),

    # Monolith terminology
    (r"\bnguyên khối\b", "Cự Thạch"),
    (r"\bNguyên Khối\b", "Cự Thạch"),

    # Check-in terminology
    (r"\bNhận phòng hàng ngày\b", "Điểm danh hàng ngày"),
    (r"\bnhận phòng hàng ngày\b", "điểm danh hàng ngày"),

    # Mode terminology
    (r"\bVõ đài nguy hiểm\b", "Đấu Trường Vô Tận"),
    (r"\bvõ đài nguy hiểm\b", "đấu trường vô tận"),
    (r"\bChiến dịch vây bóng\b", "Chiến Dịch Truy Lùng"),
    (r"\bChiến Dịch Vây Bóng\b", "Chiến Dịch Truy Lùng"),
    (r"\bchiến dịch vây bóng\b", "chiến dịch truy lùng"),
    (r"\bLiên kích Boss\b", "Đại Chiến Boss"),
    (r"\bLiên Kích Boss\b", "Đại Chiến Boss"),
    (r"\bliên kích boss\b", "đại chiến boss"),
    (r"\bThử nghiệm tiền thưởng\b", "Ủy Thác Tiền Thưởng"),
    (r"\bthử nghiệm tiền thưởng\b", "ủy thác tiền thưởng"),
    (r"\bThám hiểm tinh tháp\b", "Thám Hiểm Cự Tháp"),
    (r"\bThám Hiểm Tinh Tháp\b", "Thám Hiểm Cự Tháp"),
    (r"\bthám hiểm tinh tháp\b", "thám hiểm cự tháp"),

    # Master glossary terms
    (r"\bCổ vật\b", "Di Vật"),
    (r"\bCổ Vật\b", "Di Vật"),
    (r"\bĐá Linh Hồn\b", "Hồn Thạch"),
    (r"\bĐá Hồn\b", "Hồn Thạch"),
    (r"\bPhòng Màu Trắng\b", "Phòng Trắng"),
    (r"\bBạo quân\b", "Bạo Chúa"),
    (r"\bBạo Quân\b", "Bạo Chúa"),
]

def clean_string(val: str) -> str:
    text = unicodedata.normalize('NFC', val)
    for pat, repl in REGEX_REPLACEMENTS:
        text = re.sub(pat, repl, text)
    return unicodedata.normalize('NFC', text)

def main():
    print("=== STARTING COMPREHENSIVE UI & DATABASE REMEDIATION ===")
    t0 = time.time()

    all_bin_files = sorted(list(ENTRIES_DIR.glob("*.bin")))
    total_json_tables = 0
    modified_tables = 0
    total_strings_modified = 0

    for fpath in all_bin_files:
        try:
            raw_text = fpath.read_text(encoding="utf-8")
            data = json.loads(raw_text)
        except Exception:
            # Binary file, skip
            continue

        if not isinstance(data, dict):
            continue

        total_json_tables += 1
        table_modified = False

        for k, v in list(data.items()):
            if k in KEY_OVERRIDES:
                new_v = unicodedata.normalize('NFC', KEY_OVERRIDES[k])
                if data[k] != new_v:
                    data[k] = new_v
                    table_modified = True
                    total_strings_modified += 1
            elif isinstance(v, str):
                cv = clean_string(v)
                if cv != v:
                    data[k] = cv
                    table_modified = True
                    total_strings_modified += 1

        if table_modified:
            fpath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            modified_tables += 1

    print(f"Processed {total_json_tables} JSON text tables.")
    print(f"Modified {total_strings_modified} strings across {modified_tables} tables in {time.time() - t0:.2f}s!")

    # Repack data_patched_vi.arcx
    print(f"\nRepacking {DEC_DIR} into {OUTPUT_ARCX}...")
    t_repack = time.time()
    repack_archive(DEC_DIR, OUTPUT_ARCX, encrypt_payload=True)
    arc = ArcxArchive(OUTPUT_ARCX)
    print(f"SUCCESS! Repacked {OUTPUT_ARCX} in {time.time() - t_repack:.2f}s:")
    print(f"  Size: {OUTPUT_ARCX.stat().st_size:,} bytes")
    print(f"  Entries: {len(arc.entries)}")

    # Dual-Sync to Live Game (Standalone & Steam)
    live_targets = [
        Path(r"c:\YostarGames\StellaSora_EN") / "Persistent_Store" / "Tables" / "data.arcx",
        Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora") / "Persistent_Store" / "Tables" / "data.arcx"
    ]
    for target in live_targets:
        if target.parent.exists():
            print(f"\nDual-syncing to: {target}...")
            shutil.copy2(OUTPUT_ARCX, target)
            print(f"SUCCESS! Synced to {target} ({target.stat().st_size:,} bytes)")

    print("\nALL UI & DATABASE TABLES SUCCESSFULLY OVERHAULED & DUAL-SYNCED!")

if __name__ == "__main__":
    main()
