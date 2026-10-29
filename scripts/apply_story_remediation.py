# -*- coding: utf-8 -*-
"""
Script: apply_story_remediation.py
Run: remediation_v110_20261029_r01
Role: LOCALIZATION_QA_REVIEWER
Task: task_remediate_story

Remediates all story defects across 6 batch files and 12 campaign proposals through 3 phases:
Phase 1: Technical Blockers & CJK/EN Leaks
Phase 2: World Terminology & Addressing Harmonization
Phase 3: Light Novel Style & Idiom Polish
"""

import os
import sys
import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path(r"C:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "scripts"))
from remediation_dict import BINARY_CLEANUP_MAP

# -------------------------------------------------------------
# PHASE 1 RULES: CJK & English & Ruby Tags
# -------------------------------------------------------------
CJK_FIXES = {
    "STm01_07.85": "（Tại đây có nhắc nhở cài đặt biểu tượng tính năng mới mở ra——）",
    "CG_141_01.49": "BGM Dừng",
    "CG_141_02.6": "BGM U Ám",
    "CG_141_02.26": "BGM Dừng",
}

RUBY_REPLACEMENTS = [
    (r"<r=Nazuka, can you hear me\?></r>", r"<r=Nazuka, cậu có nghe thấy tớ không?></r>"),
    (r"<r=Listen, Nazuka, I will protect your soul through soul trading\.></r>", r"<r=Nghe này Nazuka, tớ sẽ bảo vệ linh hồn cậu bằng giao dịch linh hồn.></r>"),
    (r"<r=Any wish, and I'll make it come true!></r>", r"<r=Bất kỳ điều ước nào, ta cũng sẽ biến nó thành hiện thực!></r>"),
    (r"<r=So, make a wish to me! With your entire will\.\.\.Make a wish to me!></r>", r"<r=Vậy nên, hãy ước với ta đi! Bằng trọn vẹn ý chí của ngươi... Hãy ước với ta đi!></r>"),
    (r"<r=Here you are\.></r>", r"<r=Của cậu đây.></r>"),
    (r"<r=Take care now\.></r>", r"<r=Bảo trọng nhé.></r>"),
    (r"<r=Legs\.\.\.></r>", r"<r=Đôi chân...></r>"),
    (r"<r=My\.\.\. My tongue\.\.\.></r>", r"<r=Lưỡi... Lưỡi của tôi...></r>"),
    (r"<r=N-No\.\.\.></r>", r"<r=K-Không...></r>"),
    (r"<r=She won't listen to a word\.\.\.></r>", r"<r=Cô ấy chẳng chịu nghe lấy một lời...></r>"),
    (r"<r=Is the person I'm waiting for here></r>", r"<r=Người tôi đang đợi có ở đây không></r>"),
    (r"<r=claw machine></r>", r"<r=máy gắp thú></r>"),
    (r"<r=cloak>lớp da</r>", r"<r=áo choàng>lớp da</r>"),
    (r"<r=contradictory>yêu</r>", r"<r=mâu thuẫn>yêu</r>"),
    (r"<r=damp></r>", r"<r=ẩm ướt></r>"),
    (r"<r=diary>ách</r>", r"<r=nhật ký>ách</r>"),
    (r"<r=cell></r>", r"<r=buồng giam></r>"),
    (r"<r=karma></r>", r"<r=nghiệp chướng></r>"),
    (r"<r=keep slacking off>cán đích thành công</r>", r"<r=tiếp tục lười biếng>cán đích thành công</r>"),
    (r"<r=kill the Tyrant>thế giới</r>", r"<r=tiêu diệt Bạo Chúa>thế giới</r>"),
    (r"<r=legit>đích thực</r>", r"<r=chính hiệu>đích thực</r>"),
    (r"<r=my home></r>", r"<r=nhà tôi></r>"),
    (r"<r=ninjas></r>", r"<r=ninja></r>"),
    (r"<r=outfit>kiếm</r>", r"<r=trang phục>kiếm</r>"),
    (r"<r=outfits>kiếm</r>", r"<r=trang phục>kiếm</r>"),
    (r"<r=person></r>", r"<r=người></r>"),
    (r"<r=strap>tơ</r>", r"<r=dây đai>tơ</r>"),
    (r"<r=threat></r>", r"<r=mối đe dọa></r>"),
    (r"<r=Waiter>Phục\.\.\. phục vụ</r>", r"<r=Bồi bàn>Phục... phục vụ</r>"),
    (r"<r=the dolls></r>", r"<r=những con búp bê></r>"),
    (r"<r=the dolls'></r>", r"<r=những con búp bê></r>"),
    (r"<r=dolls></r>", r"<r=búp bê></r>"),
]

ENGLISH_FIXES = {
    "PM10302.42": "Nàng bán vỏ sò bên bờ biển sóng vỗ",
    "PM10302.43": "Chú sóc chuột có thể ném được bao nhiêu gỗ",
    "PM10302.44": "Nếu chú sóc chuột thật sự biết ném gỗ?",
    "PM11602.39": "Dừng lại, mau dừng lại đi!",
    "PM12001.89": "Tôi koo mộnggg duuu",
    "PM12001.94": "tôi dạy học 21 ngày liền từ tii",
    "PM12001.95": "Kèm cặp cả trùm lũ nhóc",
    "PM12001.96": "Lại còn bao nhiêu cuộc họpppp",
    "PM12001.97": "Toàn nói chuyện nhảm nhí",
    "PM12001.100": "bao nhiêu việc trong khi",
    "PM12001.101": "tôi cũng muốn đi đâu đó chơi với cậu màaaaa",
    "Mmmph-hmm, mmm-hmm!": "Ư-ưm, ưm-ưm!",
    "Mmmph-mm, hmm-hmm!": "Ưm-ừm, hừm-hừm!",
    "<size=50>Cluck-cluck—==W==cluck-cluck—</size>": "<size=50>Cục-tác—==W==cục-tác—</size>",
    "<size=50>Hooooo, hoot-hoot!==W== Hoot-hoot—!</size>": "<size=50>Húuuu, cúc-cu!==W== Cúc-cu—!</size>",
    "Coo-coo-coooo!==B====W==<size=50> Coo-coo—</size>": "Gù-gù-gùuuu!==B====W==<size=50> Gù-gù—</size>",
    "Heh...==W== Heh heh heh...==W== HAHAHAHA!==W==": "Hê...==W== Hê hề hề...==W== HAHAHAHA!==W==",
    "Kh-khah, kh-khah.": "Khặc-khặc, khặc-khặc.",
    "Nya-ha-ha-ha!": "Nha-ha-ha-ha!",
    "Ticka-Boom Ding-Dong Bang!": "Tích-Tắc Bùm Đùng-Đoàng Banh!",
    "Yeee-ah! Yeee-yah—": "Áaaa! Áaaa-chà—",
    "_NOT_IN_LOG_<br><margin-left=5em><align=left><i><b><size=800%>Y O <alpha=#88>U</size></b></i></align></margin>==A0.15==": "_NOT_IN_LOG_<br><margin-left=5em><align=left><i><b><size=800%>N G Ư <alpha=#88>Ơ I</size></b></i></align></margin>==A0.15==",
}

# -------------------------------------------------------------
# PHASE 2 RULES: Terminology & Addressing Harmonization
# -------------------------------------------------------------
PHASE_2_RULES = [
    # Monolith
    (re.compile(r"Cự Thạch", re.UNICODE), "Cự Tháp"),
    (re.compile(r"cự thạch", re.UNICODE), "cự tháp"),
    (re.compile(r"núi nguyên khối", re.IGNORECASE), "Cự Tháp"),
    (re.compile(r"Thành phố ngàn khối đá", re.IGNORECASE), "Thành phố ngàn Cự Tháp"),
    (re.compile(r"\bMonolith\b"), "Cự Tháp"),

    # New Star Guild
    (re.compile(r"Công Hội Tân Tinh", re.UNICODE), "Lữ Đoàn Tân Tinh"),
    (re.compile(r"công hội Tân Tinh", re.UNICODE), "lữ đoàn Tân Tinh"),
    (re.compile(r"Hội Ngôi sao Mới|Hội Ngôi Sao Mới", re.IGNORECASE), "Lữ Đoàn Tân Tinh"),

    # Dusk Arbiter & Church Arbiter
    (re.compile(r"Trọng Tài Hoàng Hôn|Trọng Tài Chạng Vạng|Trọng tài Hoàng Hôn|Trọng tài Chạng Vạng", re.UNICODE), "Thẩm Phán Hoàng Hôn"),
    (re.compile(r"Trọng tài (Gerie|Hoàng Hôn|Chạng Vạng)", re.IGNORECASE), r"Thẩm Phán \1"),
    (re.compile(r"Trọng Tài Gerie", re.UNICODE), "Thẩm Phán Gerie"),
    (re.compile(r"Trọng tài Gerie", re.UNICODE), "Thẩm Phán Gerie"),

    # Grace Imperium & An Dien
    (re.compile(r"Kim Khố Ý Chí Ân Tứ", re.IGNORECASE), "Kim Khố Đế Quốc Grace"),
    (re.compile(r"Ý Chí Ân Tứ", re.IGNORECASE), "Đế Quốc Grace"),
    (re.compile(r"Ân [đĐ]iển", re.UNICODE), "Ân Tứ"),
    (re.compile(r"ân điển", re.UNICODE), "ân tứ"),

    # Soul Stone
    (re.compile(r"Hòn Hồn Thạch|Viên Hồn Thạch", re.IGNORECASE), "Hồn Thạch"),
    (re.compile(r"Viên đá Linh hồn|viên đá linh hồn", re.IGNORECASE), "Hồn Thạch"),
    (re.compile(r"Đá linh hồn", re.UNICODE), "Hồn Thạch"),
    (re.compile(r"đá linh hồn", re.UNICODE), "hồn thạch"),
    (re.compile(r"\bSoul Stone\b|\bSoulstone\b", re.IGNORECASE), "Hồn Thạch"),

    # Addressing & Roles
    (re.compile(r"Thưa bác sĩ", re.IGNORECASE), "Thưa tiền bối"),
    (re.compile(r"bạn đời", re.IGNORECASE), "cộng sự"),
    (re.compile(r"bữa tiệc bất ngờ", re.IGNORECASE), "đối tác bất ngờ"),
    (re.compile(r"bữa tiệc tham gia", re.IGNORECASE), "bên tham gia"),
    (re.compile(r"bữa tiệc ký kết", re.IGNORECASE), "bên ký kết"),
    (re.compile(r"bữa tiệc đối tác", re.IGNORECASE), "phía đối tác"),
    (re.compile(r"(?:thuyền trưởng|Thuyền trưởng|Thuyền Trưởng) (Fuyuka|Nazuka|Nazuna|Gerie|Narida)", re.IGNORECASE), r"Đội Trưởng \1"),
    (re.compile(r"Bà Angie|Quý Cô Angie", re.IGNORECASE), "Tiểu Thư Angie"),

    # Boss Addressing Calques
    (re.compile(r"Hiệp định của ông chủ", re.IGNORECASE), "Hiệp Ước Của Sếp"),
    (re.compile(r"Sếp Accord|Hiệp Ước Boss", re.IGNORECASE), "Hiệp Ước Của Sếp"),
    (re.compile(r"BOSS CỦA BẠN", re.IGNORECASE), "Sếp của bạn"),
    (re.compile(r"\bông chủ tiệm video\b", re.IGNORECASE), "chủ tiệm video"),
]

# -------------------------------------------------------------
# PHASE 3 RULES: Light Novel Calques
# -------------------------------------------------------------
PHASE_3_RULES = [
    (re.compile(r"Vâng, tốt\.|Tốt, tốt\.", re.IGNORECASE), "Chà chà..."),
    (re.compile(r"điều đầu tiên trước tiên", re.IGNORECASE), "trước hết"),
    (re.compile(r"vụ cướp đường cao tốc", re.IGNORECASE), "chém giá cắt cổ"),
    (re.compile(r"cứu người khỏi bữa tiệc", re.IGNORECASE), "giữ lại miếng bánh"),
    (re.compile(r"con cá bột", re.IGNORECASE), "cá chiên"),
    (re.compile(r"lời nói dối trắng trợn", re.IGNORECASE), "lời nói dối vô hại"),
    (re.compile(r"quay lưng của ([^\s]+) lại với", re.IGNORECASE), r"ngoảnh mặt làm ngơ với \1"),
    (re.compile(r"tinh thần cây tuyết|thần cây tuyết|Tuyết Thụ Linh", re.IGNORECASE), "Mộc Linh Băng Tuyết"),
    (re.compile(r"hội thảo di động", re.IGNORECASE), "xưởng cơ khí lưu động"),
    (re.compile(r"tàn tích đông lạnh", re.IGNORECASE), "Tàn Tích Băng Giá"),
    (re.compile(r"RA KHỎI ĐÓ—!", re.IGNORECASE), "MAU RỜI KHỎI ĐÓ—!"),
]

BINARY_OPCODE_REGEX = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u05ff]|Gѿ")

