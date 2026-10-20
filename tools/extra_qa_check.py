import json
import unicodedata
import re

p = "StellaSora_VietHoa/work/batches/dialogue_batch6_awakening_talk_approved.json"
data = json.load(open(p, encoding="utf-8"))

print(f"Total items: {len(data)}")

issues = []
for idx, it in enumerate(data):
    k = it.get("key", "")
    vi = it.get("approved_vi", "")
    reason = it.get("reason", "")
    
    # 1. NFC check
    if vi != unicodedata.normalize('NFC', vi):
        issues.append((k, "Not NFC normalized!"))
        
    # 2. Non-empty reason
    if not reason.strip():
        issues.append((k, "Empty reason!"))
        
    # 3. Check for raw English fragments left behind
    english_remnants = [
        r"\bpart\b", r"\bstay tuned\b", r"\bcommission\b", r"\btyrant\b", r"\bboss\b(?!.*\b(Boss|Ma Vương)\b)",
        r"\bthe\b", r"\band\b", r"\bwith\b", r"\bfrom\b", r"\binto\b"
    ]
    for er in english_remnants:
        if re.search(er, vi, re.IGNORECASE):
            # Exclude proper names like Partia/Portia or deliberate terms
            issues.append((k, f"Possible English remnant: {er} in '{vi}'"))
            
    # 4. Check for forbidden terms
    for fb in ["Hổ phách", "Diên Vĩ", "Ngôi sao mới", "Sơ Quang", "Cái gì trên thế giới", "hoa hồng", "bánh mì nướng"]:
        if fb.lower() in vi.lower():
            issues.append((k, f"Forbidden term found: {fb}"))

print(f"Total issues found: {len(issues)}")
for k, msg in issues:
    print(f"  [{k}] {msg}")
