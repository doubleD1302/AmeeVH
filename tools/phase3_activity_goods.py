#!/usr/bin/env python3
"""Module for polishing ActivityGoods table (818 items)."""

import re
from pathlib import Path

GOODS_TITLE_MAP = {
    # Mistranslated items
    'Exeunt Bowler': 'Mũ Phớt Hạ Màn',
    'Spotlight Bowler': 'Mũ Dạ Ánh Đèn',
    'Summer March': 'Hành Khúc Mùa Hè',
    'Summer March Melody': 'Giai Điệu Hành Khúc Mùa Hè',
    'Monolith Stairs Pass': 'Vé Thang Sao Cự Tháp',
    'Cerulean Ticket': 'Vé Thanh Không',
    'Sprout Ticket': 'Vé Manh Nha',
    'Fighting Game Cartridge': 'Băng Game Đối Kháng',
    'Magic Sound Game Cartridge': 'Băng Game Ma Âm',
    'Rhythm Game Cartridge': 'Băng Game Âm Nhạc',
    'Phantom Game Cartridge': 'Băng Game Quỷ Thần',
    'Demon Bee Game Cartridge': 'Băng Game Yêu Ong',
    'Star Emblem Polisher': 'Dung Dịch Đánh Bóng Tinh Chương',
    'Exquisite Blower': 'Quạt Cầm Tay Tinh Xảo',
    'Chilling Wind Spinner': 'Cánh Quạt Nghỉ Mát',
    'Moonlit Companion': 'Vầng Trăng Bầu Bạn',
    'Count\'s Gift': 'Ân Điển Của Nam Tước',
    'Summer Sanctuary': 'Miền Trú Ẩn Mùa Hè',
    'Summer Sanctuary Melody': 'Giai Điệu Miền Trú Ẩn Mùa Hè',
    'Daring Adventure! The Ghost Ship Haunts the Deep': 'Thám Hiểm Ly Kỳ! Huyền Thoại Tàu Ma Vực Biển',
    'Wine Warm, Lamps Alight': 'Khi Rượu Ấm Đèn Hoa Lên',
    'Wine Warm, Lamps Alight Melody': 'Giai Điệu Khi Rượu Ấm Đèn Hoa Lên',
    'Winter Requiem and the Trigger of Dawn': 'Trấn Hồn Khúc Đêm Đông & Cò Súng Bình Minh',
    'Go, My Lady! Training Handbook Plus!': 'Cố Lên Nào! Cẩm Nang Tu Luyện Lữ Khách Của Tiểu Thư!',
    'Guild Sweet Guild': 'Lữ Đoàn Của Chúng Ta',
    'Heartbeat! Neo-Inspired Rhapsody': 'Thình Thịch! Cuồng Tưởng Khúc Ánh Sáng Dịu',
    'Seed Alike': 'Tựa Như Đôi Ta',
    'Seed Alike Melody': 'Giai Điệu Tựa Như Đôi Ta',
    'Solitary Waltz in Night\'s Embrace': 'U Dạ Độc Vũ Ảnh Đơn Côi',
    'Reflective Photo Capturer': 'Máy Ảnh Phản Chiếu',
    'Fist of Courage': 'Nắm Đấm Dũng Khí',
    'Fist of Courage Melody': 'Giai Điệu Nắm Đấm Dũng Khí',
    'Framing the Feelings Unseen': 'Khung Hình Bắt Trọn Tâm Can',
    'Emerging Talent': 'Tài Năng Tỏa Sáng',
    'Miracle of a Flicker': 'Kỳ Tích Đốm Lửa Nhỏ',
    'Joyful Gathering': 'Khoảnh Khắc Tụ Họp',
    'Joyful Gathering Melody': 'Giai Điệu Khoảnh Khắc Tụ Họp',
    'Moment of Glory': 'Khoảnh Khắc Vinh Quang',
    'Moment of Glory Melody': 'Giai Điệu Khoảnh Khắc Vinh Quang',
    'To My Dearest You': 'Kính Gửi, Người Tôi Trân Quý Nhất',
    'Touch of Miracle': 'Cú Chạm Kỳ Tích',
    'Touch of Miracle Melody': 'Giai Điệu Cú Chạm Kỳ Tích',
    'The Bud of Change': 'Mầm Mống Đổi Mới',
    'The Bud of Change Melody': 'Giai Điệu Mầm Mống Đổi Mới',
    'The Break of Frost Melody': 'Giai Điệu Bình Minh Sau Đêm Đông',
    'Wrath Beauty': 'Thịnh Nộ Giai Nhân',
    'Radiant Messenger, Holy Night Spirit': 'Sứ Giả Rạng Rỡ & Tinh Linh Đêm Thánh',
    'Sunlit Breeze, Azure Seas: Checking In for A Cozy Summer~': 'Gió Lộng Biển Xanh · Thư Thái Ngày Hè Cùng Check-in~',
    'Surfing Splash: A Sparkling Holiday Adventure!': 'Sóng Reo Hát Mừng · Thám Hiểm Sóng Lớn Kỳ Nghỉ Rực Rỡ!',
}

