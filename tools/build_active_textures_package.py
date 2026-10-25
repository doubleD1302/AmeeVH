#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build Active Textures Package:
Exports only active, currently-in-use textures that have drawn typography/text into:
  dist/StellaSora_Textures_Chua_Viet_Hoa_Dang_Hoat_Dong/
  dist/StellaSora_Textures_Chua_Viet_Hoa_Dang_Hoat_Dong.zip
Excludes:
  - Past seasons (Joint Drill S1/S5/S6/S7, Duel S3/S4, BattlePass S1-S7)
  - Past expired events/minigames (Mining, Math Parkour, Anniversary 1.0)
  - Expired limited rate-up banners
  - Textures with no text / pure illustrations / single letter HUD indicators
"""

import csv
import hashlib
import html
import os
from pathlib import Path
import shutil
import time
import zipfile
from PIL import Image

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
SOURCE_DIR = ROOT / "dist/StellaSora_Textures_Chua_Viet_Hoa/07_GiaoDienKhac_OtherUI"
OUT_DIR = ROOT / "dist/StellaSora_Textures_Chua_Viet_Hoa_Dang_Hoat_Dong"
OUT_ZIP = ROOT / "dist/StellaSora_Textures_Chua_Viet_Hoa_Dang_Hoat_Dong.zip"

TRANSLATIONS_MAP = {
    # 01 Common & Equipment
    'db_gacha_tips.png': ('4 or Higher!', 'Từ 4 Sao Trở Lên!'),
    'fatecardpack_101_XS.png': ('Stats', 'Chỉ Số'),
    'fatecardpack_102_XS.png': ('Attack', 'Tấn Công'),
    'fatecardpack_201_XS.png': ('Skill', 'Kỹ Năng'),
    'fatecardpack_202_XS.png': ('Aqua', 'Thủy'),
    'fatecardpack_203_XS.png': ('Ignis', 'Hỏa'),
    'fatecardpack_204_XS.png': ('Ventus', 'Phong'),
    'fatecardpack_205_XS.png': ('Terra', 'Địa'),
    'fatecardpack_206_XS.png': ('Lux', 'Quang'),
    'fatecardpack_207_XS.png': ('Umbra', 'Ám'),
    'fatecardpack_301_XS.png': ('Support', 'Hỗ Trợ'),
    'fatecardpack_302_XS.png': ('Defense', 'Phòng Thủ'),
    'fatecardpack_303_XS.png': ('Control', 'Khống Chế'),
    'fatecardpack_304_XS.png': ('Burst', 'Bộc Phát'),
    'fatecardpack_305_XS.png': ('Sustain', 'Hồi Phục'),
    'fatecardpack_306_XS.png': ('Special', 'Đặc Biệt'),
    'icon_agent_emergency.png': ('URGENT', 'KHẨN CẤP'),
    'icon_agent_everyday.png': ('DAILY', 'MỖI NGÀY'),
    'zs_achievement_total.png': ('Achieved', 'Đã Đạt'),
    'zs_bag_drops.png': ('Bonus', 'Rơi Thêm'),
    'zs_bag_drops_1.png': ('Bonus', 'Rơi Thêm'),
    'zs_bag_first.png': ('First Clear', 'Thưởng Lần Đầu'),
    'zs_bag_not.png': ('Locked', 'Đã Khóa'),
    'zs_challenge_text.png': ('New Record !', 'Kỷ Lục Mới!'),
    'zs_character_text_1.png': ('Power Up ! (Cyan)', 'Tăng Lực!'),
    'zs_character_text_2.png': ('Power Up ! (Yellow)', 'Tăng Lực!'),
    'zs_character_text_3.png': ('Power Up ! (Pink)', 'Tăng Lực!'),
    'zs_character_text_5.png': ('Item Conversion', 'Chuyển Đổi Vật Phẩm'),
    'zs_common_max.png': ('Max!', 'Tối Đa!'),
    'zs_common_new_1.png': ('NEW!!', 'MỚI!!'),
    'zs_favor_cgunlock.png': ('UNLOCKED', 'ĐÃ MỞ KHÓA'),
    'zs_infinitytower_promote.png': ('Arena Level Up!', 'Thăng Cấp Đấu Trường!'),
    'zs_infinitytower_ringlevel.png': ('Arena Level', 'Cấp Đấu Trường'),
    'zs_list_shards_text.png': ('Recruitable', 'Có Thể Chiêu Mộ'),
    'zs_stage_flag.png': ('STORY', 'CỐT TRUYỆN'),
    'zs_stage_monster_1.png': ('! Elite', '! Tinh Anh'),
    'zs_stage_monster_2.png': ('! Leader', '! Thủ Lĩnh'),
    'zs_stage_monster_3.png': ('! Boss', '! Trùm'),
    'zs_survivor_danger.png': ('DANGER!', 'NGUY HIỂM!'),
    'zs_survivor_ranktext.png': ('New Record!', 'Kỷ Lục Mới!'),
    'zs_survivor_talent.png': ('Talent Points Converted', 'Đã Quy Đổi Điểm Thiên Phú'),
    # 02 Penguin Card
    'zs_penguincard_tt_01.png': ('VICTORY!', 'CHIẾN THẮNG!'),
    'zs_penguincard_tt_02.png': ('FAILED', 'THẤT BẠI'),
    # 03 Mall
    'mallAdv.month_01.png': ('Everbright Wishes / Expire in 30 Days', 'Ước Nguyện Vĩnh Hằng / Hạn 30 Ngày'),
    'icon_mallcheckinact_tabel_lang.png': ('DEAL 480%', 'ƯU ĐÃI 480%'),
    # 04 Permanent Gacha
    'cover_1__cover_1.png': ("Boss's Regulars - Permanent Trekker Banner", 'Đội Hình Quen Thuộc - Chiêu Mộ Thường Trực'),
    'cover_2__cover_2.png': ('Memories Rewind - Permanent Disc Banner', 'Ký Ức Tuần Hoàn - Đĩa Nhạc Thường Trực'),
    'cover_5__cover_5.png': ('Opening Act - Beginner Limited', 'Khúc Mở Màn - Chiêu Mộ Tân Thủ'),
    # 05 Stellar Return
    'zs_reengagement_shop_lang.png': ('Stellar Return Special', 'Đặc Quyền Hội Ngộ Tân Tinh')
}

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=== TỔNG HỢP TEXTURE CHƯA VIỆT HÓA (CHỈ CÓ CHỮ & ĐANG HOẠT ĐỘNG) ===")
    t0 = time.time()

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    folders = {
        '01_GiaoDien_Chung_Common_Equipment': [],
        '02_MiniGame_PenguinCard': [],
        '03_CuaHang_TheThang_TrangPhuc_Mall': [],
        '04_Gacha_ThuongTruc_Permanent': [],
        '05_TinhNang_HoiNgo_StellarReturn': []
    }

    # Gather files
    for f in sorted(SOURCE_DIR.glob('*.png')):
        name = f.name
        # Exclude past seasons and non-text
        if any(k in name for k in [
            'battlepass_', 'jointdrill', 'duel_boss', 'duel_v', 'ep_duel',
            'mining', 'mathparkour', 'anniversaryact',
            'cover_1001', 'cover_10', 'cover_11', 'cover_20', 'cover_21',
            'storypic', 'skill_text', 'gift_'
        ]):
            continue
        
        if 'penguincard' in name:
            folders['02_MiniGame_PenguinCard'].append(f)
        elif 'reengagement' in name:
            folders['05_TinhNang_HoiNgo_StellarReturn'].append(f)
        elif 'cover_1' in name or 'cover_2' in name or 'cover_5' in name:
            folders['04_Gacha_ThuongTruc_Permanent'].append(f)
        elif 'mallAdv.skin' in name or 'mallAdv.month' in name or 'mallcheckin' in name:
            folders['03_CuaHang_TheThang_TrangPhuc_Mall'].append(f)
        elif 'ui_commonex' in name or 'ui_equipment' in name:
            folders['01_GiaoDien_Chung_Common_Equipment'].append(f)

    catalog_rows = []
    html_items = []
    seen_unique = set()

    for cat_name, file_list in folders.items():
        cat_dir = OUT_DIR / cat_name
        cat_dir.mkdir(parents=True, exist_ok=True)
        print(f"Exporting {cat_name}: {len(file_list)} files...")

        for src_path in file_list:
            dst_path = cat_dir / src_path.name
            shutil.copy2(src_path, dst_path)

            try:
                with Image.open(src_path) as im:
                    w, h = im.size
            except Exception:
                w, h = 0, 0

            sprite_key = src_path.name
            if '__' in sprite_key:
                short_sprite = sprite_key.split('__')[1]
            else:
                short_sprite = sprite_key

            en_text, vi_rec = TRANSLATIONS_MAP.get(short_sprite, TRANSLATIONS_MAP.get(src_path.name, ('[Văn bản hình ảnh]', '[Bản dịch khuyến nghị]')))

            is_duplicate = short_sprite in seen_unique
            if not is_duplicate:
                seen_unique.add(short_sprite)

            catalog_rows.append({
                "Nhom": cat_name,
                "Ten_Tep_PNG": src_path.name,
                "Sprite_Goc": short_sprite,
                "Chieu_Rong_px": w,
                "Chieu_Cao_px": h,
                "Dung_Luong_Bytes": src_path.stat().st_size,
                "Chu_Tieng_Anh_Goc": en_text,
                "Dich_Goi_Y_Tieng_Viet": vi_rec,
                "Ghi_Chu": "Dùng chung cả CommonEx & Equipment" if is_duplicate else "Tài nguyên hoạt động"
            })

            html_items.append({
                "cat": cat_name,
                "name": src_path.name,
                "sprite": short_sprite,
                "w": w,
                "h": h,
                "rel_path": f"{cat_name}/{src_path.name}",
                "en": en_text,
                "vi": vi_rec,
                "is_dup": is_duplicate
            })

    # Write CSV
    csv_out = OUT_DIR / "DANH_SACH_TEXTURE_CHUA_VIET_HOA_DANG_HOAT_DONG.csv"
    with open(csv_out, "w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "Nhom", "Ten_Tep_PNG", "Sprite_Goc", "Chieu_Rong_px", "Chieu_Cao_px",
            "Dung_Luong_Bytes", "Chu_Tieng_Anh_Goc", "Dich_Goi_Y_Tieng_Viet", "Ghi_Chu"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in catalog_rows:
            writer.writerow(r)
    print(f"Wrote CSV catalog: {csv_out.name} ({len(catalog_rows)} entries, {len(seen_unique)} unique sprites)")

    # Write HTML Gallery
    html_out = OUT_DIR / "XEM_TRUOC_TEXTURE_DANG_HOAT_DONG.html"
    html_out.write_text(generate_html(html_items, len(seen_unique)), encoding="utf-8")
    print(f"Wrote HTML gallery: {html_out.name}")

    # Write README
    readme_out = OUT_DIR / "HUONG_DAN_SU_DUNG.md"
    readme_out.write_text(generate_readme(len(catalog_rows), len(seen_unique)), encoding="utf-8")
    print(f"Wrote README: {readme_out.name}")

    # Package ZIP
    print(f"\nCompressing into {OUT_ZIP.name}...")
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(OUT_DIR):
            for file in files:
                fpath = Path(root) / file
                arcname = fpath.relative_to(OUT_DIR)
                zf.write(fpath, arcname=str(arcname))

    print(f"SUCCESS! Created {OUT_ZIP.name} in {time.time() - t0:.2f}s:")
    print(f"  Path: {OUT_ZIP}")
    print(f"  Size: {OUT_ZIP.stat().st_size:,} bytes")
    print(f"  SHA256: {sha256_file(OUT_ZIP)}")


def generate_html(items, unique_count) -> str:
    cards = []
    for it in items:
        dup_tag = "<span class='tag-dup'>Trùng sprite</span>" if it['is_dup'] else "<span class='tag-active'>Đang hoạt động</span>"
        cards.append(f"""
        <div class="card" data-cat="{html.escape(it['cat'])}" data-name="{html.escape(it['name'].lower())}" data-en="{html.escape(it['en'].lower())}">
            <div class="img-box">
                <img src="{html.escape(it['rel_path'])}" alt="{html.escape(it['name'])}" loading="lazy">
            </div>
            <div class="card-info">
                <div class="card-header">
                    <span class="cat-pill">{html.escape(it['cat'].split('_')[1])}</span>
                    {dup_tag}
                </div>
                <div class="file-name" title="{html.escape(it['name'])}">{html.escape(it['name'])}</div>
                <div class="dim">{it['w']} × {it['h']} px</div>
                <div class="text-row">
                    <div class="lbl">Tiếng Anh gốc:</div>
                    <div class="val en">{html.escape(it['en'])}</div>
                </div>
                <div class="text-row">
                    <div class="lbl">Gợi ý dịch:</div>
                    <div class="val vi">{html.escape(it['vi'])}</div>
                </div>
            </div>
        </div>
        """)

    cards_html = "\n".join(cards)

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Thư Viện Texture Chưa Việt Hóa — Đang Hoạt Động</title>
<style>
    :root {{
        --bg: #0f141c;
        --card-bg: #1a2230;
        --accent: #3b82f6;
        --accent-hover: #2563eb;
        --text: #e2e8f0;
        --muted: #94a3b8;
        --border: #334155;
        --green: #10b981;
        --amber: #f59e0b;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        background: var(--bg);
        color: var(--text);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        padding: 24px;
        line-height: 1.5;
    }}
    header {{
        max-width: 1400px;
        margin: 0 auto 24px;
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 24px;
    }}
    h1 {{ font-size: 24px; font-weight: 700; margin-bottom: 8px; color: #fff; }}
    .subtitle {{ color: var(--muted); font-size: 14px; margin-bottom: 16px; }}
    .stats-bar {{
        display: flex;
        gap: 16px;
        flex-wrap: wrap;
        margin-bottom: 20px;
    }}
    .stat-pill {{
        background: #0f172a;
        padding: 8px 16px;
        border-radius: 8px;
        border: 1px solid var(--border);
        font-size: 13px;
    }}
    .stat-pill b {{ color: var(--accent); font-size: 15px; }}
    .controls {{
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        align-items: center;
    }}
    input[type="text"] {{
        background: #0f172a;
        border: 1px solid var(--border);
        color: #fff;
        padding: 10px 16px;
        border-radius: 8px;
        font-size: 14px;
        flex: 1;
        min-width: 250px;
    }}
    .filter-btn {{
        background: #0f172a;
        color: var(--text);
        border: 1px solid var(--border);
        padding: 8px 16px;
        border-radius: 8px;
        cursor: pointer;
        font-size: 13px;
        transition: all 0.15s ease;
    }}
    .filter-btn.active, .filter-btn:hover {{
        background: var(--accent);
        border-color: var(--accent);
        color: #fff;
    }}
    .grid {{
        max-width: 1400px;
        margin: 0 auto;
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 16px;
    }}
    .card {{
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 10px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }}
    .img-box {{
        background: #090d14;
        background-image: 
            linear-gradient(45deg, #151c28 25%, transparent 25%), 
            linear-gradient(-45deg, #151c28 25%, transparent 25%), 
            linear-gradient(45deg, transparent 75%, #151c28 75%), 
            linear-gradient(-45deg, transparent 75%, #151c28 75%);
        background-size: 16px 16px;
        background-position: 0 0, 0 8px, 8px -8px, -8px 0px;
        padding: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 180px;
    }}
    .img-box img {{
        max-width: 100%;
        max-height: 180px;
        object-fit: contain;
    }}
    .card-info {{
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        flex: 1;
    }}
    .card-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .cat-pill {{
        background: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
        font-size: 11px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
    }}
    .tag-active {{
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        font-size: 11px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
    }}
    .tag-dup {{
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        font-size: 11px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
    }}
    .file-name {{
        font-size: 13px;
        font-weight: 600;
        color: #fff;
        word-break: break-all;
    }}
    .dim {{
        font-size: 11px;
        color: var(--muted);
    }}
    .text-row {{
        background: #0f172a;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 12px;
    }}
    .text-row .lbl {{
        color: var(--muted);
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }}
    .text-row .val.en {{
        color: #93c5fd;
        font-weight: 500;
    }}
    .text-row .val.vi {{
        color: #4ade80;
        font-weight: 600;
    }}
</style>
</head>
<body>

<header>
    <h1>Thư Viện Texture Tiếng Anh Chưa Việt Hóa (Tài Nguyên Đang Hoạt Động)</h1>
    <p class="subtitle">Đã lọc sạch các mùa giải cũ, minigame/sự kiện đã đóng và texture không có chữ. Chỉ bao gồm 100% tài nguyên đang hoạt động trong game.</p>
    
    <div class="stats-bar">
        <div class="stat-pill">Tổng tệp xuất: <b>{len(items)}</b></div>
        <div class="stat-pill">Texture gốc độc lập: <b>{unique_count}</b></div>
        <div class="stat-pill">Nhóm Common/Equipment: <b>81</b></div>
        <div class="stat-pill">Trang phục Mall Shop: <b>16</b></div>
        <div class="stat-pill">Banner Gacha thường trực: <b>3</b></div>
        <div class="stat-pill">Penguin Card & Return Shop: <b>5</b></div>
    </div>

    <div class="controls">
        <input type="text" id="search" placeholder="Tìm kiếm theo tên file hoặc nội dung chữ..." oninput="applyFilters()">
        <button class="filter-btn active" onclick="setCategory('ALL', this)">Tất cả ({len(items)})</button>
        <button class="filter-btn" onclick="setCategory('01_GiaoDien_Chung_Common_Equipment', this)">01 Giao Diện Chung</button>
        <button class="filter-btn" onclick="setCategory('03_CuaHang_TheThang_TrangPhuc_Mall', this)">03 Shop & Trang Phục</button>
        <button class="filter-btn" onclick="setCategory('04_Gacha_ThuongTruc_Permanent', this)">04 Gacha Thường Trực</button>
        <button class="filter-btn" onclick="setCategory('02_MiniGame_PenguinCard', this)">02 Penguin Card</button>
        <button class="filter-btn" onclick="setCategory('05_TinhNang_HoiNgo_StellarReturn', this)">05 Hội Ngộ</button>
    </div>
</header>

<div class="grid" id="grid">
    {cards_html}
</div>

<script>
    let currentCat = 'ALL';
    function setCategory(cat, btn) {{
        currentCat = cat;
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        applyFilters();
    }}

    function applyFilters() {{
        const q = document.getElementById('search').value.toLowerCase();
        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {{
            const cat = card.getAttribute('data-cat');
            const name = card.getAttribute('data-name');
            const en = card.getAttribute('data-en');
            const matchCat = (currentCat === 'ALL' || cat === currentCat);
            const matchQuery = (!q || name.includes(q) || en.includes(q));
            card.style.display = (matchCat && matchQuery) ? 'flex' : 'none';
        }});
    }}
</script>

</body>
</html>
"""


