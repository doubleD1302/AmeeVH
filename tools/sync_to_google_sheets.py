#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stella Sora - Sync to Google Sheets CLI Bridge
Đồng bộ từng đợt dữ liệu trực tiếp vào Google Spreadsheet qua gsheets CLI.
"""

import sys
import os
import json
import subprocess
from typing import List, Dict, Any

SPREADSHEET_ID = "13ooFrJLyeP9LsSFrkzp4SWpQY5ePd6ap5muvWCwWOdM"

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_gsheets_batch(requests_data: List[Dict[str, Any]], tmp_file: str):
    """Ghi danh sách thao tác ra file tạm và gọi gsheets mutate batch."""
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(requests_data, f, ensure_ascii=False, indent=2)

    cmd = ["gsheets", "mutate", "batch", SPREADSHEET_ID, "-f", tmp_file]
    print(f"[*] Đang thực thi {len(requests_data)} thao tác qua gsheets mutate batch...")
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", shell=True)
    if res.returncode == 0:
        print("[+] Thành công!")
        if res.stdout:
            print(res.stdout.strip())
    else:
        print("[-] Lỗi thực thi gsheets:")
        print(res.stderr.strip() or res.stdout.strip())
        raise RuntimeError("gsheets batch failed")


def sync_batch_1_glossary_and_voice():
    """Đợt 1: Cập nhật Master Glossary (322 mục) & Ma trận tính cách (41 nhân vật + 12 ma trận)."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    batch_json_p = os.path.join(base_dir, "work", "batches", "google_sheets_batch_data.json")
    with open(batch_json_p, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Sheet 01: Thống nhất danh từ
    glossary_rows = [
        ["BẢNG THỐNG NHẤT DANH TỪ & THUẬT NGỮ TOÀN GAME (GLOSSARY 322 MỤC)", "", "", "", ""],
        ["Danh từ chuẩn bắt buộc tuân thủ. Giúp toàn bộ các Chương và Màn không bao giờ bị lệch thuật ngữ.", "", "", "", ""],
        ["Danh từ gốc (EN)", "Bản dịch Tiếng Việt chuẩn", "Phân loại nhóm", "Ghi chú ngữ cảnh", "Trạng thái"]
    ]
    cur_group = ""
    for item in data.get("glossary", []):
        grp = item.get("group_vi", item.get("category", "Chung"))
        if grp != cur_group:
            cur_group = grp
            glossary_rows.append([f"--- NHÓM: {cur_group.upper()} ---", "", "", "", ""])
        glossary_rows.append([
            item.get("source", item.get("term_en", "")),
            item.get("target", item.get("target_vi", "")),
            item.get("category", "General"),
            item.get("notes", ""),
            item.get("status", "approved")
        ])

    # 2. Sheet 02: Ma trận tính cách & xưng hô
    voice_rows = [
        ["MA TRẬN TÍNH CÁCH, KHẨU KHÍ & QUY CHUẨN XƯNG HÔ (VOICE BIBLE & MATRIX)", "", "", "", "", ""],
        ["Xác định đại từ và khẩu khí theo từng cặp nhân vật. Đảm bảo nhân vật luôn giữ đúng cá tính xuyên suốt.", "", "", "", "", ""],
        ["Nhân vật (Speaker)", "Đối tượng nghe (Listener)", "Đại từ Xưng - Gọi chuẩn", "Tính cách cốt lõi & Khẩu khí (Tone)", "Mẫu câu ví dụ đúng điệu", "Điều TUYỆT ĐỐI TRÁNH"],
        ["--- I. MA TRẬN XƯNG HÔ CỐT LÕI GIỮA CÁC CẶP NHÂN VẬT ---", "", "", "", "", ""]
    ]
    for r in data.get("voice_bible", {}).get("relationship_matrix", []):
        prn = r.get("pronouns", r.get("pronoun_rule", ""))
        tone = r.get("tone", r.get("tone_and_manner", ""))
        eg = r.get("sample_dialogue", r.get("example_dialogue", ""))
        dont = r.get("do_not", "")
        voice_rows.append([
            r.get("speaker", ""),
            r.get("listener", ""),
            prn,
            tone,
            eg,
            dont
        ])

    voice_rows.append(["--- II. DANH MỤC 41 NHÂN VẬT & KHẨU KHÍ RIÊNG BIỆT ---", "", "", "", "", ""])
    for c in data.get("voice_bible", {}).get("characters", []):
        c_name = f"{c.get('name_en', '')} ({c.get('name_vi', '')})"
        c_fac = c.get("faction", "Chưa rõ")
        c_prn = f"Xưng: {c.get('default_self', 'tôi')}\nGọi: {c.get('default_address', 'bạn')}"
        c_trait = c.get("personality_summary", "")
        if isinstance(c_trait, list):
            c_trait = "\n".join(str(x) for x in c_trait)
        c_eg = f"Khẩu hiệu: {c.get('catchphrase', '...')}"
        dont_raw = c.get("do_not", "Tránh từ lóng teen, giữ văn phong lịch sự.")
        if isinstance(dont_raw, list):
            c_dont = "\n".join(str(x) for x in dont_raw)
        else:
            c_dont = str(dont_raw)
        voice_rows.append([c_name, c_fac, c_prn, c_trait, c_eg, c_dont])

    # Tạo batch requests
    reqs = [
        {"op": "write", "range": "01_Thong_Nhat_Danh_Tu!A1", "data": glossary_rows},
        {"op": "write", "range": "02_Ma_Tran_Tinh_Cach_Xung_Ho!A1", "data": voice_rows}
    ]

    tmp_path = os.path.join(base_dir, "work", "batches", "tmp_reqs_batch1.json")
    run_gsheets_batch(reqs, tmp_path)
    if os.path.exists(tmp_path):
        os.remove(tmp_path)


def sync_batch_2_chapter_1():
    """Đợt 2: Cập nhật toàn bộ 12 Màn kịch bản Chương 1 (1.303 câu)."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    batch_json_p = os.path.join(base_dir, "work", "batches", "google_sheets_batch_data.json")
    with open(batch_json_p, "r", encoding="utf-8") as f:
        data = json.load(f)

    ch1_rows = [
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

    for scene in data.get("chapter_1_scenes", []):
        sc_title = scene.get("scene_title", "Phân đoạn")
        sc_id = scene.get("scene_id", "")
        ch1_rows.append([f"🌟 {sc_title.upper()}", "", "", "", "", "", "", ""])

        for line in scene.get("lines", []):
            l_id = line.get("line_id", "")
            spk = line.get("speaker", "Dẫn chuyện")
            en = line.get("en_text", "")
            vi_old = line.get("vi_ptc", "")
            vi_new = line.get("vi_clean", vi_old)
            ch1_rows.append([sc_id, l_id, spk, en, vi_old, vi_new, "Đã duyệt", ""])

    # Chia thành 2 chunks nếu cần để tránh payload quá lớn
    chunk_size = 700
    reqs = []
    for i in range(0, len(ch1_rows), chunk_size):
        chunk = ch1_rows[i:i + chunk_size]
        start_row = i + 1
        reqs.append({"op": "write", "range": f"Chuong_1_MainStory!A{start_row}", "data": chunk})

    tmp_path = os.path.join(base_dir, "work", "batches", "tmp_reqs_batch2.json")
    run_gsheets_batch(reqs, tmp_path)
    if os.path.exists(tmp_path):
        os.remove(tmp_path)


def sync_batch_3_chapter_2():
    """Đợt 3: Tạo sheet Chuong_2_MainStory và cập nhật toàn bộ 14 Màn kịch bản Chương 2 (1.503 câu)."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    batch_json_p = os.path.join(base_dir, "work", "batches", "google_sheets_batch_data.json")
    with open(batch_json_p, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Kiểm tra xem sheet Chuong_2_MainStory đã tồn tại chưa
    res = subprocess.run(["gsheets", "readonly", "list-sheets", SPREADSHEET_ID], capture_output=True, text=True, encoding="utf-8", shell=True)
    if "Chuong_2_MainStory" not in res.stdout:
        print("[*] Đang tạo sheet mới 'Chuong_2_MainStory'...")
        subprocess.run(["gsheets", "mutate", "add-sheet", SPREADSHEET_ID, "--title", "Chuong_2_MainStory"], check=True, shell=True)

    ch2_rows = [
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

    for scene in data.get("chapter_2_scenes", []):
        sc_title = scene.get("scene_title", "Phân đoạn")
        sc_id = scene.get("scene_id", "")
        ch2_rows.append([f"🌟 {sc_title.upper()}", "", "", "", "", "", "", ""])

        for line in scene.get("lines", []):
            l_id = line.get("line_id", "")
            spk = line.get("speaker", "Dẫn chuyện")
            en = line.get("en_text", "")
            vi_old = line.get("vi_ptc", "")
            vi_new = line.get("vi_clean", vi_old)
            ch2_rows.append([sc_id, l_id, spk, en, vi_old, vi_new, "Đã duyệt", ""])

    chunk_size = 700
    reqs = []
    for i in range(0, len(ch2_rows), chunk_size):
        chunk = ch2_rows[i:i + chunk_size]
        start_row = i + 1
        reqs.append({"op": "write", "range": f"Chuong_2_MainStory!A{start_row}", "data": chunk})

    tmp_path = os.path.join(base_dir, "work", "batches", "tmp_reqs_batch3.json")
    run_gsheets_batch(reqs, tmp_path)
    if os.path.exists(tmp_path):
        os.remove(tmp_path)


def main():
    if len(sys.argv) < 2:
        print("Usage: python sync_to_google_sheets.py [batch1|batch2|batch3|all]")
        return

    arg = sys.argv[1].lower()
    if arg in ("batch1", "all"):
        print("\n=== ĐANG ĐỒNG BỘ ĐỢT 1: GLOSSARY (322) & VOICE BIBLE (41) ===")
        sync_batch_1_glossary_and_voice()
    if arg in ("batch2", "all"):
        print("\n=== ĐANG ĐỒNG BỘ ĐỢT 2: CHƯƠNG 1 (12 MÀN, 1,303 CÂU) ===")
        sync_batch_2_chapter_1()
    if arg in ("batch3", "all"):
        print("\n=== ĐANG ĐỒNG BỘ ĐỢT 3: CHƯƠNG 2 (14 MÀN, 1,503 CÂU) ===")
        sync_batch_3_chapter_2()


if __name__ == "__main__":
    main()
