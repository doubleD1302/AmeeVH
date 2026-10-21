#!/usr/bin/env python3
"""Publish Release v0.9.5 on GitHub with full drawn-text textures & AssetBundles."""

import json
import subprocess
import urllib.request
from pathlib import Path


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


def upload_asset_to_release(
    rel, file_path: Path, ctype: str, headers: dict, repo: str
):
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
            print(f"Deleted old asset {aname}")
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
    with urllib.request.urlopen(up_req) as resp:
        up_res = json.loads(resp.read().decode("utf-8"))
        print(f"Uploaded {aname} -> {up_res.get('browser_download_url')}")


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
    tag = "v0.9.5"
    name = (
        "Stella Sora Việt Hóa v0.9.5 - Phát Hành Toàn Diện Tài Nguyên Hình Ảnh"
        " & 60 AssetBundles Đồ Họa"
    )
    body = """### 🖼️ Bản phát hành v0.9.5 - Kích Hoạt Việt Hóa Hình Ảnh & AssetBundles Đồ Họa

Phiên bản **v0.9.5** mang đến bước tiến đột phá về đồ họa: **Chính thức Việt hóa các hình ảnh vẽ chữ (drawn-text textures / typography) trong game** và nạp trực tiếp vào **60 tệp AssetBundles (`.en.unity3d`)** của cả Yostar Client và Steam PC!

---

### ✨ Những điểm nổi bật trong phiên bản v0.9.5:
1. **Việt Hóa 493 Hình Ảnh Trong 60 AssetBundles (`.en.unity3d`)**:
   - **Mục 1 — Truyện Tranh 4 Ô Màn Hình Chờ (`01_TruyenTranh_LoadingComics_VI`)**: 53 / 53 ảnh (100%) — Toàn bộ truyện tranh loading comic đã chuyển sang tiếng Việt mượt mà, dí dỏm.
   - **Mục 2 — Danh Hiệu Nhân Vật & Người Chơi (`02_DanhHieu_HonorTitles_VI`)**: 361 / 361 ảnh (100%) — Danh hiệu vinh dự cá nhân trên hồ sơ.
   - **Mục 3 — Tiêu Đề Chương & Logo Hoạt Động (`03_TieuDe_Logos_Headers_VI`)**: 79 logo chương cốt truyện, di tích, sự kiện, thẻ tháng.
2. **Bộ Sưu Tập Đầy Đủ 610 Ảnh Vẽ Chữ Việt Hóa (`StellaSora_Texture_VI.zip`)**:
   - Bao gồm toàn bộ 6 danh mục: Truyện tranh (53), Danh hiệu (361), Logo tiêu đề (105), Nút bấm & Huy hiệu (31), Banner sự kiện (48), Chữ nghệ thuật trang phục (12).
   - Tích hợp **Thư viện ảnh tương tác HTML Gallery** (`DANH_SACH_ANH_VIET_HOA.html`) để xem trước trực quan trên trình duyệt và file bảng tính CSV chi tiết.
3. **Cập Nhật Launcher PC v0.9.5**:
   - Tự động nhận diện, sao lưu và cài đặt đồng bộ cả 3 tầng tài nguyên:
     * `Persistent_Store/Tables/data.arcx` (Cơ sở dữ liệu & Phụ đề lồng tiếng VoiceTable).
     * `Persistent_Store/Scripts/lua.arcx` (Kịch bản cốt truyện & Tin nhắn điện thoại).
     * `Persistent_Store/AssetBundles/*.en.unity3d` (60 tệp AssetBundles đồ họa ảnh chữ).
   - Tương thích song song cả **Steam PC** (AppID 4813850) và **Yostar Standalone Client**.

---

### 📥 Danh sách tệp tải về (Tùy chọn theo nhu cầu):
* **`StellaSora_Launcher_PC.zip` (180.03 MB)**: **[Khuyên dùng]** Gói trọn gói offline đầy đủ nhất (Launcher PC + Tables ArcX + Scripts ArcX + 60 AssetBundles ảnh chữ).
* **`StellaSora_AssetBundles_VI_Cat123.zip` (82.28 MB)**: Gói riêng 60 tệp AssetBundles đã vá sẵn (giải nén chép đè vào `Persistent_Store/AssetBundles/`).
* **`StellaSora_Texture_VI.zip` (96.87 MB)**: Bộ tài nguyên gốc 610 ảnh PNG tiếng Việt độ nét cao + HTML Gallery tra cứu.
* **`StellaSora_Launcher.exe` (9.49 MB)**: Trình cập nhật 1-chạm cho Windows PC.
* **`data_patched_vi.arcx` (24.61 MB)**: Cơ sở dữ liệu và toàn bộ lời thoại lồng tiếng nhân vật VoiceTable.
* **`lua_patched_vi.arcx` (64.16 MB)**: Kịch bản cốt truyện và tin nhắn điện thoại đã trau chuốt.
* **`StellaSora_VietHoa.apk` (0.03 MB)**: Ứng dụng hỗ trợ Android.
"""

    # Check or create release v0.9.5
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

    # Assets list to upload to v0.9.5
    assets = [
        (
            root / "dist" / "StellaSora_Launcher_PC.zip",
            "application/zip",
        ),  # 180 MB
        (
            root / "dist" / "StellaSora_AssetBundles_VI_Cat123.zip",
            "application/zip",
        ),  # 82 MB
        (
            root / "dist" / "StellaSora_Texture_VI.zip",
            "application/zip",
        ),  # 96 MB
        (
            root / "dist" / "StellaSora_Launcher.exe",
            "application/vnd.microsoft.portable-executable",
        ),  # 9.5 MB
        (
            root / "dist" / "data_patched_vi.arcx",
            "application/octet-stream",
        ),  # 24.6 MB
        (
            root / "dist" / "lua_patched_vi.arcx",
            "application/octet-stream",
        ),  # 64.2 MB
        (
            root / "android" / "bin" / "StellaSora_VietHoa.apk",
            "application/vnd.android.package-archive",
        ),  # 0.03 MB
    ]

    for file_path, ctype in assets:
        if file_path.exists():
            upload_asset_to_release(rel, file_path, ctype, headers, repo)
        else:
            print(f"Warning: File not found {file_path}")

    # Also upload texture packages to v0.9.0 if v0.9.0 exists
    rel_v090 = next((r for r in releases if r.get("tag_name") == "v0.9.0"), None)
    if rel_v090:
        print("\nAlso adding texture packages to Release v0.9.0...")
        extra_assets = [
            (root / "dist" / "StellaSora_Launcher_PC.zip", "application/zip"),
            (
                root / "dist" / "StellaSora_AssetBundles_VI_Cat123.zip",
                "application/zip",
            ),
            (root / "dist" / "StellaSora_Texture_VI.zip", "application/zip"),
        ]
        for file_path, ctype in extra_assets:
            if file_path.exists():
                upload_asset_to_release(
                    rel_v090, file_path, ctype, headers, repo
                )

    print("\n=== HOÀN TẤT PHÁT HÀNH TÀI NGUYÊN LÊN GITHUB ===")
    print(f"HTML URL: {rel.get('html_url')}")


if __name__ == "__main__":
    main()
