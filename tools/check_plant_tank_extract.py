import json
import re

with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA.json', 'r', encoding='utf-8') as f:
    src = json.load(f)
with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA_translated.json', 'r', encoding='utf-8') as f:
    dst = json.load(f)

print("Checking 'Nhà máy' (from Plant):")
for k, v in dst.items():
    if 'nhà máy' in v.lower() and 'plant' in src.get(k, '').lower():
        print(f"[{k}]\n  SRC: {src[k]}\n  DST: {v}")

print("\nChecking 'xe tăng' (from Tank):")
for k, v in dst.items():
    if 'xe tăng' in v.lower() and 'tank' in src.get(k, '').lower():
        print(f"[{k}]\n  SRC: {src[k]}\n  DST: {v}")

print("\nChecking 'giải nén' (from Extract):")
for k, v in dst.items():
    if 'giải nén' in v.lower() and 'extract' in src.get(k, '').lower():
        print(f"[{k}]\n  SRC: {src[k]}\n  DST: {v}")
