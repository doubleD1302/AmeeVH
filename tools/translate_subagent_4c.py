#!/usr/bin/env python3
"""
Rewards, Shop & Card Tables Translator for Stella Sora (EN -> VI)
Subagent 4C: Translates AffinityUpReward, ActivityGoods, MallPackage, PenguinCard
Guarantees 100% preservation of tokens: {0}, {1}, <color=...>, </color>, \\n, \\x0b, &Param...&, ##...#
"""

import json
import re
import shutil
import sys
import time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_DIR = ROOT / "work" / "research" / "data_decrypted" / "entries"
CACHE_PATH = ROOT / "work" / "batches" / "rewards_economy_translation_cache.json"
ITEM_CACHE_PATH = ROOT / "work" / "batches" / "item_db_translation_cache.json"

TABLES = [
    {
        "name": "AffinityUpReward",
        "en_file": "00511_0xc0b538ebf3963e61.bin",
        "cn_file": "00732_0xaa8312ae07d84ae0.bin",
        "expected_count": 1760,
    },
    {
        "name": "ActivityGoods",
        "en_file": "00498_0x988f7b6f2592bacd.bin",
        "cn_file": "00719_0x6685539fd40c9e98.bin",
        "expected_count": 818,
    },
    {
        "name": "MallPackage",
        "en_file": "00594_0xee9e1d54770d965d.bin",
        "cn_file": "00815_0x6f0361474c111904.bin",
        "expected_count": 435,
    },
    {
        "name": "PenguinCard",
        "en_file": "00612_0x6125df00885a1629.bin",
        "cn_file": "00833_0x469c8ae265bf9745.bin",
        "expected_count": 360,
    },
]

# 1. Exact mapping for AffinityUpReward (all 20 unique strings)
AFFINITY_UP_REWARD_MAP = {
    "Affinity Title": "Danh hiệu Độ thân mật",
    "Affinity Up": "Tăng cấp Độ thân mật",
    "Affinity Voiceover 1": "Lồng tiếng Độ thân mật 1",
    "Affinity Voiceover 2": "Lồng tiếng Độ thân mật 2",
    "Affinity Voiceover 3": "Lồng tiếng Độ thân mật 3",
    "Affinity Voiceover 4": "Lồng tiếng Độ thân mật 4",
    "Affinity Voiceover 5": "Lồng tiếng Độ thân mật 5",
    "Appendix": "Phụ lục Hồ sơ",
    "Archive": "Hồ sơ",
    "CV Excerpt": "Trích yếu Hồ sơ",
    "Peer Comments": "Đánh giá từ Đồng nghiệp",
    "Special Archive Entry": "Hồ sơ Đặc biệt",
    "TA Feedback": "Phản hồi từ Hiệp hội",
    "Trekker Story": "Cốt truyện Lữ khách",
    "Trekker Story, Part Ⅰ": "Cốt truyện Lữ khách - Phần Ⅰ",
    "Trekker Story, Part Ⅱ": "Cốt truyện Lữ khách - Phần Ⅱ",
    "Trekker Story, Part Ⅲ": "Cốt truyện Lữ khách - Phần Ⅲ",
    "Unlock": "Mở khóa",
    "Voiceover": "Lồng tiếng",
    "Weapon Anecdote": "Giai thoại Vũ khí",
}

