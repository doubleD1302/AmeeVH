#!/usr/bin/env python3
"""
Create and publish release v0.8.5 on GitHub with PC Launcher, dual ArcX archives (data & lua) and APK.
"""

import json
import subprocess
import urllib.request
from pathlib import Path

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
    root = Path(__file__).parent.parent
    token = get_github_token()
    if not token:
        print('Error: Could not retrieve GitHub token')
        return

    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'AmeeVH-Release-Script'
    }

    repo = 'doubleD1302/AmeeVH'
    tag = 'v0.8.5'
    name = 'Stella Sora Việt Hóa v0.8.5 - Đột Phá Thoại Nhân Vật & Tin Nhắn Lua, Khử Hán Việt Toàn Diện'
    body = """### 🎉 Bản phát hành v0.8.5 - Đột Phá Lịch Sử: Kích Hoạt 100% Thoại & Tin Nhắn Game Stella Sora

Chào các Lữ Khách! Phiên bản v0.8.5 mang đến bước tiến đột phá quan trọng bậc nhất của dự án Việt hóa: **Chính thức giải mã và nạp thành công toàn bộ lời thoại cốt truyện và tin nhắn điện thoại (Phone Chats) trực tiếp vào game**, đồng thời **trau chuốt lại toàn bộ câu từ, khử sạch lạm dụng từ Hán Việt** theo đúng yêu cầu cộng đồng!

---

### ✨ Những điểm nâng cấp cốt lõi trong v0.8.5:
1. **Đột Phá Công Nghệ Lua 5.3 Bytecode Engine (`Scripts/lua.arcx`)**:
   - Giải mã và vá thành công **66.161 chuỗi kịch bản** trên **621 tệp Lua AVG**.
   - **Thoại Cốt Truyện Chính (`STm*`)**: Toàn bộ các chương từ Chap 0 đến Chap 10.
   - **Tin Nhắn Điện Thoại (`PM*.lua`)**: 100% cuộc trò chuyện qua điện thoại của tất cả Lữ Khách (Amber, Tilia, Iris, Jinglin, Kasimira, Donna, Laru, Minova, Wraith, Nazuka...).
   - **Hẹn Hò & Ký Sự Nhân Vật (`CG_*`, `BBm*`, `STev*`, `STsp*`)**: Mượt mà, sinh động, chuẩn cấu trúc nhị phân engine không gây crash.

2. **Chiến Dịch Khử Lạm Dụng Hán Việt & Văn Phong Chuẩn Người Việt**:
   - Khử triệt để các đại từ và danh xưng quan phương/cổ trang: *"Bệ hạ"*, *"Các hạ"*, *"Tại hạ"*, *"Bản tọa"*, *"Thị vệ"*, *"Thương hội"*, *"Đa tạ"*, *"Khôn nguôi"*, *"Thống khổ"*, *"Minh ước"*.
   - Khử toàn bộ calque máy dịch khô cứng: *"Cái gì trên thế giới?!"* -> *"Cái quái gì thế này?!"*, *"Tôi nghe thấy bạn"* -> *"Tớ nghe thấy cậu rồi"*, *"Trích Yếu Lý Lịch"* -> *"Hồ Sơ Cá Nhân"*, *"Bèo Nước Gặp Nhau"* -> *"Vừa Mới Quen"*.
   - Chuẩn hóa 1.640 tiêu đề lồng tiếng trong `CharacterArchiveVoice`: *"Khi Tung Chiêu"*, *"Khi Bị Hạ Gục"*, *"Mở Khóa Tiềm Năng"*, *"Tháp Sao: Khi Xuất Trận"*.
   - Tin nhắn điện thoại chuẩn văn phong nhắn tin giới trẻ đời thường, dí dỏm, đáng yêu ("Gõ chữ khó ghê", "Để bữa sau tớ chỉ cho nè", "Ủa alo?", "Trời đất ơi").

3. **Nâng Cấp Launcher v0.8.5 Hỗ Trợ Đồng Bộ Song Song Cả 2 Gói**:
   - Tự động sao lưu và cài đặt đồng thời:
     * `Persistent_Store/Tables/data.arcx` (Cơ sở dữ liệu, vật phẩm, kỹ năng, UI).
     * `Persistent_Store/Scripts/lua.arcx` (Kịch bản cốt truyện, thoại nhân vật, tin nhắn).
   - Tương thích hoàn hảo cả **Steam PC** (AppID 4813850) và **Yostar Client**.

---

### 📥 Tệp tải về:
- **`StellaSora_Launcher.exe`**: Trình khởi chạy & cập nhật 1-chạm (tự động tải và áp dụng cả 2 gói `data.arcx` và `lua.arcx`).
- **`StellaSora_Launcher_PC.zip`**: Gói offline đầy đủ gồm Launcher exe + `data_patched_vi.arcx` + `lua_patched_vi.arcx`.
- **`data_patched_vi.arcx`**: Tệp cơ sở dữ liệu đã Việt hóa & khử Hán Việt (chép vào `Persistent_Store/Tables/data.arcx`).
- **`lua_patched_vi.arcx`**: Tệp kịch bản thoại & tin nhắn điện thoại (chép vào `Persistent_Store/Scripts/lua.arcx`).
- **`StellaSora_VietHoa.apk`**: Ứng dụng hỗ trợ Android.
"""

    # 1. Check existing releases
    check_req = urllib.request.Request(f'https://api.github.com/repos/{repo}/releases', headers=headers)
    with urllib.request.urlopen(check_req) as resp:
        releases = json.loads(resp.read().decode('utf-8'))

    existing = next((r for r in releases if r.get('tag_name') == tag), None)
    if existing:
        print(f"Release with tag {tag} already exists (id: {existing['id']})")
        rel = existing
        patch_req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/releases/{rel['id']}",
            data=json.dumps({'body': body, 'name': name}).encode('utf-8'),
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
        (root / 'dist' / 'StellaSora_Launcher_PC.zip', 'application/zip'),
        (root / 'dist' / 'data_patched_vi.arcx', 'application/octet-stream'),
        (root / 'dist' / 'lua_patched_vi.arcx', 'application/octet-stream'),
        (root / 'android' / 'bin' / 'StellaSora_VietHoa.apk', 'application/vnd.android.package-archive'),
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

        print(f"Uploading {aname} ({file_path.stat().st_size / (1024*1024):.2f} MB)...")
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
        with urllib.request.urlopen(up_req) as resp:
            up_res = json.loads(resp.read().decode('utf-8'))
            print(f"Uploaded {aname} -> {up_res.get('browser_download_url')}")

    print('\n=== RELEASE v0.8.5 PUBLISHED SUCCESSFULLY ===')
    print(f"HTML URL: {rel.get('html_url')}")

if __name__ == '__main__':
    main()
