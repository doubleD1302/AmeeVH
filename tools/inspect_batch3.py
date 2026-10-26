# -*- coding: utf-8 -*-
import json

with open('StellaSora_VietHoa/work/batches/BATCH_FIX_03_DATA_UNTRANSLATED.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

embedded = [e for e in data['entries'] if e.get('table') == 'embedded_0x80911df3a563e0f3']

print(f"\n--- EMBEDDED VOICE ENTRIES (Total: {len(embedded)}) ---")
# Show a cross-section of voice lines: first 15, middle 15, last 15
indices_to_show = list(range(0, 15)) + list(range(45, 60)) + list(range(96, len(embedded)))

for idx in indices_to_show:
    e = embedded[idx]
    print(f"[{idx+1}] ID: {e.get('id')}")
    print(f"  EN: {e.get('source_en')}")
    print(f"  VI: {e.get('text_vi')}")
    print(f"  Notes: {e.get('notes', '')}")
    print("-" * 50)
