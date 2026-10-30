import os
import json
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path("StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))
from extract_clean_10k_avg import extract_clean_lua53_strings

master_trans = {}
for bf in [
    "work/batches/pillars_translation_cache.json",
    "work/batches/remaining_lua_avg_cache.json",
    "work/batches/dialogue_remaining_avg_approved.json",
    "work/batches/batch_10000_avg_clean.json",
    "work/batches/batch_10k_approved.json",
    "work/batches/batch_10k_b2_approved.json",
    "work/batches/batch_10k_b3_approved.json",
    "work/batches/batch_10k_b4_approved.json",
]:
    p = ROOT / bf
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        master_trans.update(data)

print("Master trans total keys:", len(master_trans))

lua_dir = ROOT / "work" / "research" / "lua_tree" / "Game" / "UI" / "Avg" / "_en" / "Config"
ch_stats = defaultdict(lambda: {"files": 0, "lines": 0, "translated": 0})

for f in sorted(os.listdir(lua_dir)):
    if not f.endswith(".lua"):
        continue
    if f.startswith("STm"):
        ch = f[:5]
    elif f.startswith("STsp"):
        ch = "STsp"
    elif f.startswith("STev"):
        ch = "STev"
    elif f.startswith("BBm"):
        ch = "BBm"
    elif f.startswith("PM"):
        ch = "PM"
    elif f.startswith("CG"):
        ch = "CG"
    elif f.startswith("DP"):
        ch = "DP"
    else:
        ch = f.split("_")[0]

    ch_stats[ch]["files"] += 1
    raw = extract_clean_lua53_strings(lua_dir / f)
    scene_id = f[:-4]
    for idx, en_str in enumerate(raw):
        line_id = f"{scene_id}.{idx+1}"
        ch_stats[ch]["lines"] += 1
        if line_id in master_trans or en_str in master_trans:
            ch_stats[ch]["translated"] += 1

total_files = sum(s["files"] for s in ch_stats.values())
total_lines = sum(s["lines"] for s in ch_stats.values())
total_trans = sum(s["translated"] for s in ch_stats.values())

for ch in sorted(ch_stats.keys()):
    s = ch_stats[ch]
    cov = (s["translated"] / s["lines"] * 100) if s["lines"] > 0 else 0
    print(f"{ch:8s}: {s['files']:3d} files | {s['lines']:5d} lines | {s['translated']:5d} translated ({cov:.1f}%)")

print("-" * 50)
print(f"TOTAL: {total_files} files | {total_lines} lines | {total_trans} translated ({total_trans/total_lines*100:.1f}%)")
