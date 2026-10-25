import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
entries = ROOT / "work" / "research" / "data_200_decrypted" / "entries"

tables = ["DiscIP", "Item", "MainSkill", "SecondarySkill", "Skill", "Potential", "Talent"]

for t in tables:
    matches = []
    for f in entries.glob("*.bin"):
        try:
            raw = f.read_bytes()
            if raw.startswith(b"{"):
                d = json.loads(raw.decode("utf-8"))
                first_k = next(iter(d.keys()), "")
                if first_k.startswith(f"{t}."):
                    sample_v = d[first_k]
                    # check if sample_v is vietnamese/english or chinese
                    is_cjk = any('\u4e00' <= char <= '\u9fff' for char in str(sample_v))
                    matches.append((f.name, len(d), "ZH" if is_cjk else "VI/EN", first_k, repr(sample_v)[:40]))
        except:
            pass
    print(f"=== Table: {t} ===")
    for m in matches:
        print(f"  {m[0]}: {m[1]} keys, Lang={m[2]}, {m[3]} = {m[4]}")
