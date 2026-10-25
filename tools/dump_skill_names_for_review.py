#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")

def dump_all_skills():
    mainskill_path = ROOT / "work" / "polish" / "unique_mainskill.json"
    secskill_path = ROOT / "work" / "polish" / "unique_secskill.json"
    
    main_skills = []
    if mainskill_path.exists():
        data = json.loads(mainskill_path.read_text(encoding="utf-8"))
        for it in data:
            key = it.get('key', '')
            # check if it is a name (ends with .1, or key without dot, or short string)
            if key.endswith('.1') or (len(it.get('en', '')) < 50 and '\n' not in it.get('en', '')):
                main_skills.append({
                    'table': 'MainSkill',
                    'key': key,
                    'en': it.get('en', ''),
                    'cn': it.get('cn', ''),
                    'vi': it.get('vi_current', '')
                })
                
    sec_skills = []
    if secskill_path.exists():
        data = json.loads(secskill_path.read_text(encoding="utf-8"))
        for it in data:
            key = it.get('key', '')
            if key.endswith('.1') or (len(it.get('en', '')) < 50 and '\n' not in it.get('en', '')):
                sec_skills.append({
                    'table': 'SecondarySkill',
                    'key': key,
                    'en': it.get('en', ''),
                    'cn': it.get('cn', ''),
                    'vi': it.get('vi_current', '')
                })
                
    print(f"MainSkill names: {len(main_skills)}")
    print(f"SecondarySkill names: {len(sec_skills)}")
    
    out_all = {
        'main_skills': main_skills,
        'sec_skills': sec_skills
    }
    (ROOT / "work" / "batches" / "all_skill_names_dump.json").write_text(json.dumps(out_all, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Saved to work/batches/all_skill_names_dump.json")

if __name__ == "__main__":
    dump_all_skills()
