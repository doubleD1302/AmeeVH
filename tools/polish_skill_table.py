#!/usr/bin/env python3
"""Polisher for Skill table (00636_0x998f849a64309b25.bin)."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from phase2a_token_manager import extract_tokens, shield_tokens, unshield_tokens, validate_token_preservation

TAG_REGEX = re.compile(r'##[^#\n\x0b<>]+(?:#[0-9]+)?#')

def restore_tags_sequential(vi_text: str, en_orig: str) -> str:
    en_tags = TAG_REGEX.findall(en_orig)
    vi_tags = TAG_REGEX.findall(vi_text)
    if len(en_tags) == len(vi_tags) and len(en_tags) > 0:
        idx = 0
        def repl(m):
            nonlocal idx
            tag = en_tags[idx]
            idx += 1
            return tag
        return TAG_REGEX.sub(repl, vi_text)
    return vi_text

def polish_skill_entry(vi_text: str, en_orig: str) -> str:
    # 1. Restore exact original ## tags from EN sequentially
    restored_vi = restore_tags_sequential(vi_text, en_orig)
                
    sh, toks = shield_tokens(restored_vi)

    # 2. Polish terminology
    sh = re.sub(r'\bKỹ Năng Chính\b', 'Kỹ Năng Chủ Lực', sh)
    sh = re.sub(r'\bkỹ năng chính\b', 'kỹ năng chủ lực', sh)
    sh = re.sub(r'\bKỹ Năng Hỗ Trợ\b', 'Kỹ Năng Viện Trợ', sh)
    sh = re.sub(r'\bkỹ năng hỗ trợ\b', 'kỹ năng viện trợ', sh)
    sh = re.sub(r'\bLữ Khách chính\b', 'Lữ Khách chủ lực', sh)
    sh = re.sub(r'\bLữ khách chính\b', 'Lữ Khách chủ lực', sh)
    sh = re.sub(r'\bLữ khách hỗ trợ\b', 'Lữ Khách viện trợ', sh)
    sh = re.sub(r'\bTấn Công Tự Động\b', 'Đòn Đánh Thường', sh, flags=re.I)
    sh = re.sub(r'\btấn công tự động\b', 'Đòn Đánh Thường', sh, flags=re.I)
    sh = re.sub(r'\bSát Thương Đòn Đánh Thường\b', 'Sát Thương Đòn Đánh Thường', sh, flags=re.I)
    sh = re.sub(r'\bsát thương Đòn Đánh Thường\b', 'Sát Thương Đòn Đánh Thường', sh)

    # 3. Polish verbs & flow
    sh = re.sub(r'\bkhi kích hoạt sẽ gây\b', 'khi kích hoạt gây', sh)
    sh = re.sub(r'\bsẽ gây\b', 'gây', sh)
    sh = re.sub(r'\bsẽ tăng\b', 'tăng', sh)
    sh = re.sub(r'\bsẽ giảm\b', 'giảm', sh)
    sh = re.sub(r'\bsẽ hồi\b', 'hồi', sh)
    sh = re.sub(r'\bsẽ nhận\b', 'nhận', sh)
    sh = re.sub(r'\bthiệt hại\b', 'sát thương', sh, flags=re.I)

    # Clean whitespace and unshield
    sh = re.sub(r'[ \t]{2,}', ' ', sh)
    res = unshield_tokens(sh, toks)
    return res

def polish_skill_table(items):
    polished = []
    changes = 0
    token_errors = 0
    for it in items:
        en = it['en']
        orig_vi = it['vi_current']
        new_vi = polish_skill_entry(orig_vi, en)
        
        valid, ot, vt = validate_token_preservation(en, new_vi)
        if not valid:
            token_errors += 1
            print(f"Token error in Skill [{it['key']}]:")
            print("  EN toks:", ot)
            print("  VI toks:", vt)
            # fallback to orig_vi if invalid
            new_vi = orig_vi
            
        if new_vi != orig_vi:
            changes += 1
            
        polished.append({
            'key': it['key'],
            'en': en,
            'vi': new_vi
        })
    print(f"Skill table: {changes} items polished, {token_errors} token errors.")
    return polished
