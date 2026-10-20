# Generator and verifier of dictionary for Pillar 3 untranslated strings
import json
import re
from pathlib import Path

# Load untranslated
untr_path = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\untranslated_unique.json")
untr_data = json.loads(untr_path.read_text(encoding="utf-8"))
all_en = [d["en"] for d in untr_data]

MAPPING = {}

# 1. LevelQuestTarget (26 items)
char_map = {
    "Firenze": "Firenze", "Noya": "Noya", "Nanoha": "Nanoha", 
    "Mistique": "Mistique", "Chitose": "Chitose", "Gerie": "Gerie", 
    "Shia": "Shia", "Firstlight Noya": "Noya - Khải Minh"
}

for s in all_en:
    # LevelQuestTarget
    if "Cast " in s:
        m = re.match(r"Cast (.+?)'s (Main Skill|Support Skill|Ultimate) \{Param2\} \{Param1\} times(?:\}?)(<space=7>)?", s)
        if m:
            cname = char_map.get(m.group(1), m.group(1))
            stype = {"Main Skill": "Kỹ Năng Chủ Lực", "Support Skill": "Kỹ Năng Viện Trợ", "Ultimate": "Tuyệt Kỹ"}[m.group(2)]
            space = m.group(3) or ""
            MAPPING[s] = f"Thi triển {stype} của {cname} {{Param2}} {{Param1}} lần{space}"
    elif s == 'Kill {Param2} ×{Param1}<space=7>':
        MAPPING[s] = 'Tiêu diệt {Param2} ×{Param1}<space=7>'
    elif s == 'You have completed all the missions. You may continue the battle or exit using the elevator above.':
        MAPPING[s] = 'Đã hoàn thành toàn bộ mục tiêu thử thách! Bạn có thể tiếp tục chiến đấu hoặc rời đi bằng thang máy phía trên.'

