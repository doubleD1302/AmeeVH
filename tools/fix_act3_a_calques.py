import json
from pathlib import Path
import hashlib

p = Path(r"StellaSora_VietHoa/work/subagents/act3_story_editorial_20261024_r01/translator_act3_a/PROPOSALS.jsonl")
lines = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]

fixes = {
    "STm08_17_b.73": "Thứ quỷ quái gì thế này—! Đó chẳng lẽ là... Quyền Trượng Tử Thần sao?!==W== Khốn thật, mau rút lui! Thoái lui ngay!",
    "STm08_17_b.105": "Bán vũ khí giá rẻ như cho không, rồi thu lợi nhuận kếch xù từ việc bán đạn dược. Haha, tay Sếp đó đúng là một thiên tài kinh doanh quỷ quyệt.",
    "STm08_18_a.170": "Tình hình gay go rồi.==W== Ai đó mau bắn pháo hiệu cầu cứu đi!==W=="
}

patched = 0
for it in lines:
    lid = it.get("id")
    if lid in fixes:
        print(f"Patching {lid}:")
        print(f"  Old: {it['vi_editorial']}")
        it["vi_editorial"] = fixes[lid]
        print(f"  New: {it['vi_editorial']}")
        patched += 1

print(f"Patched {patched} lines.")
with open(p, "w", encoding="utf-8") as f:
    for it in lines:
        f.write(json.dumps(it, ensure_ascii=False) + "\n")

h = hashlib.sha256(p.read_bytes()).hexdigest()
print(f"New SHA256 of PROPOSALS.jsonl: {h}")
