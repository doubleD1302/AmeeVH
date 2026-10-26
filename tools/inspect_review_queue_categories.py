import json
from pathlib import Path
from collections import Counter

RQ_PATH = Path('StellaSora_VietHoa/reports/full_localization_audit_20261026_r02/REVIEW_QUEUE.jsonl')

def inspect_candidates():
    items = []
    with open(RQ_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))

    # Let's inspect by domain
    for domain in ['data', 'story', 'subtitle', 'app_source']:
        dom_items = [x for x in items if x.get('domain') == domain]
        print(f"\n==================================================")
        print(f"DOMAIN: {domain} ({len(dom_items)} candidates)")
        print(f"==================================================")
        
        # Group by category
        by_cat = {}
        for x in dom_items:
            for c in x.get('categories', []):
                by_cat.setdefault(c, []).append(x)
                
        for cat, cat_list in sorted(by_cat.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"\n--- Category: {cat} ({len(cat_list)} items) ---")
            for idx, item in enumerate(cat_list[:3], 1):
                loc = item.get('locator')
                src = repr(item.get('source_en', ''))[:80]
                vi = repr(item.get('text_vi', ''))[:80]
                rat = item.get('rationales', [''])[0][:80]
                print(f"  [{idx}] {loc}")
                print(f"      EN: {src}")
                print(f"      VI: {vi}")
                print(f"      Rationale: {rat}")

if __name__ == '__main__':
    inspect_candidates()
