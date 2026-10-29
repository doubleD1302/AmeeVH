import json

with open('StellaSora_VietHoa/work/subagents/remediation_v110_20261029_r01/story/unique_binary_132.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

with open('StellaSora_VietHoa/work/subagents/remediation_v110_20261029_r01/story/all_132_binary.txt', 'w', encoding='utf-8') as f:
    for i, it in enumerate(items):
        f.write(f"=== [{i+1}] ID: {it['id']} | Files: {it['files']} ===\n")
        f.write(f"EN: {repr(it['en'])}\n")
        f.write(f"VI: {repr(it['vi'])}\n\n")

print(f"Dumped {len(items)} binary items to all_132_binary.txt")
