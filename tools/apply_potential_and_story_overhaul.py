#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Overhaul Character Potentials and Story Navigation Cards (Campaign 24)
---------------------------------------------------------------------
1. Fix 275 character potential names in Item (00653) & Item twin (00900)
   - Eliminates MT blunders: 'đình công vu khống', 'quét dấu gạch ngang', 'mật khẩu an toàn',
     'vòi hoa sen kim', 'bóng móng tay', 'hiến pháp chống băng giá', 'thời gian khuyến mãi',
     'bộ đếm hiện tại', 'bóng chuyền khu vực', 'dây phơi', 'người quét rác', v.v.
   - Enforces Title Case across all potentials.
2. Fix Story UI Navigation in UIText (00789/01036) & TopBar (00769/01016)
   - 'The Nova Times' -> 'Thời Báo Nova'
   - 'Event Review' -> 'Hồi Tưởng Sự Kiện'
   - 'Previous Event Stories' -> 'Cốt Truyện Sự Kiện Kỳ Trước'
   - 'What's new in Nova' -> 'Chuyện Chốn Phương Xa Cũng Gắn Liền Với Bạn'
   - Harmonize related story review keys.
3. Repack dist/data_patched_vi.arcx with XXTEA encryption.
4. Dual-deploy to Yostar and Steam installations.
5. Anti-regression verification via tools/verify_deployed_game_data.py.
"""

from __future__ import annotations
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT))
from tools.arcx_adapter import ArcxArchive, repack_archive

DEC_DIR = ROOT / "work" / "research" / "data_200_decrypted"
ENTRIES_DIR = DEC_DIR / "entries"
OUTPUT_ARCX = ROOT / "dist" / "data_patched_vi.arcx"
PROPOSAL_FILE = ROOT / "work" / "research" / "potential_and_story_overhaul_proposals.json"

LIVE_YOSTAR_DATA = Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx")
LIVE_STEAM_DATA = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Tables\data.arcx")

def main():
    t0 = time.time()
    print("=" * 80)
    print("BẮT ĐẦU ĐẠI TU TIỀM NĂNG 40 NHÂN VẬT & 2 GIAO DIỆN CỐT TRUYỆN (CAMPAIGN 24)")
    print("=" * 80)

    assert PROPOSAL_FILE.exists(), f"Proposal file missing: {PROPOSAL_FILE}"
    proposal_data = json.loads(PROPOSAL_FILE.read_text(encoding="utf-8"))

    story_proposals = proposal_data.get("story_and_ui_proposals", {})
    potential_proposals = proposal_data.get("potential_items_proposals", {})

    print(f"-> Nạp {len(potential_proposals)} đề xuất sửa đổi Thẻ Tiềm Năng.")
    print(f"-> Nạp {len(story_proposals)} đề xuất sửa đổi Giao diện Cốt Truyện.")

    # ---------------------------------------------------------------------
    # 1. CẬP NHẬT ITEM (00653 & 00900)
    # ---------------------------------------------------------------------
    p_item_en = ENTRIES_DIR / "00653_0xe60634348b826f41.bin"
    p_item_twin = ENTRIES_DIR / "00900_0xdb546f14f2f79a11.bin"
    assert p_item_en.exists() and p_item_twin.exists(), "Item tables missing!"

    d_item_en = json.loads(p_item_en.read_text(encoding="utf-8"))
    d_item_twin = json.loads(p_item_twin.read_text(encoding="utf-8"))

    item_fix_count = 0
    for k, item_info in potential_proposals.items():
        new_val = item_info.get("proposed_vi")
        if new_val:
            d_item_en[k] = new_val
            d_item_twin[k] = new_val
            item_fix_count += 1

    p_item_en.write_text(json.dumps(d_item_en, indent=2, ensure_ascii=False), encoding="utf-8")
    p_item_twin.write_text(json.dumps(d_item_twin, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Đã cập nhật thành công {item_fix_count} Thẻ Tiềm Năng vào Item (00653 & 00900).")

    # ---------------------------------------------------------------------
    # 2. CẬP NHẬT UITEXT (00789 & 01036)
    # ---------------------------------------------------------------------
    p_uitext_en = ENTRIES_DIR / "00789_0x87cc29ac0defc2d9.bin"
    p_uitext_twin = ENTRIES_DIR / "01036_0x363690c09b175230.bin"
    assert p_uitext_en.exists() and p_uitext_twin.exists(), "UIText tables missing!"

    d_uitext_en = json.loads(p_uitext_en.read_text(encoding="utf-8"))
    d_uitext_twin = json.loads(p_uitext_twin.read_text(encoding="utf-8"))

    uitext_fix_count = 0
    for k, info in story_proposals.items():
        if k.startswith("UIText."):
            val = info.get("proposed")
            if val:
                d_uitext_en[k] = val
                d_uitext_twin[k] = val
                uitext_fix_count += 1

    p_uitext_en.write_text(json.dumps(d_uitext_en, indent=2, ensure_ascii=False), encoding="utf-8")
    p_uitext_twin.write_text(json.dumps(d_uitext_twin, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Đã cập nhật thành công {uitext_fix_count} chuỗi Cốt truyện vào UIText (00789 & 01036).")

    # ---------------------------------------------------------------------
    # 3. CẬP NHẬT TOPBAR (00769 & 01016)
    # ---------------------------------------------------------------------
    p_topbar_en = ENTRIES_DIR / "00769_0x07e80ecffd123c7a.bin"
    p_topbar_twin = ENTRIES_DIR / "01016_0x80fe12b895323941.bin"
    assert p_topbar_en.exists() and p_topbar_twin.exists(), "TopBar tables missing!"

    d_topbar_en = json.loads(p_topbar_en.read_text(encoding="utf-8"))
    d_topbar_twin = json.loads(p_topbar_twin.read_text(encoding="utf-8"))

    topbar_val = story_proposals.get("TopBar.StorySet.1", {}).get("proposed", "Thời Báo Nova")
    d_topbar_en["TopBar.StorySet.1"] = topbar_val
    d_topbar_twin["TopBar.StorySet.1"] = topbar_val

    p_topbar_en.write_text(json.dumps(d_topbar_en, indent=2, ensure_ascii=False), encoding="utf-8")
    p_topbar_twin.write_text(json.dumps(d_topbar_twin, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Đã cập nhật TopBar.StorySet.1 = '{topbar_val}' vào TopBar (00769 & 01016).")

    # ---------------------------------------------------------------------
    # 4. ĐÓNG GÓI LẠI DIST/DATA_PATCHED_VI.ARCX
    # ---------------------------------------------------------------------
    print("\n-> Đang đóng gói lại dist/data_patched_vi.arcx với mã hóa XXTEA...")
    repack_archive(DEC_DIR, OUTPUT_ARCX, encrypt_payload=True)
    arc = ArcxArchive(OUTPUT_ARCX)
    new_sha = hashlib.sha256(OUTPUT_ARCX.read_bytes()).hexdigest()
    new_size = OUTPUT_ARCX.stat().st_size
    print(f"✓ Hoàn tất đóng gói canonical archive: {new_size:,} bytes")
    print(f"  SHA-256: {new_sha}")

    # ---------------------------------------------------------------------
    # 5. DUAL-DEPLOY TRỰC TIẾP VÀO GAME
    # ---------------------------------------------------------------------
    print("\n-> Đang triển khai trực tiếp từ dist/ vào client game...")
    deploy_targets = [
        ("Yostar Standalone", LIVE_YOSTAR_DATA),
        ("Steam Installation", LIVE_STEAM_DATA)
    ]
    for label, target_path in deploy_targets:
        if target_path.parent.exists():
            shutil.copy2(OUTPUT_ARCX, target_path)
            deployed_sha = hashlib.sha256(target_path.read_bytes()).hexdigest()
            assert deployed_sha == new_sha, f"Deployment verification failed for {label}!"
            print(f"  [DEPLOYED] {label}: {target_path} ({deployed_sha[:12]}...)")
        else:
            print(f"  [SKIP] {label}: Đường dẫn không tồn tại ({target_path.parent})")

    # ---------------------------------------------------------------------
    # 6. CẬP NHẬT BÀI KIỂM THỬ CHỐNG THOÁI LUI VERIFY_DEPLOYED_GAME_DATA.PY
    # ---------------------------------------------------------------------
    print("\n-> Đang cập nhật và chạy kiểm chứng tự động qua verify_deployed_game_data.py...")
    verify_script = ROOT / "tools" / "verify_deployed_game_data.py"
    v_content = verify_script.read_text(encoding="utf-8")

    # Add checks for Activity_Review, Nova_Story, and key potentials if not present
    if "UIText.Activity_Review.1" not in v_content:
        v_content = v_content.replace(
            '"UIText.Plot_Index.1": "Hồi {0}",',
            '"UIText.Plot_Index.1": "Hồi {0}",\n    "UIText.Activity_Review.1": "Hồi Tưởng Sự Kiện",\n    "UIText.Nova_Story.1": "Thời Báo Nova",'
        )
    if "Item.514908.1" not in v_content:
        v_content = v_content.replace(
            '"Item.1030.2": "Dùng để kích hoạt Thiên phú Du Hành Giả."',
            '"Item.1030.2": "Dùng để kích hoạt Thiên phú Du Hành Giả.",\n    "Item.514908.1": "Đòn Đánh Hiểm Độc",\n    "Item.513913.1": "Lướt Quét Thần Tốc",\n    "Item.514906.1": "Tuyệt Không Khoan Nhượng",'
        )

    verify_script.write_text(v_content, encoding="utf-8")

    res = subprocess.run([sys.executable, str(verify_script)], capture_output=True, text=True, encoding="utf-8")
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        sys.exit(1)

    elapsed = time.time() - t0
    print(f"\n[HOÀN THÀNH XUẤT SẮC TRONG {elapsed:.2f} GIÂY] ĐẠI TU TOÀN BỘ TIỀM NĂNG VÀ CỐT TRUYỆN!")

if __name__ == "__main__":
    main()
