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

ENGINE_KEYWORDS = {
    'avg', 'Set', 'Play', 'se_', 'bgm_', 'bgs_', 'btn_', 'icon_', 'item_', 'tex_',
    'fx_', 'story_', 'qstory_', 'ep_', 'city_', 'hotel_', 'wog_', 'luckyoasis_',
    'music_', 'emoji_', 'tiao2', 'xingshi', 'lengzhan'
}

def is_engine_word(w):
    w_low = w.lower()
    return any(w_low.startswith(k) or w_low == k for k in ENGINE_KEYWORDS)

patched_count = 0
for k, v in data.items():
    if not v or not v.strip():
        continue
    # If string contains english words but no Vietnamese diacritics
    words = re.findall(r'[a-zA-Z]{2,}', v)
    if not words or VI_REGEX.search(v):
        continue

    # Ignore pure tags or names
    if v.strip().startswith('==PLAYER_NAME=='):
        continue

    # Split on control chars and multiple spaces
    parts = re.split(r'([\x00-\x1f]+| {2,})', v)
    new_parts = []
    modified = False

    for p in parts:
        p_clean = p.strip()
        p_words = re.findall(r'[a-zA-Z]{2,}', p_clean)
        # Check if this part contains meaningful English dialogue sentence (not pure engine keywords)
        if len(p_words) >= 2 and not all(is_engine_word(w) for w in p_words) and not VI_REGEX.search(p_clean):
            # Strip leading symbols like #, @, etc.
            lead_sym = ""
            core = p_clean
            if core.startswith(('#', '@', '$', '—', '-', 'i', 'x', 'z', 'A', 'G')):
                m = re.match(r'^([^a-zA-Z0-9\s]*[a-zA-Z0-9]?)(.*)', core)
                # If there's an embedded command character
                # Let's see if English phrase follows
                en_match = re.search(r'([A-Z][a-z].*)', core)
                if en_match:
                    lead_sym = core[:en_match.start()]
                    core = en_match.group(1)

            try:
                trans = translate_batch([core])[0]
                polished = post_process_vietnamese(trans, terms, forbidden)
                polished = re.sub(r'\bCự\s+Thạch\b', 'Cự Tháp', polished)
                polished = re.sub(r'\b(Firstlight|First Light)\s*Noya\b', 'Noya - Khải Minh', polished, flags=re.I)
                polished = re.sub(r'\bSơ Quang\b', 'Khải Minh', polished)

                leading_ws = p[:len(p) - len(p.lstrip())]
                trailing_ws = p[len(p.rstrip()):]
                new_parts.append(f"{leading_ws}{lead_sym}{polished}{trailing_ws}")
                modified = True
            except Exception:
                new_parts.append(p)
        else:
            new_parts.append(p)

    if modified:
        data[k] = "".join(new_parts)
        patched_count += 1

print(f"Patched embedded dialogue strings: {patched_count}")
with open(b4_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("Updated batch_10k_b4_approved.json successfully!")
