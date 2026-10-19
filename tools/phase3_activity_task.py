#!/usr/bin/env python3
"""Module for polishing ActivityTask table (919 items)."""

import re
from pathlib import Path

STAGE_NAMES = {
    'Summer Brawl': 'Hỗn Chiến Mùa Hè',
    'Treasure Raider': 'Đoạt Bảo Kỳ Binh',
    'Hexhorn Whale Showdown': 'Quyết Chiến Cá Voi Lục Sừng',
    'Carols & Odd Stove': 'Khúc Thánh Ca & Bếp Lò Kỳ Dị',
    'Fluffy Knight': 'Kỵ Sĩ Lông Xù',
    'Logging Crab Assault': 'Đột Kích Cua Đốn Gỗ',
    'Logging Crab Showdown': 'Quyết Chiến Cua Đốn Gỗ',
    'Dense Woods Hunt': 'Săn Lùng Rừng Rậm',
    'Operation Green Sweep': 'Chiến Dịch Quét Xanh',
    'The Imperial Guards Close In': 'Cận Vệ Hoàng Gia Áp Sát',
    'Leave, Hermit Crab': 'Rời Khỏi Đi, Cua Ẩn Sĩ',
    'Seabreeze Echoes': 'Vọng Âm Gió Biển',
    'Savory Summer': 'Mùa Hè Đậm Đà',
    'Sunlit Sands': 'Bãi Cát Tắm Nắng',
    'Cooling Supply Station': 'Trạm Tiếp Tế Tránh Nóng',
    'Danger Zone!': 'Vùng Nguy Hiểm!',
    'Dark Challenge': 'Khiêu Chiến Bóng Tối',
    'Dark Trial': 'Thử Thách Bóng Tối',
    'Deadly Invitation': 'Lời Mời Chết Chóc',
    'Deadly Magic': 'Ma Thuật Chết Chóc',
    'Decapitation Strike': 'Đòn Đánh Chém Đầu',
    'Defying the Odds': 'Nghịch Cảnh Vươn Lên',
    'Dog Patrol Squad': 'Đội Tuần Tra Chó Săn',
    'Evelong Defense': 'Phòng Thủ Evelong',
    'Fair Competition': 'Cạnh Tranh Công Bằng',
    'Fighting Retreat': 'Vừa Đánh Vừa Lui',
    'Final Proving': 'Minh Chứng Cuối Cùng',
    'Forbidden Fruit': 'Trái Cấm',
    'Greenhouse Inquiry': 'Điều Tra Nhà Kính',
    'Guests Gather': 'Khách Quý Tụ Họp',
    'Here Comes the Boss': 'Thủ Lĩnh Xuất Hiện',
    'Into the Nest': 'Tiến Vào Ổ Địch',
    'Lanterns and Crowds': 'Đèn Hoa & Biển Người',
    'Mail Scramble': 'Tranh Giành Thư Từ',
    'Mech Rampant': 'Cơ Giáp Hoành Hành',
    'New Year\'s Opening': 'Khai Màn Năm Mới',
    'No Risky Stunts': 'Không Hành Động Mạo Hiểm',
    'Perilous Thorns': 'Gai Nhọn Nguy Hiểm',
    'Route Clearance': 'Dọn Sạch Lộ Trình',
    'Runaway Gift Cart': 'Xe Quà Mất Lái',
    'Sharpness Hidden': 'Mũi Nhọn Ẩn Giấu',
    'Shifted Seats': 'Chỗ Ngồi Đảo Lộn',
    'Show Some Grit': 'Thể Hiện Bản Lĩnh',
    'Showcase of Growth': 'Trình Diễn Trưởng Thành',
    'Snowish Eve Escapade': 'Cuộc Đào Tẩu Đêm Tuyết',
    'Suspicious Move': 'Hành Động Khả Nghi',
    'Tech Showdown': 'Quyết Đấu Công Nghệ',
    'The Boss Is Up!': 'Thủ Lĩnh Đã Dậy!',
    'The Forging of War': 'Tôi Luyện Chiến Tranh',
    'The Gloomy Forest': 'Khu Rừng U Ám',
    'The Mastermind': 'Kẻ Chủ Mưu',
    'The Reaping of Souls': 'Thu Hoạch Linh Hồn',
    'Trouble After Trouble': 'Hết Họa Lại Đến Tai',
    'Two Against One?': 'Hai Đánh Một?',
    'Uh-oh, the Hound\'s Here': 'Nguy Rồi, Chó Săn Đã Đến',
    'Vanguard of War': 'Tiên Phong Chiến Tranh',
    'Warm-Up Has Just Begun': 'Khởi Động Mới Bắt Đầu',
}

def translate_stage_name(stg: str) -> str:
    res = stg
    for en_name, vi_name in STAGE_NAMES.items():
        res = res.replace(en_name, vi_name)
    res = res.replace('(Normal)', '(Thường)').replace('(Hard)', '(Khó)').replace('(Expert)', '(Chuyên Gia)').replace('(Beginner)', '(Tân Thủ)')
    return res

