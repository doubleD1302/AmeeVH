import json
import re
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00728_0xc316bcdb179b0d6e.bin', 'r', encoding='utf-8') as f:
    cn_task = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    tasks = json.load(f)['ActivityTask']

print("Checking ActivityTask translation patterns...")
stages_map = {
    'Summer Brawl': 'Hỗn Chiến Mùa Hè',
    'Treasure Raider': 'Đoạt Bảo Kỳ Binh',
    'Hexhorn Whale Showdown': 'Quyết Chiến Cá Voi Lục Sừng',
    'Carols & Odd Stove': 'Khúc Thánh Ca & Bếp Lò Kỳ Dị',
}

def polish_task(en, cn, vi):
    # Untranslated English stages
    if en == 'Clear Carols & Odd Stove Ⅰ':
        return 'Vượt qua Khúc Thánh Ca & Bếp Lò Kỳ Dị Ⅰ'
    if en == 'Clear Carols & Odd Stove Ⅱ':
        return 'Vượt qua Khúc Thánh Ca & Bếp Lò Kỳ Dị Ⅱ'

    # 1. Clear {Stage} with 3★
    m = re.match(r'Clear (.*?) with 3★\.?', en)
    if m:
        stg = m.group(1).strip()
        for k, v in stages_map.items():
            stg = stg.replace(k, v)
        stg = stg.replace('(Normal)', '(Thường)').replace('(Hard)', '(Khó)')
        return f"Đạt đánh giá 3★ vượt qua {stg}"

    # 2. Clear {Stage}
    m = re.match(r'Clear (.*?)\.?', en)
    if m:
        stg = m.group(1).strip()
        # check if it is Battle Stages
        m_bs = re.match(r'event Battle Stages ([0-9]+) times\.?', stg)
        if m_bs:
            return f"Khiêu chiến {m_bs.group(1)} lần ải chiến đấu sự kiện."
        if 'Battle Stages' in stg:
            m_cnt = re.search(r'([0-9]+)', stg)
            if m_cnt:
                return f"Khiêu chiến {m_cnt.group(1)} lần ải chiến đấu sự kiện."

        for k, v in stages_map.items():
            stg = stg.replace(k, v)
        stg = stg.replace('(Normal)', '(Thường)').replace('(Hard)', '(Khó)')
        return f"Vượt qua {stg}."

    # 3. Read event story: {Story}.
    m = re.match(r'Read event story:\s*(.*?)\.?', en)
    if m:
        stitle = m.group(1).strip()
        # use CN title if available: 《...》
        m_cn = re.search(r'《(.*?)》', cn)
        # We can extract existing Vietnamese story title from vi if already translated
        m_vi = re.search(r'(?:sự kiện:\s*|《)(.*?)(?:》|\.|$)', vi)
        vtitle = m_vi.group(1).strip() if m_vi else stitle
        return f"Đọc cốt truyện sự kiện: 《{vtitle}》."

    # 4. Collect {X} stars in Hard stages
    m = re.match(r'Collect ([0-9]+) stars in Hard stages\.?', en)
    if m:
        return f"Thu thập {m.group(1)} sao trong các ải chế độ Khiêu Chiến."

    # General replacements in existing vi
    vi = vi.replace('Cuộc chiến mùa hè rõ ràng', 'Hỗn Chiến Mùa Hè')
    vi = vi.replace('Xóa kho báu', 'Đoạt Bảo Kỳ Binh')
    vi = vi.replace('Xóa Treasure Raider', 'Đoạt Bảo Kỳ Binh')
    vi = vi.replace('Hoàn thành các Giai đoạn Chiến đấu của sự kiện', 'Khiêu chiến')
    vi = vi.replace('cuộc thách đấu cá voi Hexhorn', 'Quyết Chiến Cá Voi Lục Sừng')
    vi = vi.replace('trận đấu với cá voi Hexhorn', 'Quyết Chiến Cá Voi Lục Sừng')
    vi = vi.replace('Lữ khách', 'Lữ Khách')
    return vi

# Test on all tasks
tested = [polish_task(it['en'], cn_task.get(it['key'], ''), it['vi_current']) for it in tasks]
print(f"Tested {len(tested)} tasks.")
for i in range(15):
    print(f"  [{tasks[i]['key']}] EN: '{tasks[i]['en']}' -> VI: '{tested[i]}'")
