import json

with open('StellaSora_VietHoa/work/subagents/remediation_v110_20261029_r01/story/binary_defects.json', 'r', encoding='utf-8') as f:
    binary = json.load(f)

unique_ids = {}
for b in binary:
    qid = b['id']
    if qid not in unique_ids:
        unique_ids[qid] = {
            "id": qid,
            "files": [],
            "en": b['en'],
            "vi": b['vi']
        }
    unique_ids[qid]["files"].append(b['file'])

with open('StellaSora_VietHoa/work/subagents/remediation_v110_20261029_r01/story/unique_binary_132.json', 'w', encoding='utf-8') as f:
    json.dump(list(unique_ids.values()), f, ensure_ascii=False, indent=2)

print(f"Dumped {len(unique_ids)} unique binary IDs.")
