import json

with open('StellaSora_VietHoa/work/subagents/remediation_v110_20261029_r01/story/en_defects.json', 'r', encoding='utf-8') as f:
    en_items = json.load(f)

print(f"Total EN defects: {len(en_items)}")
unique_en_ids = {}
for it in en_items:
    qid = it['id']
    if qid not in unique_en_ids:
        unique_en_ids[qid] = []
    unique_en_ids[qid].append(it)

print(f"Unique IDs: {len(unique_en_ids)}")

with open('StellaSora_VietHoa/work/subagents/remediation_v110_20261029_r01/story/en_defects_details.txt', 'w', encoding='utf-8') as f:
    for qid, items in unique_en_ids.items():
        f.write(f"ID: {qid} (in {len(items)} files: {[x['file'] for x in items]})\n")
        f.write(f"  EN: {repr(items[0]['en'])}\n")
        f.write(f"  VI: {repr(items[0]['vi'])}\n\n")

print("Wrote en_defects_details.txt")
