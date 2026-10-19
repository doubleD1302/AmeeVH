#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "work" / "polish" / "phase2a_dataset.json"

with open(DATASET_PATH, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

for tname, items in dataset.items():
    print(f"=== ANALYSIS OF TABLE {tname} ({len(items)} items) ===")
    
    # Check tokens in this table
    token_patterns = [
        (r'\{[0-9a-zA-Z_]+\}', 'brace token {0}'),
        (r'&Param\d+&', '&Param& token'),
        (r'##[^#]+#[^#]+#|##[^#]+#', '##tag## token'),
        (r'<color=[^>]+>', '<color> tag'),
        (r'</color>', '</color> tag'),
        (r'<sprite=[^>]+>', '<sprite> tag'),
        (r'\\x0b|\x0b', 'vertical tab \\x0b'),
        (r'\\n|\n', 'newline \\n'),
        (r'#\d+#', '#1# token')
    ]
    for pat, desc in token_patterns:
        c = sum(1 for it in items if re.search(pat, it['en']))
        if c > 0:
            print(f"  Token '{desc}': present in {c} items")
