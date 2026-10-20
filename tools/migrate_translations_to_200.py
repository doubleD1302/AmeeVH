import json
import re
import sys
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT))
from tools.arcx_adapter import ArcxArchive, repack_archive

VI_REGEX = re.compile(
    r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ"
    r"ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]"
)

def main():
    print("=" * 70)
    print("MIGRATING ALL VIETNAMESE TRANSLATIONS TO 2.0.0 ARCHIVE")
    print("=" * 70)

    old_dir = ROOT / "work" / "research" / "data_decrypted"
    new_dir = ROOT / "work" / "research" / "data_200_decrypted"
    output_arcx = ROOT / "work" / "research" / "data_patched_vi.arcx"

    old_m = json.loads((old_dir / "manifest.json").read_text(encoding="utf-8"))
    new_m = json.loads((new_dir / "manifest.json").read_text(encoding="utf-8"))

    old_by_hash = {e["hash_hex"]: e["filename"] for e in old_m["entries"]}
    new_by_hash = {e["hash_hex"]: e["filename"] for e in new_m["entries"]}

    print(f"Old archive total entries: {len(old_m['entries'])}")
    print(f"2.0.0 archive total entries: {len(new_m['entries'])}")

    tables_migrated = 0
    strings_migrated = 0
    preserved_200_keys = 0

    for h_hex, old_fn in old_by_hash.items():
        if h_hex not in new_by_hash:
            continue

        old_fp = old_dir / "entries" / old_fn
        try:
            old_data = json.loads(old_fp.read_text(encoding="utf-8"))
        except Exception:
            continue

        if not isinstance(old_data, dict):
            continue

        # Extract genuine Vietnamese translations
        vi_entries = {k: v for k, v in old_data.items() if isinstance(v, str) and VI_REGEX.search(v)}
        if not vi_entries:
            continue

        new_fn = new_by_hash[h_hex]
        new_fp = new_dir / "entries" / new_fn

        try:
            new_data = json.loads(new_fp.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Warning: 2.0.0 table {new_fn} (hash {h_hex}) is not JSON: {e}")
            continue

        if not isinstance(new_data, dict):
            continue

        applied_this_table = 0
        for k, v in vi_entries.items():
            if k in new_data:
                new_data[k] = v
                applied_this_table += 1
            else:
                # Key from older version might not exist in 2.0.0, or new schema
                new_data[k] = v
                applied_this_table += 1

        new_fp.write_text(json.dumps(new_data, indent=2, ensure_ascii=False), encoding="utf-8")
        tables_migrated += 1
        strings_migrated += applied_this_table

    print(f"\nMigration Results:")
    print(f"  Tables migrated:        {tables_migrated}")
    print(f"  Total strings merged:   {strings_migrated}")

    # Repack to data_patched_vi.arcx
    print(f"\nRepacking to {output_arcx}...")
    repack_archive(new_dir, output_arcx, encrypt_payload=True)

    print(f"Verifying repacked archive...")
    arc = ArcxArchive(output_arcx)
    print(f"  Successfully repacked!")
    print(f"  Entry count: {len(arc.entries)} (Expected: {len(new_m['entries'])})")
    print(f"  Output size: {output_arcx.stat().st_size} bytes")

    assert len(arc.entries) == len(new_m["entries"]), "Entry count mismatch!"
    print("\n✓ 2.0.0 ARCX PACKAGING VERIFICATION PASSED!")

if __name__ == "__main__":
    main()
