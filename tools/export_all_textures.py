#!/usr/bin/env python3
"""Export all drawn-text textures and sprites from Stella Sora EN bundles (.en.unity3d).

Packages them into a categorized, translation-ready structure with:
1. All PNG images categorized into intuitive directories.
2. Metadata catalog (CSV and JSON).
3. Interactive HTML visual gallery with thumbnails and search.
4. Comprehensive editing and localization guide (Markdown).
5. A single standalone ZIP archive for user distribution.
"""
from __future__ import annotations

import csv
import io
import json
import os
from pathlib import Path
import re
import shutil
import time
import zipfile

import UnityPy
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
BUNDLES_DIR = WORKSPACE_ROOT / "Persistent_Store" / "AssetBundles"
OUTPUT_DIR = PROJECT_ROOT / "work" / "textures" / "export_for_translation"
DIST_DIR = PROJECT_ROOT / "dist"
ZIP_PATH = DIST_DIR / "StellaSora_Texture_AnhVeChu_EN.zip"

CATEGORIES = {
    "01_TruyenTranh_LoadingComics": "Truyện tranh 4 ô màn hình chờ (Loading Comics / Manga)",
    "02_DanhHieu_HonorTitles": "Danh hiệu vinh dự nhân vật / người chơi (Honor Titles)",
    "03_TieuDe_Logos_Headers": "Tiêu đề lớn, Logo chương & Tên tính năng (UI Titles & Logos)",
    "04_NutBam_HuyHieu_Results": "Nút bấm, Huy hiệu Thắng/Thua, Thăng cấp, Nhận thưởng (Buttons & Results)",
    "05_SuKien_Banners_Tabs": "Banner sự kiện, Thẻ hoạt động, Giao diện Chiêu mộ (Banners & Tabs)",
    "06_TrangPhuc_SkinArtText": "Chữ thư pháp nghệ thuật trang phục nhân vật (Skin Art Text)",
    "07_GiaoDienKhac_OtherUI": "Các biểu tượng và chi tiết đồ họa giao diện khác (Other UI)",
    "08_Full_Atlas_Textures": "Bản đồ họa Texture Atlas gốc (SpriteAtlas Language Full Textures)",
}


def classify_sprite(name: str) -> str:
    l = name.lower()
    if "loading_comic" in l or "comic" in l:
        return "01_TruyenTranh_LoadingComics"
    if "honortitle" in l or "honor" in l:
        return "02_DanhHieu_HonorTitles"
    if "charskin" in l or "arttext" in l or "skin_art" in l:
        return "06_TrangPhuc_SkinArtText"
    if any(k in l for k in ["result", "win", "defeat", "victory", "levelup", "complete", "getitem", "btn", "button", "badge", "chargem", "monthlycard"]):
        return "04_NutBam_HuyHieu_Results"
    if any(k in l for k in ["title", "logo", "header", "vestige", "favor_title", "gacha_new", "infinitytower_complete"]):
        return "03_TieuDe_Logos_Headers"
    if any(k in l for k in ["banner", "tab_", "activity", "event"]):
        return "05_SuKien_Banners_Tabs"
    return "07_GiaoDienKhac_OtherUI"


