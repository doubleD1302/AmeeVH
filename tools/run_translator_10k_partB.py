#!/usr/bin/env python3
"""
Senior Translator B: Cốt Truyện Chính Chương 3 & Tin Nhắn Điện Thoại (4,073 items)
Translates Main Story Chapter 3 (STm03) & Phone Messages (PM10*, PM11*).
Enforces:
- Youthful, natural, witty tone for phone chat dialogues (no stiff Sino-Vietnamese / awkward calques).
- Standard organization & place names: Thành Phố Emor, Thành Phố Philae, Thương Hội Creta, Giếng Vạn Giới.
- 100% preservation of technical tokens & Lua engine identifiers (Set*, emoji_*, fx_*, ep_*, story_*, etc.).
"""

import json
import re
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pipeline_translator_engine import (
    load_master_glossary, load_cache, save_cache,
    shield_tokens, unshield_tokens, translate_batch,
    post_process_vietnamese, is_valid_token_preservation
)

INPUT_PATH = ROOT / "work" / "batches" / "batch_10k_partB_mainstory3_phone.json"
OUTPUT_PATH = ROOT / "work" / "batches" / "batch_10k_partB_translated.json"

IDENT_PATTERN = re.compile(
    r'^(Set[A-Z][a-zA-Z0-9]+|emoji_[a-z0-9_]+|fx_[a-z0-9_]+|story_[a-z0-9_]+|qstory_[a-z0-9_]+|ep_[a-z0-9_]+|[a-z0-9]+(_[a-z0-9]+)+)$'
)

PART_B_CURATED_TERMS = {
    "Interlude I": "Khúc Đệm I",
    "Interlude (II)": "Khúc Đệm (II)",
    "The Phone": "Chiếc Điện Thoại",
    "Well of Worlds": "Giếng Vạn Giới",
    "Well of Worlds Tyrant Development System": "Hệ Thống Bồi Dưỡng Bạo Chúa Giếng Vạn Giới",
    "Creta Trading": "Thương Hội Creta",
    "the Creta Trading": "Thương Hội Creta",
    "Throne": "Vương Tọa",
    "Tawny Nightingale": "Bánh Mì Họa Mi Nâu",
    "Seal of Grace": "Dấu Ấn Ân Sủng",
    "Soul Trading": "Giao Dịch Linh Hồn",
    "Soul trading": "Giao dịch linh hồn",
    "soul trading": "giao dịch linh hồn",
    "soul trades": "giao dịch linh hồn",
    "soul trade": "giao dịch linh hồn",
    "Monolith Meltdown": "Vụ Tan Chảy Cự Tháp",
    "Stellaroid": "Stellaroid",
    "Waterway": "Thủy Đạo",
    "Philae": "Thành Phố Philae",
    "Emor": "Thành Phố Emor",
}

def is_valid_translation(orig: str, trans: str) -> bool:
    if not trans or not trans.strip():
        return False
    if orig == trans:
        words = re.findall(r'[a-zA-Z]{2,}', orig)
        has_vi = bool(re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]', trans))
        if len(words) >= 2 and not has_vi:
            return False
    return True

