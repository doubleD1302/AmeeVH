#!/usr/bin/env python3
"""Module for polishing AffinityUpReward table (1,760 items)."""

AFFINITY_UP_REWARD_MAP = {
    'Archive': 'Hồ Sơ',
    'Affinity Title': 'Danh Hiệu Thân Mật',
    'Voiceover': 'Lồng Tiếng',
    'Affinity Up': 'Thăng Cấp Thân Mật',
    'Trekker Story': 'Truyện Ký Lữ Khách',
    'CV Excerpt': 'Trích Yếu Lý Lịch',
    'Special Archive Entry': 'Hồ Sơ Đặc Biệt',
    'Trekker Story, Part Ⅰ': 'Truyện Ký Lữ Khách - Phần Ⅰ',
    'Trekker Story, Part Ⅱ': 'Truyện Ký Lữ Khách - Phần Ⅱ',
    'Trekker Story, Part Ⅲ': 'Truyện Ký Lữ Khách - Phần Ⅲ',
    'Unlock': 'Mở Khóa',
    'Affinity Voiceover 1': 'Lồng Tiếng Thân Mật 1',
    'Peer Comments': 'Đánh Giá Từ Đồng Đội',
    'Affinity Voiceover 2': 'Lồng Tiếng Thân Mật 2',
    'TA Feedback': 'Phản Hồi Từ Hiệp Hội',
    'Appendix': 'Phụ Lục Hồ Sơ',
    'Affinity Voiceover 3': 'Lồng Tiếng Thân Mật 3',
    'Affinity Voiceover 4': 'Lồng Tiếng Thân Mật 4',
    'Affinity Voiceover 5': 'Lồng Tiếng Thân Mật 5',
    'Weapon Anecdote': 'Giai Thoại Binh Khí'
}

def polish_affinity_up_reward(item):
    en = item['en']
    if en in AFFINITY_UP_REWARD_MAP:
        return AFFINITY_UP_REWARD_MAP[en]
    return item['vi_current']

if __name__ == '__main__':
    import json
    from pathlib import Path
    p = Path('StellaSora_VietHoa/work/polish/phase3_dataset.json')
    with open(p, 'r', encoding='utf-8') as f:
        items = json.load(f)['AffinityUpReward']
    polished = [polish_affinity_up_reward(it) for it in items]
    print(f"Polished {len(polished)} / {len(items)} AffinityUpReward items.")
    assert len(polished) == len(items)
    print("AffinityUpReward OK.")
