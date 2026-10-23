import json

# Fix STm01_07.32 in translator_main_1
p1_path = "StellaSora_VietHoa/work/subagents/lightnovel_editorial_20261024_r02/translator_main_1/PROPOSALS.json"
with open(p1_path, "r", encoding="utf-8") as f:
    p1 = json.load(f)

for sc in p1.get("scenes", []):
    for l in sc.get("lines", []):
        if l.get("id") == "STm01_07.32":
            l["vi_editorial"] = "Chính xác, đây đích thực là món Cổ Vật truyền tin mà ta đang cần tìm rồi."

with open(p1_path, "w", encoding="utf-8") as f:
    json.dump(p1, f, ensure_ascii=False, indent=2)

# Fix STm02_05.61 in translator_main_2
p2_path = "StellaSora_VietHoa/work/subagents/lightnovel_editorial_20261024_r02/translator_main_2/PROPOSALS_R02.json"
with open(p2_path, "r", encoding="utf-8") as f:
    p2 = json.load(f)

for sc in p2.get("scenes", []):
    for l in sc.get("lines", []):
        if l.get("id") == "STm02_05.61":
            l["vi_editorial"] = "Này! Cô vừa lỡ mồm nói toẹt điều thầm kín trong lòng ra rồi đấy!"

with open(p2_path, "w", encoding="utf-8") as f:
    json.dump(p2, f, ensure_ascii=False, indent=2)

print("Fixed slang occurrences in P1 and P2 source proposals.")
