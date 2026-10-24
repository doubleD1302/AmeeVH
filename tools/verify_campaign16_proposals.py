#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Independent Zero-Defect Quality Gate & Verification Tool for Campaign 16 (Đợt 8):
Event Stories Part 4 (FINAL EVENT STORIES: STev_09, STev_10, STev_11, STev_12).
Total: 3,440 items across 35 scenes.
- Partition A: STev_09 (8 scenes), STev_10 (9 scenes) = 1,676 lines.
- Partition B: STev_11 (9 scenes), STev_12 (9 scenes) = 1,764 lines.
"""

import json
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/event_stories_part4_editorial_20261025_r01"

SOURCE_A = CAMPAIGN_DIR / "PARTITION_A_SOURCE.json"
SOURCE_B = CAMPAIGN_DIR / "PARTITION_B_SOURCE.json"

PROP_A = CAMPAIGN_DIR / "PROPOSALS_PARTITION_A.jsonl"
PROP_B = CAMPAIGN_DIR / "PROPOSALS_PARTITION_B.jsonl"

UNIFIED_OUT = CAMPAIGN_DIR / "UNIFIED_CAMPAIGN_16_PROPOSALS.jsonl"
QA_FINDINGS_PATH = CAMPAIGN_DIR / "QA_FINDINGS.json"

BANNED_WORDS = [
    (r"\bMa Vương\b", "Cấm dùng Ma Vương cho Demon King / Lord"),
    (r"\bchết tiệt\b", "Cấm dùng chửi thề thô tục 'chết tiệt'"),
    (r"\bbạn biết đấy\b", "Calque máy dịch 'you know'"),
    (r"\bcái quái gì\b", "Calque dịch thô 'what the hell'"),
    (r"\blàm sao mà\b", "Calque dịch thô 'how come'"),
    (r"\bkhoảng không quảng cáo\b", "Calque máy dịch 'inventory' -> túi đồ/kho đồ"),
    (r"\bchụp nhanh bộ nhớ\b", "Calque máy dịch 'memory snapshot' -> hồi ức đặc tả"),
    (r"\bHội Ngôi Sao Mới\b", "Cấm dùng Hội Ngôi Sao Mới -> chuẩn hóa: Lữ Đoàn Tân Tinh"),
    (r"\bHiệp hội Ngôi sao Mới\b", "Cấm dùng Hiệp hội Ngôi sao Mới -> chuẩn hóa: Lữ Đoàn Tân Tinh"),
    (r"\bBạo Quân\b", "Cấm dùng Bạo Quân -> chuẩn hóa: Bạo Chúa"),
    (r"\b(màn một|Màn một|Màn 1|màn 1)\b", "Tiêu đề Hồi phải chuẩn hóa viết hoa: Hồi 1"),
]

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

def check_tokens(src_tokens, dst_text):
    dst_tokens = TAG_PATTERN.findall(dst_text)
    return sorted(src_tokens) == sorted(dst_tokens), src_tokens, dst_tokens

def check_control_chars(src_text, dst_text):
    src_ctrls = [c for c in src_text if ord(c) < 32 and c not in '\r\n\t']
    dst_ctrls = [c for c in dst_text if ord(c) < 32 and c not in '\r\n\t']
    return src_ctrls == dst_ctrls, src_ctrls, dst_ctrls

def audit_file(prop_path, src_path, part_name):
    print(f"--- Auditing Partition {part_name} ({prop_path.name}) ---")
    if not prop_path.exists():
        print(f"WAITING: {prop_path.name} does not exist yet.")
        return False, ["MISSING_PROPOSAL_FILE"], [], []

    with open(src_path, "r", encoding="utf-8") as f:
        src_items = {it["id"]: it for it in json.load(f)}

    proposals = []
    with open(prop_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                proposals.append(json.loads(line))

    print(f"Expected: {len(src_items)} | Actual: {len(proposals)}")

    blockers = []
    majors = []
    minors = []

    if len(proposals) != len(src_items):
        blockers.append(f"Line count mismatch: expected {len(src_items)}, got {len(proposals)}")

    for p in proposals:
        iid = p["id"]
        if iid not in src_items:
            blockers.append(f"Unknown ID {iid}")
            continue

        src = src_items[iid]
        vi = p.get("vi_editorial", "")
        en = src["en"]

        if not vi or not vi.strip():
            blockers.append(f"[{iid}] Empty Vietnamese translation")
            continue

        # NFC normalization check
        if vi != unicodedata.normalize("NFC", vi):
            majors.append(f"[{iid}] Text is not NFC normalized")

        # Token parity
        ok_tok, st, dt = check_tokens(src["tokens"], vi)
        if not ok_tok:
            blockers.append(f"[{iid}] Token mismatch: src={st} vs dst={dt}")

        # Control char parity
        ok_ctrl, sc, dc = check_control_chars(en, vi)
        if not ok_ctrl:
            blockers.append(f"[{iid}] Control char mismatch: src={sc} vs dst={dc}")

        # Banned words & calques check
        for pat, desc in BANNED_WORDS:
            if re.search(pat, vi, re.IGNORECASE):
                majors.append(f"[{iid}] Banned pattern violated: {desc} in '{vi[:60]}'")

    print(f"Audit results for Partition {part_name}: {len(blockers)} Blockers, {len(majors)} Majors, {len(minors)} Minors.")
    is_ok = len(blockers) == 0 and len(majors) == 0
    return is_ok, blockers, majors, minors

def main():
    ok_a, b_a, m_a, _ = audit_file(PROP_A, SOURCE_A, "A")
    ok_b, b_b, m_b, _ = audit_file(PROP_B, SOURCE_B, "B")

    findings = {
        "partition_a": {"ok": ok_a, "blockers": len(b_a), "majors": len(m_a), "errors": b_a + m_a},
        "partition_b": {"ok": ok_b, "blockers": len(b_b), "majors": len(m_b), "errors": b_b + m_b},
        "all_passed": ok_a and ok_b
    }

    with open(QA_FINDINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False, indent=2)
    print(f"Saved QA findings to {QA_FINDINGS_PATH.name}")

    if ok_a and ok_b:
        print("Both partitions PASSED audit! Writing UNIFIED proposals...")
        unified_items = []
        with open(PROP_A, "r", encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    unified_items.append(l.strip())
        with open(PROP_B, "r", encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    unified_items.append(l.strip())

        with open(UNIFIED_OUT, "w", encoding="utf-8") as f:
            for item_line in unified_items:
                f.write(item_line + "\n")
        print(f"Successfully created {UNIFIED_OUT.name} with {len(unified_items)} items!")
        sys.exit(0)
    else:
        print("Audit failed or waiting for partitions to finish. Verdict: REVISION_REQUIRED")
        sys.exit(1)

if __name__ == "__main__":
    main()
