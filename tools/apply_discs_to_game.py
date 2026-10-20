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
    batch_dir / "batch_discs_part1_approved.json",
    batch_dir / "batch_discs_part2_approved.json",
    batch_dir / "batch_discs_part3_approved.json"
]

def main():
    print("Checking approved disc files...")
    for f in approved_files:
        if not f.exists():
            print(f"Error: {f.name} does not exist!")
            return False

    # Load DiscIP.json and Item.json
    discip_path = entries_dir / "00620_0x1f924138769d46ec.bin"
    item_path = entries_dir / "00653_0xe60634348b826f41.bin"

    disc_data = json.loads(discip_path.read_text(encoding="utf-8"))
    item_data = json.loads(item_path.read_text(encoding="utf-8"))

    total_discs = 0
    for f in approved_files:
        items = json.loads(f.read_text(encoding="utf-8"))
        print(f"Applying {len(items)} discs from {f.name}...")
        for it in items:
            did = it["id"]
            name = it["approved_name"].strip()
            desc = it.get("approved_desc", "").strip()

            # Update DiscIP.json
            disc_k = f"DiscIP.{did}.3"
            disc_data[disc_k] = name

            # Update Item.json (name)
            item_k1 = f"Item.{did}.1"
            item_data[item_k1] = name

            # Update Item.json (desc if provided)
            if desc:
                item_k3 = f"Item.{did}.3"
                item_data[item_k3] = desc

            total_discs += 1

    # Write back
    discip_path.write_text(json.dumps(disc_data, indent=2, ensure_ascii=False), encoding="utf-8")
    item_path.write_text(json.dumps(item_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Successfully updated {total_discs} discs in DiscIP and Item tables!")

    # Repack
    output_arcx = ROOT / "dist" / "data_patched_vi.arcx"
    dec_dir = ROOT / "work" / "research" / "data_200_decrypted"
    print(f"Repacking archive into {output_arcx}...")
    repack_archive(dec_dir, output_arcx, encrypt_payload=True)
    arc = ArcxArchive(output_arcx)
    print(f"Repacked successfully! Size: {output_arcx.stat().st_size} bytes, {len(arc.entries)} entries.")

    # Deploy to Steam, Yostar and research
    dests = [
        ROOT / "work" / "research" / "data_patched_vi.arcx",
        Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Tables\data.arcx"),
        Path(r"C:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx")
    ]
    for d in dests:
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(output_arcx, d)
        print(f"Deployed {output_arcx.stat().st_size} bytes to {d}")

    print("ALL DONE! 100% Complete & Synchronized!")
    return True

if __name__ == "__main__":
    main()
