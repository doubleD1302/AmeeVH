#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remediation Script: Fix Potential Preset Name Length & Restore Accurate ErrorCode Table.
Resolves:
1. "Illegal name length" (ErrorCode 110201) caused by "Thiết lập đề xuất hệ thống 1" (28 chars > 16 chars).
   Shortens all PotentialPreset.*.1 to concise, standard names: "Đề xuất 1" and "Đề xuất 2" (8 chars, 12 bytes).
2. Misaligned ErrorCode table where 110201 was mistranslated as "Không tìm thấy người chơi" (Player not found)
   instead of "Độ dài tên không hợp lệ" (Illegal name length).
Repacks dist/data_patched_vi.arcx, dual-deploys to live games, and verifies anti-regression.
"""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))

from arcx_adapter import repack_archive, ArcxArchive, xxtea_decrypt, XXTEA_KEY
from build_accurate_error_codes import ERROR_CODES_VI

ENTRIES_DIR = ROOT / "work" / "research" / "data_200_decrypted" / "entries"
PRESET_BIN = ENTRIES_DIR / "00705_0x01c03095eb011849.bin"
ERROR_BIN = ENTRIES_DIR / "00630_0x79d5a3cef377df0c.bin"
OUTPUT_DATA_ARCX = ROOT / "dist" / "data_patched_vi.arcx"

LIVE_YOSTAR_DATA = Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx")
LIVE_STEAM_DATA = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Tables\data.arcx")

def apply_fixes():
    print("=== 1. PATCHING POTENTIAL PRESET NAMES ===")
    preset_data = json.loads(PRESET_BIN.read_text(encoding="utf-8"))
    p_en = json.loads((ROOT / "work/research/data_200_pristine_en/entries/00705_0x01c03095eb011849.bin").read_text(encoding="utf-8"))
    
    updated_presets = 0
    for k in sorted(preset_data.keys()):
        if k.endswith(".1"):
            sub = k.split(".")[1]
            if sub.endswith("01"):
                preset_data[k] = "Đề xuất 1"
            elif sub.endswith("02"):
                preset_data[k] = "Đề xuất 2"
            updated_presets += 1
        elif k.endswith(".2"):
            # e.g. "Firstlight Noya Default Preset 1" -> "Firstlight Noya - Đề xuất 1"
            en_val = p_en.get(k, "")
            char_name = en_val.replace(" Default Preset 1", "").replace(" Default Preset 2", "").strip()
            sub = k.split(".")[1]
            num = "1" if sub.endswith("01") else "2"
            preset_data[k] = f"{char_name} - Đề xuất {num}"
            updated_presets += 1

    PRESET_BIN.write_text(json.dumps(preset_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Patched {updated_presets} entries in {PRESET_BIN.name}:")
    print(f"  Sample PotentialPreset.16201.1: {preset_data['PotentialPreset.16201.1']} ({len(preset_data['PotentialPreset.16201.1'])} chars, {len(preset_data['PotentialPreset.16201.1'].encode('utf-8'))} bytes)")
    print(f"  Sample PotentialPreset.16201.2: {preset_data['PotentialPreset.16201.2']}")

    print("\n=== 2. RESTORING ACCURATE ERRORCODE TABLE ===")
    error_data = json.loads(ERROR_BIN.read_text(encoding="utf-8"))
    print(f"Old ErrorCode table had {len(error_data)} entries.")
    print(f"Old ErrorCode.110201.1: {error_data.get('ErrorCode.110201.1')}")

    # Replace with accurately aligned 189 error codes
    ERROR_BIN.write_text(json.dumps(ERROR_CODES_VI, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(ERROR_CODES_VI)} accurate error codes to {ERROR_BIN.name}:")
    print(f"  New ErrorCode.110201.1: {ERROR_CODES_VI['ErrorCode.110201.1']}")

    print("\n=== 3. REPACKING data_patched_vi.arcx ===")
    dec_dir = ROOT / "work" / "research" / "data_200_decrypted"
    t0 = time.time()
    repack_archive(dec_dir, OUTPUT_DATA_ARCX, encrypt_payload=True)
    elapsed = time.time() - t0
    print(f"SUCCESS! Repacked {OUTPUT_DATA_ARCX} in {elapsed:.2f}s ({OUTPUT_DATA_ARCX.stat().st_size:,} bytes)")

    print("\n=== 4. DUAL-DEPLOYING TO LIVE CLIENTS ===")
    for target in [LIVE_YOSTAR_DATA, LIVE_STEAM_DATA]:
        if target.parent.exists():
            shutil.copy2(OUTPUT_DATA_ARCX, target)
            print(f"Synced {OUTPUT_DATA_ARCX.stat().st_size:,} bytes to: {target}")

    print("\n=== 5. RUNNING ANTI-REGRESSION VERIFICATION GATE ===")
    import verify_deployed_game_data
    verify_deployed_game_data.main()

    print("\n=== 6. SPOT CHECKING LIVE DEPLOYED DATA ===")
    arc = ArcxArchive(LIVE_YOSTAR_DATA)
    raw = LIVE_YOSTAR_DATA.read_bytes()
    
    found_preset = False
    found_error = False
    for e in arc.entries:
        if e["hash"] == 0x01c03095eb011849: # PotentialPreset
            d = json.loads(xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY).decode("utf-8"))
            val = d.get("PotentialPreset.16201.1")
            print(f"  [VERIFIED] Live PotentialPreset.16201.1 = '{val}' (Expected: 'Đề xuất 1')")
            assert val == "Đề xuất 1"
            found_preset = True
        elif e["hash"] == 0x79d5a3cef377df0c: # ErrorCode
            d = json.loads(xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY).decode("utf-8"))
            val = d.get("ErrorCode.110201.1")
            print(f"  [VERIFIED] Live ErrorCode.110201.1 = '{val}' (Expected: 'Độ dài tên không hợp lệ')")
            assert val == "Độ dài tên không hợp lệ"
            found_error = True

    assert found_preset and found_error, "Failed to verify live table entries!"
    print("\n[SUCCESS] ALL FIXES APPLIED, DEPLOYED, AND 100% VERIFIED!")

if __name__ == "__main__":
    apply_fixes()
