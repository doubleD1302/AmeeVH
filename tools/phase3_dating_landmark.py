#!/usr/bin/env python3
"""Module for polishing DatingLandmarkEvent table (262 items)."""

import re
from pathlib import Path

DLAND_CUSTOM = {
    'DatingLandmarkEvent.1403.1': 'Thật không đúng lúc, mọi người đều đang trong giờ học nên cổng vào vắng tanh. Bạn và ==DATING_CHARACTER== bèn vờ làm học viên rồi đường hoàng bước vào.',
    'DatingLandmarkEvent.1403.2': 'Bác bảo vệ cẩn thận đánh giá hai bạn một lượt: Trông hai người có thực sự là học viên không? May thay, bác ấy không giữ hai bạn lại.',
    'DatingLandmarkEvent.1403.3': '==DATING_CHARACTER== bảo trông bạn vẫn toát lên vẻ thư sinh như một học viên thực thụ.',
    'DatingLandmarkEvent.1404.2': 'Có vẻ đây là một tiết chuyên ngành khá "nặng đô", bạn hoàn toàn chẳng hiểu nổi mấy khái niệm đó. Nét phấn trên bảng tựa như chữ thiên thư, tiếng giảng bài của giáo sư dần trôi xa, mi mắt bạn bắt đầu trĩu nặng...',
    'DatingLandmarkEvent.1404.3': '"Reng..." Chuông tan học vang lên, bạn cũng vừa kịp choàng tỉnh. Quay đầu nhìn sang, bạn bắt gặp ==DATING_CHARACTER== đang ngồi bên cạnh che miệng cười trộm.',
    'DatingLandmarkEvent.608.3': 'Phụ huynh của đứa trẻ vội chạy tới xin lỗi cả hai. Thật là một phen hú vía nhưng may sao không ai bị thương, hai bạn đều thở phào nhẹ nhõm.',
    'DatingLandmarkEvent.701.1': 'Nghe đồn phiên chợ hôm nay là phiên chợ sầm uất và quy mô nhất dạo gần đây.',
    'DatingLandmarkEvent.724.3': 'Đúng là tâm ý tương thông! Cả hai đều thoáng chút ngại ngùng nhưng rồi lại vui vẻ trao quà cho nhau.',
    'DatingLandmarkEvent.1712.1': 'Chẳng mấy chốc, hai bạn đã tản bộ đến khu suối ngâm chân. Dưới mái đình gỗ mộc mạc là một bể suối nước nóng thon dài xây bằng đá cẩm thạch. Nhân dịp này thử ngâm một chút xem sao, dù gì trong làn nước cạn thế này cũng chẳng sợ nguy hiểm.',
    'DatingLandmarkEvent.812.1': 'Trong nhà ăn thủy thủ có phục vụ trải nghiệm "suất ăn thủy thủ", bạn và ==DATING_CHARACTER== quyết định nếm thử xem sao.',
}

def polish_dating_landmark_item(item):
    k = item['key']
    en = item['en']
    vi = item['vi_current']

    if k in DLAND_CUSTOM:
        return DLAND_CUSTOM[k]

    # Clean awkward patterns
    vi = vi.replace('Lữ khách', 'Lữ Khách')
    vi = vi.replace('Cự tháp', 'Cự Tháp')
    vi = vi.replace('vùng hoang dã', 'Vùng Hoang Dã')
    vi = vi.replace('Thời gian là xấu', 'Thật không đúng lúc')
    vi = vi.replace('đủ để đậu', 'đủ để qua mắt')
    vi = vi.replace('bài giảng dày đặc', 'bài giảng chuyên ngành')
    vi = vi.replace('thị trường ngày nay', 'phiên chợ hôm nay')
    vi = vi.replace('Tâm trí quan tâm nghĩ như nhau', 'Tâm ý tương thông')
    vi = vi.replace('quyết định suýt xảy ra', 'một phen hú vía')
    vi = vi.replace('người ném bóng', 'mũ phớt')
    vi = vi.replace('được coi là', 'tính là')
    vi = vi.replace('có thể được', 'có thể')

    return vi

if __name__ == '__main__':
    p = Path(__file__).resolve().parent.parent / 'work' / 'polish' / 'phase3_dataset.json'
    import json
    with open(p, 'r', encoding='utf-8') as f:
        items = json.load(f)['DatingLandmarkEvent']

    polished = [polish_dating_landmark_item(it) for it in items]
    print(f"Polished {len(polished)} / {len(items)} DatingLandmarkEvent items.")
    assert len(polished) == len(items)

    for i in range(10):
        print(f"  [{items[i]['key']}] EN: '{items[i]['en']}' -> VI: '{polished[i]}'")
