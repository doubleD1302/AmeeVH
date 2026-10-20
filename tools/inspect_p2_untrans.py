import json
import re

with open(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\partition2_characters_tactics.json", "r", encoding="utf-8") as f:
    d = json.load(f)

untrans = []
for k, table in d.items():
    for sk, s in table["entries"].items():
        words = re.findall(r'[a-zA-Z]{2,}', s)
        has_vi = bool(re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]', s))
        if len(words) >= 2 and not has_vi:
            untrans.append((sk, s))

print(f"Total English phrases in Partition 2: {len(untrans)}")
for sk, s in untrans[:15]:
    print(f"  {sk}: {s[:60]}")
