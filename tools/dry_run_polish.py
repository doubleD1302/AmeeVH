import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
entries = ROOT / "work" / "research" / "data_200_decrypted" / "entries"

# Tables to update
table_files = {
    "DiscIP": "00620_0x1f924138769d46ec.bin",
    "Item": "00653_0xe60634348b826f41.bin",
    "MainSkill": "00667_0x57e760255c1d3b2d.bin",
    "SecondarySkill": "00715_0x31a8814a91313129.bin",
    "Skill": "00716_0x998f849a64309b25.bin",
    "Potential": "00704_0x02ce11eca01b5fc8.bin",
    "Talent": "00764_0x3f0bd5f8db2389b6.bin"
}

# 1. Disc explicit updates
DISC_EXPLICIT = {
    211001: "Sớm Mai Trong Lành",
    211005: "Cồn Cát Hoang Vắng",
    211006: "Dòng Suối Ngọt Ngào",
    212002: "Reo Vui Náo Nhiệt",
    212005: "Ngọn Lửa Nồng Nhiệt",
    212007: "Cưỡi Gió Vút Bay",
    213001: "Hiếu Kỳ Tươi Vui",
    213010: "Say Làn Hơi Nước",
    213013: "Thì Thầm Mùa Thu",
    213017: "★Vòng Quay Cuộc Đời★",
    213021: "Tụng Ca Màu Nhiệm",
    213022: "Lời Nguyền Bến Yêu",
    213026: "Xả Hết Muộn Phiền ♥",
    214001: "Khúc Ca Miêu Thần",
    214003: "Hạt Mầm Tri Kỷ",
    214007: "Vút Bay Giữa Trời Xanh",
    214013: "Tiếng Hươu Gọi Đàn",
    214022: "Chuông Mèo Nửa Đêm",
    214026: "Kiếm Rẽ Làn Sóng",
    214027: "Rồng Bay Phượng Múa",
    214028: "Khu Vườn Ngập Nắng",
    214029: "Kho Báu Mèo Con",
    214031: "Đao Rìu Tranh Hùng",
    214032: "Xưởng Mộng ☆Chân Lý",
    214033: "Vũ Điệu Cùng Bạch Cốt",
    214036: "Kẻ Hành Hương Lạc Bước",
    214037: "Bắt Trọn Huyền Thoại",
    214040: "Quyền Năng Dũng Khí",
    214042: "Rượu Ấm Đèn Hoa",
    214044: "Sớm Xuân Bừng Tỉnh",
    214047: "Cánh Thư Bay Theo Gió",
    214050: "Bóng Hình Dạ Yến",
    214056: "Bóng Nắng Chiều Hè",
    214058: "Hành Khúc Mùa Hè",
    214059: "Bay Đi, Chim Trong Lồng",
    214061: "Cổ Tích Trước Giờ Ngủ",
    214066: "Khải Minh Dẫn Lối",
    214067: "Rực Rỡ Vĩnh Hằng"
}

