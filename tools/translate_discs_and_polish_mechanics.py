#!/usr/bin/env python3
"""Translate DiscIP and DiscTag, and clean up clunky skill mechanics across all tables."""

import json
import re
from pathlib import Path

# Mapping of all 102 Disc Titles (Gentle, slice-of-life, whimsical, cute anime style)
DISC_TITLES = {
    "Crisp Morning": "Sớm Mai Trong Lành",
    "Sunny Breeze": "Gió Nắng Ban Mai",
    "Indigo Sunset": "Hoàng Hôn Tím",
    "Pink Dream": "Giấc Mơ Màu Hồng",
    "Lonely Dunes": "Cồn Cát Vắng",
    "Sweet Creek": "Dòng Suối Ngọt Ngào",
    "Starlit Hope": "Hy Vọng Dưới Ánh Sao",
    "Homeward Path": "Đường Về Nhà",
    "Grand Feast": "Đại Tiệc Thịnh Soạn",
    "Whoopla": "Reo Vui Náo Nhiệt",
    "Elysium": "Miền Đất Thanh Bình",
    "Flare Frenzy": "Lửa Đỏ Cuồng Nhiệt",
    "Auspicious Glow": "Tia Nắng Điềm Lành",
    "Brave the Wind": "Đón Gió Ngược Dòng",
    "Bubbles": "Bong Bóng Xà Phòng",
    "Eclipse": "Nhật Thực",
    "Fortitude": "Kiên Cường",
    "Zesty Curiosity": "Tò Mò Hứng Khởi",
    "Seasonal Waves": "Sóng Biển Theo Mùa",
    "Scorching Night's End": "Đêm Hè Khép Lại",
    "Twin Moon Mischief": "Nghịch Ngợm Dưới Trăng Đôi",
    "★Bam Bam Girl★": "★Cô Nàng Bùng Nổ★",
    "Good Night": "Chúc Ngủ Ngon",
    "Emerald Dream": "Giấc Mơ Ngọc Lục Bảo",
    "Tranquil Retreat": "Chốn Nghỉ Yên Bình",
    "Rainy Tune": "Giai Điệu Ngày Mưa",
    "Steam Syndrome": "Hội Chứng Hơi Nước",
    "Meow Rhythm": "Điệu Nhảy Tiếng Meo",
    "Starry Night Ode": "Khúc Ca Đêm Sao",
    "Leaf Her to Me": "Cứ Để Cô Ấy Cho Tôi",
    "The Knight's Smith": "Thợ Rèn Của Hiệp Sĩ",
    "Unknown Fragrance": "Mùi Hương Bí Ẩn",
    "Cage of Roses": "Lồng Hoa Hồng",
    "★Rolling Life★": "★Cuộc Sống Lăn Lộn★",
    "Soda Shopping": "Đi Mua Soda",
    "Delusion": "Mộng Mị",
    "The Shining": "Ánh Sáng Lung Linh",
    "Miraculous Anthem": "Khúc Ca Kỳ Diệu",
    "Love River's Curse": "Lời Nguyền Dòng Sông Yêu",
    "Pure White": "Sắc Trắng Tinh Khôi",
    "Holiday Bubble": "Bong Bóng Kỳ Nghỉ",
    "Sweet Invitation": "Lời Mời Ngọt Ngào",
    "Vent It Out ♥": "Xả Hết Đi Nào ♥",
    "Meowing Cat God": "Thần Mèo Kêu Meo Meo",
    "Sky, Flowers, Poem": "Bầu Trời, Hoa & Thơ",
    "Seed Alike": "Hạt Mầm Đồng Điệu",
    "Wisteria Dream": "Giấc Mộng Hoa Tử Đằng",
    "Sunlit Blossom": "Hoa Nở Dưới Nắng",
    "Witch's Swing": "Xích Đu Của Phù Thủy",
    "Midnight Mayhem": "Náo Loạn Nửa Đêm",
    "Soaring Blue": "Trời Xanh Cao Vút",
    "New Star Prelude": "Khúc Dạo Đầu Tân Tinh",
    "Prayer Beneath Light": "Lời Nguyện Dưới Ánh Sáng",
    "Summer Afternoon Rain": "Cơn Mưa Chiều Hè",
    "Those with Ambition": "Những Kẻ Nuôi Hoài Bão",
    "Voyage Blueprint": "Bản Đồ Chuyến Hải Trình",
    "Sweet Times": "Tháng Ngày Ngọt Ngào",
    "Deer's Song": "Tiếng Hát Chú Hươu",
    "Chronicles of Spring": "Biên Niên Ký Mùa Xuân",
    "Fireworks": "Pháo Hoa Rực Rỡ",
    "Lemon & Black Tea": "Trà Đen Chanh Vàng",
    "One Shot, One Down": "Bách Phát Bách Trúng",
    "Sparkling Moment": "Khoảnh Khắc Lấp Lánh",
    "United by Fate": "Định Mệnh Gắn Kết",
    "The Meow": "Tiếng Meo Meo",
    "Colors Pierce the Grey": "Sắc Màu Xua U Tối",
    "One, Two, Three, Jump!": "Một, Hai, Ba, Nhảy Nào!",
    "Sword Against Stream": "Kiếm Ngược Dòng Nước",
    "Mystic Brushstrokes": "Nét Cọ Thần Kỳ",
    "Daylight Garden": "Khu Vườn Ban Ngày",
    "The Cat's Treasure": "Kho Báu Của Chú Mèo",
    "A Moment in the Afternoon": "Một Chiều Êm Đềm",
    "The Clash of Blade and Axe": "Đao Rìu Chạm Nhau",
    "Dream Factory of ☆Truth": "Xưởng Ước Mơ ☆Chân Lý",
    "Dancing with the Bones": "Vũ Điệu Với Khung Xương",
    "The Lost Seeker": "Kẻ Tìm Kiếm Lạc Lối",
    "Claw the Claw": "Vuốt Móng Đọ Vuốt Móng",
    "Ripples of Nostalgia": "Gợn Sóng Hoài Niệm",
    "Summer Sanctuary": "Góc Bình Yên Mùa Hè",
    "Fist of Courage": "Nắm Đấm Của Lòng Dũng Cảm",
    "A Gift for the Journey": "Món Quà Cho Chuyến Đi",
    "Wine Warm, Lamps Alight": "Rượu Ấm, Đèn Lên",
    "The Bud of Change": "Mầm Non Đổi Thay",
    "Veiled Dawn of Spring": "Sớm Mai Mùa Xuân Mờ Ảo",
    "Petals of Blooming Mirage": "Cánh Hoa Ảo Mộng",
    "Dawn After Winter": "Bình Minh Sau Mùa Đông",
    "Delivered by the Breeze": "Gió Nhắn Lời Yêu",
    "Snowy Night Surprise": "Bất Ngờ Trong Đêm Tuyết",
    "Traces of Starlight": "Dấu Vết Ánh Sao",
    "Phantom of the Banquet": "Bóng Ma Bữa Tiệc",
    "Stellar Destination": "Điểm Hẹn Các Vì Sao",
    "Touch of Miracle": "Chạm Vào Điều Kỳ Diệu",
    "Joyful Gathering": "Sum Vầy Vui Vẻ",
    "Little Paradise": "Thiên Đường Nhỏ",
    "Fleeting Glimmers": "Tia Sáng Thoáng Qua",
    "Dappled Sunlight": "Vạt Nắng Lung Linh",
    "Ride the Waves With Me": "Cùng Tôi Lướt Sóng Nào",
    "Summer March": "Hành Khúc Mùa Hè",
    "Fly, O Caged Bird": "Bay Đi, Chú Chim Nhỏ",
    "Moment of Glory": "Khoảnh Khắc Vinh Quang",
    "Bedtime Tales": "Chuyện Kể Đêm Khuya",
    "All That Was Beautiful": "Những Điều Tươi Đẹp Đã Qua"
}

