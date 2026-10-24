#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch AvgContacts.lua (Entry 02804_0x6b338c3a32f44951.bin) with Vietnamese Signatures and Locations.
"""

import json
from pathlib import Path
import sys

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))

from test_lua_roundtrip import Lua53Chunk, serialize_proto
from arcx_adapter import xxtea_decrypt, xxtea_encrypt, XXTEA_KEY

CONTACTS_DICT = {
    # Signatures
    "Left on read is a crime!!!": "Đã xem mà không trả lời là phạm pháp đấy nhé!!!",
    "Please stay vigilant to telecoms fraud": "Cảnh giác cao độ trước các thủ đoạn lừa đảo viễn thông!",
    "For mercenary business, please contact my work account": "Ủy thác lính đánh thuê, xin vui lòng liên hệ tài khoản công việc.",
    "Do not disturb at off-hours": "Miễn làm phiền ngoài giờ làm việc.",
    "Available for all types of accounting, magic, and teaching part-time jobs": "Nhận làm thêm kế toán, biểu diễn ma pháp và gia sư các loại.",
    "Left empty intentionally ... or being slack...": "Cố tình để trống... hoặc lười quá chưa viết...",
    "To shops that have received Fire Hazard Abatement Notices: Please rectify immediately!!!": "Các cửa hàng đã nhận Thông báo Khắc phục Nguy cơ Cháy nổ: Vui lòng xử lý ngay lập tức!!!",
    "Open for music/fighting/danmaku shooting game carry services": "Nhận gánh team / kéo rank game âm nhạc, đối kháng, bắn đạn danmaku.",
    "Where can I find more plushies~": "Tìm thêm gấu bông plushie ở đâu được nhỉ~",
    "Still tryin' to figure out photosynthesis...": "Vẫn đang vò đầu bứt tai tìm hiểu cơ chế quang hợp...",
    "Welcome to Jing's Bistro! Please book in advance": "Chào mừng đến Quán Ăn Của Jing! Vui lòng đặt bàn trước.",
    "Hello": "Xin chào.",
    "Goodwind Homecare: Always at your service with care": "Hộ Lý Thuận Phong: Luôn tận tâm đồng hành bên bạn.",
    "Not gonna reply any \"What's the homework for today\" questions": "Từ chối trả lời mọi câu hỏi kiểu \"Hôm nay có bài tập về nhà không cô\".",
    "Gaoooo~": "Gaoooo~",
    "Usually calm and collected": "Bình thường rất điềm đạm và thấu đáo.",
    "Don't forget to come watch the show": "Đừng quên ghé xem buổi biểu diễn nhé.",
    "One good deed a day!": "Mỗi ngày làm một việc tốt!",
    "Keeping it real!": "Sống thật với chính mình!",
    "Keep up! Spending money is light work": "Bắt kịp nhịp nào! Tiêu tiền chỉ là chuyện nhỏ.",
    "Am I r34lly str0ng, or just fl3x1ng?": "M-Mình thật sự mạhh, hay chỉ đag kh3o mẻ thế nhở?",
    "Who really gets it?": "Có ai thực sự thấu hiểu chăng?",
    "Newbie here!": "Lính mới toe đây ạ!",
    "For news tips, please visit the Scarlet Sights Beacon": "Cung cấp tin tức độc quyền, xin ghé Đèn Hiệu Scarlet Sights.",
    "No pic, no proof": "Không có ảnh coi như không có bằng chứng.",
    "Shopaholic!": "Tín đồ mua sắm cuồng nhiệt!",
    "On leave. Return date TBD.": "Đang trong kỳ nghỉ phép. Ngày trở lại chưa ấn định.",
    "Looking after the little ones.": "Đang trông nom chăm sóc mấy đứa nhỏ.",
    "Do not disturb unless necessary.": "Miễn làm phiền trừ phi thực sự khẩn cấp.",
    "Top-tier Xuan Shi! If you need a talisman, I'm your master.": "Huyền Sư thượng thừa! Cần vẽ bùa hộ mệnh cứ việc tìm tôi.",
    "Bio hidden due to privacy settings": "Tiểu sử đã ẩn do cài đặt quyền riêng tư.",
    "Too cool to chat": "Quá ngầu để tán gẫu.",
    "A blade knows no hesitation.": "Lưỡi gươm vung lên không bao giờ do dự.",
    "This account has been suspended for violating the rules.": "Tài khoản này đã bị tạm khóa do vi phạm tiêu chuẩn cộng đồng.",
    "Available for performances. Snacks accepted as deposit!": "Nhận lịch diễn ca nhạc. Nhận đặt cọc bằng đồ ăn vặt!",
    "Texted the God of Grace. Got a \"no service\" reply": "Đã nhắn tin cho Thần Ân Điển. Nhận lại phản hồi \"ngoài vùng phủ sóng\".",
    "Monolith fries are so good, everyone loves 'em, even the fish.": "Khoai tây chiên Cự Tháp ngon tuyệt cú mèo, ai cũng mê, ngay cả cá cũng thích.",
    "Let's go to the beach!": "Ra bãi biển chơi thôi nào!",
    "Have you seen my rag doll?": "Cậu có thấy con búp bê vải của tôi ở đâu không?",
    "Stay away perv": "Biến đi đồ biến thái.",
    "In my super-productive, main-character work era. Do not disturb.": "Đang trong thời kỳ làm việc cật lực chuẩn vai chính. Xin đừng làm phiền.",
    "Out on vacation.": "Đang đi nghỉ dưỡng.",
    "Stay safe at the beach!": "Vui chơi ở biển nhớ giữ an toàn nhé!",
    "It wants me to write something here, but I can't seem to write on it.": "Màn hình bảo mình viết gì đó vào đây, nhưng mình không biết gõ chữ kiểu gì cả.",
    "Bold in heart, brave in spirit!": "Nhiệt huyết trong tim, quả cảm trong tâm hồn!",
    "It's work time! Put your phone down": "Đến giờ làm việc rồi! Mau đặt điện thoại xuống.",
    "CEO of Boss Accord Staffing Co.": "Tổng Giám Đốc Công Ty Nhân Sự Accord.",
    "Words written down here will never be forgotten.": "Những ngôn từ được ghi lại nơi đây sẽ không bao giờ phai nhạt.",
    "Fried chicken is half-price today": "Gà rán hôm nay giảm giá một nửa nè.",
    "No comment.": "Miễn bình luận.",
    "With tea, we greet; with blade, we stand.": "Lấy trà tương đãi, vung kiếm trừ tà.",
    "Beat the monsters, complete the quests!": "Hạ gục quái vật, hoàn thành nhiệm vụ!",
    "Don't forget to sign the delivery receipt!": "Đừng quên ký nhận vào biên lai chuyển phát nhé!",
    "If you block us, don't leave the chat. If you leave, don't block.": "Nếu chặn thì đừng rời nhóm. Nếu rời nhóm thì xin đừng chặn.",
    "My promotion to full-time is underway!": "Tiến trình xét duyệt lên nhân viên chính thức đang diễn ra!",
    "File not found. The specified search pattern yielded no results.": "Không tìm thấy tập tin. Mẫu tìm kiếm chỉ định không có kết quả.",
    "Pieces reset. Resources allocated. Process initiated.": "Thiết lập lại các mảnh. Phân bổ tài nguyên. Tiến trình bắt đầu.",

    # Locations
    "Roof of the Lucky Oasis": "Sân Thượng Ốc Đảo May Mắn",
    "Slope Apartments 2-3 (Next to the Stargate Inn in Emor's Ash District)": "Khu Chung Cư Con Dốc 2-3 (Cạnh Quán Trọ Tinh Môn, Khu Tro Tàn, Emor)",
    "Leave a message on the flagpole at the southern entrance of Mirage": "Để lại lời nhắn trên cột cờ ở lối vào phía nam Mirage",
    "Building 6, Xueshi Ave, Gold District, Philae": "Tòa Nhà 6, Đại Lộ Xueshi, Khu Kim Hoàn, Philae",
    "The Lucky Oasis": "Ốc Đảo May Mắn",
    "No. 6 Zhulin Road, Cangwu City": "Số 6 Đường Trúc Lâm, Thành Phố Cangwu",
    "Top Floor, Building 14, Phoenix-tail Cat Alley, Mirage": "Tầng Thượng, Tòa Nhà 14, Hẻm Mèo Đuôi Phượng, Mirage",
    "Room 2707, Building 7, Grace Light Academy Dormitory, Emor": "Phòng 2707, Tòa Nhà 7, Ký Túc Xá Học Viện Quang Ân, Emor",
    "Greenhouse No. 6, United Harvest South Sector, Philae ": "Nhà Kính Số 6, Phân Khu Phía Nam Liên Hợp Nông Nghiệp, Philae",
    "8 Aswan Street, Philae": "Số 8 Phố Aswan, Philae",
    "*That* Clinic in Philae": "Phòng Khám *Đó* ở Philae",
    "\"That\" Clinic in Philae": "Phòng Khám *Đó* ở Philae",
    "Please send to your nearest Goodwind Homecare Service Point": "Vui lòng gửi đến Điểm Phục Vụ Hộ Lý Thuận Phong gần nhất",
    "Teacher's Office, Building 3, Grace Light Academy, Emor City": "Văn Phòng Giáo Viên, Tòa Nhà 3, Học Viện Quang Ân, Emor",
    "Eaze Village": "Làng Eaze",
    "No. 9 Tenth Street, Port Bellin": "Số 9 Phố Thứ Mười, Cảng Bellin",
    "Southern Forest, near Flavio": "Khu Rừng Phía Nam, gần Flavio",
    "Bloc's Traveling Stall": "Sạp Hàng Lưu Động Của Bloc",
    "Under the Waterway, Ash District, Emor": "Dưới Cầu Dẫn Nước, Khu Tro Tàn, Emor",
    "Petal Bloom Guild Camp, Eastern Forest, Philae Outskirts": "Doanh Trại Công Hội Hoa Nở, Rừng Phía Đông Ngoại Ô Philae",
    "The Fitzroy Family Mansion, Gold District, Emor": "Dinh Thự Gia Tộc Fitzroy, Khu Kim Hoàn, Emor",
    "No. 10, Meister Street, Philae": "Số 10 Phố Meister, Philae",
    "Daisy Orphanage, Mirage": "Mái Ấm Hoa Cúc, Mirage",
    "On the move. Contact me in person.": "Đang di chuyển ngoài đường. Cần việc hãy gặp mặt trực tiếp.",
    "I spend four months a year in Cangwu": "Mỗi năm ở Cangwu bốn tháng",
    "Please contact Trekker Association in Emor City": "Vui lòng liên hệ Hiệp Hội Lữ Khách tại Thành Phố Emor",
    "Arcade": "Khu Trò Chơi Điện Tử",
    "Amekiku Inn": "Quán Trọ Amekiku",
    "Everywhere": "Bất Cứ Nơi Nào",
    "Somewhere near Flavio, maybe": "Đâu đó gần Flavio, có lẽ vậy",
    "Silver District, Emor Grand Sanctuary of Grace": "Khu Bạch Ngân, Đại Thánh Đường Ân Điển Emor",
    "Deep water near the grove outside Emor": "Vùng nước sâu gần rặng cây ngoại ô Emor",
    "78 Dawn Street, Sailstead": "Số 78 Phố Rạng Đông, Sailstead",
    "Snowwish Festival Organizing Committee Office": "Văn Phòng Ban Tổ Chức Lễ Hội Ước Tuyết",
    "Trekkers' House, Emor": "Nhà Của Lữ Khách, Emor",
    "Filanis": "Filanis",
    "United Harvest (Philae)": "Liên Hợp Nông Nghiệp (Philae)",
    "Lucky Oasis": "Ốc Đảo May Mắn",
    "Loxy's Secret Base": "Căn Cứ Bí Mật Của Loxy",
    "Goodwind Homecare – Philae's First Squad": "Hộ Lý Thuận Phong – Đội Tiên Phong Philae",
    "Petal Bloom Revival Meeting": "Buổi Họp Phục Hưng Hoa Nở",
    "Daily Delivery Check": "Kiểm Tra Giao Hàng Hằng Ngày",
    "Countryside Sherlock": "Sherlock Holmes Chốn Làng Quê",
    "Anti-Ghosting Squad": "Biệt Đội Chống Lơ Tin Nhắn",
    "Emor, Soul Shop Flagship": "Cửa Hàng Linh Hồn Kỳ Hạm, Emor",
}

def patch_proto(proto, stats):
    new_constants = []
    for ktype, val in proto['constants']:
        if ktype in (4, 20):
            tag, s_bytes = val
            try:
                s = s_bytes.decode('utf-8')
                s_strip = s.strip()
                if s_strip in CONTACTS_DICT:
                    new_text = CONTACTS_DICT[s_strip]
                    l_pad = len(s) - len(s.lstrip())
                    r_pad = len(s) - len(s.rstrip())
                    full_new = (" " * l_pad) + new_text + (" " * r_pad)
                    new_s_bytes = full_new.encode('utf-8')
                    new_len = len(new_s_bytes) + 1
                    new_tag = 0xFF if new_len >= 0xFF else new_len
                    new_constants.append((ktype, (new_tag, new_s_bytes)))
                    stats['patched'] += 1
                    continue
            except Exception:
                pass
        new_constants.append((ktype, val))
    proto['constants'] = new_constants
    for child in proto['protos']:
        patch_proto(child, stats)

def patch_avg_contacts_entry(bin_path: Path):
    enc = bin_path.read_bytes()
    dec = xxtea_decrypt(enc, XXTEA_KEY)
    chunk = Lua53Chunk(dec)
    hdr = chunk.read_bytes(33)
    size_up = chunk.read_byte()
    proto = chunk.parse_proto()
    
    stats = {'patched': 0}
    patch_proto(proto, stats)
    
    rebuilt = hdr + bytes([size_up]) + serialize_proto(proto)
    re_enc = xxtea_encrypt(rebuilt, XXTEA_KEY)
    bin_path.write_bytes(re_enc)
    print(f"Patched {stats['patched']} contact strings in {bin_path.name}")
    return stats['patched']

if __name__ == "__main__":
    entry_path = ROOT / "work/research/lua_full_unpacked/entries/02804_0x6b338c3a32f44951.bin"
    patch_avg_contacts_entry(entry_path)
