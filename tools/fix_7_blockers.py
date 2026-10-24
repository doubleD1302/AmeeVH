import json
from pathlib import Path

p_unified = Path(r"StellaSora_VietHoa/work/editorial/act3_story_editorial_20261024_r01/UNIFIED_ACT3_PROPOSALS.jsonl")
p_a = Path(r"StellaSora_VietHoa/work/subagents/act3_story_editorial_20261024_r01/translator_act3_a/PROPOSALS.jsonl")
p_b = Path(r"StellaSora_VietHoa/work/subagents/act3_story_editorial_20261024_r01/translator_act3_b/PROPOSALS.jsonl")

lines = [json.loads(l) for l in p_unified.read_text(encoding="utf-8").splitlines() if l.strip()]

for it in lines:
    lid = it["id"]
    en = it.get("en", "")
    vi = it.get("vi_editorial", "")
    
    if lid == "STm08_11.63":
        # EN had 0 ==W==, remove extra ==W==
        it["vi_editorial"] = vi.replace("==W==", "")
    elif lid == "STm08_11.64":
        it["vi_editorial"] = vi.replace("==W==", "")
    elif lid == "STm08_11.65":
        it["vi_editorial"] = vi.replace("==W==", "")
    elif lid == "STm08_13.50":
        # EN: "What a coincidence.==W== That's wonderful!==W== We're all clear on this end too..."
        # VI had only 1 ==W==
        it["vi_editorial"] = "Trùng hợp đến thế cơ à! Thật tuyệt vời quá đi mất!==W== Bên phía chúng tôi cũng đã giải quyết xong xuôi cả rồi...==W== Hả?"
    elif lid == "STm08_16_a.45":
        # EN: "Um, Noya...==W== Could you at least pretend to hesitate a bit...==W=="
        # Add missing ==W== at the end
        if not vi.endswith("==W=="):
            it["vi_editorial"] = vi.rstrip() + "==W=="
    elif lid == "STm08_18_a.27":
        # EN: "Do you think Auntie could help these kids?==W== She took Amber and me in,==W== so maybe..."
        # Add missing ==W==
        it["vi_editorial"] = "Cậu có nghĩ dì sẽ cưu mang giúp mấy đứa nhỏ này không?==W== Dù sao thì trước đây dì cũng từng nhận nuôi tớ và Amber,==W== nên biết đâu đấy..."
    elif lid == "STm08_19_b.147":
        # EN: "Oh my... A little overdone. I was wondering why I smelled something burning... Slipped my mind!"
        # Change 'mùi khét lẹt' to 'mùi cháy khét'
        it["vi_editorial"] = vi.replace("khét lẹt", "cháy khét")

# Save unified
with open(p_unified, "w", encoding="utf-8") as f:
    for it in lines:
        f.write(json.dumps(it, ensure_ascii=False) + "\n")

# Save partition A & B
part_a_dict = {it["id"]: it for it in lines if it.get("partition") == "PARTITION_A"}
part_b_dict = {it["id"]: it for it in lines if it.get("partition") == "PARTITION_B"}

lines_a = [json.loads(l) for l in p_a.read_text(encoding="utf-8").splitlines() if l.strip()]
for it in lines_a:
    if it["id"] in part_a_dict:
        it["vi_editorial"] = part_a_dict[it["id"]]["vi_editorial"]
with open(p_a, "w", encoding="utf-8") as f:
    for it in lines_a:
        f.write(json.dumps(it, ensure_ascii=False) + "\n")

lines_b = [json.loads(l) for l in p_b.read_text(encoding="utf-8").splitlines() if l.strip()]
for it in lines_b:
    if it["id"] in part_b_dict:
        it["vi_editorial"] = part_b_dict[it["id"]]["vi_editorial"]
with open(p_b, "w", encoding="utf-8") as f:
    for it in lines_b:
        f.write(json.dumps(it, ensure_ascii=False) + "\n")

print("Fixed all 7 blockers across unified and partition files successfully!")
