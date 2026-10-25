#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")

discs_file = ROOT / "work" / "batches" / "all_104_discs_survey.json"
discs = json.loads(discs_file.read_text(encoding="utf-8"))

clunky_discs = []

# List of discs needing polish
DISC_POLISH_PROPOSALS = {
    # ID: (EN, ZH, Current_DiscIP, Current_Item, Proposed_Polished, Reason)
    211001: ("Crisp Morning", "朝霭", "Sớm Mai Trong Lành", "buổi sáng sắc nét", "Sớm Mai Trong Lành", "Sửa 'buổi sáng sắc nét' trong Item table"),
    211005: ("Lonely Dunes", "孤烟", "Cồn Cát Vắng", "Cồn cát cô đơn", "Khói Độc Sa Mạc / Cồn Cát Vắng", "Đồng bộ hóa tên Item thành Cồn Cát Vắng"),
    211006: ("Sweet Creek", "甘露", "Dòng Suối Ngọt Ngào", "Lạch Ngọt", "Dòng Suối Ngọt Ngào", "Sửa 'Lạch Ngọt' máy dịch thô thiển trong Item"),
    212002: ("Whoopla", "喧哗", "Reo Vui Náo Nhiệt", "ôi chao", "Reo Vui Náo Nhiệt", "Sửa 'ôi chao' máy dịch trong Item"),
    212005: ("Flare Frenzy", "情热", "Lửa Đỏ Cuồng Nhiệt", "bùng cháy điên cuồng", "Ngọn Lửa Nồng Nhiệt", "Thanh thoát hơn 'Lửa đỏ cuồng nhiệt' và sửa 'bùng cháy điên cuồng'"),
    212007: ("Brave the Wind", "乘风", "Đón Gió Ngược Dòng", "Dũng cảm với gió", "Cưỡi Gió Vút Bay", "Gốc ZH là 乘风 (Thừa phong = Cưỡi gió), sửa 'Dũng cảm với gió'"),
    213001: ("Zesty Curiosity", "柠柚好奇", "Tò Mò Hứng Khởi", "Sự tò mò hào hứng", "Hiếu Kỳ Tươi Vui", "Tự nhiên, trong trẻo đúng chất anime"),
    213010: ("Steam Syndrome", "水蒸汽症候群", "Hội Chứng Hơi Nước", "Hội chứng hơi nước", "Say Làn Khói Nước / Hơi Nước Mộng Mị", "Tránh từ 'hội chứng hơi nước' khô khan như bệnh lý"),
    213013: ("Leaf Her to Me", "秋日絮语", "Cứ Để Cô Ấy Cho Tôi", "Lá cô ấy cho tôi", "Thì Thầm Mùa Thu", "Gốc ZH là 秋日絮语 (Thì thầm mùa thu), sửa thảm họa 'Lá cô ấy cho tôi'"),
    213017: ("★Rolling Life★", "★~转转人生~★", "★Cuộc Sống Lăn Lộn★", "★Cuộc sống lăn lộn★", "★Vòng Quay Cuộc Đời★", "Tránh từ 'lăn lộn' nghe tiêu cực, mưu sinh vất vả; gốc là chiếc đĩa/vòng quay xoay vần"),
    213021: ("Miraculous Anthem", "灵验颂歌", "Khúc Ca Kỳ Diệu", "Quốc ca kỳ diệu", "Tụng Ca Màu Nhiệm", "Sửa thảm họa dịch Anthem thành 'Quốc ca' trong Item"),
    213022: ("Love River's Curse", "诅咒爱河", "Lời Nguyền Dòng Sông Yêu", "Lời nguyền dòng sông tình yêu", "Lời Nguyền Sông Tình", "Gọn gàng, giàu chất thơ hơn 'dòng sông yêu'"),
    213026: ("Vent It Out ♥", "清扫时间DA♥YO", "Xả Hết Đi Nào ♥", "Hãy trút giận ♥", "Xả Hết Muộn Phiền ♥", "Tự nhiên, dễ thương"),
    214001: ("Meowing Cat God", "猫神降歌", "Thần Mèo Kêu Meo Meo", "Thần mèo meo meo", "Khúc Ca Miêu Thần", "Gốc ZH là 猫神降歌 (Miêu thần giáng ca), 'Thần mèo kêu meo meo' nghe như nhạc thiếu nhi"),
    214003: ("Seed Alike", "你与我相似", "Hạt Mầm Đồng Điệu", "Hạt giống tương tự", "Tâm Đầu Ý Hợp / Hạt Mầm Đồng Điệu", "Sửa 'Hạt giống tương tự' máy dịch"),
    214007: ("Soaring Blue", "极速天蓝", "Trời Xanh Cao Vút", "Tăng vọt màu xanh lam", "Vút Bay Giữa Trời Xanh", "Sửa 'Tăng vọt màu xanh lam' máy dịch"),
    214013: ("Deer's Song", "鹿鸣", "Tiếng Hát Chú Hươu", "Bài hát của hươu", "Tiếng Hươu Gọi Đàn", "Gốc Kinh Thi 鹿鸣 (Lộc minh: hươu kêu gọi đàn, hươu không biết hát)"),
    214022: ("The Meow", "午夜喵铃", "Tiếng Meo Meo", "Mèo mèo", "Chuông Mèo Nửa Đêm", "Gốc ZH là 午夜喵铃 (Chuông mèo nửa đêm), sửa 'Mèo mèo'"),
    214026: ("Sword Against Stream", "潋滟故池水", "Kiếm Ngược Dòng Nước", "Kiếm Ngược Dòng", "Kiếm Nghịch Làn Sóng", "Gốc ZH là 潋滟故池水 (Sóng biếc hồ xưa), kiếm vung ngược làn sóng"),
    214027: ("Mystic Brushstrokes", "龙飞凤舞", "Nét Cọ Thần Kỳ", "Nét vẽ huyền bí", "Rồng Bay Phượng Múa", "Gốc thành ngữ ZH 龙飞凤舞"),
    214028: ("Daylight Garden", "白日花园", "Khu Vườn Ban Ngày", "Vườn Ánh Sáng Ban Ngày", "Khu Vườn Ngập Nắng", "Tránh từ 'ban ngày' thô thiển"),
    214031: ("The Clash of Blade and Axe", "刀与斧的铮鸣", "Đao Rìu Chạm Nhau", "Cuộc đụng độ của lưỡi kiếm và rìu", "Đao Rìu Tranh Hùng / Tiếng Vang Đao Rìu", "Gốc 刀与斧的铮鸣 (Tiếng đao búa va chạm rền vang)"),
    214032: ("Dream Factory of ☆Truth", "真相☆梦工厂", "Xưởng Ước Mơ ☆Chân Lý", "Nhà máy mơ ước của ☆Sự thật", "Xưởng Mộng ☆Chân Lý", "Sửa 'Nhà máy mơ ước của ☆Sự thật' máy dịch thô"),
    214033: ("Dancing with the Bones", "与骨共舞", "Vũ Điệu Với Khung Xương", "Khiêu vũ với xương", "Vũ Điệu Cùng Bạch Cốt", "Tránh 'Vũ điệu với khung xương' / 'Khiêu vũ với xương' thô thiển"),
    214036: ("The Lost Seeker", "迷途的朝圣者", "Kẻ Tìm Kiếm Lạc Lối", "Người hành hương lạc lối", "Kẻ Hành Hương Lạc Lối", "Gốc ZH là 朝圣者 (Người hành hương / pilgrim)"),
    214037: ("Claw the Claw", "抓住传说", "Vuốt Móng Đọ Vuốt Móng", "Vuốt móng vuốt", "Bắt Trọn Huyền Thoại", "Gốc ZH là 抓住传说 (Bắt trọn huyền thoại - máy gắp thú bông), sửa 'Vuốt móng vuốt'"),
    214040: ("Fist of Courage", "勇气之拳", "Nắm Đấm Của Lòng Dũng Cảm", "Nắm đấm dũng cảm", "Quyền Năng Dũng Khí", "Bỏ chữ 'của lòng dũng cảm' rườm rà"),
    214042: ("Wine Warm, Lamps Alight", "酒暖灯明时", "Rượu Ấm, Đèn Lên", "Rượu ấm, đèn xuống", "Rượu Ấm Đèn Hoa", "Sửa 'Rượu ấm, đèn xuống' máy dịch thô"),
    214044: ("Veiled Dawn of Spring", "罗帷春染岁朝新", "Sớm Mai Mùa Xuân Mờ Ảo", "Bình minh che khuất của mùa xuân", "Sớm Xuân Bừng Tỉnh", "Thơ mộng, chuẩn anime"),
    214047: ("Delivered by the Breeze", "信笺乘风而去", "Gió Nhắn Lời Yêu", "Được cung cấp bởi Breeze", "Cánh Thư Bay Theo Gió", "Gốc 信笺乘风而去 (Lá thư cưỡi gió bay đi), sửa 'Được cung cấp bởi Breeze'"),
    214050: ("Phantom of the Banquet", "夜宴谜影", "Bóng Ma Bữa Tiệc", "Bóng ma của bữa tiệc", "Bóng Hình Đêm Tiệc", "Gốc 夜宴谜影 (Bóng ảo dạ tiệc), 'bóng ma' gây cảm giác kinh dị"),
    214056: ("Dappled Sunlight", "斑驳夏影", "Vạt Nắng Lung Linh", "Ánh nắng lốm đốm", "Bóng Nắng Chiều Hè", "Sửa 'Ánh nắng lốm đốm' máy dịch"),
    214058: ("Summer March", "夏日进行曲", "Hành Khúc Mùa Hè", "Mùa hè tháng ba", "Hành Khúc Mùa Hè", "Sửa thảm họa 'Mùa hè tháng ba' dịch March thành tháng 3 trong Item!"),
    214059: ("Fly, O Caged Bird", "飞吧，笼中鸟", "Bay Đi, Chú Chim Nhỏ", "Bay đi hỡi chú chim trong lồng", "Bay Đi, Chim Trong Lồng", "Giữ trọn hình ảnh 'chim trong lồng'"),
    214061: ("Bedtime Tales", "睡前童话", "Chuyện Kể Đêm Khuya", "Câu chuyện trước khi đi ngủ", "Cổ Tích Trước Giờ Ngủ", "Ấm áp, thơ mộng"),
    214066: ("My Guiding Star", "指引前路的启明星", "My Guiding Star", "My Guiding Star", "Khải Minh Dẫn Lối", "Đĩa còn sót tiếng Anh nguyên gốc!"),
    214067: ("Eternal Brilliance", "永恒的闪耀", "Eternal Brilliance", "Eternal Brilliance", "Rực Rỡ Vĩnh Hằng", "Đĩa còn sót tiếng Anh nguyên gốc!")
}

print(f"Total curated polished discs: {len(DISC_POLISH_PROPOSALS)}")
for did, info in DISC_POLISH_PROPOSALS.items():
    print(f"[{did}] {info[0]} -> {info[4]} ({info[5]})")
