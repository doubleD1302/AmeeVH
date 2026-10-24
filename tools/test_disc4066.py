import json, re, unicodedata
from pathlib import Path

raw_path = Path(r"StellaSora_VietHoa\work\editorial\final_cg_npc_and_disc_editorial_20261025_r01\cg_disc4066_raw.json")
with open(raw_path, 'r', encoding='utf-8') as f:
    items = json.load(f)

src_map = {it['id']: it for it in items}

import sys
sys.path.append(r"StellaSora_VietHoa\work\editorial\final_cg_npc_and_disc_editorial_20261025_r01")
from translations_cg_disc4066 import TRANSLATIONS_CG_DISC4066

TAG_PATTERN = re.compile(r'<[^>]+>|==[a-zA-Z0-9_.-]+==|\{[0-9]+\}|_NOT_IN_LOG_')

sys.path.append(r"StellaSora_VietHoa\tools")
import verify_campaign17_proposals as v

blockers = []
majors = []

print(f"Loaded {len(TRANSLATIONS_CG_DISC4066)} translation items. Raw source items: {len(items)}")

if len(TRANSLATIONS_CG_DISC4066) != len(items):
    blockers.append(f"Count mismatch: expected {len(items)}, got {len(TRANSLATIONS_CG_DISC4066)}")

for iid, it in src_map.items():
    if iid not in TRANSLATIONS_CG_DISC4066:
        blockers.append(f"[{iid}] Missing from translation dictionary!")
        continue
    
    vi = TRANSLATIONS_CG_DISC4066[iid]
    en = it['en']
    src_tokens = it['tokens']
    dst_tokens = TAG_PATTERN.findall(vi)
    
    # 1. NFC
    if vi != unicodedata.normalize('NFC', vi):
        majors.append(f"[{iid}] Text is not NFC normalized")
        
    # 2. Token match
    if sorted(src_tokens) != sorted(dst_tokens):
        blockers.append(f"[{iid}] Token mismatch!\n  Src: {src_tokens}\n  Dst: {dst_tokens}")
        
    # 3. Control opcodes
    src_ctrls = [c for c in en if ord(c) < 32 and c not in '\r\n\t']
    dst_ctrls = [c for c in vi if ord(c) < 32 and c not in '\r\n\t']
    if src_ctrls != dst_ctrls:
        blockers.append(f"[{iid}] Control chars mismatch!")
        
    # 4. Banned words
    for pat, desc in v.BANNED_WORDS:
        # Note: in this disc scene, prompt specifically asked for Monolith -> Cự Thạch (not Cự Tháp)
        # So we don't ban Cự Thạch here.
        if re.search(pat, vi, re.IGNORECASE):
            majors.append(f"[{iid}] Banned word '{pat}': {desc}\n  Text: {vi}")

print(f"Verification Results:")
print(f"  Blockers: {len(blockers)}")
print(f"  Majors:   {len(majors)}")

if blockers:
    for b in blockers:
        print("  BLOCKER:", b)
if majors:
    for m in majors:
        print("  MAJOR:", m)

if not blockers and not majors:
    print(">>> ZERO DEFECTS! CG_disc4066 TRANSLATION FULLY VALIDATED! <<<")
