#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create and publish release v0.8.0 on GitHub with PC, Steam & Android binaries."""

import json
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
import sys

def get_github_token() -> str:
    p = subprocess.Popen(
        ['git', 'credential', 'fill'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    out, _ = p.communicate(input='protocol=https\nhost=github.com\n\n')
    for line in out.splitlines():
        if line.startswith('password='):
            return line[9:]
    return ''

def main():
    root = Path(__file__).resolve().parent.parent
    token = get_github_token()
    if not token:
        print('Error: Could not retrieve GitHub token')
        sys.exit(1)

    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'AmeeVH-Release-Script'
    }

    repo = 'doubleD1302/AmeeVH'
    tag = 'v0.8.0'
    name = 'Stella Sora Việt Hóa v0.8.0 - Hỗ Trợ Steam PC & Hoàn Tất 100% Cơ Sở Dữ Liệu Toàn Game'
    body = """# 🌟 Stella Sora Việt Hóa v0.8.0 — Bản Phát Hành Toàn Diện Đa Nền Tảng

Bản phát hành chính thức **v0.8.0** mang đến bước nhảy vọt toàn diện: Hỗ trợ hoàn hảo cho **Steam PC**, hoàn tất **100% cơ sở dữ liệu** toàn game và tối ưu hóa bộ công cụ cài đặt 1-chạm.

---

### 📥 Tải Về & Cài Đặt 1-Chạm:
- **PC Windows (Steam & Yostar Standalone)**:
  * Tải `StellaSora_Launcher.exe` (chạy trực tiếp không cần cài đặt Python).
  * Hoặc tải `StellaSora_Launcher_PC.zip` nếu cần bộ cài kèm cấu hình.
- **Trực tiếp Game Data Client**:
  * Tải `data_patched_vi.arcx` và sao chép vào `Persistent_Store/Tables/data.arcx` (hỗ trợ cả bản Steam lẫn Yostar).
- **Thiết bị Android**:
  * Tải `StellaSora_VietHoa.apk` để sử dụng cửa sổ thông báo nổi và nạp bản vá qua Local ADB.

---

### ✨ Những Điểm Nổi Bật Trong Bản v0.8.0:
1. **🎮 Hỗ Trợ Toàn Diện Steam PC (AppID 4813850)**:
   - Launcher v0.8.0 tích hợp thuật toán quét thư viện Steam đa phân vùng (`C:`, `D:`, `E:`...).
   - Thêm nút duyệt thư mục linh hoạt và tự động nhận diện bản Steam vs Yostar Standalone.
   - Hỗ trợ khởi động game trực tiếp thông qua giao thức `steam://rungameid/4813850` giúp giữ trọn vẹn Steam Overlay (Shift+Tab), đo FPS, chụp ảnh F12 và kết nối mọi tay cầm (Xbox, PlayStation DualSense, Nintendo Switch).

2. **📖 Hoàn Tất 100% Cơ Sở Dữ Liệu Toàn Game (Zero English Remaining)**:
   - Toàn bộ **71.249 chuỗi văn bản** thuộc **229 bảng dữ liệu** đã được chuyển ngữ hoàn chỉnh sang tiếng Việt.
   - Dịch & trau chuốt sâu sắc toàn bộ các minigame:
     * **Vampire Survivor** (`VampireSurvivor`, `VampireSurvivorQuest`): Cuộc Săn Nộ Cốt, các ải và thẻ buff.
     * **Đua Xe Toán Học** (`MathParkour*`): Pháo Hoa Thỏ Con, Mũi Khoan Đột Phá Nhu Quang, Cưa Tròn Nhu Quang.
     * **Đập Gạch Pha Lê** (`BreakOutLevel`): Banh Nảy Hỗn Loạn, Bi Phân Tách, Bi Laser.
     * **Sổ Tay Quái Vật** (`MonsterManual`): Mèo Hút Lông, Gà Nổ Oanh Tạc, Cỗ Máy Nổ Tung, Boss Mistique.
     * **Ký Túc Xá & Tháp Ma Vương** (`Dorm*`): Nhiệm vụ bài trí, thành tựu nội thất ấm cúng.
     * **Bách Khoa Thư & Hoạt Động Sự Kiện** (`Dictionary*`, `Activity*`).
   - Loại bỏ 100% calque dịch máy thô cứng, câu cú thuần Việt, dí dỏm, mượt mà và chuẩn phong cách Anime RPG.

3. **📝 Sổ Tay Đối Soát Toàn Bộ Bản Dịch (7.485 Sửa Đổi Độc Nhất)**:
   - Toàn bộ mọi chỉnh sửa từ trước đến nay đều được lưu vết đầy đủ trong một tệp duy nhất để tiện theo dõi và đối soát.

4. **⚡ Tự Động Cập Nhật Trực Tiếp Qua GitHub**:
   - Launcher và App di động tự động phát hiện bản phát hành mới và cho phép cập nhật 1-chạm không gián đoạn.
"""

    # 1. Check existing release
    check_req = urllib.request.Request(f'https://api.github.com/repos/{repo}/releases', headers=headers)
    with urllib.request.urlopen(check_req) as resp:
        releases = json.loads(resp.read().decode('utf-8'))

    existing = next((r for r in releases if r.get('tag_name') == tag), None)
    if existing:
        print(f"Release with tag {tag} already exists (id: {existing['id']})")
        rel = existing
        patch_req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/releases/{rel['id']}",
            data=json.dumps({'body': body, 'name': name, 'draft': False, 'prerelease': False}).encode('utf-8'),
            headers={**headers, 'Content-Type': 'application/json'},
            method='PATCH'
        )
        try:
            with urllib.request.urlopen(patch_req) as resp:
                rel = json.loads(resp.read().decode('utf-8'))
                print("Updated release metadata.")
        except Exception as e:
            print(f"Note: Could not patch release metadata: {e}")
    else:
        payload = {
            'tag_name': tag,
            'target_commitish': 'main',
            'name': name,
            'body': body,
            'draft': False,
            'prerelease': False
        }
        create_req = urllib.request.Request(
            f'https://api.github.com/repos/{repo}/releases',
            data=json.dumps(payload).encode('utf-8'),
            headers={**headers, 'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(create_req) as resp:
            rel = json.loads(resp.read().decode('utf-8'))
            print(f"Created Release: id {rel['id']}, url: {rel['html_url']}")

    upload_url_tmpl = rel['upload_url'].split('{')[0]

    # 2. Upload assets
    assets = [
        (root / 'dist' / 'StellaSora_Launcher.exe', 'application/vnd.microsoft.portable-executable'),
        (root / 'android' / 'bin' / 'StellaSora_VietHoa.apk', 'application/vnd.android.package-archive'),
        (root / 'StellaSora_Launcher_PC.zip', 'application/zip'),
        (root / 'dist' / 'data_patched_vi.arcx', 'application/octet-stream'),
    ]

    existing_assets = {a['name']: a['id'] for a in rel.get('assets', [])}

    for file_path, ctype in assets:
        if not file_path.exists():
            print(f"File {file_path} not found!")
            continue

        aname = file_path.name
        if aname in existing_assets:
            aid = existing_assets[aname]
            del_req = urllib.request.Request(
                f'https://api.github.com/repos/{repo}/releases/assets/{aid}',
                headers=headers,
                method='DELETE'
            )
            try:
                urllib.request.urlopen(del_req)
                print(f"Deleted old asset {aname}")
            except Exception as e:
                print(f"Could not delete old asset: {e}")

        print(f"Uploading {aname} ({file_path.stat().st_size:,} bytes)...")
        upload_url = f'{upload_url_tmpl}?name={aname}'
        data = file_path.read_bytes()
        up_req = urllib.request.Request(
            upload_url,
            data=data,
            headers={
                **headers,
                'Content-Type': ctype,
                'Content-Length': str(len(data))
            },
            method='POST'
        )
        try:
            with urllib.request.urlopen(up_req) as resp:
                up_res = json.loads(resp.read().decode('utf-8'))
                print(f"✓ Uploaded {aname} -> {up_res.get('browser_download_url')}")
        except Exception as e:
            print(f"❌ Failed to upload {aname}: {e}")

    print('\n=== RELEASE v0.8.0 PUBLISHED SUCCESSFULLY ===')
    print(f"HTML URL: {rel.get('html_url')}")
    print(f"Draft: {rel.get('draft')}")
    print(f"Prerelease: {rel.get('prerelease')}")

if __name__ == '__main__':
    main()
