import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
p = ROOT / "work" / "batches" / "all_104_discs_survey.json"
recs = json.loads(p.read_text(encoding="utf-8"))

part1 = recs[:30]   # 211001 - 213013 (30 discs)
part2 = recs[30:67]  # 213014 - 214024 (37 discs)
part3 = recs[67:]    # 214026 - 214067 (37 discs)

p1_file = ROOT / "work" / "batches" / "batch_discs_part1.json"
p2_file = ROOT / "work" / "batches" / "batch_discs_part2.json"
p3_file = ROOT / "work" / "batches" / "batch_discs_part3.json"

p1_file.write_text(json.dumps(part1, indent=2, ensure_ascii=False), encoding="utf-8")
p2_file.write_text(json.dumps(part2, indent=2, ensure_ascii=False), encoding="utf-8")
p3_file.write_text(json.dumps(part3, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"Part 1: {len(part1)} discs (IDs {part1[0]['id']} - {part1[-1]['id']}) -> {p1_file.name}")
print(f"Part 2: {len(part2)} discs (IDs {part2[0]['id']} - {part2[-1]['id']}) -> {p2_file.name}")
print(f"Part 3: {len(part3)} discs (IDs {part3[0]['id']} - {part3[-1]['id']}) -> {p3_file.name}")
