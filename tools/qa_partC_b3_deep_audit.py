import json
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parent.parent
orig_path = ROOT / "work" / "batches" / "batch_10k_b3_partC.json"
trans_path = ROOT / "work" / "batches" / "batch_10k_b3_partC_translated.json"
glossary_path = ROOT / "config" / "master_glossary.json"

orig = json.load(open(orig_path, encoding='utf-8'))
trans = json.load(open(trans_path, encoding='utf-8'))
glossary = json.load(open(glossary_path, encoding='utf-8')) if glossary_path.exists() else {}

print(f"=== BATCH 3 PART C QA DEEP AUDIT ===")
print(f"Total entries in original: {len(orig)}")
print(f"Total entries in translated: {len(trans)}")

# 1. Key alignment
missing_keys = set(orig.keys()) - set(trans.keys())
extra_keys = set(trans.keys()) - set(orig.keys())
print(f"Missing keys: {len(missing_keys)}, Extra keys: {len(extra_keys)}")

# 2. Check Firstlight Noya / So Quang / Noya
so_quang = []
firstlight = []
noya_orig = []
noya_trans = []
for k, o in orig.items():
    t = trans.get(k, "")
    if "sơ quang" in t.lower():
        so_quang.append((k, o, t))
    if "firstlight" in t.lower():
        firstlight.append((k, o, t))
    if "noya" in o.lower():
        noya_orig.append((k, o, t))
    if "noya" in t.lower():
        noya_trans.append((k, o, t))

print(f"\n--- 1. Firstlight Noya / So Quang Audit ---")
print(f"Occurrences of 'Sơ Quang' (forbidden): {len(so_quang)}")
for k, o, t in so_quang[:5]:
    print(f"  [FAIL] {k}: {t}")
print(f"Occurrences of 'Firstlight' in translation: {len(firstlight)}")
print(f"Occurrences of 'Noya' in original: {len(noya_orig)}")
print(f"Occurrences of 'Noya' in translation: {len(noya_trans)}")
for k, o, t in noya_orig[:10]:
    print(f"  {k} | Orig: {o} | Trans: {t}")

# 3. Token & Tag Integrity
print(f"\n--- 2. Token & Tag Integrity Audit ---")
token_pattern = re.compile(r'==[A-Z0-9_]+==|\{[A-Za-z0-9_]+\}|<color=[^>]+>|</color>|<size=[^>]+>|</size>|<r=[^>]+>.*?</r>|<r=[^>]+>|</r>')
ruby_pattern = re.compile(r'<r=([^>]+)>(.*?)</r>')

token_mismatches = []
ruby_items = []
ruby_errors = []

for k, o in orig.items():
    t = trans.get(k, "")
    
    # Check ruby tags
    o_rubies = ruby_pattern.findall(o)
    t_rubies = ruby_pattern.findall(t)
    if o_rubies or t_rubies:
        ruby_items.append((k, o, t, o_rubies, t_rubies))
        if len(o_rubies) != len(t_rubies):
            ruby_errors.append((k, o, t, "Count mismatch", o_rubies, t_rubies))
        else:
            for r_o, r_t in zip(o_rubies, t_rubies):
                if r_o[0] != r_t[0]: # pronunciation tag
                    ruby_errors.append((k, o, t, f"Ruby attr mismatch '{r_o[0]}' != '{r_t[0]}'", o_rubies, t_rubies))

    # Check ==TAG==
    o_tags = re.findall(r'==[A-Z0-9_]+==', o)
    t_tags = re.findall(r'==[A-Z0-9_]+==', t)
    if Counter(o_tags) != Counter(t_tags):
        token_mismatches.append((k, o, t, f"==TAG== mismatch: {o_tags} vs {t_tags}"))

    # Check <color=...> and </color>
    o_colors_open = re.findall(r'<color=#[A-Fa-f0-9]+>|<color=[a-zA-Z]+>', o)
    t_colors_open = re.findall(r'<color=#[A-Fa-f0-9]+>|<color=[a-zA-Z]+>', t)
    o_colors_close = o.count('</color>')
    t_colors_close = t.count('</color>')
    if len(o_colors_open) != len(t_colors_open) or o_colors_close != t_colors_close:
        token_mismatches.append((k, o, t, f"<color> mismatch: {len(o_colors_open)}/{o_colors_close} vs {len(t_colors_open)}/{t_colors_close}"))

    # Check <size=...> and </size>
    o_size_open = re.findall(r'<size=[0-9]+>', o)
    t_size_open = re.findall(r'<size=[0-9]+>', t)
    o_size_close = o.count('</size>')
    t_size_close = t.count('</size>')
    if len(o_size_open) != len(t_size_open) or o_size_close != t_size_close:
        token_mismatches.append((k, o, t, f"<size> mismatch: {len(o_size_open)}/{o_size_close} vs {len(t_size_open)}/{t_size_close}"))

