"""Build lua_extra.jsonl: Vietnamese for strings the 2.1.0 delivery never covered (phone-profile bios,
generic speaker-name list). Speaker names come from SS/glossary/glossary.csv (character_name rows)."""
import csv, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NAMES_FILE = "0x201f5620a1a481f9"
BIO_FILE = "0x6b338c3a32f44951"

BIOS = {
'"That" Clinic in Philae': 'Phòng khám “Đó” ở Philae',
'*That* Clinic in Philae': 'Phòng khám *Đó* ở Philae',
'78 Dawn Street, Sailstead': '78 phố Bình Minh, Sailstead',
'8 Aswan Street, Philae': '8 phố Aswan, Philae',
'A blade knows no hesitation.': 'Lưỡi kiếm không biết do dự.',
'Am I r34lly str0ng, or just fl3x1ng?': 'Tôi thật sự mạnh, hay chỉ đang khoe mẽ?',
'Available for all types of accounting, magic, and teaching part-time jobs': 'Nhận mọi việc làm thêm: kế toán, ma thuật và dạy học',
'Available for performances. Snacks accepted as deposit!': 'Nhận biểu diễn. Đặt cọc bằng đồ ăn vặt cũng được!',
'Beat the monsters, complete the quests!': 'Đánh quái vật, hoàn thành nhiệm vụ!',
'Bio hidden due to privacy settings': 'Tiểu sử bị ẩn do cài đặt riêng tư',
'Bold in heart, brave in spirit!': 'Tim gan dũng cảm, tinh thần can trường!',
'Building 6, Xueshi Ave, Gold District, Philae': 'Tòa 6, đại lộ Xueshi, Quận Vàng, Philae',
'CEO of Boss Accord Staffing Co.': 'CEO Công ty nhân lực Giao ước Boss',
'Deep water near the grove outside Emor': 'Vùng nước sâu gần lùm cây ngoài Emor',
'Do not disturb at off-hours': 'Ngoài giờ làm việc xin đừng làm phiền',
'Do not disturb unless necessary.': 'Không có việc cần thì đừng làm phiền.',
"Don't forget to come watch the show": 'Nhớ đến xem buổi diễn nhé',
"Don't forget to sign the delivery receipt!": 'Đừng quên ký nhận phiếu giao hàng!',
'Emor, Soul Shop Flagship': 'Emor, Tiệm linh hồn chính hiệu',
'File not found. The specified search pattern yielded no results.': 'Không tìm thấy tệp. Mẫu tìm kiếm đã chỉ định không cho kết quả nào.',
'For mercenary business, please contact my work account': 'Việc thuê lính đánh thuê xin liên hệ tài khoản công việc của tôi',
'For news tips, please visit the Scarlet Sights Beacon': 'Cung cấp tin tức xin ghé Hải đăng Mắt Đỏ',
'Fried chicken is half-price today': 'Hôm nay gà rán giảm nửa giá',
"Goodwind Homecare – Philae's First Squad": 'Goodwind Homecare – Đội chăm sóc đầu tiên của Philae',
'Goodwind Homecare: Always at your service with care': 'Goodwind Homecare: Luôn tận tâm phục vụ bạn',
'Greenhouse No. 6, United Harvest South Sector, Philae': 'Nhà kính số 6, Khu Nam United Harvest, Philae',
'Have you seen my rag doll?': 'Bạn có thấy con búp bê vải của tôi không?',
'I spend four months a year in Cangwu': 'Mỗi năm tôi ở Cangwu bốn tháng',
"If you block us, don't leave the chat. If you leave, don't block.": 'Nếu chặn thì đừng rời nhóm. Nếu rời nhóm thì đừng chặn.',
'In my super-productive, main-character work era. Do not disturb.': 'Đang trong thời kỳ làm việc siêu năng suất, nhân vật chính. Xin đừng làm phiền.',
"It wants me to write something here, but I can't seem to write on it.": 'Nó bắt tôi viết gì đó ở đây, nhưng tôi có vẻ không viết được.',
"It's work time! Put your phone down": 'Đang giờ làm việc! Bỏ điện thoại xuống',
'Keep up! Spending money is light work': 'Theo kịp nào! Tiêu tiền là việc nhẹ nhàng',
'Leave a message on the flagpole at the southern entrance of Mirage': 'Để lại lời nhắn trên cột cờ ở cổng phía nam Mirage',
'Left empty intentionally ... or being slack...': 'Cố tình để trống ... hoặc là lười...',
'Left on read is a crime!!!': 'Đọc mà không trả lời là có tội!!!',
"Let's go to the beach!": 'Đi biển thôi!',
'Looking after the little ones.': 'Đang trông mấy đứa nhỏ.',
"Monolith fries are so good, everyone loves 'em, even the fish.": 'Khoai chiên Tháp sao ngon quá, ai cũng mê, đến cá cũng thích.',
'My promotion to full-time is underway!': 'Tôi sắp được lên nhân viên chính thức!',
'No. 10, Meister Street, Philae': 'Số 10, phố Meister, Philae',
'No. 6 Zhulin Road, Cangwu City': 'Số 6 đường Zhulin, thành phố Cangwu',
'No. 9 Tenth Street, Port Bellin': 'Số 9 phố Thứ Mười, cảng Bellin',
'Not gonna reply any "What\'s the homework for today" questions': 'Sẽ không trả lời câu hỏi “Hôm nay bài tập là gì” nào hết',
'On leave. Return date TBD.': 'Đang nghỉ phép. Ngày trở lại chưa xác định.',
'On the move. Contact me in person.': 'Đang di chuyển. Hãy liên hệ trực tiếp với tôi.',
'One good deed a day!': 'Mỗi ngày một việc tốt!',
'Petal Bloom Guild Camp, Eastern Forest, Philae Outskirts': 'Trại hội Lữ Đoàn Hoa Lệnh, Rừng Đông, ngoại ô Philae',
'Petal Bloom Revival Meeting': 'Buổi họp phục hưng Lữ Đoàn Hoa Lệnh',
'Pieces reset. Resources allocated. Process initiated.': 'Đã đặt lại các mảnh. Đã phân bổ tài nguyên. Đã khởi động quy trình.',
'Please contact Trekker Association in Emor City': 'Xin liên hệ Hiệp hội Tuần du giả ở thành phố Emor',
'Please send to your nearest Goodwind Homecare Service Point': 'Vui lòng gửi đến điểm dịch vụ Goodwind Homecare gần nhất',
'Please stay vigilant to telecoms fraud': 'Xin hãy cảnh giác với lừa đảo viễn thông',
'Roof of the Lucky Oasis': 'Mái nhà Ốc đảo May mắn',
'Room 2707, Building 7, Grace Light Academy Dormitory, Emor': 'Phòng 2707, tòa 7, ký túc xá Học viện Grace Light, Emor',
'Silver District, Emor Grand Sanctuary of Grace': 'Quận Bạc, Đại Thánh điện Ân điển Emor',
'Snowwish Festival Organizing Committee Office': 'Văn phòng Ban tổ chức Lễ hội Tuyết Nguyện',
'Somewhere near Flavio, maybe': 'Chắc là đâu đó gần Flavio',
'Southern Forest, near Flavio': 'Rừng Nam, gần Flavio',
'Stay safe at the beach!': 'Đi biển nhớ giữ an toàn nhé!',
'Still tryin\' to figure out photosynthesis...': 'Vẫn đang cố hiểu quang hợp là gì...',
"Teacher's Office, Building 3, Grace Light Academy, Emor City": 'Phòng giáo viên, tòa 3, Học viện Grace Light, thành phố Emor',
'Texted the God of Grace. Got a "no service" reply': 'Nhắn tin cho Thần Ân điển. Nhận lại tin “không có dịch vụ”',
'The Fitzroy Family Mansion, Gold District, Emor': 'Dinh thự gia tộc Fitzroy, Quận Vàng, Emor',
'This account has been suspended for violating the rules.': 'Tài khoản này đã bị đình chỉ do vi phạm quy định.',
'To shops that have received Fire Hazard Abatement Notices: Please rectify immediately!!!': 'Gửi các cửa hàng đã nhận thông báo khắc phục nguy cơ cháy nổ: Hãy chỉnh sửa ngay lập tức!!!',
'Too cool to chat': 'Ngầu quá nên không buồn chat',
'Top Floor, Building 14, Phoenix-tail Cat Alley, Mirage': 'Tầng thượng, tòa 14, hẻm Mèo Đuôi Phượng, Mirage',
"Top-tier Xuan Shi! If you need a talisman, I'm your master.": 'Huyền sư hàng đầu! Cần bùa chú thì tôi là bậc thầy của bạn.',
'Under the Waterway, Ash District, Emor': 'Dưới thủy đạo, Quận Tro, Emor',
'Usually calm and collected': 'Thường ngày điềm tĩnh và bình thản',
"Welcome to Jing's Bistro! Please book in advance": 'Chào mừng đến Quán của Jing! Xin đặt bàn trước',
'Where can I find more plushies~': 'Tìm thêm thú nhồi bông ở đâu nhỉ~',
'Who really gets it?': 'Ai thật sự hiểu chứ?',
'With tea, we greet; with blade, we stand.': 'Lấy trà đón khách; lấy kiếm đứng vững.',
'Words written down here will never be forgotten.': 'Những lời viết ở đây sẽ không bao giờ bị lãng quên.',
}

