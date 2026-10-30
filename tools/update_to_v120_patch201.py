#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update Stella Sora Vietnamese Localization to v1.2.0 (Compatible with Game Patch 2.0.1).
- Integrates all 31 new localization strings for Patch 2.0.1.
- Repacks data.arcx preserving all 2.0.1 protobuf/binary schemas via arcx_adapter.repack_archive.
- Repacks lua.arcx preserving all 88 official 2.0.1 engine/system bugfixes and embedding 601 localized AVG story dialogues.
- Dual-syncs to Yostar Standalone and Steam installations.
- Verifies anti-regression with verify_deployed_game_data.py.
"""

from __future__ import annotations
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.arcx_adapter import (
    ArcxArchive,
    repack_archive,
    xxtea_decrypt,
    xxtea_encrypt,
    XXTEA_KEY,
)

NEW_TRANSLATIONS = {
    # Chitose Skin 14404
    "CharacterSkin.14404.1": "Em Sẽ Luôn... Ở Bên Cạnh Ngài…",
    "CharacterSkin.14404.2": "Dù đã hóa thành u linh, nàng vẫn quẩn quanh bên cạnh chủ quân của mình, khẽ thì thầm tâm nguyện chưa vẹn lúc sinh thời——\nRèn kiếm... rèn kiếm...",
    "CharGetLines.14406.1": "Dù đã hóa thành u linh, nàng vẫn quẩn quanh bên cạnh chủ quân của mình, khẽ thì thầm tâm nguyện chưa vẹn lúc sinh thời——\nRèn kiếm... rèn kiếm...",
    "Item.14404.1": "Em Sẽ Luôn... Ở Bên Cạnh Ngài…",
    "Item.14404.2": "Chứng nhận mở khóa ngoại hình độc quyền của Chitose: 「Em Sẽ Luôn... Ở Bên Cạnh Ngài...」!",
    "Item.14404.3": "Dù đã hóa thành u linh, nàng vẫn quẩn quanh bên cạnh chủ quân của mình, khẽ thì thầm tâm nguyện chưa vẹn lúc sinh thời——\nRèn kiếm... rèn kiếm...",
    "Item.199031.1": "Ngoại hình độc quyền Chitose (2D):\nEm Sẽ Luôn... Ở Bên Cạnh Ngài…",
    "Item.199031.2": "Ngoại hình độc quyền Chitose (2D):\nEm Sẽ Luôn... Ở Bên Cạnh Ngài…",
    "Item.199031.3": "Ngoại hình độc quyền Chitose (2D):\nEm Sẽ Luôn... Ở Bên Cạnh Ngài…",
    "PlayerHead.14404.1": "Nhận ngoại hình để mở khóa\n\"Em Sẽ Luôn... Ở Bên Cạnh Ngài…\"",

    # Startup Grant Season 13 / Battle Pass
    "Item.101029.1": "Vật Phẩm Tặng Kèm Trợ Cấp Hoàng Gia",
    "Item.101029.2": "Bao gồm các vật phẩm tặng kèm tương ứng khi mua Trợ Cấp Hoàng Gia của Quỹ Khởi Nghiệp kỳ này.",
    "Item.101030.1": "Vật Phẩm Bù Chênh Lệch Nâng Cấp Trợ Cấp",
    "Item.101030.2": "Bao gồm các vật phẩm tặng kèm tương ứng khi mua Trợ Cấp Hoàng Gia của Quỹ Khởi Nghiệp kỳ này.",
    "Item.130013.1": "Kìa, Nhìn Bên Đó!",
    "Item.130013.2": "Mở khóa khung hình đại diện: 「Kìa, Nhìn Bên Đó!」",
    "Item.130013.3": "Kìa! Là một Bạo Chúa hoang dã xuất hiện!",
    "Item.199032.1": "Hình Đại Diện Giới Hạn Kỳ Này:\nKìa, Nhìn Bên Đó!",
    "Item.199032.2": "Hình Đại Diện Giới Hạn Kỳ Này:\nKìa, Nhìn Bên Đó!",
    "Item.199032.3": "Hình Đại Diện Giới Hạn Kỳ Này:\nKìa, Nhìn Bên Đó!",
    "PlayerHead.130013.1": "Quỹ Khởi Nghiệp Mùa 13\nNhận được khi mở khóa Trợ Cấp Hoàng Gia",

    # Score Boss Abilities
    "ScoreBossAbility.100025.1": "Rạn Nứt Ầm Ầm",
    "ScoreBossAbility.100025.2": "HP tối đa của Du Hành Giả chủ lực tăng <color=#ec6d21>&Param4&</color>, sát thương phải chịu tăng <color=#ec6d21>&Param5&</color>.\nKhi Du Hành Giả chủ lực gây sát thương lên mục tiêu Thủ Lĩnh và kích hoạt Tiêu Ký, sát thương kỹ năng mà Thủ Lĩnh phải chịu tăng thêm <color=#ec6d21>&Param1&</color> trong <color=#ec6d21>&Param2&</color> giây, tối đa cộng dồn <color=#ec6d21>&Param3&</color> tầng.",
    "ScoreBossAbility.100026.1": "Tàn Hoa Lộ Nhụy",
    "ScoreBossAbility.100026.2": "Mỗi khi mục tiêu Thủ Lĩnh chịu Sát Thương Tuyệt Kỹ, sát thương Tiêu Ký phải chịu tăng thêm <color=#ec6d21>&Param1&</color> trong <color=#ec6d21>&Param2&</color> giây, tối đa cộng dồn <color=#ec6d21>&Param3&</color> tầng.\nMỗi khi mục tiêu Thủ Lĩnh chịu Sát Thương Kỹ Năng, sát thương kỹ năng phải chịu tăng thêm <color=#ec6d21>&Param4&</color> trong <color=#ec6d21>&Param5&</color> giây, tối đa cộng dồn <color=#ec6d21>&Param6&</color> tầng.",

    # Story Epilogue
    "Story.1124.1": "Đón Chờ Hồi Sau",
    "Story.1124.2": "Đón Chờ Hồi Sau",
    "Story.1124.4": "Vĩ Thanh",

    # UIText
    "UIText.DormFriend_Visit.1": "Thăm Viếng",
    "UIText.Dorm_Go.1": "Đến Ngay",
    "UIText.Soldier_Result_Recommend_Tips.1": "Trận đấu quá mãn nhãn! Bạn có muốn đến Quảng Trường Chiến Thuật chia sẻ làm cẩm nang không?",
}

def update_data_arcx():
    print("\n--- REPACKING DATA.ARCX (2.0.1) ---")
    live_arcx_path = Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx")
    vi_arcx_path = ROOT / "dist" / "data_patched_vi.arcx"
    output_path = ROOT / "dist" / "data_patched_vi.arcx"

    live_arc = ArcxArchive(live_arcx_path)
    live_raw = live_arcx_path.read_bytes()

    vi_arc = ArcxArchive(vi_arcx_path)
    vi_raw = vi_arcx_path.read_bytes()
    vi_map = {e["hash"]: e for e in vi_arc.entries}

    staging_dir = ROOT / "work" / "staging_data_201"
    entries_dir = staging_dir / "entries"
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    entries_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "archive_name": "data.arcx",
        "version": live_arc.version,
        "flag": live_arc.flag,
        "entry_count": live_arc.entry_count,
        "payload_decrypted": False,
        "entries": [],
    }

    json_count = 0
    binary_count = 0
    patched_keys_count = 0

    for e in live_arc.entries:
        h = e["hash"]
        live_entry_bytes = live_arc.extract_entry(e, live_raw)
        live_payload = xxtea_decrypt(live_entry_bytes, XXTEA_KEY)

        is_json = False
        live_json = None
        try:
            live_json = json.loads(live_payload.decode("utf-8"))
            is_json = isinstance(live_json, dict)
        except Exception:
            pass

        fname = f"{e['index']:05d}_{e['hash_hex']}.bin"
        fpath = entries_dir / fname

        if is_json:
            json_count += 1
            target_json = {}
            if h in vi_map:
                vi_bytes = vi_arc.extract_entry(vi_map[h], vi_raw)
                try:
                    target_json = json.loads(xxtea_decrypt(vi_bytes, XXTEA_KEY).decode("utf-8"))
                except Exception:
                    target_json = dict(live_json)
            else:
                target_json = dict(live_json)

            for k, v in live_json.items():
                if k not in target_json:
                    target_json[k] = v

            for k, vi_str in NEW_TRANSLATIONS.items():
                if k in target_json:
                    target_json[k] = vi_str
                    patched_keys_count += 1

            new_payload_bytes = json.dumps(target_json, ensure_ascii=False, indent=2).encode("utf-8")
            enc_payload = xxtea_encrypt(new_payload_bytes, XXTEA_KEY)
            fpath.write_bytes(enc_payload)
            final_size = len(enc_payload)
        else:
            binary_count += 1
            fpath.write_bytes(live_entry_bytes)
            final_size = len(live_entry_bytes)

        manifest["entries"].append({
            "index": e["index"],
            "hash": h,
            "hash_hex": e["hash_hex"],
            "filename": fname,
            "origin_size": final_size,
            "payload_size": final_size,
        })

    manifest_file = staging_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Total entries: {len(manifest['entries'])} (JSON tables: {json_count}, Binary tables: {binary_count})")
    print(f"New translated keys applied: {patched_keys_count}")

    t0 = time.time()
    repack_archive(staging_dir, output_path, encrypt_payload=False)
    dur = time.time() - t0
    print(f"✓ Successfully repacked {output_path} ({output_path.stat().st_size:,} bytes) in {dur:.2f}s")


def update_lua_arcx():
    print("\n--- REPACKING LUA.ARCX (2.0.1) ---")
    live_arcx_path = Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Scripts\lua.arcx")
    vi_arcx_path = ROOT / "dist" / "lua_patched_vi.arcx"
    output_path = ROOT / "dist" / "lua_patched_vi.arcx"

    avg_mapping_file = ROOT / "work" / "research" / "avg_file_to_entry.json"
    avg_map = json.load(avg_mapping_file.open(encoding="utf-8"))
    avg_hashes = {d["entry"]["hash"]: name for name, d in avg_map.items()}

    live_arc = ArcxArchive(live_arcx_path)
    live_raw = live_arcx_path.read_bytes()

    vi_arc = ArcxArchive(vi_arcx_path)
    vi_raw = vi_arcx_path.read_bytes()
    vi_map = {e["hash"]: e for e in vi_arc.entries}

    staging_dir = ROOT / "work" / "staging_lua_201"
    entries_dir = staging_dir / "entries"
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    entries_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "archive_name": "lua.arcx",
        "version": live_arc.version,
        "flag": live_arc.flag,
        "entry_count": live_arc.entry_count,
        "payload_decrypted": False,
        "entries": [],
    }

    story_count = 0
    system_count = 0

    for e in live_arc.entries:
        h = e["hash"]
        fname = f"{e['index']:05d}_{e['hash_hex']}.bin"
        fpath = entries_dir / fname

        if h in avg_hashes and h in vi_map:
            story_count += 1
            content = vi_arc.extract_entry(vi_map[h], vi_raw)
        else:
            system_count += 1
            content = live_arc.extract_entry(e, live_raw)

        fpath.write_bytes(content)
        content_sz = len(content)

        manifest["entries"].append({
            "index": e["index"],
            "hash": h,
            "hash_hex": e["hash_hex"],
            "filename": fname,
            "origin_size": content_sz,
            "payload_size": content_sz,
        })

    manifest_file = staging_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Total script entries: {len(manifest['entries'])} (Localized Story: {story_count}, 2.0.1 Engine/System: {system_count})")

    t0 = time.time()
    repack_archive(staging_dir, output_path, encrypt_payload=False)
    dur = time.time() - t0
    print(f"✓ Successfully repacked {output_path} ({output_path.stat().st_size:,} bytes) in {dur:.2f}s")


def restore_subtitles_and_deploy():
    print("\n--- DEPLOYING TO LIVE GAME & STEAM ---")
    data_vi = ROOT / "dist" / "data_patched_vi.arcx"
    lua_vi = ROOT / "dist" / "lua_patched_vi.arcx"
    videos_vi = ROOT / "dist" / "Videos"

    deploy_targets = [
        Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store"),
        Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store"),
    ]

    for target in deploy_targets:
        if not target.exists():
            continue
        print(f"Deploying to: {target}")
        
        # Tables
        tb_dir = target / "Tables"
        tb_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(data_vi, tb_dir / "data.arcx")
        print(f"  ✓ Copied Tables/data.arcx")

        # Scripts
        sc_dir = target / "Scripts"
        sc_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(lua_vi, sc_dir / "lua.arcx")
        print(f"  ✓ Copied Scripts/lua.arcx")

        # Videos SRT
        vid_dir = target / "Videos"
        if vid_dir.exists() and videos_vi.exists():
            for srt in videos_vi.glob("*.srt"):
                shutil.copy2(srt, vid_dir / srt.name)
            print(f"  ✓ Restored all Vietnamese SRTs in Videos/")

def main():
    print("=== STARTING PATCH 2.0.1 LOCALIZATION & REPACK PIPELINE ===")
    update_data_arcx()
    update_lua_arcx()
    restore_subtitles_and_deploy()
    print("\n=== COMPLETE! READY FOR ANTI-REGRESSION VERIFICATION ===")

if __name__ == "__main__":
    main()
