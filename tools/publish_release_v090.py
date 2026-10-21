#!/usr/bin/env python3
"""
Create and publish release v0.9.0 on GitHub with full VoiceTable localization and polished natural chat scripts.
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
    tag = 'v0.9.0'
    name = 'Stella Sora Việt Hóa v0.9.0 - Việt Hóa Toàn Diện Lời Thoại Nhân Vật, Khử Calque Chat & Cốt Truyện'
    body = """### 🎉 Bản phát hành v0.9.0 - Bước Đột Phá Lớn: Việt Hóa 100% Lời Thoại Nhân Vật & Khử Sạch Calque Máy Dịch

Chào các Lữ Khách! Phiên bản **v0.9.0** giải quyết triệt để 2 vấn đề lớn nhất được cộng đồng phản hồi: **Việt hóa toàn bộ lời thoại hiển thị trên màn hình chính/khi lồng tiếng phát ra (VoiceTable)** và **xóa bỏ hoàn toàn văn phong máy dịch khô cứng trong tin nhắn điện thoại (Phone Chats)**!

---

### ✨ Những cải tiến cốt lõi trong phiên bản v0.9.0:
1. **Việt Hóa 100% Bảng Lời Thoại Nhân Vật (`VoiceTable` / `00552`)**:
   - Dịch toàn bộ **4.400 mục lồng tiếng** với **6.658 câu thoại phụ đề**:
     * **Bong bóng thoại màn hình chính (Lobby Greetings)**: Đã Việt hóa 100% câu thoại chào đón của tất cả Lữ Khách (ví dụ câu thoại Alina: *"Nếu cậu muốn dạo quanh Filanis một vòng, tôi rất sẵn lòng dẫn đường cho cậu đấy. Cứ bảo tôi một tiếng nhé."*).
     * **Thoại Chiến Đấu (Combat Voice Lines)**: Xuất trận, tung chiêu, tiêu diệt địch, bị hạ gục, dọn sạch ải, nhắc nhở đồng đội...
     * **Thoại Tương Tác Sảnh Chờ & Hồ Sơ (Touch, Idle, Favor, Present)**: Chạm màn hình, trò chuyện thân mật, tặng quà, tăng cấp độ, đột phá...
   - Toàn bộ được dịch theo phong cách lồng tiếng anime truyền cảm, giàu cảm xúc, chuẩn tính cách của từng nhân vật!

2. **Khử Sạch Lỗi Dịch Máy Ngô Nghê Trong Tin Nhắn Điện Thoại (`PM*.lua`)**:
   - Đã loại bỏ hoàn toàn các cụm từ máy dịch ngớ ngẩn:
     * *"What a shame."* ➔ Sửa dứt điểm từ *"Thật là xấu hổ"* thành **"Tiếc ghê á~"** / **"Uổng thật đấy~"**.
     * *"That was a joke."* ➔ Sửa từ *"Đó là một trò đùa"* thành **"Đùa chút thôi mà~"** / **"Trêu cậu tí thôi mà~"**.
     * *"Is that so?"* ➔ Sửa từ *"Có phải vậy không?"* thành **"Vậy sao?"** / **"Thế à?"**.
     * *"This is the way to reach me"* ➔ Sửa từ *"Đây là cách để tiếp cận tôi"* thành **"Có việc gì cứ nhắn cho tôi qua đây nhé."**.
     * *"I use this phone for non-work stuff"* ➔ Sửa thành **"Tôi dùng máy này để nói mấy chuyện ngoài lề công việc thôi nhé."**.
     * *"Mentor!"* ➔ Sửa từ *"Người hướng dẫn!"* thành **"Tiền bối ơi!"**.
     * *"Booyah! We're contacts now."* ➔ Sửa từ *"Bây giờ chúng ta là người liên hệ"* thành **"Tuyệt cú mèo! Bọn mình kết bạn xong xuôi rồi nha!"**.
     * *"Why asking me this all the sudden?"* ➔ Dịch chuẩn thành **"Sao tự nhiên cậu lại hỏi tôi chuyện này thế?"**.
     * *"Post Haste"* ➔ **"Chuyển Phát Siêu Tốc"**, *"Trong Kỷ Quán"* ➔ **"Khách Sạn Kỷ Nguyên"**.
   - Thống nhất xưng hô giữa hai người trò chuyện, văn phong chuẩn tin nhắn giới trẻ tự nhiên, gần gũi, dí dỏm.

3. **Chuẩn Hóa Danh Xưng Nhân Vật Toàn Diện**:
   - Sửa triệt để tên tiếng Anh sót lại *"Firstlight Noya"* thành **"Noya - Khải Minh"** trên toàn bộ danh bạ điện thoại, bảng NPC và mô tả lữ khách.

4. **Launcher v0.9.0 Đồng Bộ Tự Động Toàn Diện**:
   - Tự động nhận diện và cập nhật cả 2 kho lưu trữ:
     * `Persistent_Store/Tables/data.arcx` (Cơ sở dữ liệu, vật phẩm, kỹ năng, VoiceTable).
     * `Persistent_Store/Scripts/lua.arcx` (Toàn bộ kịch bản cốt truyện, thoại nhân vật, tin nhắn điện thoại).
   - Tương thích 100% với cả **Steam PC** (AppID 4813850) và **Yostar Client**.

---

### 📥 Danh sách tệp tải về:
- **`StellaSora_Launcher.exe`**: Trình cập nhật 1-chạm (tự động đồng bộ bản mới nhất từ GitHub vào game).
- **`StellaSora_Launcher_PC.zip`**: Gói offline đầy đủ gồm Launcher exe + `data_patched_vi.arcx` + `lua_patched_vi.arcx`.
- **`data_patched_vi.arcx`**: Cơ sở dữ liệu và toàn bộ lời thoại lồng tiếng nhân vật VoiceTable (chép vào `Persistent_Store/Tables/data.arcx`).
- **`lua_patched_vi.arcx`**: Kịch bản cốt truyện và tin nhắn điện thoại đã trau chuốt (chép vào `Persistent_Store/Scripts/lua.arcx`).
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

    print('\n=== RELEASE v0.9.0 PUBLISHED SUCCESSFULLY ===')
    print(f"HTML URL: {rel.get('html_url')}")

if __name__ == '__main__':
    main()
