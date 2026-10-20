import json
import re
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
b4_path = os.path.join(viet_dir, r"work\batches\batch_10k_b4_approved.json")
with open(b4_path, "r", encoding="utf-8") as f:
    data = json.load(f)

VI_REGEX = re.compile(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]')

ENGINE_PREFIXES = (
    'fx_', 'story_', 'qstory_', 'ep_', 'city_', 'hotel_', 'wog_', 'luckyoasis_',
    'avg', 'Set', 'Play', 'se_', 'bgm_', 'bgs_', 'btn_', 'icon_', 'item_', 'tex_'
)

no_vi = []
for k, v in data.items():
    if not v or not v.strip():
        continue
    words = re.findall(r'[a-zA-Z]{2,}', v)
    if len(words) >= 2 and not VI_REGEX.search(v) and not v.strip().startswith(ENGINE_PREFIXES) and not re.match(r'^[a-z0-9_]+$', v.strip()):
        no_vi.append((k, v))

print(f"Total entries in batch_10k_b4_approved: {len(data):,}")
print(f"Strings without Vietnamese diacritics: {len(no_vi)}")
for k, v in no_vi[:10]:
    print(f"  [{k}] {v}")
