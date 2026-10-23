#!/usr/bin/env python3
"""Publish Release v0.9.6 on GitHub with full 63 AssetBundles (842 textures) & Manifest."""

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
    tag = "v0.9.6"
    name = (
        "Stella Sora Việt Hóa v0.9.6 - Tích Hợp Toàn Bộ 63 AssetBundles Đồ Họa & Đồng Bộ 3 Tầng"
    )
    body = """### 🎨 Bản phát hành v0.9.6 - Hoàn Thiện Toàn Bộ 63 AssetBundles Đồ Họa & Nâng Cấp Launcher

Phiên bản **v0.9.6** chính thức tích hợp toàn bộ **63 tệp AssetBundles đồ họa (842 ảnh chữ Việt hóa)** thuộc trọn vẹn cả 6 danh mục, đồng thời nâng cấp Launcher PC hỗ trợ cơ chế xác thực Manifest, kiểm tra mã băm SHA256 từng tệp, thay thế nguyên tử (atomic replace) và sao lưu preimage an toàn!

---

### ✨ Những điểm nâng cấp cốt lõi trong phiên bản v0.9.6:

1. **Phát Hành Toàn Bộ 63 AssetBundles (`.en.unity3d`) Đồ Họa (842 Textures)**:
   - **Mục 1 — Truyện Tranh 4 Ô Màn Hình Chờ (`01_TruyenTranh_LoadingComics`)**: 53 / 53 ảnh (100%) — Toàn bộ truyện tranh loading comic chuyển ngữ tự nhiên, hài hước.
   - **Mục 2 — Danh Hiệu Cá Nhân (`02_DanhHieu_HonorTitles`)**: 361 / 361 danh hiệu (100%) — Đạt chuẩn 1:1 hình khối khung viền gốc, giữ trọn vẹn bóng đổ mờ drop shadow và sắc nét trên mọi giao diện UI.
   - **Mục 3 — Tiêu Đề Chương & Logo Hoạt Động (`03_TieuDe_Logos_Headers`)**: Khử sạch 100% hiện tượng đè tem (ghosting) trên SpriteAtlas đa ngôn ngữ (`ui_commonex`, `ui_equipment`).
   - **Mục 4 — Nút Bấm & Nhãn Chức Năng (`04_NutBam_Buttons`)**: Nút chiến đấu, tự động, bỏ qua và nhãn tính năng.
   - **Mục 5 — Banners Hoạt Động & Sự Kiện (`05_SuKien_Banners_Tabs`)**: Toàn bộ banner sự kiện, giới thiệu trang phục và tab hoạt động.
   - **Mục 6 — Chữ Nghệ Thuật Trang Phục (`06_TrangPhuc_SkinArtText`)**: Các chữ nghệ thuật độc quyền trên skin nhân vật.

2. **Nâng Cấp Quy Trình Cập Nhật Launcher PC v0.9.6 (3 Tầng Đồng Bộ)**:
   - Tự động tải và áp dụng đồng bộ cả 3 gói dữ liệu chính:
     * **[1/3] Bảng dữ liệu Tables (`data.arcx` ~25.8 MB)**: Giao diện Core UI, Bách khoa thư, Kỹ năng chiến đấu.
     * **[2/3] Kịch bản thoại & Tin nhắn (`lua.arcx` ~67.3 MB)**: Toàn bộ 10,000+ câu thoại cốt truyện, Ký sự tiểu sử, Thức tỉnh, Thư từ.
     * **[3/3] Đồ họa ảnh chữ AssetBundles (`StellaSora_AssetBundles_VI.zip` ~92.1 MB)**: Toàn bộ 63 AssetBundles đồ họa.
   - Cơ chế bảo mật: Xác thực mã băm SHA256 từng bundle qua `patch_manifest.json`, chống ghi tràn đường dẫn (path traversal), sao lưu preimage phục hồi an toàn.
   - Hỗ trợ song song cả **Yostar Standalone Client** và **Steam PC (AppID 4813850)**.

---

### 📥 Danh sách tệp tải về:
* **`StellaSora_Launcher_PC.zip` (180.01 MB)**: **[Khuyên dùng]** Gói trọn gói offline đầy đủ nhất (Launcher PC v0.9.6 + Tables ArcX + Scripts ArcX + 63 AssetBundles đồ họa).
* **`StellaSora_AssetBundles_VI.zip` (92.10 MB)**: Trọn bộ 63 AssetBundles ảnh chữ Việt hóa đã vá sẵn.
* **`patch_manifest.json` (0.02 MB)**: Bảng kê khai mã băm SHA256 và kích thước chi tiết của từng bundle phục vụ tự động xác thực.
* **`StellaSora_Launcher.exe` (9.93 MB)**: Trình cập nhật và khởi chạy 1-chạm cho Windows PC (v0.9.6).
* **`data_patched_vi.arcx` (25.80 MB)**: Cơ sở dữ liệu và toàn bộ lời thoại lồng tiếng nhân vật VoiceTable.
* **`lua_patched_vi.arcx` (67.27 MB)**: Kịch bản cốt truyện, ký sự và tin nhắn điện thoại.
* **`StellaSora_Texture_VI.zip` (96.87 MB)**: Bộ tài nguyên 610 ảnh PNG tiếng Việt gốc + Thư viện ảnh HTML Gallery.
* **`StellaSora_VietHoa.apk` (0.03 MB)**: Ứng dụng hỗ trợ Android.
"""

    # Check or create release v0.9.6
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

    # Assets list to upload to v0.9.6
    assets = [
        (root / "dist" / "StellaSora_Launcher_PC.zip", "application/zip"),  # 180 MB
        (root / "dist" / "StellaSora_AssetBundles_VI.zip", "application/zip"),  # 92 MB
        (root / "dist" / "patch_manifest.json", "application/json"),  # 24 KB
        (root / "dist" / "StellaSora_Launcher.exe", "application/vnd.microsoft.portable-executable"),  # 9.9 MB
        (root / "dist" / "data_patched_vi.arcx", "application/octet-stream"),  # 25.8 MB
        (root / "dist" / "lua_patched_vi.arcx", "application/octet-stream"),  # 67.3 MB
        (root / "dist" / "StellaSora_Texture_VI.zip", "application/zip"),  # 96.9 MB
        (root / "android" / "bin" / "StellaSora_VietHoa.apk", "application/vnd.android.package-archive"),  # 0.03 MB
    ]

    for file_path, ctype in assets:
        if file_path.exists():
            upload_asset_to_release(rel, file_path, ctype, headers, repo)
        else:
            print(f"Warning: File not found {file_path}")

    print("\n=== HOÀN TẤT PHÁT HÀNH TÀI NGUYÊN V0.9.6 LÊN GITHUB ===")
    print(f"Release URL: {rel.get('html_url')}")


if __name__ == "__main__":
    main()