# 2. ActivityTask (82 items)
activity_tasks = {
    'Clear the Main Story Special Episode: Yesterday Once More': 'Vượt qua Ngoại Truyện Cốt Truyện Chính: 《Ngày Ấy Trở Lại》',
    'Clear the Main Story Special Episode: The Meaning of the Saintess': 'Vượt qua Ngoại Truyện Cốt Truyện Chính: 《Ý Nghĩa Của Thánh Nữ》',
    'Main story continues on Oct 30.': 'Cốt truyện chính sẽ tiếp tục vào ngày 30/10.',
    'Clear A Gathering Storm Ⅰ with 3★': 'Vượt qua 《Bão Tố Hội Tụ Ⅰ》 đạt 3★',
    'Clear Piercing Chill Ⅰ with 3★': 'Vượt qua 《Lạnh Thấu Xương Ⅰ》 đạt 3★',
    'Clear A Gathering Storm Ⅱ with 3★': 'Vượt qua 《Bão Tố Hội Tụ Ⅱ》 đạt 3★',
    'Clear Glint of Steel Ⅰ with 3★': 'Vượt qua 《Lưỡi Thép Lóe Sáng Ⅰ》 đạt 3★',
    'Clear Thralls of Eternity Ⅰ with 3★': 'Vượt qua 《Nô Lệ Vĩnh Hằng Ⅰ》 đạt 3★',
    'Clear Piercing Chill Ⅱ with 3★': 'Vượt qua 《Lạnh Thấu Xương Ⅱ》 đạt 3★',
    'Clear The First Throne Ⅰ with 3★': 'Vượt qua 《Ngai Vàng Khởi Nguyên Ⅰ》 đạt 3★',
    'Clear Whispers in the Dark Ⅴ with 3★': 'Vượt qua 《Thì Thầm Trong Đêm Ⅴ》 đạt 3★',
    'Clear A Gathering Storm Ⅲ with 3': 'Vượt qua 《Bão Tố Hội Tụ Ⅲ》 đạt 3★',
    'Clear Piercing Chill Ⅲ with 3★': 'Vượt qua 《Lạnh Thấu Xương Ⅲ》 đạt 3★',
    'Clear Thralls of Eternity Ⅱ with 3★': 'Vượt qua 《Nô Lệ Vĩnh Hằng Ⅱ》 đạt 3★',
    'Clear Glint of Steel Ⅲ with 3★': 'Vượt qua 《Lưỡi Thép Lóe Sáng Ⅲ》 đạt 3★',
    'Clear Piercing Chill Ⅳ with 3★': 'Vượt qua 《Lạnh Thấu Xương Ⅳ》 đạt 3★',
    'Clear Ancient Malice Ⅰ with 3★': 'Vượt qua 《Oán Niệm Cổ Xưa Ⅰ》 đạt 3★',
    'Clear The First Throne Ⅱ with 3★': 'Vượt qua 《Ngai Vàng Khởi Nguyên Ⅱ》 đạt 3★',
    'Clear Rolling Start in Speed & Wheels': 'Vượt qua 《Xuất Phát Lăn Bánh》 trong Tốc Độ & Bánh Xe',
    'Clear Joyride in Speed & Wheels': 'Vượt qua 《Dạo Phố Thảnh Thơi》 trong Tốc Độ & Bánh Xe',
    'Clear Hot Pursuit in Speed & Wheels': 'Vượt qua 《Truy Kích Gay Cấn》 trong Tốc Độ & Bánh Xe',
    'Clear Asphalt Rush in Speed & Wheels': 'Vượt qua 《Lao Nhanh Nhựa Đường》 trong Tốc Độ & Bánh Xe',
    'Clear Most Wanted in Speed & Wheels': 'Vượt qua 《Truy Nã Đỉnh Điểm》 trong Tốc Độ & Bánh Xe',
    'Clear Neo Romance in Speed & Wheels': 'Vượt qua 《Lãng Mạn Tân Thời》 trong Tốc Độ & Bánh Xe',
    'Clear Racing Horizon in Speed & Wheels': 'Vượt qua 《Chân Trời Tốc Độ》 trong Tốc Độ & Bánh Xe',
    'Clear Moment of Entry in Fatebound Stellar Deck': 'Vượt qua 《Khoảnh Khắc Bước Vào》 trong Bộ Bài Tinh Tú Định Mệnh',
    'Clear Contract Mirror in Fatebound Stellar Deck': 'Vượt qua 《Gương Khế Ước》 trong Bộ Bài Tinh Tú Định Mệnh',
    'Clear Ignis Mirror in Fatebound Stellar Deck': 'Vượt qua 《Gương Lửa Ignis》 trong Bộ Bài Tinh Tú Định Mệnh',
    'Clear Ultimate Mirror in Fatebound Stellar Deck': 'Vượt qua 《Gương Tối Thượng》 trong Bộ Bài Tinh Tú Định Mệnh',
    'Clear Stardust Whispers (Beginner) within 100s': 'Vượt qua 《Lời Thì Thầm Bụi Sao (Sơ Cấp)》 trong vòng 100 giây',
    'Clear Aurora Mirage (Beginner) within 100s': 'Vượt qua 《Ảo Ảnh Cực Quang (Sơ Cấp)》 trong vòng 100 giây',
    'Clear Ode to Nova (Normal) within 100s': 'Vượt qua 《Khúc Ca Nova (Trung Cấp)》 trong vòng 100 giây',
    "Clear Meteor's Song (Normal) within 100s": 'Vượt qua 《Khúc Ca Sao Băng (Trung Cấp)》 trong vòng 100 giây',
    'Clear Pulse Overture (Hard) with at least 4 Stamina remaining': 'Vượt qua 《Khúc Dạo Đầu Mạch Đập (Khó)》 với ít nhất 4 Thể Lực còn lại',
    'Clear Gaze into Time (Hard) with at least 4 Stamina remaining': 'Vượt qua 《Ánh Nhìn Thời Gian (Khó)》 với ít nhất 4 Thể Lực còn lại',
    'Clear Black Hole Echoes (Expert) with at least 4 Stamina remaining': 'Vượt qua 《Tiếng Vọng Hố Đen (Chuyên Gia)》 với ít nhất 4 Thể Lực còn lại',
    'Clear Cosmic Drift (Expert) with at least 4 Stamina remaining': 'Vượt qua 《Trôi Dạt Vũ Trụ (Chuyên Gia)》 với ít nhất 4 Thể Lực còn lại',
}
MAPPING.update(activity_tasks)

# Regex activity tasks
for s in all_en:
    if s in MAPPING:
        continue
    m1 = re.match(r"Clear event Battle Stages (\d+) times\.", s)
    if m1:
        MAPPING[s] = f"Vượt Ải Chiến Đấu sự kiện {m1.group(1)} lần."
        continue
    m2 = re.match(r"Obtain Antique Bronze Coin ×([\d,]+) during the event", s)
    if m2:
        MAPPING[s] = f"Tích lũy Xu Đồng Cổ ×{m2.group(1)} trong thời gian sự kiện"
        continue
    m3 = re.match(r"Reach a total score of ([\d,]+) in Speed & Wheels", s)
    if m3:
        MAPPING[s] = f"Đạt tổng điểm {m3.group(1)} trong Tốc Độ & Bánh Xe"
        continue
    m4 = re.match(r"Score ([\d,]+) points in a single run of Fatebound Stellar Deck", s)
    if m4:
        MAPPING[s] = f"Đạt {m4.group(1)} điểm trong một lượt chơi Bộ Bài Tinh Tú Định Mệnh"
        continue
    m5 = re.match(r"Defeat (\d+) enemies in any stage\.?", s)
    if m5:
        MAPPING[s] = f"Tiêu diệt {m5.group(1)} kẻ địch ở ải bất kỳ."
        continue
    m6 = re.match(r"Destroy (\d+) tiles in any stage\.", s)
    if m6:
        MAPPING[s] = f"Phá hủy {m6.group(1)} ô gạch ở ải bất kỳ."
        continue
    m7 = re.match(r"Collect (\d+) items in any stage\.", s)
    if m7:
        MAPPING[s] = f"Thu thập {m7.group(1)} vật phẩm ở ải bất kỳ."
        continue

print(f"Mapped so far: {len(MAPPING)} / {len(all_en)}")
