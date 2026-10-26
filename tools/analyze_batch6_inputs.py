import json
from pathlib import Path
from collections import Counter

RQ_PATH = Path('StellaSora_VietHoa/reports/full_localization_audit_20261026_r02/REVIEW_QUEUE.jsonl')

def main():
    items = []
    with open(RQ_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))

    print(f"Total Review Queue items: {len(items)}")
    
    # 1. Texture bundle items (27)
    bundles = [x for x in items if x.get('domain') == 'texture_bundle']
    print(f"\n=== 1. Texture Bundles ({len(bundles)} items) ===")
    for idx, b in enumerate(bundles, 1):
        loc = b.get('locator')
        inst_sha = b.get('installed_sha256', 'none')[:12]
        dist_sha = b.get('dist_sha256', 'none')[:12]
        print(f"[{idx:02d}] {loc:<50} | installed={inst_sha}... | dist={dist_sha}...")

    # 2. Domain breakdown of remaining 398 items
    print("\n=== 2. Text Candidates Breakdown (398 items) ===")
    for domain in ['data', 'story', 'subtitle', 'app_source']:
        domain_items = [x for x in items if x.get('domain') == domain]
        print(f"\n--- Domain: {domain} ({len(domain_items)} items) ---")
        cats = Counter()
        for x in domain_items:
            for c in x.get('categories', []):
                cats[c] += 1
        for cat, count in cats.most_common():
            print(f"    {cat:<35}: {count}")

if __name__ == '__main__':
    main()
