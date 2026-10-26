#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Targeted Fix for Story Act Naming and Archive Header Overflow (Campaign 23)
--------------------------------------------------------------------------
1. Story Act Naming:
   - Replaces absurd literal MT 'Đạo luật {0}' (Act {0}) with theatrical/literary 'Hồi {0}'.
   - Replaces raw English 'Story: Act {0}' with 'Cốt Truyện: Hồi {0}'.
   - Standardizes skin plot indexing to '{0}: Hồi {1}'.
   - Synchronizes across UIText (00789) and twin (01036).

2. Archive Base Info Header Overflow:
   - Replaces wrapped 'Thông Tin Cơ Bản' with sleek 'Thông Tin'.
   - Fixes all 39 CharacterArchiveContent (00593) headers and twin (00840).
   - Fixes UIText base info keys (CharPlot_BaseInfo, CharacterInfo_Simpe_Info, CharacterRelation_Base_Info).

3. Repack dist/data_patched_vi.arcx with XXTEA encryption.
4. Dual-deploy to Yostar and Steam live clients.
5. Anti-regression verification with tools/verify_deployed_game_data.py.
"""

from __future__ import annotations
import hashlib
import json
import re
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

LIVE_YOSTAR_DATA = Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx")
LIVE_STEAM_DATA = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Tables\data.arcx")

UITEXT_OVERRIDES = {
    "UIText.Plot_Index.1": "Hồi {0}",
    "UIText.TowerDef_Story_Index.1": "Hồi {0}",
    "UIText.Skin_Plot_Index.1": "{0}: Hồi {1}",
    "UIText.Affinity_UnLock_PrePlot.1": "Hoàn thành Cốt Truyện: Hồi {0} để mở khóa",
    "UIText.Affinity_UnLock_PrePlot_Skin.1": "Hoàn thành {0}: Hồi {1} để mở khóa",
    "UIText.CharPlot_BaseInfo.1": "Thông Tin",
    "UIText.CharacterInfo_Simpe_Info.1": "Thông Tin",
    "UIText.CharacterRelation_Base_Info.1": "Thông Tin",
}

def main():
    t0 = time.time()
    print("=" * 80)
    print("BẮT ĐẦU SỬA LỖI ĐẠO LUẬT -> HỒI VÀ TRÀN CHỮ THÔNG TIN CƠ BẢN (CAMPAIGN 23)")
    print("=" * 80)

    # ---------------------------------------------------------------------
    # 1. UITEXT (00789 & 01036)
    # ---------------------------------------------------------------------
    p_789 = ENTRIES_DIR / "00789_0x87cc29ac0defc2d9.bin"
    p_1036 = ENTRIES_DIR / "01036_0x363690c09b175230.bin"
    assert p_789.exists() and p_1036.exists(), "UIText tables missing!"

    d_789 = json.loads(p_789.read_text(encoding="utf-8"))
    d_1036 = json.loads(p_1036.read_text(encoding="utf-8"))

    for k, v in UITEXT_OVERRIDES.items():
        d_789[k] = v
        d_1036[k] = v

    p_789.write_text(json.dumps(d_789, indent=2, ensure_ascii=False), encoding="utf-8")
    p_1036.write_text(json.dumps(d_1036, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Đã cập nhật UIText (00789 & 01036): Sửa 'Đạo luật' -> 'Hồi' và chuẩn hóa 'Thông Tin'.")

    # ---------------------------------------------------------------------
    # 2. CHARACTER ARCHIVE CONTENT (00593 & 00840)
    # ---------------------------------------------------------------------
    p_593 = ENTRIES_DIR / "00593_0x843b3b0812018dd2.bin"
    p_840 = ENTRIES_DIR / "00840_0x4a3c44844ee817d1.bin"
    assert p_593.exists() and p_840.exists(), "CharacterArchiveContent tables missing!"

    d_593 = json.loads(p_593.read_text(encoding="utf-8"))
    d_840 = json.loads(p_840.read_text(encoding="utf-8"))

    header_count = 0
    for k in list(d_593.keys()):
        if k.endswith("01.1") and d_593[k] == "Thông Tin Cơ Bản":
            d_593[k] = "Thông Tin"
            d_840[k] = "Thông Tin"
            header_count += 1

    p_593.write_text(json.dumps(d_593, indent=2, ensure_ascii=False), encoding="utf-8")
    p_840.write_text(json.dumps(d_840, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Đã cập nhật CharacterArchiveContent (00593 & 00840): {header_count} tiêu đề thẻ hồ sơ được rút gọn thành 'Thông Tin' (triệt tiêu tràn chữ).")

    # ---------------------------------------------------------------------
    # 3. REPACK DIST/DATA_PATCHED_VI.ARCX
    # ---------------------------------------------------------------------
    print("\n-> Đang đóng gói lại dist/data_patched_vi.arcx với mã hóa XXTEA...")
    repack_archive(DEC_DIR, OUTPUT_ARCX, encrypt_payload=True)
    arc = ArcxArchive(OUTPUT_ARCX)
    new_sha = hashlib.sha256(OUTPUT_ARCX.read_bytes()).hexdigest()
    new_size = OUTPUT_ARCX.stat().st_size
    print(f"✓ Hoàn tất đóng gói canonical archive: {new_size:,} bytes")
    print(f"  SHA-256: {new_sha}")

    # ---------------------------------------------------------------------
    # 4. DUAL-DEPLOY TO YOSTAR AND STEAM INSTALLATIONS
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
    # 5. ANTI-REGRESSION VERIFICATION
    # ---------------------------------------------------------------------
    print("\n-> Đang cập nhật và chạy kiểm chứng tự động qua verify_deployed_game_data.py...")
    verify_script = ROOT / "tools" / "verify_deployed_game_data.py"
    v_content = verify_script.read_text(encoding="utf-8")

    # Update golden hash
    v_content = re.sub(
        r'EXPECTED_DATA_SHA256 = "[a-f0-9]{64}"',
        f'EXPECTED_DATA_SHA256 = "{new_sha}"',
        v_content
    )

    # Add Plot_Index check to verify script if not present
    if "UIText.Plot_Index.1" not in v_content:
        v_content = v_content.replace(
            '"UIText.Recruit_history_empty.1": "Chưa có lịch sử chiêu mộ",',
            '"UIText.Recruit_history_empty.1": "Chưa có lịch sử chiêu mộ",\n    "UIText.Plot_Index.1": "Hồi {0}",'
        )

    verify_script.write_text(v_content, encoding="utf-8")

    import subprocess
    res = subprocess.run([sys.executable, str(verify_script)], capture_output=True, text=True, encoding="utf-8")
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        sys.exit(1)

    elapsed = time.time() - t0
    print(f"\n[HOÀN THÀNH XUẤT SẮC TRONG {elapsed:.2f} GIÂY] ĐÃ SỬA TRIỆT ĐỂ LỖI 'ĐẠO LUẬT' VÀ TRÀN CHỮ!")

if __name__ == "__main__":
    main()
