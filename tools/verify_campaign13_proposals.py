#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification and Merge Tool for Campaign 13 (Đợt 5):
Special Side Stories Part 2 & Event Stories (3,233 items across 33 scenes).
"""

import json
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/side_stories_part2_editorial_20261025_r01"

SOURCE_A = CAMPAIGN_DIR / "PARTITION_A_SOURCE.json"
SOURCE_B = CAMPAIGN_DIR / "PARTITION_B_SOURCE.json"

PROP_A = CAMPAIGN_DIR / "PROPOSALS_PARTITION_A.jsonl"
PROP_B = CAMPAIGN_DIR / "PROPOSALS_PARTITION_B.jsonl"

UNIFIED_OUT = CAMPAIGN_DIR / "UNIFIED_CAMPAIGN13_PROPOSALS.jsonl"
QA_FINDINGS_PATH = CAMPAIGN_DIR / "QA_FINDINGS.json"

BANNED_WORDS = [
    (r"\bMa Vương\b", "Cấm dùng Ma Vương cho Demon King / Lord"),
    (r"\bchết tiệt\b", "Cấm dùng chửi thề thô tục 'chết tiệt'"),
    (r"\bbạn biết đấy\b", "Calque máy dịch 'you know'"),
    (r"\bcái quái gì\b", "Calque dịch thô 'what the hell'"),
    (r"\blàm sao mà\b", "Calque dịch thô 'how come'"),
    (r"\btrỗi dậy và tỏa sáng\b", "Calque máy dịch 'rise and shine'"),
    (r"\bnhảy ra khỏi lồng ngực\b", "Calque máy dịch 'jump out of one's chest'"),
    (r"\bGrand Thanh tra\b", "Calque hỗn tạp 'Grand Thanh tra' -> Đại Thanh Tra"),
    (r"\bHòn Hồn Thạch\b", "Calque dịch lặp 'Hòn Hồn Thạch' -> Hồn Thạch"),
    (r"\bnhững kẻ buồn ngủ\b", "Calque dịch máy 'sleepyheads'"),
    (r"\btrục mìn\b", "Calque dịch máy 'mineshaft'"),
    (r"\bKỵ Sĩ Hoàng Gia\b", "Imperial Guard (Tilia) phải dịch là Cận Vệ Hoàng Gia!"),
    (r"\bTrọng Tài Chạng Vạng\b", "Dusk Arbiter phải dịch là Trọng Tài Hoàng Hôn!"),
    (r"\b(Chiến Binh Cây Bụi|Chuột Cây Bụi|Thành cổ Cây bụi)\b", "Shrubshrew phải chuẩn hóa là Chuột Bụi!"),
    (r"\b(Đá Linh Hồn|Đá Hồn)\b", "Soul Stone phải chuẩn hóa là Hồn Thạch!"),
    (r"\b(Sơ Quang|Trần Sa)\b", "Noya tuyệt đối không dùng Sơ Quang / Trần Sa (phải là Noya - Khải Minh)!"),
    (r"\bHổ phách\b", "Tên nhân vật Amber cấm dịch thành Hổ phách!"),
    (r"\bDiên Vĩ\b", "Tên nhân vật Iris cấm dịch thành Diên Vĩ!"),
    (r"\bPhòng Màu Trắng\b", "White Room phải dịch là Phòng Trắng!"),
    (r"\bĐêm Vĩnh Cửu\b", "Nocturn Eterna phải dịch là Đêm Trường Vĩnh Cửu!"),
    (r"\bKim Khố Ý Chí Ân Tứ\b", "Grace Imperium phải dịch là Đế Quốc Grace!"),
    (r"\b(Bà Angie|Quý Cô Angie)\b", "Lady Angie phải dịch là Tiểu Thư Angie!"),
    (r"\bHiệu Trưởng Allie\b", "Director Allie phải dịch là Giám Đốc Allie!"),
    (r"Cái gì trên thế giới", "Calque máy dịch 'What in the world'"),
    (r"\bbánh mì nướng\b", "Calque dịch sai từ toast (nâng ly)"),
]

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

def check_tokens(src_tokens, dst_text):
    dst_tokens = TAG_PATTERN.findall(dst_text)
    return sorted(src_tokens) == sorted(dst_tokens), src_tokens, dst_tokens

def check_control_chars(src_text, dst_text):
    src_ctrls = [c for c in src_text if ord(c) < 32 and c not in '\r\n']
    dst_ctrls = [c for c in dst_text if ord(c) < 32 and c not in '\r\n']
    return src_ctrls == dst_ctrls, src_ctrls, dst_ctrls

def audit_partition(prop_path, src_path, part_name):
    print(f"--- Auditing {part_name} ({prop_path.name}) ---")
    if not prop_path.exists():
        print(f"WAITING: {prop_path.name} does not exist yet.")
        return False, [], {"blockers": [f"{prop_path.name} not found"], "majors": [], "minors": []}

    with open(src_path, 'r', encoding='utf-8') as f:
        src_data = json.load(f)
    src_map = {item['id']: item for item in src_data}

    props = []
    with open(prop_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                props.append(item)
            except Exception as e:
                print(f"JSON Parse Error at line {idx}: {e}")
                return False, [], {"blockers": [f"JSON Parse Error at line {idx}: {e}"], "majors": [], "minors": []}

    print(f"Expected: {len(src_data)} | Actual: {len(props)}")
    if len(props) != len(src_data):
        print(f"ERROR: Line count mismatch in {part_name}!")
        return False, [], {"blockers": [f"Line count mismatch: expected {len(src_data)}, got {len(props)}"], "majors": [], "minors": []}

    blockers = []
    majors = []
    minors = []
    
    for item in props:
        iid = item.get("id")
        vi = item.get("vi_editorial", "")
        src_item = src_map.get(iid)
        if not src_item:
            blockers.append(f"[{iid}] ID not found in source dataset")
            continue
        
        src_en = src_item.get("en", "")

        # 1. NFC normalization check
        if vi != unicodedata.normalize('NFC', vi):
            majors.append(f"[{iid}] Text is not NFC normalized")

        # 2. Token preservation check
        src_tokens = TAG_PATTERN.findall(src_en)
        ok, st, dt = check_tokens(src_tokens, vi)
        if not ok:
            blockers.append(f"[{iid}] Token mismatch! Src: {st} vs Dst: {dt}")

        # 3. Binary control characters preservation check
        ok_ctrl, sc, dc = check_control_chars(src_en, vi)
        if not ok_ctrl:
            blockers.append(f"[{iid}] Binary control opcode mismatch! Src codes: {[ord(c) for c in sc]} vs Dst: {[ord(c) for c in dc]}")

        # 4. Newline check
        if '\n' in src_en and '\n' not in vi:
            blockers.append(f"[{iid}] Missing newline (\\n) present in source")

        # 5. Banned word / calque check
        for pattern, desc in BANNED_WORDS:
            if re.search(pattern, vi, re.IGNORECASE):
                majors.append(f"[{iid}] Contains banned term '{pattern}' ({desc}): {vi}")

        # 6. Untranslated / empty check
        if not vi.strip() and src_en.strip():
            blockers.append(f"[{iid}] Empty translation!")

    print(f"Audit results for {part_name}: {len(blockers)} Blockers, {len(majors)} Majors, {len(minors)} Minors.")
    if blockers:
        for b in blockers[:10]:
            print("  [BLOCKER]", b)
    if majors:
        for m in majors[:10]:
            print("  [MAJOR]", m)

    is_passed = (len(blockers) == 0 and len(majors) == 0)
    findings = {"blockers": blockers, "majors": majors, "minors": minors}
    return is_passed, props, findings

def main():
    ok_a, props_a, findings_a = audit_partition(PROP_A, SOURCE_A, "Partition A")
    ok_b, props_b, findings_b = audit_partition(PROP_B, SOURCE_B, "Partition B")

    total_blockers = findings_a["blockers"] + findings_b["blockers"]
    total_majors = findings_a["majors"] + findings_b["majors"]
    total_minors = findings_a["minors"] + findings_b["minors"]

    verdict = "APPROVED_FOR_RELEASE" if (ok_a and ok_b) else "REVISION_REQUIRED"

    qa_report = {
        "campaign_id": "side_stories_part2_editorial_20261025_r01",
        "verdict": verdict,
        "total_lines_expected": 3233,
        "total_lines_actual": len(props_a) + len(props_b),
        "partition_a": {
            "status": "PASS" if ok_a else "FAIL",
            "lines": len(props_a),
            "findings": findings_a
        },
        "partition_b": {
            "status": "PASS" if ok_b else "FAIL",
            "lines": len(props_b),
            "findings": findings_b
        }
    }

    with open(QA_FINDINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(qa_report, f, ensure_ascii=False, indent=2)

    if ok_a and ok_b:
        print("Both partitions PASSED audit! Writing UNIFIED proposals...")
        with open(UNIFIED_OUT, "w", encoding="utf-8") as f:
            for p in props_a + props_b:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")
        print(f"Successfully created {UNIFIED_OUT.name} with {len(props_a) + len(props_b)} items!")
    else:
        print("Audit failed or waiting for partitions to finish. Verdict: REVISION_REQUIRED")

if __name__ == "__main__":
    main()
