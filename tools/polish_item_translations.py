#!/usr/bin/env python3
"""Polishes translated Item Database entries for Stella Sora.

Ensures:
1. All Character names (Amber, Iris, Firefly, Ridge, Freesia, Flora, Mistique, Caramel, etc.) remain intact.
2. Character skins (e.g. Amber: Default -> Amber: Mặc định, Amber: Awakened -> Amber: Thức tỉnh).
3. Character soul keys (e.g. Amber's Soul Key -> Chìa khóa Tâm hồn của Amber).
4. Trekker is consistently translated as 'Lữ khách' (never 'người đi bộ').
5. Title prefixes and formatting are standardized.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EN_BAK = ROOT / "work" / "research" / "data_decrypted" / "entries" / "00577_0xe60634348b826f41.bin.bak"
VI_PATH = ROOT / "work" / "research" / "data_decrypted" / "entries" / "00577_0xe60634348b826f41.bin"

CHAR_NAMES = [
    "Amber", "Tilia", "Kasimira", "Firenze", "Iris", "Noya", "Shimiao", "Chaton",
    "Firefly", "Ridge", "Jinglin", "Coronis", "Nanoha", "Canace", "Ann", "Freesia",
    "Flora", "Teresa", "Donna", "Minova", "Nazuka", "Fuyuka", "Mistique", "Eleanor",
    "Allie", "Sparkla", "Chixia", "Cosette", "Wraith", "Chitose", "Otoha", "Caramel",
    "Gerie", "Laru", "Shia", "Nazuna", "Karin", "Willow", "Vollara", "Neuvira", "Sherlock",
    "Snowish Laru", "Springseek Coronis", "Suntide Willow"
]

def polish():
    with open(EN_BAK, "r", encoding="utf-8") as f:
        en_data = json.load(f)
    with open(VI_PATH, "r", encoding="utf-8") as f:
        vi_data = json.load(f)

    changes = 0

    for k, v in vi_data.items():
        orig_en = en_data[k]
        new_v = v

        # 1. Base character names
        if k.endswith(".1") and orig_en in CHAR_NAMES:
            if new_v != orig_en:
                new_v = orig_en
                changes += 1

        # 2. Skin / Appearance: Default, Awakened
        for cname in CHAR_NAMES:
            if orig_en == f"{cname}: Default":
                new_v = f"{cname}: Mặc định"
                changes += 1
                break
            elif orig_en == f"{cname}: Awakened":
                new_v = f"{cname}: Thức tỉnh"
                changes += 1
                break
            elif orig_en == f"{cname}'s Soul Key":
                new_v = f"Chìa khóa Tâm hồn của {cname}"
                changes += 1
                break

        # 3. Trekker terminology
        if any(w in new_v.lower() for w in ["người đi bộ", "người đi phượt", "người phượt"]):
            new_v = re.sub(r'[Nn]hững người đi bộ', 'các Lữ khách', new_v)
            new_v = re.sub(r'[Nn]gười đi bộ', 'Lữ khách', new_v)
            new_v = re.sub(r'[Nn]hững người đi phượt', 'các Lữ khách', new_v)
            new_v = re.sub(r'[Nn]gười đi phượt', 'Lữ khách', new_v)
            new_v = re.sub(r'[Nn]gười phượt', 'Lữ khách', new_v)
            changes += 1

        # 4. Trekker's Guide
        if orig_en == "Trekker's Guide":
            new_v = "Cẩm nang Lữ khách"
            changes += 1

        # 5. Soul key capitalization
        if new_v.startswith("Chìa khóa linh hồn"):
            new_v = new_v.replace("Chìa khóa linh hồn", "Chìa khóa Tâm hồn")
            changes += 1

        # 6. Specific titles and terms
        if orig_en.startswith("Prefix Title:"):
            title_name = orig_en.replace("Prefix Title:", "").strip()
            # If Google translate gave Tiền tố danh hiệu: ... keep title or translate
            if not new_v.startswith("Tiền tố danh hiệu:"):
                new_v = re.sub(r'^(?:Tiêu đề tiền tố|Tiền tố Tiêu đề):\s*', 'Tiền tố danh hiệu: ', new_v)
                changes += 1

        if orig_en.startswith("Suffix Title:"):
            if not new_v.startswith("Hậu tố danh hiệu:"):
                new_v = re.sub(r'^(?:Tiêu đề hậu tố|Hậu tố Tiêu đề):\s*', 'Hậu tố danh hiệu: ', new_v)
                changes += 1

        if new_v != v:
            vi_data[k] = new_v

    print(f"Applied {changes} polishing changes.")

    # Write back to file
    with open(VI_PATH, "w", encoding="utf-8") as f:
        json.dump(vi_data, f, ensure_ascii=False, indent=2)
    print(f"Updated {VI_PATH}")

if __name__ == "__main__":
    polish()