# 2. Exact mappings for ActivityGoods (the 41 new strings)
ACTIVITY_GOODS_EXACT = {
    'A Disc Record titled "Touch of Miracle". It can unleash great power.': 'Một Đĩa nhạc mang tên "Chạm Vào Kỳ Tích". Có thể phát huy sức mạnh to lớn.',
    'A Runic Disc titled [A Gift for the Journey]. It can unleash great power.': 'Một Đĩa nhạc Cổ ngữ mang tên [Món Quà Cho Cuộc Hành Trình]. Có thể phát huy sức mạnh to lớn.',
    'A Runic Disc titled [All That Was Beautiful]. It can unleash great power.': 'Một Đĩa nhạc Cổ ngữ mang tên [Mọi Điều Từng Đẹp Đẽ]. Có thể phát huy sức mạnh to lớn.',
    'A Runic Disc titled [Dappled Sunlight]. It can unleash great power.': 'Một Đĩa nhạc Cổ ngữ mang tên [Ánh Nắng Lốm Đốm]. Có thể phát huy sức mạnh to lớn.',
    'A Runic Disc titled [Delivered by the Breeze]. It can unleash great power.': 'Một Đĩa nhạc Cổ ngữ mang tên [Cánh Thư Theo Gió]. Có thể phát huy sức mạnh to lớn.',
    'A Runic Disc titled [Fist of Courage]. It can unleash great power.': 'Một Đĩa nhạc Cổ ngữ mang tên [Nắm Đấm Dũng Cảm]. Có thể phát huy sức mạnh to lớn.',
    'A Runic Disc titled [Joyful Gathering]. It can unleash great power.': 'Một Đĩa nhạc Cổ ngữ mang tên [Thời Khắc Vui Tụ]. Có thể phát huy sức mạnh to lớn.',
    'A Runic Disc titled [Moment of Glory]. It can unleash great power.': 'Một Đĩa nhạc Cổ ngữ mang tên [Khoảnh Khắc Vinh Quang]. Có thể phát huy sức mạnh to lớn.',
    'A Runic Disc titled [One, Two, Three, Jump!]. It can unleash great power.': 'Một Đĩa nhạc Cổ ngữ mang tên [Một, Hai, Ba, Nhảy!]. Có thể phát huy sức mạnh to lớn.',
    'A Runic Disc titled [Phantom of the Banquet]. It can unleash great power.': 'Một Đĩa nhạc Cổ ngữ mang tên [Bóng Ma Yến Tiệc]. Có thể phát huy sức mạnh to lớn.',
    'A Runic Disc titled [Seed Alike]. It can unleash great power.': 'Một Đĩa nhạc Cổ ngữ mang tên [Ngươi Và Ta Tương Tự]. Có thể phát huy sức mạnh to lớn.',
    'A Runic Disc titled [Summer March]. It can unleash great power.': 'Một Đĩa nhạc Cổ ngữ mang tên [Hành Khúc Mùa Hè]. Có thể phát huy sức mạnh to lớn.',
    'A Runic Disc titled [Summer Sanctuary]. It can unleash great power.': 'Một Đĩa nhạc Cổ ngữ mang tên [Khu Bảo Tồn Mùa Hè]. Có thể phát huy sức mạnh to lớn.',
    'A Runic Disc titled [The Break of Frost]. It can unleash great power.': 'Một Đĩa nhạc Cổ ngữ mang tên [Bình Minh Sau Đêm Đông]. Có thể phát huy sức mạnh to lớn.',
    'A Runic Disc titled [The Bud of Change]. It can unleash great power.': 'Một Đĩa nhạc Cổ ngữ mang tên [Mầm Mống Cách Tân]. Có thể phát huy sức mạnh to lớn.',
    'A Runic Disc titled [Wine Warm, Lamps Alight]. It can unleash great power.': 'Một Đĩa nhạc Cổ ngữ mang tên [Rượu Ấm Đèn Hoa]. Có thể phát huy sức mạnh to lớn.',
    "A gift that increases a Trekker's Affinity by 500.": "Quà tặng giúp tăng 500 điểm Độ thân mật của Lữ khách.",
    'All That Was Beautiful Melody': 'Giai điệu Mọi Điều Từng Đẹp Đẽ',
    'An advanced material used for Discs tier-up.': 'Nguyên liệu cao cấp dùng để thăng giai Đĩa nhạc.',
    'An advanced material used for Trekker ability upgrades.': 'Nguyên liệu cao cấp dùng để nâng cấp năng lực Lữ khách.',
    'An advanced material used for Trekker tier-up.': 'Nguyên liệu cao cấp dùng để thăng giai Lữ khách.',
    'An intermediate material used for Discs tier-up.': 'Nguyên liệu trung cấp dùng để thăng giai Đĩa nhạc.',
    'An intermediate material used for Trekker tier-up.': 'Nguyên liệu trung cấp dùng để thăng giai Lữ khách.',
    'Material required for the Crescendo of the Disc: Dappled Sunlight.': 'Nguyên liệu cần thiết để Đột phá Đĩa nhạc: Ánh Nắng Lốm Đốm.',
    'Material required for the Crescendo of the Disc: Delivered by the Breeze.': 'Nguyên liệu cần thiết để Đột phá Đĩa nhạc: Cánh Thư Theo Gió.',
    'Material required for the Crescendo of the Disc: Joyful Gathering': 'Nguyên liệu cần thiết để Đột phá Đĩa nhạc: Thời Khắc Vui Tụ.',
    'Material required for the Crescendo of the Disc: Moment of Glory': 'Nguyên liệu cần thiết để Đột phá Đĩa nhạc: Khoảnh Khắc Vinh Quang.',
    'Material required for the Crescendo of the Disc: One, Two, Three, Jump!.': 'Nguyên liệu cần thiết để Đột phá Đĩa nhạc: Một, Hai, Ba, Nhảy!.',
    'Material required for the Crescendo of the Disc: Summer March.': 'Nguyên liệu cần thiết để Đột phá Đĩa nhạc: Hành Khúc Mùa Hè.',
    'Material required for the Crescendo of the Disc: Summer Sanctuary.': 'Nguyên liệu cần thiết để Đột phá Đĩa nhạc: Khu Bảo Tồn Mùa Hè.',
    'Material required for the Crescendo of the [A Gift for the Journey] Disc.': 'Nguyên liệu cần thiết để Đột phá Đĩa nhạc [Món Quà Cho Cuộc Hành Trình].',
    'Material required for the Crescendo of this Disc: "Touch of Miracle"': 'Nguyên liệu cần thiết để Đột phá Đĩa nhạc: "Chạm Vào Kỳ Tích".',
    'Material required for the Crescendo of this Disc: All That Was Beautiful.': 'Nguyên liệu cần thiết để Đột phá Đĩa nhạc: Mọi Điều Từng Đẹp Đẽ.',
    'Material required for the Crescendo of this Disc: Fist of Courage.': 'Nguyên liệu cần thiết để Đột phá Đĩa nhạc: Nắm Đấm Dũng Cảm.',
    'Material required for the Crescendo of this Disc: The Break of Frost.': 'Nguyên liệu cần thiết để Đột phá Đĩa nhạc: Bình Minh Sau Đêm Đông.',
    'Material required for the Crescendo of this Disc: The Bud of Change.': 'Nguyên liệu cần thiết để Đột phá Đĩa nhạc: Mầm Mống Cách Tân.',
    'Material required for the Crescendo of this Disc: Wine Warm, Lamps Alight.': 'Nguyên liệu cần thiết để Đột phá Đĩa nhạc: Rượu Ấm Đèn Hoa.',
    'Material required to Crescendo the Disc "Seed Alike"': 'Nguyên liệu cần thiết để Đột phá Đĩa nhạc "Ngươi Và Ta Tương Tự".',
    'Materials required to Crescendo the Disc "Phantom of the Banquet"': 'Nguyên liệu cần thiết để Đột phá Đĩa nhạc "Bóng Ma Yến Tiệc".',
    'Unlocks the Honor Title: Sunlit Breeze, Azure Seas: Checking In for A Cozy Summer~': 'Mở khóa Danh hiệu Danh dự: Gió Ấm Biển Xanh · Thảnh Thơi Check-in Mùa Hè Êm Đềm~',
    'Used for certain Trekker skill upgrade (Lv.7 to Lv.10).': 'Dùng để nâng cấp kỹ năng Lữ khách (Lv.7 đến Lv.10).',
    'Novice Trekker Promotion Box': 'Hộp Quà Thăng Cấp Lữ Khách Tân Thủ',
    'Novice Disc Promotion Box': 'Hộp Quà Thăng Cấp Đĩa Nhạc Tân Thủ',
    'Beginner Cartridge Box': 'Hộp Quà Thẻ Băng Tân Thủ',
    'Grants one basic Trekker promotion material from Tier-up Trial of your choice.': 'Tự chọn nhận một nguyên liệu thăng cấp Lữ khách cơ bản từ Thử Nghiệm Thăng Giai.',
    'Grants one basic Disc material from Tier-up Trial of your choice.': 'Tự chọn nhận một nguyên liệu thăng cấp Đĩa nhạc cơ bản từ Thử Nghiệm Thăng Giai.',
    'Grants a Basic Game Cartridge of your choice.': 'Tự chọn nhận một Thẻ Băng Trò Chơi cơ bản.',
    'Special material for locking Affixes during Trekker Emblems resets.': 'Nguyên liệu đặc biệt dùng để khóa Dòng thuộc tính khi đúc lại Huy hiệu Lữ khách.',
    'An advanced material used for Trekker skill upgrades.': 'Nguyên liệu cao cấp dùng để nâng cấp kỹ năng Lữ khách.',
    'An intermediate material used for Trekker skill upgrades.': 'Nguyên liệu trung cấp dùng để nâng cấp kỹ năng Lữ khách.',
    'A generic material used for Trekker skill upgrades.': 'Nguyên liệu phổ thông dùng để nâng cấp kỹ năng Lữ khách.',
    'Grants tons of EXP for leveling up Trekkers.': 'Cung cấp lượng lớn EXP để tăng cấp Lữ khách.',
    'Grants tons of EXP for upgrading Discs.': 'Cung cấp lượng lớn EXP để nâng cấp Đĩa nhạc.',
    'Grants a large amount of EXP for upgrading Discs.': 'Cung cấp nhiều EXP để nâng cấp Đĩa nhạc.',
}