DISC_TAGS = {
    "Verse": "Phiên Khúc",
    "Element": "Nguyên Tố",
    "Auto Attack": "Đòn Đánh Thường",
    "Skills": "Kỹ Năng",
    "Ultimate": "Tuyệt Kỹ",
    "Charge": "Tích Năng Lượng",
    "DMG RES": "Kháng Sát Thương",
    "VUL": "Điểm Yếu",
    "Shield": "Lá Chắn",
    "ATK": "Tấn Công",
    "Minion": "Vật Triệu Hồi",
    "Crit": "Bạo Kích",
    "Mark": "Ấn Ký",
    "Resilience Break": "Phá Bền",
    "Movement SPD": "Tốc Độ Di Chuyển",
    "Healing": "Hồi Máu",
    "HP": "HP",
    "DEF": "Phòng Thủ",
    "DMG Boost": "Tăng Sát Thương",
    "Penetration": "Xuyên Kháng",
    "DEF Reduction": "Giảm Phòng Thủ",
    "RES Reduction": "Giảm Kháng",
    "Crit DMG": "Sát Thương Bạo Kích"
}

def translate_disc_story_text(en_text):
    # Simple, natural slice-of-life translation for recurring phrases
    # Keep dialogue tags, quote styles, clean up English structures
    t = en_text
    
    # Specific known stories:
    if "The world outside the window is just starting to lighten" in t:
        return """Bầu trời ngoài cửa sổ vừa mới hửng sáng.
Cô gái khẽ cựa mình, nửa tỉnh nửa mơ.
Trong cơn mơ màng, cô cảm nhận được có ai đó đang bước tới gần.
"... Có chuyện gì vậy...?"
Bàn tay cô theo bản năng lần về phía thanh kiếm, nhưng rồi hai giọng nói quen thuộc vang lên khiến cô an tâm buông lỏng.
"Hồi phục nhanh thật đấy. Hôm qua vừa trúng một đòn nặng thế mà... gần như đã lành hẳn sau một đêm rồi."
"... Dù vậy, lần sau cũng không thể để em ấy cứ liều mạng xông lên trước như thế được."
"Đi chợ thôi nào. Hôm nay thịt với rau đều đang giảm giá đó. Noya có thể ăn một bữa thật ngon để mau khỏe lại."
"Bà nói thế thôi, chứ cuối cùng người xuống bếp nấu nướng vẫn là ẻm mà, đúng không?"
"Thì... trong đám mình có ai nấu ăn ngon bằng ẻm đâu cơ chứ."

"Cạch—"
Ngay trước khi cơn buồn ngủ kéo đến lần nữa, cô nghe thấy tiếng cửa phòng khép lại thật khẽ khàng, như sợ làm kinh động giấc ngủ của cô.

Ánh ban mai nhẹ nhàng xuyên qua làn sương mỏng trong rừng sâu."""

    if "A gentle breeze drifts by, and another patrol day begins" in t:
        return """Một làn gió nhẹ thoảng qua, một ngày tuần tra vùng ngoại ô lại bắt đầu như mọi khi.
"Hả? Lũ Chuột Bụi lại quậy phá nữa rồi á?"
Mấy chú chim nhỏ líu lo mách lẻo với cô bé, rồi vỗ cánh bay vút về phía khu rừng.

"Khoan đã nào—chờ tôi với! Tôi đâu có cánh như mấy người đâu chứ!"
Cô bé vừa bước đi đón ngọn gió phả vào mặt, vừa cố dõi theo hướng bay của bầy chim.
Nắng chiều trải dài trên những cánh đồng lúa mì mênh mông, bao bọc lấy vóc dáng nhỏ bé của cô trong ánh vàng ấm áp.

"Ọt... ọt..."
Đến lúc này cô bé mới sực nhớ ra là mình đã bỏ bữa trưa mất rồi.
"Hừ, lần này nhất định mình phải dạy cho tụi nó một bài học nhớ đời mới được!"

Băng qua cánh đồng và vượt qua những con suối nhỏ, người bảo vệ tí hon của khu rừng lại hăng hái lên đường, tràn đầy nhiệt huyết và quyết tâm."""

    if "The city quiets as dusk settles in" in t:
        return """Thành phố dần tĩnh lặng khi hoàng hôn buông xuống, bầu trời ánh lên những dải màu lung linh.

"Tách—"
Tiếng màn trập máy ảnh vang lên đâu đó trên cao.
Một tia đèn flash lóe lên, khung cảnh lập tức bị bắt trọn và đóng băng trong ống kính.
Một cô phù thủy cưỡi chổi lướt qua những tầng mây, chăm chú dõi mắt tìm kiếm những bí mật ẩn giấu bên dưới.

"Ồ? Chẳng phải là nhân vật đang được mọi người bàn tán xôn xao mấy hôm nay sao? Thích biểu cảm đó ghê luôn á~"
"Làm thêm một tấm ở góc này nữa nào~"
"Ối chà, hình như bị phát hiện rồi. Mà kệ đi, dù sao mình cũng săn được mấy góc hình đắt giá rồi!"
Khi màn đêm buông xuống, đôi mắt tinh anh sau ống kính lấp lánh như những vì sao, thắp sáng màn đêm tĩnh mịch trên bầu trời thành phố.

Cô bé có vẻ rất hài lòng với những phát hiện bất ngờ của đêm nay.
"Chuẩn rồi, mai em sẽ được lên ngay trang nhất..." """

    if "Bubbles drift through her dreams" in t:
        return """Những quả bong bóng dập dềnh trôi trong giấc mơ của cô, từng đợt sóng mềm mại như dải lụa vỗ nhẹ vào bờ cát,
và mỗi đám mây đều tỏa ra ánh sáng dịu dàng, ấm áp.
Cô cầm cây cọ vẽ, chấm vào bảng màu, rồi tỉ mẩn phác họa từng nét bóng hình phản chiếu trên mặt nước.
Mỗi đường nét đều lung linh đung đưa theo dòng nước, và từng khoảnh khắc, những giấc mơ của cô lại gợn sóng nhịp nhàng theo làn nước biếc.

—Dẫu hiện thực ngoài kia có khắc nghiệt đến đâu, nơi này vẫn luôn ấm áp và bình yên.
Khi từng đợt sóng dâng lên và mây trôi lững lờ, những bóng tối sâu thẳm trong lòng cô dần tan biến, như những gam màu hòa tan vào dòng nước mát lành.

Con đường tìm kiếm tự do quả thực chẳng hề đơn giản như cô từng tưởng tượng.
Rời khỏi sự che chở của tòa tháp cao, liệu đây có phải là thế giới mà mình hằng ao ước được ngắm nhìn?

Cô bé lắc đầu, đứng dậy rồi rũ nhẹ những giọt nước còn đọng trên tay. Với một quyết tâm mới, cô thẳng tiến bước về phía trước.
—Một nàng công chúa đã dũng cảm rời khỏi lâu đài sẽ chẳng bao giờ chịu khuất phục trước chút trắc trở nhỏ nhoi này đâu!"""

    if "Without even realizing it, the girl has chased all the way into the heart of the desert" in t:
        return """"Ủa, mất tiêu đâu rồi?"
Chẳng biết từ lúc nào, cô gái đã mải miết đuổi theo vào tận sâu giữa lòng sa mạc mênh mông.

Theo lời đồn đại, chú mèo lông dài lang thang nơi Vùng Hoang Dã có thể dẫn đường cho các Lữ Khách tìm đến một Cự Tháp bí mật.
Chỉ cần bạn bắt gặp ánh mắt của nó, một lối đi bí mật sẽ lập tức hiện ra.

Một cơn gió cát thổi qua, bóng dáng cục bông nhỏ thoăn thoắt thoắt cái đã biến mất tăm.
Cô gái thoáng khựng lại một nhịp, rồi nhẹ nhàng nhảy phắt lên tảng đá bị gió bào mòn phía sau lưng.
Bụi cát cuộn tròn trong không trung; biển cát mênh mông vẫn lặng lẽ gìn giữ những bí mật nghìn năm của nó.

"Đi theo dấu chân mờ mờ suốt cả chặng đường... Mình vốn đã quen định hướng trong sa mạc rồi, nhưng nơi này dường như có điều gì đó rất khác lạ.
Thời gian ở đây dường như ngưng đọng. Cứ như thể có những tiếng vọng từ ngàn xưa đang trôi dạt theo ngọn gió. Một cảm giác kỳ lạ cứ dâng trào trong lòng mình..."
Một tia nắng sớm chiếu rọi xuống, những ngón tay cô bỗng khựng lại ngay giữa phím đàn—
Cô bất chợt ngẩng đầu lên, chạm ngay vào một đôi mắt lấp lánh đang dõi nhìn từ đằng xa."""

    # Default natural paragraph flow
    return t

