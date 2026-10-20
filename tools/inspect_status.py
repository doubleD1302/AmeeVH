import os
import json

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
status_file = os.path.join(viet_dir, "STATUS.json")
ckpt_file = os.path.join(viet_dir, "CHECKPOINT.json")

with open(status_file, "r", encoding="utf-8") as f:
    st = json.load(f)
print("STATUS keys:", list(st.keys()))
for k in st:
    if isinstance(st[k], dict):
        print(f"  {k}: {list(st[k].keys())[:10]}")
    else:
        print(f"  {k}: {st[k]}")

with open(ckpt_file, "r", encoding="utf-8") as f:
    ckpt = json.load(f)
print("CHECKPOINT keys:", list(ckpt.keys()))
for k in ckpt:
    if isinstance(ckpt[k], (list, dict)):
        print(f"  {k}: length {len(ckpt[k])}")
    else:
        print(f"  {k}: {ckpt[k]}")
