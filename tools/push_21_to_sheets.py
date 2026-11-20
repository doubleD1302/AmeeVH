#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stella Sora - Push 2.1 Localization Content to Google Sheets
Tự động đồng bộ toàn bộ nội dung mới của bản 2.1 chưa có trên Google Spreadsheet:
1. 'Chương 10' (STm10001: 2,263 dòng thoại)
2. 'Cốt Truyện Sự Kiện' (STev_13: 1,029 dòng)
3. 'Ngoại Truyện' (STsp_19: 398 dòng)
4. 'Kịch Bản Ký Ức (CG)' (CG_161 & CG_disc4068: 455 dòng)
5. 'Tin Nhắn Điện Thoại' (PM16101: 153 dòng)
6. 'Ủy Thác Hội Quán' (BBm10001_BT02 & BT03: 41 dòng)
7. 'Hẹn Hò Nhân Vật' (DP_single161: 4 dòng)
8. Cập nhật 'Chương 4': 2 dòng thoại thay đổi (STm04_07.118, STm04_09.142)
9. '03_BangText_UI_KyNang': Toàn bộ bảng text/UI mới của 2.1 (1,557 dòng)
"""

import sys
import os
import re
import json
import subprocess
from pathlib import Path
from collections import defaultdict

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SPREADSHEET_ID = "13ooFrJLyeP9LsSFrkzp4SWpQY5ePd6ap5muvWCwWOdM"
ROOT = Path(__file__).resolve().parent.parent

# Nạp actor preset map
sys.path.insert(0, str(ROOT / "tools"))
try:
    from export_google_sheets_batch import build_actor_preset_map
    ACTOR_MAP = build_actor_preset_map()
except Exception as e:
    print(f"Warning: could not load actor map: {e}")
    ACTOR_MAP = {}

SHEET_INFO = {
    "Chương 10": {"id": 1724837432, "rows": 2500},
    "Cốt Truyện Sự Kiện": {"id": 1471986453, "rows": 10967},
    "Ngoại Truyện": {"id": 1699026156, "rows": 5769},
    "Kịch Bản Ký Ức (CG)": {"id": 499773622, "rows": 14428},
    "Tin Nhắn Điện Thoại": {"id": 1999742602, "rows": 8837},
    "Ủy Thác Hội Quán": {"id": 801579187, "rows": 1000},
    "Hẹn Hò Nhân Vật": {"id": 433256131, "rows": 1000},
    "03_BangText_UI_KyNang": {"id": 2101040008, "rows": 1325}
}

def sanitize_cell(val):
    if val is None:
        return ""
    if not isinstance(val, str):
        val = str(val)
    val = val.replace("\x00", "")
    return re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", "", val)

def run_batch(requests_data, chunk_desc="batch"):
    tmp_path = ROOT / "work" / f"tmp_gsheets_{os.getpid()}.json"
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(requests_data, f, ensure_ascii=False, indent=2)
    
    cmd = f'gsheets mutate batch {SPREADSHEET_ID} -f "{tmp_path}"'
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8")
    if tmp_path.exists():
        tmp_path.unlink()
    
    if res.returncode == 0:
        print(f"  [+] Thành công: {chunk_desc}")
        return True
    else:
        print(f"  [-] Lỗi ({chunk_desc}): {res.stderr.strip() or res.stdout.strip()}")
        return False

def ensure_rows(sheet_name, required_max_row):
    info = SHEET_INFO.get(sheet_name)
    if not info:
        return
    cur_rows = info["rows"]
    if required_max_row > cur_rows:
        needed = (required_max_row - cur_rows) + 200
        start = cur_rows - 1
        print(f" -> Mở rộng lưới cho '{sheet_name}': hiện có {cur_rows}, cần ít nhất {required_max_row}. Thêm {needed} hàng...")
        cmd = f'gsheets mutate insert-rows {SPREADSHEET_ID} --sheet-id {info["id"]} --count {needed} --start {start}'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8")
        if res.returncode == 0:
            print(f"    [+] Mở rộng hàng thành công!")
            info["rows"] = cur_rows + needed
        else:
            print(f"    [-] Lỗi mở rộng: {res.stderr.strip() or res.stdout.strip()}")

def push_in_chunks(sheet_name, start_row, rows, chunk_size=500):
    total = len(rows)
    end_row = start_row + total - 1
    ensure_rows(sheet_name, end_row)
    
    for i in range(0, total, chunk_size):
        chunk = rows[i:i + chunk_size]
        curr_start = start_row + i
        clean_chunk = [[sanitize_cell(c) for c in r] for r in chunk]
        reqs = [{
            "op": "write",
            "range": f"'{sheet_name}'!A{curr_start}",
            "data": clean_chunk
        }]
        desc = f"{sheet_name} A{curr_start}: hàng {i+1}-{min(i+chunk_size, total)} / {total}"
        ok = run_batch(reqs, desc)
        if not ok:
            raise RuntimeError(f"Failed to push chunk {desc}")

def get_speaker_name(src):
    actor_voice = src.get("actor_voice", "")
    cmd = src.get("command", "")
    en = src.get("source_text", "")
    
    if cmd in ("SetSceneHeading", "SetBGM", "SetSound", "SetEffect") or en.startswith(("ep_", "story_", "fx_", "Set", "sound_")):
        return "[Hệ thống / Lệnh]"
    
    if actor_voice:
        parts = [p.strip() for p in actor_voice.split("|")]
        actor_id = parts[0]
        if actor_id in ACTOR_MAP:
            return ACTOR_MAP[actor_id]
        if len(parts) > 1 and parts[1] in ACTOR_MAP:
            return ACTOR_MAP[parts[1]]
    
    if any(w in en for w in ["Floris Month", "Pluvia Month", "26th", "27th", "Ash District", "Vault", "Corridor", "Street", "Near Emor"]):
        return "Dẫn chuyện (Bối cảnh)"
    
    return "Dẫn chuyện"

def main():
    print("=" * 70)
    print("STELLA SORA - BẮT ĐẦU ĐỒNG BỘ NỘI DUNG 2.1 LÊN GOOGLE SHEETS")
    print("=" * 70)
    
    # 1. Nạp dữ liệu
    print("[1/9] Đang nạp toàn bộ dữ liệu 2.1 và các bản vá hotfix...")
    v210_p = ROOT / "translations/2.1.0/Van_ban_EN_VI.jsonl"
    pending_p = ROOT / "translations/hotfix_2611141949/pending_vi.jsonl"
    lua_extra_p = ROOT / "translations/hotfix_2611141949/lua_extra.jsonl"
    data_extra_p = ROOT / "translations/hotfix_2611141949/data_extra.jsonl"
    
    overlays = {}
    for p in [pending_p, lua_extra_p, data_extra_p]:
        if p.exists():
            for l in p.read_text(encoding="utf-8").splitlines():
                if l.strip():
                    d = json.loads(l)
                    overlays[d["id"]] = d.get("text_vi", "")
    print(f" -> Đã nạp {len(overlays)} bản dịch ghi đè từ hotfix.")
    
    all_rows_210 = []
    with open(v210_p, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            d = json.loads(line)
            if d["id"] in overlays:
                d["text_vi"] = overlays[d["id"]]
            all_rows_210.append(d)
    print(f" -> Đã nạp {len(all_rows_210)} mục từ 2.1.0 Van_ban_EN_VI.jsonl.")
    
    story_by_scene = defaultdict(list)
    table_rows = []
    
    for r in all_rows_210:
        src = r.get("source", {})
        fk = src.get("field_kind", "")
        sc = src.get("scene", "")
        if fk == "Văn bản hiển thị" or not sc:
            table_rows.append(r)
        else:
            story_by_scene[sc].append(r)
    
    existing_ids = {r["id"] for r in all_rows_210}
    if data_extra_p.exists():
        for l in data_extra_p.read_text(encoding="utf-8").splitlines():
            if l.strip():
                d = json.loads(l)
                if d["id"] not in existing_ids:
                    table_rows.append(d)
    
    print(f" -> Tổng số phân đoạn thoại: {len(story_by_scene)} scenes.")
    print(f" -> Tổng số dòng bảng text/UI: {len(table_rows)} dòng.")
    
    # 2. Xử lý 'Chương 10'
    print("\n[2/9] Đồng bộ 'Chương 10' (STm10001)...")
    stm10_scenes = sorted([sc for sc in story_by_scene if sc.startswith("STm10001")])
    stm10_rows = [
        [
            "Màn (Phân đoạn)",
            "Mã câu (ID) [Khóa]",
            "Chủ thể / Người nói (Ai nói) 🗣️",
            "Nguồn EN",
            "Nguồn CN (r03)",
            "Nguồn JP (r03)",
            "Bản dịch cũ (Tham khảo) [Khóa]",
            "BẢN DỊCH MỚI (⭐ SỬA Ở ĐÂY)",
            "Dịch giả"
        ]
    ]
    total_stm10_lines = 0
    for sc in stm10_scenes:
        lines = story_by_scene[sc]
        total_stm10_lines += len(lines)
        stm10_rows.append([f"🌟 MÀN {sc.upper()}", "", "", "", "", "", "", "", ""])
        for idx, item in enumerate(lines, 1):
            src = item.get("source", {})
            spk = get_speaker_name(src)
            en = src.get("source_text", "")
            prev = src.get("previous_text", "")
            vi = item.get("text_vi", "")
            status = "Đã duyệt" if vi and vi != en else "Bản dịch 2.1"
            stm10_rows.append([
                sc,
                f"{sc}.{idx}",
                spk,
                en,
                "",
                "",
                prev,
                vi,
                status
            ])
    
    print(f" -> Đang đẩy {len(stm10_rows)} hàng ({total_stm10_lines} câu thoại) vào 'Chương 10'...")
    push_in_chunks("Chương 10", 1, stm10_rows, chunk_size=500)
    
    def build_story_append_rows(scenes):
        res_rows = []
        count = 0
        for sc in sorted(scenes):
            lines = story_by_scene[sc]
            count += len(lines)
            res_rows.append([f"🌟 MÀN {sc.upper()}", "", "", "", "", "", "", "", ""])
            for idx, item in enumerate(lines, 1):
                src = item.get("source", {})
                spk = get_speaker_name(src)
                en = src.get("source_text", "")
                prev = src.get("previous_text", "")
                vi = item.get("text_vi", "")
                status = "Đã duyệt" if vi and vi != en else "Bản dịch 2.1"
                res_rows.append([
                    sc,
                    f"{sc}.{idx}",
                    spk,
                    en,
                    "",
                    "",
                    prev,
                    vi,
                    status
                ])
        return res_rows, count

    # 3. 'Cốt Truyện Sự Kiện'
    print("\n[3/9] Đồng bộ 'Cốt Truyện Sự Kiện' (STev_13)...")
    stev_scenes = [sc for sc in story_by_scene if sc.startswith("STev_13")]
    stev_rows, stev_count = build_story_append_rows(stev_scenes)
    start_stev = 10968
    print(f" -> Đang đẩy {len(stev_rows)} hàng ({stev_count} câu thoại) từ hàng {start_stev}...")
    push_in_chunks("Cốt Truyện Sự Kiện", start_stev, stev_rows, chunk_size=500)
    
    # 4. 'Ngoại Truyện'
    print("\n[4/9] Đồng bộ 'Ngoại Truyện' (STsp_19)...")
    stsp_scenes = [sc for sc in story_by_scene if sc.startswith("STsp_19")]
    stsp_rows, stsp_count = build_story_append_rows(stsp_scenes)
    start_stsp = 5770
    print(f" -> Đang đẩy {len(stsp_rows)} hàng ({stsp_count} câu thoại) từ hàng {start_stsp}...")
    push_in_chunks("Ngoại Truyện", start_stsp, stsp_rows, chunk_size=500)
    
    # 5. 'Kịch Bản Ký Ức (CG)'
    print("\n[5/9] Đồng bộ 'Kịch Bản Ký Ức (CG)' (CG_161 & CG_disc4068)...")
    cg_scenes = [sc for sc in story_by_scene if sc.startswith("CG_")]
    cg_rows, cg_count = build_story_append_rows(cg_scenes)
    start_cg = 14429
    print(f" -> Đang đẩy {len(cg_rows)} hàng ({cg_count} câu thoại) từ hàng {start_cg}...")
    push_in_chunks("Kịch Bản Ký Ức (CG)", start_cg, cg_rows, chunk_size=500)
    
    # 6. 'Tin Nhắn Điện Thoại'
    print("\n[6/9] Đồng bộ 'Tin Nhắn Điện Thoại' (PM16101)...")
    pm_scenes = [sc for sc in story_by_scene if sc.startswith("PM")]
    pm_rows, pm_count = build_story_append_rows(pm_scenes)
    start_pm = 8838
    print(f" -> Đang đẩy {len(pm_rows)} hàng ({pm_count} tin nhắn) từ hàng {start_pm}...")
    push_in_chunks("Tin Nhắn Điện Thoại", start_pm, pm_rows, chunk_size=500)
    
    # 7. 'Ủy Thác Hội Quán'
    print("\n[7/9] Đồng bộ 'Ủy Thác Hội Quán' (BBm10001)...")
    bbm_scenes = [sc for sc in story_by_scene if sc.startswith("BBm")]
    bbm_rows, bbm_count = build_story_append_rows(bbm_scenes)
    start_bbm = 488
    print(f" -> Đang đẩy {len(bbm_rows)} hàng ({bbm_count} câu thoại) từ hàng {start_bbm}...")
    push_in_chunks("Ủy Thác Hội Quán", start_bbm, bbm_rows, chunk_size=500)
    
    # 8. 'Hẹn Hò Nhân Vật'
    print("\n[8/9] Đồng bộ 'Hẹn Hò Nhân Vật' (DP_single161)...")
    dp_scenes = [sc for sc in story_by_scene if sc.startswith("DP")]
    dp_rows, dp_count = build_story_append_rows(dp_scenes)
    start_dp = 324
    print(f" -> Đang đẩy {len(dp_rows)} hàng ({dp_count} câu thoại) từ hàng {start_dp}...")
    push_in_chunks("Hẹn Hò Nhân Vật", start_dp, dp_rows, chunk_size=500)
    
    # 9. Cập nhật 2 dòng sửa đổi tại 'Chương 4'
    print("\n[9/9] Cập nhật 2 dòng sửa đổi tại 'Chương 4'...")
    new_en_ch4 = "If there really was an evil god who demanded a sacrifice to stop rains and floods, a true saint would strike them down instead."
    new_vi_ch4 = "Nếu thật sự có tà thần đòi vật hiến tế để ngăn mưa lũ, người xứng danh thánh nhân sẽ tiêu diệt chính tà thần đó."
    ch4_reqs = [
        {"op": "write", "range": "'Chương 4'!D1449", "data": [[new_en_ch4]]},
        {"op": "write", "range": "'Chương 4'!H1449:I1449", "data": [[new_vi_ch4, "Bản dịch 2.1"]]},
        {"op": "write", "range": "'Chương 4'!D1833", "data": [[new_en_ch4]]},
        {"op": "write", "range": "'Chương 4'!H1833:I1833", "data": [[new_vi_ch4, "Bản dịch 2.1"]]}
    ]
    run_batch(ch4_reqs, "Cập nhật Chương 4 hàng 1449 và 1833")
    
    # 10. Bảng text/UI vào '03_BangText_UI_KyNang'
    print("\n[BỔ SUNG] Đồng bộ Bảng text & UI 2.1 vào '03_BangText_UI_KyNang'...")
    ui_rows = []
    for idx, r in enumerate(table_rows, 1):
        src = r.get("source", {})
        table_name = src.get("table") or r.get("id", "").split(":")[1] if ":" in r.get("id", "") else "Table21"
        cat = src.get("category", "")
        en = src.get("source_text", "")
        vi = r.get("text_vi", "")
        loc = src.get("locator", "")
        refs = json.dumps({"id": r.get("id", ""), "locator": loc, "category": cat}, ensure_ascii=False)
        ui_rows.append([
            table_name,
            str(idx),
            cat,
            "",
            "",
            "",
            "",
            vi,
            "",
            "",
            en,
            refs
        ])
    
    start_ui = 1326
    print(f" -> Đang đẩy {len(ui_rows)} hàng bảng text/UI từ hàng {start_ui}...")
    push_in_chunks("03_BangText_UI_KyNang", start_ui, ui_rows, chunk_size=500)
    
    print("\n" + "=" * 70)
    print("HOÀN TẤT 100% QUÁ TRÌNH ĐỒNG BỘ NỘI DUNG 2.1 LÊN GOOGLE SHEETS!")
    print("=" * 70)
    print(f"1. Chương 10: {total_stm10_lines} câu thoại mới (Đã tạo sheet mới)")
    print(f"2. Cốt Truyện Sự Kiện: {stev_count} câu thoại mới (STev_13)")
    print(f"3. Ngoại Truyện: {stsp_count} câu thoại mới (STsp_19)")
    print(f"4. Kịch Bản Ký Ức (CG): {cg_count} câu thoại mới")
    print(f"5. Tin Nhắn Điện Thoại: {pm_count} tin nhắn mới")
    print(f"6. Ủy Thác Hội Quán: {bbm_count} câu thoại mới")
    print(f"7. Hẹn Hò Nhân Vật: {dp_count} câu thoại mới")
    print(f"8. Chương 4: Đã cập nhật 2 dòng thoại chỉnh sửa")
    print(f"9. 03_BangText_UI_KyNang: {len(ui_rows)} dòng bảng text/kỹ năng/UI 2.1 mới")

if __name__ == "__main__":
    main()
