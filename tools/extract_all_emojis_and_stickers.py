#!/usr/bin/env python3
"""
Trích xuất toàn bộ emoji, sticker, biểu cảm của game Stella Sora.
Tổng hợp và phân loại chi tiết thành thư mục chuẩn, kèm catalog JSON, HTML gallery và file ZIP.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import zipfile
from PIL import Image
import UnityPy

WORKSPACE_ROOT = Path(r"C:\YostarGames\StellaSora_EN")
PERSISTENT_BUNDLES = WORKSPACE_ROOT / "Persistent_Store" / "AssetBundles"
OUTPUT_DIR = WORKSPACE_ROOT / "StellaSora_Emojis_Stickers"

# Định nghĩa các danh mục
CATEGORIES = {
    "01_Stickers_NhanVat_Chat": {
        "title": "Stickers Nhân Vật Chat Điện Thoại (Phone Chat Emojis)",
        "desc": "Các sticker biểu cảm siêu dễ thương của dàn nhân vật dùng trong hệ thống tin nhắn điện thoại (Phone Chat / Messenger)."
    },
    "02_Anh_Chat_DienThoai": {
        "title": "Ảnh Minh Họa Chat Điện Thoại (Phone Chat Pictures)",
        "desc": "Các hình ảnh, khoảnh khắc và tranh minh họa được gửi qua tin nhắn trong cốt truyện điện thoại."
    },
    "03_BieuCam_AVG_CotTruyen": {
        "title": "Biểu Cảm AVG Cốt Truyện (Visual Novel Dialogue Emojis)",
        "desc": "Các biểu tượng cảm xúc anime xuất hiện trên đầu nhân vật trong các đoạn hội thoại dẫn truyện AVG (giận dữ, ngại ngùng, hoa nở, v.v.)."
    },
    "04_BieuCam_KyTucXa_Dorm": {
        "title": "Biểu Cảm Ký Túc Xá (Dormitory Chibi Emotes & Bubbles)",
        "desc": "Bong bóng biểu cảm và hiệu ứng cảm xúc của nhân vật chibi trong phòng ký túc xá (Dorm)."
    },
    "05_Sticker_SuKien_HoatDong": {
        "title": "Sticker Sự Kiện & Hoạt Động (Event & Activity Stickers)",
        "desc": "Bộ sticker ngoại truyện (Side Story), điểm danh mùa hè, điểm danh hàng ngày, emoji thủ thành Tower Defense và đấu trường Trekker."
    }
}

def get_best_image(ainfo):
    """Lấy PIL Image tốt nhất từ asset info (ưu tiên Sprite nếu là atlas, hoặc Texture2D nếu standalone)."""
    try:
        asset = ainfo.asset.read()
        if hasattr(asset, 'image') and asset.image is not None:
            return asset.image, type(asset).__name__
    except Exception as e:
        pass
    return None, None

def main():
    print("=" * 70)
    print("🚀 BẮT ĐẦU TRÍCH XUẤT TOÀN BỘ EMOJI & STICKER GAME STELLA SORA")
    print("=" * 70)

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for cat_dir in CATEGORIES:
        (OUTPUT_DIR / cat_dir).mkdir(parents=True, exist_ok=True)
    flat_dir = OUTPUT_DIR / "_TongHop_TatCa_Flat"
    flat_dir.mkdir(parents=True, exist_ok=True)

    catalog = []
    extracted_counts = {cat: 0 for cat in CATEGORIES}

    # 1. Trích xuất Phone Chat Emojis & Pictures từ icon-*.unity3d
    print("\n📦 [1/5] Quét các bundle icon-* để lấy Phone Chat Emojis & Pictures...")
    icon_bundles = sorted(PERSISTENT_BUNDLES.glob("icon-*.unity3d"))
    
    # Gom các assets theo container path để tránh xử lý trùng
    icon_assets = {}
    for b in icon_bundles:
        try:
            env = UnityPy.load(str(b))
            for obj in env.objects:
                if obj.type.name == 'AssetBundle':
                    d = obj.read()
                    for cpath, ainfo in d.m_Container:
                        clow = cpath.lower()
                        if 'avgphoneemojimsg' in clow and clow.endswith('.png'):
                            icon_assets.setdefault(cpath, []).append((b.name, ainfo))
                        elif 'avgphoneimagemsg' in clow and clow.endswith('.png'):
                            icon_assets.setdefault(cpath, []).append((b.name, ainfo))
        except Exception as e:
            print(f"Lỗi khi đọc {b.name}: {e}")

    for cpath, entries in sorted(icon_assets.items()):
        fname = Path(cpath).name
        clow = cpath.lower()
        if 'avgphoneemojimsg' in clow:
            cat = "01_Stickers_NhanVat_Chat"
            flat_prefix = "Chat_Emoji"
        else:
            cat = "02_Anh_Chat_DienThoai"
            flat_prefix = "Chat_Pic"

        # Lấy ảnh tốt nhất từ danh sách entries
        best_img = None
        best_type = ""
        source_bname = ""
        # Thử lấy Sprite trước, nếu không được thì Texture2D
        for bname, ainfo in entries:
            img, tname = get_best_image(ainfo)
            if img:
                if tname == 'Texture2D' and best_img is None:
                    best_img, best_type, source_bname = img, tname, bname
                elif tname == 'Texture2D' and (img.size[0] == 180 or img.size[0] == 180):
                    # Ưu tiên Texture2D 180x180 chuẩn không bị crop
                    best_img, best_type, source_bname = img, tname, bname
                    break
                elif best_img is None:
                    best_img, best_type, source_bname = img, tname, bname

        if best_img:
            out_file = OUTPUT_DIR / cat / fname
            best_img.save(out_file, format="PNG")
            
            flat_name = f"{flat_prefix}_{fname}"
            best_img.save(flat_dir / flat_name, format="PNG")

            extracted_counts[cat] += 1
            catalog.append({
                "id": len(catalog) + 1,
                "name": fname,
                "flat_name": flat_name,
                "category": cat,
                "category_title": CATEGORIES[cat]["title"],
                "width": best_img.size[0],
                "height": best_img.size[1],
                "file_size": out_file.stat().st_size,
                "source_bundle": source_bname,
                "container_path": cpath
            })

    print(f"  -> Đã trích xuất {extracted_counts['01_Stickers_NhanVat_Chat']} Chat Emojis và {extracted_counts['02_Anh_Chat_DienThoai']} Chat Pictures.")

    # 2. Trích xuất Story AVG Emojis từ ui_avg.unity3d
    print("\n📦 [2/5] Quét ui_avg.unity3d để lấy Biểu cảm Cốt truyện (AVG AnimEmoji)...")
    cat = "03_BieuCam_AVG_CotTruyen"
    avg_bundle = PERSISTENT_BUNDLES / "ui_avg.unity3d"
    if avg_bundle.exists():
        env = UnityPy.load(str(avg_bundle))
        for obj in env.objects:
            if obj.type.name == 'AssetBundle':
                d = obj.read()
                seen_cpaths = set()
                for cpath, ainfo in d.m_Container:
                    clow = cpath.lower()
                    if 'animemoji' in clow and clow.endswith('.png') and cpath not in seen_cpaths:
                        seen_cpaths.add(cpath)
                        img, tname = get_best_image(ainfo)
                        if img:
                            fname = Path(cpath).name
                            out_file = OUTPUT_DIR / cat / fname
                            img.save(out_file, format="PNG")

                            flat_name = f"AVG_{fname}"
                            img.save(flat_dir / flat_name, format="PNG")

                            extracted_counts[cat] += 1
                            catalog.append({
                                "id": len(catalog) + 1,
                                "name": fname,
                                "flat_name": flat_name,
                                "category": cat,
                                "category_title": CATEGORIES[cat]["title"],
                                "width": img.size[0],
                                "height": img.size[1],
                                "file_size": out_file.stat().st_size,
                                "source_bundle": "ui_avg.unity3d",
                                "container_path": cpath
                            })
    print(f"  -> Đã trích xuất {extracted_counts[cat]} AVG Dialogue Emojis.")

    # 3. Trích xuất Dorm Chibi Emojis từ fx_dorm_emoji_bubble & fx_dorm_emoji_effect
    print("\n📦 [3/5] Quét các bundle fx_dorm_emoji_* để lấy Biểu cảm Ký Túc Xá...")
    cat = "04_BieuCam_KyTucXa_Dorm"
    for bname in ["fx_dorm_emoji_bubble.unity3d", "fx_dorm_emoji_effect.unity3d"]:
        bpath = PERSISTENT_BUNDLES / bname
        if not bpath.exists():
            continue
        env = UnityPy.load(str(bpath))
        for obj in env.objects:
            if obj.type.name == 'AssetBundle':
                d = obj.read()
                seen_cpaths = set()
                for cpath, ainfo in d.m_Container:
                    clow = cpath.lower()
                    if clow.endswith('.png') and cpath not in seen_cpaths:
                        seen_cpaths.add(cpath)
                        img, tname = get_best_image(ainfo)
                        if img:
                            fname = Path(cpath).name
                            out_file = OUTPUT_DIR / cat / fname
                            img.save(out_file, format="PNG")

                            flat_name = f"Dorm_{fname}"
                            img.save(flat_dir / flat_name, format="PNG")

                            extracted_counts[cat] += 1
                            catalog.append({
                                "id": len(catalog) + 1,
                                "name": fname,
                                "flat_name": flat_name,
                                "category": cat,
                                "category_title": CATEGORIES[cat]["title"],
                                "width": img.size[0],
                                "height": img.size[1],
                                "file_size": out_file.stat().st_size,
                                "source_bundle": bname,
                                "container_path": cpath
                            })
    print(f"  -> Đã trích xuất {extracted_counts[cat]} Dorm Chibi Emotes.")

    # 4. Trích xuất Event, Activity & Mini-game Stickers
    print("\n📦 [4/5] Quét các bundle hoạt động & minigame để lấy Stickers & Emoji Stamps...")
    cat = "05_Sticker_SuKien_HoatDong"
    activity_targets = [
        "ui_activity__201015.unity3d",
        "ui_activity_20103.unity3d",
        "ui_activity_towerdefense.unity3d",
        "ui_activity__600004.unity3d",
        "ui_commonex.unity3d",
        "ui_big_sprites.unity3d"
    ]
    seen_fnames = set()
    for bname in activity_targets:
        bpath = PERSISTENT_BUNDLES / bname
        if not bpath.exists():
            continue
        env = UnityPy.load(str(bpath))
        seen_bundle_cpaths = set()
        for obj in env.objects:
            if obj.type.name == 'AssetBundle':
                d = obj.read()
                for cpath, ainfo in d.m_Container:
                    if cpath in seen_bundle_cpaths:
                        continue
                    clow = cpath.lower()
                    if (('sticker' in clow or 'emoji' in clow) and clow.endswith('.png')):
                        seen_bundle_cpaths.add(cpath)
                        fname = Path(cpath).name
                        if fname in seen_fnames and bname != "ui_big_sprites.unity3d":
                            continue
                        
                        img, tname = get_best_image(ainfo)
                        if img:
                            seen_fnames.add(fname)
                            # Nếu trùng tên với bundle khác (như db_phone_emoji), gắn thêm tên bundle
                            save_name = fname
                            if (OUTPUT_DIR / cat / save_name).exists():
                                save_name = f"{Path(bname).stem}_{fname}"
                            
                            out_file = OUTPUT_DIR / cat / save_name
                            img.save(out_file, format="PNG")

                            flat_name = f"Activity_{save_name}"
                            img.save(flat_dir / flat_name, format="PNG")

                            extracted_counts[cat] += 1
                            catalog.append({
                                "id": len(catalog) + 1,
                                "name": save_name,
                                "flat_name": flat_name,
                                "category": cat,
                                "category_title": CATEGORIES[cat]["title"],
                                "width": img.size[0],
                                "height": img.size[1],
                                "file_size": out_file.stat().st_size,
                                "source_bundle": bname,
                                "container_path": cpath
                            })
    print(f"  -> Đã trích xuất {extracted_counts[cat]} Event/Activity Stickers.")

    # 5. Ghi Metadata Catalog JSON
    print("\n📝 [5/5] Đang tạo Catalog JSON, HTML Gallery và file ZIP tổng hợp...")
    manifest_path = OUTPUT_DIR / "catalog.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "game": "Stella Sora",
            "total_items": len(catalog),
            "categories": {k: {"title": v["title"], "count": extracted_counts[k]} for k, v in CATEGORIES.items()},
            "items": catalog
        }, f, indent=2, ensure_ascii=False)

    # Tạo README.md
    readme_path = OUTPUT_DIR / "README.md"
    total_all = len(catalog)
    readme_content = f"""# Bộ Sưu Tập Toàn Bộ Emoji & Sticker Stella Sora