def remediate_text(k: str, v: str) -> tuple:
    """
    Applies Phase 1, Phase 2, and Phase 3 remedies to text string v.
    Returns (remediated_v, phase1_modified, phase2_modified, phase3_modified).
    """
    if not isinstance(v, str) or not v:
        return v, False, False, False

    p1_mod = False
    p2_mod = False
    p3_mod = False

    # ----------------- PHASE 1 -----------------
    # 1. Exact Binary Cleanup Map
    if k in BINARY_CLEANUP_MAP:
        v = BINARY_CLEANUP_MAP[k]
        p1_mod = True
    elif BINARY_OPCODE_REGEX.search(v):
        # Fallback binary cleaner if any opcode remains
        cleaned = BINARY_OPCODE_REGEX.sub("", v).strip()
        if cleaned != v:
            v = cleaned
            p1_mod = True

    # 2. CJK Leak
    if k in CJK_FIXES:
        v = CJK_FIXES[k]
        p1_mod = True
    elif "此处有新功能" in v:
        v = "(Tại đây có nhắc nhở cài đặt biểu tượng tính năng mới mở ra)"
        p1_mod = True
    elif "BGM 停止" in v:
        v = v.replace("BGM 停止", "BGM Dừng")
        p1_mod = True
    elif "BGM 阴森" in v:
        v = v.replace("BGM 阴森", "BGM U Ám")
        p1_mod = True

    # 3. Ruby tags
    for pat, rep in RUBY_REPLACEMENTS:
        new_v = re.sub(pat, rep, v)
        if new_v != v:
            v = new_v
            p1_mod = True

    # 4. English leftover phrases
    if k in ENGLISH_FIXES:
        v = ENGLISH_FIXES[k]
        p1_mod = True
    elif v in ENGLISH_FIXES:
        v = ENGLISH_FIXES[v]
        p1_mod = True

    # ----------------- PHASE 2 -----------------
    for regex, rep in PHASE_2_RULES:
        new_v = regex.sub(rep, v)
        if new_v != v:
            v = new_v
            p2_mod = True

    # ----------------- PHASE 3 -----------------
    for regex, rep in PHASE_3_RULES:
        new_v = regex.sub(rep, v)
        if new_v != v:
            v = new_v
            p3_mod = True

    return v, p1_mod, p2_mod, p3_mod


