#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publish Release v0.9.7 on GitHub with full 15,224 Light Novel lines & 63 AssetBundles."""

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
            with urllib.request.urlopen(up_req, timeout=180) as resp:
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
    tag = "v0.9.7"
    name = (
        "Stella Sora Việt Hóa v0.9.7 - Đại Bản Doanh Light Novel (15.224 Dòng Thoại) & 63 AssetBundles Đồ Họa"
    )
    body = """### 🌟 Bản phát hành v0.9.7 — Đại Bản Doanh Light Novel & Toàn Bộ Đồ Họa Tiếng Việt

Phiên bản **v0.9.7** là mốc nâng cấp toàn diện nhất của dự án **Stella Sora Việt Hóa**, chính thức tích hợp trọn vẹn **15.224 dòng thoại & ký sự phong cách Light Novel** (252+ phân cảnh) và toàn bộ **63 AssetBundles đồ họa (842 ảnh chữ Việt hóa)**, cùng bản cập nhật Launcher PC v0.9.7 hỗ trợ cơ chế xác thực Manifest, kiểm tra mã băm SHA256 từng tệp, thay thế nguyên tử và tương thích song song cả Yostar Client lẫn Steam PC!

---

### ✨ Những điểm nâng cấp cốt lõi trong phiên bản v0.9.7:

1. **Trọn Bộ 15.224 Dòng Thoại Phong Cách Light Novel (252+ Phân Cảnh Cốt Truyện)**:
   - **Chiến dịch 1 — Cốt truyện Chính & Sự kiện Hẹn Hò (`Story Light Novel`)**: 5.558 dòng thoại (174 cảnh) — Trọn vẹn Hồi 0, Hồi 1, Hồi 2, Tháp Sao và Chuỗi sự kiện hẹn hò của 6 nữ chính đầu tiên (Kasimira, Jinglin, Noya, Minova, Laru, Shia).
   - **Chiến dịch 2 — Tin nhắn Thoại Cá nhân (`Phone Messages`)**: 3.280 dòng thoại (24 cảnh) — Toàn bộ tin nhắn trò chuyện SMS/chat riêng tư của 14 nhân vật với ngữ điệu tự nhiên, hóm hỉnh.
   - **Chiến dịch 3 — Ký Sự Tiểu Sử & Lời Thoại Hồ Sơ (`Character Archives & Lore`)**: 1.662 dòng ký sự thuộc 4 bảng cơ sở dữ liệu (`CharacterArchiveContent`, `CharGetLines`, `Plot`, `StarTowerTalk`). **Khử sạch 100% tàn tích dịch máy "Ma Vương"** (chuyển ngữ chuẩn xác thành Đội trưởng/Sếp/Người chỉ huy), bảo toàn nguyên vẹn mã rich-text sprites (`<sprite...>`).
   - **Chiến dịch 4 — Ký Sự Hẹn Hò & CG Story 18 Nữ Chính Còn Lại (`Character CG Stories`)**: 4.724 dòng thoại (54 cảnh) — Amber (103), Tilia (107), Iris (111), Firefly (115), Coronis (118), Canace (120), Teresa (127), Fuyuka (134), Chitose (144), Firenze (110), Shimiao (113), Chaton (114), Ridge (116), Nanoha (119), Ann (123), Freesia (125), Flora (126), Donna (130). Được QA độc lập thẩm định 100% đạt chuẩn `APPROVED_FOR_RELEASE` (0 Blocker, 0 Major).

2. **Tích Hợp Toàn Bộ 63 AssetBundles Đồ Họa (`.en.unity3d`) (842 Textures)**:
   - **Mục 1 — Truyện Tranh 4 Ô Màn Hình Chờ (`01_TruyenTranh_LoadingComics`)**: 53 / 53 ảnh (100%).
   - **Mục 2 — Danh Hiệu Cá Nhân (`02_DanhHieu_HonorTitles`)**: 361 / 361 danh hiệu (100%) chuẩn 1:1 viền gốc.
   - **Mục 3 — Tiêu Đề Chương & Logo Hoạt Động (`03_TieuDe_Logos_Headers`)**: Khử sạch hiện tượng đè tem (ghosting) trên SpriteAtlas (`ui_commonex`, `ui_equipment`).
   - **Mục 4 — Nút Bấm & Nhãn Chức Năng (`04_NutBam_Buttons`)**: 31 nút chức năng.
   - **Mục 5 — Banners Hoạt Động & Sự Kiện (`05_SuKien_Banners_Tabs`)**: 280 banner sự kiện và tab hoạt động.
   - **Mục 6 — Chữ Nghệ Thuật Trang Phục (`06_TrangPhuc_SkinArtText`)**: 12 chữ nghệ thuật skin.

3. **Nâng Cấp Launcher PC v0.9.7 (Đồng Bộ 3 Tầng & Hỗ Trợ Steam PC)**:
   - Tự động tải và áp dụng đồng bộ cả 3 gói dữ liệu chính:
     * **[1/3] Bảng dữ liệu Tables (`data.arcx` ~25.8 MB)**: Giao diện Core UI, Bách khoa thư, Kỹ năng, Ký sự nhân vật (1.662 dòng).
     * **[2/3] Kịch bản thoại & Tin nhắn (`lua.arcx` ~67.5 MB)**: Toàn bộ 66.224 chuỗi thoại kịch bản đã thay thế, trong đó có 12.554 dòng Light Novel biên tập độc quyền.
     * **[3/3] Đồ họa ảnh chữ AssetBundles (`StellaSora_AssetBundles_VI.zip` ~85.2 MB)**: Trọn vẹn 63 AssetBundles đồ họa.
   - Cơ chế bảo mật: Xác thực mã băm SHA256 từng bundle qua `patch_manifest.json`, chống ghi tràn đường dẫn, sao lưu preimage phục hồi an toàn.
   - Hỗ trợ song song cả **Yostar Standalone Client** và **Steam PC (AppID 4813850)**.

---

### 📥 Danh sách tệp tải về:
* **`StellaSora_Launcher_PC.zip` (271.80 MB)**: **[Khuyên dùng]** Gói trọn gói offline đầy đủ nhất (Launcher PC v0.9.7 + Tables ArcX + Scripts ArcX + Manifest + Toàn bộ 63 AssetBundles đồ họa).
* **`StellaSora_AssetBundles_VI.zip` (85.22 MB)**: Trọn bộ 63 AssetBundles ảnh chữ Việt hóa đã vá sẵn.
* **`patch_manifest.json` (0.02 MB)**: Bảng kê khai mã băm SHA256 và kích thước chi tiết của từng bundle phục vụ tự động xác thực.
* **`StellaSora_Launcher.exe` (9.93 MB)**: Trình cập nhật và khởi chạy 1-chạm cho Windows PC (v0.9.7).
* **`data_patched_vi.arcx` (25.78 MB)**: Cơ sở dữ liệu và toàn bộ lời thoại lồng tiếng nhân vật VoiceTable + Ký sự nhân vật.
* **`lua_patched_vi.arcx` (67.46 MB)**: Kịch bản cốt truyện, ký sự và tin nhắn điện thoại Light Novel.
* **`StellaSora_Character_CG_Stories_VI_20261024_r01.zip` (0.52 MB)**: Gói tư liệu biên dịch 54 cảnh CG Story 18 Nữ chính.
* **`StellaSora_Character_Archives_VI_20261024_r01.zip` (0.34 MB)**: Gói tư liệu biên dịch 1.662 dòng Ký sự & Hồ sơ.
* **`StellaSora_Phone_Messages_VI_20261024_r01.zip` (0.17 MB)**: Gói tư liệu biên dịch 3.280 dòng Tin nhắn điện thoại.
* **`StellaSora_Story_LightNovel_VI_20261024_r02.zip` (0.53 MB)**: Gói tư liệu biên dịch 5.558 dòng Cốt truyện chính.
* **`StellaSora_Texture_VI.zip` (96.87 MB)**: Bộ tài nguyên 610 ảnh PNG tiếng Việt gốc + Thư viện ảnh HTML Gallery.
* **`StellaSora_VietHoa.apk` (0.03 MB)**: Ứng dụng hỗ trợ Android.
"""

    # Check or create release v0.9.7
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

    # Assets list to upload to v0.9.7
    assets = [
        (root / "dist" / "StellaSora_Launcher_PC.zip", "application/zip"),  # 271.8 MB
        (root / "dist" / "StellaSora_AssetBundles_VI.zip", "application/zip"),  # 85.2 MB
        (root / "dist" / "patch_manifest.json", "application/json"),  # 24 KB
        (root / "dist" / "StellaSora_Launcher.exe", "application/vnd.microsoft.portable-executable"),  # 9.9 MB
        (root / "dist" / "data_patched_vi.arcx", "application/octet-stream"),  # 25.8 MB
        (root / "dist" / "lua_patched_vi.arcx", "application/octet-stream"),  # 67.5 MB
        (root / "dist" / "StellaSora_Character_CG_Stories_VI_20261024_r01.zip", "application/zip"),  # 0.52 MB
        (root / "dist" / "StellaSora_Character_Archives_VI_20261024_r01.zip", "application/zip"),  # 0.34 MB
        (root / "dist" / "StellaSora_Phone_Messages_VI_20261024_r01.zip", "application/zip"),  # 0.17 MB
        (root / "dist" / "StellaSora_Story_LightNovel_VI_20261024_r02.zip", "application/zip"),  # 0.53 MB
        (root / "dist" / "StellaSora_Texture_VI.zip", "application/zip"),  # 96.9 MB
        (root / "android" / "bin" / "StellaSora_VietHoa.apk", "application/vnd.android.package-archive"),  # 0.03 MB
    ]

    for file_path, ctype in assets:
        if file_path.exists():
            upload_asset_to_release(rel, file_path, ctype, headers, repo)
        else:
            print(f"Warning: File not found {file_path}")

    print("\n=== HOÀN TẤT PHÁT HÀNH TÀI NGUYÊN V0.9.7 LÊN GITHUB ===")
    print(f"Release URL: {rel.get('html_url')}")

if __name__ == "__main__":
    main()
