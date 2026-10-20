import json
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
b4_path = os.path.join(viet_dir, r"work\batches\batch_10k_b4_approved.json")
with open(b4_path, "r", encoding="utf-8") as f:
    data = json.load(f)

keys = ['STm09_01_d.15', 'STm09_01_d.126', 'STm09_01_d.242', 'STm09_01_d.265', 'STm09_02_c.20']
for k in keys:
    print(k, "repr:", repr(data.get(k)))
