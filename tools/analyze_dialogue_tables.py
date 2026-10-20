import json
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
EN_DIR = ROOT / "work" / "research" / "data_200_pristine_en" / "entries"
VI_DIR = ROOT / "work" / "research" / "data_200_decrypted" / "entries"
CN_DIR = ROOT / "work" / "research" / "data_decrypted" / "entries"

DIALOGUE_TABLES = [
    ("CharacterArchiveVoice", "00594_0xd8b61831cfe58bf2.bin"),
    ("CharacterArchiveContent", "00593_0x843b3b0812018dd2.bin"),
    ("DatingCharacterEvent", "00611_0xd46d025e8dae5d69.bin"),
    ("DatingLandmarkEvent", "00613_0xdc09272e31aceb9b.bin"),
    ("StarTowerTalk", "00746_0x334464ea98858db1.bin"),
    ("Story", "00752_0xdda397c15ce0b289.bin"),
    ("ActivityStory", "00570_0x0c2ee3471b91208e.bin"),
    ("Plot", "00703_0x8dc130b6f79ff422.bin"),
    ("AffinityQuest", "00576_0xde9e039952f8c2d2.bin")
]

# Check existing files in ENTRIES_DIR for exact names
results = []
for tname, fname in DIALOGUE_TABLES:
    vi_p = VI_DIR / fname
    en_p = EN_DIR / fname
    if not vi_p.exists():
        # search for bin with prefix
        for cand in VI_DIR.glob("*.bin"):
            try:
                raw = cand.read_bytes()
                if raw.startswith(b"{"):
                    d = json.loads(raw.decode("utf-8"))
                    if any(k.startswith(f"{tname}.") for k in d.keys()):
                        vi_p = cand
                        en_p = EN_DIR / cand.name
                        break
            except Exception:
                pass
    if not vi_p.exists():
        continue
        
    try:
        vi_data = json.loads(vi_p.read_text(encoding="utf-8"))
        en_data = json.loads(en_p.read_text(encoding="utf-8")) if en_p.exists() else {}
        
        untrans = 0
        total = 0
        samples_untrans = []
        samples_clunky = []
        
        for k, v in vi_data.items():
            if not isinstance(v, str) or not v.strip():
                continue
            if v.isdigit():
                continue
            total += 1
            v_en = en_data.get(k, "")
            
            # Check untranslated
            is_untrans = False
            if v == v_en and len(v) > 3 and not v.startswith("res/"):
                is_untrans = True
                untrans += 1
                if len(samples_untrans) < 3:
                    samples_untrans.append((k, v))
                    
            # Check clunky
            if not is_untrans:
                if any(w in v for w in ["của bạn", "hoa hồng", "Thành Phố Thành Phố", "bánh mì nướng", "không thể không"]):
                    if len(samples_clunky) < 3:
                        samples_clunky.append((k, v))
                        
        results.append({
            "table": tname,
            "file": vi_p.name,
            "total_text": total,
            "untranslated": untrans,
            "samples_untrans": samples_untrans,
            "samples_clunky": samples_clunky
        })
    except Exception as e:
        results.append({"table": tname, "error": str(e)})

print("=== DIALOGUE TABLES ANALYSIS ===")
for r in results:
    if "error" in r:
        print(f"[{r['table']}] Error: {r['error']}")
    else:
        print(f"[{r['table']}] ({r['file']}): Total={r['total_text']}, Untranslated={r['untranslated']}")
        for k, s in r['samples_untrans']:
            print(f"  [UNTRANS] {k}: {repr(s[:70])}")
        for k, s in r['samples_clunky']:
            print(f"  [CLUNKY]  {k}: {repr(s[:70])}")
