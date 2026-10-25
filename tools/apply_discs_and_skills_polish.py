#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master Application Script: Discs & Skills Polish & Synchronization
Applies polished, elegant anime-style translations for:
- 37 Runic Discs across DiscIP, Item, ActivityGoods, ResidentGoods
- 37 Skills across Skill, MainSkill, SecondarySkill, Potential, MathParkourBuffItem
Repacks data.arcx, dual-syncs to Standalone and Steam, and updates manifests.
"""

import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT))
from tools.arcx_adapter import ArcxArchive, repack_archive

ENTRIES_DIR = ROOT / "work" / "research" / "data_200_decrypted" / "entries"
DEC_DIR = ROOT / "work" / "research" / "data_200_decrypted"
OUTPUT_ARCX = ROOT / "dist" / "data_patched_vi.arcx"

TABLE_FILES = {
    "DiscIP": "00620_0x1f924138769d46ec.bin",
    "Item": "00653_0xe60634348b826f41.bin",
    "MainSkill": "00667_0x57e760255c1d3b2d.bin",
    "SecondarySkill": "00715_0x31a8814a91313129.bin",
    "Skill": "00716_0x998f849a64309b25.bin",
    "Potential": "00704_0x02ce11eca01b5fc8.bin",
    "Talent": "00764_0x3f0bd5f8db2389b6.bin",
    "ActivityGoods": "00557_0x988f7b6f2592bacd.bin",
    "MathParkourBuffItem": "00677_0x5a83026d964c9848.bin",
    "ResidentGoods": "00711_0x16665e9556f7d213.bin"
}

DISC_EXPLICIT = {
    211001: "Sớm Mai Trong Lành",
    211005: "Cồn Cát Hoang Vắng",
    211006: "Dòng Suối Ngọt Ngào",
    212002: "Reo Vui Náo Nhiệt",
    212005: "Ngọn Lửa Nồng Nhiệt",
    212007: "Cưỡi Gió Vút Bay",
    213001: "Hiếu Kỳ Tươi Vui",
    213010: "Say Làn Hơi Nước",
    213013: "Thì Thầm Mùa Thu",
    213017: "★Vòng Quay Cuộc Đời★",
    213021: "Tụng Ca Màu Nhiệm",
    213022: "Lời Nguyền Bến Yêu",
    213026: "Xả Hết Muộn Phiền ♥",
    214001: "Khúc Ca Miêu Thần",
    214003: "Hạt Mầm Tri Kỷ",
    214007: "Vút Bay Giữa Trời Xanh",
    214013: "Tiếng Hươu Gọi Đàn",
    214022: "Chuông Mèo Nửa Đêm",
    214026: "Kiếm Rẽ Làn Sóng",
    214027: "Rồng Bay Phượng Múa",
    214028: "Khu Vườn Ngập Nắng",
    214029: "Kho Báu Mèo Con",
    214031: "Đao Rìu Tranh Hùng",
    214032: "Xưởng Mộng ☆Chân Lý",
    214033: "Vũ Điệu Cùng Bạch Cốt",
    214036: "Kẻ Hành Hương Lạc Bước",
    214037: "Bắt Trọn Huyền Thoại",
    214040: "Quyền Năng Dũng Khí",
    214042: "Rượu Ấm Đèn Hoa",
    214044: "Sớm Xuân Bừng Tỉnh",
    214047: "Cánh Thư Bay Theo Gió",
    214050: "Bóng Hình Dạ Yến",
    214056: "Bóng Nắng Chiều Hè",
    214058: "Hành Khúc Mùa Hè",
    214059: "Bay Đi, Chim Trong Lồng",
    214061: "Cổ Tích Trước Giờ Ngủ",
    214066: "Khải Minh Dẫn Lối",
    214067: "Rực Rỡ Vĩnh Hằng"
}

TERM_REPLACEMENTS = [
    # Character skills and skill trees
    ("Ném Chuột Chuột", "Ném Chuột Chù"),
    ("Minh Ước Chuột Chuột", "Khế Ước Chuột Chù"),
    ("Bom Bồm Bộp", "Bom Bùm Bụp"),
    ("Trị Liệu Bồm Bộp", "Trị Liệu Bùm Bụp"),
    ("Đạo Tiêu Sương Giá", "Hàn Băng Lộ"),
    ("Kiên Băng Dũng Trận", "Băng Trụ Bùng Nổ"),
    ("Diệu Tinh Truy Lạp", "Sao Băng Truy Kích"),
    ("Trần Phong Chi Tinh", "Tinh Cầu Gió Cát"),
    ("Lạc Anh Tân Phấn", "Mưa Hoa Rực Rỡ"),
    ("Tật Bộ Xung Quyền", "Quyền Năng Bộc Phát"),
    ("Cối Xay Gió Nhào Lộn", "Bungee Nhào Lộn"),
    ("Thoáng Thác Đổ", "Thủy Triều Dâng Trào"),
    ("Địa Ngục Gai Góc", "Hỏa Ngục Gai Nhọn"),
    ("Bích Ba Luân Tấu", "Khúc Luân Tấu Lướt Sóng"),
    ("Món Quà Của Mèo", "Mèo Con Trao Quà"),
    ("Trị Liệu Của Mèo", "Mèo Con Trị Liệu"),
    ("Bảo Hộ Của Mèo", "Mèo Con Che Chở"),
    ("Né Tránh Của Eleanor", "Eleanor Né Tránh"),
    ("Lướt Nhanh Của Eleanor", "Eleanor Lướt Nhanh"),
    ("Áp Chế Toàn Diện Của Thỏ", "Bão Đạn Thỏ Con"),
    ("Cảnh Tử Vong", "Khúc Tử Điệu"),
    ("Thiên Thần Sa Ngã Nhịp Điệu", "Giai Điệu Seraphim"),
    ("Săn Bắn Đặc Biệt Đánh Thường", "Đòn Đánh Thường: Thợ Săn"),
    ("Lò Tháp - Đi Dạo", "Lò Tháp: Tuần Tra"),
    ("Hương Chanh Tò Mò", "Hiếu Kỳ Tươi Vui"),
    ("Kho Báu Của Mèo Con", "Kho Báu Mèo Con"),
    ("Kho Báu Của Mèo", "Kho Báu Mèo Cưng"),
    ("Kẻ Hành Hương Lạc Lối", "Kẻ Hành Hương Lạc Bước"),
    ("Bay Đi, Chú Chim Trong Lồng", "Bay Đi, Chim Trong Lồng"),
    ("Bôi Trơn Động Cơ", "Tiếp Dầu Động Cơ"),
    ("Thấu Tâm Lạnh Giá", "Lạnh Thấu Tâm Can"),
    ("Khoảnh Khắc Giật Mình", "Khoảnh Khắc Bất Ngờ"),
    ("Thục Huệ Bản Sắc", "Nết Na Thục Nữ"),
    ("Dường Như Hôm Qua", "Ngỡ Như Hôm Qua"),
    ("Gió Nhẹ Chảy Trong Mộng", "Gió Thoảng Miền Mộng Ảo"),
    ("Giam Hãm Trong Men Tình", "Ngục Tù Men Tình"),
    ("Nhiệt Huyết Của Đoàn Trưởng", "Nhiệt Huyết Đoàn Trưởng"),
    ("Hoa Nở Cũng Cần Dưỡng Nuôi", "Hoa Nở Cần Nắng Dưỡng"),

    # Disc phrases in Item, shops and descriptions
    ("buổi sáng sắc nét", "Sớm Mai Trong Lành"),
    ("Cồn cát cô đơn", "Cồn Cát Hoang Vắng"),
    ("Lạch Ngọt", "Dòng Suối Ngọt Ngào"),
    ("ôi chao", "Reo Vui Náo Nhiệt"),
    ("bùng cháy điên cuồng", "Ngọn Lửa Nồng Nhiệt"),
    ("Dũng cảm với gió", "Cưỡi Gió Vút Bay"),
    ("Lá cô ấy cho tôi", "Thì Thầm Mùa Thu"),
    ("Quốc ca kỳ diệu", "Tụng Ca Màu Nhiệm"),
    ("Thần Mèo Kêu Meo Meo", "Khúc Ca Miêu Thần"),
    ("Thần mèo meo meo", "Khúc Ca Miêu Thần"),
    ("Hạt giống tương tự", "Hạt Mầm Tri Kỷ"),
    ("Tăng vọt màu xanh lam", "Vút Bay Giữa Trời Xanh"),
    ("Tiếng Hát Chú Hươu", "Tiếng Hươu Gọi Đàn"),
    ("Bài hát của hươu", "Tiếng Hươu Gọi Đàn"),
    ("Mèo mèo", "Chuông Mèo Nửa Đêm"),
    ("Kiếm Ngược Dòng Nước", "Kiếm Rẽ Làn Sóng"),
    ("Kiếm Ngược Dòng", "Kiếm Rẽ Làn Sóng"),
    ("Nét Cọ Thần Kỳ", "Rồng Bay Phượng Múa"),
    ("Nét vẽ huyền bí", "Rồng Bay Phượng Múa"),
    ("Khu Vườn Ban Ngày", "Khu Vườn Ngập Nắng"),
    ("Vườn Ánh Sáng Ban Ngày", "Khu Vườn Ngập Nắng"),
    ("Đao Rìu Chạm Nhau", "Đao Rìu Tranh Hùng"),
    ("Cuộc đụng độ của lưỡi kiếm và rìu", "Đao Rìu Tranh Hùng"),
    ("Nhà máy mơ ước của ☆Sự thật", "Xưởng Mộng ☆Chân Lý"),
    ("Vũ Điệu Với Khung Xương", "Vũ Điệu Cùng Bạch Cốt"),
    ("Khiêu vũ với xương", "Vũ Điệu Cùng Bạch Cốt"),
    ("Người hành hương lạc lối", "Kẻ Hành Hương Lạc Bước"),
    ("Vuốt Móng Đọ Vuốt Móng", "Bắt Trọn Huyền Thoại"),
    ("Vuốt móng vuốt", "Bắt Trọn Huyền Thoại"),
    ("Nắm Đấm Của Lòng Dũng Cảm", "Quyền Năng Dũng Khí"),
    ("Rượu ấm, đèn xuống", "Rượu Ấm Đèn Hoa"),
    ("Rượu Ấm, Đèn Lên", "Rượu Ấm Đèn Hoa"),
    ("Bình minh che khuất của mùa xuân", "Sớm Xuân Bừng Tỉnh"),
    ("Sớm Mai Mùa Xuân Mờ Ảo", "Sớm Xuân Bừng Tỉnh"),
    ("Được cung cấp bởi Breeze", "Cánh Thư Bay Theo Gió"),
    ("Gió Nhắn Lời Yêu", "Cánh Thư Bay Theo Gió"),
    ("Bóng Ma Bữa Tiệc", "Bóng Hình Dạ Yến"),
    ("Bóng ma của bữa tiệc", "Bóng Hình Dạ Yến"),
    ("Ánh nắng lốm đốm", "Bóng Nắng Chiều Hè"),
    ("Vạt Nắng Lung Linh", "Bóng Nắng Chiều Hè"),
    ("Mùa hè tháng ba", "Hành Khúc Mùa Hè"),
    ("Bay Đi, Chú Chim Nhỏ", "Bay Đi, Chim Trong Lồng"),
    ("Bay đi hỡi chú chim trong lồng", "Bay Đi, Chim Trong Lồng"),
    ("Chuyện Cổ Tích Đêm Muộn", "Cổ Tích Trước Giờ Ngủ"),
    ("Chuyện Kể Đêm Khuya", "Cổ Tích Trước Giờ Ngủ"),
    ("Câu chuyện trước khi đi ngủ", "Cổ Tích Trước Giờ Ngủ"),
    ("Khải Minh Tinh Dẫn Lối", "Khải Minh Dẫn Lối"),
    ("Ánh Hào Quang Vĩnh Cửu", "Rực Rỡ Vĩnh Hằng"),
    ("★Cuộc Sống Lăn Lộn★", "★Vòng Quay Cuộc Đời★"),
    ("★Cuộc sống lăn lộn★", "★Vòng Quay Cuộc Đời★"),
    ("Lời Nguyền Dòng Sông Yêu", "Lời Nguyền Bến Yêu"),
    ("Lời nguyền dòng sông tình yêu", "Lời Nguyền Bến Yêu"),
    ("Xả Hết Đi Nào ♥", "Xả Hết Muộn Phiền ♥"),
    ("Hãy trút giận ♥", "Xả Hết Muộn Phiền ♥")
]

# Ensure longer phrases are matched first
TERM_REPLACEMENTS.sort(key=lambda x: len(x[0]), reverse=True)


def main():
    print("==================================================================")
    print("STARTING STELLA SORA DISCS & SKILLS POLISH APPLICATION PIPELINE")
    print("==================================================================")

    total_modified_strings = 0
    table_stats = {}

    for tname, fname in TABLE_FILES.items():
        fpath = ENTRIES_DIR / fname
        if not fpath.exists():
            print(f"Warning: {fname} ({tname}) not found!")
            continue

        data = json.loads(fpath.read_text(encoding="utf-8"))
        mod_count = 0

        # 1. Explicit Disc Updates
        if tname == "DiscIP":
            for did, new_name in DISC_EXPLICIT.items():
                k = f"DiscIP.{did}.3"
                if k in data and data[k] != new_name:
                    data[k] = new_name
                    mod_count += 1
        elif tname == "Item":
            for did, new_name in DISC_EXPLICIT.items():
                k = f"Item.{did}.1"
                if k in data and data[k] != new_name:
                    data[k] = new_name
                    mod_count += 1

        # 2. General Term Replacements Across All Keys
        for k, v in list(data.items()):
            if not isinstance(v, str):
                continue
            v_new = v
            for old_term, new_term in TERM_REPLACEMENTS:
                if old_term in v_new:
                    v_new = v_new.replace(old_term, new_term)
            if v_new != v:
                data[k] = v_new
                mod_count += 1

        fpath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        table_stats[tname] = mod_count
        total_modified_strings += mod_count
        print(f"[{tname}] ({fname}): Successfully updated {mod_count} entries.")

    print("------------------------------------------------------------------")
    print(f"Total Database Modifications: {total_modified_strings} strings across {len(TABLE_FILES)} tables.")
    print("------------------------------------------------------------------")

    # Step 2: Repack data.arcx with XXTEA encryption
    print("\nRepacking data.arcx with XXTEA payload encryption...")
    repack_archive(DEC_DIR, OUTPUT_ARCX, encrypt_payload=True)

    arc = ArcxArchive(OUTPUT_ARCX)
    arcx_size = OUTPUT_ARCX.stat().st_size
    with open(OUTPUT_ARCX, "rb") as f:
        arcx_sha256 = hashlib.sha256(f.read()).hexdigest()

    print(f"Repack successful!")
    print(f"  File: {OUTPUT_ARCX}")
    print(f"  Size: {arcx_size:,} bytes")
    print(f"  Entries: {len(arc.entries)}")
    print(f"  SHA-256: {arcx_sha256}")

    # Step 3: Dual-Sync to Live Games
    dests = [
        ROOT / "work" / "research" / "data_patched_vi.arcx",
        Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx"),
        Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Tables\data.arcx")
    ]

    print("\nDeploying to live environments...")
    for d in dests:
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(OUTPUT_ARCX, d)
        print(f"  -> Deployed {d.stat().st_size:,} bytes to: {d}")

    # Step 4: Update patch manifest
    manifest_file = ROOT / "dist" / "patch_manifest.json"
    if manifest_file.exists():
        p_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        for item in p_manifest.get("files", []):
            if item.get("path") == "Persistent_Store/Tables/data.arcx":
                item["size"] = arcx_size
                item["sha256"] = arcx_sha256
        manifest_file.write_text(json.dumps(p_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nUpdated {manifest_file} with new data.arcx checksum.")

    # Step 5: Update STATUS.json and CHECKPOINT.json
    status_file = ROOT / "STATUS.json"
    if status_file.exists():
        st = json.loads(status_file.read_text(encoding="utf-8"))
        st["updated_local_date"] = time.strftime("%Y-%m-%d")
        st["discs_and_skills_polish"] = {
            "applied_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "discs_polished_count": len(DISC_EXPLICIT),
            "skills_and_terms_polished_count": len(TERM_REPLACEMENTS),
            "total_database_modifications": total_modified_strings,
            "data_arcx_sha256": arcx_sha256,
            "data_arcx_size": arcx_size,
            "live_sync": "synchronized_standalone_and_steam"
        }
        status_file.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Updated STATUS.json.")

    checkpoint_file = ROOT / "CHECKPOINT.json"
    if checkpoint_file.exists():
        cp = json.loads(checkpoint_file.read_text(encoding="utf-8"))
        cp["updated_local_date"] = time.strftime("%Y-%m-%d")
        cp["last_polish_batch"] = "DISCS_AND_SKILLS_POLISH_37_DISCS_37_SKILLS"
        checkpoint_file.write_text(json.dumps(cp, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Updated CHECKPOINT.json.")

    print("\n==================================================================")
    print("ALL DISCS AND SKILLS SUCCESSFULLY POLISHED, REPACKED & DEPLOYED!")
    print("==================================================================")
    return True

if __name__ == "__main__":
    main()
