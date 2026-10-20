import json

p = "StellaSora_VietHoa/work/batches/final_wave_group1_gameplay_minigames.json"
data = json.load(open(p, encoding="utf-8"))

with open("StellaSora_VietHoa/work/batches/group1_details.txt", "w", encoding="utf-8") as out:
    for i, it in enumerate(data):
        out.write(f"[{i}] {it['table']} | {it['key']}\n")
        out.write(f"  EN: {it.get('en', '')}\n")
        out.write(f"  ZH: {it.get('zh', '')}\n\n")

print(f"Dumped {len(data)} items to group1_details.txt")
