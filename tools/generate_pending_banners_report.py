import csv
import json
from pathlib import Path
from PIL import Image

ROOT = Path(r"C:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
EXPORT_DIR = ROOT / "dist/Xuat_Texture_Banner_Lon_Chua_Dich"
G01_EN = EXPORT_DIR / "01_Logo_TieuDe_Gacha_Cover/EN"
G02 = EXPORT_DIR / "02_Banner_SuKien_Va_CuaHang"
DELIV = EXPORT_DIR / "01_Logo_TieuDe_Gacha_Cover/deliverables_20261027/StellaSora_Banner_VI_Completed_20261027"

completed_g01 = set([p.name for p in DELIV.glob("*.png")])

# 1. Remaining Gacha Covers (3 items)
pending_gacha = []
for p in sorted(G01_EN.glob("*.png")):
    if p.name not in completed_g01:
        with Image.open(p) as im:
            w, h = im.size
        parts = p.name.replace(".png", "").split("__")
        cid = parts[0].replace("Cover_", "")
        tex_name = parts[1]
        bundle = f"ui_gachacover_cover_{cid.lower()}.en.unity3d"
        note = "Cần bảo toàn thiết kế gốc" if "20162" in p.name else ("Banner Kỷ Niệm 1 Năm" if "1001" in p.name else "Banner Khắc Ấn")
        pending_gacha.append({
            "category": "Gacha Cover (Tiêu đề Banner Chiêu Mộ)",
            "file": p.name,
            "bundle": bundle,
            "tex_name": tex_name,
            "size": f"{w}x{h}",
            "note": note
        })

# 2. Group 02 Items (49 items)
pending_events_mall = []
for p in sorted(G02.glob("*.png")):
    with Image.open(p) as im:
        w, h = im.size
    name = p.name
    # categorize
    if "db_sidestory" in name:
        cat = "Cốt truyện phụ (Side Story)"
        bundle = "ui_activity_advertise.en.unity3d" if "advertise" in name else "ui_activity.en.unity3d"
    elif "duel" in name:
        cat = "Trùm Khiêu Chiến (Duel Boss)"
        bundle = "ui_activity.en.unity3d" if "ui_activity" in name else ("ui_commonex.en.unity3d" if "ui_commonex" in name else "ui_equipment.en.unity3d")
    elif "reengagement" in name:
        cat = "Cửa hàng Tái Xuất (Reengagement Shop)"
        bundle = "ui_activity.en.unity3d"
    elif "battlepass" in name:
        cat = "Sổ Tay Hành Trình (Battle Pass)"
        bundle = "ui_big_sprites.en.unity3d"
    elif "gift" in name:
        cat = "Gói Quà Cửa Hàng (Mall Gift Packs)"
        bundle = "ui_big_sprites.en.unity3d"
    elif "skin" in name:
        cat = "Trang Phục Nhân Vật (Mall Skin Art Text)"
        bundle = "ui_big_sprites.en.unity3d"
    elif "month" in name:
        cat = "Thẻ Tháng (Monthly Pass)"
        bundle = "ui_big_sprites.en.unity3d"
    else:
        cat = "Khác"
        bundle = "ui_big_sprites.en.unity3d"
        
    parts = name.replace(".png", "").split("__")
    tex_name = parts[-1]
    
    pending_events_mall.append({
        "category": cat,
        "file": p.name,
        "bundle": bundle,
        "tex_name": tex_name,
        "size": f"{w}x{h}",
        "note": ""
    })

all_pending = pending_gacha + pending_events_mall
print(f"Total Pending Banner Textures: {len(all_pending)}")

REPORT_MD = ROOT / "reports" / "TONG_HOP_BANNER_TEXTURE_CHUA_VIET_HOA_20261027.md"
REPORT_MD.parent.mkdir(parents=True, exist_ok=True)

with open(REPORT_MD, "w", encoding="utf-8") as f:
    f.write("# BÁO CÁO TỔNG HỢP TOÀN BỘ BANNER TEXTURE CHƯA VIỆT HÓA\n\n")
    f.write(f"**Thời điểm cập nhật:** 27/10/2026  \n")
    f.write(f"**Tổng số banner lớn chưa Việt hóa:** **{len(all_pending)} banner**  \n")
    f.write(f"**Đã hoàn thành và tích hợp:** **25 banner Gacha Cover** (trong `dist/StellaSora_Texture_VI/08_Banner_GachaCover_VI`)\n\n")
    f.write("---\n\n")
    
    # Group by category
    cats = {}
    for item in all_pending:
        cats.setdefault(item["category"], []).append(item)
        
    for cat_name, items in cats.items():
        f.write(f"## {cat_name} ({len(items)} banner)\n\n")
        f.write("| STT | Tên Tệp Nguồn | AssetBundle Mục Tiêu | Tên Texture | Kích Thước | Ghi Chú / Tình Trạng |\n")
        f.write("|:---:|:---|:---|:---|:---:|:---|\n")
        for idx, it in enumerate(items, 1):
            f.write(f"| {idx} | `{it['file']}` | `{it['bundle']}` | `{it['tex_name']}` | `{it['size']}` | {it['note']} |\n")
        f.write("\n")

print(f"✓ Đã xuất báo cáo chi tiết ra: {REPORT_MD}")
