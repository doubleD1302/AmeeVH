#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Potential Preset Name Server Validation:
Switch preset name (.1) to ASCII-safe "Preset 1" / "Preset 2" to bypass server regex filter
that rejects non-ASCII / Vietnamese diacritics with ErrorCode 110202/110203 ("Tên chứa từ ngữ không hợp lệ").
"""

import json
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))

from arcx_adapter import repack_archive, ArcxArchive, xxtea_decrypt, XXTEA_KEY
from overhaul_potential_talent_affinity_manga import PRESET_CHAR_NAMES

ENTRIES_DIR = ROOT / "work" / "research" / "data_200_decrypted" / "entries"
P_705 = ENTRIES_DIR / "00705_0x01c03095eb011849.bin"
P_952 = ENTRIES_DIR / "00952_0xeb62a80c4e7d0c15.bin"
P_789 = ENTRIES_DIR / "00789_0x87cc29ac0defc2d9.bin"
P_1036 = ENTRIES_DIR / "01036_0x363690c09b175230.bin"
OVERHAUL_SCRIPT = ROOT / "tools" / "overhaul_potential_talent_affinity_manga.py"
OUTPUT_DATA_ARCX = ROOT / "dist" / "data_patched_vi.arcx"

LIVE_YOSTAR_DATA = Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx")
LIVE_STEAM_DATA = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Tables\data.arcx")

def patch_overhaul_script():
    print("=== 1. UPDATING OVERHAUL SCRIPT CLEAN_PRESET_ENTRY ===")
    content = OVERHAUL_SCRIPT.read_text(encoding="utf-8")
    old_target = '        if field == "1":\n            return f"Gợi ý {preset_num}"'
    new_target = '        if field == "1":\n            return f"Preset {preset_num}"'
    if old_target in content:
        content = content.replace(old_target, new_target)
        OVERHAUL_SCRIPT.write_text(content, encoding="utf-8")
        print("✓ Patched overhaul script clean_preset_entry -> 'Preset {preset_num}'")
    else:
        print("Note: overhaul script already has target or different block.")

def patch_preset_bins():
    print("\n=== 2. UPDATING POTENTIAL PRESET BINS (00705 & 00952) ===")
    d_705 = json.loads(P_705.read_text(encoding="utf-8"))
    updated = 0
    for k in sorted(d_705.keys()):
        parts = k.split(".")
        if len(parts) >= 2:
            entry_id = parts[1]
            field = parts[2] if len(parts) >= 3 else "1"
            cid = entry_id[:3]
            preset_num = entry_id[-1]
            char_name = PRESET_CHAR_NAMES.get(cid, "Du Hành Giả")
            
            if field == "1":
                d_705[k] = f"Preset {preset_num}"
                updated += 1
            elif field == "2":
                d_705[k] = f"Gợi ý {preset_num} của {char_name}"
                updated += 1
                
    P_705.write_text(json.dumps(d_705, indent=2, ensure_ascii=False), encoding="utf-8")
    P_952.write_text(json.dumps(d_705, indent=2, ensure_ascii=False), encoding="utf-8")
    
    val1 = d_705["PotentialPreset.10301.1"]
    val2 = d_705["PotentialPreset.10301.2"]
    print(f"✓ Updated {updated} preset entries:")
    print(f"  Field 1: '{val1}' ({len(val1)} chars, pure ASCII: {val1.isascii()})")
    print(f"  Field 2: '{val2}'")
    assert val1 == "Preset 1" and val1.isascii()

def patch_uitext_init_name():
    print("\n=== 3. UPDATING UITEXT INIT PRESET NAME (00789 & 01036) ===")
    d_789 = json.loads(P_789.read_text(encoding="utf-8"))
    d_789["UIText.Potential_Preselection_Name_Init.1"] = "Preset"
    P_789.write_text(json.dumps(d_789, indent=2, ensure_ascii=False), encoding="utf-8")
    
    d_1036 = json.loads(P_1036.read_text(encoding="utf-8"))
    d_1036["UIText.Potential_Preselection_Name_Init.1"] = "Preset"
    P_1036.write_text(json.dumps(d_1036, indent=2, ensure_ascii=False), encoding="utf-8")
    print("✓ Updated UIText.Potential_Preselection_Name_Init.1 -> 'Preset' (pure ASCII)")

def repack_and_deploy():
    print("\n=== 4. REPACKING dist/data_patched_vi.arcx ===")
    dec_dir = ROOT / "work" / "research" / "data_200_decrypted"
    t0 = time.time()
    repack_archive(dec_dir, OUTPUT_DATA_ARCX, encrypt_payload=True)
    elapsed = time.time() - t0
    print(f"✓ Repacked {OUTPUT_DATA_ARCX} in {elapsed:.2f}s ({OUTPUT_DATA_ARCX.stat().st_size:,} bytes)")
    
    print("\n=== 5. DUAL-DEPLOYING TO LIVE CLIENTS ===")
    for target in [LIVE_YOSTAR_DATA, LIVE_STEAM_DATA]:
        if target.parent.exists():
            shutil.copy2(OUTPUT_DATA_ARCX, target)
            print(f"✓ Synced {OUTPUT_DATA_ARCX.stat().st_size:,} bytes to: {target}")

    print("\n=== 6. VERIFYING ANTI-REGRESSION GATE ===")
    import verify_deployed_game_data
    verify_deployed_game_data.main()

def verify_live():
    print("\n=== 7. DIRECT SPOT-CHECK ON LIVE ARCHIVE ===")
    arc = ArcxArchive(LIVE_YOSTAR_DATA)
    raw = LIVE_YOSTAR_DATA.read_bytes()
    for e in arc.entries:
        if e["hash"] == 0x01c03095eb011849: # PotentialPreset
            d = json.loads(xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY).decode("utf-8"))
            val1 = d.get("PotentialPreset.10301.1")
            print(f"  [LIVE 00705] PotentialPreset.10301.1 = '{val1}' (ASCII={val1.isascii()})")
            assert val1 == "Preset 1"
        elif e["hash"] == 0x87cc29ac0defc2d9: # UIText
            d = json.loads(xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY).decode("utf-8"))
            val_init = d.get("UIText.Potential_Preselection_Name_Init.1")
            print(f"  [LIVE 00789] UIText.Potential_Preselection_Name_Init.1 = '{val_init}'")
            assert val_init == "Preset"
    print("✓ LIVE SPOT-CHECK PASSED!")

if __name__ == "__main__":
    patch_overhaul_script()
    patch_preset_bins()
    patch_uitext_init_name()
    repack_and_deploy()
    verify_live()
    print("\n>>> ALL STEPS FINISHED PERFECTLY! <<<")