# 3. Exact mappings for MallPackage themes & bundle types
MALL_THEMES = {
    'A Breezy Romance': 'Gió Nhẹ Lãng Mạn',
    'Afternoon Tea': 'Tiệc Trà Chiều',
    'Awakening Universe': 'Vạn Tượng Khởi Nguyên',
    "Blade's Glimmer": 'Ánh Đao Lấp Lánh',
    'Departure': 'Khởi Hành Giới Hạn',
    'Departure Limited': 'Khởi Hành Giới Hạn',
    'Ebon Grimoire': 'Ma Điển Hắc Ám',
    "Emerald's Brilliance": 'Bích Ngọc Lung Linh',
    'Fanta-sea Reverie': 'Biển Biếc Ảo Mộng',
    'Fortune': 'Khai Trương Đại Cát',
    'Fortune Begins': 'Khai Trương Đại Cát',
    'Gleaming Summer': 'Mộng Hè Lấp Lánh',
    'Icy Embrace': 'Hàn Phong Băng Giá',
    'Ingenious Artisan': 'Hòm Thợ Khéo Léo',
    'Lunar Fragrance': 'Hương Nguyệt Rơi Rụng',
    'New Blossom': 'Mầm Non Nở Rộ',
    'Raging Tides': 'Sóng Lớn Cuộn Trào',
    'Seasong Voyage': 'Biển Mây Hành Ca',
    'Seasong Voyage:': 'Biển Mây Hành Ca',
    'Shimmering Snow': 'Tuyết Nguyện Lấp Lánh',
    'Splendid Spring': 'Gấm Vóc Đón Xuân',
    'Starlight Guardian': 'Hộ Vệ Tinh Khôi',
    'Stellar Grace': 'Tắm Sao Nhã Nhặn',
    'Stellar Offer': 'Lời Mời Dưới Sao',
    'Stellar Tribute': 'Cống Phẩm Ánh Sao',
    'Stellar Tribute ': 'Cống Phẩm Ánh Sao',
    'Swift Arrival': 'Sứ Mệnh Tất Đạt',
    'Weekly': 'Ưu Đãi Hàng Tuần',
    'Weekly Special': 'Ưu Đãi Hàng Tuần',
    'Wishing': 'Ưu Đãi Cầu Nguyện',
    'Wishing Special': 'Ưu Đãi Cầu Nguyện',
}

MALL_BUNDLES = {
    'Boost Deal Bundle': 'Gói Bồi Dưỡng Tinh Thể Siêu Trị',
    'Cerulean Ticket Ascent Set': 'Gói Vé Cerulean Leo Sao',
    'Cerulean Ticket Set': 'Gói Vé Cerulean',
    'Deluxe Boost Bundle': 'Gói Bồi Dưỡng Tinh Thể Xa Hoa',
    'Deluxe Disc Set': 'Gói Đĩa Nhạc Xa Hoa',
    'Deluxe Ticket Set': 'Gói Vé Xa Hoa',
    'Disc Choice Bundle': 'Gói Tự Chọn Đĩa Nhạc',
    'Disc Tuning Bundle': 'Gói Điều Âm Đĩa Nhạc',
    'Disc Value Set': 'Gói Đĩa Nhạc Siêu Trị',
    'Fortune Favor': 'Quà May Mắn',
    'Gold Disc Ascent Set': 'Gói Đĩa Vàng Leo Sao',
    'Gold Disc Set': 'Gói Đĩa Vàng',
    'Heartfelt Bundle': 'Gói Quà Tận Tâm',
    'Lumina Emblem Bundle': 'Gói Huy Hiệu Tinh Thể',
    'Skill Enhancement Bundle': 'Gói Cường Hóa Kỹ Năng',
    'Special Boost Bundle': 'Gói Bồi Dưỡng Tinh Thể Đặc Biệt',
    'Special Disc Set': 'Gói Đĩa Nhạc Đặc Biệt',
    'Sprout Ticket Set': 'Gói Vé Mầm',
    'Ticket Deal Set': 'Gói Vé Ưu Đãi',
    'Ticket Value Set': 'Gói Vé Siêu Trị',
    'Trekker Boost Bundle': 'Gói Bồi Dưỡng Lữ Khách',
    'Trekker Boost Pack': 'Gói Bồi Dưỡng Lữ Khách',
    'Trekker Choice Bundle': 'Gói Tự Chọn Lữ Khách',
    'Welcome Pack': 'Gói Quà Chào Mừng',
}

