import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
orig = json.load(open(ROOT / "work" / "batches" / "batch_10k_b3_partC.json", encoding='utf-8'))
trans = json.load(open(ROOT / "work" / "batches" / "batch_10k_b3_partC_translated.json", encoding='utf-8'))
glossary = json.load(open(ROOT / "config" / "master_glossary.json", encoding='utf-8'))

print("=== CHECKING COMMON CALQUES & TRANSLATION DEFECTS ===")

# 1. Commission -> hoa hồng check
hoa_hong = []
for k, o in orig.items():
    t = trans.get(k, "")
    if "hoa hồng" in t.lower() and "commission" in o.lower():
        hoa_hong.append((k, o, t))
print(f"1. 'hoa hồng' for commission: {len(hoa_hong)}")
for k, o, t in hoa_hong[:5]:
    print(f"   [{k}] Orig: {o}\n        Trans: {t}")

# 2. New Star Guild
new_star = []
for k, o in orig.items():
    t = trans.get(k, "")
    if "new star guild" in o.lower() and "lữ đoàn tân tinh" not in t.lower():
        new_star.append((k, o, t))
print(f"2. 'New Star Guild' not 'Lữ Đoàn Tân Tinh': {len(new_star)}")
for k, o, t in new_star[:5]:
    print(f"   [{k}] Orig: {o}\n        Trans: {t}")

# 3. White Cat Troupe
white_cat = []
for k, o in orig.items():
    t = trans.get(k, "")
    if "white cat troupe" in o.lower() and "gánh xiếc mèo trắng" not in t.lower():
        white_cat.append((k, o, t))
print(f"3. 'White Cat Troupe' not 'Gánh Xiếc Mèo Trắng': {len(white_cat)}")
for k, o, t in white_cat[:5]:
    print(f"   [{k}] Orig: {o}\n        Trans: {t}")

# 4. Imperial Guard
imp_guard = []
for k, o in orig.items():
    t = trans.get(k, "")
    if "imperial guard" in o.lower() and "cận vệ hoàng gia" not in t.lower():
        imp_guard.append((k, o, t))
print(f"4. 'Imperial Guard' not 'Cận Vệ Hoàng Gia': {len(imp_guard)}")
for k, o, t in imp_guard[:5]:
    print(f"   [{k}] Orig: {o}\n        Trans: {t}")

# 5. Radio copy / do you copy
radio_copy = []
for k, o in orig.items():
    t = trans.get(k, "")
    if ("copy" in o.lower()) and any(w in t.lower() for w in ["sao chép", "bản sao", "chép"]):
        radio_copy.append((k, o, t))
print(f"5. Radio copy calques: {len(radio_copy)}")
for k, o, t in radio_copy[:5]:
    print(f"   [{k}] Orig: {o}\n        Trans: {t}")

# 6. Untranslated or mostly English
english_sentences = []
for k, o in orig.items():
    t = trans.get(k, "")
    # Check if more than 5 english words remain
    words_o = set(re.findall(r'[a-zA-Z]{4,}', o))
    words_t = set(re.findall(r'[a-zA-Z]{4,}', t))
    overlap = words_o.intersection(words_t)
    # Ignore names and code tokens
    ignore = {"NOT_IN_LOG", "color", "size", "margin", "left", "right", "align", "alpha", "Noya", "Iris", "Amber", "Taffett", "Hazana", "Angie", "Allie", "Chaton", "Myrsha", "Philae", "Creta", "Emor", "Mirage", "Eureka", "Grace", "Accord", "Dorra", "Virigia", "Virigi", "Coronis", "Kasimira", "Freesia", "Tilia", "Beatrixa", "Portia", "Laru", "Shia", "Nazuna", "Karin", "Willow"}
    overlap = {w for w in overlap if w not in ignore and not w.startswith("STm") and not w.startswith("PM")}
    if len(overlap) >= 3 and len(o.split()) > 4:
        english_sentences.append((k, o, t, overlap))

print(f"6. Untranslated / English leak: {len(english_sentences)}")
for k, o, t, ov in english_sentences[:10]:
    print(f"   [{k}] Overlap: {ov}\n        Orig: {o}\n        Trans: {t}")

# 7. Check bytecode strings in orig
bytecode_issues = []
for k, o in orig.items():
    t = trans.get(k, "")
    if any(c in o for c in ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08', '\x0b', '\x0c', '\x0e', '\x0f', '\x10', '\x11', '\x12', '\x13', '\x14', '\x15', '\x16', '\x17', '\x18', '\x19', '\x1a', '\x1b', '\x1c', '\x1d', '\x1e', '\x1f']):
        bytecode_issues.append((k, o, t))
print(f"7. Bytecode in orig: {len(bytecode_issues)}")
for k, o, t in bytecode_issues[:10]:
    print(f"   [{k}] Orig: {repr(o)}\n        Trans: {repr(t)}")
