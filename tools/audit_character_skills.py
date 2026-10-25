#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")

def audit_skill_table_names():
    dataset_path = ROOT / "work" / "polish" / "phase2a_dataset.json"
    data = json.loads(dataset_path.read_text(encoding="utf-8"))['Skill']
    
    # Also load CN table for Skill if available
    # Let's find CN skill file
    cn_file = ROOT / "work" / "research" / "data_decrypted" / "entries" / "00661_0x1da55a9cf733eec1.bin"
    cn_skill = {}
    if cn_file.exists():
        cn_skill = json.load(open(cn_file, 'r', encoding='utf-8'))
        
    names = []
    seen = set()
    for it in data:
        key = it.get('key', '')
        en = it.get('en', '')
        vi = it.get('vi_current', '')
        if key.endswith('.1') and len(en) < 60 and '\n' not in en:
            if en not in seen:
                seen.add(en)
                names.append({
                    'key': key,
                    'en': en,
                    'cn': cn_skill.get(key, ''),
                    'vi': vi
                })
                
    print(f"Total unique Skill names in Skill table: {len(names)}")
    out_path = ROOT / "work" / "batches" / "unique_character_skills_audit.json"
    out_path.write_text(json.dumps(names, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # Scan for awkward or crude patterns
    bad = []
    for s in names:
        en = s['en']
        vi = s['vi']
        cn = s['cn']
        issues = []
        if re.search(r'^[A-Za-z0-9\s:,\'!?\-_]+$', vi):
            issues.append("Chưa dịch (tiếng Anh)")
        if vi.lower() == en.lower():
            issues.append("Trùng tiếng Anh")
            
        # Check suspicious patterns
        for pat in ['của', 'được', 'với', 'trong', 'làm', 'bị', 'khiến', 'gây', 'này', 'ấy', 'cho']:
            if f" {pat} " in f" {vi.lower()} ":
                issues.append(f"Chứa hư từ '{pat}'")
                
        if issues:
            bad.append((s, issues))
            
    print(f"Suspicious Skill names: {len(bad)}")
    for s, issues in bad[:35]:
        print(f"[{s['key']}] EN='{s['en']}' | CN='{s['cn']}' | VI='{s['vi']}' -> {', '.join(issues)}")

if __name__ == "__main__":
    audit_skill_table_names()
