# -*- coding: utf-8 -*-
"""
Script to apply comprehensive terminology and pronoun consistency fixes to all data tables.
Target Fixes:
1. Character Names:
   - "Hệ thực vật" / "hệ thực vật" -> "Flora" (in Potential & AssistQuest)
   - "Hổ phách" -> "Amber" (in AssistQuest)
   - "Đom Đóm" -> "Firefly" (in BreakOutCharacter)
2. Dungeon / Monster Boss terminology:
   - "Ông chủ đến đây Ⅰ/Ⅱ/Ⅲ" -> "Thủ Lĩnh Xuất Hiện Ⅰ/Ⅱ/Ⅲ"
   - "Ông chủ Stellaroid đang ở đây!" -> "Thủ Lĩnh Stellaroid Đang Ở Đây!"
   - "Ông chủ đã lên! Ⅰ/Ⅱ" -> "Thủ Lĩnh Đã Lên Ⅰ/Ⅱ"
   - UIText: "Chúa tể đến" -> "Thủ Lĩnh Xuất Hiện", "chúa tể" -> "Số Lượng Thủ Lĩnh"
3. Promotion & Mechanics:
   - UIText: "Yêu cầu khuyến mãi" -> "Điều Kiện Phong Cấp", "Khuyến mãi dành cho Du Hành Giả" -> "Phong Cấp Du Hành Giả"
   - Item: "Hộp khuyến mãi dành cho người mới đi Du Hành Giả" -> "Hộp Quà Tân Thủ Du Hành Giả"
   - Item: "Hộp khuyến mãi Du Hành Giả cao cấp" -> "Hộp Quà Du Hành Giả Cao Cấp"
   - Item: "Hộp khuyến mãi đĩa..." -> "Hộp Quà Đĩa Âm Nhạc..."
   - ResidentGoods: "Hộp khuyến mãi dành cho người mới đi Lữ khách" -> "Hộp Quà Tân Thủ Du Hành Giả"
   - MainSkill: "hệ Quang phượt thủ đa năng" -> "Du Hành Giả Toàn Năng hệ Quang"
4. Potential skill calques:
   - "thua ##Tiêu Ký Thợ Săn#4046#" -> "mất ##Tiêu Ký Thợ Săn#4046#"
   - "Umbra Auto Tấn công sát thương" -> "Sát Thương Đòn Đánh Tự Động hệ Ám"
   - "đội toàn Umbra" / "đội hình toàn Umbra" -> "đội hình thuần hệ Ám"
   - "đồng đội Umbra" -> "đồng đội hệ Ám"
   - "những Du Hành Giả đa năng Umbra" -> "những Du Hành Giả Toàn Năng hệ Ám"
   - "Boss Shark" -> "Cá Mập Thủ Lĩnh"
   - "Biển Raging" / "Biển cuồng nộ" -> "Biển Nộ Cuộn Trào"
   - "Mồi và Bắt" -> "Mồi Và Lưỡi Câu"
   - "Auto Tấn công" / "Auto Tấn Công" -> "Đòn Đánh Tự Động"
5. Elements in BdConvertCondition:
   - "Triển khai Lux Du Hành Giả làm Du Hành Giả chính" -> "Triển khai Du Hành Giả hệ Quang làm Du Hành Giả chính"
   - "Yếu tố Du Hành Giả chính là Lux hoặc Ám" -> "Thuộc tính của Du Hành Giả chính là Quang hoặc Ám"
6. Grace & Soul Stone in items:
   - "Đá linh hồn" / "đá linh hồn" -> "Hồn Thạch" / "hồn thạch"
   - "đồ tạo tác phục vụ đồ ăn" -> "di vật phục vụ đồ ăn"
   - "Một Đồ tạo tác" -> "Một Di Vật"
   - "Thần Ân Điển" -> "Thần Ân Tứ"
   - "Dấu ấn Ân điển" -> "Ấn Ký Ân Tứ"
7. Character lines:
   - "Cảm ơn Chúa Tể đã đến chứng kiến..." -> "Cảm ơn Bạo Chúa đã đến chứng kiến..."
   - "...lát nữa em sẽ gửi qua tin nhắn cho anh nhé." -> "...lát nữa em sẽ gửi qua tin nhắn cho Sếp nhé."
"""

import json
from pathlib import Path
import re
import sys
import time

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))
from arcx_adapter import repack_archive

