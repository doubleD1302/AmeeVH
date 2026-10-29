import json

with open('StellaSora_VietHoa/work/subagents/remediation_v110_20261029_r01/story/binary_defects.json', 'r', encoding='utf-8') as f:
    binary = json.load(f)

for idx, b in enumerate(binary):
    vi = b['vi']
    has_vi = any(c in vi for c in "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ")
    if not has_vi:
        print(f"[{idx+1}] ID: {b['id']} | File: {b['file']}")
        print(f"  EN: {repr(b['en'])}")
        print(f"  VI: {repr(b['vi'])}")
        print()
