import json, re, unicodedata
from pathlib import Path

# Load source
items = json.load(open('StellaSora_VietHoa/work/editorial/tutorial_and_character_cg_editorial_20261025_r01/SLICE1_SOURCE.json', encoding='utf-8'))
src_map = {it['id']: it for it in items}

# Regex
TAG_PATTERN = re.compile(r'<[^>]+>|==[a-zA-Z0-9_.-]+==|\{[0-9]+\}|_NOT_IN_LOG_')

# Unclosed IDs
UNCLOSED_SIZE_IDS = {
    'STm10001_01.121', 'STm10001_01.249', 'STm10001_03.160', 'STm10001_03.317',
    'STm10001_03.410', 'STm10001_03.412', 'STm10001_03.441'
}

# Banned patterns
import sys
sys.path.append('StellaSora_VietHoa/tools')
import verify_campaign17_proposals as v

def validate_dict(trans_dict, scene_filter=None):
    blockers = []
    majors = []
    
    count = 0
    for iid, vi in trans_dict.items():
        if scene_filter and not iid.startswith(scene_filter):
            continue
        count += 1
        src = src_map.get(iid)
        if not src:
            blockers.append(f"[{iid}] Unknown ID!")
            continue
        
        en = src['en']
        src_tokens = TAG_PATTERN.findall(en)
        dst_tokens = TAG_PATTERN.findall(vi)
        
        # 1. NFC
        if vi != unicodedata.normalize('NFC', vi):
            majors.append(f"[{iid}] Not NFC normalized!")
            
        # 2. Token match
        if sorted(src_tokens) != sorted(dst_tokens):
            blockers.append(f"[{iid}] Token mismatch!\n  Src: {src_tokens}\n  Dst: {dst_tokens}")
            
        # 3. Unclosed size
        if iid in UNCLOSED_SIZE_IDS:
            if '</size>' in vi:
                blockers.append(f"[{iid}] Invented closing </size> tag on unclosed size line!")
        else:
            if '</size>' not in en and '</size>' in vi:
                blockers.append(f"[{iid}] Invented closing </size> tag!")
                
        # 4. Control chars
        src_ctrls = [c for c in en if ord(c) < 32 and c not in '\r\n\t']
        dst_ctrls = [c for c in vi if ord(c) < 32 and c not in '\r\n\t']
        if src_ctrls != dst_ctrls:
            blockers.append(f"[{iid}] Control chars mismatch!")
            
        # 5. Banned words
        for pat, desc in v.BANNED_WORDS:
            if re.search(pat, vi, re.IGNORECASE):
                majors.append(f"[{iid}] Banned word '{pat}': {desc}\n  Text: {vi}")
                
    print(f"Validated {count} items. Blockers: {len(blockers)}, Majors: {len(majors)}")
    for b in blockers[:10]:
        print("  BLOCKER:", b)
    for m in majors[:10]:
        print("  MAJOR:", m)
    return len(blockers) == 0 and len(majors) == 0

if __name__ == '__main__':
    import sys
    sys.path.append('StellaSora_VietHoa/tools')
    from translations_stm10001_slice1 import TRANSLATIONS_SLICE1
    
    print(f"Loaded TRANSLATIONS_SLICE1 with {len(TRANSLATIONS_SLICE1)} items.")
    ok = validate_dict(TRANSLATIONS_SLICE1)
    
    if ok and len(TRANSLATIONS_SLICE1) == 372:
        print("\n>>> FULL SLICE 1 VERIFICATION PASSED (0 BLOCKERS, 0 MAJORS, 100% PARITY)! <<<")
    else:
        print("\n>>> FULL SLICE 1 VERIFICATION FAILED! <<<")



