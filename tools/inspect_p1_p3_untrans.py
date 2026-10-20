import json
import re

for part_num, p_file in [(1, "partition1_minigames_modes.json"), (3, "partition3_story_quests_ui.json")]:
    with open(f"c:\\YostarGames\\StellaSora_EN\\StellaSora_VietHoa\\work\\batches\\{p_file}", "r", encoding="utf-8") as f:
        d = json.load(f)
    untrans = []
    for k, table in d.items():
        for sk, s in table["entries"].items():
            words = re.findall(r'[a-zA-Z]{2,}', s)
            has_vi = bool(re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]', s))
            if len(words) >= 2 and not has_vi:
                untrans.append((sk, s))
    print(f"Partition {part_num} English phrases: {len(untrans)}")
    for sk, s in untrans[:5]:
        print(f"  {sk}: {s[:60]}")
