# -*- coding: utf-8 -*-
import json
import sys

def inspect_batch(path, start=1, end=None):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    entries = data['entries']
    total = len(entries)
    if end is None or end > total:
        end = total
    print(f"==================================================")
    print(f"BATCH: {data.get('batch_id')} | Showing {start} to {end} of {total}")
    print(f"Translator: {data.get('translator')}")
    print(f"==================================================")
    for idx in range(start - 1, end):
        e = entries[idx]
        print(f"[{idx+1}] ID: {e.get('id')}")
        print(f"  EN: {e.get('source_en')}")
        print(f"  VI: {e.get('text_vi')}")
        print(f"  Notes: {e.get('notes', '')}")
        print("-" * 50)

if __name__ == '__main__':
    batch_num = sys.argv[1] if len(sys.argv) > 1 else '1'
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    end = int(sys.argv[3]) if len(sys.argv) > 3 else None
    files = {
        '1': 'StellaSora_VietHoa/work/batches/BATCH_FIX_01_MECHANISMS_TOKENS.json',
        '2': 'StellaSora_VietHoa/work/batches/BATCH_FIX_02_SUBTITLES_CH10001INTRO.json',
        '3': 'StellaSora_VietHoa/work/batches/BATCH_FIX_03_DATA_UNTRANSLATED.json',
        '4': 'StellaSora_VietHoa/work/batches/BATCH_FIX_04_STORY_SHORT_LINES.json'
    }
    inspect_batch(files[batch_num], start, end)
