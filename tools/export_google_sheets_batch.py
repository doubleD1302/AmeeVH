#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stella Sora - Google Sheets Batch Data Generator
Trích xuất toàn diện dữ liệu phục vụ đồng bộ Google Spreadsheet:
1. Toàn bộ 322 mục danh từ từ config/glossary.json phân nhóm khoa học.
2. 41 hồ sơ nhân vật & ma trận xưng hô, khẩu khí từ CHARACTER_VOICE_PROFILES.json, CHARACTER_RELATIONSHIP_MATRIX.json, CHARACTER_ROSTER.json.
3. Toàn bộ kịch bản Chương 1 (STm01_01 -> STm01_10, 12 files, 1303 câu) và Chương 2 (STm02_01 -> STm02_11, 14 files, 1503 câu),
   phân tách rõ: Tên Màn, Mã câu ID, Chủ thể / Người nói, Lời thoại gốc EN, Bản dịch tham khảo từ pillars_translation_cache.json và batch_10000_avg_clean.json.
4. Xuất JSON chuẩn hóa tại work/batches/google_sheets_batch_data.json.
"""

import os
import sys
import json
import struct
import re
from pathlib import Path
from collections import Counter, OrderedDict

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from test_lua_roundtrip import Lua53Chunk
from extract_clean_10k_avg import extract_clean_lua53_strings

# ==============================================================================
# 1. TRÍCH XUẤT VÀ PHÂN NHÓM GLOSSARY (322 MỤC)
# ==============================================================================

def load_and_classify_glossary():
    gloss_path = ROOT / "config" / "glossary.json"
    with open(gloss_path, "r", encoding="utf-8") as f:
        gloss_data = json.load(f)

    entries = gloss_data.get("entries", [])
    classified_entries = []

    def get_group(cat, src, tgt):
        c = (cat or "").lower()
        if "monster" in c or "boss" in c:
            return "5. Quái vật & Sinh vật"
        if "combat" in c or "skill" in c:
            return "4. Kỹ năng & Giao diện chiến đấu"
        if "location" in c or "dungeon" in c or c == "calendar":
            return "1. Địa danh & Bối cảnh thế giới"
        if any(k in c for k in ["faction", "organization", "character", "npc", "role", "title", "race"]):
            return "2. Phe phái, Tổ chức & Nhân vật"
        if any(k in c for k in ["ui", "item", "progression", "event", "tech", "concept", "vehicle / weapon"]):
            return "3. Chế độ game, Vật phẩm & Trang bị"
        if "lore" in c:
            return "1. Địa danh & Bối cảnh thế giới"
        return "6. Thành ngữ & Cụm từ đặc biệt"

    group_counts = Counter()
    for e in entries:
        src = e.get("source", "").strip()
        tgt = e.get("target", "").strip()
        cat = e.get("category", "")
        status = e.get("status", "approved")
        notes = e.get("notes", "")
        group = get_group(cat, src, tgt)
        group_counts[group] += 1
        classified_entries.append({
            "source": src,
            "target": tgt,
            "group": group,
            "category_original": cat,
            "status": status,
            "notes": notes
        })

    # Sắp xếp theo group rồi theo source
    classified_entries.sort(key=lambda x: (x["group"], x["source"].lower()))
    return classified_entries, dict(group_counts)


# ==============================================================================
# 2. HỒ SƠ 41 NHÂN VẬT & MA TRẬN XƯNG HÔ (VOICE BIBLE & MATRIX)
# ==============================================================================

def load_character_voice_and_matrix():
    char_ctx_dir = ROOT / "work" / "character_context_20261023_r01"

    # 1. Roster
    roster_path = char_ctx_dir / "CHARACTER_ROSTER.json"
    with open(roster_path, "r", encoding="utf-8") as f:
        roster_data = json.load(f)
    roster_chars = {c["id"]: c for c in roster_data.get("characters", [])}

    # 2. Voice Profiles
    profiles_path = char_ctx_dir / "CHARACTER_VOICE_PROFILES.json"
    with open(profiles_path, "r", encoding="utf-8") as f:
        prof_data = json.load(f)
    profiles_list = prof_data.get("profiles", [])

    # 3. Relationship Matrix
    matrix_path = char_ctx_dir / "CHARACTER_RELATIONSHIP_MATRIX.json"
    with open(matrix_path, "r", encoding="utf-8") as f:
        matrix_data = json.load(f)

    # 4. Standard Relationship Pairs from Voice Bible & Sheets Pipeline
    standard_relationship_pairs = [
        {
            "speaker": "Amber (Kohaku)",
            "speaker_id": "char:103",
            "listener": "Iris (Ayame)",
            "listener_id": "char:111",
            "pronouns": "Xưng: tớ / Gọi: cậu, Iris",
            "tone": "Điềm đạm, ấm áp, câu ngắn gọn, quan sát tinh tế. Kỷ niệm gắn bó từ trại trẻ mồ côi.",
            "sample_dialogue": "“Ừ. Tớ vẫn đang nghe đây.”\n“Thế thì tớ sẽ vừa đi vừa nghĩ về hai cậu nhé.”",
            "do_not": "Không tự thêm 'nè/nha/hì hì' làm nhân vật quá nhí nhảnh."
        },
        {
            "speaker": "Amber (Kohaku)",
            "speaker_id": "char:103",
            "listener": "Trekker (Người chơi / Chỉ huy)",
            "listener_id": "char:1",
            "pronouns": "Xưng: tôi / tớ / Gọi: Chỉ huy, Cậu",
            "tone": "Lịch sự, bình thản, chân thành, đối tác đồng hành đáng tin cậy.",
            "sample_dialogue": "“Chào mừng Chỉ huy đã trở lại.”\n“Đừng lo, có tôi ở đây rồi.”",
            "do_not": "Tuyệt đối không tự ý xưng 'em - anh'."
        },
        {
            "speaker": "Iris (Ayame)",
            "speaker_id": "char:111",
            "listener": "Amber (Kohaku)",
            "listener_id": "char:103",
            "pronouns": "Xưng: tớ / Gọi: cậu, Amber",
            "tone": "Nhanh nhẹn, thực tế, lo toan tài chính & hậu cần, hay cằn nhằn nhưng rất quan tâm bạn bè.",
            "sample_dialogue": "“Am-ber! Cậu có nghe rõ không đấy!?”\n“Bộ ai đời lại đi ăn đồ ăn cho mèo bao giờ chứ!?”",
            "do_not": "Không làm mọi câu yếu đuối, ngập ngừng (tránh lạm dụng 'ừm/tớ nghĩ')."
        },
        {
            "speaker": "Iris (Ayame)",
            "speaker_id": "char:111",
            "listener": "Trekker (Người chơi / Chỉ huy)",
            "listener_id": "char:1",
            "pronouns": "Xưng: tớ / em / Gọi: Chỉ huy, Cậu",
            "tone": "Nhiệt tình, tinh nghịch, hay đùa về tài chính và hợp đồng làm ăn.",
            "sample_dialogue": "“Chỉ huy, hôm nay hội quán mình có hợp đồng béo bở này!”",
            "do_not": "Không nói trống không hoặc dùng từ ngữ thô lỗ."
        },
        {
            "speaker": "Noya",
            "speaker_id": "char:112",
            "listener": "Amber & Iris",
            "listener_id": "char:103,111",
            "pronouns": "Xưng: tớ / mình / Gọi: hai cậu, các cậu",
            "tone": "Lạc quan, vô tư, giàu trí tưởng tượng, luôn mơ về ngày hội quán nổi tiếng phát tài.",
            "sample_dialogue": "“Nếu trái tim bọn mình thực sự đồng điệu thì kiểu gì chẳng tìm thấy nhau!”",
            "do_not": "Không dùng giọng điệu trầm u uất hoặc nói chuyện quá già dặn."
        },
        {
            "speaker": "Tilia",
            "speaker_id": "char:107",
            "listener": "Trekker (Chỉ huy) / Đồng đội",
            "listener_id": "char:1",
            "pronouns": "Xưng: tôi / Gọi: Ngài, Chỉ huy, Các vị",
            "tone": "Chuẩn mực hiệp sĩ, đĩnh đạc, coi trọng danh dự, luật pháp và bảo vệ kẻ yếu.",
            "sample_dialogue": "“Tận trung với Đế chế, gìn giữ công lý, bảo vệ người yếu thế...”",
            "do_not": "Không cợt nhả, không dùng từ lóng teen, không xưng hô suồng sã."
        },
        {
            "speaker": "Firenze",
            "speaker_id": "char:110",
            "listener": "Trekker (Chỉ huy) / Đối tác",
            "listener_id": "char:1",
            "pronouns": "Xưng: tôi / Gọi: Ngài, Quý cô, Chỉ huy",
            "tone": "Quý phái, sắc sảo, câu từ lịch thiệp, tư duy liên minh và đàm phán thương vụ đôi bên cùng có lợi.",
            "sample_dialogue": "“Tôi tin rằng sự hợp tác giữa chúng ta sẽ mang lại lợi ích to lớn cho cả hai bên.”",
            "do_not": "Không dùng ngôn ngữ kiếm hiệp cổ trang sáo rỗng."
        },
        {
            "speaker": "Ruby & Sapphire",
            "speaker_id": "char:980",
            "listener": "Firenze",
            "listener_id": "char:110",
            "pronouns": "Xưng: chúng tôi / Gọi: Tiểu thư Firenze, Lady Firenze",
            "tone": "Thuộc hạ trung thành, cung kính, tuyệt đối phục tùng mệnh lệnh.",
            "sample_dialogue": "“Ý nguyện của tiểu thư là mệnh lệnh của chúng tôi.”",
            "do_not": "Tuyệt đối không xưng hô ngang hàng với Firenze."
        },
        {
            "speaker": "Minova",
            "speaker_id": "char:132",
            "listener": "Gia tộc Tàn Phong & Đồng đội",
            "listener_id": "clan:ashwind",
            "pronouns": "Xưng: tôi / Minova / Gọi: các cậu, mọi người",
            "tone": "Đội trưởng bản lĩnh, dứt khoát, nghĩa khí, luôn quan tâm bảo bọc người dân Khu Tro Tàn.",
            "sample_dialogue": "“Khu Tro Tàn là nhà của chúng ta. Tôi tuyệt đối không để ai chà đạp lên nơi này.”",
            "do_not": "Không dùng từ ngữ quý tộc hoa mỹ, giữ chất phong trần, cương trực."
        },
        {
            "speaker": "Kasimira",
            "speaker_id": "char:108",
            "listener": "Trekker & Đồng đội",
            "listener_id": "char:1",
            "pronouns": "Xưng: tôi / Kasimira / Gọi: Chỉ huy, các bạn",
            "tone": "Vững vàng, chín chắn, thấu hiểu lòng người, khéo léo và chu đáo.",
            "sample_dialogue": "“Nghỉ tay chút đã nhé, tôi vừa gấp xong vài con hạc giấy tặng mọi người đây.”",
            "do_not": "Không rải 'bé cưng/nhóc tỳ' hoặc giọng tán tỉnh bừa bãi."
        },
        {
            "speaker": "Jinglin",
            "speaker_id": "char:117",
            "listener": "Khách hàng & Trekker",
            "listener_id": "char:1",
            "pronouns": "Xưng: tôi / Jinglin / Gọi: quý khách, bạn",
            "tone": "Sáng rõ, hiếu khách, tràn đầy năng lượng của một quản lý nhà hàng chuyên nghiệp.",
            "sample_dialogue": "“Dù là quản lý Huaijing Restaurant hay làm Lữ Khách, tôi cam đoan sẽ không làm bạn thất vọng!”",
            "do_not": "Không gán tính cách nhà khoa học cuồng thí nghiệm hay 'bổn cô nương'."
        },
        {
            "speaker": "Trekker (Nhà Thám Hiểm / Chỉ huy)",
            "speaker_id": "char:1",
            "listener": "Tất cả nhân vật",
            "listener_id": "all",
            "pronouns": "Xưng: tôi / mình / Gọi: cậu, bạn, tên nhân vật",
            "tone": "Người chơi chính, điềm tĩnh, thân thiện, đáng tin cậy và quyết đoán.",
            "sample_dialogue": "“Mọi người cẩn thận, phía trước có dấu hiệu bất thường.”",
            "do_not": "Không tự ý xưng 'anh' gọi 'em' khi chưa xác định mối quan hệ thân mật."
        }
    ]

    characters_result = []
    for p in profiles_list:
        cid = p.get("character_id")
        name_en = p.get("name_en", "")
        r_info = roster_chars.get(cid, {})
        name_vi = r_info.get("name_vi", name_en)
        affil = r_info.get("affiliation_en", "Chưa rõ")
        style = p.get("vi_style_proposal") or {}

        observed = p.get("observed_traits", [])
        traits_desc = " ".join([o.get("description_vi", "") for o in observed if isinstance(o, dict)])
        if not traits_desc:
            traits_desc = "Hồ sơ lưu trữ game, phong cách tự nhiên theo ngữ cảnh nguồn."

        characters_result.append({
            "character_id": cid,
            "name_en": name_en,
            "name_vi": name_vi,
            "affiliation": affil,
            "status": p.get("status", "pending_character_evidence"),
            "core_traits": traits_desc,
            "sentence_rhythm": style.get("sentence_rhythm", "Theo sát nhịp điệu và ngữ cảnh nguồn gốc."),
            "self_pronouns": style.get("self_pronouns", []),
            "address_by_listener": style.get("address_by_listener", []),
            "catchphrases": style.get("catchphrases", []),
            "do_not": style.get("do_not", ["Không thêm kính ngữ, biệt danh hoặc thán từ không có căn cứ trong nguồn."])
        })

    return characters_result, standard_relationship_pairs


# ==============================================================================
# 3. TRÍCH XUẤT TOÀN BỘ CHƯƠNG 1 (12 FILES) VÀ CHƯƠNG 2 (14 FILES)
# ==============================================================================

def build_actor_preset_map():
    avg_char_path = ROOT / "work" / "research" / "lua_tree" / "Game" / "UI" / "Avg" / "_en" / "Preset" / "AvgCharacter.lua"
    actor_names = {
        "0": "Dẫn chuyện",
        "1": "Trekker (Người chơi)",
        "avg3_100": "Trekker (Người chơi)",
        "avg3_999": "??? (Kẻ phản bội bí ẩn)"
    }
    if avg_char_path.exists():
        raw_ac = avg_char_path.read_bytes()
        p_ac = Lua53Chunk(raw_ac)
        p_ac.read_bytes(34)
        proto_ac = p_ac.parse_proto()
        k_ac = [val[1].decode("utf-8", errors="ignore") if ktype in (4,20) else "" for ktype, val in proto_ac["constants"]]
        for i in range(len(k_ac) - 1):
            c = k_ac[i]
            nxt = k_ac[i+1]
            if (c.startswith("avg1_") or c.startswith("avg2_") or c.startswith("avg3_")) and nxt and not nxt.startswith("avg") and not nxt.startswith("#") and nxt not in ("reuse", "ver"):
                actor_names[c] = nxt

    # Bổ sung từ roster
    roster_path = ROOT / "work" / "character_context_20261023_r01" / "CHARACTER_ROSTER.json"
    if roster_path.exists():
        with open(roster_path, "r", encoding="utf-8") as f:
            roster = json.load(f)
        for ch in roster.get("characters", []):
            cid = ch.get("game_character_id")
            name = ch.get("name_en")
            if cid and name:
                actor_names[f"avg1_{cid}"] = name
                actor_names[f"avg2_{cid}"] = name
                actor_names[f"avg3_{cid}"] = name

    # Bổ sung các tên chuẩn cố định
    actor_names["avg1_112"] = "Noya"
    actor_names["avg1_103"] = "Amber"
    actor_names["avg1_111"] = "Iris"
    actor_names["avg1_107"] = "Tilia"
    actor_names["avg1_110"] = "Firenze"
    actor_names["avg1_132"] = "Minova"
    actor_names["avg1_117"] = "Jinglin"
    return actor_names


def parse_scene_lua_bytecode(fpath: Path, actor_names: dict):
    raw = fpath.read_bytes()
    p = Lua53Chunk(raw)
    p.read_bytes(34)
    proto = p.parse_proto()
    code = proto["code"]
    k = proto["constants"]

    def get_k(idx):
        if idx < len(k):
            kt, v = k[idx]
            if kt in (4, 20): return v[1].decode("utf-8", errors="ignore")
            elif kt == 1: return str(v)
            elif kt in (3, 19):
                try: return str(struct.unpack("<d", v)[0])
                except: return str(v)
        return ""

    num_insts = len(code) // 4
    registers = {}
    mapping = {}

    for i in range(num_insts):
        inst = struct.unpack("<I", code[i*4:(i+1)*4])[0]
        op = inst & 0x3F
        a = (inst >> 6) & 0xFF
        b = (inst >> 23) & 0x1FF
        c = (inst >> 14) & 0x1FF
        bx = (inst >> 14) & 0x3FFFF

        if op == 0: registers[a] = registers.get(b)
        elif op == 1: registers[a] = get_k(bx)
        elif op == 11: registers[a] = []
        elif op == 43:
            target = registers.get(a)
            if isinstance(target, list):
                for r_idx in range(1, b + 1):
                    target.append(registers.get(a + r_idx))
        elif op == 10:
            key = get_k(b - 256) if b >= 256 else registers.get(b)
            val = get_k(c - 256) if c >= 256 else registers.get(c)
            target = registers.get(a)
            if isinstance(target, dict): target[key] = val
            elif isinstance(target, list):
                d = {"_items": target, key: val}
                registers[a] = d
            if key == "param" and isinstance(target, dict) and "cmd" in target:
                cmd = target["cmd"]
                param = val
                if isinstance(param, list):
                    if cmd == "SetIntro":
                        for text in param:
                            if isinstance(text, str) and len(text) > 0 and not text.startswith("0"):
                                mapping[text] = "Dẫn chuyện"
                    elif cmd == "SetTalk":
                        actor_id = param[1] if len(param) > 1 and isinstance(param[1], str) else "0"
                        spk = actor_names.get(actor_id, actor_id if actor_id else "Dẫn chuyện")
                        for t in param:
                            if isinstance(t, str) and any(ch.isalpha() for ch in t) and (" " in t or len(t) > 12):
                                if t not in ["SetTalk", "default", "Linear", "OutSine", "none", "Clear"]:
                                    mapping[t] = spk
                    elif cmd == "SetChoiceBegin":
                        for opt in param:
                            if isinstance(opt, list):
                                for o in opt:
                                    if isinstance(o, str) and len(o) > 0 and any(ch.isalpha() for ch in o):
                                        mapping[o] = "Trekker (Lựa chọn)"
                            elif isinstance(opt, str) and len(opt) > 0 and any(ch.isalpha() for ch in opt):
                                mapping[opt] = "Trekker (Lựa chọn)"
                    elif cmd == "SetBubble":
                        actor_id = param[1] if len(param) > 1 and isinstance(param[1], str) else "0"
                        spk = actor_names.get(actor_id, actor_id if actor_id else "Dẫn chuyện")
                        for t in param:
                            if isinstance(t, str) and any(ch.isalpha() for ch in t) and (" " in t or len(t) > 12):
                                mapping[t] = spk
    return mapping


SCENE_TITLES = {
    # CHƯƠNG 1 (12 màn)
    "STm01_01": "Màn 01: Hồi Một - Khởi Đầu Thức Tỉnh (Act One - The Awakening Reset)",
    "STm01_02": "Màn 02: Cửa Hàng Hồn Thạch & Đế Quốc Grace (Soul Shop & Grace Imperium)",
    "STm01_03": "Màn 03: Trước Cổng Cửa Hàng Hồn Thạch (Soul Stone Shop Entrance)",
    "STm01_04": "Màn 04: Hầm Cầu Thủy Lộ (Waterway Bridge Underpass)",
    "STm01_05": "Màn 05: Hồi Năm - Ngọn Gió Khu Tro Tàn (Act Five - Winds of Ash District)",
    "STm01_06": "Màn 06: Hồi Sáu - Tung Cánh Nơi Tro Tàn (Act Six - Flying from the Ash)",
    "STm01_07": "Màn 07: Hồi Bảy - Một Nguyện Ước Khác Biệt (Act Seven - A Different Kind of Wish)",
    "STm01_08_a": "Màn 08a: Gia Tộc Tàn Phong (Ashwind Clan)",
    "STm01_08_b": "Màn 08b: Kết Thúc - Tương Lai Không Còn Lữ Khách (The End - A Future Without Trekkers)",
    "STm01_08_c": "Màn 08c: Hồi Tám - Món Tráng Miệng Sau Bữa Tối (Act Eight - After-Dinner Dessert)",
    "STm01_09": "Màn 09: Hồi Chín - Cách Hàn Gắn Ký Ức (Act Nine - How Memories Are Mended)",
    "STm01_10": "Màn 10: Hồi Mười - Quyền Giải Thích Cuối Cùng (Act Ten - Final Interpretation)",

    # CHƯƠNG 2 (14 màn)
    "STm02_01": "Màn 01: Hồi Một - Loxy và Công Ty (Act One - Loxy and the Company)",
    "STm02_02_a": "Màn 02a: Hồi Hai - Đột Nhập Nửa Đêm (Act Two - Midnight Infiltration)",
    "STm02_02_b": "Màn 02b: Hồi Hai - Cải Trang Điều Tra (Act Two - Disguised Investigation)",
    "STm02_02_c": "Màn 02c: Hồi Kết - Một Hồi Kết Bất Tận (The End - An Interminable End)",
    "STm02_03_a": "Màn 03a: Hồi Ba - Ánh Mắt Trong Đêm (Act Three - Gaze in the Dark)",
    "STm02_03_b": "Màn 03b: Hồi Ba - Chờ Hết Giờ Làm (Act Three - Waiting for Clock Out)",
    "STm02_04": "Màn 04: Hồi Bốn - Thiếu Nữ Áo Đen (Act Four - Girl in Black)",
    "STm02_05": "Màn 05: Hồi Năm - Tinh Thần Võ Sĩ (Act Five - Code of Honor)",
    "STm02_06": "Màn 06: Hồi Sáu - Đặc Quyền Công Ty (Act Six - Company Privilege)",
    "STm02_07": "Màn 07: Hồi Bảy - Đặc Quyền Kinh Doanh Độc Quyền (Act Seven - Exclusive Franchise)",
    "STm02_08": "Màn 08: Hầm Kho Đế Quốc Grace (Grace Imperium Vault)",
    "STm02_09": "Màn 09: Phố Cảnh Đỏ Rực (Scarlet Sights Street)",
    "STm02_10": "Màn 10: Hành Lang Cầu Thủy Lộ (Waterway Bridge Corridor)",
    "STm02_11": "Màn 11: Đoạn Kết - Khởi Đầu Mới (Epilogue - A New Beginning)"
}


def extract_chapters_data():
    lua_dir = ROOT / "work" / "research" / "lua_tree" / "Game" / "UI" / "Avg" / "_en" / "Config"

    # Cache nạp
    cache_ptc_path = ROOT / "work" / "batches" / "pillars_translation_cache.json"
    with open(cache_ptc_path, "r", encoding="utf-8") as f:
        cache_ptc = json.load(f)

    clean_path = ROOT / "work" / "batches" / "batch_10000_avg_clean.json"
    with open(clean_path, "r", encoding="utf-8") as f:
        clean_dict = json.load(f)

    actor_names = build_actor_preset_map()

    def process_chapter(prefix, chapter_name):
        files = sorted([f for f in os.listdir(lua_dir) if f.startswith(prefix) and f.endswith(".lua")])
        chapter_scenes = []
        total_chapter_lines = 0

        for f in files:
            scene_id = f[:-4]
            fpath = lua_dir / f
            raw_strings = extract_clean_lua53_strings(fpath)
            spk_map = parse_scene_lua_bytecode(fpath, actor_names)
            scene_title = SCENE_TITLES.get(scene_id, f"Màn {scene_id}")

            scene_lines = []
            for idx, en_str in enumerate(raw_strings):
                line_id = f"{scene_id}.{idx+1}"

                # Xác định speaker
                if en_str.startswith(("ep_", "story_", "fx_", "qstory_", "Set", "\x00", "flavio_", "wog_", "hotel_", "city_", "hospital_", "ward_")):
                    speaker = "[Hệ thống / Lệnh]"
                    line_type = "system_command"
                elif any(w in en_str for w in ["Floris Month", "Pluvia Month", "26th", "27th", "Ash District", "Vault", "Corridor", "Street", "Near Emor"]):
                    speaker = "Dẫn chuyện (Bối cảnh)"
                    line_type = "narration"
                else:
                    speaker = spk_map.get(en_str, "Dẫn chuyện")
                    if speaker == "Trekker (Lựa chọn)":
                        line_type = "choice"
                    elif speaker == "Dẫn chuyện":
                        line_type = "narration"
                    else:
                        line_type = "dialogue"

                vi_ptc_val = cache_ptc.get(en_str, clean_dict.get(line_id, en_str))
                vi_clean_val = clean_dict.get(line_id, vi_ptc_val)

                scene_lines.append({
                    "line_id": line_id,
                    "speaker": speaker,
                    "en_text": en_str,
                    "vi_ptc": vi_ptc_val,
                    "vi_clean": vi_clean_val,
                    "line_type": line_type
                })

            total_chapter_lines += len(scene_lines)
            chapter_scenes.append({
                "scene_id": scene_id,
                "file_name": f,
                "scene_title": scene_title,
                "total_lines": len(scene_lines),
                "lines": scene_lines
            })

        return chapter_scenes, total_chapter_lines

    ch1_scenes, ch1_total = process_chapter("STm01_", "Chương 1")
    ch2_scenes, ch2_total = process_chapter("STm02_", "Chương 2")

    return ch1_scenes, ch1_total, ch2_scenes, ch2_total


# ==============================================================================
# 4. CHÍNH - XUẤT FILE JSON VÀ BÁO CÁO
# ==============================================================================

def main():
    print("=" * 70)
    print("Stella Sora - Bắt đầu trích xuất dữ liệu Google Spreadsheet Batch")
    print("=" * 70)

    # 1. Glossary
    print("\n[1/4] Đang nạp và phân loại 322 mục danh từ từ config/glossary.json...")
    glossary_entries, group_counts = load_and_classify_glossary()
    print(f" -> Đã trích xuất thành công {len(glossary_entries)} mục danh từ.")
    for g, c in sorted(group_counts.items()):
        print(f"    * {g}: {c} mục")

    # 2. Voice Bible & Matrix
    print("\n[2/4] Đang nạp 41 hồ sơ nhân vật & ma trận khẩu khí...")
    characters, relationship_pairs = load_character_voice_and_matrix()
    print(f" -> Đã tổng hợp thành công {len(characters)} hồ sơ nhân vật.")
    print(f" -> Đã thiết lập {len(relationship_pairs)} cặp quy chuẩn xưng hô và khẩu khí.")

    # 3. Kịch bản Chương 1 & Chương 2
    print("\n[3/4] Đang trích xuất toàn bộ kịch bản Chương 1 và Chương 2 từ Lua bytecode...")
    ch1_scenes, ch1_total, ch2_scenes, ch2_total = extract_chapters_data()
    print(f" -> Chương 1 (STm01): {len(ch1_scenes)} files/màn, tổng cộng {ch1_total} câu.")
    for sc in ch1_scenes:
        print(f"    - {sc['file_name']:15s} | {sc['scene_title'][:45]:45s} | {sc['total_lines']:4d} câu")

    print(f"\n -> Chương 2 (STm02): {len(ch2_scenes)} files/màn, tổng cộng {ch2_total} câu.")
    for sc in ch2_scenes:
        print(f"    - {sc['file_name']:15s} | {sc['scene_title'][:45]:45s} | {sc['total_lines']:4d} câu")

    # 4. Tổng hợp và lưu JSON
    output_path = ROOT / "work" / "batches" / "google_sheets_batch_data.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    batch_data = {
        "metadata": {
            "title": "Stella Sora - Dữ liệu Dịch thuật Toàn diện Google Spreadsheet",
            "version": "1.0.0",
            "created_at": "2026-10-30",
            "total_glossary_entries": len(glossary_entries),
            "total_characters": len(characters),
            "total_relationship_pairs": len(relationship_pairs),
            "chapter_1": {
                "name": "Chương 1 - Thức Tỉnh & Đại Lục Nova",
                "total_files": len(ch1_scenes),
                "total_lines": ch1_total,
                "scenes_breakdown": {sc["scene_id"]: sc["total_lines"] for sc in ch1_scenes}
            },
            "chapter_2": {
                "name": "Chương 2 - Thương Hội Creta & Đặc Quyền",
                "total_files": len(ch2_scenes),
                "total_lines": ch2_total,
                "scenes_breakdown": {sc["scene_id"]: sc["total_lines"] for sc in ch2_scenes}
            },
            "grand_total_dialogue_lines": ch1_total + ch2_total
        },
        "glossary_groups_summary": group_counts,
        "glossary": glossary_entries,
        "voice_bible": {
            "characters": characters,
            "relationship_matrix": relationship_pairs
        },
        "chapter_1_scenes": ch1_scenes,
        "chapter_2_scenes": ch2_scenes
    }

    print(f"\n[4/4] Đang ghi dữ liệu cấu trúc hóa ra file: {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(batch_data, f, ensure_ascii=False, indent=2)

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f" -> Hoàn tất! File đã được ghi thành công ({file_size_mb:.2f} MB).")
    print("=" * 70)


if __name__ == "__main__":
    main()