def polish_partB_dialogue(orig: str, trans: str, is_pm: bool = False) -> str:
    # 1. First, if orig is an engine/asset identifier, preserve 100%
    if IDENT_PATTERN.match(orig):
        return orig

    # 2. Fix duplicate place name artifacts and multiple repetitions
    trans = re.sub(r'(?:thành\s*phố\s*){2,}', 'Thành Phố ', trans, flags=re.IGNORECASE)
    trans = re.sub(r'\bThành Phố Emor City\b', 'Thành Phố Emor', trans, flags=re.IGNORECASE)
    trans = re.sub(r'\bThành Phố Philae City\b', 'Thành Phố Philae', trans, flags=re.IGNORECASE)
    trans = re.sub(r'(?:người\s*){2,}', 'Người ', trans, flags=re.IGNORECASE)
    trans = re.sub(r'(?:dân\s*){2,}', 'Dân ', trans, flags=re.IGNORECASE)

    # 3. Master Glossary & Organizations & Monolith
    trans = re.sub(r'\b(Giao dịch|Thương mại|Thương vụ)\s+Creta\b', 'Thương Hội Creta', trans, flags=re.IGNORECASE)
    trans = re.sub(r'\bxen kẽ tôi\b', 'Khúc Đệm I', trans, flags=re.IGNORECASE)
    trans = re.sub(r'\bKhúc dạo đầu \(II\)\b', 'Khúc Đệm (II)', trans, flags=re.IGNORECASE)
    trans = re.sub(r'\b(con chim sơn ca|chim sơn ca)\s+Tawny\b', 'Bánh Mì Họa Mi Nâu', trans, flags=re.IGNORECASE)
    trans = re.sub(r'\bTawny Nightingale\b', 'Bánh Mì Họa Mi Nâu', trans)
    trans = re.sub(r'\bGiếng nước Bạo [cC]húa\b', 'Giếng Vạn Giới Bạo Chúa', trans)
    trans = re.sub(r'\bWell of Worlds\b', 'Giếng Vạn Giới', trans)

    # Fix Monolith calques
    trans = re.sub(r'(?:tảng|khối|những khối|các khối)\s*đá\s*nguyên\s*khối', 'Cự Tháp', trans, flags=re.IGNORECASE)
    trans = re.sub(r'(?:tảng|khối)\s*nguyên\s*khối', 'Cự Tháp', trans, flags=re.IGNORECASE)
    trans = re.sub(r'\bthực phẩm nguyên khối\b', 'thực phẩm Cự Tháp', trans, flags=re.IGNORECASE)
    trans = re.sub(r'\bVụ tan chảy đá nguyên(?:\s*khối)?\b', 'Vụ Tan Chảy Cự Tháp', trans, flags=re.IGNORECASE)

    # 4. Idiomatic dialogue fixes
    trans = re.sub(r'\bTôi có cái này rồi\.\.\.!', 'Mình làm được mà...!', trans)
    trans = re.sub(r'\bBạn hiểu rồi, Fuyuka!', 'Cố lên nhé, Fuyuka!', trans)
    trans = re.sub(r'\bbạn đã hoàn toàn hiểu được điều này\b', 'cậu chắc chắn sẽ làm được thôi!', trans)
    trans = re.sub(r'\bcó ý nghĩa tốt với tôi\b', 'có ý tốt với tôi', trans)
    trans = re.sub(r'\bThực ra nó có ý nghĩa\b', 'Nghĩ kỹ thì cũng hợp lý thật', trans)
    trans = re.sub(r'\bđiều đó có ý nghĩa\b', 'điều đó cũng hợp lý', trans, flags=re.IGNORECASE)
    trans = re.sub(r'\bhoàn toàn không có ý nghĩa gì\b', 'hoàn toàn vô lý hết sức', trans, flags=re.IGNORECASE)
    trans = re.sub(r'\bcó ý nghĩa hoàn hảo\b', 'hoàn toàn hợp lý', trans, flags=re.IGNORECASE)
    trans = re.sub(r'\bkhông bao giờ có ý nghĩa quá nhiều đối với tôi\b', 'trước giờ tớ thấy nó chẳng hợp lý chút nào', trans, flags=re.IGNORECASE)

    # 5. Phone chat specific natural tone (PM*)
    if is_pm:
        trans = re.sub(r'NP\. Nó giống như trở về nhà', 'Không sao đâu. Cảm giác như được về nhà vậy', trans)
        trans = re.sub(r'Hãy cho tôi biết nếu bạn hiểu được điều này, ==PLAYER_NAME==!', 'Nhắn lại cho tớ nếu cậu nhận được tin này nhé, ==PLAYER_NAME==!', trans)
        trans = re.sub(r'Đúng, đã nhận được tin nhắn', 'Rồi, tớ nhận được rồi', trans)
        trans = re.sub(r'Không, tôi chưa nhận được nó', 'Chưa, tớ chưa nhận được đâu', trans)
        trans = re.sub(r'Ơ\? Đây có phải là lỗi của tôi không\?', 'Ơ? Máy tớ bị lỗi à?', trans)
        trans = re.sub(r'Không, tôi chỉ gửi nó hai lần vì tôi quá phấn khích', 'Không, tại tớ hào hứng quá nên bấm gửi tận hai lần đó!', trans)
        trans = re.sub(r'Heh, lần đầu tiên tôi sử dụng điện thoại cũng bị như vậy', 'Heh, lần đầu tiên tớ dùng điện thoại cũng bị y như vậy đó', trans)
        trans = re.sub(r'Một chiếc điện thoại di động mới có giá bao nhiêu\?', 'Một chiếc điện thoại mới có đắt lắm không nhỉ?', trans)
        trans = re.sub(r'Có lẽ hãy hỏi Iris sau', 'Chắc lát nữa phải hỏi Iris xem sao', trans)
        trans = re.sub(r'Đợi một chút! Bạn đã nhận được tin nhắn của tôi!', 'Ủa khoan đã! Rõ ràng là cậu nhận được tin nhắn rồi mà!', trans)
        trans = re.sub(r'Tôi nghĩ có kẹo trong túi tôi\. Thú vị\?', 'Hình như trong túi tớ có kẹo này. Cậu muốn ăn thử không?', trans)
        trans = re.sub(r'Ôi, tôi suýt quên mất điều quan trọng', 'Ôi, tí thì tớ quên mất chuyện quan trọng', trans)
        trans = re.sub(r'Nếu bạn cảm thấy không khỏe vì bất kỳ lý do gì, hãy cho chúng tôi biết, được chứ\?', 'Nếu cậu thấy không khỏe ở đâu thì cứ bảo tụi tớ nhé, nha?', trans)
        trans = re.sub(r'Chúng tôi sẽ chăm sóc bạn thật tốt kể từ khi chúng tôi đưa bạn ra khỏi Cự Tháp!', 'Tụi tớ đã đưa cậu ra khỏi Cự Tháp thì nhất định sẽ chăm sóc cậu thật chu đáo!', trans)
        trans = re.sub(r'Tôi có bạn trên điện thoại của tôi!', 'Tớ có số của cậu rồi nha!', trans)
        trans = re.sub(r'Đây! Thông tin liên lạc của tôi\.', 'Đây nè! Thông tin liên lạc của tôi.', trans)
        trans = re.sub(r'Ghé qua để kiểm tra\?', 'Đến để kiểm tra à?', trans)
        trans = re.sub(r'Tôi thậm chí còn làm hỏng nút "gửi"', 'Tớ còn suýt làm hỏng cả nút "gửi" nữa này', trans)
        trans = re.sub(r'Nếu bạn có hoa hồng cho tôi', 'Nếu bạn có ủy thác gì cho tôi', trans)
        trans = re.sub(r'chúng tôi có thể có được một hoa hồng', 'chúng ta có thể nhận được một ủy thác', trans)
        trans = re.sub(r'\bbáo cáo trong\b', 'xin báo cáo', trans)
        trans = re.sub(r'Này này này!', 'Hế lô hế lô!', trans)
        trans = re.sub(r'người bảo vệ Công lý', 'Người Bảo Vệ Công Lý', trans, flags=re.IGNORECASE)

    # 6. Clean accidental single character prefixes
    trans = re.sub(r'^[%\^!=\+58Zz](?=[A-ZÀ-Ỹa-zà-ỹ\s])', '', trans)

    # Final cleanup of any trailing/leading duplicate spaces
    trans = re.sub(r'[ \t]{2,}', ' ', trans)
    return trans.strip()