MALL_EXACT = {
    'Lv. 5 Trekker Boost Set': 'Gói Bồi Dưỡng Lữ Khách Lv.5',
    'Lv. 10 Trekker Boost Set': 'Gói Bồi Dưỡng Lữ Khách Lv.10',
    'Lv. 15 Trekker Boost Set': 'Gói Bồi Dưỡng Lữ Khách Lv.15',
    'Lv. 20 Power Boost Set': 'Gói Tăng Cường Lực Chiến Lv.20',
    'Lv. 25 Power Boost Set': 'Gói Tăng Cường Lực Chiến Lv.25',
    'Lv. 30 Power Boost Set': 'Gói Tăng Cường Lực Chiến Lv.30',
    'Gold Disc Set': 'Gói Đĩa Vàng',
    'Heartfelt Bundle': 'Gói Quà Tận Tâm',
    'Trekker Boost Bundle': 'Gói Bồi Dưỡng Lữ Khách',
    'Cerulean Ticket Set': 'Gói Vé Cerulean',
    'Deluxe Disc Set': 'Gói Đĩa Nhạc Xa Hoa',
    'Deluxe Ticket Set': 'Gói Vé Xa Hoa',
    'Cerulean Ticket Ascent Set': 'Gói Vé Cerulean Leo Sao',
    'Disc Choice Bundle': 'Gói Tự Chọn Đĩa Nhạc',
    'Lumina Emblem Bundle': 'Gói Huy Hiệu Tinh Thể',
    'Trekker Choice Bundle': 'Gói Tự Chọn Lữ Khách',
    'Lingering Sunlight': 'Hơi Ấm Nắng Chiều',
    'When Distant Winds Rise': 'Khi Gió Phương Xa Nổi Lên',
    'The Gift of Falling Snow': 'Món Quà Tuyết Rơi',
    'Probation Period Cleared!': 'Vượt Qua Giai Đoạn Thử Việc!',
    'Cocoa Night Sweetheart': 'Người Tình Đêm Ca Cao',
    'Promise Beyond the Thaw': 'Hẹn Ước Sau Mùa Tuyết Tan',
    'A Dip of Fresh Summer': 'Giọt Sương Đầu Hạ',
    'When Morning Glories Bloom, Her Eyes Open': 'Hoa Triêu Nhan Nở, Thiếu Nữ Bừng Tỉnh',
    'Quirky Tea Party': 'Tiệc Trà Kỳ Quái',
    'Rippling Void of the Darkest Heartbreak': 'Bóng Gương Gợn Sóng: Vết Thương Lòng Đen Tối',
    'Ease Into an Unhurried Summer': 'Mùa Hè Thư Thái',
    'Crimson Reflection of Queen of Hearts': 'Hình Bóng Đỏ Thẫm Của Nữ Hoàng Cơ',
    'Drifting Together on Gentle Waves': 'Cùng Trôi Dạt Trên Làn Sóng Êm Đềm',
    'Carefree in the Golden Glow': 'Thong Dong Dưới Ánh Hoàng Hôn',
    'Shining Bright, Spirits High': 'Tỏa Sáng Rực Rỡ, Tinh Thần Phấn Chấn',
    'My Stage, My Creation': 'Sân Khấu Của Tôi, Sáng Tạo Của Tôi',
}

# 4. Exact mappings for PenguinCard base cards & descriptions
PENGUIN_BASE_CARDS = {
    '!PENDING!': '!PENDING!',
    'Against Elite': 'Đối Địch Tinh Anh',
    'Air Current': 'Luồng Khí',
    'Chase the Shadows': 'Truy Phong Tróc Ảnh',
    'Classic Move': 'Chiêu Cũ Tái Hiện',
    'Cloud Elite': 'Tân Quý Mây Trắng',
    'Crowning Moment': 'Khoảnh Khắc Đăng Quang',
    'Deep-Sea Mogul': 'Tài Phiệt Biển Sâu',
    'Destined Pair': 'Song Tinh Định Mệnh',
    'Destiny Catcher': 'Kẻ Bắt Lấy Định Mệnh',
    'Ember Reborn': 'Hỏa Chủng Tái Sinh',
    'Fan the Flames': 'Thêm Dầu Vào Lửa',
    'Fated Favor': 'Tinh Mệnh Chiếu Rọi',
    'Flame Tycoon': 'Tài Phiệt Ngọn Lửa',
    'Focus Energy': 'Tụ Khí',
    'Fountain Resurgence': 'Suối Nguồn Tái Khởi',
    'Four As One': 'Tứ Tượng Quy Nhất',
    'Gathering Dew': 'Ngưng Tụ Sương Sớm',
    'Golden Hoard': 'Tọa Ủng Kim Sơn',
    'Grand Measure': 'Thước Đo Thiên Hạ',
    'Heat Stack': 'Tích Tụ Nhiệt Lượng',
    'Hell Lord': 'Chúa Tể Địa Ngục',
    'Inevitable Abyss': 'Vực Sâu Tương Phùng',
    'Inevitable Flame': 'Hỏa Diễm Tương Lai',
    'Inevitable Source': 'Cội Nguồn Truy Vết',
    'Inevitable Wind': 'Ngọn Gió Định Hướng',
    'Raging Waves': 'Từng Lớp Sóng Dữ',
    'Reignited Ember': 'Tàn Tro Bùng Cháy',
    'Residual Gains': 'Lợi Nhuận Tái Sinh',
    'Returning Breeze': 'Gió Thoảng Tái Khởi',
    'Ripple': 'Gợn Sóng Lăn Tăn',
    'Rising Blaze': 'Hỏa Thế Dâng Cao',
    'Rising Winds': 'Gió Cuộn Rừng Xanh',
    'Roaming Gale': 'Trường Phong Tuần Hành',
    'Rushing Tide': 'Thủy Triều Cuồn Cuộn',
    'Seaside Celebrity': 'Danh Lưu Vùng Biển',
    'Shared Toast': 'Cạn Ly Chung Vui',
    'Stacking Heatwave': 'Sóng Nhiệt Chồng Chất',
    'Starfire': 'Ánh Sao Lấp Lánh',
    'Stir the Waters': 'Thúc Đẩy Làn Sóng',
    'Storm Oligarch': 'Độc Quyền Bão Tố',
    'Turbulent Current': 'Luồng Khí Cuộn Trào',
    'Verdant Spring': 'Suối Trong Nuôi Rừng',
}

