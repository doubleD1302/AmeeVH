import json
import re
import sys
from pathlib import Path

PARAM_RE = re.compile(r"&Param\d+&%?")
TAG_RE = re.compile(r"</?color[^>]*>")
MACRO_RE = re.compile(r"##[^#]+#(\d+)#")

def validate_item(key, orig_en, orig_zh, new_vi):
    issues = []
    
    # 1. Check Params
    params_en = sorted(PARAM_RE.findall(orig_en))
    params_zh = sorted(PARAM_RE.findall(orig_zh))
    params_vi = sorted(PARAM_RE.findall(new_vi))
    
    expected_params = params_zh if params_zh else params_en
    if params_vi != expected_params:
        issues.append(f"Param mismatch: expected {expected_params}, got {params_vi}")
        
    # 2. Check Color tag balance
    open_tags = len(re.findall(r"<color=[^>]+>", new_vi))
    close_tags = len(re.findall(r"</color>", new_vi))
    if open_tags != close_tags:
        issues.append(f"Color tag imbalance: {open_tags} open vs {close_tags} close")
        
    # 3. Check Macro ID integrity
    macros_src = MACRO_RE.findall(orig_zh) if orig_zh else MACRO_RE.findall(orig_en)
    macros_vi = MACRO_RE.findall(new_vi)
    if sorted(macros_src) != sorted(macros_vi):
        issues.append(f"Macro ID mismatch: expected {sorted(macros_src)}, got {sorted(macros_vi)}")
        
    # 4. Check forbidden terms
    if "Sơ Quang" in new_vi:
        issues.append("Forbidden term found: 'Sơ Quang' (Must use 'Noya - Khải Minh')")
    if "số tiền hiện có" in new_vi:
        issues.append("Fatal mistranslation found: 'số tiền hiện có'")
    if "Lux Auto" in new_vi:
        issues.append("Fatal calque found: 'Lux Auto'")
    if "Avalanche: Pháo nổi" in new_vi:
        issues.append("Fatal calque found: 'Avalanche: Pháo nổi'")
        
    return issues

def validate_file(path_str):
    p = Path(path_str)
    if not p.exists():
        print(f"File not found: {path_str}")
        return False
    data = json.loads(p.read_text(encoding="utf-8"))
    print(f"Validating {len(data)} items in {p.name}...")
    all_issues = 0
    for item in data:
        k = item.get("key")
        en = item.get("en", "")
        zh = item.get("zh", "")
        vi = item.get("vi", item.get("translated", ""))
        issues = validate_item(k, en, zh, vi)
        if issues:
            all_issues += 1
            print(f"[{k}] ISSUES:")
            for iss in issues:
                print(f"  - {iss}")
    if all_issues == 0:
        print(f"SUCCESS: 100% Validated! 0 issues across all {len(data)} items in {p.name}.")
        return True
    else:
        print(f"WARNING: Found {all_issues} items with issues in {p.name}!")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        validate_file(sys.argv[1])
    else:
        print("Usage: python validate_gameplay_translation.py <path_to_json>")
