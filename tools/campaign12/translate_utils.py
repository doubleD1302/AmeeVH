#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Campaign 12 Translation Utilities.
Provides robust token verification, NFC normalization, and proposal compilation.
"""

import json
from pathlib import Path
import re
import unicodedata

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')
CTRL_PATTERN = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')

BANNED_WORDS = [
    r"\bMa Vương\b",
    r"\bchết tiệt\b",
    r"\bbạn biết đấy\b",
    r"\bcái quái gì\b",
    r"\blàm sao mà\b",
    r"\btrỗi dậy và tỏa sáng\b",
    r"\bnhảy ra khỏi lồng ngực\b",
    r"\bGrand Thanh tra\b",
    r"\bHòn Hồn Thạch\b",
    r"\bnhững kẻ buồn ngủ\b",
    r"\btrục mìn\b",
    r"\bcon sói đơn độc\b",
]

def clean_text(text: str) -> str:
    """Normalize to Unicode NFC and trim excess whitespace."""
    if not text:
        return ""
    return unicodedata.normalize("NFC", text).strip()

def verify_tokens(src_en: str, dst_vi: str):
    """Check if all formatting tags in source are strictly preserved in destination."""
    src_tokens = sorted(TAG_PATTERN.findall(src_en))
    dst_tokens = sorted(TAG_PATTERN.findall(dst_vi))
    if src_tokens != dst_tokens:
        return False, src_tokens, dst_tokens
    return True, src_tokens, dst_tokens

def check_banned(text: str):
    """Check if any banned calques appear."""
    for bw in BANNED_WORDS:
        m = re.search(bw, text, re.IGNORECASE)
        if m:
            return m.group(0)
    return None

def build_proposals(source_json_path, translation_map, output_jsonl_path):
    """
    Compile proposals from translation map.
    For entries with binary control chars, preserves source text.
    Validates token parity and banned words.
    """
    with open(source_json_path, "r", encoding="utf-8") as f:
        source_data = json.load(f)

    proposals = []
    errors = []

    for item in source_data:
        iid = item["id"]
        en = item["en"]
        
        # Binary control char check
        if CTRL_PATTERN.search(en):
            vi = en
        elif iid in translation_map:
            vi = clean_text(translation_map[iid])
        else:
            # Missing translation
            errors.append(f"MISSING: [{iid}] {en}")
            vi = item.get("current_vi", en)

        # Token verification
        ok, st, dt = verify_tokens(en, vi)
        if not ok:
            errors.append(f"TOKEN_MISMATCH: [{iid}] Expected {st} got {dt}")

        # Banned words check
        bw = check_banned(vi)
        if bw:
            errors.append(f"BANNED_CALQUE: [{iid}] Contains banned word '{bw}'")

        proposals.append({
            "id": iid,
            "vi_editorial": vi
        })

    if errors:
        print(f"FAILED with {len(errors)} issues:")
        for err in errors[:10]:
            print(f"  {err}")
        return False, errors

    # Write output
    with open(output_jsonl_path, "w", encoding="utf-8") as f:
        for prop in proposals:
            f.write(json.dumps(prop, ensure_ascii=False) + "\n")

    print(f"SUCCESS: Generated {len(proposals)} proposals to {output_jsonl_path.name}")
    return True, []
