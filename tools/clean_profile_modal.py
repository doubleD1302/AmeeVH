#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from pathlib import Path

files = [
    Path("StellaSora_VietHoa/work/SS-Trans/index.html"),
    Path("StellaSora_VietHoa/web/story_translator/index.html")
]

for p in files:
    if not p.exists(): continue
    text = p.read_text(encoding="utf-8")
    
    # Remove the GAS URL input block
    pattern = r'\s*<div style="display:flex; flex-direction:column; gap:8px;">\s*<label style="[^"]*">GOOGLE APPS SCRIPT WEB APP URL.*?</label>.*?</div>'
    cleaned = re.sub(pattern, '', text, flags=re.DOTALL)
    p.write_text(cleaned, encoding="utf-8")
    print(f"✓ Cleaned: {p}")