print(f"Ruby tag items in corpus: {len(ruby_items)}")
print(f"Ruby tag errors: {len(ruby_errors)}")
for err in ruby_errors:
    print(f"  [RUBY ERR] {err[0]}: {err[3]}")
    print(f"    Orig: {err[1]}")
    print(f"    Trans: {err[2]}")

print(f"General token mismatches: {len(token_mismatches)}")
for err in token_mismatches[:10]:
    print(f"  [TOKEN ERR] {err[0]}: {err[3]}")
    print(f"    Orig: {err[1]}")
    print(f"    Trans: {err[2]}")

# 4. Engine Strings & Bytecode Identifiers
print(f"\n--- 3. Engine Identifier & Untranslated Audit ---")
untranslated_count = 0
untranslated_samples = []
for k, o in orig.items():
    t = trans.get(k, "")
    if o.strip() == t.strip():
        # Check if it was an engine string or intentionally untouched
        untranslated_count += 1
        if len(untranslated_samples) < 15:
            untranslated_samples.append((k, o))

print(f"Identical orig and trans: {untranslated_count}")
for k, o in untranslated_samples:
    print(f"  [ID] {k}: '{o}'")

# 5. Master Glossary & Forbidden Terms
print(f"\n--- 4. Master Glossary & Forbidden Term Audit ---")
forbidden_terms = {
    "do you copy": ["sao chép", "bạn có chép", "nghe máy"],
    "copy that": ["sao chép điều đó", "chép lại"],
    "Firstlight / So Quang": ["sơ quang"],
    "New Star Guild": ["Hội Ngôi sao mới", "Hiệp hội Ngôi sao mới"],
    "White Cat Troupe": ["Đội Mèo Trắng", "Bầy Mèo Trắng"],
    "Imperial Guard": ["Vệ binh Hoàng gia"],
    "Commission": ["hoa hồng"],
    "Boss Accord": ["ông chủ"],
}

forbidden_hits = []
for k, t in trans.items():
    o = orig[k]
    t_low = t.lower()
    for term, f_list in forbidden_terms.items():
        for f in f_list:
            if re.search(r'\b' + re.escape(f) + r'\b', t_low, re.IGNORECASE):
                forbidden_hits.append((k, term, f, o, t))

print(f"Forbidden term hits: {len(forbidden_hits)}")
for k, term, f, o, t in forbidden_hits[:15]:
    print(f"  [FORBIDDEN] {k} (term: {term}, matched: '{f}'):")
    print(f"    Orig: {o}")
    print(f"    Trans: {t}")

# 6. Phone Messages Tone & Style Audit (PM*)
print(f"\n--- 5. Phone Messages Tone & Style Audit ---")
pm_keys = [k for k in orig if k.startswith("PM")]
print(f"Total Phone Messages entries: {len(pm_keys)}")
# Sample phone messages to inspect anime chat flavor
print("Sample Phone Messages:")
for k in pm_keys[::100][:10]:
    print(f"  [{k}]")
    print(f"    Orig:  {orig[k]}")
    print(f"    Trans: {trans[k]}")

# 7. Main Story Ch 8 Climax Tone & Style Audit (STm08*)
print(f"\n--- 6. Main Story Ch 8 Climax Tone & Style Audit ---")
stm_keys = [k for k in orig if k.startswith("STm08")]
print(f"Total Main Story Ch 8 entries: {len(stm_keys)}")
print("Sample Main Story Ch 8 lines:")
for k in stm_keys[::200][:8]:
    print(f"  [{k}]")
    print(f"    Orig:  {orig[k]}")
    print(f"    Trans: {trans[k]}")
