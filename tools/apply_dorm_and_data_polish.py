# -*- coding: utf-8 -*-
"""
Script to apply Dormitory / Camping UI polish and Terminology updates to data tables.
Updates:
1. UIText (00789_0x87cc29ac0defc2d9.bin):
   - DormBtn_Role: "Bố Trí Nhân Vật" (was "Bố Trí Đình Thần")
   - Dorm_CharListTitle: "Bố Trí Nhân Vật" (was "Bố Trí Đình Thần")
   - DormTips_RoleFull: "Số Lượng Nhân Vật Đã Đầy" (was "Đình Thần Đã Đầy")
   - Guide_524_1: "Mấy đứa tụi tôi cũng muốn xuống xe đi dạo cùng Bạo Chúa!\nNhấn <color=#EA5946>Bố Trí Nhân Vật</color> nào!"
   - Guide_524_4: "Xem ra Amber lại muốn được Bạo Chúa xoa đầu rồi.\nSau khi tiến lại gần người bạn du hành giả, nhấn <color=#EA5946>Xoa Đầu</color> là có thể tương tác với cô ấy!"
   - DormBtn_Visit: "Thăm Bạn" (was "Tuần Du")
   - DormBtn_Edior: "Bài Trí" (was "Trưng Bày Bảo Vật")
   - Guide_522_1: "Đã đến lúc bắt đầu bài trí khu cắm trại rồi!\nNhấn <color=#EA5946>Bài Trí</color> để xem có nội thất nào có thể đặt được nhé!"
   - DormBtn_BossMode: "Chế Độ Tự Do" (was "Chế Độ Thư Giãn")
   - Guide_526_1: "Ở <color=#EA5946>Chế Độ Tự Do</color>, bạn có thể trực tiếp điều khiển Bạo Chúa để tương tác với bạn đồng hành hoặc nội thất.\nỞ <color=#EA5946>Chế Độ Ngắm Cảnh</color>, có thể quan sát toàn cảnh từ góc nhìn trên cao.\nNhấn nút để chuyển đổi giữa hai chế độ."
   - DormQuest_Title: "Nhiệm Vụ Ký Túc Xá" (was "Con Đường Thu Thập Kho Báu")
   - Dorm_HandBook_Title: "Sổ Tay Nội Thất" (was "Danh Sách Bảo Vật")
   - Dorm_HandBook_Tog2: "Bộ Nội Thất" (was "Bộ Bảo Vật")
   - Dorm_HandBook_Tog3: "Minh Họa Nội Thất" (was "Minh Họa Bảo Vật")
   - Dorm_MainMenu_FurnitureReward: "Sổ Tay Nội Thất" (was "Danh Sách Bảo Vật")

2. DictionaryDiagram (00616_0x88d705ae9564e65e.bin):
   - 70010401.2: "Trong Chế Độ Tự Do, bạn có thể trực tiếp điều khiển Bạo Chúa di chuyển tự do khắp căn phòng."
   - 70010601.2: "Nhấn nút để chuyển đổi linh hoạt giữa Chế Độ Tự Do và Chế Độ Ngắm Cảnh.\nỞ Chế Độ Tự Do, bạn có thể điều khiển Bạo Chúa tương tác với Du Hành Giả và nội thất.\nỞ Chế Độ Ngắm Cảnh, có thể quan sát toàn cảnh căn phòng từ góc nhìn trên cao."

3. DormQuest (00624_0x20a8feef4911d428.bin):
   - DormQuest.500016.1: "Đặt nội thất [Bốt Tâm Liên]" (was "Đặt nội thất [Chòi Tâm Liên]")

4. DormLayoutReward (00623_0x128234a91c526c13.bin):
   - DormLayoutReward.731002.4: "Nhận khi hoàn thành nhiệm vụ Ký Túc Xá"

5. Item (00653_0xe60634348b826f41.bin & 00900_0xdb546f14f2f79a11.bin):
   - Item.700001.1: "Bốt Tâm Liên" (was "Chòi Tâm Liên")
"""

import json
from pathlib import Path
import sys
import time

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))
from arcx_adapter import repack_archive

ENTRIES_DIR = ROOT / "work" / "research" / "data_200_decrypted" / "entries"
DEC_DIR = ROOT / "work" / "research" / "data_200_decrypted"
OUTPUT_ARCX = ROOT / "dist" / "data_patched_vi.arcx"

def update_json_file(filename: str, updates: dict):
    fpath = ENTRIES_DIR / filename
    if not fpath.exists():
        raise FileNotFoundError(f"Missing {fpath}")
    data = json.loads(fpath.read_text(encoding="utf-8"))
    modified = 0
    for k, v in updates.items():
        if k in data:
            old_v = data[k]
            if old_v != v:
                data[k] = v
                modified += 1
                print(f"  [{filename}] {k}: '{old_v}' -> '{v}'")
        else:
            print(f"  [WARNING] Key not found in {filename}: {k}")
    fpath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated {filename}: {modified} keys changed.")