PENGUIN_DESCS = {
    'Upgrades cost 20% less <sprite name="icon_pengbuildcard_coin">.': 'Nâng cấp tiêu hao giảm 20% <sprite name="icon_pengbuildcard_coin">.',
    'Upgrades cost 30% less <sprite name="icon_pengbuildcard_coin">.': 'Nâng cấp tiêu hao giảm 30% <sprite name="icon_pengbuildcard_coin">.',
    'Upgrades cost 40% less <sprite name="icon_pengbuildcard_coin">.': 'Nâng cấp tiêu hao giảm 40% <sprite name="icon_pengbuildcard_coin">.',
    'Lowers clear requirements by 20%.': 'Mục tiêu qua màn giảm 20%.',
    'Lowers clear requirements by 25%.': 'Mục tiêu qua màn giảm 25%.',
    'Lowers clear requirements by 30%.': 'Mục tiêu qua màn giảm 30%.',
    'Gain 1 Card Peek per turn': 'Mỗi hiệp nhận 1 lượt xem trước bài',
    'Gain 2 Card Peeks per turn': 'Mỗi hiệp nhận 2 lượt xem trước bài',
    'Gain 3 Card Peeks per turn': 'Mỗi hiệp nhận 3 lượt xem trước bài',
    'When flipping cards, there is a 20% chance to draw a [Wild Card] that counts as any element, up to {TriggerLimitParam} times.': 'Khi lật bài, có 20% xác suất xuất hiện [Lá Bài Vạn Năng] được coi là nguyên tố bất kỳ, tối đa {TriggerLimitParam} lần.',
    'Recover 1 Stamina when starting a new difficulty.': 'Khi bắt đầu độ khó mới, hồi phục 1 Thể lực.',
    'When starting a new difficulty, increases the level of 1 random Fatebound Stellar Card by 1.': 'Khi bắt đầu độ khó mới, tăng 1 cấp cho 1 Thẻ Tinh Mệnh ngẫu nhiên.',
    'When starting a new difficulty, increases the level of 2 random Fatebound Stellar Cards by 1.': 'Khi bắt đầu độ khó mới, tăng 1 cấp cho 2 Thẻ Tinh Mệnh ngẫu nhiên.',
    'Each revealed {GrowthTriggerParam_1} this turn grants <color=#ec6b2a>+ {GrowthEffectParam_1}</color> Multiplier when scored.\x0b(Current: <color=#ec6b2a>+ {TotalEffectParam_1}</color> Multiplier)': 'Khi tính điểm, mỗi {GrowthTriggerParam_1} đã lật trong hiệp này tăng <color=#ec6b2a>+{GrowthEffectParam_1}</color> Bội số.\x0b(Hiện tại: <color=#ec6b2a>+{TotalEffectParam_1}</color> Bội số)',
    '<color=#ec6b2a>{TriggerProbability}%</color> chance to tier up {TriggerParam_1} to {EffectParam_1}, up to <color=#ec6b2a>{TriggerLimitParam}</color> times per turn.': '<color=#ec6b2a>{TriggerProbability}%</color> xác suất thăng giai {TriggerParam_1} thành {EffectParam_1}, mỗi hiệp giới hạn <color=#ec6b2a>{TriggerLimitParam}</color> lần.',
    'Gain <color=#ec6b2a>+ {TotalEffectParam_1}</color> Chips when scored. Decreases by <color=#ec6b2a>{GrowthEffectParam_1}</color> each turn.': 'Khi tính điểm, nhận <color=#ec6b2a>+{TotalEffectParam_1}</color> Chip, mỗi hiệp giảm <color=#ec6b2a>{GrowthEffectParam_1}</color>.',
    'Gain <color=#ec6b2a>+ {TotalEffectParam_1}</color> Multiplier when scored. Decreases by <color=#ec6b2a>{GrowthEffectParam_1}</color> each turn.': 'Khi tính điểm, nhận <color=#ec6b2a>+{TotalEffectParam_1}</color> Bội số, mỗi hiệp giảm <color=#ec6b2a>{GrowthEffectParam_1}</color>.',
    'On the first upgrade each turn, refund <color=#ec6b2a>{EffectParam_1}%</color> of Chips spent.': 'Ở lần nâng cấp đầu tiên mỗi hiệp, hoàn trả <color=#ec6b2a>{EffectParam_1}%</color> Chip đã tiêu hao.',
    'Gain Chips equal to: Total level of owned Destiny Cards × <color=#ec6b2a>{GrowthEffectParam_1}</color> Chips when scored.\x0b (Current: <color=#ec6b2a> + {TotalEffectParam_1}</color> Chips)': 'Khi tính điểm, nhận số Chip bằng: Tổng cấp Thẻ Tinh Mệnh sở hữu × <color=#ec6b2a>{GrowthEffectParam_1}</color> Chip.\x0b (Hiện tại: <color=#ec6b2a> + {TotalEffectParam_1}</color> Chip)',
    'Gain Chips equal to: Total level of owned Destiny Cards × <color=#ec6b2a>{GrowthEffectParam_1}</color> Chips when scored.\x0b(Current: <color=#ec6b2a>+ {TotalEffectParam_1}</color> Chips)': 'Khi tính điểm, nhận số Chip bằng: Tổng cấp Thẻ Tinh Mệnh sở hữu × <color=#ec6b2a>{GrowthEffectParam_1}</color> Chip.\x0b(Hiện tại: <color=#ec6b2a>+ {TotalEffectParam_1}</color> Chip)',
    'Gain Chips equal to: Total level of owned Destiny Cards × <color=#ec6b2a>{GrowthEffectParam_1}</color> Chipswhen scored.\x0b(Current: <color=#ec6b2a>+ {TotalEffectParam_1}</color> Chips)': 'Khi tính điểm, nhận số Chip bằng: Tổng cấp Thẻ Tinh Mệnh sở hữu × <color=#ec6b2a>{GrowthEffectParam_1}</color> Chip.\x0b(Hiện tại: <color=#ec6b2a>+ {TotalEffectParam_1}</color> Chip)',
    'If the hand contains <color=#ec6b2a>{TriggerParam_1}</color> when scored, Multiplier becomes <color=#ec6b2a> × {EffectParam_1}</color>.': 'Khi tính điểm, nếu tay bài có chứa <color=#ec6b2a>{TriggerParam_1}</color>, Bội số trở thành <color=#ec6b2a> × {EffectParam_1}</color>.',
    'If the same hand type has appeared this turn when scored, Multiplier becomes <color=#ec6b2a> × {EffectParam_1}</color>.': 'Khi tính điểm, nếu loại tay bài tương tự đã xuất hiện trong hiệp này, Bội số trở thành <color=#ec6b2a> × {EffectParam_1}</color>.',
    'If {TriggerParam_1} exists when scored, <color=#ec6b2a>+{EffectParam_1}</color> chips.': 'Khi tính điểm nếu có {TriggerParam_1}, <color=#ec6b2a>+{EffectParam_1}</color> Chip.',
    'If {TriggerParam_1} exists when scored, multiplier <color=#ec6b2a>+{EffectParam_1}</color>.': 'Khi tính điểm nếu có {TriggerParam_1}, Bội số <color=#ec6b2a>+{EffectParam_1}</color>.',
    'If {TriggerParam_1} exists when scored, multiplier <color=#ec6b2a>×{EffectParam_1}</color>.': 'Khi tính điểm nếu có {TriggerParam_1}, Bội số <color=#ec6b2a>×{EffectParam_1}</color>.',
    'If {TriggerParam_1}{TriggerParam_2}{TriggerParam_3} is present when scored, gain <color=#ec6b2a> + {EffectParam_1}</color> Multiplier.': 'Khi tính điểm nếu có {TriggerParam_1}{TriggerParam_2}{TriggerParam_3}, nhận <color=#ec6b2a> + {EffectParam_1}</color> Bội số.',
    'Increases the chance of triggering {EffectParam_1}.': 'Tăng xác suất xuất hiện của {EffectParam_1}.',
    'Multiplier <color=#ec6b2a>+{EffectParam_1}</color> when scored.': 'Khi tính điểm, Bội số <color=#ec6b2a>+{EffectParam_1}</color>.',
    'Up to <color=#ec6b2a>{TriggerLimitParam}</color> times per turn. Manual refreshes will guarantee one of the following: <color=#ec6b2a>[{EffectParam_1}], [{EffectParam_2}], [{EffectParam_3}], [{EffectParam_4}], or [{EffectParam_5}]</color>.': 'Mỗi hiệp giới hạn <color=#ec6b2a>{TriggerLimitParam}</color> lần. Làm mới thủ công chắc chắn xuất hiện một trong các mục sau: <color=#ec6b2a>[{EffectParam_1}], [{EffectParam_2}], [{EffectParam_3}], [{EffectParam_4}] hoặc [{EffectParam_5}]</color>.',
    'Up to <color=#ec6b2a>{TriggerLimitParam}</color> times per turn. Manual refreshes will guarantee one of the following: <color=#ec6b2a>[{EffectParam_1}], [{EffectParam_2}], or [{EffectParam_3}]</color>.': 'Mỗi hiệp giới hạn <color=#ec6b2a>{TriggerLimitParam}</color> lần. Làm mới thủ công chắc chắn xuất hiện một trong các mục sau: <color=#ec6b2a>[{EffectParam_1}], [{EffectParam_2}] hoặc [{EffectParam_3}]</color>.',
    'Whenever you flip a card with {TriggerParam_1}, <color=#ec6b2a>+{EffectParam_1}</color> chips.': 'Mỗi khi lật một lá bài có {TriggerParam_1}, <color=#ec6b2a>+{EffectParam_1}</color> Chip.',
    'Whenever you flip a card with {TriggerParam_1}, multiplier <color=#ec6b2a>+{EffectParam_1}</color>.': 'Mỗi khi lật một lá bài có {TriggerParam_1}, Bội số <color=#ec6b2a>+{EffectParam_1}</color>.',
    'Gain <color=#ec6b2a>+ {TotalEffectParam_1}</color> Chips when scored. Each time a hand containing <color=#ec6b2a>{GrowthTriggerParam_1}</color> is played, increases this effect by <color=#ec6b2a>+ {GrowthEffectParam_1}</color> Chips.': 'Khi tính điểm, nhận <color=#ec6b2a>+{TotalEffectParam_1}</color> Chip. Mỗi khi đánh ra tay bài chứa <color=#ec6b2a>{GrowthTriggerParam_1}</color>, hiệu quả này tăng <color=#ec6b2a>+{GrowthEffectParam_1}</color> Chip.',
    'Gain <color=#ec6b2a>+ {TotalEffectParam_1}</color> Multiplier when scored. Each time a hand containing <color=#ec6b2a>{GrowthTriggerParam_1} is played, increases this effect by </color>+ <color=#ec6b2a>{GrowthEffectParam_1}</color> Multiplier.': 'Khi tính điểm, nhận <color=#ec6b2a>+{TotalEffectParam_1}</color> Bội số. Mỗi khi đánh ra tay bài chứa <color=#ec6b2a>{GrowthTriggerParam_1} hiệu quả này tăng </color>+ <color=#ec6b2a>{GrowthEffectParam_1}</color> Bội số.',
    'Each revealed {GrowthTriggerParam_1} this turn grants <color=#ec6b2a>+ {GrowthEffectParam_1}</color> Chips when scored.\x0b(Current: <color=#ec6b2a>+ {TotalEffectParam_1}</color> Chips)': 'Khi tính điểm, mỗi {GrowthTriggerParam_1} đã lật trong hiệp này tăng <color=#ec6b2a>+{GrowthEffectParam_1}</color> Chip.\x0b(Hiện tại: <color=#ec6b2a>+{TotalEffectParam_1}</color> Chip)',
    '<color=#ec6b2a>+{EffectParam_1}</color> chips when scored.': 'Khi tính điểm, <color=#ec6b2a>+{EffectParam_1}</color> Chip.',
}