GOODS_DESC_REPLACEMENTS = [
    # Currency
    ('Một loại tiền tệ cơ bản có thể được sử dụng trong nhiều tính năng khác nhau.', 'Tiền tệ cơ bản, dùng cho nhiều tính năng trong game.'),
    # Tickets
    ('Chứng chỉ được sử dụng để tuyển dụng trong Limited Lữ khách Banner.', 'Vé dùng để chiêu mộ trong [Kỳ Chiêu Mộ Lữ Khách Giới Hạn].'),
    ('Chứng chỉ được sử dụng để tuyển dụng vào Biểu ngữ Lữ khách vĩnh viễn.', 'Vé dùng để chiêu mộ trong [Kỳ Chiêu Mộ Lữ Khách Thường Trực].'),
    ('Một thẻ được sử dụng để bắt đầu Cự tháp Express.', 'Vé dùng để mở tính năng Tốc Hành Cự Tháp.'),
    # Upgrades & materials
    ('Nguyên liệu cao cấp dùng để thăng giai Lữ khách.', 'Nguyên liệu cao cấp dùng để đột phá bậc Lữ Khách.'),
    ('Nguyên liệu cao cấp dùng để nâng cấp kỹ năng Lữ khách.', 'Nguyên liệu cao cấp dùng để nâng cấp kỹ năng Lữ Khách.'),
    ('Nguyên liệu cao cấp dùng để thăng giai Đĩa nhạc.', 'Nguyên liệu cao cấp dùng để đột phá bậc Đĩa Cổ Ngữ.'),
    ('Một Đĩa nhạc Cổ ngữ mang tên [Khu Bảo Tồn Mùa Hè]. Có thể phát huy sức mạnh to lớn.', 'Đĩa Cổ Ngữ mang tên [Miền Trú Ẩn Mùa Hè], ẩn chứa uy lực mạnh mẽ.'),
    ('Nguyên liệu cần thiết để Đột phá Đĩa nhạc: Khu Bảo Tồn Mùa Hè.', 'Nguyên liệu cần thiết để đột phá Đĩa Cổ Ngữ: Miền Trú Ẩn Mùa Hè.'),
    ('Mở khóa Danh hiệu vinh dự: Cuộc phiêu lưu táo bạo! Con tàu ma ám ảnh vực sâu.', 'Mở khóa Danh Hiệu Danh Dự: Thám Hiểm Ly Kỳ! Huyền Thoại Tàu Ma Vực Biển.'),
    ('Nguyên liệu đặc biệt dùng để khóa Dòng thuộc tính khi đúc lại Huy hiệu Lữ khách.', 'Nguyên liệu đặc biệt dùng để khóa Dòng Thuộc Tính khi đúc lại Huy Hiệu Lữ Khách.'),
    ('Cung cấp lượng lớn EXP để tăng cấp Lữ khách.', 'Cung cấp lượng lớn EXP để tăng cấp Lữ Khách.'),
    ('Lữ khách', 'Lữ Khách'),
]

def polish_activity_goods(item):
    k = item['key']
    en = item['en']
    vi = item['vi_current']

    if k.endswith('.1'):
        if en in GOODS_TITLE_MAP:
            return GOODS_TITLE_MAP[en]
        return vi

    if k.endswith('.2'):
        for old, new in GOODS_DESC_REPLACEMENTS:
            vi = vi.replace(old, new)
        return vi

    return vi

if __name__ == '__main__':
    import json
    p = Path('StellaSora_VietHoa/work/polish/phase3_dataset.json')
    with open(p, 'r', encoding='utf-8') as f:
        items = json.load(f)['ActivityGoods']

    polished = [polish_activity_goods(it) for it in items]
    print(f"Polished {len(polished)} / {len(items)} ActivityGoods items.")
    assert len(polished) == len(items)
    for i in range(10):
        print(f"  [{items[i]['key']}] EN: '{items[i]['en']}' -> VI: '{polished[i]}'")
