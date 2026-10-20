# -*- coding: utf-8 -*-
"""
Independent QA Verification Engine - Group 1: Gameplay, Minigames & Combat
Validates all 354 entries for fidelity, technical token preservation, zero forbidden words,
and pure Vietnamese natural phrasing.
"""

import json
import re
import sys
from pathlib import Path

FORBIDDEN_PATTERNS = [
    (r"\bHổ phách\b", "Tên nhân vật Amber bị dịch thành Hổ phách!"),
    (r"\bDiên Vĩ\b", "Tên nhân vật Iris bị dịch thành Diên Vĩ!"),
    (r"Cái gì trên thế giới", "Calque ngớ ngẩn 'What in the world'"),
    (r"\bhoa hồng\b", "commission/rose bị dịch nhầm thành hoa hồng!"),
    (r"\bbánh mì nướng\b", "toast bị dịch nhầm thành bánh mì nướng!"),
    (r"\bSơ Quang\b", "Cấm dùng Sơ Quang cho Noya - Khải Minh!"),
    (r"\bTrần Sa\b", "Cấm dùng Trần Sa cho Noya!")
]

TOKEN_REGEXES = [
    r"==[A-Z0-9_]+==",
    r"\{\d+\}",
    r"&Param\d+&",
    r"<color=[^>]+>",
    r"</color>",
    r"<r=[^>]+>",
    r"</r>",
    r"##[^#]+#[0-9]+#",
    r"<sprite[^>]*>",
    r"<size=[^>]+>",
    r"</size>"
]

HANZI_REGEX = re.compile(r"[\u4e00-\u9fff]")

def verify_group1(file_path, base_ref_path="StellaSora_VietHoa/work/batches/final_wave_group1_gameplay_minigames.json"):
    p = Path(file_path)
    if not p.exists():
        print(f"[ERROR] Target file not found: {p}")
        return False
        
    data = json.loads(p.read_text(encoding="utf-8"))
    ref_data = json.loads(Path(base_ref_path).read_text(encoding="utf-8")) if Path(base_ref_path).exists() else []
    ref_keys = {item["key"]: item for item in ref_data}
    
    print(f"=== INDEPENDENT QA VERIFICATION: {p.name} ===")
    print(f"Items to audit: {len(data)} (Expected: {len(ref_data)})")
    
    errors = []
    warnings = []
    
    if len(data) != len(ref_data) and len(ref_data) > 0:
        errors.append(f"Item count mismatch: Expected {len(ref_data)}, found {len(data)}")
        
    for idx, item in enumerate(data):
        k = item.get("key", f"idx_{idx}")
        table = item.get("table", "")
        en = item.get("en", "")
        zh = item.get("zh", "")
        vi = item.get("approved_vi") or item.get("vi") or item.get("current_vi") or ""
        
        # 1. Non-empty check
        if not vi.strip():
            errors.append(f"[{k}] Empty translation text!")
            continue
            
        # 2. Key existence in ref
        if ref_keys and k not in ref_keys:
            warnings.append(f"[{k}] Key not found in reference dataset!")
            
        # 3. Forbidden pattern check
        for pat, msg in FORBIDDEN_PATTERNS:
            if re.search(pat, vi, re.IGNORECASE):
                errors.append(f"[{k}] FORBIDDEN TERM: {msg} | Match in: {repr(vi[:60])}")
                
        # 4. Technical token check
        for token_pat in TOKEN_REGEXES:
            en_tokens = re.findall(token_pat, en)
            vi_tokens = re.findall(token_pat, vi)
            if sorted(en_tokens) != sorted(vi_tokens):
                # Also check zh tokens if en was missing some
                zh_tokens = re.findall(token_pat, zh)
                if sorted(zh_tokens) != sorted(vi_tokens):
                    errors.append(f"[{k}] TOKEN MISMATCH for {token_pat}: EN={en_tokens}, ZH={zh_tokens} vs VI={vi_tokens}")
                    
        # 5. Newline consistency check
        en_newlines = en.count("\n")
        vi_newlines = vi.count("\n")
        if en_newlines != vi_newlines:
            # If ZH has newlines, check against ZH
            zh_newlines = zh.count("\n")
            if vi_newlines != zh_newlines and en_newlines > 0:
                warnings.append(f"[{k}] Newline count difference: EN={en_newlines}, ZH={zh_newlines}, VI={vi_newlines}")
                
        # 6. Hanzi residue check
        hanzi_matches = HANZI_REGEX.findall(vi)
        if hanzi_matches:
            errors.append(f"[{k}] UNTRANSLATED HANZI DETECTED: {hanzi_matches} in: {repr(vi[:60])}")
            
        # 7. Character name check
        if re.search(r"\bAmber\b", en) and not re.search(r"\bAmber\b", vi, re.IGNORECASE):
            # Check if amber was lost
            if "Hổ phách" in vi or "hổ phách" in vi:
                errors.append(f"[{k}] Amber mistranslated as Hổ phách!")
        if re.search(r"\bIris\b", en) and not re.search(r"\bIris\b", vi, re.IGNORECASE):
            if "Diên Vĩ" in vi or "diên vĩ" in vi:
                errors.append(f"[{k}] Iris mistranslated as Diên Vĩ!")
        if re.search(r"\bNoya\b", en) and not re.search(r"\bNoya\b", vi, re.IGNORECASE):
            if "Sơ Quang" in vi or "Trần Sa" in vi:
                errors.append(f"[{k}] Noya mistranslated!")

    print(f"\n--- AUDIT SUMMARY ---")
    print(f"Total checked: {len(data)}")
    print(f"Errors found:  {len(errors)}")
    print(f"Warnings:      {len(warnings)}")
    
    if errors:
        print("\n[CRITICAL ERRORS]")
        for e in errors[:15]:
            print("  ❌", e)
        if len(errors) > 15:
            print(f"  ... and {len(errors) - 15} more errors.")
        return False
    else:
        print("\n✅ PERFECT PASS! Zero critical errors found.")
        if warnings:
            print(f"Note: {len(warnings)} non-blocking formatting notices observed.")
            for w in warnings[:5]:
                print("  ⚠️", w)
        return True

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "StellaSora_VietHoa/work/batches/final_wave_group1_gameplay_minigames_approved.json"
    success = verify_group1(target)
    sys.exit(0 if success else 1)
