import json
import sys
from pathlib import Path

FORBIDDEN_WORDS = [
    "buổi sáng sắc nét",
    "ôi chao",
    "Lá cô ấy cho tôi",
    "Được cung cấp bởi Breeze",
    "Mùa hè tháng ba",
    "Một phát, một xuống",
    "Vuốt móng vuốt",
    "Rượu ấm, đèn xuống",
    "Hạt giống nhau",
    "Thần mèo meo meo",
    "My Guiding Star",
    "Eternal Brilliance",
    "cồn cát cô đơn",
    "Lạch Ngọt",
    "Dũng cảm với gió",
    "sức mạnh"
]

def validate_discs(file_path):
    p = Path(file_path)
    if not p.exists():
        print(f"Error: {p} does not exist!")
        return False
        
    data = json.loads(p.read_text(encoding="utf-8"))
    print(f"Validating {len(data)} discs in {p.name}...")
    issues = 0
    for item in data:
        did = item.get("id")
        name = item.get("approved_name", "").strip()
        if not name:
            print(f"[{did}] Missing approved_name!")
            issues += 1
            continue
            
        for fw in FORBIDDEN_WORDS:
            if fw.lower() in name.lower():
                print(f"[{did}] Found forbidden/clunky word in approved_name '{name}': '{fw}'")
                issues += 1
                
    if issues == 0:
        print(f"SUCCESS: 100% Validated! 0 issues across all {len(data)} discs in {p.name}.")
        return True
    else:
        print(f"WARNING: Found {issues} issues in {p.name}!")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        validate_discs(sys.argv[1])
    else:
        print("Usage: python validate_discs_translation.py <path_to_json>")