def main():
    print("=== APPLYING DORM AND DATA TABLE LOCALIZATION FIXES ===")
    
    # 1. UIText
    uitext_fixes = {
        "UIText.DormBtn_Role.1": "Bố Trí Nhân Vật",
        "UIText.Dorm_CharListTitle.1": "Bố Trí Nhân Vật",
        "UIText.DormTips_RoleFull.1": "Số Lượng Nhân Vật Đã Đầy",
        "UIText.Guide_524_1.1": "Mấy đứa tụi tôi cũng muốn xuống xe đi dạo cùng Bạo Chúa!\nNhấn <color=#EA5946>Bố Trí Nhân Vật</color> nào!",
        "UIText.Guide_524_4.1": "Xem ra Amber lại muốn được Bạo Chúa xoa đầu rồi.\nSau khi tiến lại gần người bạn du hành giả, nhấn <color=#EA5946>Xoa Đầu</color> là có thể tương tác với cô ấy!",
        "UIText.DormBtn_Visit.1": "Thăm Bạn",
        "UIText.DormBtn_Edior.1": "Bài Trí",
        "UIText.Guide_522_1.1": "Đã đến lúc bắt đầu bài trí khu cắm trại rồi!\nNhấn <color=#EA5946>Bài Trí</color> để xem có nội thất nào có thể đặt được nhé!",
        "UIText.DormBtn_BossMode.1": "Chế Độ Tự Do",
        "UIText.Guide_526_1.1": "Ở <color=#EA5946>Chế Độ Tự Do</color>, bạn có thể trực tiếp điều khiển Bạo Chúa để tương tác với bạn đồng hành hoặc nội thất.\nỞ <color=#EA5946>Chế Độ Ngắm Cảnh</color>, có thể quan sát toàn cảnh từ góc nhìn trên cao.\nNhấn nút để chuyển đổi giữa hai chế độ.",
        "UIText.DormQuest_Title.1": "Nhiệm Vụ Ký Túc Xá",
        "UIText.Dorm_HandBook_Title.1": "Sổ Tay Nội Thất",
        "UIText.Dorm_HandBook_Tog2.1": "Bộ Nội Thất",
        "UIText.Dorm_HandBook_Tog3.1": "Minh Họa Nội Thất",
        "UIText.Dorm_MainMenu_FurnitureReward.1": "Sổ Tay Nội Thất",
    }
    update_json_file("00789_0x87cc29ac0defc2d9.bin", uitext_fixes)
    
    # 2. DictionaryDiagram
    dict_fixes = {
        "DictionaryDiagram.70010401.2": "Trong Chế Độ Tự Do, bạn có thể trực tiếp điều khiển Bạo Chúa di chuyển tự do khắp căn phòng.",
        "DictionaryDiagram.70010601.2": "Nhấn nút để chuyển đổi linh hoạt giữa Chế Độ Tự Do và Chế Độ Ngắm Cảnh.\nỞ Chế Độ Tự Do, bạn có thể điều khiển Bạo Chúa tương tác với Du Hành Giả và nội thất.\nỞ Chế Độ Ngắm Cảnh, có thể quan sát toàn cảnh căn phòng từ góc nhìn trên cao.",
    }
    update_json_file("00616_0x88d705ae9564e65e.bin", dict_fixes)
    
    # 3. DormQuest
    dormquest_fixes = {
        "DormQuest.500016.1": "Đặt nội thất [Bốt Tâm Liên]",
    }
    update_json_file("00624_0x20a8feef4911d428.bin", dormquest_fixes)
    
    # 4. DormLayoutReward
    dormreward_fixes = {
        "DormLayoutReward.731002.4": "Nhận khi hoàn thành nhiệm vụ Ký Túc Xá",
    }
    update_json_file("00623_0x128234a91c526c13.bin", dormreward_fixes)
    
    # 5. Item
    item_fixes = {
        "Item.700001.1": "Bốt Tâm Liên",
    }
    update_json_file("00653_0xe60634348b826f41.bin", item_fixes)
    if (ENTRIES_DIR / "00900_0xdb546f14f2f79a11.bin").exists():
        update_json_file("00900_0xdb546f14f2f79a11.bin", item_fixes)

    # Repack dist/data_patched_vi.arcx
    print(f"\nRepacking {DEC_DIR} into {OUTPUT_ARCX}...")
    t0 = time.time()
    repack_archive(DEC_DIR, OUTPUT_ARCX, encrypt_payload=True)
    print(f"Repack complete in {time.time() - t0:.2f}s! Size: {OUTPUT_ARCX.stat().st_size:,} bytes")

if __name__ == "__main__":
    main()
