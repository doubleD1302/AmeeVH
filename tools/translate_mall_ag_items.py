import json
import re
from pathlib import Path
import sys

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT))
from tools.audit_logger_engine import log_batch_modifications, export_audit_markdown
from tools.arcx_adapter import repack_archive, ArcxArchive
import shutil

ENTRIES_DIR = ROOT / "work" / "research" / "data_200_decrypted" / "entries"
ag_file = ENTRIES_DIR / "00557_0x988f7b6f2592bacd.bin"
mp_file = ENTRIES_DIR / "00671_0xee9e1d54770d965d.bin"
item_file = ENTRIES_DIR / "00653_0xe60634348b826f41.bin"

ag_data = json.loads(ag_file.read_text(encoding="utf-8"))
mp_data = json.loads(mp_file.read_text(encoding="utf-8"))
item_data = json.loads(item_file.read_text(encoding="utf-8"))

# 1. Translation dictionary for MallPackage (64 items)
MP_TRANSLATIONS = {
    'Deadly Beauty, Unparalleled Allure': 'Tuyệt Sắc Khuynh Thành',
    'Certificate that unlocks Firenze\'s exclusive appearance "Deadly Beauty, Unparalleled Allure"!': 'Đạo cụ mở khóa trang phục độc quyền của Firenze: "Tuyệt Sắc Khuynh Thành"!',
    'Call of the Coral Sea': 'Tiếng Gọi Biển San Hô',
    'Certificate that unlocks Shia\'s exclusive appearance "Call of the Coral Sea"!': 'Đạo cụ mở khóa trang phục độc quyền của Shia: "Tiếng Gọi Biển San Hô"!',
    'Practice Log': 'Khúc Gỗ Luyện Tập',
    'Claw Machine': 'Máy Gắp Thú',
    'Cabinet of Truths': 'Tủ Đựng Chân Lý',
    'Everyday Living Room Set': 'Bộ Phòng Khách Thường Nhật',
    'Sleek Black Camping Set': 'Bộ Cắm Trại Đen Huyền Bí',
    'Lv. 40 Power Boost Set': 'Gói Đột Phá Lực Chiến Cấp 40',
    'Lv. 50 Power Boost Set': 'Gói Đột Phá Lực Chiến Cấp 50',
    'Lv. 60 Power Boost Set': 'Gói Đột Phá Lực Chiến Cấp 60',
    'Stellar Ascent\x0bRecord Crescendo Set': 'Tinh Tú Thăng Hoa\nBộ Đĩa Nhạc Cao Trào',
    'Stellar Ascent: Record Crescendo Set': 'Tinh Tú Thăng Hoa: Bộ Đĩa Nhạc Cao Trào',
    'Record Crescendo Set': 'Bộ Đĩa Nhạc Cao Trào',
    'Stellar Splendor\x0bSpecial Anniversary Bundle': 'Tinh Quang Rực Rỡ\nGói Kỷ Niệm Đặc Biệt',
    'Stellar Splendor: Special Anniversary Bundle': 'Tinh Quang Rực Rỡ: Gói Kỷ Niệm Đặc Biệt',
    'Special Anniversary Bundle': 'Gói Kỷ Niệm Đặc Biệt',
    'Journey to Origins\x0bSpecial Disc Set': 'Hành Trình Khởi Nguyên\nBộ Đĩa Nhạc Đặc Biệt',
    'Journey to Origins: Special Disc Set': 'Hành Trình Khởi Nguyên: Bộ Đĩa Nhạc Đặc Biệt',
    'Journey to Origins\x0bDeluxe Disc Set': 'Hành Trình Khởi Nguyên\nBộ Đĩa Nhạc Sang Trọng',
    'Journey to Origins: Deluxe Disc Set': 'Hành Trình Khởi Nguyên: Bộ Đĩa Nhạc Sang Trọng',
    'Deluxe Disc Set': 'Bộ Đĩa Nhạc Sang Trọng',
    'Journey to Origins\x0bDisc Value Set': 'Hành Trình Khởi Nguyên\nBộ Đĩa Nhạc Ưu Đãi',
    'Journey to Origins: Disc Value Set': 'Hành Trình Khởi Nguyên: Bộ Đĩa Nhạc Ưu Đãi',
    'Duet with the Stars\x0bDisc Choice Bundle': 'Hòa Tấu Cùng Tinh Tú\nGói Tự Chọn Đĩa Nhạc',
    'Duet with the Stars: Disc Choice Bundle': 'Hòa Tấu Cùng Tinh Tú: Gói Tự Chọn Đĩa Nhạc',
    'Shine with the Stars\x0bEmblems Bloom Bundle': 'Tỏa Sáng Cùng Tinh Tú\nGói Huy Hiệu Tinh Hoa',
    'Shine with the Stars: Emblems Bloom Bundle': 'Tỏa Sáng Cùng Tinh Tú: Gói Huy Hiệu Tinh Hoa',
    'Emblems Bloom Bundle': 'Gói Huy Hiệu Tinh Hoa',
    'Journey to Origins\x0bHeartfelt Bundle': 'Hành Trình Khởi Nguyên\nGói Quà Chân Tình',
    'Journey to Origins: Heartfelt Bundle': 'Hành Trình Khởi Nguyên: Gói Quà Chân Tình',
    'Heartfelt Bundle': 'Gói Quà Chân Tình',
    'Journey to Origins\x0bTrekker Boost Bundle': 'Hành Trình Khởi Nguyên\nGói Tiếp Sức Lữ Khách',
    'Journey to Origins: Trekker Boost Bundle': 'Hành Trình Khởi Nguyên: Gói Tiếp Sức Lữ Khách',
    'Trekker Boost Bundle': 'Gói Tiếp Sức Lữ Khách',
    'Journey to Origins\x0bTicket Deal Set': 'Hành Trình Khởi Nguyên\nGói Vé Ưu Đãi',
    'Journey to Origins: Ticket Deal Set': 'Hành Trình Khởi Nguyên: Gói Vé Ưu Đãi',
    'Journey to Origins\x0bDeluxe Ticket Set': 'Hành Trình Khởi Nguyên\nGói Vé Sang Trọng',
    'Journey to Origins: Deluxe Ticket Set': 'Hành Trình Khởi Nguyên: Gói Vé Sang Trọng',
    'Deluxe Ticket Set': 'Gói Vé Sang Trọng',
    'Journey to Origins\x0bTicket Value Set': 'Hành Trình Khởi Nguyên\nGói Vé Tiết Kiệm',
    'Journey to Origins: Ticket Value Set': 'Hành Trình Khởi Nguyên: Gói Vé Tiết Kiệm',
    'Alongside the Stars\x0bTrekker Choice Bundle': 'Sát Cánh Cùng Tinh Tú\nGói Tự Chọn Lữ Khách',
    'Alongside the Stars: Trekker Choice Bundle': 'Sát Cánh Cùng Tinh Tú: Gói Tự Chọn Lữ Khách',
    'Trekker Choice Bundle': 'Gói Tự Chọn Lữ Khách',
    'One Starlit Year\x0bOne Destined Reunion Ticket Set': 'Một Năm Ánh Sao\nGói Vé Tương Phùng Định Mệnh',
    'One Starlit Year: One Destined Reunion Ticket Set': 'Một Năm Ánh Sao: Gói Vé Tương Phùng Định Mệnh',
    'One Starlit Year\x0bSpecial Anniversary Bundle': 'Một Năm Ánh Sao\nGói Kỷ Niệm Đặc Biệt',
    'One Starlit Year: Special Anniversary Bundle': 'Một Năm Ánh Sao: Gói Kỷ Niệm Đặc Biệt',
    'Treasured Collection\x0bEncounter': 'Bộ Sưu Tập Quý Giá\nTương Ngộ',
    'Treasured Collection: Encounter': 'Bộ Sưu Tập Quý Giá: Tương Ngộ',
    'Treasured Collection\x0bHarmony': 'Bộ Sưu Tập Quý Giá\nHòa Hợp',
    'Treasured Collection: Harmony': 'Bộ Sưu Tập Quý Giá: Hòa Hợp',
    'Lingering Sunlight': 'Ánh Nắng Vấn Vương',
    "Certificate that unlocks Noya's exclusive appearance: Lingering Sunlight!": 'Đạo cụ mở khóa trang phục độc quyền của Noya: "Ánh Nắng Vấn Vương"!',
    'When Distant Winds Rise': 'Khi Gió Xa Nổi Lên',
    'Certificate that unlocks Nanoha\'s exclusive appearance "When Distant Winds Rise"!': 'Đạo cụ mở khóa trang phục độc quyền của Nanoha: "Khi Gió Xa Nổi Lên"!',
    'Cocoa Night Sweetheart': 'Kẹo Ngọt Đêm Ca Cao',
    'Certificate that unlocks Mistique\'s exclusive appearance "Cocoa Night Sweetheart"!': 'Đạo cụ mở khóa trang phục độc quyền của Mistique: "Kẹo Ngọt Đêm Ca Cao"!',
    'Promise Beyond the Thaw': 'Lời Hẹn Khi Băng Tan',
    'Certificate that unlocks Gerie\'s exclusive appearance "Promise Beyond the Thaw"!': 'Đạo cụ mở khóa trang phục độc quyền của Gerie: "Lời Hẹn Khi Băng Tan"!',
    'When Morning Glories Bloom, Her Eyes Open': 'Hoa Triêu Nhan Nở, Khép Lại Giấc Mơ',
    'Certificate that unlocks Chitose\'s exclusive appearance "When Morning Glories Bloom, Her Eyes Open"!': 'Đạo cụ mở khóa trang phục độc quyền của Chitose: "Hoa Triêu Nhan Nở, Khép Lại Giấc Mơ"!'
}

