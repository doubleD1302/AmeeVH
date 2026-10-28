import json, shutil
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
FILE_PATH = ROOT / "launcher" / "notifications.json"

new_notifs = [
    {
        "id": "NOTIF-021",
        "date": "2026-10-28",
        "title": "Bản cập nhật v1.0.7: Khôi Phục Texture Gốc Danh Hiệu, SKIP & Tối Ưu Chiêu Mộ",
        "type": "release",
        "content": "Khôi phục nguyên bản 100% texture gốc tiếng Anh cho toàn bộ 360+ Danh hiệu (Honor Titles), nút 'SKIP' và banner chiêu mộ kiếm 20162 / 1 Năm. Khắc phục triệt để lỗi kẹt vào giao diện Chiêu Mộ (Gacha) trên PC và nạp đầy đủ 606 hình ảnh Việt hóa chuẩn ASTC cho Android."
    },
    {
        "id": "NOTIF-020",
        "date": "2026-10-28",
        "title": "Bản cập nhật v1.0.6: Sửa Lỗi Cài Đặt APK Android & Hỗ Trợ Tạo Lối Tắt Desktop",
        "type": "release",
        "content": "Nâng cấp cơ chế tự động cài đặt cập nhật APK Android trực tiếp trong ứng dụng. Bổ sung tùy chọn tạo lối tắt màn hình chính (Desktop Shortcut) ngay sau khi cài đặt trên Launcher PC Windows (hỗ trợ cả OneDrive Desktop)."
    },
    {
        "id": "NOTIF-019",
        "date": "2026-10-28",
        "title": "Bản cập nhật v1.0.5: Tối Ưu Hóa Giao Diện & Đồng Bộ Đa Nền Tảng",
        "type": "release",
        "content": "Cải tiến độ phân giải giao diện, khử răng cưa chữ và hình ảnh trên launcher PC. Tối ưu hóa bộ nhớ đệm và cải thiện tốc độ kiểm tra cập nhật tự động."
    },
    {
        "id": "NOTIF-018",
        "date": "2026-10-27",
        "title": "Bản cập nhật v1.0.4: Nâng Cấp Tự Động Cập Nhật Trực Tiếp Trong Ứng Dụng",
        "type": "release",
        "content": "Trang bị quy trình tự động cập nhật launcher trong ứng dụng theo quy chuẩn an toàn, loại bỏ hoàn toàn việc phải tải lại thủ công."
    },
    {
        "id": "NOTIF-017",
        "date": "2026-10-27",
        "title": "Bản cập nhật v1.0.3: Khắc Phục Lỗi Nạp AssetBundles & Hoàn Thiện Âm Thanh",
        "type": "release",
        "content": "Sửa lỗi nạp gói AssetBundles trên một số thiết bị Android cấu hình đặc thù, đồng bộ hóa 100% bảng phụ đề âm thanh chiến đấu."
    }
]

with open(FILE_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

data["version"] = "1.0.7"
data["updated_at"] = "2026-10-28"

existing_ids = {a["id"] for a in data.get("announcements", [])}
to_add = [n for n in new_notifs if n["id"] not in existing_ids]
data["announcements"] = to_add + data.get("announcements", [])

content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"

with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.write(content)

# Offline fallbacks
shutil.copy2(FILE_PATH, ROOT / "launcher" / "resources" / "ui" / "notifications.json")
shutil.copy2(FILE_PATH, ROOT / "android" / "app" / "src" / "main" / "assets" / "ui" / "notifications.json")

print(f"Successfully updated notifications.json. Total announcements: {len(data['announcements'])}")