def polish_activity_task(item, cn_text: str = ''):
    en = item['en'].strip()
    vi = item['vi_current'].strip()

    # Special stage names without Clear
    if en == 'Clear Carols & Odd Stove Ⅰ':
        return 'Vượt qua Khúc Thánh Ca & Bếp Lò Kỳ Dị Ⅰ'
    if en == 'Clear Carols & Odd Stove Ⅱ':
        return 'Vượt qua Khúc Thánh Ca & Bếp Lò Kỳ Dị Ⅱ'

    # Clear Battle Stages {N} times
    m_bs = re.match(r'Clear event Battle Stages ([0-9]+) times\.?', en, re.I)
    if m_bs:
        return f"Khiêu chiến {m_bs.group(1)} lần ải chiến đấu sự kiện."

    # Clear with 3★
    if en.startswith('Clear ') and 'with 3★' in en:
        stg_part = en[6:].replace('with 3★', '').strip().rstrip('.')
        stg = translate_stage_name(stg_part)
        return f"Đạt đánh giá 3★ vượt qua {stg}"

    # Clear within {N}s
    m_sec = re.match(r'Clear (.+?) within ([0-9]+)s\.?', en, re.I)
    if m_sec:
        stg = translate_stage_name(m_sec.group(1).strip())
        return f"Vượt qua {stg} trong vòng {m_sec.group(2)} giây."

    # Clear with at least {N} Stamina remaining
    m_sta = re.match(r'Clear (.+?) with at least ([0-9]+) Stamina remaining\.?', en, re.I)
    if m_sta:
        stg = translate_stage_name(m_sta.group(1).strip())
        return f"Vượt qua {stg} và còn lại ít nhất {m_sta.group(2)} Thể Lực khi tính điểm."

    # Clear {Stage}
    if en.startswith('Clear ') and not ('Battle Stages' in en):
        stg_part = en[6:].strip().rstrip('.')
        stg = translate_stage_name(stg_part)
        return f"Vượt qua {stg}."

    # Read event story: {Story}.
    m_story = re.match(r'Read event story:\s*(.*?)\.?', en, re.I)
    if m_story:
        # Extract title from vi
        m_vi = re.search(r'(?:sự kiện:\s*|《)(.*?)(?:》|\.|$)', vi)
        vtitle = m_vi.group(1).strip() if m_vi else m_story.group(1).strip()
        return f"Đọc cốt truyện sự kiện: 《{vtitle}》."

    # Collect {N} stars in Hard stages
    m_star = re.match(r'Collect ([0-9]+) stars in Hard stages\.?', en, re.I)
    if m_star:
        return f"Thu thập {m_star.group(1)} sao trong các ải chế độ Khiêu Chiến."

    # General replacements in existing vi
    vi = vi.replace('Cuộc chiến mùa hè rõ ràng', 'Hỗn Chiến Mùa Hè')
    vi = vi.replace('Xóa kho báu', 'Đoạt Bảo Kỳ Binh')
    vi = vi.replace('Xóa Treasure Raider', 'Đoạt Bảo Kỳ Binh')
    vi = vi.replace('Hoàn thành các Giai đoạn Chiến đấu của sự kiện', 'Khiêu chiến')
    vi = vi.replace('cuộc thách đấu cá voi Hexhorn', 'Quyết Chiến Cá Voi Lục Sừng')
    vi = vi.replace('trận đấu với cá voi Hexhorn', 'Quyết Chiến Cá Voi Lục Sừng')
    vi = vi.replace('Lữ khách', 'Lữ Khách')
    return vi

if __name__ == '__main__':
    import json
    entries = Path(__file__).resolve().parent.parent / 'work' / 'research' / 'data_en_original' / 'entries'
    with open(entries / '00728_0xc316bcdb179b0d6e.bin', 'r', encoding='utf-8') as f:
        cn_task = json.load(f)

    p = Path(__file__).resolve().parent.parent / 'work' / 'polish' / 'phase3_dataset.json'
    with open(p, 'r', encoding='utf-8') as f:
        items = json.load(f)['ActivityTask']

    polished = [polish_activity_task(it, cn_task.get(it['key'], '')) for it in items]
    print(f"Polished {len(polished)} / {len(items)} ActivityTask items.")
    assert len(polished) == len(items)

    # Check for remaining bad patterns
    bad = [p for p in polished if any(w in p.lower() for w in ['rõ ràng', 'xóa kho báu', 'xóa treasure', 'clear summer'])]
    print(f"Remaining bad phrases in polished tasks: {len(bad)}")
    assert len(bad) == 0

    for i in range(12):
        print(f"  [{items[i]['key']}] EN: '{items[i]['en']}' -> VI: '{polished[i]}'")
