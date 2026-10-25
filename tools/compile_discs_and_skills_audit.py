#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")

def compile_audit_matrix():
    # 1. Load Discs
    discs_file = ROOT / "work" / "batches" / "all_104_discs_survey.json"
    discs = json.loads(discs_file.read_text(encoding="utf-8")) if discs_file.exists() else []
    
    # 2. Load Skills
    char_skills_file = ROOT / "work" / "batches" / "unique_character_skills_audit.json"
    char_skills = json.loads(char_skills_file.read_text(encoding="utf-8")) if char_skills_file.exists() else []
    
    dump_skills_file = ROOT / "work" / "batches" / "all_skill_names_dump.json"
    dump_skills = json.loads(dump_skills_file.read_text(encoding="utf-8")) if dump_skills_file.exists() else {}
    main_skills = dump_skills.get('main_skills', [])
    sec_skills = dump_skills.get('sec_skills', [])
    
    print(f"Loaded: {len(discs)} discs, {len(char_skills)} char skills, {len(main_skills)} main skills, {len(sec_skills)} sec skills")
    
    # Compile candidate remediation list
    # We will curate high-quality recommendations for every clunky / crude item
    
compile_audit_matrix()
