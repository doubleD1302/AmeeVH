#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")

def scan_all_skills():
    dump_path = ROOT / "work" / "batches" / "all_skill_names_dump.json"
    if not dump_path.exists():
        print("all_skill_names_dump.json not found")
        return
        
    data = json.loads(dump_path.read_text(encoding="utf-8"))
    
    print(f"Total MainSkills: {len(data['main_skills'])}")
    print(f"Total SecondarySkills: {len(data['sec_skills'])}")
    
    # Check suspicious patterns:
    # 1. Untranslated / English characters
    # 2. Clunky words
    # 3. Known bad patterns
    suspicious = []
    
    clunky_words = [
        'bôi trơn', 'động cơ', 'hương chanh', 'giật mình', 'thục huệ',
        'của', 'với', 'trong', 'lăn lộn', 'tò mò', 'lạc lối', 'đập mạnh',
        'nắm đấm của', 'khiến', 'bởi', 'gánh chịu', 'dường như', 'thấu tâm',
        'máy móc', 'nhưng', 'cũng', 'được'
    ]
    
    for sk in data['main_skills'] + data['sec_skills']:
        en = sk['en']
        vi = sk['vi']
        cn = sk['cn']
        key = sk['key']
        table = sk['table']
        
        reasons = []
        # Check if still pure English
        if re.search(r'^[A-Za-z0-9\s:,\'!?\-_★]+$', vi):
            reasons.append("Chưa dịch (còn nguyên tiếng Anh)")
            
        # Check clunky words
        for w in clunky_words:
            if w in vi.lower():
                reasons.append(f"Chứa từ thô/sượng: '{w}'")
                
        # Check if VI equals EN
        if vi.lower() == en.lower():
            reasons.append("Bản dịch trùng 100% tiếng Anh")
            
        if reasons:
            suspicious.append({
                'table': table,
                'key': key,
                'en': en,
                'cn': cn,
                'vi': vi,
                'reasons': reasons
            })
            
    print(f"\nTotal suspicious skill names flagged: {len(suspicious)}")
    out_path = ROOT / "work" / "batches" / "suspicious_skills_audit.json"
    out_path.write_text(json.dumps(suspicious, ensure_ascii=False, indent=2), encoding="utf-8")
    
    for s in suspicious:
        print(f"[{s['table']}:{s['key']}] EN='{s['en']}' | CN='{s['cn']}' | VI='{s['vi']}' -> {', '.join(s['reasons'])}")

if __name__ == "__main__":
    scan_all_skills()