def shield_tokens(text: str):
    """Shield formatting tags and control chars so translation doesn't alter them."""
    tokens = []
    def repl(m):
        idx = len(tokens)
        tokens.append(m.group(0))
        return f" [[TOK{idx}]] "
    pattern = re.compile(r'(\x0b|\n|<[^>]+>|\{[0-9a-zA-Z_]+\}|&[a-zA-Z0-9_]+&|##[^#]+#)')
    shielded = pattern.sub(repl, text)
    return shielded, tokens

def unshield_tokens(text: str, tokens: list):
    """Restore shielded tokens cleanly."""
    def repl(m):
        idx = int(m.group(1))
        if idx >= len(tokens):
            return ""
        tok = tokens[idx]
        if tok in ('\x0b', '\n'):
            return tok
        return f" {tok} "

    res = re.sub(r'\s*\[\[\s*TOK(\d+)\s*\]\]\s*', repl, text, flags=re.IGNORECASE)
    # Clean spacing around color tags
    res = re.sub(r'(<color=[^>]+>)\s+', r'\1', res)
    res = re.sub(r'\s+(</color>)', r'\1', res)
    # Clean spacing around &Param...&
    res = re.sub(r' +(&[a-zA-Z0-9_]+&) +', r' \1 ', res)
    # Clean whitespace around \x0b and \n
    res = re.sub(r'[ \t]*\x0b[ \t]*', '\x0b', res)
    res = re.sub(r'[ \t]*\n[ \t]*', '\n', res)
    # Clean double spaces
    res = re.sub(r'[ \t]{2,}', ' ', res)
    return res.strip()

