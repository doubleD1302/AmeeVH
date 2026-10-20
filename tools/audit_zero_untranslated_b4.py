import json
import re
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pipeline_translator_engine import (
    load_master_glossary, translate_batch,
    post_process_vietnamese, is_valid_token_preservation,
    shield_tokens, unshield_tokens, TOKEN_REGEX
)

VI_REGEX = re.compile(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]')

ENGINE_PREFIXES = (
    'fx_', 'story_', 'qstory_', 'ep_', 'city_', 'hotel_', 'wog_', 'luckyoasis_',
    'avg', 'Set', 'Play', 'se_', 'bgm_', 'bgs_', 'btn_', 'icon_', 'item_', 'tex_'
)

def is_engine_identifier(s: str) -> bool:
    if any(ord(c) < 32 and c not in '\n\r\t\x0b' for c in s):
        return True
    s_clean = s.strip()
    if re.match(r'^(?:fx_|story_|qstory_|ep_|emoji_|mainstory)[a-zA-Z0-9_]+$', s_clean):
        return True
    if re.match(r'^[a-z0-9_]+$', s_clean):
        return True
    if re.match(r'^Set[A-Z][a-zA-Z0-9_]*$', s_clean):
        return True
    if re.match(r'^AvgChoice_[a-zA-Z0-9_]+$', s_clean):
        return True
    return False

def audit_and_patch_batch(batch_path: Path, terms: dict, forbidden: dict):
    print("=" * 70)
    print(f"Auditing and Patching: {batch_path.name}")
    print("=" * 70)
    with open(batch_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Identify all strings needing translation
    untranslated_keys = []
    untranslated_texts = []
    for k, v in data.items():
        if not v or not v.strip():
            continue
        if is_engine_identifier(v):
            continue
        words = re.findall(r'[a-zA-Z]{2,}', v)
        if len(words) >= 2 and not VI_REGEX.search(v) and not v.strip().startswith(ENGINE_PREFIXES):
            untranslated_keys.append(k)
            untranslated_texts.append(v)

    print(f"Total entries: {len(data):,}")
    print(f"Identified strings requiring Vietnamese translation: {len(untranslated_texts):,}")

    if not untranslated_texts:
        print("All strings already contain Vietnamese translations!")
        return 0

    # 2. Translate in chunks with ThreadPoolExecutor
    batch_size = 25
    chunks = [untranslated_texts[i : i + batch_size] for i in range(0, len(untranslated_texts), batch_size)]
    print(f"Translating {len(untranslated_texts)} items across {len(chunks)} batches with ThreadPoolExecutor(max_workers=10)...")

    def process_chunk(chunk):
        shielded_items = []
        tokens_list = []
        for txt in chunk:
            s, tok = shield_tokens(txt)
            shielded_items.append(s)
            tokens_list.append(tok)

        translated = translate_batch(shielded_items)
        results = []
        for orig_txt, trans_s, tok in zip(chunk, translated, tokens_list):
            polished = post_process_vietnamese(trans_s, terms, forbidden)
            unshielded = unshield_tokens(polished, tok)
            polished = post_process_vietnamese(unshielded, terms, forbidden)

            # Monolith -> Cự Tháp
            polished = re.sub(r'\bCự\s+Thạch\b', 'Cự Tháp', polished)
            polished = re.sub(r'\bĐá\s+nguyên\s+khối\b', 'Cự Tháp', polished)
            polished = re.sub(r'\b(Firstlight|First Light)\s*Noya\b', 'Noya - Khải Minh', polished, flags=re.I)
            polished = re.sub(r'\bSơ Quang\b', 'Khải Minh', polished)

            if not is_valid_token_preservation(orig_txt, polished):
                raw_unshielded = unshield_tokens(trans_s, tok)
                if is_valid_token_preservation(orig_txt, raw_unshielded):
                    polished = post_process_vietnamese(raw_unshielded, terms, forbidden)

            results.append((orig_txt, polished))
        return results

    translated_map = {}
    completed = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_chunk = {executor.submit(process_chunk, c): c for c in chunks}
        for future in as_completed(future_to_chunk):
            try:
                res = future.result()
                for orig_t, trans_t in res:
                    translated_map[orig_t] = trans_t
            except Exception as e:
                print(f"Batch failed: {e}")
            completed += 1
            if completed % 15 == 0 or completed == len(chunks):
                print(f"  Progress: {completed}/{len(chunks)} batches completed ({(completed/len(chunks))*100:.1f}%)")

    # 3. Patch into data
    patched_count = 0
    for k, orig_v in zip(untranslated_keys, untranslated_texts):
        if orig_v in translated_map:
            trans_v = translated_map[orig_v]
            if trans_v != orig_v:
                data[k] = trans_v
                patched_count += 1

    print(f"Successfully patched {patched_count:,} untranslated strings in Batch 4!")
    with open(batch_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved cleanly patched dataset: {batch_path.name}")
    return patched_count

def main():
    terms, forbidden = load_master_glossary()
    b4_path = ROOT / "work" / "batches" / "batch_10k_b4_approved.json"
    if not b4_path.exists():
        print(f"Batch 4 approved dataset does not exist: {b4_path}")
        return 0
    c4 = audit_and_patch_batch(b4_path, terms, forbidden)
    print("=" * 70)
    print(f"ZERO-UNTRANSLATED AUDIT FOR BATCH 4 COMPLETED: {c4} strings patched.")
    print("=" * 70)
    return c4

if __name__ == "__main__":
    main()