def main():
    print("=" * 80)
    print("STARTING THREE-PHASE STORY REMEDIATION (FINAL RUN)")
    print("=" * 80)

    files_to_remediate = [
        # Batches
        ("batch:batch_10k_approved.json", "work/batches/batch_10k_approved.json", "json_kv"),
        ("batch:batch_10k_b2_approved.json", "work/batches/batch_10k_b2_approved.json", "json_kv"),
        ("batch:batch_10k_b3_approved.json", "work/batches/batch_10k_b3_approved.json", "json_kv"),
        ("batch:batch_10k_b4_approved.json", "work/batches/batch_10k_b4_approved.json", "json_kv"),
        ("batch:remaining_lua_avg_cache.json", "work/batches/remaining_lua_avg_cache.json", "json_kv"),
        ("batch:dialogue_remaining_avg_approved.json", "work/batches/dialogue_remaining_avg_approved.json", "json_kv"),
        # Proposals
        ("campaign:lightnovel_story", "work/editorial/lightnovel_editorial_20261024_r02/UNIFIED_STORY_PROPOSALS.jsonl", "jsonl"),
        ("campaign:act1_act2", "work/editorial/act1_act2_story_editorial_20261024_r01/UNIFIED_ACT1_ACT2_PROPOSALS.jsonl", "jsonl"),
        ("campaign:act2_climax", "work/editorial/act2_climax_story_editorial_20261024_r01/UNIFIED_ACT2_CLIMAX_PROPOSALS.jsonl", "jsonl"),
        ("campaign:act3", "work/editorial/act3_story_editorial_20261024_r01/UNIFIED_ACT3_PROPOSALS.jsonl", "jsonl"),
        ("campaign:act3_part1", "work/editorial/act3_part1_story_editorial_20261024_r01/UNIFIED_ACT3_PART1_PROPOSALS.jsonl", "jsonl"),
        ("campaign:act4_final", "work/editorial/act4_final_story_editorial_20261024_r01/UNIFIED_ACT4_STORY_PROPOSALS.jsonl", "jsonl"),
        ("campaign:side_stories_part1", "work/editorial/side_stories_part1_editorial_20261025_r01/UNIFIED_STSP_PART1_PROPOSALS.jsonl", "jsonl"),
        ("campaign:side_stories_part2", "work/editorial/side_stories_part2_editorial_20261025_r01/UNIFIED_CAMPAIGN13_PROPOSALS.jsonl", "jsonl"),
        ("campaign:event_stories_part2", "work/editorial/event_stories_part2_editorial_20261025_r01/UNIFIED_CAMPAIGN_14_PROPOSALS.jsonl", "jsonl"),
        ("campaign:event_stories_part3", "work/editorial/event_stories_part3_editorial_20261025_r01/UNIFIED_CAMPAIGN_15_PROPOSALS.jsonl", "jsonl"),
        ("campaign:event_stories_part4", "work/editorial/event_stories_part4_editorial_20261025_r01/UNIFIED_CAMPAIGN_16_PROPOSALS.jsonl", "jsonl"),
        ("campaign:campaign_19_polished", "work/editorial/campaign19_polish_remaining_20680_20261025_r01/UNIFIED_CAMPAIGN_19_POLISHED.jsonl", "jsonl_c19"),
    ]

    total_stats = {
        "phase1_technical_and_cjk_en": 0,
        "phase2_terminology_and_pronouns": 0,
        "phase3_lightnovel_calques": 0,
        "total_lines_modified": 0,
    }

    per_file_report = {}

    for name, rel_path, ftype in files_to_remediate:
        full_path = ROOT / rel_path
        if not full_path.exists():
            print(f"Skipping {rel_path} (not found)")
            continue

        print(f"Remediating [{name}]...")
        file_p1 = 0
        file_p2 = 0
        file_p3 = 0
        file_modified = 0

        if ftype == "json_kv":
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for k, v in list(data.items()):
                new_v, p1, p2, p3 = remediate_text(k, v)
                if p1: file_p1 += 1
                if p2: file_p2 += 1
                if p3: file_p3 += 1
                if p1 or p2 or p3:
                    file_modified += 1
                    data[k] = new_v
            
            if file_modified > 0:
                with open(full_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

        elif ftype == "jsonl":
            lines = full_path.read_text(encoding="utf-8").splitlines()
            new_lines = []
            for lidx, l in enumerate(lines):
                if not l.strip():
                    continue
                d = json.loads(l)
                k = d.get("id") or d.get("scene_id") or f"line_{lidx}"
                v_field = "vi" if "vi" in d else "vi_editorial"
                v = d.get(v_field, "")
                new_v, p1, p2, p3 = remediate_text(k, v)
                if p1: file_p1 += 1
                if p2: file_p2 += 1
                if p3: file_p3 += 1
                if p1 or p2 or p3:
                    file_modified += 1
                    d[v_field] = new_v
                new_lines.append(json.dumps(d, ensure_ascii=False))

            if file_modified > 0:
                full_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

        elif ftype == "jsonl_c19":
            lines = full_path.read_text(encoding="utf-8").splitlines()
            new_lines = []
            for lidx, l in enumerate(lines):
                if not l.strip():
                    continue
                d = json.loads(l)
                k = f"global_id_{d.get('global_id')}"
                v_field = "polished_vi" if "polished_vi" in d else "original_vi"
                v = d.get(v_field, "")
                new_v, p1, p2, p3 = remediate_text(k, v)
                if p1: file_p1 += 1
                if p2: file_p2 += 1
                if p3: file_p3 += 1
                if p1 or p2 or p3:
                    file_modified += 1
                    d[v_field] = new_v
                new_lines.append(json.dumps(d, ensure_ascii=False))

            if file_modified > 0:
                full_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

        print(f"  -> {name}: P1={file_p1}, P2={file_p2}, P3={file_p3}, total_modified={file_modified}")
        total_stats["phase1_technical_and_cjk_en"] += file_p1
        total_stats["phase2_terminology_and_pronouns"] += file_p2
        total_stats["phase3_lightnovel_calques"] += file_p3
        total_stats["total_lines_modified"] += file_modified

        per_file_report[name] = {
            "path": rel_path,
            "phase1_modifications": file_p1,
            "phase2_modifications": file_p2,
            "phase3_modifications": file_p3,
            "total_lines_modified": file_modified,
        }

    print("\n" + "=" * 80)
    print("REMEDIATION SUMMARY")
    print("=" * 80)
    print(f"Phase 1 (Technical Blockers & CJK/EN): {total_stats['phase1_technical_and_cjk_en']} instances fixed")
    print(f"Phase 2 (Terminology & Pronouns):      {total_stats['phase2_terminology_and_pronouns']} instances fixed")
    print(f"Phase 3 (Light Novel Calques):         {total_stats['phase3_lightnovel_calques']} instances fixed")
    print(f"Total Modified Lines Across Files:    {total_stats['total_lines_modified']}")

    out_dir = ROOT / "work/subagents/remediation_v110_20261029_r01/story"
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / "RESULT.json"

    result_data = {
        "schema": 1,
        "run_id": "remediation_v110_20261029_r01",
        "task_id": "task_remediate_story",
        "role": "LOCALIZATION_QA_REVIEWER",
        "status": "COMPLETED",
        "summary": total_stats,
        "files_remediated_count": len(files_to_remediate),
        "details_by_file": per_file_report,
    }

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print(f"\nWritten remediation report to {result_path}")

if __name__ == "__main__":
    main()