def post_process_vi(text: str) -> str:
    """Standardize RPG terminology and style according to project guidelines."""
    # Key game nouns
    text = re.sub(r'\bDora\b', 'Dorra', text)
    text = re.sub(r'\bTrekkers?\b', 'Lữ khách', text)
    text = re.sub(r'\b[Nn]hững người đi bộ\b', 'các Lữ khách', text)
    text = re.sub(r'\b[Nn]gười đi bộ\b', 'Lữ khách', text)
    text = re.sub(r'\b[Nn]hững người đi phượt\b', 'các Lữ khách', text)
    text = re.sub(r'\b[Nn]gười đi phượt\b', 'Lữ khách', text)
    text = re.sub(r'\b[Nn]gười phượt\b', 'Lữ khách', text)
    text = re.sub(r'\b[Nn]gười du hành\b', 'Lữ khách', text)
    text = re.sub(r'\bMonolith\b', 'Cự tháp', text)
    text = re.sub(r'\b[Đđ]á nguyên khối\b', 'Cự tháp', text)
    text = re.sub(r'\bNovians\b', 'người Nova', text)
    text = re.sub(r'\bNova Continent\b', 'Lục địa Nova', text)
    text = re.sub(r'\bthe Wilds\b', 'Vùng hoang dã', text)
    text = re.sub(r'\bWilds\b', 'Vùng hoang dã', text)
    text = re.sub(r'\bDiscs?\b', 'Đĩa nhạc', text)
    text = re.sub(r'\bEmblems?\b', 'Huy hiệu', text)
    text = re.sub(r'\bVigor\b', 'Năng lượng', text)
    text = re.sub(r'\bDiamonds?\b', 'Kim Cương', text)
    text = re.sub(r'\bDestiny Cards?\b', 'Thẻ Tinh Mệnh', text)
    text = re.sub(r'\bFatebound Stellar Cards?\b', 'Thẻ Tinh Mệnh', text)
    text = re.sub(r'\bMonthly Card\b', 'Thẻ Tháng', text)

    # Combat & Stats
    text = re.sub(r'\bSuperarmor\b', 'Bá thể', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSuper Armor\b', 'Bá thể', text, flags=re.IGNORECASE)
    text = re.sub(r'\bsiêu giáp\b', 'Bá thể', text, flags=re.IGNORECASE)
    text = re.sub(r'\bResilience Break\b', 'Phá vỡ Kiên định', text, flags=re.IGNORECASE)
    text = re.sub(r'\bResilience\b', 'Kiên định', text, flags=re.IGNORECASE)
    text = re.sub(r'\bkhả năng phục hồi\b', 'Kiên định', text, flags=re.IGNORECASE)
    text = re.sub(r'\bAffinity\b', 'Độ thân mật', text, flags=re.IGNORECASE)
    text = re.sub(r'\bái lực\b', 'Độ thân mật', text, flags=re.IGNORECASE)
    text = re.sub(r'\bmối quan hệ họ hàng\b', 'Độ thân mật', text, flags=re.IGNORECASE)

    # Clean whitespace before punctuation
    text = re.sub(r' +([,.:;?!])', r'\1', text)
    return text.strip()

def translate_batch(texts: list, session: requests.Session) -> list:
    """Translate a batch of shielded texts using Google Translate API with auto split/retry."""
    if not texts:
        return []

    delim = "\n###\n"
    joined = delim.join(texts)

    for attempt in range(3):
        try:
            r = session.get(
                "https://translate.googleapis.com/translate_a/single",
                params={
                    "client": "gtx",
                    "sl": "en",
                    "tl": "vi",
                    "dt": "t",
                    "q": joined,
                },
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20,
            )
            if r.status_code == 200:
                res = r.json()
                full_text = "".join([item[0] for item in res[0] if item[0]])
                parts = [p.strip() for p in full_text.split("###")]
                if len(parts) == len(texts):
                    return parts
                else:
                    if len(texts) > 1:
                        mid = len(texts) // 2
                        return translate_batch(texts[:mid], session) + translate_batch(texts[mid:], session)
                    else:
                        return [full_text.strip()]
            time.sleep(1.0 * (attempt + 1))
        except Exception:
            time.sleep(1.0 * (attempt + 1))

    # Fallback 1 by 1
    results = []
    for t in texts:
        try:
            r = session.get(
                "https://translate.googleapis.com/translate_a/single",
                params={"client": "gtx", "sl": "en", "tl": "vi", "dt": "t", "q": t},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )
            if r.status_code == 200:
                res = r.json()
                full = "".join([item[0] for item in res[0] if item[0]])
                results.append(full.strip())
            else:
                results.append(t)
        except Exception:
            results.append(t)
        time.sleep(0.1)
    return results

def resolve_translation(table_name: str, key: str, en_text: str, cache: dict, item_cache: dict) -> str:
    """Determine translation using exact rules, caches, or return None if needs batch translation."""
    if en_text in ("!NONEED!", "!PENDING!"):
        return en_text

    # 1. AffinityUpReward
    if table_name == "AffinityUpReward":
        if en_text in AFFINITY_UP_REWARD_MAP:
            return AFFINITY_UP_REWARD_MAP[en_text]

    # 2. ActivityGoods
    if table_name == "ActivityGoods":
        if en_text in ACTIVITY_GOODS_EXACT:
            return ACTIVITY_GOODS_EXACT[en_text]
        if en_text in item_cache:
            return item_cache[en_text]

    # 3. MallPackage
    if table_name == "MallPackage":
        if en_text in MALL_EXACT:
            return MALL_EXACT[en_text]
        if en_text in item_cache:
            return item_cache[en_text]

        # Handle Theme\x0bBundle or Theme: Bundle
        for sep, joiner in [(chr(11), chr(11)), (': ', ': ')]:
            if sep in en_text:
                parts = en_text.split(sep, 1)
                theme = parts[0].strip()
                bundle = parts[1].strip()
                vi_theme = MALL_THEMES.get(theme)
                vi_bundle = MALL_BUNDLES.get(bundle)
                if vi_theme and vi_bundle:
                    return f"{vi_theme}{joiner}{vi_bundle}"

        # Handle Certificate that unlocks [Character]'s exclusive appearance "[Costume]"!
        m_cert = re.match(r'Certificate that unlocks (.+?)\'s exclusive appearance ("[^"]+"|\:[^!]+)(.*)', en_text)
        if m_cert:
            char_name = m_cert.group(1).strip()
            costume_name = m_cert.group(2).strip()
            rest = m_cert.group(3).strip()
            # If costume has translation in MALL_EXACT
            clean_costume = costume_name.strip('": ')
            vi_costume = MALL_EXACT.get(clean_costume, clean_costume)
            if costume_name.startswith(':'):
                return f"Chứng chỉ mở khóa ngoại hình độc quyền của {char_name}: {vi_costume}{rest}"
            else:
                return f'Chứng chỉ mở khóa ngoại hình độc quyền của {char_name} "{vi_costume}"{rest}'

    # 4. PenguinCard
    if table_name == "PenguinCard":
        if en_text in PENGUIN_DESCS:
            return PENGUIN_DESCS[en_text]
        # Check base cards with possible +1, +2, +3, +4
        m_card = re.match(r'^(.*?)(\s*\+\d+)?$', en_text)
        if m_card:
            base = m_card.group(1).strip()
            lvl = m_card.group(2) or ""
            if base in PENGUIN_BASE_CARDS:
                if base == "!PENDING!":
                    return "!PENDING!"
                return f"{PENGUIN_BASE_CARDS[base]}{lvl}"

    # Check caches
    if key in cache:
        return cache[key]
    if en_text in cache:
        return cache[en_text]

    return None

def main():
    print("=" * 70)
    print("Stella Sora - Subagent 4C: Rewards, Shop & Card Tables Translator")
    print("=" * 70)

    # 1. Load or initialize cache
    cache = {}
    if CACHE_PATH.exists():
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                cache = json.load(f)
            print(f"Loaded {len(cache)} existing cached translations from {CACHE_PATH.name}")
        except Exception as e:
            print(f"Warning loading cache: {e}")

    item_cache = {}
    if ITEM_CACHE_PATH.exists():
        try:
            with open(ITEM_CACHE_PATH, "r", encoding="utf-8") as f:
                item_cache = json.load(f)
            print(f"Loaded {len(item_cache)} item translations from {ITEM_CACHE_PATH.name}")
        except Exception as e:
            print(f"Warning loading item cache: {e}")

    # 2. Back up original files
    for t in TABLES:
        en_path = ENTRIES_DIR / t["en_file"]
        bak_path = en_path.with_suffix(".bin.bak")
        if not bak_path.exists():
            shutil.copy2(en_path, bak_path)
            print(f"Created backup: {bak_path.name}")
        else:
            print(f"Backup already exists: {bak_path.name}")

    session = requests.Session()

    # Process all tables
    translated_tables = {}
    total_items = 0

    for t in TABLES:
        name = t["name"]
        en_file = t["en_file"]
        cn_file = t["cn_file"]
        en_path = ENTRIES_DIR / en_file
        cn_path = ENTRIES_DIR / cn_file

        source_en_path = en_path.with_suffix(".bin.bak") if en_path.with_suffix(".bin.bak").exists() else en_path
        with open(source_en_path, "r", encoding="utf-8") as f:
            en_data = json.load(f)
        with open(cn_path, "r", encoding="utf-8") as f:
            cn_data = json.load(f)

        print(f"\nProcessing {name} ({len(en_data)} items)...")
        total_items += len(en_data)

        vi_data = {}
        to_translate_keys = []
        to_translate_texts = []
        tokens_map = {}

        for k, en_text in en_data.items():
            res = resolve_translation(name, k, en_text, cache, item_cache)
            if res is not None:
                vi_data[k] = res
                cache[k] = res
                cache[en_text] = res
                continue

            # Needs translation
            shielded, tokens = shield_tokens(en_text)
            tokens_map[k] = tokens
            to_translate_keys.append(k)
            to_translate_texts.append(shielded)

        print(f"  Exact / cached: {len(vi_data)}, Needs API translation: {len(to_translate_keys)}")

        # Batch translation if any
        if to_translate_keys:
            batch_size = 20
            for i in range(0, len(to_translate_keys), batch_size):
                batch_keys = to_translate_keys[i:i + batch_size]
                batch_texts = to_translate_texts[i:i + batch_size]

                translated_parts = translate_batch(batch_texts, session)

                for key, trans in zip(batch_keys, translated_parts):
                    toks = tokens_map[key]
                    unshielded = unshield_tokens(trans, toks)
                    polished = post_process_vi(unshielded)
                    vi_data[key] = polished
                    cache[key] = polished
                    cache[en_data[key]] = polished

                print(f"  Translated batch {i//batch_size + 1} / {(len(to_translate_keys) + batch_size - 1)//batch_size} ({len(batch_keys)} items)")
                time.sleep(0.3)

        # Save cache incrementally
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

        translated_tables[name] = (en_path, vi_data, en_data)

    # 3. Verification Gate: Exact Token & Placeholder Check
    print("\n" + "=" * 70)
    print("VERIFICATION GATE: Exact Token & Placeholder Check")
    print("=" * 70)

    tok_re = re.compile(r'(\{[0-9a-zA-Z_]+\}|<[^>]+>|\x0b|\n|&[a-zA-Z0-9_]+&|##[^#]+#)')
    has_error = False

    for name, (en_path, vi_data, en_data) in translated_tables.items():
        table_errors = 0
        for k in en_data:
            orig = en_data[k]
            trans = vi_data.get(k, "")

            if not trans:
                table_errors += 1
                has_error = True
                print(f"ERROR: Empty translation in {name} [{k}]")
                continue

            orig_tokens = tok_re.findall(orig)
            trans_tokens = tok_re.findall(trans)

            if orig_tokens != trans_tokens:
                if sorted(orig_tokens) != sorted(trans_tokens):
                    table_errors += 1
                    has_error = True
                    print(f"ERROR in {name} [{k}]:")
                    print(f"  EN: {repr(orig)}")
                    print(f"  VI: {repr(trans)}")
                    print(f"  Expected tokens: {orig_tokens}")
                    print(f"  Found tokens:    {trans_tokens}")

        if table_errors == 0:
            print(f"[{name}] ALL {len(en_data)} entries passed token validation 100%!")
        else:
            print(f"[{name}] FAILED with {table_errors} errors!")

    if has_error:
        print("\nStopping before write due to token errors!")
        sys.exit(1)

    # 4. Write back to EN .bin files
    print("\n" + "=" * 70)
    print("WRITING TRANSLATED TABLES TO .bin FILES")
    print("=" * 70)

    for name, (en_path, vi_data, en_data) in translated_tables.items():
        with open(en_path, "w", encoding="utf-8") as f:
            json.dump(vi_data, f, ensure_ascii=False, indent=2)
        print(f"Successfully wrote {len(vi_data)} entries to {en_path.name}")

        # Syntax check
        with open(en_path, "r", encoding="utf-8") as f:
            verified = json.load(f)
        assert len(verified) == len(en_data), f"Count mismatch in {name}!"
        print(f"Syntax verification passed: {en_path.name} is valid UTF-8 JSON.")

    print("\n" + "=" * 70)
    print(f"SUBAGENT 4C COMPLETED SUCCESSFULLY! Total {total_items} items processed.")
    print("=" * 70)

if __name__ == "__main__":
    main()
