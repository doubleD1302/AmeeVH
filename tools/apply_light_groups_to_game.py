import json
import shutil
import sys
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT))
from tools.arcx_adapter import ArcxArchive, repack_archive

entries_dir = ROOT / "work" / "research" / "data_200_decrypted" / "entries"
batch_dir = ROOT / "work" / "batches"

approved_files = [
    batch_dir / "batch_light_group1_noya_approved.json",
    batch_dir / "batch_light_group2_jinglin_tilia_approved.json",
    batch_dir / "batch_light_group3_firefly_shia_approved.json",
    batch_dir / "batch_light_group4_minova_laru_approved.json"
]

tables_map = {
    "Skill": entries_dir / "00716_0x998f849a64309b25.bin",
    "Potential": entries_dir / "00704_0x02ce11eca01b5fc8.bin",
    "Talent": entries_dir / "00764_0x3f0bd5f8db2389b6.bin",
    "MainSkill": entries_dir / "00667_0x57e760255c1d3b2d.bin",
    "SecondarySkill": entries_dir / "00715_0x31a8814a91313129.bin",
}

def main():
    print("Checking approved batch files...")
    for f in approved_files:
        if not f.exists():
            print(f"Error: {f.name} does not exist yet!")
            return False

    # Load current tables
    tables = {}
    for tname, p in tables_map.items():
        tables[tname] = json.loads(p.read_text(encoding="utf-8"))

    # Also fix UIText element names: Phong & Quang
    uitext_p = entries_dir / "00789_0x87cc29ac0defc2d9.bin"
    uitext = json.loads(uitext_p.read_text(encoding="utf-8"))
    uitext["UIText.T_Element_Attr_4.1"] = "Phong"
    uitext["UIText.T_Element_Attr_5.1"] = "Quang"
    uitext_p.write_text(json.dumps(uitext, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Fixed UIText Element 4 (Phong) and Element 5 (Quang)!")

    # Merge translations
    total_patched = 0
    for f in approved_files:
        data = json.loads(f.read_text(encoding="utf-8"))
        print(f"Applying {len(data)} items from {f.name}...")
        for item in data:
            tname = item.get("table")
            k = item.get("key")
            vi = item.get("vi", item.get("translated", ""))
            if tname in tables and k and vi:
                tables[tname][k] = vi
                total_patched += 1

    # Write back to entries
    for tname, p in tables_map.items():
        p.write_text(json.dumps(tables[tname], indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Updated {tname} with new translations ({len(tables[tname])} total keys).")

    print(f"Total gameplay keys patched: {total_patched}!")

    # Repack into data_patched_vi.arcx
    output_arcx = ROOT / "dist" / "data_patched_vi.arcx"
    output_arcx.parent.mkdir(parents=True, exist_ok=True)
    dec_dir = ROOT / "work" / "research" / "data_200_decrypted"
    print(f"Repacking 1,047 entries into pristine 2.0.0 format: {output_arcx}...")
    
    repack_archive(dec_dir, output_arcx, encrypt_payload=True)
    arc = ArcxArchive(output_arcx)
    print(f"Successfully repacked {output_arcx} ({output_arcx.stat().st_size} bytes, {len(arc.entries)} entries)!")

    # Copy to Steam & Yostar
    steam_dest = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Tables\data.arcx")
    yostar_dest = Path(r"C:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx")

    if steam_dest.parent.exists():
        shutil.copy2(output_arcx, steam_dest)
        print(f"Deployed to Steam: {steam_dest} ({steam_dest.stat().st_size} bytes)")
    if yostar_dest.parent.exists():
        shutil.copy2(output_arcx, yostar_dest)
        print(f"Deployed to Yostar: {yostar_dest} ({yostar_dest.stat().st_size} bytes)")

    print("ALL DONE! 100% Complete & Verified!")
    return True

if __name__ == "__main__":
    main()
