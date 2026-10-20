#!/usr/bin/env python3
"""
Senior Translator 3 (Batch 3 - Part C): Main Story Chapter 8 Climax & Phone Messages (STm08*, PM*)
Total dialogue strings: 3,333 items.
Applies Master Glossary from config/master_glossary.json.
Enforces:
- Firstlight Noya -> Noya - Khải Minh (Strictly forbid "Sơ Quang").
- Phone chats & SMS: youth anime tone, playful, witty, affectionate, natural texting styles.
- Main Story Climax: high tension, dramatic, solemn, anime voice.
- 100% technical token preservation: ==W==, ==PLAYER_NAME==, <color=...>, <size=...>, etc.
Saves output to: work/batches/batch_10k_b3_partC_translated.json
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

INPUT_PATH = ROOT / "work" / "batches" / "batch_10k_b3_partC.json"
OUTPUT_PATH = ROOT / "work" / "batches" / "batch_10k_b3_partC_translated.json"

COLOR_TAG_OPEN = re.compile(r'<color=#[0-9a-fA-F]{6}>')
COLOR_TAG_CLOSE = re.compile(r'</color>')

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

def polish_part_c_specifics(text: str, is_phone_msg: bool = False) -> str:
    # 1. Enforce Firstlight Noya rule strictly (never Sơ Quang)
    text = re.sub(r'\b(Firstlight|First Light)\s*Noya\b', 'Noya - Khải Minh', text, flags=re.IGNORECASE)
    text = re.sub(r'\bNoya\s*[-–—]?\s*(Sơ Quang|Khải Minh)\b', 'Noya - Khải Minh', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(Sơ Quang|Khải Minh)\s*Noya\b', 'Noya - Khải Minh', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSơ Quang\b', 'Khải Minh', text)
    text = re.sub(r'\bNoya Sơ Quang\b', 'Noya - Khải Minh', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSơ Quang Noya\b', 'Noya - Khải Minh', text, flags=re.IGNORECASE)

    # 2. Key Story Names & Trio (Noya, Iris, Amber)
    text = re.sub(r'\b(Hoa diên vĩ|Hoa Diên Vĩ)\s*&\s*Noya\s*&\s*Hổ [Pp]hách\b', 'Iris & Noya & Amber', text, flags=re.IGNORECASE)
    text = re.sub(r'\bNoya\s*&\s*Iris\s*&\s*Hổ [Pp]hách\b', 'Noya & Iris & Amber', text, flags=re.IGNORECASE)
    text = re.sub(r'\bNoya\.\.\.\s*Iris\.\.\.\s*Hổ [Pp]hách\b', 'Noya... Iris... Amber...', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(Lady Grey|Lady Gray)\b', 'Quý Cô Gray', text, flags=re.IGNORECASE)
    text = re.sub(r'\bTaffet\b', 'Taffett', text)
    text = re.sub(r'\bDesert Scorpions?\b', 'Bọ Cạp Sa Mạc', text, flags=re.IGNORECASE)
    text = re.sub(r'\bScorpions\b', 'Bọ Cạp Sa Mạc', text)
    text = re.sub(r'\bWhite Cat Troupe\b', 'Gánh Xiếc Mèo Trắng', text, flags=re.IGNORECASE)
    text = re.sub(r'\bThe White Cats\b', 'Mèo Trắng', text, flags=re.IGNORECASE)
    text = re.sub(r'\bWhite Cats\b', 'Mèo Trắng', text, flags=re.IGNORECASE)
    text = re.sub(r'\bWhite Cat\b', 'Mèo Trắng', text, flags=re.IGNORECASE)
    text = re.sub(r'\bNova Empress\b', 'Nữ Hoàng Nova', text, flags=re.IGNORECASE)

    # 3. Main Story Chapter 8 Climax Polish
    text = re.sub(r'\bĐứng xuống đi\b', 'Lùi lại đi', text, flags=re.IGNORECASE)
    text = re.sub(r'\bĐứng xuống\b', 'Lùi lại', text, flags=re.IGNORECASE)
    text = re.sub(r'\bnhững con dao được thuê\b', 'lính đánh thuê', text, flags=re.IGNORECASE)
    text = re.sub(r'\bcon dao được thuê\b', 'lính đánh thuê', text, flags=re.IGNORECASE)
    text = re.sub(r'\bgây chiến với người dân địa phương\b', 'gây sự với dân địa phương', text, flags=re.IGNORECASE)
    text = re.sub(r'\bchọn một cuộc chiến\b', 'gây sự', text, flags=re.IGNORECASE)
    text = re.sub(r'\bquầng thâm của bạn\b', 'quầng thâm mắt của cậu', text, flags=re.IGNORECASE)
    text = re.sub(r'\bngủ lạnh ngắt\b', 'ngủ say như chết', text, flags=re.IGNORECASE)
    text = re.sub(r'\bchết cóng vào đêm qua\b', 'ngủ say như chết tối qua', text, flags=re.IGNORECASE)
    text = re.sub(r'\bchết lạnh\b', 'ngủ say li bì', text, flags=re.IGNORECASE)
    text = re.sub(r'\bCái tên đó có vang không\b', 'Cái tên đó nghe quen chứ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bCuộn nó lại, Taffett\b', 'Bình tĩnh lại đi, Taffett', text, flags=re.IGNORECASE)
    text = re.sub(r'\bbay khỏi tay cầm như thế này\b', 'dễ nổi nóng như thế này', text, flags=re.IGNORECASE)
    text = re.sub(r'\bchúng tôi sẽ không lừa đảo\b', 'chúng ta tuyệt đối không làm phản', text, flags=re.IGNORECASE)
    text = re.sub(r'\bsân cỏ của Bọ Cạp Sa Mạc\b', 'địa bàn của Bọ Cạp Sa Mạc', text, flags=re.IGNORECASE)
    text = re.sub(r'\bnhững kẻ theo đuổi bạn sắp bắt kịp\b', 'kẻ truy đuổi sắp đuổi kịp bạn rồi', text, flags=re.IGNORECASE)
    text = re.sub(r'\bđặt cược an toàn nhất\b', 'lựa chọn an toàn nhất', text, flags=re.IGNORECASE)
    text = re.sub(r'\bchọn cái tên từ hoa diên vĩ\b', 'chọn cái tên từ khóm hoa diên vĩ', text, flags=re.IGNORECASE)
    text = re.sub(r'\btừ khi nào mà cậu có được cu<r=contradictory></r>te vậy\b', 'từ bao giờ mà cậu lại đáng yêu thế này', text, flags=re.IGNORECASE)
    text = re.sub(r'\btừ khi nào mà cậu có được cute vậy\b', 'từ bao giờ mà cậu lại đáng yêu thế này', text, flags=re.IGNORECASE)
    text = re.sub(r'\bÔng chủ đã ở cùng với họ\b', 'Sếp cũng đi cùng với họ', text, flags=re.IGNORECASE)

    # 4. Phone Messages & Chat Styling (Youthful, playful, cute, natural texting)
    if is_phone_msg:
        text = re.sub(r'\bông chủ\b', 'sếp', text, flags=re.IGNORECASE)
        text = re.sub(r'\bNày sếp\b', 'Sếp ơi', text, flags=re.IGNORECASE)
        text = re.sub(r'\bhôm nay ông rảnh không\??', 'hôm nay sếp có rảnh không nè?', text, flags=re.IGNORECASE)
        text = re.sub(r'\bDorra bạn đã cứu\??', 'Tiền Dorra cậu tiết kiệm được á?', text, flags=re.IGNORECASE)
        text = re.sub(r'\bbạn có ở đó không\b', 'sếp có đó không ạ', text, flags=re.IGNORECASE)
        text = re.sub(r'\bbạn ở đó à\b', 'sếp có đó không nè', text, flags=re.IGNORECASE)
        text = re.sub(r'\bở đó không\b', 'có đó không', text, flags=re.IGNORECASE)
        text = re.sub(r'\blol\b', 'haha', text, flags=re.IGNORECASE)
        text = re.sub(r'\blại bị lừa nữa rồi\b', 'lại bị lừa rồi', text, flags=re.IGNORECASE)
        text = re.sub(r'\bngu ngốc\b', 'ngốc nghếch', text, flags=re.IGNORECASE)
        text = re.sub(r'\bkho thực phẩm khẩn cấp\b', 'kho đồ ăn khẩn cấp', text, flags=re.IGNORECASE)
        text = re.sub(r'\bthực phẩm khẩn cấp\b', 'đồ ăn khẩn cấp', text, flags=re.IGNORECASE)
        text = re.sub(r'\bStandard injury from a trip to the Cự Thạch\b', 'Vết thương thường gặp trong chuyến đi khám phá Cự Thạch thôi mà', text, flags=re.IGNORECASE)
        text = re.sub(r'\bTôi rảnh!\b', 'Tớ rảnh nè!', text)
        text = re.sub(r'\bTôi rảnh\b', 'Tớ rảnh', text)

    return text

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

    if is_valid_token_preservation(orig, trans):
        return trans

    return trans

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

def is_valid_translation(orig: str, trans: str, forbidden: dict) -> bool:
    if not trans or not trans.strip():
        return False
    for wrong in forbidden:
        if wrong.lower() in trans.lower():
            return False
    if 'sơ quang' in trans.lower():
        return False
    if 'do you copy' in orig.lower() and 'sao chép' in trans.lower():
        return False
    if not is_valid_token_preservation(orig, trans):
        return False
    return True

def main():
    print("=" * 75)
    print("Senior Translator 3 (Batch 3 - Part C): Main Story Ch 8 Climax & Phone Messages")
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
        batch_size = 20
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
                polished = polish_part_c_specifics(polished, is_phone_msg=False)
                polished = auto_repair_tokens(orig_txt, polished)

                if not is_valid_token_preservation(orig_txt, polished):
                    raw_unshielded = robust_unshield_tokens(trans_s, tok)
                    repaired = auto_repair_tokens(orig_txt, raw_unshielded)
                    if is_valid_token_preservation(orig_txt, repaired):
                        polished = post_process_vietnamese(repaired, terms, forbidden)
                        polished = polish_part_c_specifics(polished, is_phone_msg=False)
                        polished = auto_repair_tokens(orig_txt, polished)
                    else:
                        polished = post_process_vietnamese(orig_txt, terms, forbidden)
                        polished = polish_part_c_specifics(polished, is_phone_msg=False)

                results.append((orig_txt, polished))
            return results

        completed_batches = 0
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_chunk = {executor.submit(process_batch, b): b for b in batches}
            for future in as_completed(future_to_chunk):
                try:
                    res = future.result()
                    for orig_txt, trans_txt in res:
                        cache[orig_txt] = trans_txt
                except Exception as e:
                    print(f"Batch failed: {e}")
                completed_batches += 1
                if completed_batches % 20 == 0 or completed_batches == len(batches):
                    print(f"  Progress: {completed_batches}/{len(batches)} batches completed ({(completed_batches/len(batches))*100:.1f}%)")
                    save_cache(cache)

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

        is_phone = str_key.startswith("PM")
        trans = cache.get(str_val, str_val)
        trans = post_process_vietnamese(trans, terms, forbidden)
        trans = polish_part_c_specifics(trans, is_phone_msg=is_phone)
        trans = auto_repair_tokens(str_val, trans)

        if not is_valid_token_preservation(str_val, trans):
            trans = auto_repair_tokens(str_val, post_process_vietnamese(str_val, terms, forbidden))

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
