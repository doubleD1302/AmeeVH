import json
import re
from pathlib import Path

flaw_patterns = [
    r'máy chủ', # server in restaurant!
    r'bản in đẹp', # fine print
    r'nhà vô địch của công lý', # champion of justice
    r'Thời gian là xấu', # The timing is bad
    r'lừa gạt để xâm nhập', # bluff your way in
    r'đủ để đậu', # enough to pass
    r'người ném bóng', # bowler
    r'bài giảng dày đặc', # dense lecture
    r'mùa hè tháng ba', # summer march
    r'ở một mình trong',
    r'vùng hoang dã',
    r'mất khả năng lao động',
    r'có thể được',
    r'được sử dụng',
    r'được áp dụng',
    r'được nhận',
    r'được coi là',
    r'gây ra bởi',
    r'tăng lên bởi',
    r'giảm đi bởi',
    r'lữ khách', # lowercase
    r'tân tinh',
    r'Đóng mạng',
    r'khoai tây chiên',
    r'trại trẻ mồ côi',
    r'của bạn',
    r'cho bạn',
    r'nó giải phóng',
    r'bị chôn vùi',
    r'Thủ thuật quán cà phê',
    r'móng vuốt giải thưởng',
    r'chết đuối',
    r'Tâm trí quan tâm',
    r'quyết định suýt xảy ra',
    r'thị trường ngày nay',
    r'lợi nhuận khó khăn',
    r'Năm xa nhau',
    r'có cơ hội giúp bạn',
    r'một người lăn đi',
]

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    p3 = json.load(f)

for tname in ['Story', 'ActivityStory', 'DatingLandmarkEvent', 'DatingCharacterEvent']:
    items = p3[tname]
    found = []
    for it in items:
        vi = it['vi_current']
        en = it['en']
        k = it['key']
        matches = [p for p in flaw_patterns if re.search(p, vi, re.I)]
        if matches:
            found.append((k, en, vi, matches))
    print(f"\nTable {tname}: {len(found)} / {len(items)} items matched flaw patterns")
    for k, en, vi, matches in found[:8]:
        print(f"  [{k}] Matches: {matches}")
        print(f"    EN: {en}")
        print(f"    VI: {vi}")
