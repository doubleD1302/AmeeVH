#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import csv
import subprocess
from pathlib import Path

ROOT = Path("StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))
from export_google_sheets_batch import build_actor_preset_map, parse_scene_lua_bytecode
from extract_clean_10k_avg import extract_clean_lua53_strings

SPREADSHEET_ID = "13ooFrJLyeP9LsSFrkzp4SWpQY5ePd6ap5muvWCwWOdM"

print("[1/3] Loading master translation dictionaries...")
trans_by_id = {}
trans_by_en = {}

batch_files = [
    "work/batches/pillars_translation_cache.json",
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

editorial_dir = ROOT / "work/editorial"
for p in editorial_dir.rglob("*.jsonl"):
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            d = json.loads(line)
            k = d.get("id") or d.get("scene_id")
            v = d.get("vi_editorial") or d.get("polished_vi") or d.get("vi") or d.get("proposed_vi")
            en = d.get("en")
            if k and v:
                trans_by_id[k] = v
            if en and v:
                trans_by_en[en] = v
        except Exception:
            pass

print(f" -> Loaded {len(trans_by_id)} keys by ID and {len(trans_by_en)} keys by EN.")

actor_names = build_actor_preset_map()
print(f" -> Loaded {len(actor_names)} actor presets.")

def process_chapter(prefix, title, sheet_name):
    print(f"\n[*] Processing {title} ({sheet_name})...")
    lua_dir = ROOT / "work" / "research" / "lua_tree" / "Game" / "UI" / "Avg" / "_en" / "Config"
    files = sorted([f for f in os.listdir(lua_dir) if f.startswith(prefix) and f.endswith(".lua")])
    print(f" -> Found {len(files)} files.")

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
    for f in files:
        scene_id = f[:-4]
        fpath = lua_dir / f
        raw_strings = extract_clean_lua53_strings(fpath)
        spk_map = parse_scene_lua_bytecode(fpath, actor_names)

        # Detect scene title
        scene_title = f"MÀN {scene_id}"
        # If there is Act One/Two or subtitle in raw strings
        act_name = ""
        sub_name = ""
        for s in raw_strings[:4]:
            if any(w in s for w in ["Act One", "Act Two", "Act Three", "Act Four", "Act Five", "Act Six", "Act Seven", "Act Eight", "Act Nine", "Act Ten", "Interlude", "The End", "Prologue", "Epilogue"]):
                act_name = trans_by_en.get(s, s)
            elif len(s) < 40 and not s.startswith(("ep_", "story_", "fx_")) and not act_name == s:
                sub_name = trans_by_en.get(s, s)
        if act_name or sub_name:
            scene_title = f"MÀN {scene_id}: {act_name} - {sub_name}".strip(" -")

        rows.append([f"🌟 {scene_title.upper()}", "", "", "", "", "", "", ""])

        for idx, en_str in enumerate(raw_strings):
            total_lines += 1
            line_id = f"{scene_id}.{idx+1}"

            # Determine speaker
            if en_str.startswith(("ep_", "story_", "fx_", "qstory_", "Set", "\x00", "flavio_", "wog_", "hotel_", "city_", "hospital_", "ward_", "ui_", "sound_")):
                speaker = "[Hệ thống / Lệnh]"
            elif any(w in en_str for w in ["Floris Month", "Pluvia Month", "26th", "27th", "Ash District", "Vault", "Corridor", "Street", "Near Emor"]):
                speaker = "Dẫn chuyện (Bối cảnh)"
            else:
                speaker = spk_map.get(en_str, "Dẫn chuyện")

            vi_val = trans_by_id.get(line_id, trans_by_en.get(en_str, en_str if speaker == "[Hệ thống / Lệnh]" else ""))
            vi_old = trans_by_en.get(en_str, vi_val)
            if not vi_val:
                vi_val = en_str

            status = "Đã duyệt" if vi_val != en_str or speaker == "[Hệ thống / Lệnh]" else "Chờ dịch"

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

    print(f" -> Total {total_lines} lines extracted across {len(files)} files.")

    # Write CSV
    out_dir = ROOT / "work" / "sheets_export"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{sheet_name}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        for r in rows:
            writer.writerow(r)

    print(f" -> Saved CSV to {csv_path} ({csv_path.stat().st_size:,} bytes).")

    # Check sheet in Google Sheets
    check = subprocess.run(["gsheets", "readonly", "list-sheets", SPREADSHEET_ID], capture_output=True, text=True, encoding="utf-8", shell=True)
    if sheet_name not in check.stdout:
        print(f" -> Sheet '{sheet_name}' not found. Creating...")
        add_res = subprocess.run(["gsheets", "mutate", "add-sheet", SPREADSHEET_ID, "--title", sheet_name], capture_output=True, text=True, encoding="utf-8", shell=True)
        print("    ", add_res.stdout.strip())

    # Import CSV
    print(f" -> Importing CSV to Google Sheets sheet '{sheet_name}'...")
    imp_res = subprocess.run(["gsheets", "mutate", "import-csv", SPREADSHEET_ID, str(csv_path), "--sheet", sheet_name], capture_output=True, text=True, encoding="utf-8", shell=True)
    print("    ", imp_res.stdout.strip() or imp_res.stderr.strip())

if __name__ == "__main__":
    process_chapter("STm03", "Chương 3 (Cốt truyện chính)", "Chuong_3_MainStory")
