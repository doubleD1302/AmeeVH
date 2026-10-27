#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publish Release v0.9.9 on GitHub with Official Windows & Android Launchers."""

import json
from pathlib import Path
import subprocess
import time
import urllib.request

def get_github_token() -> str:
    p = subprocess.Popen(
        ["git", "credential", "fill"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out, _ = p.communicate(input="protocol=https\nhost=github.com\n\n")
    for line in out.splitlines():
        if line.startswith("password="):
            return line[9:]
    return ""

def upload_asset_to_release(rel, file_path: Path, ctype: str, headers: dict, repo: str):
    upload_url_tmpl = rel["upload_url"].split("{")[0]
    existing_assets = {a["name"]: a["id"] for a in rel.get("assets", [])}
    aname = file_path.name

    if aname in existing_assets:
        aid = existing_assets[aname]
        del_req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/releases/assets/{aid}",
            headers=headers,
            method="DELETE",
        )
        try:
            urllib.request.urlopen(del_req)
            print(f"Deleted old asset {aname} (id: {aid})")
        except Exception as e:
            print(f"Could not delete old asset {aname}: {e}")

    file_mb = file_path.stat().st_size / (1024 * 1024)
    print(f"Uploading {aname} ({file_mb:.2f} MB)...")
    upload_url = f"{upload_url_tmpl}?name={aname}"
    data = file_path.read_bytes()
    up_req = urllib.request.Request(
        upload_url,
        data=data,
        headers={
            **headers,
            "Content-Type": ctype,
            "Content-Length": str(len(data)),
        },
        method="POST",
    )
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(up_req, timeout=300) as resp:
                up_res = json.loads(resp.read().decode("utf-8"))
                print(f"Uploaded {aname} -> {up_res.get('browser_download_url')}")
                break
        except Exception as e:
            print(f"Upload attempt {attempt + 1} failed for {aname}: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(3)

def main():
    root = Path(__file__).parent.parent
    token = get_github_token()
    if not token:
        print("Error: Could not retrieve GitHub token")
        return

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AmeeVH-Release-Script",
    }

    repo = "doubleD1302/AmeeVH"
    tag = "v0.9.9"
    name = (
        "Stella Sora Việt Hóa v0.9.9 - Ra Mắt Bộ Đôi Launcher Chính Thức (Windows & Android ADB) & Chuẩn Hóa Thuật Ngữ Toàn Diện"
    )
    body = """### 🌟 Bản phát hành v0.9.9 — Bộ Đôi Launcher Chính Thức & Hoàn Thiện Bản Dịch

Phiên bản **v0.9.9** đánh dấu bước tiến quan trọng của dự án **Stella Sora Việt Hóa**, chính thức ra mắt bộ đôi launcher thế hệ mới cho cả **Windows PC** và **Android** (Local ADB), cùng giao diện trang tải phong cách kính mờ hiện đại và toàn bộ dữ liệu game đã được rà soát, khử sạch lỗi dịch máy.

---

### ✨ Những điểm nâng cấp cốt lõi trong phiên bản v0.9.9:

1. **Bộ Đôi Launcher Chính Thức Thế Hệ Mới**:
   - **Windows Launcher (`StellaSora-Windows_v0.9.9.exe`)**:
     * Giao diện kính mờ (Glassmorphism) tinh xảo, hiệu ứng ánh sao và chuyển động mượt mà.
     * Tự động nhận diện Yostar Standalone Client & Steam PC (AppID 4813850).
     * Cập nhật 1-chạm, kiểm tra mã băm SHA256 từng tệp, thay thế nguyên tử (atomic move) và sao lưu preimage bảo vệ dữ liệu gốc tuyệt đối.
   - **Android Launcher (`StellaSora-Android_v0.1.1.apk`)**:
     * Kết nối Local ADB không dây (Wireless Debugging) ngay trên thiết bị Android 11+ mà không cần root hay máy tính.
     * Liên kết tự động kiểm tra và cập nhật ứng dụng qua GitHub Releases (`android_localadb_launcher.json`).
     * Tải và cài đặt trực tiếp bản dịch (`data.arcx` & `lua.arcx`) vào vùng lưu trữ game Android (`android_patch_manifest.json`), có thể kiểm chứng (verify) và hoàn tác (restore) 100%.

2. **Giao Diện Trang Web Tải Bản Dịch Phong Cách Kính Mờ (`Web_Tai_Launcher_Viet_Hoa`)**:
   - Tích hợp 2 nút tải pha lê trực tiếp cho Windows (`.exe`) và Android (`.apk`).
   - Tích hợp trình phát nhạc nền lãng mạn với nút bật/tắt biểu tượng âm nhạc tinh tế.
   - Hiệu ứng xe chạy hoạt họa Stella Sora và nhân vật động Iris / Downdust sống động.
   - Đầy đủ thông tin liên hệ tác giả **DoubleD1302** (Facebook, GitHub) và bản quyền dự án.

3. **Chuẩn Hóa Toàn Diện Cơ Sở Dữ Liệu & Thuật Ngữ Đĩa Nhạc (Discs & Skills)**:
   - Rà soát và hoàn thiện 104 kỹ năng Đĩa Nhạc (MainSkill & SecondarySkill), khử triệt để mọi dấu vết dịch máy.
   - Thống nhất danh hiệu *"Du Hành Giả Đa Năng"* (thay thế mọi biến thể phượt thủ/cân bằng).
   - Bảo toàn trọn vẹn thuật ngữ gốc *"Tinh Vọng"* theo phản hồi cộng đồng.
   - Chuẩn hóa chuỗi *"Độ khó..."* (khắc phục lỗi hiển thị *"Khó khăn..."*).

4. **Làm Sạch Mã Nguồn & Tối Ưu Kho Lưu Trữ GitHub**:
   - Dọn sạch toàn bộ tệp trung gian, prompt AI và dữ liệu rác, chỉ lưu trữ mã nguồn sạch, tinh gọn của dự án.

---

### 📥 Danh sách tệp phát hành chính thức:

* **`StellaSora-Windows_v0.9.9.exe` (54.63 MB)**: Trình khởi chạy và cài đặt Việt hóa chính thức cho Windows PC.
* **`StellaSora-Android_v0.1.1.apk` (15.89 MB)**: Trình cài đặt Việt hóa Local ADB chính thức cho Android.
* **`data_patched_vi.arcx` (24.98 MB)**: Cơ sở dữ liệu và lời thoại nhân vật VoiceTable tiếng Việt đã hoàn thiện.
* **`lua_patched_vi.arcx` (64.80 MB)**: Kịch bản cốt truyện, ký sự và tin nhắn điện thoại Light Novel tiếng Việt.
* **`android_patch_manifest.json` (842 B)**: Bảng kê khai gói bản dịch Android dành riêng cho Android Launcher.
* **`android_localadb_launcher.json` (515 B)**: Kênh kiểm tra cập nhật tự động dành cho Android Launcher.
* **`patch_manifest.json` (24.38 KB)**: Bảng kê khai chi tiết phục vụ kiểm tra toàn vẹn và cập nhật trên PC Launcher.
* **`SHA256SUMS.txt` (649 B)**: Danh sách mã băm SHA256 chính thức để người dùng đối chiếu toàn vẹn tệp tin.
"""

    # Check or create release v0.9.9
    check_req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases", headers=headers
    )
    with urllib.request.urlopen(check_req) as resp:
        releases = json.loads(resp.read().decode("utf-8"))

    existing = next((r for r in releases if r.get("tag_name") == tag), None)
    if existing:
        print(f"Release {tag} already exists (id: {existing['id']})")
        rel = existing
        patch_req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/releases/{rel['id']}",
            data=json.dumps({"body": body, "name": name}).encode("utf-8"),
            headers={**headers, "Content-Type": "application/json"},
            method="PATCH",
        )
        with urllib.request.urlopen(patch_req) as resp:
            rel = json.loads(resp.read().decode("utf-8"))
            print("Updated release metadata.")
    else:
        payload = {
            "tag_name": tag,
            "target_commitish": "main",
            "name": name,
            "body": body,
            "draft": False,
            "prerelease": False,
        }
        create_req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/releases",
            data=json.dumps(payload).encode("utf-8"),
            headers={**headers, "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(create_req) as resp:
            rel = json.loads(resp.read().decode("utf-8"))
            print(f"Created Release: id {rel['id']}, url: {rel['html_url']}")

    dist = root / "dist"
    assets = [
        (dist / "StellaSora-Windows_v0.9.9.exe", "application/vnd.microsoft.portable-executable"),
        (dist / "StellaSora-Android_v0.1.1.apk", "application/vnd.android.package-archive"),
        (dist / "data_patched_vi.arcx", "application/octet-stream"),
        (dist / "lua_patched_vi.arcx", "application/octet-stream"),
        (dist / "android_patch_manifest.json", "application/json"),
        (dist / "android_localadb_launcher.json", "application/json"),
        (dist / "patch_manifest.json", "application/json"),
        (dist / "SHA256SUMS.txt", "text/plain"),
    ]

    for file_path, ctype in assets:
        if file_path.exists():
            upload_asset_to_release(rel, file_path, ctype, headers, repo)
        else:
            print(f"Warning: File not found {file_path}")

    print("\n=== HOÀN TẤT PHÁT HÀNH TÀI NGUYÊN V0.9.9 LÊN GITHUB ===")
    print(f"Release URL: {rel.get('html_url')}")

if __name__ == "__main__":
    main()
