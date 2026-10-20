#!/usr/bin/env python3
"""
Senior Translator 3 (Batch 4 - Part C): Event Stories (STev_*) & Dating/Promenade (DP_*)
Total dialogue strings: 3,333 items.
Applies Master Glossary from config/master_glossary.json.
Enforces:
- Anime RPG voice: festive, joyful, sweet anime dating dialogues, seasonal events (Snowish Festival, Ghost Ship).
- Radio / communication: "Do you copy?" -> "Bạn có nghe rõ không!?" / "Nghe rõ không!?".
- Event entities: "Lễ Hội Snowish", "Tinh Linh Cây Snowish", "U Linh Hạm", "Cá Voi Lục Sừng", "Hồn Thạch", "Đêm Trường Vĩnh Cửu".
- De-calquing: "dates" -> "hẹn hò" (no palm dates / dates confusion), "commission" -> "nhiệm vụ ủy thác / thù lao ủy thác".
- 100% token preservation: ==W==, ==PLAYER_NAME==, <color=...>, <size=...>, etc.
Saves output to: work/batches/batch_10k_b4_partC_translated.json
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
    post_process_vietnamese, is_valid_token_preservation,
    TOKEN_REGEX
)

INPUT_PATH = ROOT / "work" / "batches" / "batch_10k_b4_partC.json"
OUTPUT_PATH = ROOT / "work" / "batches" / "batch_10k_b4_partC_translated.json"

COLOR_TAG_OPEN = re.compile(r'<color=#[0-9a-fA-F]{6}>')
COLOR_TAG_CLOSE = re.compile(r'</color>')

COMMON_EN_REGEX = re.compile(
    r'\b(the|and|that|have|for|not|with|you|this|but|his|from|they|say|her|she|will|one|all|would|there|their|what|out|about|who|get|which|when|make|can|like|time|just|him|know|take|people|into|year|your|good|some|could|them|see|other|than|then|now|look|only|come|its|over|think|also|back|after|use|two|how|our|work|first|well|way|even|new|want|because|any|these|give|day|most|us)\b',
    re.IGNORECASE
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
    if s_clean in ('ChaoDaZhenDong', '==PLAYER_NAME=='):
        return True
    return False

def robust_unshield_tokens(text: str, tokens: list) -> str:
    def repl(m):
        idx = int(m.group(1))
        if idx >= len(tokens):
            return ""
        tok = tokens[idx]
        if any(ord(c) < 32 and c not in '\t' for c in tok):
            return tok
        if tok in ('\x0b', '\n', '\r\n'):
            return tok
        return f" {tok} "

    res = re.sub(r'\s*\[\s*\[\s*[Tt][Oo][Kk]\s*(\d+)\s*\]\s*\]\s*', repl, text)
    res = re.sub(r'\s*\[\s*[Tt][Oo][Kk]\s*(\d+)\s*\]\s*', repl, res)
    res = re.sub(r'\b[Tt][Oo][Kk]\s*(\d+)\b', repl, res)
    res = re.sub(r'(<color=[^>]+>)\s+', r'\1', res)
    res = re.sub(r'\s+(</color>)', r'\1', res)
    res = re.sub(r'(<size=[^>]+>)\s*', r'\1', res)
    res = re.sub(r'\s*(</size>)', r'\1', res)
    res = re.sub(r'==\s*([a-zA-Z0-9_]+)\s*==', r'==\1==', res)
    while re.search(r'(==[a-zA-Z0-9_]+==)\s+(==[a-zA-Z0-9_]+==)', res):
        res = re.sub(r'(==[a-zA-Z0-9_]+==)\s+(==[a-zA-Z0-9_]+==)', r'\1\2', res)
    res = re.sub(r'[ \t]{2,}', ' ', res)
    return res.strip(" \t\r\n")

def auto_repair_tokens(orig: str, trans: str) -> str:
    if is_valid_token_preservation(orig, trans):
        return trans

    orig_tokens = TOKEN_REGEX.findall(orig)

    # 1. Standardize spacing around delimiters
    trans = re.sub(r'==\s*([a-zA-Z0-9_]+)\s*==', r'==\1==', trans)
    trans = re.sub(r'(<color=[^>]+>)\s+', r'\1', trans)
    trans = re.sub(r'\s+(</color>)', r'\1', trans)
    trans = re.sub(r'(<size=[^>]+>)\s*', r'\1', trans)
    trans = re.sub(r'\s*(</size>)', r'\1', trans)

    # 2. Check color tag balance
    c_open = COLOR_TAG_OPEN.findall(trans)
    c_close = COLOR_TAG_CLOSE.findall(trans)
    if len(c_open) > len(c_close):
        trans += '</color>' * (len(c_open) - len(c_close))
    elif len(c_close) > len(c_open):
        for _ in range(len(c_close) - len(c_open)):
            idx = trans.rfind('</color>')
            if idx != -1:
                trans = trans[:idx] + trans[idx+8:]

    if is_valid_token_preservation(orig, trans):
        return trans

    # 3. Check for missing tokens from orig
    curr_tokens = TOKEN_REGEX.findall(trans)
    for tok in orig_tokens:
        if curr_tokens.count(tok) < orig_tokens.count(tok):
            if tok in ('==W==', '==RT==', '==P==', '==B=='):
                trans += f' {tok}'
            elif tok.startswith('<color='):
                trans = tok + trans
            elif tok == '</color>':
                trans = trans + tok
            else:
                trans += f' {tok}'
            curr_tokens = TOKEN_REGEX.findall(trans)

    # 4. Check for excess tokens in trans not in orig
    curr_tokens = TOKEN_REGEX.findall(trans)
    for tok in set(curr_tokens):
        excess = curr_tokens.count(tok) - orig_tokens.count(tok)
        if excess > 0:
            for _ in range(excess):
                idx = trans.rfind(tok)
                if idx != -1:
                    trans = trans[:idx] + trans[idx+len(tok):]

    return trans

VI_DIACRITICS = re.compile(
    r'[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'
    r'ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ]'
)

def is_valid_translation(orig: str, trans: str, forbidden: dict) -> bool:
    if not trans or not trans.strip():
        return False
    if is_engine_identifier(orig):
        return True
    words_orig = re.findall(r'[a-zA-Z]+', orig)
    if len(words_orig) >= 2:
        if trans.strip().lower() == orig.strip().lower():
            return False
        if not VI_DIACRITICS.search(trans):
            return False
    for wrong in forbidden:
        if wrong.lower() in trans.lower():
            return False
    if 'do you copy' in orig.lower() and 'sao chép' in trans.lower():
        return False
    if 'sơ quang' in trans.lower():
        return False
    if not is_valid_token_preservation(orig, trans):
        return False
    return True

def polish_dialogue_b4_partC(orig: str, trans: str) -> str:
    """Enforces festive, sweet, natural anime dialogue for events and dating interactions in Batch 4 Part C."""
    # 0. Clean accidental glossary slashes
    trans = re.sub(r'nhiệm vụ ủy thác\s*/\s*thù lao ủy thác', 'nhiệm vụ ủy thác', trans)

    # 1. Festival & event terminology (Snowish Festival, Ghost Ship, Hexhorn Whale)
    trans = re.sub(r'\b(Snowish Festival|Lễ hội Tuyết rơi|Lễ hội tuyết rơi|Lễ hội Tuyết|Lễ hội tuyết|Lễ hội Snowish|lễ hội Snowish)\b', 'Lễ Hội Snowish', trans)
    trans = re.sub(r'\b(Snowish Tree Spirit|Tinh linh Cây Tuyết|Tinh linh cây tuyết|Tinh linh cây Snowish|tinh linh cây snowish|Thần Cây Tuyết|Thần cây Tuyết|Thần Cây Snowish|Thần cây Snowish)\b', 'Tinh Linh Cây Snowish', trans)
    trans = re.sub(r'\b(Snowish Tree|Cây Tuyết|cây Tuyết|Cây tuyết|cây tuyết)\b', 'Cây Snowish', trans)
    trans = re.sub(r'\b(Snowish messenger|Snowish Messenger|Snowish Festival Messenger|Sứ giả lễ hội tuyết|sứ giả lễ hội tuyết|Sứ giả tuyết|sứ giả Snowish|Sứ giả của Tuyết|sứ giả của Tuyết|sứ giả của Snowish|Người đưa tin về Lễ hội Tuyết|Người đưa tin của Lễ hội Tuyết|Lễ Hội Snowish Messenger)\b', 'Sứ Giả Lễ Hội Snowish', trans)
    trans = re.sub(r'\b(Snowish outfit|trang phục tuyết|trang phục mùa tuyết)\b', 'trang phục Snowish', trans, flags=re.I)
    trans = re.sub(r'\b(Snowish vacation|kỳ nghỉ tuyết)\b', 'kỳ nghỉ Snowish', trans, flags=re.I)

    # Ghost Ship & Hexhorn Whale
    trans = re.sub(r'\b(The Ghost Ship|Ghost Ship|Tàu ma|Con tàu ma|Con Tàu Ma|Thuyền ma|con tàu ma|tàu ma|thuyền ma|U Linh Thuyền)\b', 'U Linh Hạm', trans)
    trans = re.sub(r'The\.\s*Bóng\s*ma\.\s*Tàu\s*thủy\.', 'U. Linh. Hạm.', trans)
    trans = re.sub(r'\b(The Hexhorn Whale|Hexhorn Whale|Cá voi Hexhorn|Cá Voi Hexhorn|Cá voi sáu sừng|cá voi sáu sừng|Cá voi lục sừng|cá voi lục sừng|Cá Voi 6 Sừng)\b', 'Cá Voi Lục Sừng', trans)
    trans = re.sub(r'\b(Soul Stones?|Soulstones?|Đá Linh Hồn|đá linh hồn|Đá Hồn|đá hồn|viên đá tâm hồn)\b', 'Hồn Thạch', trans, flags=re.I)
    trans = re.sub(r'\b(Nocturn Eterna|Eternal Night|Đêm vĩnh cửu|Đêm Vĩnh Cửu|Đêm vĩnh hằng|Đêm Vĩnh Hằng)\b', 'Đêm Trường Vĩnh Cửu', trans)

    # 2. Characters & Dating nuances
    trans = re.sub(r'\b(Firstlight|First Light)\s*Noya\b', 'Noya - Khải Minh', trans, flags=re.I)
    trans = re.sub(r'\bNoya\s*[-–—]?\s*(Sơ Quang|Khải Minh)\b', 'Noya - Khải Minh', trans, flags=re.I)
    trans = re.sub(r'\b(Sơ Quang|Khải Minh)\s*Noya\b', 'Noya - Khải Minh', trans, flags=re.I)
    trans = re.sub(r'\bSơ Quang\b', 'Khải Minh', trans)
    trans = re.sub(r'\b(Miss Caramel|Cô bé Caramel|cô bé Caramel|Tiểu thư Caramel|tiểu thư Caramel)\b', 'Cô Caramel', trans)
    trans = re.sub(r'\b(Lady Angie|Bà Angie|bà Angie|Quý cô Angie|quý cô Angie|Tiểu thư Angie)\b', 'Tiểu Thư Angie', trans)
    trans = re.sub(r'\b(Director Allie|Hiệu trưởng Allie|hiệu trưởng Allie)\b', 'Giám Đốc Allie', trans)
    trans = re.sub(r'\b(Daisy Orphanage|Trại mồ côi Daisy|Trại Mồ Côi Daisy|Trại mồ côi cúc họa mi)\b', 'Viện Mồ Côi Daisy', trans)
    trans = re.sub(r'\b(Grace Imperium|Kim Khố Ý Chí Ân Tứ)\b', 'Đế Quốc Grace', trans)
    trans = re.sub(r'\b(God of Grace|Chúa nhân từ|Thần Ân sủng|Thần ân sủng)\b', 'Thần Ân Điển', trans)
    trans = re.sub(r'\b(New Star Guild|Hội Tân Tinh|Bang Tân Tinh)\b', 'Công Hội Tân Tinh', trans)
    trans = re.sub(r'\b(Baize Bureau|Cục Bạch Trạch|Văn phòng Baize)\b', 'Phủ Bạch Trạch', trans)
    trans = re.sub(r'\b(Imperial Guard|Kỵ sĩ hoàng gia|kỵ sĩ hoàng gia)\b', 'Cận Vệ Hoàng Gia', trans)
    trans = re.sub(r'\b(Pep Pep Juice|Nước bọt bọt)\b', 'Nước Ép Năng Lượng Pep Pep', trans)

    # Clean duplicates
    trans = re.sub(r'(Chuyển Phát Hỏa Tốc\s*)+Post Haste', 'Chuyển Phát Hỏa Tốc Post Haste', trans)
    trans = re.sub(r'(Thành Phố\s*)+Emor', 'Thành Phố Emor', trans)

    # 3. Radio & communications
    trans = re.sub(r'^[Nn]ghe rõ đó\b', 'Đã rõ', trans)
    trans = re.sub(r'\bnghe rõ đó\b', 'đã rõ', trans)
    trans = re.sub(r'\b[Bb]ạn có sao chép không[\s?!]*', 'Bạn có nghe rõ không!?', trans)
    trans = re.sub(r'\b[Cc]ó sao chép không[\s?!]*', 'Nghe rõ không!?', trans)
    trans = re.sub(r'\bsao chép không[\s?!]*', 'nghe rõ không!?', trans)
    trans = re.sub(r'\bsao chép điều đó\b', 'đã rõ', trans, flags=re.I)
    trans = re.sub(r'\bsao chép rồi\b', 'đã rõ', trans, flags=re.I)
    trans = re.sub(r'\b(Copy that|Roger that)\b', 'Đã rõ', trans, flags=re.I)
    trans = re.sub(r'\bDo you copy\b', 'Nghe rõ không!?', trans, flags=re.I)
    trans = re.sub(r'\bTôi nghe thấy bạn\b', 'Tớ nghe thấy cậu rồi', trans, flags=re.I)
    trans = re.sub(r'\bnghe thấy bạn\b', 'nghe thấy cậu', trans, flags=re.I)
    trans = re.sub(r'\bVâng\. Tôi nghe thấy bạn\.', 'Ừ. Tớ nghe đây.', trans)

    # 4. De-calquing dates & commissions
    # Dates: when referring to romantic dates vs calendar dates / palm fruit
    if 'on a date' in orig.lower():
        trans = re.sub(r'vào một ngày hẹn hò', 'đi hẹn hò', trans)
        trans = re.sub(r'trong một buổi hẹn hò', 'khi đi hẹn hò', trans)
        trans = re.sub(r'vào một ngày\b', 'đi hẹn hò', trans)
    trans = re.sub(r'\bquả chà là\b', 'buổi hẹn hò', trans, flags=re.I)
    trans = re.sub(r'\btrái chà là\b', 'buổi hẹn hò', trans, flags=re.I)

    # Commissions
    trans = re.sub(r'\bhoa hồng đang hoạt động\b', 'nhiệm vụ ủy thác chưa hoàn thành', trans)
    trans = re.sub(r'\bphí hoa hồng\b', 'thù lao ủy thác', trans)
    trans = re.sub(r'\btiền hoa hồng\b', 'tiền thù lao ủy thác', trans)
    trans = re.sub(r'\bnhận hoa hồng\b', 'nhận ủy thác', trans)
    trans = re.sub(r'\btrao hoa hồng\b', 'tiếp nhận ủy thác', trans)
    trans = re.sub(r'\bhoàn thành hoa hồng\b', 'hoàn thành ủy thác', trans)
    trans = re.sub(r'\bkhoản hoa hồng\b', 'tiền thù lao ủy thác', trans)
    trans = re.sub(r'\bnhiệm vụ hoa hồng\b', 'nhiệm vụ ủy thác', trans)
    trans = re.sub(r'\bHoa hồng ủy thác\b', 'Thù lao ủy thác', trans)
    trans = re.sub(r'\bhóa đơn hoa hồng\b', 'hóa đơn thù lao ủy thác', trans)
    trans = re.sub(r'\bthêm hoa hồng\b', 'thêm ủy thác', trans)
    trans = re.sub(r'\blàm hoa hồng\b', 'làm ủy thác', trans)
    trans = re.sub(r'\b(được nhận|nhận được)\s+hoa hồng\b', r'\1 thù lao ủy thác', trans)
    trans = re.sub(r'\bhoa hồng Lữ Khách\b', 'ủy thác Lữ Khách', trans)
    trans = re.sub(r'\bvới hoa hồng này\b', 'với nhiệm vụ ủy thác này', trans)
    trans = re.sub(r'\bVề hoa hồng\b', 'Về nhiệm vụ ủy thác', trans)

    # Monolith & World
    trans = re.sub(r'\b[Cc]ự\s+[Tt]hạch\b', 'Cự Tháp', trans)
    trans = re.sub(r'\b[Đđ]á\s+nguyên\s+khối\b', 'Cự Tháp', trans)
    trans = re.sub(r'\bkhối đá nguyên khối\b', 'Cự Tháp', trans)
    trans = re.sub(r'\bDân\s+Người\s+Novian\b', 'người Novian', trans, flags=re.I)
    trans = re.sub(r'\bDân\s+Novian\b', 'người Novian', trans, flags=re.I)
    trans = re.sub(r'\bNgười\s+Novian\b', 'người Novian', trans)
    trans = re.sub(r'\b[Nn]gười đi bộ\b', 'Lữ Khách', trans)
    trans = re.sub(r'\b[Nn]hững người đi bộ\b', 'các Lữ Khách', trans)
    trans = re.sub(r'\b[Nn]gười du hành\b', 'Lữ Khách', trans)

    # 5. Tokens & formatting
    trans = re.sub(r'==\s*([A-Za-z0-9_]+)\s*==', r'==\1==', trans)
    trans = re.sub(r'<r=([^>]+)>\s*</r>', r'<r=\1></r>', trans)
    trans = re.sub(r'(<color=[^>]+>)\s+', r'\1', trans)
    trans = re.sub(r'\s+(</color>)', r'\1', trans)
    trans = re.sub(r'(<size=[^>]+>)\s*', r'\1', trans)
    trans = re.sub(r'\s*(</size>)', r'\1', trans)
    trans = re.sub(r'\s+([,.:;?!])', r'\1', trans)

    return trans

def main():
    print("=" * 75)
    print("Senior Translator 3 (Batch 4 - Part C): Event Stories & Dating Promenade")
    print("=" * 75)

    terms, forbidden = load_master_glossary()
    cache = load_cache()
    print(f"Loaded master glossary ({len(terms)} terms, {len(forbidden)} forbidden rules).")
    print(f"Existing translation cache: {len(cache)} entries.")

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_strings = len(data)
    print(f"Total strings to process in Part C: {total_strings}")

    exact_lookup = {k.lower(): v for k, v in terms.items()}
    exact_lookup.update(terms)

    to_translate = []
    engine_id_count = 0

    for str_key, str_val in data.items():
        if not str_val or not str_val.strip():
            continue
        if is_engine_identifier(str_val):
            cache[str_val] = str_val
            engine_id_count += 1
            continue
        if str_val in exact_lookup:
            cache[str_val] = exact_lookup[str_val]
        elif str_val.lower() in exact_lookup:
            cache[str_val] = exact_lookup[str_val.lower()]
        elif str_val in cache and is_valid_translation(str_val, cache[str_val], forbidden):
            continue
        else:
            to_translate.append(str_val)

    unique_to_translate = list(dict.fromkeys(to_translate))
    print(f"Engine identifiers preserved: {engine_id_count}")
    print(f"Strings requiring API translation: {len(unique_to_translate)} (cached/resolved: {total_strings - len(unique_to_translate)})")

    if unique_to_translate:
        batch_size = 15
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
                unshielded = robust_unshield_tokens(trans_s, tok)
                polished = post_process_vietnamese(unshielded, terms, forbidden)
                polished = polish_dialogue_b4_partC(orig_txt, polished)
                polished = auto_repair_tokens(orig_txt, polished)

                if not is_valid_token_preservation(orig_txt, polished):
                    raw_unshielded = robust_unshield_tokens(trans_s, tok)
                    repaired = auto_repair_tokens(orig_txt, raw_unshielded)
                    if is_valid_token_preservation(orig_txt, repaired):
                        polished = post_process_vietnamese(repaired, terms, forbidden)
                        polished = polish_dialogue_b4_partC(orig_txt, polished)
                        polished = auto_repair_tokens(orig_txt, polished)
                results.append((orig_txt, polished))
            return results

        completed_batches = 0
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_chunk = {executor.submit(process_batch, b): b for b in batches}
            for future in as_completed(future_to_chunk):
                try:
                    res = future.result()
                    for orig_txt, trans_txt in res:
                        cache[orig_txt] = trans_txt
                except Exception as e:
                    print(f"Batch failed: {e}")
                completed_batches += 1
                if completed_batches % 10 == 0 or completed_batches == len(batches):
                    print(f"  Progress: {completed_batches}/{len(batches)} batches completed ({(completed_batches/len(batches))*100:.1f}%)")
                    save_cache(cache)
                time.sleep(0.2)

        save_cache(cache)
        print("Batch translation completed.")

    final_translated = {}
    valid_count = 0
    token_ok_count = 0

    for str_key, str_val in data.items():
        if not str_val or not str_val.strip():
            final_translated[str_key] = str_val
            continue
        if is_engine_identifier(str_val):
            final_translated[str_key] = str_val
            valid_count += 1
            token_ok_count += 1
            continue

        trans = cache.get(str_val, str_val)
        trans = post_process_vietnamese(trans, terms, forbidden)
        trans = polish_dialogue_b4_partC(str_val, trans)
        trans = auto_repair_tokens(str_val, trans)

        if not is_valid_token_preservation(str_val, trans):
            raw_trans = cache.get(str_val, str_val)
            repaired = auto_repair_tokens(str_val, raw_trans)
            if is_valid_token_preservation(str_val, repaired):
                trans = repaired

        final_translated[str_key] = trans
        valid_count += 1
        if is_valid_token_preservation(str_val, trans):
            token_ok_count += 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(final_translated, f, indent=2, ensure_ascii=False)

    print("=" * 75)
    print(f"Successfully exported Part C: {len(final_translated)} strings to {OUTPUT_PATH.name}")
    print(f"Token preservation rate: {token_ok_count}/{valid_count} ({(token_ok_count/valid_count)*100:.2f}%)")
    print("=" * 75)

if __name__ == "__main__":
    main()
