#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mechanical QA Verification Script for Campaign 5: Act 3 Story & Allies Phone.
Audits PROPOSALS.jsonl against source candidate file:
- 100% Line count matching
- 100% Token parity
- Check for banned calques & MT relics
- Unicode NFC normalization check
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")

BANNED_CALQUES = [
    r"\bMa Vương\b", r"\bbạn biết đấy\b", r"\blàm sao mà\b",
    r"\bcái quái gì\b", r"\btôi đoán vậy\b", r"\bchết tiệt\b",
    r"\btổ tiên của tôi ơi\b"
]

def audit_partition(candidate_path: Path, proposals_path: Path):
    assert candidate_path.exists(), f"Missing candidate {candidate_path}"
    assert proposals_path.exists(), f"Missing proposals {proposals_path}"
    
    cand_lines = [json.loads(l) for l in candidate_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    prop_lines = [json.loads(l) for l in proposals_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    
    cand_dict = {it["id"]: it for it in cand_lines}
    prop_dict = {it["id"]: it for it in prop_lines}
    
    findings = {
        "blockers": [],
        "majors": [],
        "minors": [],
        "total_lines": len(cand_lines),
        "proposed_lines": len(prop_lines)
    }
    
    # Check completeness
    missing = set(cand_dict.keys()) - set(prop_dict.keys())
    if missing:
        findings["blockers"].append(f"Missing {len(missing)} lines in proposal: {list(missing)[:5]}")
        
    for lid, cit in cand_dict.items():
        pit = prop_dict.get(lid)
        if not pit: continue
        
        # Tech lines
        if cit.get("is_tech"):
            if pit.get("vi_editorial") is not None and pit.get("vi_editorial") != cit.get("en"):
                findings["majors"].append(f"[{lid}] Tech line modified: {pit.get('vi_editorial')}")
            continue
            
        vi = pit.get("vi_editorial")
        if not vi or not vi.strip():
            findings["blockers"].append(f"[{lid}] Empty translation")
            continue
            
        # NFC check
        if vi != unicodedata.normalize("NFC", vi):
            findings["minors"].append(f"[{lid}] Non-NFC unicode: {vi[:30]}")
            
        # Token parity
        source_tokens = cit.get("tokens", [])
        for tk in source_tokens:
            if tk not in vi:
                findings["blockers"].append(f"[{lid}] Missing token '{tk}' in translation: '{vi}'")
                
        # Banned calques
        for pattern in BANNED_CALQUES:
            if re.search(pattern, vi, re.IGNORECASE):
                findings["blockers"].append(f"[{lid}] Found banned MT calque '{pattern}' in: '{vi}'")
                
    return findings

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: audit_act3_proposals.py <candidates_jsonl> <proposals_jsonl>")
        sys.exit(1)
    res = audit_partition(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps({
        "total_lines": res["total_lines"],
        "proposed_lines": res["proposed_lines"],
        "blockers_count": len(res["blockers"]),
        "majors_count": len(res["majors"]),
        "minors_count": len(res["minors"]),
        "blockers_sample": res["blockers"][:5],
        "majors_sample": res["majors"][:5]
    }, indent=2, ensure_ascii=False))