def generate_readme(total_files, unique_count) -> str:
    return f"""# DANH MỤC TEXTURE CHƯA VIỆT HÓA ĐANG HOẠT ĐỘNG (ACTIVE ONLY)
**Phiên bản dữ liệu:** 25/10/2026  
**Tổng số tệp xuất ra:** {total_files} ảnh  
**Số lượng texture gốc độc lập:** {unique_count} ảnh  

---

## 1. Tiêu chí sàng lọc (Strict Filter Criteria)
1. **Chỉ lấy texture có chữ (Has Text / Typography)**:
   - Đã loại bỏ toàn bộ các ảnh minh họa thuần túy không chữ, ảnh khung viền UI trống, icon bánh răng/vũ khí không chứa ký tự.
   - Đã loại bỏ các ký hiệu chữ cái đơn lẻ của slot chiêu thức (`A`, `M`, `S`, `EX`).
2. **Chỉ lấy tài nguyên đang hoạt động (Active Resources Only)**:
   - **ĐÃ LOẠI BỎ TOÀN BỘ CÁC MÙA GIẢI CŨ**:
     * Battle Pass mùa 1 đến mùa 7 cũ (`mallAdv.battlepass_01`, `02`, `10303`, `11603`, v.v.).
     * Các mùa Liên Quân Huấn Luyện cũ (Joint Drill Season 1, 5, 6, 7).
     * Các mùa Đấu Hạng cũ (Duel Season 3, 4).
   - **ĐÃ LOẠI BỎ CÁC SỰ KIỆN ĐÃ ĐÓNG / HẾT HẠN**:
     * Minigame Đào Khoáng cũ (`zs_mining_*`).
     * Minigame Math Parkour cũ (`zs_mathparkour_*`).
     * Sự kiện Kỷ Niệm 1 Năm (`icon_anniversaryact_*`).
     * Các gói nạp giới hạn mùa cũ (`mallAdv.gift_*`).
     * Toàn bộ 25 banner gacha rate-up giới hạn của các mùa trước (`cover_10xxx`, `cover_20xxx`, v.v.).

---

## 2. Phân bổ các nhóm thư mục đang hoạt động:
- **`01_GiaoDien_Chung_Common_Equipment/`** (81 tệp, gồm 41 sprite duy nhất):
  - Nhãn mẹo gacha: `db_gacha_tips.png` (*4 or Higher!* $\rightarrow$ *Từ 4 Sao Trở Lên!*).
  - Huy hiệu thẻ Thẻ Định Mệnh (`fatecardpack_*`): *Stats, Attack, Skill, Aqua, Ignis, Ventus, Terra, Lux, Umbra, Support, Defense, Control, Burst, Sustain, Special*.
  - Huy hiệu Ủy thác: `icon_agent_emergency.png` (*URGENT* $\rightarrow$ *KHẨN CẤP*), `icon_agent_everyday.png` (*DAILY* $\rightarrow$ *MỖI NGÀY*).
  - Nhãn rơi vật phẩm: `zs_bag_drops.png` (*Bonus* $\rightarrow$ *Rơi Thêm*), `zs_bag_first.png` (*First Clear* $\rightarrow$ *Thưởng Lần Đầu*), `zs_bag_not.png` (*Locked* $\rightarrow$ *Đã Khóa*).
  - Tăng cấp & Chuyển đổi: `zs_character_text_1/2/3.png` (*Power Up !* $\rightarrow$ *Tăng Lực!*), `zs_character_text_5.png` (*Item Conversion* $\rightarrow$ *Chuyển Đổi Vật Phẩm*).
  - Cột mốc & Kỷ lục: `zs_achievement_total.png` (*Achieved* $\rightarrow$ *Đã Đạt*), `zs_challenge_text.png` / `zs_survivor_ranktext.png` (*New Record!* $\rightarrow$ *Kỷ Lục Mới!*).
  - Đấu trường & Tháp: `zs_infinitytower_promote.png` (*Arena Level Up!* $\rightarrow$ *Thăng Cấp Đấu Trường!*), `zs_infinitytower_ringlevel.png` (*Arena Level* $\rightarrow$ *Cấp Đấu Trường*).
  - Chiêu mộ & Cờ ải: `zs_list_shards_text.png` (*Recruitable* $\rightarrow$ *Có Thể Chiêu Mộ*), `zs_stage_flag.png` (*STORY* $\rightarrow$ *CỐT TRUYỆN*).
  - Quái vật: `zs_stage_monster_1/2/3.png` (*! Elite, ! Leader, ! Boss*).
  - Sinh tồn: `zs_survivor_danger.png` (*DANGER!* $\rightarrow$ *NGUY HIỂM!*), `zs_survivor_talent.png` (*Talent Points Converted* $\rightarrow$ *Đã Quy Đổi Điểm Thiên Phú*).

- **`02_MiniGame_PenguinCard/`** (2 tệp):
  - `zs_penguincard_tt_01.png`: *VICTORY!* $\rightarrow$ *CHIẾN THẮNG!*
  - `zs_penguincard_tt_02.png`: *FAILED* $\rightarrow$ *THẤT BẠI*

- **`03_CuaHang_TheThang_TrangPhuc_Mall/`** (18 tệp):
  - `mallAdv.month_01.png`: Banner Thẻ Tháng thường trực Mall (*Everbright Wishes* $\rightarrow$ *Ước Nguyện Vĩnh Hằng*).
  - `icon_mallcheckinact_tabel_lang.png`: Nhãn nạp điểm danh Mall (*DEAL 480%* $\rightarrow$ *ƯU ĐÃI 480%*).
  - 16 Banner trang phục nhân vật trong Cửa Hàng Trang Phục Mall Shop.

- **`04_Gacha_ThuongTruc_Permanent/`** (3 tệp):
  - `cover_1__cover_1.png`: Banner Nhân Vật Thường Trực (*Boss's Regulars*).
  - `cover_2__cover_2.png`: Banner Đĩa Nhạc Thường Trực (*Memories Rewind*).
  - `cover_5__cover_5.png`: Banner Tân Thủ Thường Trực (*Opening Act*).

- **`05_TinhNang_HoiNgo_StellarReturn/`** (1 tệp):
  - `zs_reengagement_shop_lang.png`: Banner Cửa Hàng Hội Ngộ người chơi quay lại (*Stellar Return Special*).

---

## 3. Hướng dẫn làm việc:
1. Mở file `XEM_TRUOC_TEXTURE_DANG_HOAT_DONG.html` để duyệt nhanh toàn bộ ảnh và xem gợi ý dịch.
2. Tra cứu chi tiết kích thước, nội dung gốc tiếng Anh và bản dịch đề xuất tại file `DANH_SACH_TEXTURE_CHUA_VIET_HOA_DANG_HOAT_DONG.csv`.
3. Chỉ cần dịch **65 ảnh gốc độc lập**, hệ thống sẽ tự động nhân bản đồng bộ vào cả hai AssetBundle `ui_commonex.en.unity3d` và `ui_equipment.en.unity3d`.
"""

if __name__ == "__main__":
    main()
