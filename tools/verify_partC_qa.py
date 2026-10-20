import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pipeline_translator_engine import load_master_glossary, is_valid_token_preservation, TOKEN_REGEX

input_path = ROOT / "work" / "batches" / "batch_10k_partC_character_stories.json"
trans_path = ROOT / "work" / "batches" / "batch_10k_partC_translated.json"

with open(input_path, "r", encoding="utf-8") as f:
    input_data = json.load(f)

with open(trans_path, "r", encoding="utf-8") as f:
    trans_data = json.load(f)

terms, forbidden = load_master_glossary()

print("=" * 60)
print("QA AUDIT REPORT FOR PART C (CHARACTER STORIES CG_*)")
print("=" * 60)

print("\n1. Key Coverage:")
print(f"   Input entries : {len(input_data)}")
print(f"   Trans entries : {len(trans_data)}")
missing = [k for k in input_data if k not in trans_data]
print(f"   Missing keys  : {len(missing)}")

print("\n2. Technical Token Preservation (==W==, ==PLAYER_NAME==, <color>, <size>):")
token_mismatches = []
for k, orig in input_data.items():
    tr = trans_data.get(k, "")
    if not is_valid_token_preservation(orig, tr):
        token_mismatches.append((k, orig, tr))
print(f"   Token mismatch count: {len(token_mismatches)}")
if token_mismatches:
    for k, o, t in token_mismatches[:5]:
        print(f"     Fail [{k}]: {repr(o)} -> {repr(t)}")

print("\n3. Forbidden Calques & Anti-Sơ Quang Check:")
so_quang_hits = [k for k, v in trans_data.items() if re.search(r'\bSơ Quang\b', v, re.IGNORECASE)]
print(f"   'Sơ Quang' occurrences (Strictly 0 expected): {len(so_quang_hits)}")

forbidden_hits = {}
for f in forbidden:
    hits = [k for k, v in trans_data.items() if f.lower() in v.lower()]
    if hits:
        forbidden_hits[f] = hits
print(f"   Forbidden calques found: {len(forbidden_hits)}")
for f, hits in forbidden_hits.items():
    print(f"     - '{f}': {len(hits)} hits")

print("\n4. 'Commission' translation check (Should be 'ủy thác', not 'hoa hồng'):")
hoa_hong_hits = [k for k, v in trans_data.items() if "hoa hồng" in v.lower()]
print(f"   'hoa hồng' occurrences: {len(hoa_hong_hits)}")
for k in hoa_hong_hits:
    print(f"     [{k}] {trans_data[k]}")

print("\n5. Character Story Samples:")
samples = [
    "CG_112_01.1", "CG_112_01.15", "CG_112_01.28", "CG_112_01.51",
    "CG_103_01.4", "CG_111_01.40", "CG_115_01.19", "CG_144_01.15"
]
for s in samples:
    if s in trans_data:
        print(f"   [{s}]")
        print(f"     EN: {input_data.get(s)}")
        print(f"     VI: {trans_data.get(s)}")

print("\n" + "=" * 60)
print("AUDIT RESULT:", "PASSED 100%" if len(missing) == 0 and len(token_mismatches) == 0 and len(so_quang_hits) == 0 and len(forbidden_hits) == 0 and len(hoa_hong_hits) == 0 else "NEEDS POLISH")
print("=" * 60)