ENTRIES_DIR = ROOT / "work" / "research" / "data_200_decrypted" / "entries"
DEC_DIR = ROOT / "work" / "research" / "data_200_decrypted"
OUTPUT_ARCX = ROOT / "dist" / "data_patched_vi.arcx"

def apply_table_replacements():
    print("=== APPLYING DATA TABLE REPLACEMENTS ===")
    total_files_modified = 0
    total_keys_modified = 0

    # Specific replacements mapping
    EXACT_REPLACEMENTS = {
        # Dungeon boss names
        "ActivityLevelsLevel.1070112.1": "Thủ Lĩnh Xuất Hiện Ⅰ",
        "ActivityLevelsLevel.1070112.2": "Thủ Lĩnh Stellaroid đang ở đây! Những kẻ gây rối trên địa bàn của nó sẽ không thoát khỏi sự trừng phạt...",
        "ActivityLevelsLevel.1070208.1": "Thủ Lĩnh Xuất Hiện Ⅱ",
        "ActivityLevelsLevel.1070304.1": "Thủ Lĩnh Xuất Hiện Ⅲ",
        "ActivityLevelsLevel.1110112.1": "Thủ Lĩnh Đã Lên Ⅰ",
        "ActivityLevelsLevel.1110208.1": "Thủ Lĩnh Đã Lên Ⅱ",
        "UIText.CommonMonsterWarning_Boss.1": "Thủ Lĩnh Xuất Hiện",
        "UIText.VampireSettle_LordCount.1": "Số Lượng Thủ Lĩnh",

        # Promotion UI & Items
        "UIText.InfinityTower_Promotion_Conditions.1": "Điều Kiện Phong Cấp",
        "UIText.LevelMenu_SRegion.1": "Phong Cấp Du Hành Giả",
        "Item.82001.1": "Hộp Quà Tân Thủ Du Hành Giả",
        "Item.82002.1": "Hộp Quà Du Hành Giả Cao Cấp",
        "Item.82002.2": "Nhận một nguyên liệu phong cấp Du Hành Giả trung cấp từ Bản dùng thử theo cấp độ tự chọn",
        "Item.82003.1": "Hộp Quà Du Hành Giả Cao Cấp",
        "Item.82003.2": "Nhận một nguyên liệu phong cấp Du Hành Giả cao cấp từ Bản dùng thử theo cấp độ tự chọn.",
        "Item.82004.1": "Hộp Quà Đĩa Âm Nhạc Tân Thủ",
        "Item.82005.1": "Hộp Quà Đĩa Âm Nhạc Cao Cấp",
        "Item.82006.1": "Hộp Quà Đĩa Âm Nhạc Cao Cấp",
        "ResidentGoods.104.1": "Hộp Quà Tân Thủ Du Hành Giả",

        # Character lines
        "CharGetLines.10704.1": "Cảm ơn Bạo Chúa đã đến chứng kiến những bước chân đầu tiên trên con đường trở thành anh hùng của em!",
        "CharGetLines.10301.1": "Em là Amber.\n...Iris có viết sẵn cho em một bản tự giới thiệu, lát nữa em sẽ gửi qua tin nhắn cho Sếp nhé.",

        # Character breakout
        "BreakOutCharacter.11501.1": "Firefly",

        # BdConvertCondition
        "BdConvertCondition.605.1": "Triển khai Du Hành Giả hệ Quang làm Du Hành Giả chính",
        "BdConvertCondition.610.1": "Thuộc tính của Du Hành Giả chính là Quang hoặc Ám",

        # Disc & Partner
        "DiscIP.214036.4": '"Thiên thần sao...? Đã đến lúc rồi ư...?"\n"Không phải đâu, bé con. Nhìn kỹ lại xem nào—đây là Thần Ân Tứ mà."',
        "SoldierPartnerGroup.4.2": "Khi một mảnh Ý Chí Ân Tứ sử dụng một kỹ năng, nó sẽ áp dụng Ấn Ký Ân Tứ cho tất cả kẻ địch trong phạm vi.",
    }

    # Pattern replacements across all tables
    REGEX_RULES = [
        # Flora in character context
        (r'\bNâng cấp hệ thực vật\b', 'Nâng cấp Flora'),
        (r'\bNâng cấp Hệ thực vật\b', 'Nâng cấp Flora'),
        (r'\bHệ thực vật và Kasimira\b', 'Flora và Kasimira'),
        (r'\bTăng &Param2& của Hệ thực vật\b', 'Tăng &Param2& của Flora'),
        (r'\bTăng &Param4& của Hệ thực vật\b', 'Tăng &Param4& của Flora'),

        # Amber in AssistQuest
        (r'\bNâng cấp Hổ phách\b', 'Nâng cấp Amber'),
        (r'\bvới Hổ phách là Chính\b', 'với Amber là Chính'),

        # Phượt thủ đa năng in MainSkill
        (r'\bhệ Quang phượt thủ đa năng\b', 'Du Hành Giả Toàn Năng hệ Quang'),
        (r'\bphượt thủ đa năng\b', 'Du Hành Giả Toàn Năng'),

        # Potential mechanics
        (r'\bthua ##Tiêu Ký Thợ Săn#4046#\b', 'mất ##Tiêu Ký Thợ Săn#4046#'),
        (r'diện rộng Umbra Auto Tấn công sát thương', 'Sát Thương Đòn Đánh Tự Động hệ Ám diện rộng'),
        (r'Umbra Auto Tấn công sát thương', 'Sát Thương Đòn Đánh Tự Động hệ Ám'),
        (r'Auto Tấn công', 'Đòn Đánh Tự Động'),
        (r'Auto Tấn Công', 'Đòn Đánh Tự Động'),
        (r'\bTrong đội toàn Umbra\b', 'Trong đội hình thuần hệ Ám'),
        (r'\bTrong đội hình toàn Umbra\b', 'Trong đội hình thuần hệ Ám'),
        (r'\btất cả đồng đội Umbra\b', 'tất cả đồng đội hệ Ám'),
        (r'\bnhững Du Hành Giả đa năng Umbra\b', 'những Du Hành Giả Toàn Năng hệ Ám'),
        (r'\bDu Hành Giả đa năng Umbra\b', 'Du Hành Giả Toàn Năng hệ Ám'),
        (r'\bBoss Shark\b', 'Cá Mập Thủ Lĩnh'),
        (r'\bBiển Raging\b', 'Biển Nộ Cuộn Trào'),
        (r'\bBiển cuồng nộ\b', 'Biển Nộ Cuộn Trào'),
        (r'\bMồi và Bắt\b', 'Mồi Và Lưỡi Câu'),

        # Items and artifacts
        (r'\bĐá linh hồn\b', 'Hồn Thạch'),
        (r'\bđá linh hồn\b', 'hồn thạch'),
        (r'\bđồ tạo tác phục vụ đồ ăn\b', 'di vật phục vụ đồ ăn'),
        (r'\bMột Đồ tạo tác có thể\b', 'Một Di Vật có thể'),
        (r'\bĐồ tạo tác\b', 'Di Vật'),
        (r'\bđồ tạo tác\b', 'di vật'),
        (r'\bCổ vật Bán hàng Tự động\b', 'Di Vật Bán Hàng Tự Động'),
    ]

    for fpath in ENTRIES_DIR.glob("*.bin"):
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
        except Exception:
            continue

        file_modified = False
        for k, v in list(data.items()):
            if not isinstance(v, str):
                continue
            
            orig_v = v
            # 1. Check exact replacement
            if k in EXACT_REPLACEMENTS:
                v = EXACT_REPLACEMENTS[k]

            # 2. Check regex patterns
            for pattern, repl in REGEX_RULES:
                v = re.sub(pattern, repl, v)

            if v != orig_v:
                data[k] = v
                file_modified = True
                total_keys_modified += 1
                # print(f"  [{fpath.name}] {k}: '{orig_v}' -> '{v}'")

        if file_modified:
            fpath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            total_files_modified += 1

    print(f"Data tables updated: {total_files_modified} files, {total_keys_modified} keys patched.")

def repack_data_arcx():
    print(f"\nRepacking data archive to {OUTPUT_ARCX}...")
    t0 = time.time()
    repack_archive(DEC_DIR, OUTPUT_ARCX, encrypt_payload=False)
    print(f"Repack completed in {time.time()-t0:.2f}s. Output size: {OUTPUT_ARCX.stat().st_size:,} bytes")

def main():
    apply_table_replacements()
    repack_data_arcx()

if __name__ == "__main__":
    main()
