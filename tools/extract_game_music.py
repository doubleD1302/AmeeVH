#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script trích xuất toàn bộ nhạc (BGM, OST, Ending, Title Themes) từ thư mục cài đặt game Stella Sora.
- Giải mã và trích xuất từ các tệp Wwise Media (.wem) sang định dạng chuẩn .ogg (lossless Vorbis).
- Phân loại rõ ràng theo từng danh mục: Cốt truyện (AVG), Chiến đấu (Combat), Trang phục (Outfit), Hệ thống/Sảnh (System), Môi trường & Sự kiện (Ambience/Events), Nhạc mở đầu/Kết thúc (Cinematic).
- Trích xuất audio từ các video chủ đề (Launch_BGM, Chapter Endings).
- Xuất danh mục tra cứu chi tiết DANH_SACH_NHAC.md và MUSIC_CATALOG.json.
"""

import os
import sys
import glob
import json
import struct
import shutil
import time
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = Path(__file__).resolve().parent
WW2OGG_EXE = TOOLS_DIR / "ww2ogg" / "ww2ogg.exe"
PCB_FILE = TOOLS_DIR / "ww2ogg" / "packed_codebooks_aoTuV_603.bin"
VGMSTREAM_EXE = TOOLS_DIR / "vgmstream" / "vgmstream-cli.exe"

OUTPUT_DIR = ROOT_DIR / "Extracted_Music"
MEDIA_DIR = ROOT_DIR / "StellaSora_Data" / "StreamingAssets" / "InstallResource"
SOUNDBANKS_DIR = ROOT_DIR / "Persistent_Store" / "SoundBanks"
VIDEOS_DIR = ROOT_DIR / "Persistent_Store" / "Videos"

CATEGORIES = {
    "01_Story_AVG": "Nhạc cốt truyện & hội thoại (Visual Novel / AVG BGM)",
    "02_Combat_Battle": "Nhạc chiến đấu & Boss (Combat & Battle BGM)",
    "03_Character_Outfit": "Nhạc chủ đề trang phục & nhân vật (Character & Outfit Themes)",
    "04_System_Lobby": "Nhạc sảnh chính, menu & hệ thống (Lobby & UI Themes)",
    "05_Loading": "Nhạc màn hình chờ tải (Loading BGM)",
    "06_Ambience_Events": "Nhạc môi trường & chế độ sự kiện (Ambience & Event BGM)",
    "07_Cinematic_Themes": "Nhạc chủ đề mở đầu & kết thúc (Title Screen & Chapter Endings)"
}

def scan_soundbank_associations(media_ids):
    """Quét các soundbank để xác định mỗi media ID thuộc soundbank nào."""
    print("-> Đang phân tích liên kết giữa các bản nhạc và SoundBanks...")
    soundbank_files = list(SOUNDBANKS_DIR.glob("*.bnk"))
    
    # Map media_id -> list of bank names
    associations = {mid: [] for mid in media_ids}
    
    for bnk in soundbank_files:
        bnk_name = bnk.name
        try:
            with open(bnk, "rb") as f:
                content = f.read()
            for mid in media_ids:
                if struct.pack("<I", mid) in content:
                    associations[mid].append(bnk_name)
        except Exception as e:
            print(f"Lỗi đọc {bnk_name}: {e}")
            
    return associations

def determine_category(bank_list):
    """Xác định danh mục ưu tiên dựa trên danh sách soundbank liên kết."""
    names_str = " ".join(bank_list).lower()
    if "music_combat" in names_str:
        return "02_Combat_Battle"
    elif "music_avg" in names_str:
        return "01_Story_AVG"
    elif "music_outfit" in names_str:
        return "03_Character_Outfit"
    elif "music_system" in names_str:
        return "04_System_Lobby"
    elif "music_loading" in names_str:
        return "05_Loading"
    elif any(k in names_str for k in ["ambience", "mode_", "avg.bnk"]):
        return "06_Ambience_Events"
    elif "music" in names_str:
        return "04_System_Lobby"
    else:
        return "06_Ambience_Events"

def convert_single_wem(args):
    """Chuyển đổi 1 tệp .media.wem sang .ogg bằng ww2ogg."""
    src_path, dst_path = args
    cmd = [
        str(WW2OGG_EXE),
        str(src_path),
        "-o", str(dst_path),
        "--pcb", str(PCB_FILE)
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0 and dst_path.exists():
            return True, dst_path, None
        else:
            return False, src_path, res.stderr
    except Exception as e:
        return False, src_path, str(e)

def extract_video_audio(src_video, dst_wav):
    """Trích xuất âm thanh từ video sang tệp .wav chất lượng cao bằng vgmstream-cli."""
    cmd = [
        str(VGMSTREAM_EXE),
        "-o", str(dst_wav),
        str(src_video)
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        return res.returncode == 0 and dst_wav.exists()
    except Exception:
        return False

def get_track_duration(audio_file):
    """Lấy độ dài bài nhạc từ metadata bằng vgmstream-cli."""
    try:
        res = subprocess.check_output([str(VGMSTREAM_EXE), "-m", str(audio_file)], text=True, stderr=subprocess.DEVNULL)
        for line in res.splitlines():
            if "play duration" in line:
                # e.g.: play duration: 18104879 samples (6:50.541 seconds)
                parts = line.split("(")
                if len(parts) > 1:
                    return parts[1].replace(")", "").strip()
    except Exception:
        pass
    return "N/A"

def main():
    start_time = time.time()
    print("=" * 70)
    print(" BỘ CÔNG CỤ TRÍCH XUẤT NHẠC GAME STELLA SORA ")
    print("=" * 70)
    print(f"Thư mục gốc game  : {ROOT_DIR}")
    print(f"Thư mục xuất nhạc : {OUTPUT_DIR}")
    print(f"Công cụ giải mã   : ww2ogg + vgmstream-cli")
    print("-" * 70)

    # 1. Quét tất cả các tệp .media.wem
    media_files = list(MEDIA_DIR.glob("*.media.wem"))
    if not media_files:
        print(f"[!] Không tìm thấy tệp .media.wem nào trong {MEDIA_DIR}")
        return

    print(f"[+] Tìm thấy tổng cộng {len(media_files)} tệp nhạc .media.wem trong InstallResource.")

    media_map = {}
    for mf in media_files:
        try:
            mid = int(mf.stem.split(".")[0])
            media_map[mid] = mf
        except ValueError:
            pass

    # 2. Phân loại theo SoundBanks
    associations = scan_soundbank_associations(list(media_map.keys()))

    # Chuẩn bị danh mục thư mục xuất
    for cat in CATEGORIES:
        (OUTPUT_DIR / cat).mkdir(parents=True, exist_ok=True)

    conversion_tasks = []
    catalog = []

    print("[+] Lên lịch chuyển đổi nhạc sang định dạng chuẩn OGG Vorbis...")
    for mid, mf in media_map.items():
        banks = associations.get(mid, [])
        cat = determine_category(banks)
        
        # Tạo tên file gợi nhớ: mid + bank gợi ý
        primary_bank = banks[0].replace(".bnk", "") if banks else "Audio"
        out_name = f"Track_{mid}_{primary_bank}.ogg"
        dst_path = OUTPUT_DIR / cat / out_name
        
        conversion_tasks.append((mf, dst_path))
        catalog.append({
            "id": mid,
            "filename": out_name,
            "category": cat,
            "category_desc": CATEGORIES[cat],
            "source_banks": banks,
            "size_bytes": mf.stat().st_size,
            "output_path": str(dst_path.relative_to(ROOT_DIR))
        })

    # 3. Chạy chuyển đổi đa luồng
    print(f"-> Đang tiến hành giải mã {len(conversion_tasks)} bản nhạc bằng {os.cpu_count() or 4} luồng xử lý...")
    success_count = 0
    fail_count = 0
    
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
        futures = {executor.submit(convert_single_wem, task): task for task in conversion_tasks}
        for future in as_completed(futures):
            ok, path, err = future.result()
            if ok:
                success_count += 1
            else:
                fail_count += 1
                print(f"[x] Thất bại khi chuyển đổi {path}: {err}")

    print(f"[V] Đã chuyển đổi thành công {success_count}/{len(conversion_tasks)} bản nhạc (.ogg).")

    # 4. Trích xuất các bản nhạc Cinematic & Ending Videos
    print("\n-> Đang xử lý các bản nhạc chủ đề & Ending Video...")
    cinematic_dir = OUTPUT_DIR / "07_Cinematic_Themes"
    video_targets = [
        ("Launch_BGM.mp4", "Launch_BGM_Title_Screen.mp4", "Launch_BGM_Title_Screen.wav", "Nhạc nền mở đầu game / Màn hình đăng nhập"),
        ("CH04ED-CH04ED_FP.mp4", "Ending_Chapter_04.mp4", "Ending_Chapter_04.wav", "Bài hát kết thúc Chương 4 (Ending Song Ch.4)"),
        ("CH06ED-CH06ED.mp4", "Ending_Chapter_06.mp4", "Ending_Chapter_06.wav", "Bài hát kết thúc Chương 6 (Ending Song Ch.6)"),
        ("CH09ED-CH09ED_FP.mp4", "Ending_Chapter_09.mp4", "Ending_Chapter_09.wav", "Bài hát kết thúc Chương 9 (Ending Song Ch.9)"),
        ("Launch.mp4", "Launch_Opening_Animation.mp4", "Launch_Opening_Animation.wav", "Hoạt họa & bài hát mở màn khởi động game")
    ]

    for vid_src_name, vid_out_name, wav_out_name, desc in video_targets:
        src_v = VIDEOS_DIR / vid_src_name
        if src_v.exists():
            dst_v = cinematic_dir / vid_out_name
            dst_w = cinematic_dir / wav_out_name
            
            # Copy video
            shutil.copy2(src_v, dst_v)
            # Trích xuất sang WAV thuần âm thanh
            ok = extract_video_audio(src_v, dst_w)
            
            catalog.append({
                "id": vid_src_name,
                "filename": wav_out_name,
                "category": "07_Cinematic_Themes",
                "category_desc": desc,
                "source_banks": [vid_src_name],
                "size_bytes": dst_v.stat().st_size,
                "output_path": str(dst_w.relative_to(ROOT_DIR))
            })
            print(f"  [+] Trích xuất hoàn tất: {vid_out_name} & {wav_out_name} ({desc})")

    # 5. Cập nhật thời lượng cho các bản nhạc lớn tiêu biểu
    print("\n-> Đang lập bảng tra cứu thông tin chi tiết...")
    for item in catalog:
        fpath = ROOT_DIR / item["output_path"]
        if fpath.exists():
            item["duration"] = get_track_duration(fpath)
            item["output_size_mb"] = round(fpath.stat().st_size / (1024 * 1024), 2)
        else:
            item["duration"] = "N/A"
            item["output_size_mb"] = 0

    # 6. Ghi tệp JSON Catalog
    json_path = OUTPUT_DIR / "MUSIC_CATALOG.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"[+] Đã lưu chỉ mục dữ liệu: {json_path}")

    # 7. Ghi tệp Markdown tra cứu DANH_SACH_NHAC.md
    md_path = OUTPUT_DIR / "DANH_SACH_NHAC.md"
    
    # Gom nhóm thống kê
    by_category = {}
    for item in catalog:
        cat = item["category"]
        by_category.setdefault(cat, []).append(item)

    total_size_mb = sum(
        f.stat().st_size for f in OUTPUT_DIR.rglob("*") if f.is_file()
    ) / (1024 * 1024)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# DANH MỤC NHẠC TRÍCH XUẤT TỪ STELLA SORA\n\n")
        f.write(f"- **Ngày trích xuất:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- **Tổng số bản nhạc trích xuất:** {len(catalog)} bài\n")
        f.write(f"- **Tổng dung lượng nhạc:** {total_size_mb:.2f} MB\n")
        f.write(f"- **Định dạng âm thanh:** OGG Vorbis chuẩn (lossless Wwise Vorbis remux) & WAV chất lượng cao\n")
        f.write(f"- **Tương thích:** Phát mượt mà trên tất cả trình phát nhạc hiện đại (VLC, Windows Media Player, Groove, Foobar2000, trình duyệt web, smartphone).\n\n")
        
        f.write("## 1. Tổng quan theo từng danh mục\n\n")
        f.write("| STT | Thư mục | Mô tả danh mục | Số lượng bài |\n")
        f.write("|:---:|:---|:---|:---:|\n")
        for idx, (cat, desc) in enumerate(CATEGORIES.items(), 1):
            count = len(by_category.get(cat, []))
            f.write(f"| {idx} | `{cat}/` | {desc} | **{count}** bài |\n")

        f.write("\n## 2. Chi tiết các bài nhạc theo danh mục\n\n")
        for cat, desc in CATEGORIES.items():
            tracks = by_category.get(cat, [])
            if not tracks:
                continue
            f.write(f"### {cat} — {desc}\n\n")
            f.write(f"*Tổng cộng: {len(tracks)} bản nhạc*\n\n")
            f.write("| Tên tệp | Thời lượng | Kích thước | SoundBank liên kết |\n")
            f.write("|:---|:---:|:---:|:---|\n")
            
            # Sắp xếp bài nhạc dung lượng lớn lên trước để người nghe dễ tìm bài hay nhất
            tracks_sorted = sorted(tracks, key=lambda x: x["output_size_mb"], reverse=True)
            for t in tracks_sorted:
                banks_str = ", ".join(t["source_banks"]) if t["source_banks"] else "N/A"
                f.write(f"| `{t['filename']}` | {t['duration']} | {t['output_size_mb']} MB | {banks_str} |\n")
            f.write("\n")

    print(f"[+] Đã tạo tài liệu tra cứu: {md_path}")
    elapsed = time.time() - start_time
    print("-" * 70)
    print(f"[HOÀN TẤT] Quá trình trích xuất hoàn thành trong {elapsed:.2f} giây!")
    print(f"Toàn bộ nhạc được lưu tại: {OUTPUT_DIR}")
    print("=" * 70)

if __name__ == "__main__":
    main()