def generate_guide_markdown() -> str:
    return """# Hướng Dẫn Việt Hóa Texture & Ảnh Vẽ Chữ — Stella Sora EN

Chào bạn! Thư mục này tập hợp toàn bộ các tài nguyên hình ảnh có chữ vẽ sẵn (drawn text / typography) được trích xuất trực tiếp từ các file bundle ngôn ngữ `.en.unity3d` của game Stella Sora (bản PC mới nhất).

---

## 1. Cấu Trúc Các Thư Mục

| Thư mục | Số lượng | Mô tả nội dung | Ưu tiên dịch |
|---|---|---|---|
| `01_TruyenTranh_LoadingComics/` | 53 ảnh | Truyện tranh 4 ô loading screen có lời thoại bóng thoại (comic dialogue). | **Rất cao (Người chơi thấy thường xuyên nhất)** |
| `03_TieuDe_Logos_Headers/` | ~105 ảnh | Tiêu đề chương, logo màn chơi, tên tính năng lớn (`zs_vestige_title`, `zs_MonthlyCard_title`,...). | **Rất cao (Giao diện chính)** |
| `04_NutBam_HuyHieu_Results/` | ~104 ảnh | Nút Thắng/Thua, Thăng Cấp (Victory, Defeat, Level Up, Get Item, Complete,...). | **Rất cao (Trải nghiệm combat/nhiệm vụ)** |
| `06_TrangPhuc_SkinArtText/` | 12 ảnh | Chữ thư pháp nghệ thuật trên trang phục đặc biệt của nhân vật. | Trung bình - Cao |
| `05_SuKien_Banners_Tabs/` | ~280 ảnh | Banner sự kiện, thẻ hoạt động, thanh phân loại Gacha/Cửa hàng. | Trung bình |
| `02_DanhHieu_HonorTitles/` | 361 ảnh | Danh hiệu vinh dự (Honor Titles) gắn trên hồ sơ người chơi. | Trung bình |
| `07_GiaoDienKhac_OtherUI/` | ~407 ảnh | Các chi tiết giao diện phụ, khung viền, nhãn nhỏ. | Tùy chọn |
| `08_Full_Atlas_Textures/` | 4 ảnh | Toàn bộ tấm Texture Atlas (`SpriteAtlas_Language`) chứa các sprite ghép lại. | Dành cho ai muốn sửa trực tiếp trên Atlas |

---

## 2. Quy Tắc Khi Chỉnh Sửa Ảnh (Quan Trọng)

1. **Giữ nguyên kích thước ảnh (Resolution / Dimensions)**:
   - File PNG gốc có kích cỡ bao nhiêu (ví dụ `820x600` hoặc `486x194`), khi xuất file đã dịch phải **giữ nguyên 100% kích thước pixel đó**, không được thu nhỏ hay phóng to.
2. **Bảo tồn kênh trong suốt (Alpha Channel / RGBA)**:
   - Các ảnh nút bấm, logo, huy hiệu đều có nền trong suốt. Khi lưu ảnh mới, bắt buộc lưu dưới định dạng **PNG 32-bit (RGBA)**.
3. **Giữ nguyên tên file**:
   - Tên file có dạng `[TênBundle]__[TênSprite].png` (Ví dụ: `icon-0__loading_comic_04.png`).
   - Việc giữ nguyên tên này giúp công cụ tự động nhận diện chính xác vị trí cần đóng gói ngược lại vào game.
4. **Font chữ và Văn phong tiếng Việt**:
   - Nên dùng font chữ hỗ trợ đầy đủ tiếng Việt có dấu (Unicode UTF-8 / NFC), không bị lỗi ô vuông hoặc mất dấu.
   - Các font khuyến nghị cho phong cách Anime RPG:
     - *Truyện tranh (Comics)*: Comic Sans Neue, Manga Temple, CC Wild Words, Anime Ace, Blambot, v.v. (bản việt hóa).
     - *Nút bấm & Tiêu đề (UI/Logo)*: MiSans, Montserrat, Bahnschrift, FOT-Rodin, Bebas Neue việt hóa.
   - Văn phong tự nhiên, hào sảng, giữ đúng thuật ngữ game (Ví dụ: *Victory* → *Thắng Lợi*, *Confirm* → *Xác Nhận*, *Cancel* → *Hủy*).

---

## 3. Cách Tra Cứu Nhanh

- Bạn có thể mở file `DANH_SACH_ANH_VE_CHU.html` bằng trình duyệt web (Chrome, Edge, Cốc Cốc, Firefox) để:
  - Xem ảnh thu nhỏ (thumbnail) trực quan.
  - Tìm kiếm theo tên file hoặc lọc theo từng thư mục phân loại.
  - Bấm vào ảnh để xem kích thước đầy đủ.
- File `DANH_SACH_ANH_VE_CHU.csv` có thể mở bằng Excel để tiện theo dõi tiến độ dịch từng ảnh.

---

## 4. Sau Khi Dịch Xong Thì Làm Gì?

Khi bạn đã vẽ/dịch xong các ảnh mong muốn:
1. Bạn chỉ cần gom các file PNG đã dịch vào một thư mục (ví dụ `work/textures/translated/` hoặc giữ nguyên cấu trúc).
2. Báo lại cho AI Agent: *"Tôi đã vẽ xong các ảnh này, hãy đóng gói ngược lại vào game cho tôi"*.
3. Bộ công cụ `texture_localize.py` của dự án sẽ tự động mã hóa (encode) theo đúng định dạng nén GPU (BC7 / RGBA32) và đưa vào các file `.en.unity3d` trong game một cách an toàn tuyệt đối!

Chúc bạn dịch ảnh vui vẻ và có những tác phẩm thật đẹp mắt!
"""


