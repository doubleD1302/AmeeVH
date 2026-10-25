#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export Character Card data for the 20 main launch characters to clean CSV files.
Uses UTF-8 with BOM (utf-8-sig) for perfect Excel / Google Sheets compatibility on Windows.
Enriches all tables with original English, Chinese, and full Vietnamese reference translation.
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "dist" / "Du_Lieu_Card_20_Nhan_Vat"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 20 Main Launch Characters
CHAR_20_IDS = [
    '103', '107', '108', '110', '111', '112', '113', '114', '115', '116',
    '117', '118', '119', '120', '123', '125', '126', '127', '130', '132'
]

# Load character roster for names & affiliations
with open(ROOT / "work/character_context_20261023_r02/CHARACTER_ROSTER.json", encoding="utf-8") as f:
    roster_data = json.load(f)

name_map = {}
affil_map = {}
for c in roster_data.get("characters", []):
    cid = str(c.get("game_character_id", ""))
    name_map[cid] = c.get("name_en", "")
    affil_map[cid] = c.get("affiliation_en", "")

print(f"Loaded roster mapping for {len(name_map)} characters.")

# Load master translation cache (76k+ lines)
cache_path = ROOT / "work/batches/pillars_translation_cache.json"
master_cache = {}
if cache_path.exists():
    with open(cache_path, encoding="utf-8") as f:
        master_cache = json.load(f)
    print(f"Loaded master cache: {len(master_cache)} entries.")

