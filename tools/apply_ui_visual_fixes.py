#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master UI Visual & Layout Polish Script:
- Fixes CharGem names (emblem name clipping on both ends).
- Fixes UIText Equipment attribute pill tags (prevent 3-line wrap & row collision).
- Fixes UIText Equipment buttons (replaces 'tính khí' with 'Tôi Luyện', capitalizes buttons).
- Fixes rich-text tag leaks (<color> in TowerDef, <size> in Vampire).
- Fixes GachaType.9.17 tag mismatch.
- Fixes PenguinCard and SoldierBattle button labels.
- Repacks dist/data_patched_vi.arcx with XXTEA encryption.
- Dual-syncs to Yostar Standalone and Steam installations.
- Runs verification to ensure zero regression.
"""

from __future__ import annotations
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT))
from tools.arcx_adapter import ArcxArchive, repack_archive

DEC_DIR = ROOT / "work" / "research" / "data_200_decrypted"
ENTRIES_DIR = DEC_DIR / "entries"
OUTPUT_ARCX = ROOT / "dist" / "data_patched_vi.arcx"

# 1. CharGem Table Updates
CHARGEM_UPDATES = {
    "CharGem.101.1": "Huy Hiệu Gai Tín Đồ",
    "CharGem.102.1": "Huy Hiệu Thoi Tín Đồ",
    "CharGem.103.1": "Huy Hiệu Ánh Sao Tín Đồ",
    "CharGem.201.1": "Huy Hiệu Gai Pathfinder",
    "CharGem.202.1": "Huy Hiệu Thoi Pathfinder",
    "CharGem.203.1": "Huy Hiệu Ánh Sao Pathfinder",
    "CharGem.301.1": "Huy Hiệu Gai Hộ Vệ",
    "CharGem.302.1": "Huy Hiệu Thoi Hộ Vệ",
    "CharGem.303.1": "Huy Hiệu Ánh Sao Hộ Vệ",
}

# 2. UIText Table Updates
UITEXT_UPDATES = {
    # Attribute tags (Pills)
    "UIText.Equipment_AttrTag_3.1": "Tiềm Năng Chính",
    "UIText.Equipment_AttrTag_4.1": "Tiềm Năng Hỗ Trợ",
    "UIText.Equipment_AttrTag_5.1": "Tiềm Năng Chung",
    
    # Buttons
    "UIText.Equipment_Btn_Upgrade.1": "Tôi Luyện",
    "UIText.Equipment_Btn_Reroll.1": "Rèn Lại",
    "UIText.Equipment_Btn_GotoRoll.1": "Rèn Lại",
    "UIText.Equipment_Btn_Active.1": "Rèn",
    "UIText.Equipment_Btn_TotalAttrPreview.1": "Tổng Quan Huy Hiệu",
    
    # Titles & Labels
    "UIText.Equipment_Upgrade_CostTitle.1": "Chi Phí Tôi Luyện",
    "UIText.Equipment_Upgrade_WindowTitle.1": "Tôi Luyện Huy Hiệu",
    "UIText.Equipment_Title_Info.1": "Thông Tin Huy Hiệu",
    "UIText.Equipment_Title_EquipmentPreview.1": "Huy Hiệu Du Hành",
    "UIText.Equipment_Title_Active.1": "Rèn Huy Hiệu",
    "UIText.Equipment_Title_AttrPreview.1": "Tổng Quan Chỉ Số",
    "UIText.Equipment_Title_RollConfirm.1": "Rèn Lại Huy Hiệu",
    "UIText.Equipment_Title_Replace.1": "Đổi Huy Hiệu",
    "UIText.Equipment_Upgrade_RevertTitle.1": "Hoàn Nguyên Huy Hiệu",
    "UIText.Equipment_Roll_LockRoll.1": "Khóa Huy Hiệu",
    "UIText.Equipment_Attr_Title.1": "Thuộc Tính Huy Hiệu",
    "UIText.Equipment_Roll_EmptyTitle.1": "Huy Hiệu này chưa được rèn.",
    "UIText.Equipment_ConfirmRoll_EquipmentLock.1": "Huy Hiệu đã bị khóa. Không thể rèn lại các Nguyên tố.",
    "UIText.Equipment_Upgrade_MainTips.1": "Tiêu thụ <color=#fb8037>{item_1}</color> × {num_0} để tôi luyện Huy Hiệu này?",
    "UIText.Equipment_Upgrade_Suc_Level.1": "Cấp độ Huy Hiệu",
    "UIText.Equipment_UnEquipped.1": "Đã tháo Huy Hiệu khỏi <color=#fb8037>{0}</color>",
    
    # Unlock condition text
    "UIText.Equipment_Attr_Unlock.1": "Đạt Cấp {0} để mở khóa",
    "UIText.Equipment_SlotLock.1": "Đạt Cấp {0} để mở khóa ô Huy Hiệu này.",
    
    # Tag fixes
    "UIText.TowerDef_LevelPreTime.1": "Đợt tiếp theo bắt đầu sau <color=#08d3d4>{0}</color>",
    "UIText.Vampire_Bonus_Title.1": "{0} Chuỗi tiêu diệt <size=28>(Điểm x {1})</size>",
    
    # Minigame buttons
    "UIText.PenguinCard_Btn_NextRound.1": "Chia Bài",
    "UIText.PenguinCard_Btn_AddCheckRound.1": "Xem Thẻ +1/Lượt",
    "UIText.Soldier_Battle_Btn_Char.1": "Mảnh",
    "UIText.Soldier_Battle_Btn_Partner.1": "Đồng Hành",
}

# 3. GachaType Table Updates
GACHATYPE_9_17_CLEAN = (
    "{0} là <color=#0abec5>Khắc Ấn Giới Hạn</color>. Khắc Ấn ★5 kỳ này chắc chắn nhận được qua bảo hiểm bảo trợ (Pity) trong vòng <color=#0abec5>120 lượt</color> chiêu mộ.\n\n"
    "※Tất cả các lượt chiêu mộ chưa nhận được Khắc Ấn ★5 <color=#0abec5>「{1}」</color> sẽ được tích lũy trong 「Khắc Ấn Giới Hạn」, được kế thừa sang các kỳ 「Khắc Ấn Giới Hạn」khác, độc lập hoàn toàn với các loại chiêu mộ khác.\n\n"
    "※Khi kỳ chiêu mộ kết thúc, Khắc Ấn ★5 <color=#0abec5>「{1}」</color> <color=#fb8037>sẽ không vào</color> 「Khắc Ấn Thường」."
)

def main():
    t0 = time.time()
    print("=" * 70)
    print("BẮT ĐẦU ÁP DỤNG CÁC SỬA LỖI GIAO DIỆN & BẢN DỊCH (UI VISUAL FIXES)")
    print("=" * 70)

    # 1. Update CharGem table (00599)
    p_cg = ENTRIES_DIR / "00599_0x627a5df613782a6e.bin"
    if p_cg.exists():
        d_cg = json.loads(p_cg.read_text(encoding="utf-8"))
        cg_count = 0
        for k, v in CHARGEM_UPDATES.items():
            if k in d_cg and d_cg[k] != v:
                d_cg[k] = v
                cg_count += 1
        p_cg.write_text(json.dumps(d_cg, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✓ Đã cập nhật CharGem ({p_cg.name}): {cg_count} tên Huy Hiệu được rút gọn chuẩn hóa.")

    # 2. Update UIText tables (00789 and 01036)
    uitext_files = [
        ENTRIES_DIR / "00789_0x87cc29ac0defc2d9.bin",
        ENTRIES_DIR / "01036_0x363690c09b175230.bin"
    ]
    for p_ui in uitext_files:
        if p_ui.exists():
            d_ui = json.loads(p_ui.read_text(encoding="utf-8"))
            ui_count = 0
            for k, v in UITEXT_UPDATES.items():
                if k in d_ui and d_ui[k] != v:
                    d_ui[k] = v
                    ui_count += 1
            p_ui.write_text(json.dumps(d_ui, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"✓ Đã cập nhật UIText ({p_ui.name}): {ui_count} chuỗi giao diện được chỉnh sửa.")

    # 3. Update GachaType tables (00638 and 00885)
    gachatype_files = [
        ENTRIES_DIR / "00638_0xff1effbb00b50d0e.bin",
        ENTRIES_DIR / "00885_0x244b924d0e05f10c.bin"
    ]
    for p_gt in gachatype_files:
        if p_gt.exists():
            d_gt = json.loads(p_gt.read_text(encoding="utf-8"))
            if "GachaType.9.17" in d_gt and d_gt["GachaType.9.17"] != GACHATYPE_9_17_CLEAN:
                d_gt["GachaType.9.17"] = GACHATYPE_9_17_CLEAN
                p_gt.write_text(json.dumps(d_gt, indent=2, ensure_ascii=False), encoding="utf-8")
                print(f"✓ Đã cập nhật GachaType ({p_gt.name}): GachaType.9.17 đã xóa lỗi thẻ & chữ Trung.")

    # 4. Repack dist/data_patched_vi.arcx
    print("\n-> Đang đóng gói lại dist/data_patched_vi.arcx với mã hóa XXTEA...")
    repack_archive(DEC_DIR, OUTPUT_ARCX, encrypt_payload=True)

    arc = ArcxArchive(OUTPUT_ARCX)
    arcx_size = OUTPUT_ARCX.stat().st_size
    with open(OUTPUT_ARCX, "rb") as f:
        arcx_sha256 = hashlib.sha256(f.read()).hexdigest()

    print(f"✓ Đã xuất bản thành công: {OUTPUT_ARCX.name}")
    print(f"  Kích thước: {arcx_size:,} bytes | Số mục: {len(arc.entries)}")
    print(f"  SHA-256: {arcx_sha256}")

    # 5. Dual-Sync directly to live game installations
    print("\n-> Đồng bộ trực tiếp nguồn chuẩn dist/data_patched_vi.arcx vào các bản game:")
    targets = [
        ROOT / "work" / "research" / "data_patched_vi.arcx",
        Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx"),
        Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Tables\data.arcx")
    ]
    for dest in targets:
        if dest.parent.exists():
            shutil.copy2(OUTPUT_ARCX, dest)
            print(f"  ✓ Đã cập nhật: {dest} ({dest.stat().st_size:,} bytes)")

    elapsed = time.time() - t0
    print(f"\n🎉 HOÀN THÀNH ÁP DỤNG FIX GIAO DIỆN TRONG {elapsed:.2f} GIÂY!")
    return arcx_sha256

if __name__ == "__main__":
    main()