def generate_html_gallery(items: list[dict]) -> str:
    items_json = json.dumps(items, ensure_ascii=False)
    cats_json = json.dumps(CATEGORIES, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Thư Viện Texture & Ảnh Vẽ Chữ — Stella Sora EN</title>
<style>
  :root {{
    --bg: #0f141c;
    --card-bg: #1a2230;
    --card-border: #2a364a;
    --text: #e6edf3;
    --text-muted: #8b949e;
    --accent: #58a6ff;
    --accent-hover: #79c0ff;
    --tag-bg: #21262d;
    --badge-comic: #f0883e;
    --badge-title: #a371f7;
    --badge-button: #3fb950;
    --badge-banner: #2f81f7;
    --badge-skin: #d29922;
    --badge-honor: #db61a2;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background-color: var(--bg);
    color: var(--text);
    padding: 24px;
    line-height: 1.5;
  }}
  header {{
    max-width: 1400px;
    margin: 0 auto 24px auto;
  }}
  h1 {{
    font-size: 26px;
    font-weight: 700;
    margin-bottom: 8px;
    color: #fff;
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .subtitle {{
    color: var(--text-muted);
    font-size: 14px;
    margin-bottom: 20px;
  }}
  .stats-bar {{
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 20px;
  }}
  .stat-pill {{
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 500;
  }}
  .stat-pill b {{ color: var(--accent); }}
  .controls {{
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 24px;
    align-items: center;
  }}
  .search-box {{
    flex: 1;
    min-width: 280px;
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 8px;
    padding: 10px 14px;
    color: #fff;
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s;
  }}
  .search-box:focus {{ border-color: var(--accent); }}
  .category-filter {{
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 8px;
    padding: 10px 14px;
    color: #fff;
    font-size: 14px;
    outline: none;
    cursor: pointer;
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 16px;
    max-width: 1400px;
    margin: 0 auto;
  }}
  .card {{
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 10px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    transition: transform 0.15s, border-color 0.15s;
  }}
  .card:hover {{
    transform: translateY(-2px);
    border-color: var(--accent);
  }}
  .card-img-wrapper {{
    height: 180px;
    background: repeating-conic-gradient(#141a24 0% 25%, #1e2634 0% 50%) 50% / 16px 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 10px;
    cursor: pointer;
    overflow: hidden;
  }}
  .card-img-wrapper img {{
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    transition: transform 0.2s;
  }}
  .card-img-wrapper:hover img {{
    transform: scale(1.05);
  }}
  .card-body {{
    padding: 12px;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }}
  .card-title {{
    font-size: 13px;
    font-weight: 600;
    color: #fff;
    word-break: break-all;
  }}
  .card-meta {{
    font-size: 11px;
    color: var(--text-muted);
    display: flex;
    flex-direction: column;
    gap: 2px;
  }}
  .badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    width: fit-content;
  }}
  .badge-comic {{ background: rgba(240, 136, 62, 0.2); color: var(--badge-comic); border: 1px solid rgba(240, 136, 62, 0.4); }}
  .badge-title {{ background: rgba(163, 113, 247, 0.2); color: var(--badge-title); border: 1px solid rgba(163, 113, 247, 0.4); }}
  .badge-button {{ background: rgba(63, 185, 80, 0.2); color: var(--badge-button); border: 1px solid rgba(63, 185, 80, 0.4); }}
  .badge-banner {{ background: rgba(47, 129, 247, 0.2); color: var(--badge-banner); border: 1px solid rgba(47, 129, 247, 0.4); }}
  .badge-skin {{ background: rgba(210, 153, 34, 0.2); color: var(--badge-skin); border: 1px solid rgba(210, 153, 34, 0.4); }}
  .badge-honor {{ background: rgba(219, 97, 162, 0.2); color: var(--badge-honor); border: 1px solid rgba(219, 97, 162, 0.4); }}
  .badge-other {{ background: rgba(139, 148, 158, 0.2); color: var(--text-muted); border: 1px solid rgba(139, 148, 158, 0.4); }}

  /* Modal */
  .modal {{
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.85);
    align-items: center;
    justify-content: center;
    padding: 20px;
  }}
  .modal.active {{ display: flex; }}
  .modal-content {{
    max-width: 90vw;
    max-height: 90vh;
    object-fit: contain;
    background: repeating-conic-gradient(#141a24 0% 25%, #1e2634 0% 50%) 50% / 20px 20px;
    border: 2px solid var(--accent);
    border-radius: 8px;
    padding: 10px;
  }}
</style>
</head>
<body>

<header>
  <h1>🖼️ Thư Viện Texture & Ảnh Vẽ Chữ — Stella Sora EN</h1>
  <div class="subtitle">Tổng hợp toàn bộ các hình ảnh vẽ chữ (Texture2D & Sprite) từ các gói .en.unity3d để dịch sang tiếng Việt.</div>
  
  <div class="stats-bar" id="statsBar"></div>

  <div class="controls">
    <input type="text" id="searchInput" class="search-box" placeholder="🔍 Tìm kiếm theo tên file, tên sprite, hoặc tên bundle...">
    <select id="catSelect" class="category-filter">
      <option value="ALL">Tất cả phân loại</option>
    </select>
  </div>
</header>

<div class="grid" id="itemsGrid"></div>

<div class="modal" id="imageModal" onclick="this.classList.remove('active')">
  <img class="modal-content" id="modalImg" alt="Xem ảnh phóng to">
</div>

<script>
  const items = {items_json};
  const categories = {cats_json};

  const grid = document.getElementById('itemsGrid');
  const searchInput = document.getElementById('searchInput');
  const catSelect = document.getElementById('catSelect');
  const statsBar = document.getElementById('statsBar');
  const modal = document.getElementById('imageModal');
  const modalImg = document.getElementById('modalImg');

  // Populate categories
  Object.keys(categories).forEach(cat => {{
    const opt = document.createElement('option');
    opt.value = cat;
    opt.textContent = categories[cat];
    catSelect.appendChild(opt);
  }});

  // Compute category counts
  const catCounts = {{}};
  items.forEach(it => {{
    catCounts[it.category] = (catCounts[it.category] || 0) + 1;
  }});

  // Stats bar
  statsBar.innerHTML = `
    <div class="stat-pill">Tổng số ảnh: <b>${{items.length}}</b></div>
    <div class="stat-pill">Loading Comics: <b>${{catCounts['01_TruyenTranh_LoadingComics'] || 0}}</b></div>
    <div class="stat-pill">Tiêu đề & Logo: <b>${{catCounts['03_TieuDe_Logos_Headers'] || 0}}</b></div>
    <div class="stat-pill">Nút & Kết quả: <b>${{catCounts['04_NutBam_HuyHieu_Results'] || 0}}</b></div>
    <div class="stat-pill">Banner & Tab: <b>${{catCounts['05_SuKien_Banners_Tabs'] || 0}}</b></div>
    <div class="stat-pill">Danh hiệu: <b>${{catCounts['02_DanhHieu_HonorTitles'] || 0}}</b></div>
  `;

  function getBadgeClass(cat) {{
    if (cat.includes('TruyenTranh')) return 'badge-comic';
    if (cat.includes('TieuDe')) return 'badge-title';
    if (cat.includes('NutBam')) return 'badge-button';
    if (cat.includes('SuKien')) return 'badge-banner';
    if (cat.includes('TrangPhuc')) return 'badge-skin';
    if (cat.includes('DanhHieu')) return 'badge-honor';
    return 'badge-other';
  }}

  function render(list) {{
    grid.innerHTML = '';
    if (!list.length) {{
      grid.innerHTML = '<div style="color:var(--text-muted); grid-column: 1/-1; text-align:center; padding: 40px;">Không tìm thấy ảnh nào khớp với bộ lọc.</div>';
      return;
    }}
    const fragment = document.createDocumentFragment();
    list.forEach(item => {{
      const card = document.createElement('div');
      card.className = 'card';
      const badgeCls = getBadgeClass(item.category);
      card.innerHTML = `
        <div class="card-img-wrapper" onclick="openModal('${{item.rel_path}}')">
          <img src="${{item.rel_path}}" alt="${{item.sprite_name}}" loading="lazy">
        </div>
        <div class="card-body">
          <div class="badge ${{badgeCls}}">${{item.category.split('_').slice(1).join(' ')}}</div>
          <div class="card-title" title="${{item.filename}}">${{item.sprite_name}}</div>
          <div class="card-meta">
            <div>📐 Kích thước: <b>${{item.width}} x ${{item.height}}</b></div>
            <div>📦 Bundle: <span>${{item.bundle}}</span></div>
            <div>🏷️ File: <span style="font-family:monospace; font-size:10px;">${{item.filename}}</span></div>
          </div>
        </div>
      `;
      fragment.appendChild(card);
    }});
    grid.appendChild(fragment);
  }}

  function filterItems() {{
    const q = searchInput.value.toLowerCase().trim();
    const selCat = catSelect.value;
    const filtered = items.filter(it => {{
      const matchCat = selCat === 'ALL' || it.category === selCat;
      const matchQuery = !q || it.filename.toLowerCase().includes(q) || it.sprite_name.toLowerCase().includes(q) || it.bundle.toLowerCase().includes(q);
      return matchCat && matchQuery;
    }});
    render(filtered);
  }}

  function openModal(src) {{
    modalImg.src = src;
    modal.classList.add('active');
  }}

  searchInput.addEventListener('input', filterItems);
  catSelect.addEventListener('change', filterItems);

  // Initial render
  render(items);
</script>
</body>
</html>
"""


def main():
    start_time = time.time()
    print("=" * 70)
    print("STELLA SORA EN — TỔNG HỢP VÀ ĐÓNG GÓI TEXTURE ẢNH VẼ CHỮ (.EN.UNITY3D)")
    print("=" * 70)

    if not BUNDLES_DIR.exists():
        print(f"ERROR: Bundles directory not found at {BUNDLES_DIR}")
        return 1

    bundles = sorted(list(BUNDLES_DIR.glob("*.en.unity3d")))
    print(f"-> Tìm thấy {len(bundles)} tệp bundle .en.unity3d trong {BUNDLES_DIR.name}")

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    for cat_dir in CATEGORIES.keys():
        (OUTPUT_DIR / cat_dir).mkdir(parents=True, exist_ok=True)

    extracted_items = []
    total_bundles = len(bundles)
    success_count = 0
    fail_count = 0
    full_atlas_count = 0

    print("-> Bắt đầu trích xuất toàn bộ Sprites và Textures...")
    for idx, bpath in enumerate(bundles, 1):
        bundle_name = bpath.name
        clean_bundle_name = bundle_name.replace(".en.unity3d", "")

        try:
            raw = bpath.read_bytes()
            env = UnityPy.load(raw)
        except Exception as e:
            print(f"[{idx}/{total_bundles}] Lỗi tải bundle {bundle_name}: {e}")
            fail_count += 1
            continue

        sprites = [o for o in env.objects if o.type.name == "Sprite"]
        textures = [o for o in env.objects if o.type.name == "Texture2D"]

        # 1. Extract each Sprite
        for s in sprites:
            try:
                s_obj = s.read()
                s_name = s_obj.m_Name
                img = s_obj.image.convert("RGBA")
                w, h = img.size

                category = classify_sprite(s_name)
                filename = f"{clean_bundle_name}__{s_name}.png"
                out_path = OUTPUT_DIR / category / filename
                rel_path = f"{category}/{filename}"

                img.save(out_path, format="PNG")
                success_count += 1

                extracted_items.append({
                    "category": category,
                    "filename": filename,
                    "bundle": bundle_name,
                    "sprite_name": s_name,
                    "path_id": int(s.path_id),
                    "width": w,
                    "height": h,
                    "rel_path": rel_path,
                })
            except Exception as e:
                fail_count += 1

        # 2. Extract full atlas textures if present (SpriteAtlas_Language)
        for t in textures:
            try:
                t_obj = t.read()
                t_name = t_obj.m_Name
                if "spriteatlas_language" in t_name.lower():
                    img = t_obj.image.convert("RGBA")
                    w, h = img.size
                    category = "08_Full_Atlas_Textures"
                    filename = f"{clean_bundle_name}__Atlas__{t_name}.png"
                    out_path = OUTPUT_DIR / category / filename
                    rel_path = f"{category}/{filename}"

                    img.save(out_path, format="PNG")
                    full_atlas_count += 1

                    extracted_items.append({
                        "category": category,
                        "filename": filename,
                        "bundle": bundle_name,
                        "sprite_name": t_name,
                        "path_id": int(t.path_id),
                        "width": w,
                        "height": h,
                        "rel_path": rel_path,
                    })
            except Exception:
                pass

        if idx % 30 == 0 or idx == total_bundles:
            print(f"   Đã xử lý {idx}/{total_bundles} bundles... ({success_count} sprites, {full_atlas_count} atlases)")

    print(f"\n-> Hoàn tất giải mã: {success_count} sprites và {full_atlas_count} atlas textures thành công ({fail_count} bỏ qua/lỗi).")

    # 3. Write CSV Catalog
    csv_path = OUTPUT_DIR / "DANH_SACH_ANH_VE_CHU.csv"
    print(f"-> Tạo bảng chỉ mục tra cứu CSV: {csv_path.name}")
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Phân loại", "Tên file PNG", "Tệp Bundle nguồn", "Tên Sprite",
            "Path ID", "Chiều rộng (px)", "Chiều cao (px)", "Đường dẫn",
            "Bản dịch tiếng Việt (Ghi chú dịch giả)"
        ])
        for it in extracted_items:
            writer.writerow([
                it["category"],
                it["filename"],
                it["bundle"],
                it["sprite_name"],
                it["path_id"],
                it["width"],
                it["height"],
                it["rel_path"],
                ""
            ])

    # 4. Write JSON Catalog
    json_path = OUTPUT_DIR / "DANH_SACH_ANH_VE_CHU.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(extracted_items, f, ensure_ascii=False, indent=2)

    # 5. Write HTML Gallery
    html_path = OUTPUT_DIR / "DANH_SACH_ANH_VE_CHU.html"
    print(f"-> Tạo giao diện thư viện ảnh HTML trực quan: {html_path.name}")
    html_content = generate_html_gallery(extracted_items)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 6. Write Markdown Guide
    guide_path = OUTPUT_DIR / "HUONG_DAN_DICH_ANH.md"
    print(f"-> Tạo tài liệu hướng dẫn dịch ảnh: {guide_path.name}")
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write(generate_guide_markdown())

    # 7. Create Standalone ZIP Archive
    print(f"\n-> Đang nén toàn bộ thành file ZIP duy nhất: {ZIP_PATH.name}...")
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # Walk output directory and add files
        for root, _, files in os.walk(OUTPUT_DIR):
            for file in files:
                file_full = Path(root) / file
                archive_name = file_full.relative_to(OUTPUT_DIR)
                zf.write(file_full, arcname=archive_name)

    zip_size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    duration = time.time() - start_time

    print("=" * 70)
    print("HOÀN THÀNH XUẤT BẢN THÀNH CÔNG!")
    print(f"📦 File ZIP đích: {ZIP_PATH}")
    print(f"📊 Kích thước gói ZIP: {zip_size_mb:.2f} MB")
    print(f"🖼️ Tổng số ảnh trích xuất: {len(extracted_items)} ảnh")
    print(f"📁 Thư mục mở sẵn trên máy: {OUTPUT_DIR}")
    print(f"⏱️ Tổng thời gian thực hiện: {duration:.1f} giây")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