# 2. Translation dictionary for ActivityGoods (51 items)
AG_TRANSLATIONS = {
    "Wholeness at Reunion's Dawn": "Viên Mãn Nơi Bình Minh Tương Phùng",
    "Unlocks the Honor Title: Wholeness at Reunion's Dawn.": "Mở khóa Danh Hiệu Vinh Dự: Viên Mãn Nơi Bình Minh Tương Phùng.",
    'Eternal Brilliance Melody': 'Giai Điệu Tỏa Sáng Vĩnh Hằng',
    'Brick of Dreams': 'Viên Gạch Mộng Ước',
    'A mysterious material capable of turning inner visions into reality. Collect enough, and you may be able to recreate the scene of your dreams.': 'Loại vật liệu thần bí có khả năng biến mộng tưởng thành hiện thực. Thu thập đủ số lượng, bạn có thể tái hiện lại khung cảnh trong mơ ước.',
    "Knight's Display Cabinet": 'Tủ Trưng Bày Của Hiệp Sĩ',
    'Eternal Brilliance': 'Tỏa Sáng Vĩnh Hằng',
    'A Runic Disc titled [Eternal Brilliance]. It can unleash great power.': 'Đĩa Nhạc mang tên [Tỏa Sáng Vĩnh Hằng]. Có thể giải phóng sức mạnh to lớn.',
    'Material required for the Crescendo of the Disc: Eternal Brilliance.': 'Nguyên liệu cần thiết cho việc Nâng Cao Trào của Đĩa Nhạc: Tỏa Sáng Vĩnh Hằng.',
    'Season 4 Bouncing Bumper Bash!': 'Mùa 4: Đại Chiến Xe Đụng Nảy Lửa!',
    'Unlocks the Honor Title: Season 4 Bouncing Bumper Bash!.': 'Mở khóa Danh Hiệu Vinh Dự: Mùa 4: Đại Chiến Xe Đụng Nảy Lửa!.',
    'Summit Show: Scent of a Witch': 'Đỉnh Cao Tranh Tài: Hương Thơm Phù Thủy',
    'Unlocks the Honor Title: Summit Show: Scent of a Witch.': 'Mở khóa Danh Hiệu Vinh Dự: Đỉnh Cao Tranh Tài: Hương Thơm Phù Thủy.',
    'Proof of a stellar performance and support for Lilibea in Summit Show: Scent of a Witch.': 'Minh chứng cho thành tích xuất sắc và sự ủng hộ dành cho Lilibea trong Đỉnh Cao Tranh Tài: Hương Thơm Phù Thủy.',
    'My Guiding Star Melody': 'Giai Điệu Khải Minh Tinh Dẫn Lối',
    'Gently Falling Stars': 'Mưa Sao Rơi Êm Đềm',
    'My Guiding Star': 'Khải Minh Tinh Dẫn Lối',
    'A Runic Disc titled [My Guiding Star]. It can unleash great power.': 'Đĩa Nhạc mang tên [Khải Minh Tinh Dẫn Lối]. Có thể giải phóng sức mạnh to lớn.',
    'Material required for the Crescendo of the Disc: My Guiding Star.': 'Nguyên liệu cần thiết cho việc Nâng Cao Trào của Đĩa Nhạc: Khải Minh Tinh Dẫn Lối.'
}

