#!/usr/bin/env python3
"""Module for polishing PenguinCard table (360 items)."""

import json
from pathlib import Path

# Load Chinese sources
ROOT = Path(__file__).resolve().parent.parent
with open(ROOT / 'work' / 'research' / 'data_en_original' / 'entries' / '00833_0x469c8ae265bf9745.bin', 'r', encoding='utf-8') as f:
    CN_PENGUIN = json.load(f)

# Name overrides and polish
PENGUIN_NAME_MAP = {
    # Pending cards
    'PenguinCard.100101.1': 'Tiết Kiệm Chi Phí',
    'PenguinCard.100102.1': 'Tiết Kiệm Chi Phí +1',
    'PenguinCard.100103.1': 'Tiết Kiệm Chi Phí +2',
    'PenguinCard.100201.1': 'Giả Ngây Vượt Ải',
    'PenguinCard.100202.1': 'Giả Ngây Vượt Ải +1',
    'PenguinCard.100203.1': 'Giả Ngây Vượt Ải +2',
    'PenguinCard.100301.1': 'Ta Muốn Kiểm Bài',
    'PenguinCard.100302.1': 'Ta Muốn Kiểm Bài +1',
    'PenguinCard.100303.1': 'Ta Muốn Kiểm Bài +2',
    'PenguinCard.100401.1': 'Kỳ Thuật Hầu Gái',
    'PenguinCard.100402.1': 'Kỳ Thuật Hầu Gái +1',
    'PenguinCard.100403.1': 'Kỳ Thuật Hầu Gái +2',
    'PenguinCard.100501.1': 'Tràn Đầy Sức Sống',
    'PenguinCard.100601.1': 'Kỳ Tinh May Mắn',
    'PenguinCard.100602.1': 'Kỳ Tinh May Mắn +1',
    'PenguinCard.100603.1': 'Kỳ Tinh May Mắn +2',
}

# Polish specific translations
PENGUIN_NAME_REPLACEMENTS = {
    'Ánh Sao Lấp Lánh': 'Tinh Hỏa',
    'Độc Quyền Bão Tố': 'Tài Phiệt Bão Tố',
    'Thúc Đẩy Làn Sóng': 'Dâng Sóng Trợ Lực',
    'Lợi Nhuận Tái Sinh': 'Thu Hoạch Thặng Dư',
    'Sóng Lớn Cuộn Trào': 'Sóng Dữ Cuộn Trào',
    'Vực Sâu Tương Phùng': 'Vực Sâu Định Mệnh',
    'Hỏa Diễm Tương Lai': 'Ngọn Lửa Định Mệnh',
    'Cội Nguồn Truy Vết': 'Cội Nguồn Định Mệnh',
    'Ngọn Gió Định Hướng': 'Ngọn Gió Định Mệnh',
    'Chúa Tể Địa Ngục': 'Chúa Tể Vực Sâu',
}

def polish_penguin_card(item):
    k = item['key']
    en = item['en']
    vi = item['vi_current']

    if k in PENGUIN_NAME_MAP:
        return PENGUIN_NAME_MAP[k]

    if k.endswith('.1'):
        # Name polish
        for old, new in PENGUIN_NAME_REPLACEMENTS.items():
            if old in vi:
                vi = vi.replace(old, new)
        return vi

    if k.endswith('.2'):
        # Desc polish
        # Clean passive & grammar
        vi = vi.replace('được coi là nguyên tố bất kỳ', 'tính là nguyên tố bất kỳ')
        vi = vi.replace('Mỗi hiệp nhận 1 lượt xem trước bài', 'Mỗi hiệp nhận 1 lượt kiểm bài')
        vi = vi.replace('Mỗi hiệp nhận 2 lượt xem trước bài', 'Mỗi hiệp nhận 2 lượt kiểm bài')
        vi = vi.replace('Mỗi hiệp nhận 3 lượt xem trước bài', 'Mỗi hiệp nhận 3 lượt kiểm bài')
        vi = vi.replace('hồi phục 1 Thể lực', 'hồi phục 1 Thể Lực')
        vi = vi.replace('Mục tiêu qua màn giảm', 'Mục tiêu vượt ải giảm')
        vi = vi.replace('thăng giai {TriggerParam_1} thành', 'đột phá bậc {TriggerParam_1} thành')
        vi = vi.replace('thăng giai {TriggerParam_1} đến', 'đột phá bậc {TriggerParam_1} đến')
        vi = vi.replace('thăng giai {TriggerParam_1}', 'đột phá bậc {TriggerParam_1}')
        vi = vi.replace('được kích hoạt bởi', 'kích hoạt khi')
        vi = vi.replace('được tạo ra bởi', 'tạo ra từ')
        return vi

    return vi

if __name__ == '__main__':
    p = Path('StellaSora_VietHoa/work/polish/phase3_dataset.json')
    with open(p, 'r', encoding='utf-8') as f:
        items = json.load(f)['PenguinCard']

    polished = [polish_penguin_card(it) for it in items]
    print(f"Polished {len(polished)} / {len(items)} PenguinCard items.")
    assert len(polished) == len(items)
    for i in range(10):
        print(f"  [{items[i]['key']}] EN: '{items[i]['en']}' -> VI: '{polished[i]}'")
