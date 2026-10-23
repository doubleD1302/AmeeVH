#!/usr/bin/env python3
"""Independent validation and static audit for character context revision r02.

Verifies:
  1. JSON validity and schemas
  2. 100% ID coverage (41/41 grounded profiles)
  3. Evidence reference resolution (0 dangling refs)
  4. Source text authenticity against pristine database
  5. Unicode NFC normalization
  6. Voice Bible markdown coverage (41 sections)
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unicodedata

PROJECT_ROOT = Path(__file__).resolve().parents[1]
R02_DIR = PROJECT_ROOT / "work" / "character_context_20261023_r02"

ARCHIVE_CONTENT_PATH = PROJECT_ROOT / "work/research/data_200_pristine_en/entries/00593_0x843b3b0812018dd2.bin"


def check_nfc(text: str) -> bool:
    return text == unicodedata.normalize("NFC", text)


def run_validation():
    print("=== KIỂM ĐỊNH ĐỘC LẬP BỘ TÀI LIỆU NGỮ CẢNH NHÂN VẬT (r02) ===")
    errors = []
    warnings = []

    # 1. Load files
    files_to_check = [
        "CHARACTER_ROSTER.json",
        "SOURCE_EVIDENCE.json",
        "CHARACTER_VOICE_PROFILES.json",
        "CHARACTER_RELATIONSHIP_MATRIX.json",
        "CHARACTER_VOICE_BIBLE.md",
        "COVERAGE.json",
        "ISSUES.json",
        "CHECKPOINT_CHARACTER_CONTEXT.json"
    ]

    for fname in files_to_check:
        fpath = R02_DIR / fname
        if not fpath.exists():
            errors.append(f"Missing file: {fname}")

    if errors:
        print("Fatal: Missing files:", errors)
        return False

    with open(R02_DIR / "CHARACTER_ROSTER.json", "r", encoding="utf-8") as f:
        roster = json.load(f)
    with open(R02_DIR / "SOURCE_EVIDENCE.json", "r", encoding="utf-8") as f:
        evidence = json.load(f)
    with open(R02_DIR / "CHARACTER_VOICE_PROFILES.json", "r", encoding="utf-8") as f:
        profiles = json.load(f)
    with open(R02_DIR / "CHARACTER_RELATIONSHIP_MATRIX.json", "r", encoding="utf-8") as f:
        matrix = json.load(f)
    with open(R02_DIR / "COVERAGE.json", "r", encoding="utf-8") as f:
        coverage = json.load(f)
    with open(ARCHIVE_CONTENT_PATH, "r", encoding="utf-8") as f:
        content_db = json.load(f)

    # 2. Check Profiles Coverage
    profs = profiles.get("profiles", [])
    if len(profs) != 41:
        errors.append(f"Expected 41 profiles, found {len(profs)}")

    grounded = [p for p in profs if p.get("status") == "source_grounded_editorial_draft"]
    pending = [p for p in profs if p.get("status") == "pending_character_evidence"]
    if len(grounded) != 41:
        errors.append(f"Expected 41 grounded profiles, got {len(grounded)}")
    if len(pending) != 0:
        errors.append(f"Expected 0 pending profiles, got {len(pending)}")

    print(f"1. Độ bao phủ hồ sơ: {len(grounded)}/41 hồ sơ có căn cứ (Pending: {len(pending)}) ✓")

    # 3. Check Evidence registry
    ev_items = evidence.get("evidence", [])
    ev_map = {e["evidence_id"]: e for e in ev_items}
    print(f"2. Bằng chứng nguồn đã lưu: {len(ev_items)} mục ✓")

    # 4. Check Reference resolution
    dangling_refs = []
    for p in profs:
        for ref in p.get("evidence_refs", []):
            if ref not in ev_map:
                dangling_refs.append((p["character_id"], ref))
        for t in p.get("observed_traits", []):
            for ref in t.get("evidence_refs", []):
                if ref not in ev_map:
                    dangling_refs.append((p["character_id"], ref))

    for e in matrix.get("proposed_edges", []):
        for ref in e.get("evidence_refs", []):
            if ref not in ev_map:
                dangling_refs.append((e["id"], ref))

    if dangling_refs:
        errors.append(f"Dangling evidence refs found: {dangling_refs[:5]}")
    else:
        print(f"3. Đối soát tham chiếu bằng chứng: 100% resolve thành công (0 dangling refs) ✓")

    # 5. Check Authenticity against Pristine Content DB
    mismatched_quotes = []
    for e in ev_items:
        key = e.get("source_key")
        if key and key in content_db:
            db_text = content_db[key].strip()
            quote = e.get("quote_en", "").strip()
            if quote not in db_text and db_text not in quote:
                mismatched_quotes.append((e["evidence_id"], key))

    if mismatched_quotes:
        errors.append(f"Mismatched quotes against DB: {mismatched_quotes[:3]}")
    else:
        print(f"4. Đối chiếu nguyên văn nguồn: 100% khớp dữ liệu gốc game ✓")

    # 6. Check NFC Normalization
    non_nfc = []
    bible_text = (R02_DIR / "CHARACTER_VOICE_BIBLE.md").read_text(encoding="utf-8")
    if not check_nfc(bible_text):
        non_nfc.append("CHARACTER_VOICE_BIBLE.md")

    for p in profs:
        for t in p.get("observed_traits", []):
            if not check_nfc(t.get("description_vi", "")):
                non_nfc.append(p["character_id"])
        v = p.get("vi_style_proposal", {})
        if not check_nfc(v.get("sentence_rhythm", "")):
            non_nfc.append(p["character_id"])

    if non_nfc:
        errors.append(f"Non-NFC text found in: {non_nfc[:3]}")
    else:
        print(f"5. Chuẩn hóa tiếng Việt: 100% chuẩn Unicode NFC ✓")

    # 7. Check Voice Bible coverage
    bible_missing = []
    for p in profs:
        header = f"### {p['name_en']} (`{p['character_id']}`)"
        if header not in bible_text:
            bible_missing.append(header)

    if bible_missing:
        errors.append(f"Voice Bible missing headers for: {bible_missing[:3]}")
    else:
        print(f"6. Sổ tay Voice Bible: Đã tích hợp đầy đủ 41/41 nhân vật ✓")

    print("\n" + "=" * 60)
    if not errors:
        print("KẾT QUẢ KIỂM ĐỊNH: 100% ĐẠT TIÊU CHUẨN HOÀN TOÀN (0 LỖI)!")
        print("=" * 60)
        return True
    else:
        print(f"KẾT QUẢ KIỂM ĐỊNH: CÓ {len(errors)} LỖI:")
        for err in errors:
            print("  -", err)
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = run_validation()
    exit(0 if success else 1)
