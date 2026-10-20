import json
from pathlib import Path

ROOT = Path("StellaSora_VietHoa")
pairs = json.load(open(ROOT / "work/batches/unique_pairs_batch3.json", encoding="utf-8"))

# Load caches
caches = {}
for cname in ["item_db_translation_cache.json", "rewards_economy_translation_cache.json", "pillars_translation_cache.json"]:
    cp = ROOT / "work/batches" / cname
    if cp.exists():
        caches[cname] = json.loads(cp.read_text(encoding="utf-8"))

# Load translate_mall_ag_items dictionaries
import sys
sys.path.insert(0, str(ROOT / "tools"))
# let's extract strings from translate_mall_ag_items
import re
ag_script = (ROOT / "tools/translate_mall_ag_items.py").read_text(encoding="utf-8")
# Extract dictionaries
mall_ag_dict = {}
for m in re.finditer(r"'([^']+)':\s*'([^']+)'", ag_script):
    mall_ag_dict[m.group(1)] = m.group(2)

print(f"Loaded mall_ag_dict: {len(mall_ag_dict)} entries")

results = []
matched_count = 0
for p in pairs:
    en = p["en"]
    zh = p["zh"]
    cand = None
    source = None
    
    if en in mall_ag_dict:
        cand = mall_ag_dict[en]
        source = "mall_ag_script"
    elif en in caches.get("item_db_translation_cache.json", {}):
        cand = caches["item_db_translation_cache.json"][en]
        source = "item_db_cache"
    elif en in caches.get("rewards_economy_translation_cache.json", {}):
        cand = caches["rewards_economy_translation_cache.json"][en]
        source = "rewards_cache"
    elif en in caches.get("pillars_translation_cache.json", {}):
        cand = caches["pillars_translation_cache.json"][en]
        source = "pillars_cache"
        
    if cand:
        matched_count += 1
    results.append({
        **p,
        "candidate": cand,
        "source": source
    })

print(f"Total pairs: {len(pairs)}, Matched: {matched_count}, Unmatched: {len(pairs) - matched_count}")
Path(ROOT / "work/batches/cross_referenced_batch3.json").write_text(
    json.dumps(results, indent=2, ensure_ascii=False),
    encoding="utf-8"
)
