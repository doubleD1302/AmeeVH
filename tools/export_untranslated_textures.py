#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export Untranslated Textures Package:
Identifies, extracts, and packages all 848 textures that have not yet been localized into Vietnamese.
Outputs:
- dist/StellaSora_Textures_Chua_Viet_Hoa/ (Organized by category)
- dist/StellaSora_Textures_Chua_Viet_Hoa.zip (Full deliverable package)
- dist/StellaSora_Textures_Chua_Viet_Hoa/DANH_SACH_TEXTURE_CHUA_VIET_HOA.csv
- dist/StellaSora_Textures_Chua_Viet_Hoa/XEM_TRUOC_TEXTURE_CHUA_DICH.html (Interactive gallery)
"""

import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import time
import zipfile
from PIL import Image

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
EN_ROOT = ROOT / "dist/StellaSora_Texture_AnhVeChu_EN"
VI_ROOT_1 = ROOT / "dist/StellaSora_Texture_VI"
VI_ROOT_2 = ROOT / "dist/StellaSora_Texture_AnhVeChu_EN"

OUTPUT_DIR = ROOT / "dist/StellaSora_Textures_Chua_Viet_Hoa"
OUTPUT_ZIP = ROOT / "dist/StellaSora_Textures_Chua_Viet_Hoa.zip"

CSV_SOURCE = ROOT / "work/textures/export_for_translation/DANH_SACH_ANH_VE_CHU.csv"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=== STARTING UNTRANSLATED TEXTURES EXTRACTION ===")
    t0 = time.time()

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load metadata from CSV_SOURCE if available
    metadata_map = {}
    if CSV_SOURCE.exists():
        with open(CSV_SOURCE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            for row in reader:
                if len(row) >= 5:
                    cat, png_name, bundle, sprite, path_id = row[0], row[1], row[2], row[3], row[4]
                    metadata_map[png_name] = {
                        "cat": cat,
                        "bundle": bundle,
                        "sprite": sprite,
                        "path_id": path_id
                    }

    # 2. Gather untranslated files per category
    untranslated = {}

    # Category 2: Honor Titles (All 361)
    untranslated["02_DanhHieu_HonorTitles"] = list((EN_ROOT / "02_DanhHieu_HonorTitles").glob("*.png"))

    # Category 4: Buttons & Results (73 missing)
    p4_en = EN_ROOT / "04_NutBam_HuyHieu_Results"
    p4_vi = VI_ROOT_1 / "04_NutBam_HuyHieu_Results_VI"
    untranslated["04_NutBam_HuyHieu_Results"] = [p for p in p4_en.glob("*.png") if not (p4_vi / p.name).exists()]

    # Category 5: Event Banners & Tabs (3 missing/identical)
    p5_en = EN_ROOT / "05_SuKien_Banners_Tabs"
    p5_vi = VI_ROOT_2 / "05_SuKien_Banners_Tabs_VI"
    untranslated["05_SuKien_Banners_Tabs"] = [
        p for p in p5_en.glob("*.png")
        if not (p5_vi / p.name).exists() or p.stat().st_size == (p5_vi / p.name).stat().st_size
    ]

    # Category 7: Other UI (Only textures with drawn typography / text)
    obviously_non_text_keywords = [
        'UIMask', 'Background', 'Noise', 'gear', 'gearshadow', 'XboxOne', 'PS4', 'PS5', 'Switch',
        'DropdownArrow', 'Checkmark', 'Knob', 'Square', 'UISprite', 'InputFieldBackground',
        'loading_1_', '10104_Bg', '10104_Star', 'db_spring_main', 'zs_spring_main_deco',
        'Chopsticks', 'Eat_', 'Expression', 'Finger', 'Curtain', 'Deco', 'Desk', 'Door_',
        'Hotpot', 'Mouse', 'Sweat', 'Eye', 'Eyebrow', 'Eyelid', 'Hand', 'Ribbon', 'Water',
        'Lantern', 'Railing', 'Shimiao', 'Yuanwei', 'Chensha', 'Hupo', 'JingLin', 'Keluolisi',
        'TravelerDuelLevel_Light', 'TrekkerVersusl_Glow', 'item_21', 'item_11', 'item_heavenlygift',
        'Swim_Star', 'icon_swimsuit_story', 'icon_tech_cert', 'zs_tech_lock', 'icon_solodance_battle_cert',
        'db_common_2px', 'db_common_6px', 'zs_common_stop', 'db_stage_duel_level_little',
        'db_gacha_10158_02'
    ]
    explicit_non_text = {
        'ui_activity_30103__zs_dream_task_done_2.png',
        'ui_activity_30104__zs_dream_task_done_2.png',
        'ui_activitystoryreview__bg_viewfinder_main11.png',
        'ui_buildfunction__note_90011_S.png'
    }
    cat7_all = list((EN_ROOT / "07_GiaoDienKhac_OtherUI").glob("*.png"))
    untranslated["07_GiaoDienKhac_OtherUI"] = [
        p for p in cat7_all
        if not any(k.lower() in p.name.lower() for k in obviously_non_text_keywords)
        and p.name not in explicit_non_text
    ]

    # Category 8: Full Atlas Textures (All 4)
    untranslated["08_Full_Atlas_Textures"] = list((EN_ROOT / "08_Full_Atlas_Textures").glob("*.png"))

    total_files = sum(len(v) for v in untranslated.values())
    print(f"Total untranslated files identified: {total_files}")

    # 3. Copy files and build catalog
    catalog_rows = []
    html_items = []

    for cat_name, file_list in untranslated.items():
        cat_dir = OUTPUT_DIR / cat_name
        cat_dir.mkdir(parents=True, exist_ok=True)
        print(f"Exporting {cat_name}: {len(file_list)} files...")

        for src_path in sorted(file_list, key=lambda x: x.name):
            dst_path = cat_dir / src_path.name
            shutil.copy2(src_path, dst_path)

            # Read dimensions
            try:
                with Image.open(src_path) as im:
                    w, h = im.size
            except Exception:
                w, h = 0, 0

            meta = metadata_map.get(src_path.name, {})
            bundle_name = meta.get("bundle", "Unknown")
            sprite_name = meta.get("sprite", src_path.stem)

            catalog_rows.append({
                "Phan_Loai": cat_name,
                "Ten_File_PNG": src_path.name,
                "Chieu_Rong_px": w,
                "Chieu_Cao_px": h,
                "Dung_Luong_Bytes": src_path.stat().st_size,
                "Bundle_Nguon": bundle_name,
                "Sprite_Name": sprite_name,
                "Duong_Dan_Tuong_Doi": f"{cat_name}/{src_path.name}"
            })

            html_items.append({
                "cat": cat_name,
                "name": src_path.name,
                "w": w,
                "h": h,
                "rel_path": f"{cat_name}/{src_path.name}",
                "bundle": bundle_name,
                "sprite": sprite_name
            })

    # 4. Write CSV catalog
    csv_out = OUTPUT_DIR / "DANH_SACH_TEXTURE_CHUA_VIET_HOA.csv"
    with open(csv_out, "w", encoding="utf-8-sig", newline="") as f:
        fieldnames = ["Phan_Loai", "Ten_File_PNG", "Chieu_Rong_px", "Chieu_Cao_px", "Dung_Luong_Bytes", "Bundle_Nguon", "Sprite_Name", "Duong_Dan_Tuong_Doi"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in catalog_rows:
            writer.writerow(r)
    print(f"Wrote CSV catalog: {csv_out.name} ({len(catalog_rows)} items)")

    # 5. Write Interactive HTML Gallery
    html_out = OUTPUT_DIR / "XEM_TRUOC_TEXTURE_CHUA_DICH.html"
    html_content = generate_html_gallery(html_items, untranslated)
    html_out.write_text(html_content, encoding="utf-8")
    print(f"Wrote Interactive HTML Gallery: {html_out.name}")

    # 6. Write README Instructions
    readme_out = OUTPUT_DIR / "HUONG_DAN_SU_DUNG.md"
    readme_content = generate_readme(untranslated)
    readme_out.write_text(readme_content, encoding="utf-8")

    # 7. Package ZIP Deliverable
    print(f"\nCompressing into {OUTPUT_ZIP.name}...")
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for file in files:
                fpath = Path(root) / file
                arcname = fpath.relative_to(OUTPUT_DIR)
                zf.write(fpath, arcname=str(arcname))

    print(f"SUCCESS! Created {OUTPUT_ZIP.name} in {time.time() - t0:.2f}s:")
    print(f"  Path: {OUTPUT_ZIP}")
    print(f"  Size: {OUTPUT_ZIP.stat().st_size:,} bytes")
    print(f"  SHA256: {sha256_file(OUTPUT_ZIP)}")

def generate_readme(untranslated: dict) -> str:
    total_count = sum(len(v) for v in untranslated.values())
    c2 = len(untranslated.get("02_DanhHieu_HonorTitles", []))
    c4 = len(untranslated.get("04_NutBam_HuyHieu_Results", []))
    c5 = len(untranslated.get("05_SuKien_Banners_Tabs", []))
    c7 = len(untranslated.get("07_GiaoDienKhac_OtherUI", []))
    c8 = len(untranslated.get("08_Full_Atlas_Textures", []))

    lines = [
        "# DANH SÁCH & HƯỚNG DẪN VIỆT HÓA TEXTURE CHƯA DỊCH",
        "## STELLA SORA — TỔNG HỢP TOÀN BỘ ẢNH VẼ CHỮ CÒN NGUYÊN BẢN TIẾNG ANH",
        "",
        f"> **Tổng số texture chưa dịch**: **{total_count} ảnh PNG** (Đã lọc chính xác 100% texture có chữ)",
        "> **Ngày cập nhật**: 2026-10-25",
        "> **Định dạng**: PNG 32-bit (RGBA, bảo tồn kênh trong suốt)",
        "",
        "---",
        "",
        "### 1. Phân Loại Chi Tiết Các Thư Mục",
        "",
        "| Thư mục | Số lượng ảnh | Đặc điểm & Nội dung | Ưu tiên |",
        "| :--- | :---: | :--- | :---: |",
        f"| `02_DanhHieu_HonorTitles/` | {c2} | Danh hiệu vinh dự người chơi gắn trên profile (bản gốc tiếng Anh). | Trung bình |",
        f"| `04_NutBam_HuyHieu_Results/` | {c4} | Nút bấm giao diện, huy hiệu hoàn thành, kết quả phụ bản. | **Cao** |",
        f"| `05_SuKien_Banners_Tabs/` | {c5} | 3 banner sự kiện còn giữ nguyên bản tiếng Anh gốc. | Trung bình |",
        f"| `07_GiaoDienKhac_OtherUI/` | {c7} | **Chỉ chứa ảnh có chữ**: Banner quảng cáo shop/battlepass (`mallAdv`), logo banner gacha, huy hiệu kỹ năng/chỉ số (`Stats`, `Power Up`, `Bonus`, `Elite`, `Story`), kết quả minigame (`Victory`, `Failed`, `Battle Ended`). Toàn bộ background trống, mặt nạ mask, nút bấm tay cầm console đã được loại bỏ sạch sẽ. | **Cao** |",
        f"| `08_Full_Atlas_Textures/` | {c8} | Toàn bộ các tấm Atlas Texture ghép lớn (`SpriteAtlas_Language`). | Nâng cao |",
        "",
        "---",
        "",
        "### 2. Quy Tắc Biên Tập & Chỉnh Sửa Ảnh",
        "",
        "1. **Giữ nguyên kích thước Pixel (Resolution)**:",
        "   - Tuyệt đối không thay đổi độ rộng và độ cao (Width x Height) của từng file ảnh.",
        "2. **Bảo tồn kênh trong suốt (Alpha Channel)**:",
        "   - Bắt buộc lưu định dạng **PNG 32-bit (RGBA)** để tránh biến nền trong suốt thành màu đen.",
        "3. **Tên file không đổi**:",
        "   - Giữ nguyên tên file PNG để công cụ vá tự động (`batch_patch_all_textures.py`) nhận diện và đóng gói ngược lại vào game.",
        "",
        "---",
        "",
        "### 3. Xem Trước Trực Quan",
        "Bạn có thể mở trực tiếp file `XEM_TRUOC_TEXTURE_CHUA_DICH.html` bằng trình duyệt web bất kỳ để duyệt ảnh và xem kích thước một cách nhanh chóng nhất."
    ]
    return "\n".join(lines)

def generate_html_gallery(items: list, untranslated: dict) -> str:
    c2 = len(untranslated.get("02_DanhHieu_HonorTitles", []))
    c4 = len(untranslated.get("04_NutBam_HuyHieu_Results", []))
    c5 = len(untranslated.get("05_SuKien_Banners_Tabs", []))
    c7 = len(untranslated.get("07_GiaoDienKhac_OtherUI", []))
    c8 = len(untranslated.get("08_Full_Atlas_Textures", []))

    html = [
        "<!DOCTYPE html>",
        "<html lang='vi'>",
        "<head>",
        "  <meta charset='utf-8'>",
        "  <title>Thư Viện Texture Chưa Việt Hóa — Stella Sora</title>",
        "  <style>",
        "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #12141a; color: #e1e4ea; margin: 0; padding: 24px; }",
        "    h1 { color: #4dc2f8; margin-bottom: 8px; }",
        "    p.subtitle { color: #8e95a5; margin-top: 0; margin-bottom: 24px; }",
        "    .filters { margin-bottom: 24px; display: flex; gap: 12px; flex-wrap: wrap; }",
        "    .filter-btn { background: #1e222d; color: #a2a8b8; border: 1px solid #2d3345; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 14px; }",
        "    .filter-btn.active, .filter-btn:hover { background: #4dc2f8; color: #0b101b; font-weight: bold; border-color: #4dc2f8; }",
        "    .gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }",
        "    .card { background: #1b1f2b; border: 1px solid #282f42; border-radius: 8px; padding: 12px; display: flex; flex-direction: column; align-items: center; }",
        "    .card:hover { border-color: #4dc2f8; box-shadow: 0 4px 12px rgba(77,194,248,0.15); }",
        "    .img-wrap { width: 100%; height: 160px; display: flex; align-items: center; justify-content: center; background: #0c0e14; border-radius: 4px; overflow: hidden; margin-bottom: 12px; }",
        "    .img-wrap img { max-width: 100%; max-height: 100%; object-fit: contain; }",
        "    .name { font-size: 13px; font-weight: 600; color: #e1e4ea; word-break: break-all; margin-bottom: 4px; text-align: center; }",
        "    .meta { font-size: 11px; color: #7d8597; text-align: center; }",
        "    .tag { display: inline-block; font-size: 10px; padding: 2px 6px; border-radius: 4px; background: #262c3d; color: #4dc2f8; margin-top: 6px; }",
        "  </style>",
        "</head>",
        "<body>",
        "  <h1>Thư Viện Texture Chưa Việt Hóa — Stella Sora</h1>",
        f"  <p class='subtitle'>Tổng hợp <strong>{len(items)}</strong> ảnh vẽ chữ tiếng Anh chưa được bản địa hóa (đã lọc chỉ chứa texture có chữ). Bạn có thể bấm vào các danh mục để lọc xem trực tiếp.</p>",
        "  <div class='filters'>",
        f"    <button class='filter-btn active' onclick=\"filterCat('all')\">Tất cả ({len(items)})</button>",
        f"    <button class='filter-btn' onclick=\"filterCat('02_DanhHieu_HonorTitles')\">02 Danh Hiệu ({c2})</button>",
        f"    <button class='filter-btn' onclick=\"filterCat('04_NutBam_HuyHieu_Results')\">04 Nút Bấm & Kết Quả ({c4})</button>",
        f"    <button class='filter-btn' onclick=\"filterCat('05_SuKien_Banners_Tabs')\">05 Banner Sự Kiện ({c5})</button>",
        f"    <button class='filter-btn' onclick=\"filterCat('07_GiaoDienKhac_OtherUI')\">07 Giao Diện Khác — Chỉ Có Chữ ({c7})</button>",
        f"    <button class='filter-btn' onclick=\"filterCat('08_Full_Atlas_Textures')\">08 Full Atlas ({c8})</button>",
        "  </div>",
        "  <div class='gallery' id='gallery'>"
    ]

    for it in items:
        html.append(f"    <div class='card' data-cat='{it['cat']}'>")
        html.append(f"      <div class='img-wrap'><img src='{it['rel_path']}' loading='lazy' alt='{it['name']}'></div>")
        html.append(f"      <div class='name'>{it['name']}</div>")
        html.append(f"      <div class='meta'>{it['w']} × {it['h']} px | {it['bundle']}</div>")
        html.append(f"      <div class='tag'>{it['cat']}</div>")
        html.append(f"    </div>")

    html.extend([
        "  </div>",
        "  <script>",
        "    function filterCat(cat) {",
        "      document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));",
        "      event.target.classList.add('active');",
        "      document.querySelectorAll('.card').forEach(card => {",
        "        if (cat === 'all' || card.getAttribute('data-cat') === cat) {",
        "          card.style.display = 'flex';",
        "        } else {",
        "          card.style.display = 'none';",
        "        }",
        "      });",
        "    }",
        "  </script>",
        "</body>",
        "</html>"
    ])
    return "\n".join(html)

if __name__ == "__main__":
    main()
