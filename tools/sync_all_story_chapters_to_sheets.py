#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stella Sora - Sync All Story Chapters to Google Sheets
Tự động tổng hợp và đẩy toàn bộ dữ liệu Việt hoá của tất cả các chương truyện lên Google Spreadsheet:
- Chương 3 đến Chương 9 (Cốt truyện chính)
- Ngoại truyện (STsp)
- Cốt truyện sự kiện (STev)
- Nhiệm vụ ủy thác (BBm)
- Tin nhắn điện thoại (PM)
- Kịch bản CG & Ký ức (CG)
- Hẹn hò nhân vật (DP)
Tự động tạo sheet mới cho các chương chưa có và cập nhật 100% dữ liệu.
"""

import os
import sys
import json
import csv
import re
import subprocess
from pathlib import Path

ROOT = Path("StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "scripts"))

from export_google_sheets_batch import build_actor_preset_map, parse_scene_lua_bytecode
from extract_clean_10k_avg import extract_clean_lua53_strings
from remediation_dict import BINARY_CLEANUP_MAP

SPREADSHEET_ID = "13ooFrJLyeP9LsSFrkzp4SWpQY5ePd6ap5muvWCwWOdM"

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def sanitize_cell(val):
    if val is None:
        return ""
    if not isinstance(val, str):
        val = str(val)
    val = val.replace("\x00", "")
    return re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", "", val)


def load_all_dictionaries():
    print("[1/3] Đang nạp toàn bộ kho từ điển và bản dịch chuẩn...")
    trans_by_id = {}
    trans_by_en = {}

    # 1. Base pillars
    p_pillars = ROOT / "work/batches/pillars_translation_cache.json"
    pillars_dict = {}
    if p_pillars.exists():
        pillars_dict = json.loads(p_pillars.read_text(encoding="utf-8"))
        trans_by_en.update(pillars_dict)

    # 2. Batches
    batch_files = [
        "work/batches/batch_10000_avg_clean.json",
        "work/batches/remaining_lua_avg_cache.json",
        "work/batches/dialogue_remaining_avg_approved.json",
        "work/batches/batch_10k_approved.json",
        "work/batches/batch_10k_b2_approved.json",
        "work/batches/batch_10k_b3_approved.json",
        "work/batches/batch_10k_b4_approved.json",
    ]
    for bf in batch_files:
        p = ROOT / bf
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            for k, v in data.items():
                if "." in k and k[0].isupper():
                    trans_by_id[k] = v
                else:
                    trans_by_en[k] = v

    # 3. Editorial proposals (Overriding with approved editorial reviews)
    editorial_dir = ROOT / "work/editorial"
    if editorial_dir.exists():
        for p in sorted(editorial_dir.rglob("*.jsonl")):
            for line in p.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                    k = d.get("id") or d.get("scene_id")
                    v = d.get("vi_editorial") or d.get("polished_vi") or d.get("vi") or d.get("proposed_vi")
                    en = d.get("en")
                    if k and v:
                        if isinstance(en, str) and len(en) > 15 and isinstance(v, str) and v.startswith(("SetSceneHeading", "SetTalk", "SetBubble", "ep_", "story_main_")):
                            v = pillars_dict.get(en, v)
                        trans_by_id[k] = v
                    if en and v:
                        trans_by_en[en] = v
                except Exception:
                    pass

    # 4. Binary cleanup map
    for k, v in BINARY_CLEANUP_MAP.items():
        trans_by_id[k] = v

    print(f" -> Đã nạp thành công {len(trans_by_id):,} câu theo ID và {len(trans_by_en):,} câu theo EN.")
    return trans_by_id, trans_by_en, pillars_dict


def get_existing_sheets():
    res = subprocess.run(["gsheets", "readonly", "list-sheets", SPREADSHEET_ID], capture_output=True, text=True, encoding="utf-8", shell=True)
    existing = set()
    if res.returncode == 0:
        for line in res.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) >= 2 and parts[0].isdigit():
                existing.add(parts[1])
    return existing


def process_all_chapters():
    trans_by_id, trans_by_en, pillars_dict = load_all_dictionaries()
    actor_names = build_actor_preset_map()
    print(f" -> Đã nạp {len(actor_names)} quy chuẩn tên nhân vật.")

    lua_dir = ROOT / "work" / "research" / "lua_tree" / "Game" / "UI" / "Avg" / "_en" / "Config"
    out_dir = ROOT / "work" / "sheets_export"
    out_dir.mkdir(parents=True, exist_ok=True)

    chapters_to_sync = [
        ("STm03", "Chương 3 (Cốt truyện chính)", "Chuong_3_MainStory"),
        ("STm04", "Chương 4 (Cốt truyện chính)", "Chuong_4_MainStory"),
        ("STm05", "Chương 5 (Cốt truyện chính)", "Chuong_5_MainStory"),
        ("STm06", "Chương 6 (Cốt truyện chính)", "Chuong_6_MainStory"),
        ("STm07", "Chương 7 (Cốt truyện chính)", "Chuong_7_MainStory"),
        ("STm08", "Chương 8 (Cốt truyện chính)", "Chuong_8_MainStory"),
        ("STm09", "Chương 9 (Cốt truyện chính)", "Chuong_9_MainStory"),
        ("STsp", "Ngoại truyện (Side Stories)", "Ngoai_Truyen_STsp"),
        ("BBm", "Nhiệm vụ ủy thác (Bulletin Board)", "Uy_Thac_Hoi_Quan_BBm"),
        ("DP", "Hẹn hò & Tương tác (Dating)", "Hen_Ho_Dating_DP"),
        ("PM", "Tin nhắn điện thoại (Phone Messages)", "Tin_Nhan_Dien_Thoai_PM"),
        ("STev", "Cốt truyện sự kiện (Event Stories)", "Cot_Truyen_Su_Kien_STev"),
        ("CG", "Kịch bản CG & Ký ức nhân vật", "Kich_Ban_CG_Memory"),
    ]

    existing_sheets = get_existing_sheets()
    print(f"\n[2/3] Danh sách sheet hiện có trên Google Sheets ({len(existing_sheets)} sheets): {sorted(existing_sheets)}")

    print("\n[3/3] Bắt đầu xử lý và đồng bộ từng chương lên Google Sheets...\n" + "=" * 75)

    summary_results = []

    for prefix, title, sheet_name in chapters_to_sync:
        print(f"\n🚀 Đang xử lý: {title} -> Sheet: [{sheet_name}]...")
        files = sorted([f for f in os.listdir(lua_dir) if f.startswith(prefix) and f.endswith(".lua")])
        if not files:
            print(f" ⚠️ Không tìm thấy file nào cho tiền tố {prefix}!")
            continue

        rows = [
            [
                "Màn (Phân đoạn)",
                "Mã câu (ID) [Khóa]",
                "Chủ thể / Người nói (Ai nói) 🗣️",
                "Lời thoại gốc (EN/JP) [Khóa]",
                "Bản dịch cũ (Tham khảo) [Khóa]",
                "BẢN DỊCH MỚI (⭐ SỬA Ở ĐÂY)",
                "Trạng thái",
                "Ghi chú & Thảo luận"
            ]
        ]

        total_lines = 0
        translated_lines = 0

        for f in files:
            scene_id = f[:-4]
            fpath = lua_dir / f
            raw_strings = extract_clean_lua53_strings(fpath)
            spk_map = parse_scene_lua_bytecode(fpath, actor_names)

            # Phân tích tiêu đề màn
            scene_title = f"MÀN {scene_id}"
            act_name = ""
            sub_name = ""
            for s in raw_strings[:4]:
                if any(w in s for w in ["Act One", "Act Two", "Act Three", "Act Four", "Act Five", "Act Six", "Act Seven", "Act Eight", "Act Nine", "Act Ten", "Interlude", "The End", "Prologue", "Epilogue", "Hồi", "Màn"]):
                    act_name = trans_by_en.get(s, s)
                elif len(s) < 40 and not s.startswith(("ep_", "story_", "fx_", "qstory_")) and not act_name == s:
                    sub_name = trans_by_en.get(s, s)
            if act_name or sub_name:
                scene_title = f"MÀN {scene_id}: {act_name} - {sub_name}".strip(" -")

            rows.append([f"🌟 {scene_title.upper()}", "", "", "", "", "", "", ""])

            for idx, en_str in enumerate(raw_strings):
                total_lines += 1
                line_id = f"{scene_id}.{idx+1}"

                # Xác định chủ thể
                if en_str.startswith(("ep_", "story_", "fx_", "qstory_", "Set", "\x00", "flavio_", "wog_", "hotel_", "city_", "hospital_", "ward_", "ui_", "sound_")):
                    speaker = "[Hệ thống / Lệnh]"
                elif any(w in en_str for w in ["Floris Month", "Pluvia Month", "26th", "27th", "Ash District", "Vault", "Corridor", "Street", "Near Emor"]):
                    speaker = "Dẫn chuyện (Bối cảnh)"
                else:
                    speaker = spk_map.get(en_str, "Dẫn chuyện")

                # Lấy bản dịch tiếng Việt
                vi_val = trans_by_id.get(line_id)
                if not vi_val or (len(en_str) > 15 and vi_val.startswith(("SetSceneHeading", "SetTalk", "SetBubble", "ep_", "story_main_"))):
                    vi_val = trans_by_en.get(en_str)

                if not vi_val:
                    vi_val = pillars_dict.get(en_str)

                vi_old = trans_by_en.get(en_str, vi_val if vi_val else "")

                if not vi_val:
                    vi_val = en_str
                    status = "Chờ dịch" if speaker != "[Hệ thống / Lệnh]" else "Đã duyệt"
                else:
                    status = "Đã duyệt"
                    translated_lines += 1

                rows.append([
                    scene_id,
                    line_id,
                    speaker,
                    en_str,
                    vi_old,
                    vi_val,
                    status,
                    ""
                ])

        # Ghi file CSV an toàn với sanitize_cell
        csv_path = out_dir / f"{sheet_name}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            for r in rows:
                clean_row = [sanitize_cell(cell) for cell in r]
                writer.writerow(clean_row)

        print(f" -> Trích xuất {len(files)} files, tổng cộng {total_lines:,} câu ({translated_lines:,} câu dịch).")
        print(f" -> Đã xuất CSV: {csv_path.name} ({csv_path.stat().st_size:,} bytes).")

        # Kiểm tra và tạo sheet nếu chưa có
        if sheet_name not in existing_sheets:
            print(f" -> Sheet '{sheet_name}' chưa tồn tại. Đang tạo mới...")
            add_res = subprocess.run(["gsheets", "mutate", "add-sheet", SPREADSHEET_ID, "--title", sheet_name], capture_output=True, text=True, encoding="utf-8", shell=True)
            if add_res.returncode == 0:
                print(f"    [+] {add_res.stdout.strip()}")
                existing_sheets.add(sheet_name)
            else:
                print(f"    [-] Lỗi tạo sheet: {add_res.stderr.strip() or add_res.stdout.strip()}")

        # Import CSV vào Google Sheets
        print(f" -> Đang nhập dữ liệu vào Google Sheets [{sheet_name}]...")
        imp_res = subprocess.run(["gsheets", "mutate", "import-csv", SPREADSHEET_ID, str(csv_path), "--sheet", sheet_name], capture_output=True, text=True, encoding="utf-8", shell=True)
        if imp_res.returncode == 0:
            print(f"    [+] {imp_res.stdout.strip()}")
            summary_results.append({
                "chapter": title,
                "sheet": sheet_name,
                "files": len(files),
                "rows": total_lines,
                "status": "Thành công"
            })
        else:
            print(f"    [-] Lỗi nhập CSV: {imp_res.stderr.strip() or imp_res.stdout.strip()}")
            summary_results.append({
                "chapter": title,
                "sheet": sheet_name,
                "files": len(files),
                "rows": total_lines,
                "status": "Lỗi"
            })

    print("\n" + "=" * 75)
    print("HOÀN TẤT TỔNG HỢP VÀ ĐỒNG BỘ TOÀN BỘ CÁC CHƯƠNG LÊN GOOGLE SHEETS!")
    print("=" * 75)
    for r in summary_results:
        print(f" - {r['chapter']:35s} | Sheet: {r['sheet']:25s} | {r['files']:3d} files | {r['rows']:5d} câu | {r['status']}")


if __name__ == "__main__":
    process_all_chapters()