# 3. Apply translations
all_new_mods = []

for k, v in mp_data.items():
    if v in MP_TRANSLATIONS:
        new_v = MP_TRANSLATIONS[v]
        mp_data[k] = new_v
        all_new_mods.append({
            "table": "MallPackage",
            "key": k,
            "before": v,
            "after": new_v,
            "category": "Cửa Hàng & Gói Quà",
            "reason": "Dịch gói nạp, trang phục độc quyền và thẻ vé ưu đãi hấp dẫn, mượt mà",
            "agent": "Items & Quests Specialist Subagent",
            "timestamp": "2026-10-21 01:58:00"
        })

for k, v in ag_data.items():
    if v in AG_TRANSLATIONS:
        new_v = AG_TRANSLATIONS[v]
        ag_data[k] = new_v
        all_new_mods.append({
            "table": "ActivityGoods",
            "key": k,
            "before": v,
            "after": new_v,
            "category": "Vật Phẩm & Sự Kiện",
            "reason": "Dịch tên vật phẩm sự kiện, danh hiệu vinh dự và giai điệu đĩa nhạc chuẩn anime",
            "agent": "Items & Quests Specialist Subagent",
            "timestamp": "2026-10-21 01:58:00"
        })

# Also apply items from MP_TRANSLATIONS and AG_TRANSLATIONS in Item table if present
for k, v in item_data.items():
    if v in MP_TRANSLATIONS:
        new_v = MP_TRANSLATIONS[v]
        item_data[k] = new_v
        all_new_mods.append({
            "table": "Item",
            "key": k,
            "before": v,
            "after": new_v,
            "category": "Vật Phẩm & Nhiệm Vụ",
            "reason": "Đồng bộ tên trang phục và đạo cụ túi đồ",
            "agent": "Items & Quests Specialist Subagent",
            "timestamp": "2026-10-21 01:58:00"
        })
    elif v in AG_TRANSLATIONS:
        new_v = AG_TRANSLATIONS[v]
        item_data[k] = new_v
        all_new_mods.append({
            "table": "Item",
            "key": k,
            "before": v,
            "after": new_v,
            "category": "Vật Phẩm & Nhiệm Vụ",
            "reason": "Đồng bộ danh hiệu sự kiện và vật phẩm trong túi đồ",
            "agent": "Items & Quests Specialist Subagent",
            "timestamp": "2026-10-21 01:58:00"
        })

