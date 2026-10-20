import json
from pathlib import Path

en_dir = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\data_200_pristine_en\entries")
vi_dir = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\data_200_decrypted\entries")

total_en = 0
total_vi = 0
prefix_stats = {}

for en_file in en_dir.glob("*.bin"):
    vi_file = vi_dir / en_file.name
    if not vi_file.exists():
        continue
    raw_en = en_file.read_bytes()
    if not raw_en.startswith(b"{"):
        continue
    raw_vi = vi_file.read_bytes()
    if not raw_vi.startswith(b"{"):
        continue
    try:
        data_en = json.loads(raw_en.decode("utf-8"))
        data_vi = json.loads(raw_vi.decode("utf-8"))
        if not isinstance(data_en, dict) or not isinstance(data_vi, dict):
            continue
        
        for k, v_en in data_en.items():
            total_en += 1
            v_vi = data_vi.get(k)
            prefix = k.split(".")[0] if "." in k else "Other"
            if prefix not in prefix_stats:
                prefix_stats[prefix] = {"total": 0, "diff": 0, "file": en_file.name}
            prefix_stats[prefix]["total"] += 1
            if v_vi is not None and v_vi != v_en:
                total_vi += 1
                prefix_stats[prefix]["diff"] += 1
    except Exception:
        pass

print(f"Total entries in DB: {total_en:,}")
print(f"Total translated entries: {total_vi:,}")
print("\nTop 40 translated categories:")
for p, s in sorted(prefix_stats.items(), key=lambda x: x[1]["diff"], reverse=True)[:40]:
    if s["diff"] > 0:
        ratio = s["diff"] / s["total"] * 100
        print(f"  {p:<26} ({s['file']}): {s['diff']:>5} / {s['total']:>5} ({ratio:>5.1f}%)")