def main():
    print("=" * 70)
    print("Senior Translator B: Cốt Truyện Chính Chương 3 & Tin Nhắn Điện Thoại")
    print("=" * 70)

    terms, forbidden = load_master_glossary()
    cache = load_cache()
    print(f"Loaded master glossary ({len(terms)} terms, {len(forbidden)} forbidden rules).")
    print(f"Existing translation cache: {len(cache)} entries.")

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_strings = len(data)
    print(f"Total strings to process: {total_strings}")

    exact_lookup = {k.lower(): v for k, v in terms.items()}
    exact_lookup.update(terms)
    for k, v in PART_B_CURATED_TERMS.items():
        exact_lookup[k] = v
        exact_lookup[k.lower()] = v

    to_translate = []
    for str_key, str_val in data.items():
        if not str_val or not str_val.strip():
            continue
        if IDENT_PATTERN.match(str_val):
            cache[str_val] = str_val
            continue
        if str_val in exact_lookup:
            cache[str_val] = exact_lookup[str_val]
        elif str_val.lower() in exact_lookup:
            cache[str_val] = exact_lookup[str_val.lower()]
        elif str_val in cache and is_valid_translation(str_val, cache[str_val]):
            continue
        else:
            to_translate.append(str_val)

    unique_to_translate = list(dict.fromkeys(to_translate))
    print(f"Strings to translate via API: {len(unique_to_translate)} (resolved: {total_strings - len(unique_to_translate)})")

    if unique_to_translate:
        batch_size = 25
        batches = [unique_to_translate[i : i + batch_size] for i in range(0, len(unique_to_translate), batch_size)]
        print(f"Processing {len(unique_to_translate)} strings across {len(batches)} batches with ThreadPoolExecutor...")

        def process_batch(chunk):
            shielded_items = []
            tokens_list = []
            for txt in chunk:
                s, tok = shield_tokens(txt)
                shielded_items.append(s)
                tokens_list.append(tok)

            translated_shielded = translate_batch(shielded_items)
            results = []
            for orig_txt, trans_s, tok in zip(chunk, translated_shielded, tokens_list):
                unshielded = unshield_tokens(trans_s, tok)
                polished = post_process_vietnamese(unshielded, terms, forbidden)
                if not is_valid_token_preservation(orig_txt, polished):
                    polished = post_process_vietnamese(orig_txt, terms, forbidden)
                results.append((orig_txt, polished))
            return results

        completed_batches = 0
        with ThreadPoolExecutor(max_workers=6) as executor:
            future_to_batch = {executor.submit(process_batch, b): b for b in batches}
            for fut in as_completed(future_to_batch):
                batch_res = fut.result()
                for orig_txt, polished in batch_res:
                    cache[orig_txt] = polished
                completed_batches += 1
                if completed_batches % 25 == 0 or completed_batches == len(batches):
                    print(f"  Completed batch {completed_batches}/{len(batches)} ({completed_batches/len(batches)*100:.1f}%)")
                    save_cache(cache)

        save_cache(cache)
        print("Batch translation complete and saved to cache.")

    translated_data = {}
    for str_key, str_val in data.items():
        if not str_val or not str_val.strip():
            translated_data[str_key] = str_val
            continue

        if IDENT_PATTERN.match(str_val):
            translated_data[str_key] = str_val
            continue

        trans = cache.get(str_val, str_val)
        trans = post_process_vietnamese(trans, terms, forbidden)
        is_pm = str_key.startswith("PM")
        polished = polish_partB_dialogue(str_val, trans, is_pm=is_pm)
        if not is_valid_token_preservation(str_val, polished):
            polished = trans
        if not is_valid_token_preservation(str_val, polished):
            polished = post_process_vietnamese(str_val, terms, forbidden)

        translated_data[str_key] = polished

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(translated_data, f, ensure_ascii=False, indent=2)

    print(f"Part B translation finished: {len(translated_data)} strings.")
    print(f"Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