# 2. General term replacements (Ordered from longest to shortest to prevent partial overlapping)
TERM_REPLACEMENTS = [
    # Skill names
    ("Ném Chuột Chuột", "Ném Chuột Chù"),
    ("Minh Ước Chuột Chuột", "Khế Ước Chuột Chù"),
    ("Bom Bồm Bộp", "Bom Bùm Bụp"),
    ("Trị Liệu Bồm Bộp", "Trị Liệu Bùm Bụp"),
    ("Đạo Tiêu Sương Giá", "Hàn Băng Lộ"),
    ("Kiên Băng Dũng Trận", "Băng Trụ Bùng Nổ"),
    ("Diệu Tinh Truy Lạp", "Sao Băng Truy Kích"),
    ("Trần Phong Chi Tinh", "Tinh Cầu Gió Cát"),
    ("Lạc Anh Tân Phấn", "Mưa Hoa Rực Rỡ"),
    ("Tật Bộ Xung Quyền", "Quyền Năng Bộc Phát"),
    ("Cối Xay Gió Nhào Lộn", "Bungee Nhào Lộn"),
    ("Thoáng Thác Đổ", "Thủy Triều Dâng Trào"),
    ("Địa Ngục Gai Góc", "Hỏa Ngục Gai Nhọn"),
    ("Bích Ba Luân Tấu", "Khúc Luân Tấu Lướt Sóng"),
    ("Món Quà Của Mèo", "Mèo Con Trao Quà"),
    ("Trị Liệu Của Mèo", "Mèo Con Trị Liệu"),
    ("Bảo Hộ Của Mèo", "Mèo Con Che Chở"),
    ("Né Tránh Của Eleanor", "Eleanor Né Tránh"),
    ("Lướt Nhanh Của Eleanor", "Eleanor Lướt Nhanh"),
    ("Áp Chế Toàn Diện Của Thỏ", "Bão Đạn Thỏ Con"),
    ("Cảnh Tử Vong", "Khúc Tử Điệu"),
    ("Thiên Thần Sa Ngã Nhịp Điệu", "Giai Điệu Seraphim"),
    ("Săn Bắn Đặc Biệt Đánh Thường", "Đòn Đánh Thường: Thợ Săn"),
    ("Lò Tháp - Đi Dạo", "Lò Tháp: Tuần Tra"),
    ("Hương Chanh Tò Mò", "Hiếu Kỳ Tươi Vui"),
    ("Kho Báu Của Mèo Con", "Kho Báu Mèo Con"),
    ("Kho Báu Của Mèo", "Kho Báu Mèo Cưng"),
    ("Kẻ Hành Hương Lạc Lối", "Kẻ Hành Hương Lạc Bước"),
    ("Bay Đi, Chú Chim Trong Lồng", "Bay Đi, Chim Trong Lồng"),
    ("Bôi Trơn Động Cơ", "Tiếp Dầu Động Cơ"),
    ("Thấu Tâm Lạnh Giá", "Lạnh Thấu Tâm Can"),
    ("Khoảnh Khắc Giật Mình", "Khoảnh Khắc Bất Ngờ"),
    ("Thục Huệ Bản Sắc", "Nết Na Thục Nữ"),
    ("Dường Như Hôm Qua", "Ngỡ Như Hôm Qua"),
    ("Gió Nhẹ Chảy Trong Mộng", "Gió Thoảng Miền Mộng Ảo"),
    ("Giam Hãm Trong Men Tình", "Ngục Tù Men Tình"),
    ("Nhiệt Huyết Của Đoàn Trưởng", "Nhiệt Huyết Đoàn Trưởng"),
    ("Hoa Nở Cũng Cần Dưỡng Nuôi", "Hoa Nở Cần Nắng Dưỡng"),

    # Disc phrases in Item and descriptions
    ("buổi sáng sắc nét", "Sớm Mai Trong Lành"),
    ("Cồn cát cô đơn", "Cồn Cát Hoang Vắng"),
    ("Lạch Ngọt", "Dòng Suối Ngọt Ngào"),
    ("ôi chao", "Reo Vui Náo Nhiệt"),
    ("bùng cháy điên cuồng", "Ngọn Lửa Nồng Nhiệt"),
    ("Dũng cảm với gió", "Cưỡi Gió Vút Bay"),
    ("Lá cô ấy cho tôi", "Thì Thầm Mùa Thu"),
    ("Quốc ca kỳ diệu", "Tụng Ca Màu Nhiệm"),
    ("Thần Mèo Kêu Meo Meo", "Khúc Ca Miêu Thần"),
    ("Thần mèo meo meo", "Khúc Ca Miêu Thần"),
    ("Hạt giống tương tự", "Hạt Mầm Tri Kỷ"),
    ("Tăng vọt màu xanh lam", "Vút Bay Giữa Trời Xanh"),
    ("Tiếng Hát Chú Hươu", "Tiếng Hươu Gọi Đàn"),
    ("Bài hát của hươu", "Tiếng Hươu Gọi Đàn"),
    ("Mèo mèo", "Chuông Mèo Nửa Đêm"),
    ("Kiếm Ngược Dòng Nước", "Kiếm Rẽ Làn Sóng"),
    ("Kiếm Ngược Dòng", "Kiếm Rẽ Làn Sóng"),
    ("Nét Cọ Thần Kỳ", "Rồng Bay Phượng Múa"),
    ("Nét vẽ huyền bí", "Rồng Bay Phượng Múa"),
    ("Khu Vườn Ban Ngày", "Khu Vườn Ngập Nắng"),
    ("Vườn Ánh Sáng Ban Ngày", "Khu Vườn Ngập Nắng"),
    ("Đao Rìu Chạm Nhau", "Đao Rìu Tranh Hùng"),
    ("Cuộc đụng độ của lưỡi kiếm và rìu", "Đao Rìu Tranh Hùng"),
    ("Nhà máy mơ ước của ☆Sự thật", "Xưởng Mộng ☆Chân Lý"),
    ("Vũ Điệu Với Khung Xương", "Vũ Điệu Cùng Bạch Cốt"),
    ("Khiêu vũ với xương", "Vũ Điệu Cùng Bạch Cốt"),
    ("Người hành hương lạc lối", "Kẻ Hành Hương Lạc Bước"),
    ("Vuốt Móng Đọ Vuốt Móng", "Bắt Trọn Huyền Thoại"),
    ("Vuốt móng vuốt", "Bắt Trọn Huyền Thoại"),
    ("Nắm Đấm Của Lòng Dũng Cảm", "Quyền Năng Dũng Khí"),
    ("Rượu ấm, đèn xuống", "Rượu Ấm Đèn Hoa"),
    ("Rượu Ấm, Đèn Lên", "Rượu Ấm Đèn Hoa"),
    ("Bình minh che khuất của mùa xuân", "Sớm Xuân Bừng Tỉnh"),
    ("Sớm Mai Mùa Xuân Mờ Ảo", "Sớm Xuân Bừng Tỉnh"),
    ("Được cung cấp bởi Breeze", "Cánh Thư Bay Theo Gió"),
    ("Gió Nhắn Lời Yêu", "Cánh Thư Bay Theo Gió"),
    ("Bóng Ma Bữa Tiệc", "Bóng Hình Dạ Yến"),
    ("Bóng ma của bữa tiệc", "Bóng Hình Dạ Yến"),
    ("Ánh nắng lốm đốm", "Bóng Nắng Chiều Hè"),
    ("Vạt Nắng Lung Linh", "Bóng Nắng Chiều Hè"),
    ("Mùa hè tháng ba", "Hành Khúc Mùa Hè"),
    ("Bay Đi, Chú Chim Nhỏ", "Bay Đi, Chim Trong Lồng"),
    ("Bay đi hỡi chú chim trong lồng", "Bay Đi, Chim Trong Lồng"),
    ("Chuyện Cổ Tích Đêm Muộn", "Cổ Tích Trước Giờ Ngủ"),
    ("Chuyện Kể Đêm Khuya", "Cổ Tích Trước Giờ Ngủ"),
    ("Câu chuyện trước khi đi ngủ", "Cổ Tích Trước Giờ Ngủ"),
    ("Khải Minh Tinh Dẫn Lối", "Khải Minh Dẫn Lối"),
    ("Ánh Hào Quang Vĩnh Cửu", "Rực Rỡ Vĩnh Hằng"),
    ("★Cuộc Sống Lăn Lộn★", "★Vòng Quay Cuộc Đời★"),
    ("★Cuộc sống lăn lộn★", "★Vòng Quay Cuộc Đời★"),
    ("Lời Nguyền Dòng Sông Yêu", "Lời Nguyền Bến Yêu"),
    ("Lời nguyền dòng sông tình yêu", "Lời Nguyền Bến Yêu"),
    ("Xả Hết Đi Nào ♥", "Xả Hết Muộn Phiền ♥"),
    ("Hãy trút giận ♥", "Xả Hết Muộn Phiền ♥")
]

