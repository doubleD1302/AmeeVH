import json

with open('StellaSora_VietHoa/work/subagents/remediation_v110_20261029_r01/story/binary_defects.json', 'r', encoding='utf-8') as f:
    binary = json.load(f)

print(f"Total binary: {len(binary)}")
# Group by file
files = {}
for b in binary:
    files.setdefault(b['file'], []).append(b)

for fname, items in files.items():
    print(f"File: {fname}: {len(items)} items")

# Let's inspect some of them in detail
with open('StellaSora_VietHoa/work/subagents/remediation_v110_20261029_r01/story/binary_inspection.txt', 'w', encoding='utf-8') as f:
    for idx, b in enumerate(binary):
        f.write(f"[{idx+1}] File: {b['file']} | ID: {b['id']}\n")
        f.write(f"  EN: {repr(b['en'])}\n")
        f.write(f"  VI: {repr(b['vi'])}\n\n")

print("Dumped binary_inspection.txt")
