import json
import re

with open('StellaSora_VietHoa/work/subagents/remediation_v110_20261029_r01/story/binary_defects.json', 'r', encoding='utf-8') as f:
    binary = json.load(f)

print(f"Total binary items: {len(binary)}")

# Let's inspect the types of strings
pure_junk = []
mixed_dialogue = []

for b in binary:
    vi = b['vi']
    # Check if there are Vietnamese words or text
    has_vi = any(c in vi for c in "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ")
    if not has_vi:
        pure_junk.append(b)
    else:
        mixed_dialogue.append(b)

print(f"Pure junk / untranslated: {len(pure_junk)}")
print(f"Mixed dialogue with Vietnamese: {len(mixed_dialogue)}")

with open('StellaSora_VietHoa/work/subagents/remediation_v110_20261029_r01/story/binary_pure_junk.txt', 'w', encoding='utf-8') as f:
    for idx, b in enumerate(pure_junk):
        f.write(f"[{idx+1}] ID: {b['id']} | File: {b['file']}\n")
        f.write(f"  EN: {repr(b['en'])}\n")
        f.write(f"  VI: {repr(b['vi'])}\n\n")

with open('StellaSora_VietHoa/work/subagents/remediation_v110_20261029_r01/story/binary_mixed.txt', 'w', encoding='utf-8') as f:
    for idx, b in enumerate(mixed_dialogue):
        f.write(f"[{idx+1}] ID: {b['id']} | File: {b['file']}\n")
        f.write(f"  EN: {repr(b['en'])}\n")
        f.write(f"  VI: {repr(b['vi'])}\n\n")

print("Wrote binary_pure_junk.txt and binary_mixed.txt")
