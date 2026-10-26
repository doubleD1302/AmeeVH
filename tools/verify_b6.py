import json
import unicodedata

def verify_b6():
    with open('StellaSora_VietHoa/work/batches/BATCH_FIX_06_POLISH_CANDIDATES.json', 'r', encoding='utf-8') as f:
        d = json.load(f)

    entries = d.get('entries', [])
    print(f"Total proposals in Batch 6: {len(entries)}")
    
    empty = 0
    non_nfc = 0
    for e in entries:
        vi = e.get('text_vi', '')
        if not vi.strip():
            empty += 1
        if unicodedata.normalize('NFC', vi) != vi:
            non_nfc += 1

    print(f"Empty: {empty}")
    print(f"Non-NFC: {non_nfc}")
    assert empty == 0 and non_nfc == 0, "Technical check failed"
    print("BATCH 6 TECHNICAL CHECK 100% PASS!")

if __name__ == '__main__':
    verify_b6()