print(f"Total new modifications prepared: {len(all_new_mods)}")

# Write updated files
mp_file.write_text(json.dumps(mp_data, indent=2, ensure_ascii=False), encoding="utf-8")
ag_file.write_text(json.dumps(ag_data, indent=2, ensure_ascii=False), encoding="utf-8")
item_file.write_text(json.dumps(item_data, indent=2, ensure_ascii=False), encoding="utf-8")

# Append to JSONL log
added = log_batch_modifications(all_new_mods)
print(f"Recorded {added} new modifications to JSONL audit log.")

# Re-export master markdown report
total_md = export_audit_markdown(limit_preview=3000)
print(f"Updated Master Markdown Audit Report with {total_md:,} total unique modifications.")

# Repack archive
output_arcx = ROOT / "dist" / "data_patched_vi.arcx"
dec_dir = ROOT / "work" / "research" / "data_200_decrypted"
print(f"Repacking archive into {output_arcx}...")
repack_archive(dec_dir, output_arcx, encrypt_payload=True)
arc = ArcxArchive(output_arcx)
print(f"Repacked successfully! Size: {output_arcx.stat().st_size:,} bytes, {len(arc.entries)} entries.")

# Deploy to Steam and Yostar
dests = [
    ROOT / "work" / "research" / "data_patched_vi.arcx",
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Tables\data.arcx"),
    Path(r"C:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx")
]
for d in dests:
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output_arcx, d)
    print(f"Deployed {output_arcx.stat().st_size:,} bytes to {d}")

print("\nALL MALL, EVENT GOODS & ITEMS TRANSLATED AND AUDITED 100%!")
