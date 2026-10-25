import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
entries = ROOT / "work" / "research" / "data_200_decrypted" / "entries"

# Load tables
discip = json.loads((entries / "00620_0x1f924138769d46ec.bin").read_text(encoding="utf-8"))
item = json.loads((entries / "00653_0xe60634348b826f41.bin").read_text(encoding="utf-8"))
mainskill = json.loads((entries / "00667_0x57e760255c1d3b2d.bin").read_text(encoding="utf-8"))
secskill = json.loads((entries / "00715_0x31a8814a91313129.bin").read_text(encoding="utf-8"))
skill = json.loads((entries / "00716_0x998f849a64309b25.bin").read_text(encoding="utf-8"))
potential = json.loads((entries / "00704_0x02ce11eca01b5fc8.bin").read_text(encoding="utf-8"))
talent = json.loads((entries / "00764_0x3f0bd5f8db2389b6.bin").read_text(encoding="utf-8"))

all_tables = {
    "Skill": skill,
    "MainSkill": mainskill,
    "SecondarySkill": secskill,
    "Potential": potential,
    "Talent": talent,
    "Item": item,
    "DiscIP": discip
}

old_names = [
    "Chuột Chuột", "Bom Bồm Bộp", "Trị Liệu Bồm Bộp", "Đạo Tiêu Sương Giá",
    "Kiên Băng Dũng Trận", "Diệu Tinh Truy Lạp", "Trần Phong Chi Tinh",
    "Lạc Anh Tân Phấn", "Tật Bộ Xung Quyền", "Cối Xay Gió Nhào Lộn",
    "Thoáng Thác Đổ", "Địa Ngục Gai Góc", "Bích Ba Luân Tấu",
    "Món Quà Của Mèo", "Trị Liệu Của Mèo", "Bảo Hộ Của Mèo",
    "Áp Chế Toàn Diện Của Thỏ", "Cảnh Tử Vong", "Thiên Thần Sa Ngã Nhịp Điệu",
    "Lò Tháp - Đi Dạo", "Hương Chanh Tò Mò", "Kho Báu Của Mèo",
    "Bôi Trơn Động Cơ", "Thấu Tâm Lạnh Giá", "Khoảnh Khắc Giật Mình",
    "Thục Huệ Bản Sắc", "Gió Nhẹ Chảy Trong Mộng", "Giam Hãm Trong Men Tình",
    "buổi sáng sắc nét", "Lạch Ngọt", "ôi chao", "bùng cháy điên cuồng",
    "Dũng cảm với gió", "Lá cô ấy cho tôi", "Quốc ca kỳ diệu", "Thần mèo kêu meo meo",
    "Hạt giống tương tự", "Tăng vọt màu xanh lam", "Mèo mèo",
    "Nhà máy mơ ước của ☆Sự thật", "Rượu ấm, đèn xuống", "Được cung cấp bởi Breeze",
    "Mùa hè tháng ba"
]

print("Scanning for old terms in all descriptions...")
found = []
for old_term in old_names:
    for tname, tdict in all_tables.items():
        for k, v in tdict.items():
            if old_term in str(v):
                found.append((old_term, tname, k, v))

print(f"Total occurrences found: {len(found)}")
for old_term, tname, k, v in found:
    print(f"[{old_term}] in {tname}.{k}: {repr(v)[:100]}")
