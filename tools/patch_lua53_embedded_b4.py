import json
import re
import os
import sys

ROOT = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
sys.path.insert(0, os.path.join(ROOT, "tools"))
from pipeline_translator_engine import (
    load_master_glossary, translate_batch, post_process_vietnamese
)

b4_path = os.path.join(ROOT, r"work\batches\batch_10k_b4_approved.json")
with open(b4_path, "r", encoding="utf-8") as f:
    data = json.load(f)

terms, forbidden = load_master_glossary()

VI_REGEX = re.compile(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]')

ENGINE_PREFIXES = (
    'fx_', 'story_', 'qstory_', 'ep_', 'city_', 'hotel_', 'wog_', 'luckyoasis_',
    'avg', 'Set', 'Play', 'se_', 'bgm_', 'bgs_', 'btn_', 'icon_', 'item_', 'tex_',
    'music_', 'emoji_', 'tiao2', 'xingshi', 'lengzhan'
)

def clean_and_translate_phrase(phrase: str) -> str:
    # Remove single leading length byte if followed by capital letter or quote
    clean_p = phrase.strip()
    prefix = ""
    if len(clean_p) > 2 and clean_p[0] in '#@$iAzx' and (clean_p[1].isupper() or clean_p[1] in '"\''):
        prefix = clean_p[0]
        clean_p = clean_p[1:]

    # Check if phrase is a genuine sentence/dialogue
    words = re.findall(r'[a-zA-Z]{2,}', clean_p)
    if len(words) >= 2 and not clean_p.startswith(ENGINE_PREFIXES) and not re.match(r'^[a-z0-9_]+$', clean_p):
        if not VI_REGEX.search(clean_p):
            try:
                res = translate_batch([clean_p])[0]
                polished = post_process_vietnamese(res, terms, forbidden)
                polished = re.sub(r'\bCự\s+Thạch\b', 'Cự Tháp', polished)
                polished = re.sub(r'\b(Firstlight|First Light)\s*Noya\b', 'Noya - Khải Minh', polished, flags=re.I)
                polished = re.sub(r'\bSơ Quang\b', 'Khải Minh', polished)
                return prefix + polished
            except Exception:
                return phrase
    return phrase

def patch_line(s: str) -> str:
    parts = re.split(r'([\x00-\x1f]+)', s)
    new_parts = []
    changed = False
    for p in parts:
        if not p or any(ord(c) < 32 for c in p):
            new_parts.append(p)
            continue
        translated = clean_and_translate_phrase(p)
        if translated != p:
            changed = True
        new_parts.append(translated)
    return "".join(new_parts) if changed else s

patched = 0
for k, v in list(data.items()):
    if not v or not v.strip() or VI_REGEX.search(v):
        continue
    if v.strip().startswith('==PLAYER_NAME=='):
        continue

    new_v = patch_line(v)
    if new_v != v:
        data[k] = new_v
        patched += 1

print(f"Patched {patched} embedded binary dialogue lines in Batch 4!")
with open(b4_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("Saved cleanly patched batch_10k_b4_approved.json!")
