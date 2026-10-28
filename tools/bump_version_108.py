# -*- coding: utf-8 -*-
import json
from pathlib import Path

# 1. Update launcher/core/config.py
cfg_path = Path("launcher/core/config.py")
cfg_txt = cfg_path.read_text(encoding="utf-8")
cfg_txt = cfg_txt.replace('LAUNCHER_VERSION="1.0.7"', 'LAUNCHER_VERSION="1.0.8"')
cfg_path.write_text(cfg_txt, encoding="utf-8")
print("Updated launcher/core/config.py to LAUNCHER_VERSION=1.0.8")

# 2. Update android/app/build.gradle
gradle_path = Path("android/app/build.gradle")
gradle_txt = gradle_path.read_text(encoding="utf-8")
gradle_txt = gradle_txt.replace("versionCode 9; versionName '1.0.7'", "versionCode 10; versionName '1.0.8'")
gradle_path.write_text(gradle_txt, encoding="utf-8")
print("Updated android/app/build.gradle to versionCode 10, versionName '1.0.8'")

# 3. Update launcher/notifications.json
notif_path = Path("launcher/notifications.json")
notif_data = json.loads(notif_path.read_text(encoding="utf-8"))
notif_data["version"] = "1.0.8"
notif_data["updated_at"] = "2026-10-29"
new_announcement = {
    "id": "NOTIF-022",
    "date": "2026-10-29",
    "title": "Bản cập nhật v1.0.8: Chuẩn Hóa Thuật Ngữ & Khắc Phục Xưng Hô Nhân Vật Nữ",
    "type": "release",
    "content": "Sửa triệt để lỗi bất nhất trong xưng hô anh/chị hướng tới người chơi, đảm bảo trải nghiệm nhập vai trọn vẹn cho cả nhân vật nam và nữ trên Android và PC. Đồng bộ hóa toàn bộ thuật ngữ hệ nguyên tố, tên nhân vật, vật phẩm và di vật trong game."
}
notif_data["announcements"].insert(0, new_announcement)
notif_path.write_text(json.dumps(notif_data, indent=2, ensure_ascii=False), encoding="utf-8")
print("Updated launcher/notifications.json to v1.0.8")
