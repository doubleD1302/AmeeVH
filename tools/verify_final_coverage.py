import json
import os
import re

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
data_dec = os.path.join(viet_dir, r"work\research\data_decrypted\entries")

# Proper nouns and technical strings that are intentionally identical in EN and VI
WHITELIST = {
    "Amber", "Noya", "Iris", "Tilia", "Eleanor", "Portia", "Dorra", "Emor",
    "Bernina", "Virigia", "Minova", "Hazana", "Beatrixa", "Fuyuka", "Chitose",
    "Otoha", "Yuuki Takada", "Rumi Okubo", "Si Bai", "Chen Yu", "Li Chanfei",
    "BT01", "BT", "HP", "ATK", "DEF", "DMG", "CRIT", "EXP", "Lv", "CD", "MP", "SP",
    "Bernina & Virigia", "Virigia & Bernina", "Dorra", "Stella Coin", "Stella",
    "!NONEED!", "!PENDING!", "NONE", "null", "N/A"
}

untranslated_items = []

for fname in os.listdir(data_dec):
    if not fname.endswith(".bin"):
        continue
    fpath = os.path.join(data_dec, fname)
    with open(fpath, "r", encoding="utf-8") as fp:
        try:
            d = json.load(fp)
        except Exception:
            continue
    if not isinstance(d, dict) or not d:
        continue
    
    # Check if this is CN table
    sample_text = " ".join([v for v in d.values() if isinstance(v, str)][:15])
    cn_chars = len(re.findall(r'[\u4e00-\u9fff]', sample_text))
    if cn_chars > 15:
        continue
    
    for k, v in d.items():
        if not isinstance(v, str) or not v.strip():
            continue
        s = v.strip()
        if s in WHITELIST:
            continue
        if s.startswith("Assets/") or s.startswith("UI/") or s.startswith("Audio/") or s.startswith("Prefabs/") or s.startswith("http"):
            continue
            
        stripped = re.sub(r'<[^>]+>', '', s).strip()
        stripped = re.sub(r'\{[0-9a-zA-Z_]+\}', '', stripped).strip()
        stripped = re.sub(r'&[a-zA-Z0-9_]+&', '', stripped).strip()
        
        words = re.findall(r'[a-zA-Z]{2,}', stripped)
        has_vi = bool(re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]', stripped))
        
        # If has multiple English words and no Vietnamese diacritics
        if len(words) >= 2 and not has_vi:
            untranslated_items.append((fname, k, s))

print(f"Remaining genuine English multi-word sentences across ALL EN tables: {len(untranslated_items)}")
for f, k, s in untranslated_items[:20]:
    print(f"  [{f}] {k}: {s[:60]}")
