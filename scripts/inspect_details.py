import json

with open('StellaSora_VietHoa/work/subagents/remediation_v110_20261029_r01/story/cjk_defects.json', 'r', encoding='utf-8') as f:
    cjk = json.load(f)

print(f"=== CJK DEFECTS ({len(cjk)}) ===")
for it in cjk:
    print(f"ID: {it['id']} | File: {it['file']}")
    print(f"EN: {it['en']}")
    print(f"VI: {it['vi']}")
    print("-" * 50)

with open('StellaSora_VietHoa/work/subagents/remediation_v110_20261029_r01/story/binary_defects.json', 'r', encoding='utf-8') as f:
    binary = json.load(f)

print(f"\n=== BINARY DEFECTS SAMPLE ({len(binary)}) ===")
for it in binary[:10]:
    print(f"ID: {it['id']} | File: {it['file']}")
    print(f"EN: {repr(it['en'])}")
    print(f"VI: {repr(it['vi'])}")
    print("-" * 50)
