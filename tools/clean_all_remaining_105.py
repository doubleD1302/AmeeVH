import json
import re
import os
import sys

ROOT = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
sys.path.insert(0, os.path.join(ROOT, "tools"))
from pipeline_translator_engine import (
    load_master_glossary, translate_batch, post_process_vietnamese,
    shield_tokens, unshield_tokens, is_valid_token_preservation
)

b4_path = os.path.join(ROOT, r"work\batches\batch_10k_b4_approved.json")
with open(b4_path, "r", encoding="utf-8") as f:
    data = json.load(f)

terms, forbidden = load_master_glossary()

VI_REGEX = re.compile(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]')

ENGINE_PREFIXES = (
    'fx_', 'story_', 'qstory_', 'ep_', 'city_', 'hotel_', 'wog_', 'luckyoasis_',
    'avg', 'Set', 'Play', 'se_', 'bgm_', 'bgs_', 'btn_', 'icon_', 'item_', 'tex_'
)

to_fix_keys = []
to_fix_texts = []

for k, v in data.items():
    if not v or not v.strip():
        continue
    if v.strip() in ('==PLAYER_NAME==...', '==PLAYER_NAME==!', '==PLAYER_NAME=='):
        continue
    if re.match(r'^(?:fx_|story_|ep_|btn_|icon_|item_|tex_)[a-z0-9_]+$', v.strip()):
        continue
    words = re.findall(r'[a-zA-Z]{2,}', v)
    if words and not VI_REGEX.search(v) and not v.strip().startswith(ENGINE_PREFIXES):
        to_fix_keys.append(k)
        to_fix_texts.append(v)

print(f"Total lines needing final clean translation: {len(to_fix_texts)}")

if to_fix_texts:
    shielded_items = []
    tokens_list = []
    for txt in to_fix_texts:
        s, tok = shield_tokens(txt)
        shielded_items.append(s)
        tokens_list.append(tok)

    translated = translate_batch(shielded_items)
    for k, orig_txt, trans_s, tok in zip(to_fix_keys, to_fix_texts, translated, tokens_list):
        polished = post_process_vietnamese(trans_s, terms, forbidden)
        unshielded = unshield_tokens(polished, tok)
        polished = post_process_vietnamese(unshielded, terms, forbidden)

        polished = re.sub(r'\bCự\s+Thạch\b', 'Cự Tháp', polished)
        polished = re.sub(r'\bĐá\s+nguyên\s+khối\b', 'Cự Tháp', polished)
        polished = re.sub(r'\b(Firstlight|First Light)\s*Noya\b', 'Noya - Khải Minh', polished, flags=re.I)
        polished = re.sub(r'\bSơ Quang\b', 'Khải Minh', polished)

        if not is_valid_token_preservation(orig_txt, polished):
            raw_unshielded = unshield_tokens(trans_s, tok)
            if is_valid_token_preservation(orig_txt, raw_unshielded):
                polished = post_process_vietnamese(raw_unshielded, terms, forbidden)

        data[k] = polished

    with open(b4_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Cleaned and patched all remaining lines in batch_10k_b4_approved.json!")