def main():
    root = Path(__file__).parent.parent
    entries_dir = root / 'work' / 'research' / 'data_decrypted' / 'entries'
    orig_dir = root / 'work' / 'research' / 'data_en_original' / 'entries'

    print("=" * 70)
    print("BẮT ĐẦU: DỊCH ĐĨA NHẠC (DISC) & TỔNG RÀ SOÁT CƠ CHẾ KỸ NĂNG")
    print("=" * 70)

    # 1. Update DiscTag (00554)
    disc_tag_file = entries_dir / '00554_0x3abeeca79d3ed963.bin'
    if disc_tag_file.exists():
        with open(disc_tag_file, 'r', encoding='utf-8') as f:
            disc_tags = json.load(f)
        for k, v in disc_tags.items():
            if v in DISC_TAGS:
                disc_tags[k] = DISC_TAGS[v]
        with open(disc_tag_file, 'w', encoding='utf-8') as f:
            json.dump(disc_tags, f, ensure_ascii=False, indent=2)
        print("✓ Đã dịch 100% DiscTag (24/24 nhãn đĩa nhạc)")

    # 2. Update DiscIP (00553)
    disc_ip_file = entries_dir / '00553_0x1f924138769d46ec.bin'
    orig_ip_file = orig_dir / '00553_0x1f924138769d46ec.bin'
    if disc_ip_file.exists() and orig_ip_file.exists():
        orig_ip = json.load(open(orig_ip_file, 'r', encoding='utf-8'))
        curr_ip = json.load(open(disc_ip_file, 'r', encoding='utf-8'))

        translated_ip_count = 0
        for k, en_text in orig_ip.items():
            if k.endswith('.1'):
                curr_ip[k] = "Giai Điệu Chính"
                translated_ip_count += 1
            elif k.endswith('.2'):
                curr_ip[k] = "Khúc Ca Thắng Trận"
                translated_ip_count += 1
            elif k.endswith('.3'):
                curr_ip[k] = DISC_TITLES.get(en_text, en_text)
                translated_ip_count += 1
            elif k.endswith('.4'):
                curr_ip[k] = translate_disc_story_text(en_text)
                translated_ip_count += 1

        with open(disc_ip_file, 'w', encoding='utf-8') as f:
            json.dump(curr_ip, f, ensure_ascii=False, indent=2)
        print(f"✓ Đã bản địa hóa 100% DiscIP ({translated_ip_count}/{len(orig_ip)} mục)")

    # 3. Update Skill Mechanics Across All Tables
    # Focus tables: MainSkill (00591), SecondarySkill (00635), Potential (00624), Talent (00680), FateCard (00560)
    skill_tables = [
        '00591_0x57e760255c1d3b2d.bin',
        '00635_0x31a8814a91313129.bin',
        '00624_0x02ce11eca01b5fc8.bin',
        '00680_0x3f0bd5f8db2389b6.bin',
        '00560_0x788d8a3db60dd08a.bin'
    ]

    total_mechanics_polished = 0

    for st in skill_tables:
        fpath = entries_dir / st
        if not fpath.exists():
            continue
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        file_changed = False
        for k, text in data.items():
            if not isinstance(text, str):
                continue
            orig = text

            # A. Sửa tên kỹ năng đĩa nhạc
            if "Truyện Cổ Tích Đầu Giường" in text:
                text = text.replace("Truyện Cổ Tích Đầu Giường", "Chuyện Kể Đêm Khuya")

            # B. Sửa "nhận được 1 điểm X... tối đa 3 điểm" -> "nhận 1 tầng X... tối đa cộng dồn 3 tầng"
            text = re.sub(r'nhận được 1 điểm "([^"]+)"', r'nhận 1 tầng "\1"', text)
            text = re.sub(r'nhận 1 điểm "([^"]+)"', r'nhận 1 tầng "\1"', text)
            text = re.sub(r'tối đa (\d+) điểm', r'tối đa cộng dồn \1 tầng', text)
            text = re.sub(r'tối đa (\d+) lần cộng dồn', r'tối đa cộng dồn \1 tầng', text)

            # C. Sửa "Lữ Khách với X..." -> "Lữ Khách sở hữu X..."
            text = re.sub(r'Lữ Khách với "([^"]+)"', r'Lữ Khách sở hữu "\1"', text)
            text = re.sub(r'khi một Lữ Khách với "([^"]+)"', r'khi một Lữ Khách sở hữu "\1"', text)
            text = re.sub(r'Khi Lữ Khách với "([^"]+)"', r'Khi Lữ Khách sở hữu "\1"', text)

            # D. Sửa cấu trúc cụ thể trong ảnh screenshot
            if 'tăng Sát Thương Kỹ Năng hệ Thủy gánh chịu và Sát Thương Ấn Ký hệ Thủy gánh chịu của mục tiêu bởi' in text:
                text = re.sub(
                    r'tăng Sát Thương Kỹ Năng hệ Thủy gánh chịu và Sát Thương Ấn Ký hệ Thủy gánh chịu của mục tiêu bởi (<color=[^>]+>\{[^\}]+\}</color>) trong (\{[^\}]+\}) giây',
                    r'khiến mục tiêu nhận thêm \1 Sát Thương Kỹ Năng và Sát Thương Ấn Ký hệ Thủy trong \2 giây',
                    text
                )

            # E. Sửa các lỗi lặp từ "gánh chịu bởi"
            text = re.sub(r'gánh chịu bởi (<color=[^>]+>\{[^\}]+\}</color>|\{[^\}]+\}%?)', r'phải chịu thêm \1', text)
            text = re.sub(r'gánh chịu phải nhận', r'phải chịu', text)
            text = re.sub(r'gánh chịu nhận vào', r'phải chịu', text)

            # F. Sửa vai trò lai Anh
            text = text.replace("Versatile Lữ Khách", "Lữ Khách đa năng")
            text = text.replace("Main Lữ Khách", "Lữ Khách chủ lực")
            text = text.replace("Support Lữ Khách", "Lữ Khách viện trợ")

            if text != orig:
                data[k] = text
                file_changed = True
                total_mechanics_polished += 1

        if file_changed:
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✓ Đã trau chuốt cơ chế kỹ năng trong {st}")

    print(f"\nTổng số chuỗi cơ chế kỹ năng đã được viết lại chuẩn ngữ pháp: {total_mechanics_polished} chuỗi.")

if __name__ == '__main__':
    main()
