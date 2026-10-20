import json
from pathlib import Path

p = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\all_104_discs_survey.json")
recs = json.loads(p.read_text(encoding="utf-8"))

out_lines = []
out_lines.append(f"{'ID':8} | {'ZH Name':18} | {'EN Name':28} | {'DiscIP Name':28} | {'Item Name'}")
out_lines.append("-" * 115)
for r in recs:
    out_lines.append(f"{r['id']:8} | {r['zh_name']:18} | {r['en_name']:28} | {r['cur_discip_name']:28} | {r['cur_item_name']}")

dump_path = p.parent / "all_104_discs_dump.txt"
dump_path.write_text("\n".join(out_lines), encoding="utf-8")
print(f"Dumped {len(recs)} discs to {dump_path.name}")
