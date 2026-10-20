import json
import re
import sys
from pathlib import Path

FORBIDDEN_PATTERNS = [
    (r"\bHổ phách\b", "Tên nhân vật Amber bị dịch thành Hổ phách!"),
    (r"\bDiên Vĩ\b", "Tên nhân vật Iris bị dịch thành Diên Vĩ!"),
    (r"Cái gì trên thế giới", "Calque ngớ ngẩn 'What in the world'"),
    (r"\bhoa hồng\b", "commission bị dịch nhầm thành hoa hồng!"),
    (r"\bbánh mì nướng\b", "toast bị dịch nhầm thành bánh mì nướng!"),
    (r"Sơ Quang", "Cấm dùng Sơ Quang cho Noya - Khải Minh!")
]

TOKEN_REGEXES = [
    r"==[A-Z0-9_]+==",
    r"\{\d+\}",
    r"&Param\d+&",
    r"<color=[^>]+>",
    r"</color>",
    r"<r=[^>]+>",
    r"</r>",
    r"##[^#]+#[0-9]+#"
]

def validate_batch(file_path):
    p = Path(file_path)
    if not p.exists():
        print(f"File not found: {p}")
        return False
        
    data = json.loads(p.read_text(encoding="utf-8"))
    print(f"Validating {p.name} ({len(data)} items)...")
    
    errors = []
    for idx, it in enumerate(data):
        k = it.get("key", f"item_{idx}")
        orig = it.get("en", "")
        vi = it.get("approved_vi") or it.get("vi") or it.get("current_vi") or ""
        
        if not vi.strip():
            errors.append(f"[{k}] Empty translation text!")
            continue
            
        # Check forbidden
        for pat, msg in FORBIDDEN_PATTERNS:
            if re.search(pat, vi, re.IGNORECASE):
                errors.append(f"[{k}] Forbidden pattern: {msg} (Found in: {repr(vi[:60])})")
                
        # Check tokens
        for r in TOKEN_REGEXES:
            orig_tokens = re.findall(r, orig)
            vi_tokens = re.findall(r, vi)
            if sorted(orig_tokens) != sorted(vi_tokens):
                errors.append(f"[{k}] Token mismatch for {r}: orig={orig_tokens} vs vi={vi_tokens}")
                
    if errors:
        print(f"FAILED: Found {len(errors)} errors!")
        for e in errors[:10]:
            print("  - ", e)
        return False
    else:
        print(f"PASSED! All {len(data)} items passed validation with 0 errors.")
        return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        success = validate_batch(sys.argv[1])
        sys.exit(0 if success else 1)
