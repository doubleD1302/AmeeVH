#!/usr/bin/env python3
"""Create draft release on GitHub and upload PC/Android binaries."""

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
    tag = 'v0.4.0'
    name = 'Stella Sora Việt Hóa v0.4.0'
    body = """Bản phát hành v0.4.0 cho Stella Sora (PC & Android).

### 📥 Cài đặt:
- **PC**: Tải `StellaSora_Launcher.exe` (1-chạm tự động cài đặt).
- **Trực tiếp Game**: Tải `data_patched_vi.arcx` hoặc bấm Cập nhật từ GitHub trên Launcher.
- **Android**: Tải `StellaSora_VietHoa.apk` hoặc `StellaSora_Launcher_PC.zip`.

### ✨ Tính năng mới:
- Đột phá Đợt 4: Hoàn tất 16,255 chuỗi (Thiên Phú, Thẻ Định Mệnh, Tiềm Năng, Kỹ Năng, Phần Thưởng, Cửa Hàng, Cốt Truyện & Hẹn Hò).
- Đạt mốc 27,455 chuỗi Việt hóa toàn game (~50% dữ liệu)."""

    # 1. Check existing releases
    check_req = urllib.request.Request(f'https://api.github.com/repos/{repo}/releases', headers=headers)
    with urllib.request.urlopen(check_req) as resp:
        releases = json.loads(resp.read().decode('utf-8'))

    existing = next((r for r in releases if r.get('tag_name') == tag), None)
    if existing:
        print(f"Release with tag {tag} already exists (id: {existing['id']})")
        rel = existing
        # Update body
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
            print(f"Created Draft Release: id {rel['id']}, url: {rel['html_url']}")

    upload_url_tmpl = rel['upload_url'].split('{')[0]

    # 2. Upload assets
    assets = [
        (root / 'dist' / 'StellaSora_Launcher.exe', 'application/vnd.microsoft.portable-executable'),
        (root / 'android' / 'bin' / 'StellaSora_VietHoa.apk', 'application/vnd.android.package-archive'),
        (root / 'StellaSora_Launcher_PC.zip', 'application/zip'),
        (root / 'work' / 'research' / 'data_patched_vi.arcx', 'application/octet-stream'),
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

        print(f"Uploading {aname} ({file_path.stat().st_size} bytes)...")
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

    print('\n=== RELEASE FINISHED ===')
    print(f"HTML URL: {rel.get('html_url')}")
    print(f"Draft: {rel.get('draft')}")
    print(f"Prerelease: {rel.get('prerelease')}")

if __name__ == '__main__':
    main()