# Sort by length descending
TERM_REPLACEMENTS.sort(key=lambda x: len(x[0]), reverse=True)

# Dry run
total_changes = 0
for tname, fname in table_files.items():
    fpath = entries / fname
    data = json.loads(fpath.read_text(encoding="utf-8"))
    t_changes = 0

    # Explicit disc updates
    if tname == "DiscIP":
        for did, new_name in DISC_EXPLICIT.items():
            k = f"DiscIP.{did}.3"
            if k in data and data[k] != new_name:
                print(f"[DiscIP] {k}: '{data[k]}' -> '{new_name}'")
                t_changes += 1
    elif tname == "Item":
        for did, new_name in DISC_EXPLICIT.items():
            k = f"Item.{did}.1"
            if k in data and data[k] != new_name:
                print(f"[Item] {k}: '{data[k]}' -> '{new_name}'")
                t_changes += 1

    # Term replacements across all keys
    for k, v in list(data.items()):
        if not isinstance(v, str):
            continue
        v_new = v
        for old_term, new_term in TERM_REPLACEMENTS:
            if old_term in v_new:
                v_new = v_new.replace(old_term, new_term)
        if v_new != v:
            t_changes += 1
            if t_changes <= 5 or tname in ("Skill", "MainSkill", "SecondarySkill"):
                print(f"[{tname}] {k}: '{v}' -> '{v_new}'")

    print(f"Table {tname} total modifications: {t_changes}")
    total_changes += t_changes

print(f"\nTotal dry run modifications: {total_changes}")