Tổng cộng: **{total_all}** hình ảnh emoji, biểu cảm, tranh vẽ và sticker chất lượng gốc được trích xuất trực tiếp từ dữ liệu game **Stella Sora EN (Ver 2.0.1)**.

---

## 📁 Cấu Trúc Thư Mục

| Thư mục | Số lượng | Mô tả chi tiết |
|---|---|---|
| `01_Stickers_NhanVat_Chat/` | **{extracted_counts['01_Stickers_NhanVat_Chat']}** | Sticker biểu cảm chibi của các nhân vật (Shimiao, Iris, Noya, v.v.) trong tính năng nhắn tin Phone Chat. Định dạng PNG trong suốt (180x180). |
| `02_Anh_Chat_DienThoai/` | **{extracted_counts['02_Anh_Chat_DienThoai']}** | Ảnh minh họa, khoảnh khắc và tranh vẽ nhân vật gửi qua tin nhắn điện thoại. |
| `03_BieuCam_AVG_CotTruyen/` | **{extracted_counts['03_BieuCam_AVG_CotTruyen']}** | Biểu tượng cảm xúc anime hiện trên đầu nhân vật trong lời thoại Visual Novel (giận dữ, ngại ngùng, hoa cười, v.v.). |
| `04_BieuCam_KyTucXa_Dorm/` | **{extracted_counts['04_BieuCam_KyTucXa_Dorm']}** | Bong bóng cảm xúc và hiệu ứng tương tác của nhân vật chibi khi ở ký túc xá. |
| `05_Sticker_SuKien_HoatDong/` | **{extracted_counts['05_Sticker_SuKien_HoatDong']}** | Sticker ngoại truyện (Side Story), điểm danh hàng ngày, emoji thủ thành Tower Defense, v.v. |
| `_TongHop_TatCa_Flat/` | **{total_all}** | Toàn bộ {total_all} ảnh được gom chung vào 1 thư mục phẳng duy nhất với tiền tố phân loại, tiện lợi kéo thả vào Discord/Telegram/Zalo. |

