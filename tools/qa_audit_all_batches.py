# -*- coding: utf-8 -*-
import json
import re
import unicodedata
import sys

batch_files = [
    'StellaSora_VietHoa/work/batches/BATCH_FIX_01_MECHANISMS_TOKENS.json',
    'StellaSora_VietHoa/work/batches/BATCH_FIX_02_SUBTITLES_CH10001INTRO.json',
    'StellaSora_VietHoa/work/batches/BATCH_FIX_03_DATA_UNTRANSLATED.json',
    'StellaSora_VietHoa/work/batches/BATCH_FIX_04_STORY_SHORT_LINES.json'
]

# Patterns for tokens:
# 1. XML/HTML-like tags: <color=...>, </color>, <space=...>, <sprite=...>, <size=...>, <b>, </b>, <i>, </i>
# 2. Curled params: {0}, {1}, {name}, {PlayerName}, etc.
# 3. Ampersand params: &Param1&, &Param2&, etc.
# 4. Formatter params: %s, %d, %1$s, %1$d, etc.
# 5. Constant tags: ==PLAYER_NAME==, etc.
# 6. Literal escaped newlines: \n, \r\n, or actual newlines \n
token_pattern = re.compile(
    r'<[^>]+>'
    r'|\{[^{}]*\}'
    r'|&[a-zA-Z0-9_]+&'
    r'|%\d*\$?[a-zA-Z]'
    r'|==[A-Z0-9_]+=='
    r'|\\n'
    r'|\\r'
)

all_results = {}

for bfile in batch_files:
    with open(bfile, 'r', encoding='utf-8') as f:
        data = json.load(f)
    b_id = data.get('batch_id')
    entries = data.get('entries', [])
    print(f"==================================================")
    print(f"Auditing Batch: {b_id} ({len(entries)} entries)")
    print(f"==================================================")
    
    token_mismatches = []
    nfc_issues = []
    empty_vi = []
    
    for idx, e in enumerate(entries):
        en = e.get('source_en', '')
        vi = e.get('text_vi', '')
        
        if not vi or not vi.strip():
            empty_vi.append((idx, e.get('id')))
            
        # NFC check
        if unicodedata.normalize('NFC', vi) != vi:
            nfc_issues.append((idx, e.get('id')))
            
        # Token check
        en_toks = sorted(token_pattern.findall(en))
        vi_toks = sorted(token_pattern.findall(vi))
        
        if en_toks != vi_toks:
            token_mismatches.append((idx, e.get('id'), en_toks, vi_toks, en, vi))
            
    print(f"  Total Entries: {len(entries)}")
    print(f"  Empty Translations: {len(empty_vi)}")
    print(f"  NFC Violations: {len(nfc_issues)}")
    print(f"  Token Mismatches: {len(token_mismatches)}")
    
    if token_mismatches:
        for m in token_mismatches:
            print(f"  [TOKEN ERROR] Idx {m[0]} ID {m[1]}:")
            print(f"    EN tokens: {m[2]}")
            print(f"    VI tokens: {m[3]}")
            print(f"    EN: {m[4]}")
            print(f"    VI: {m[5]}")

    all_results[b_id] = {
        'total': len(entries),
        'empty': len(empty_vi),
        'nfc_issues': len(nfc_issues),
        'token_mismatches': len(token_mismatches)
    }

print("\nSummary:", all_results)
