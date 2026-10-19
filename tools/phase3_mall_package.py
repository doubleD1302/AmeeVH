#!/usr/bin/env python3
"""Module for polishing MallPackage table (435 items)."""

import re
from pathlib import Path

REPLACEMENTS = [
    (r'\bGói Vé Cerulean\b', 'Gói Vé Thanh Không'),
    (r'\bVé Cerulean\b', 'Vé Thanh Không'),
    (r'\bSiêu Trị\b', 'Siêu Tiết Kiệm'),
    (r'\bƯu Đãi Cầu Nguyện Gói\b', 'Ưu Đãi Cầu Nguyện - Gói'),
    (r'\bƯu Đãi Hàng Tuần Gói\b', 'Ưu Đãi Hàng Tuần - Gói'),
    (r'\bƯu Đãi Hàng Tháng Gói\b', 'Ưu Đãi Hàng Tháng - Gói'),
    (r'\bÁnh Đao Lấp Lánh Gói\b', 'Ánh Đao Lấp Lánh - Gói'),
    (r'\bSóng Lớn Cuộn Trào Gói\b', 'Sóng Lớn Cuộn Trào - Gói'),
    (r'\bMầm Non Nở Rộ Gói\b', 'Mầm Non Nở Rộ - Gói'),
    (r'\bGió Nhẹ Lãng Mạn Gói\b', 'Gió Nhẹ Lãng Mạn - Gói'),
    (r'\bTiệc Trà Chiều Gói\b', 'Tiệc Trà Chiều - Gói'),
    (r'\bVạn Tượng Khởi Nguyên Gói\b', 'Vạn Tượng Khởi Nguyên - Gói'),
    (r'\bKhúc Hát Biển Khơi Gói\b', 'Khúc Hát Biển Khơi - Gói'),
    (r'\bThanh Âm Mùa Hè Gói\b', 'Thanh Âm Mùa Hè - Gói'),
    (r'\bThử Thách Vô Tận Gói\b', 'Thử Thách Vô Tận - Gói'),
    (r'\bĐêm Hội Pháo Hoa Gói\b', 'Đêm Hội Pháo Hoa - Gói'),
    (r'\bÁnh Lửa Rực Rỡ Gói\b', 'Ánh Lửa Rực Rỡ - Gói'),
    (r'\bLữ khách\b', 'Lữ Khách'),
]

def polish_mall_package(item):
    vi = item['vi_current']
    for pattern, repl in REPLACEMENTS:
        vi = re.sub(pattern, repl, vi)
    return vi

if __name__ == '__main__':
    import json
    p = Path('StellaSora_VietHoa/work/polish/phase3_dataset.json')
    with open(p, 'r', encoding='utf-8') as f:
        items = json.load(f)['MallPackage']

    polished = [polish_mall_package(it) for it in items]
    print(f"Polished {len(polished)} / {len(items)} MallPackage items.")
    assert len(polished) == len(items)
    for i in range(10):
        print(f"  [{items[i]['key']}] EN: '{items[i]['en']}' -> VI: '{polished[i]}'")