---

## 🎨 Hướng Dẫn Sử Dụng Nhanh

1. **Xem trực quan**: Mở file `index.html` bằng bất kỳ trình duyệt nào (Chrome, Edge, Firefox) để xem toàn bộ phòng trưng bày ảnh, tìm kiếm theo tên hoặc lọc theo thể loại.
2. **Thêm vào Discord / Slack**: Kéo thả ảnh từ thư mục `_TongHop_TatCa_Flat` hoặc `01_Stickers_NhanVat_Chat` vào mục Server Emojis / Stickers.
3. **Tạo Sticker Telegram**: Dùng bot `@Stickers` của Telegram, gửi các file PNG 180x180 từ `01_Stickers_NhanVat_Chat` để tạo sticker pack siêu nét.
4. **Dữ liệu lập trình**: Xem file `catalog.json` để có đầy đủ tọa độ kích thước, đường dẫn gốc và mã phân loại.
"""
    readme_path.write_text(readme_content, encoding="utf-8")

    # Tạo HTML Gallery đẹp mắt
    generate_html_gallery(OUTPUT_DIR / "index.html", catalog, extracted_counts)

    # Đóng gói ZIP
    zip_path = WORKSPACE_ROOT / "StellaSora_Emojis_Stickers.zip"
    print(f"\n📦 Đang nén toàn bộ thành file ZIP tại: {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(OUTPUT_DIR.parent)
                zipf.write(full_path, rel_path)

    zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
    print("\n" + "=" * 70)
    print(f"🎉 HOÀN THÀNH XUẤT SẮC!")
    print(f"📁 Thư mục tổng hợp: {OUTPUT_DIR}")
    print(f"📦 File ZIP: {zip_path} ({zip_size_mb:.2f} MB)")
    print(f"📊 Tổng số emoji & sticker: {total_all} files")
    for cat, count in extracted_counts.items():
        print(f"   • {cat}: {count} files")
    print("=" * 70)

def generate_html_gallery(html_path, catalog, counts):
    """Tạo trang HTML Gallery sang trọng, giao diện anime tối hiện đại."""
    items_json = json.dumps(catalog, ensure_ascii=False)
    
    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stella Sora — Bộ Sưu Tập Emojis & Stickers</title>
    <style>
        :root {{
            --bg-primary: #0f141c;
            --bg-secondary: #182232;
            --bg-card: #1f2c40;
            --accent: #4fc3f7;
            --accent-hover: #81d4fa;
            --text-main: #e8f0fe;
            --text-dim: #9aa8ba;
            --border: #2c3e55;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg-primary);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            padding: 30px 20px;
        }}
        .header {{
            max-width: 1400px;
            margin: 0 auto 30px auto;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.2rem;
            color: #fff;
            margin-bottom: 8px;
            letter-spacing: 0.5px;
        }}
        .header h1 span {{
            color: var(--accent);
        }}
        .header p {{
            color: var(--text-dim);
            font-size: 1.05rem;
        }}
        .stats-bar {{
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 20px auto;
            flex-wrap: wrap;
            max-width: 1200px;
        }}
        .stat-badge {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .stat-badge strong {{
            color: var(--accent);
            font-size: 1.05rem;
        }}
        .controls {{
            max-width: 1200px;
            margin: 0 auto 25px auto;
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            justify-content: center;
            align-items: center;
        }}
        .search-box {{
            flex: 1;
            min-width: 250px;
            max-width: 400px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px 16px;
            color: #fff;
            font-size: 0.95rem;
            outline: none;
        }}
        .search-box:focus {{
            border-color: var(--accent);
        }}
        .filter-btn {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            color: var(--text-dim);
            padding: 9px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s ease;
        }}
        .filter-btn:hover, .filter-btn.active {{
            background: var(--accent);
            color: #0f141c;
            font-weight: 600;
            border-color: var(--accent);
        }}
        .gallery-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 16px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 12px;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
            position: relative;
        }}
        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
            border-color: var(--accent);
        }}
        .img-wrapper {{
            width: 140px;
            height: 140px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(0,0,0,0.25);
            border-radius: 8px;
            margin-bottom: 10px;
            padding: 6px;
        }}
        .img-wrapper img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            image-rendering: auto;
        }}
        .card-name {{
            font-size: 0.85rem;
            font-weight: 500;
            color: var(--text-main);
            word-break: break-all;
            margin-bottom: 4px;
            line-height: 1.2;
        }}
        .card-meta {{
            font-size: 0.75rem;
            color: var(--text-dim);
        }}
        .copy-btn {{
            margin-top: 6px;
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-dim);
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.7rem;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .copy-btn:hover {{
            color: var(--accent);
            border-color: var(--accent);
        }}
        #toast {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: var(--accent);
            color: #000;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 600;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            z-index: 1000;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>✨ <span>Stella Sora</span> — Thư Viện Emojis & Stickers</h1>
        <p>Tổng hợp toàn diện toàn bộ icon biểu cảm, sticker tin nhắn và hình ảnh vui nhộn của game</p>
        <div class="stats-bar">
            <div class="stat-badge">Tổng số: <strong>{len(catalog)}</strong> ảnh</div>
            <div class="stat-badge">💬 Chat Emojis: <strong>{counts['01_Stickers_NhanVat_Chat']}</strong></div>
            <div class="stat-badge">📸 Chat Pics: <strong>{counts['02_Anh_Chat_DienThoai']}</strong></div>
            <div class="stat-badge">📖 Story AVG: <strong>{counts['03_BieuCam_AVG_CotTruyen']}</strong></div>
            <div class="stat-badge">🏠 Ký Túc Xá: <strong>{counts['04_BieuCam_KyTucXa_Dorm']}</strong></div>
            <div class="stat-badge">🎉 Sự Kiện & Hoạt Động: <strong>{counts['05_Sticker_SuKien_HoatDong']}</strong></div>
        </div>
    </div>

    <div class="controls">
        <input type="text" id="search" class="search-box" placeholder="🔍 Tìm kiếm emoji, sticker...">
        <button class="filter-btn active" onclick="filterCategory('all')">Tất cả ({len(catalog)})</button>
        <button class="filter-btn" onclick="filterCategory('01_Stickers_NhanVat_Chat')">Stickers Chat ({counts['01_Stickers_NhanVat_Chat']})</button>
        <button class="filter-btn" onclick="filterCategory('02_Anh_Chat_DienThoai')">Ảnh Chat ({counts['02_Anh_Chat_DienThoai']})</button>
        <button class="filter-btn" onclick="filterCategory('03_BieuCam_AVG_CotTruyen')">Cốt Truyện AVG ({counts['03_BieuCam_AVG_CotTruyen']})</button>
        <button class="filter-btn" onclick="filterCategory('04_BieuCam_KyTucXa_Dorm')">Ký Túc Xá ({counts['04_BieuCam_KyTucXa_Dorm']})</button>
        <button class="filter-btn" onclick="filterCategory('05_Sticker_SuKien_HoatDong')">Sự Kiện & Khác ({counts['05_Sticker_SuKien_HoatDong']})</button>
    </div>

    <div class="gallery-grid" id="gallery"></div>
    <div id="toast">Đã copy tên file!</div>

    <script>
        const items = {items_json};
        let currentCategory = 'all';
        let searchQuery = '';

        function renderGallery() {{
            const container = document.getElementById('gallery');
            container.innerHTML = '';
            
            const filtered = items.filter(item => {{
                const matchCat = (currentCategory === 'all' || item.category === currentCategory);
                const matchSearch = (!searchQuery || item.name.toLowerCase().includes(searchQuery) || item.category_title.toLowerCase().includes(searchQuery));
                return matchCat && matchSearch;
            }});

            filtered.forEach(item => {{
                const card = document.createElement('div');
                card.className = 'card';
                card.innerHTML = `
                    <div class="img-wrapper">
                        <img src="${{item.category}}/${{item.name}}" alt="${{item.name}}" loading="lazy">
                    </div>
                    <div class="card-name">${{item.name}}</div>
                    <div class="card-meta">${{item.width}}×${{item.height}} • ${{(item.file_size/1024).toFixed(1)}} KB</div>
                    <button class="copy-btn" onclick="copyName('${{item.name}}')">Copy tên</button>
                `;
                container.appendChild(card);
            }});
        }}

        function filterCategory(cat) {{
            currentCategory = cat;
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            renderGallery();
        }}

        document.getElementById('search').addEventListener('input', (e) => {{
            searchQuery = e.target.value.toLowerCase().trim();
            renderGallery();
        }});

        function copyName(text) {{
            navigator.clipboard.writeText(text);
            const toast = document.getElementById('toast');
            toast.innerText = 'Đã copy: ' + text;
            toast.style.opacity = '1';
            setTimeout(() => {{ toast.style.opacity = '0'; }}, 1500);
        }}

        renderGallery();
    </script>
</body>
</html>
"""
    html_path.write_text(html, encoding="utf-8")

if __name__ == "__main__":
    main()