UI_FILE = "0x3e63762a97ac2700"
UI = {
'A new choice has appeared.': 'Đã xuất hiện lựa chọn mới.',
'Do you want to skip the story?': 'Bạn có muốn bỏ qua cốt truyện không?',
'If we had more information...': 'Giá mà chúng ta có thêm thông tin...',
'Leads to Bad Ending': 'Dẫn đến kết thúc xấu',
'Skipping an ending will return you to the previous choice. Continue?': 'Bỏ qua kết thúc sẽ đưa bạn về lựa chọn trước đó. Tiếp tục?',
'This branch corresponds to...': 'Nhánh này tương ứng với...',
}

def main():
    glossary = {r["EN"].strip(): r["target"] for r in csv.DictReader(
        open(ROOT / "SS/glossary/glossary.csv", encoding="utf-8-sig")) if r["category"] == "character_name"}
    rows = []
    for en, vi in BIOS.items():
        rows.append({"id": f"2.1.0:lua:{BIO_FILE}:extra/bio", "source": {"source_text": en}, "text_vi": vi, "status": "Bản nháp"})
    for en, vi in UI.items():
        rows.append({"id": f"2.1.0:lua:{UI_FILE}:extra/ui", "source": {"source_text": en}, "text_vi": vi, "status": "Bản nháp"})
    names = json.loads((HERE / "left_names.json").read_text(encoding="utf-8")) if (HERE / "left_names.json").exists() else []
    for en in names:
        if en in glossary:
            rows.append({"id": f"2.1.0:lua:{NAMES_FILE}:extra/name", "source": {"source_text": en}, "text_vi": glossary[en], "status": "Bản nháp"})
    (HERE / "lua_extra.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print("rows", len(rows))

if __name__ == "__main__":
    main()
