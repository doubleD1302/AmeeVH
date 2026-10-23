import json
from pathlib import Path
import shutil
import sys

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT))
from tools.arcx_adapter import repack_archive, ArcxArchive

DEC_DIR = ROOT / "work" / "research" / "data_200_decrypted" / "entries"
PRIS_DIR = ROOT / "work" / "research" / "data_200_pristine_en" / "entries"
GLOSSARY_PATH = ROOT / "config" / "master_glossary.json"

def update_glossary():
    if GLOSSARY_PATH.exists():
        d = json.loads(GLOSSARY_PATH.read_text(encoding="utf-8"))
        terms = d.get("terms", {})
        terms["Firstlight Noya"] = "Firstlight Noya"
        terms["First Light Noya"] = "Firstlight Noya"
        terms["Noya Firstlight"] = "Firstlight Noya"
        terms["Noya - Khải Minh"] = "Firstlight Noya"
        terms["Khải Minh Noya"] = "Firstlight Noya"
        terms["Firstlight"] = "Firstlight"
        terms["First Light"] = "Firstlight"
        d["terms"] = terms
        GLOSSARY_PATH.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
        print("Updated master_glossary.json!")

def revert_noya_firstlight():
    print("Reverting character name 'Noya - Khải Minh' -> 'Firstlight Noya'...")
    modified_files = 0
    modified_keys = 0

    replacements = [
        ("Noya - Khải Minh", "Firstlight Noya"),
        ("Noya Khải Minh", "Firstlight Noya"),
        ("Khải Minh Noya", "Firstlight Noya"),
    ]

    for p in sorted(DEC_DIR.glob("00[5-7]*.bin")):
        try:
            raw = p.read_text(encoding="utf-8")
            changed = False
            for old_s, new_s in replacements:
                if old_s in raw:
                    raw = raw.replace(old_s, new_s)
                    changed = True

            if changed:
                p.write_text(raw, encoding="utf-8")
                modified_files += 1
                # count occurrences
                for old_s, new_s in replacements:
                    pass
        except Exception as e:
            print(f"Error on {p.name}: {e}")

    print(f"Modified {modified_files} table files in data_200_decrypted.")

def repack_and_deploy():
    data_dec_dir = ROOT / "work" / "research" / "data_200_decrypted"
    out_arcx = ROOT / "dist" / "data_patched_vi.arcx"
    
    print(f"Repacking {out_arcx.name}...")
    repack_archive(data_dec_dir, out_arcx)
    print(f"Repacked successfully! Size: {out_arcx.stat().st_size} bytes")

    # Deploy to game dirs
    yostar_data = Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx")
    steam_data = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Tables\data.arcx")

    if yostar_data.parent.exists():
        shutil.copy2(out_arcx, yostar_data)
        print("Deployed to Yostar PC client:", yostar_data)

    if steam_data.parent.exists():
        shutil.copy2(out_arcx, steam_data)
        print("Deployed to Steam PC client:", steam_data)

if __name__ == "__main__":
    update_glossary()
    revert_noya_firstlight()
    repack_and_deploy()
