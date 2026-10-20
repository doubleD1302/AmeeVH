import json
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
dec_dir = ROOT / "work" / "research" / "data_200_decrypted" / "entries"

skills_en = json.loads((dec_dir / "00716_0x998f849a64309b25.bin").read_text(encoding="utf-8"))
potentials_en = json.loads((dec_dir / "00704_0x02ce11eca01b5fc8.bin").read_text(encoding="utf-8"))
talents_en = json.loads((dec_dir / "00764_0x3f0bd5f8db2389b6.bin").read_text(encoding="utf-8"))

skills_zh = json.loads((dec_dir / "00963_0xe2b9fc03308736f9.bin").read_text(encoding="utf-8"))
potentials_zh = json.loads((dec_dir / "00951_0xaa3d5eea04d1e767.bin").read_text(encoding="utf-8"))
talents_zh = json.loads((dec_dir / "01011_0x2ae3485bc9698293.bin").read_text(encoding="utf-8"))

VI_REGEX = re.compile(
    r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ"
    r"ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]"
)

light_char_ids = ["162", "117"] # 162 Firstlight Noya, 117 Jinglin

items = []

# 1. Noya (162) & Jinglin (117) Skills
for k, v in skills_en.items():
    if any(cid in k for cid in light_char_ids) and not VI_REGEX.search(v) and any(c.isalpha() for c in v):
        items.append({
            "table": "Skill",
            "key": k,
            "text_en": v,
            "text_zh": skills_zh.get(k, ""),
            "category": "Skill"
        })

# 2. Noya Potentials
for k, v in potentials_en.items():
    if "5162" in k and not VI_REGEX.search(v) and any(c.isalpha() for c in v):
        items.append({
            "table": "Potential",
            "key": k,
            "text_en": v,
            "text_zh": potentials_zh.get(k, ""),
            "category": "Potential"
        })

# 3. Noya Talents
for k, v in talents_en.items():
    if "162" in k and not VI_REGEX.search(v) and any(c.isalpha() for c in v):
        items.append({
            "table": "Talent",
            "key": k,
            "text_en": v,
            "text_zh": talents_zh.get(k, ""),
            "category": "Talent"
        })

out_path = ROOT / "work" / "batches" / "batch_light_characters_gameplay.json"
out_path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Extracted {len(items)} untranslated items for Light Characters to {out_path}!")

breakdown = {}
for it in items:
    cat = it["category"]
    breakdown[cat] = breakdown.get(cat, 0) + 1
for cat, count in breakdown.items():
    print(f"  {cat}: {count} items")