# Load original Chinese archive table
cn_arch_map = {}
cn_arch_path = ROOT / "work/research/data_200_pristine_en/entries/00840_0x4a3c44844ee817d1.bin"
if cn_arch_path.exists():
    try:
        cn_arch_map = json.loads(cn_arch_path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        pass

# 1. Export Character Archive & Profile Cards (Hồ sơ thẻ căn cước / Thông tin 20 nhân vật)
arch_proposals_path = ROOT / "work/editorial/character_archives_editorial_20261024_r01/UNIFIED_ARCHIVES_PROPOSALS.jsonl"
arch_rows = []
if arch_proposals_path.exists():
    lines = [json.loads(l) for l in arch_proposals_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    idx = 1
    for l in lines:
        cid = str(l.get("character_id", ""))
        if cid in CHAR_20_IDS:
            key = l.get("id", "")
            en_text = l.get("en", "")
            vi_text = l.get("vi_editorial", "") or master_cache.get(en_text, "")
            cn_text = cn_arch_map.get(key, "")
            
            # Determine field type
            if key.endswith(".1"):
                ftype = "Tiêu đề mục thẻ"
            elif "01.2" in key:
                ftype = "Thẻ căn cước / Thông tin cơ bản"
            elif "02.2" in key:
                ftype = "Lý do trở thành Lữ khách"
            elif any(f"0{x}.2" in key for x in range(3, 10)):
                ftype = "Trích đoạn hồ sơ lý lịch"
            else:
                ftype = "Nội dung thẻ hồ sơ / Truyện"

            arch_rows.append({
                "STT": idx,
                "Character_ID": cid,
                "Character_Name": name_map.get(cid, f"ID_{cid}"),
                "Affiliation": affil_map.get(cid, ""),
                "Key_Game": key,
                "Field_Type": ftype,
                "Original_EN": en_text,
                "Original_CN": cn_text,
                "Current_VI": vi_text,
                "Your_Translation_VI": ""
            })
            idx += 1

print(f"Collected {len(arch_rows)} archive card rows for 20 characters.")

csv_arch_file = OUTPUT_DIR / "01_The_Ho_So_20_Nhan_Vat.csv"
fieldnames_arch = [
    "STT", "Character_ID", "Character_Name", "Affiliation", "Key_Game",
    "Field_Type", "Original_EN", "Original_CN", "Current_VI", "Your_Translation_VI"
]
with open(csv_arch_file, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames_arch)
    writer.writeheader()
    writer.writerows(arch_rows)

print(f"Exported: {csv_arch_file}")

# 2. Export Character Talents Cards (Thẻ Thiên Phú 20 nhân vật)
talent_pairs_path = ROOT / "work/batches/talent_unique_pairs.json"
talent_map_path = ROOT / "tools/build_talent_names_map.py"
talent_vi_map = {}
if talent_map_path.exists():
    import re
    m = re.search(r"TALENT_NAMES_MAP\s*=\s*(\{.*?\n\})", talent_map_path.read_text(encoding="utf-8"), re.DOTALL)
    if m:
        try:
            talent_vi_map = eval(m.group(1))
        except Exception:
            pass

talent_rows = []
if talent_pairs_path.exists():
    with open(talent_pairs_path, encoding="utf-8") as f:
        t_data = json.load(f)
    idx = 1
    for item in t_data:
        skey = item.get("sample_key", "")
        if skey.startswith("Talent."):
            parts = skey.split(".")
            cid = parts[1][:3]
            if cid in CHAR_20_IDS:
                en = item.get("en", "")
                cn = item.get("cn", "")
                ttype = item.get("type", "")
                vi = talent_vi_map.get(en) or master_cache.get(en, "")
                
                ftype = "Tên Thẻ Thiên Phú" if ttype == "name" else "Hiệu ứng Thẻ Thiên Phú"
                talent_rows.append({
                    "STT": idx,
                    "Character_ID": cid,
                    "Character_Name": name_map.get(cid, f"ID_{cid}"),
                    "Key_Game": skey,
                    "Field_Type": ftype,
                    "Original_EN": en,
                    "Original_CN": cn,
                    "Current_VI": vi,
                    "Your_Translation_VI": ""
                })
                idx += 1

print(f"Collected {len(talent_rows)} talent card rows for 20 characters.")

csv_talent_file = OUTPUT_DIR / "02_The_Thien_Phu_20_Nhan_Vat.csv"
fieldnames_talent = [
    "STT", "Character_ID", "Character_Name", "Key_Game",
    "Field_Type", "Original_EN", "Original_CN", "Current_VI", "Your_Translation_VI"
]
with open(csv_talent_file, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames_talent)
    writer.writeheader()
    writer.writerows(talent_rows)

print(f"Exported: {csv_talent_file}")

# 3. Export FateCard (Thẻ Định Mệnh - Leo Tháp Sao)
fc_pairs_path = ROOT / "work/batches/fatecard_pairs.json"
fc_map_path = ROOT / "tools/build_fatecard_names_map.py"
fc_vi_map = {}
if fc_map_path.exists():
    import re
    m = re.search(r"FATECARD_NAMES_MAP\s*=\s*(\{.*?\n\})", fc_map_path.read_text(encoding="utf-8"), re.DOTALL)
    if m:
        try:
            fc_vi_map = eval(m.group(1))
        except Exception:
            pass

fc_rows = []
if fc_pairs_path.exists():
    with open(fc_pairs_path, encoding="utf-8") as f:
        fc_data = json.load(f)
    idx = 1
    for item in fc_data:
        key = item.get("key", "")
        en = item.get("en", "")
        cn = item.get("cn", "")
        ttype = item.get("type", "")
        vi = fc_vi_map.get(en) or master_cache.get(en, "")
        
        ftype = "Tên Thẻ Định Mệnh" if ttype == "name" else "Mô tả Hiệu Ứng Thẻ Định Mệnh"
        fc_rows.append({
            "STT": idx,
            "Key_Game": key,
            "Field_Type": ftype,
            "Original_EN": en,
            "Original_CN": cn,
            "Current_VI": vi,
            "Your_Translation_VI": ""
        })
        idx += 1

print(f"Collected {len(fc_rows)} FateCard rows.")

csv_fc_file = OUTPUT_DIR / "03_The_Dinh_Menh_FateCard_ThapSao.csv"
fieldnames_fc = [
    "STT", "Key_Game", "Field_Type", "Original_EN", "Original_CN", "Current_VI", "Your_Translation_VI"
]
with open(csv_fc_file, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames_fc)
    writer.writeheader()
    writer.writerows(fc_rows)

print(f"Exported: {csv_fc_file}")

# 4. Master Combined CSV for the 20 Characters (Archive + Talents)
master_rows = []
midx = 1
for r in arch_rows:
    master_rows.append({
        "STT": midx,
        "Nhom_The": "Thẻ Hồ Sơ Căn Cước / Tiểu Sử",
        "Character_ID": r["Character_ID"],
        "Character_Name": r["Character_Name"],
        "Key_Game": r["Key_Game"],
        "Field_Type": r["Field_Type"],
        "Original_EN": r["Original_EN"],
        "Original_CN": r["Original_CN"],
        "Current_VI": r["Current_VI"],
        "Your_Translation_VI": ""
    })
    midx += 1

for r in talent_rows:
    master_rows.append({
        "STT": midx,
        "Nhom_The": "Thẻ Thiên Phú Chiến Đấu",
        "Character_ID": r["Character_ID"],
        "Character_Name": r["Character_Name"],
        "Key_Game": r["Key_Game"],
        "Field_Type": r["Field_Type"],
        "Original_EN": r["Original_EN"],
        "Original_CN": r["Original_CN"],
        "Current_VI": r["Current_VI"],
        "Your_Translation_VI": ""
    })
    midx += 1

csv_master_file = OUTPUT_DIR / "TONG_HOP_DU_LIEU_CARD_20_NHAN_VAT.csv"
fieldnames_master = [
    "STT", "Nhom_The", "Character_ID", "Character_Name", "Key_Game",
    "Field_Type", "Original_EN", "Original_CN", "Current_VI", "Your_Translation_VI"
]
with open(csv_master_file, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames_master)
    writer.writeheader()
    writer.writerows(master_rows)

print(f"Exported Master: {csv_master_file} ({len(master_rows)} rows)")

# Write a README guide for the user
readme_path = OUTPUT_DIR / "HUONG_DAN_SU_DUNG.md"
readme_content = """# HƯỚNG DẪN SỬ DỤNG DỮ LIỆU CARD 20 NHÂN VẬT ĐỂ TỰ VIỆT HÓA

Thư mục này chứa toàn bộ dữ liệu thẻ (Card) của **20 nhân vật khởi đầu** trong game Stella Sora, được xuất ra định dạng CSV chuẩn **UTF-8 with BOM** (mở trực tiếp bằng Microsoft Excel, Google Sheets, Notepad++ hoặc VS Code mà không lo lỗi font tiếng Việt).

## 1. Danh sách các file CSV

1. **`01_The_Ho_So_20_Nhan_Vat.csv`** (784 dòng):
   * Thẻ căn cước thông tin cá nhân (Tên, Ngày sinh, Trực thuộc, Sở trường, Vũ khí, v.v.).
   * Thẻ lý do trở thành Lữ khách (Reason for Becoming a Trekker).
   * Thẻ trích đoạn hồ sơ lý lịch (CV Excerpts 1 -> 7).
   * Thẻ truyện và tiểu sử nhân vật.

2. **`02_The_Thien_Phu_20_Nhan_Vat.csv`** (229 dòng):
   * Tên các Thẻ Thiên Phú (Talent Cards) độc quyền của từng nhân vật (ví dụ của Amber: *Vũ Điệu Đạn Lạc, Khói Lửa Nòng Súng, Ký Ức Hư Ảo, Con Đường Thầm Lặng, Vọng Viễn Trời Cao...*).
   * Mô tả hiệu ứng chiến đấu, chỉ số tăng cường của từng thẻ thiên phú.

3. **`03_The_Dinh_Menh_FateCard_ThapSao.csv`** (468 dòng):
   * Thẻ Định Mệnh (FateCard) xuất hiện ngẫu nhiên khi leo Tháp Sao (Star Tower).
   * Gồm Tên thẻ và Mô tả hiệu ứng chọn lựa.

4. **`TONG_HOP_DU_LIEU_CARD_20_NHAN_VAT.csv`** (1,013 dòng):
   * File gộp toàn bộ cả **Thẻ Hồ Sơ** và **Thẻ Thiên Phú** của 20 nhân vật vào một bảng duy nhất để tiện theo dõi toàn diện.

---

## 2. Danh sách 20 nhân vật được trích xuất

| STT | ID Game | Tên Nhân Vật (EN) | Trực Thuộc / Phái (Affiliation) |
| :---: | :---: | :--- | :--- |
| 1 | 103 | **Amber** | New Star Guild (Lữ Đoàn Tân Tinh) |
| 2 | 107 | **Tilia** | Imperial Guard (Cận Vệ Hoàng Gia) |
| 3 | 108 | **Kasimira** | White Cat Troupe (Gánh Xiếc Mèo Trắng) |
| 4 | 110 | **Firenze** | United Harvest (Liên Bang Bội Thu) |
| 5 | 111 | **Iris** | New Star Guild (Lữ Đoàn Tân Tinh) |
| 6 | 112 | **Noya** | New Star Guild (Lữ Đoàn Tân Tinh) |
| 7 | 113 | **Shimiao** | Baize Bureau (Cục Bạch Trạch) |
| 8 | 114 | **Chaton** | White Cat Troupe (Gánh Xiếc Mèo Trắng) |
| 9 | 115 | **Firefly** | Grace Light Academy (Học Viện Ân Quang) |
| 10 | 116 | **Ridge** | United Harvest (Liên Bang Bội Thu) |
| 11 | 117 | **Jinglin** | Fenghuang Diner (Quán Ăn Phượng Hoàng) |
| 12 | 118 | **Coronis** | Freelance Trekker (Lữ Khách Tự Do) |
| 13 | 119 | **Nanoha** | Goodwind Homecare (Dịch Vụ Gia Đình Phong Lành) |
| 14 | 120 | **Canace** | Grace Light Academy (Học Viện Ân Quang) |
| 15 | 123 | **Ann** | Eaze Village Scout Squad (Đội Trinh Sát Làng Eaze) |
| 16 | 125 | **Freesia** | Post Haste (Chuyển Phát Hỏa Tốc) |
| 17 | 126 | **Flora** | Ozora Production (Công Ty Giải Trí Ozora) |
| 18 | 127 | **Teresa** | Post Haste (Chuyển Phát Hỏa Tốc) |
| 19 | 130 | **Donna** | Post Haste (Chuyển Phát Hỏa Tốc) |
| 20 | 132 | **Minova** | Ashwind Clan (Bộ Tộc Tro Gió) |

---

## 3. Hướng dẫn tự dịch & nạp lại vào game

1. **Cách dịch:**
   * Mở file CSV bằng **Microsoft Excel** hoặc **Google Sheets**.
   * Nhìn vào cột **`Original_EN`** (Tiếng Anh) và **`Original_CN`** (Tiếng Trung) để hiểu chính xác nghĩa gốc.
   * Cột **`Current_VI`** là bản dịch hiện tại của dự án để bạn tham khảo.
   * Gõ bản dịch ưng ý của bạn vào cột **`Your_Translation_VI`**. Nếu giữ nguyên câu của dự án, bạn có thể copy từ `Current_VI` sang hoặc để trống (hệ thống sẽ ưu tiên lấy `Your_Translation_VI` trước, nếu trống thì giữ `Current_VI`).
   * **Lưu ý quan trọng:** Không thay đổi giá trị ở cột **`Key_Game`** vì đây là mã định danh để nạp tự động vào game.

2. **Cách nạp vào game sau khi dịch xong:**
   * Sau khi bạn chỉnh sửa và lưu lại file CSV, chỉ cần gửi yêu cầu cho AI (ví dụ: *"hãy nạp file CSV tôi vừa dịch vào game"*), AI sẽ tự động đọc cột `Your_Translation_VI`, đóng gói vào file `data.arcx` và triển khai thẳng vào Steam cho bạn!
"""
readme_path.write_text(readme_content, encoding="utf-8")
print(f"Created documentation: {readme_path}")
print("FINISHED ALL SUCCESSFULLY!")
