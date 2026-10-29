import json

with open('StellaSora_VietHoa/work/subagents/remediation_v110_20261029_r01/story/binary_defects.json', 'r', encoding='utf-8') as f:
    binary = json.load(f)

unique_ids = {}
for b in binary:
    qid = b['id']
    if qid not in unique_ids:
        unique_ids[qid] = []
    unique_ids[qid].append(b)

print(f"Total entries: {len(binary)}, Unique IDs: {len(unique_ids)}")

for qid, items in list(unique_ids.items())[:20]:
    files = [it['file'] for it in items]
    print(f"ID: {qid} (in {len(files)} files: {files})")
    print(f"  EN: {repr(items[0]['en'])}")
    print(f"  VI: {repr(items[0]['vi'])}")
    print("-" * 50)
