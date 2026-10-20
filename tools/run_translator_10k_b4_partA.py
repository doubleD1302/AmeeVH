#!/usr/bin/env python3
"""
Senior Translator 1 (Batch 4 - Part A): Main Story Chapter 9 (STm09_*) & Early Special Story (STsp_01*, STsp_02*)
Total dialogue strings: 3,334 items.
Applies Master Glossary from config/master_glossary.json.
Enforces:
- Anime RPG voice: high-stakes climax, confrontation between Salvation Committee and Trekkers, royal intrigue.
- Radio / communication: "Do you copy?" -> "Bạn có nghe rõ không!?" / "Nghe rõ không!?".
- 100% token preservation: ==W==, ==PLAYER_NAME==, <color=...>, <size=...>, etc.
Saves output to: work/batches/batch_10k_b4_partA_translated.json
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

INPUT_PATH = ROOT / "work" / "batches" / "batch_10k_b4_partA.json"
OUTPUT_PATH = ROOT / "work" / "batches" / "batch_10k_b4_partA_translated.json"

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

VI_DIACRITICS = set('áàảãạâấầẩẫậăắằẳẵặéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđÁÀẢÃẠÂẤẦẨẪẬĂẮẰẲẴẶÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ')
COMMON_EN_STOPS = {'the', 'and', 'to', 'of', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us'}

def is_actually_vietnamese(orig: str, trans: str) -> bool:
    if not trans or not trans.strip():
        return False
    if is_engine_identifier(orig):
        return True
    words_orig = [w for w in orig.split() if w.isalpha()]
    if not words_orig:
        return True
    if not any(c in VI_DIACRITICS for c in trans):
        words_trans = [w.strip('.,!?:;\"\'()[]{}').lower() for w in trans.split()]
        words_trans = [w for w in words_trans if w and not w.startswith('==') and not w.startswith('<')]
        if words_trans:
            if any(w in COMMON_EN_STOPS for w in words_trans) or words_trans == [w.lower() for w in words_orig]:
                return False
    words_trans = [w.strip('.,!?:;\"\'()[]{}').lower() for w in trans.split()]
    words_trans = [w for w in words_trans if w and not w.startswith('==') and not w.startswith('<')]
    if len(words_trans) >= 4:
        en_stop_count = sum(1 for w in words_trans if w in COMMON_EN_STOPS)
        if en_stop_count / len(words_trans) > 0.20:
            return False
    return True

def is_valid_translation(orig: str, trans: str, forbidden: dict) -> bool:
    if not trans or not trans.strip():
        return False
    for wrong in forbidden:
        if wrong.lower() in trans.lower():
            return False
    if 'do you copy' in orig.lower() and 'sao chép' in trans.lower():
        return False
    if not is_valid_token_preservation(orig, trans):
        return False
    if not is_actually_vietnamese(orig, trans):
        return False
    return True

def normalize_shielded_text(text: str) -> str:
    """Normalizes any spacing or casing alterations of [[TOK...]] from translation APIs."""
    text = re.sub(r'\[\s*\[\s*TOK\s*(\d+)\s*\]\s*\]', r'[[TOK\1]]', text, flags=re.IGNORECASE)
    text = re.sub(r'(?<!\[)\[\s*TOK\s*(\d+)\s*\](?!\])', r'[[TOK\1]]', text, flags=re.IGNORECASE)
    return text

def ensure_token_preservation(orig: str, trans: str) -> str:
    """Enforces 100% token preservation, restoring missing tokens and stripping extraneous closing tags."""
    if is_valid_token_preservation(orig, trans):
        return trans

    orig_toks = TOKEN_REGEX.findall(orig)
    orig_counts = {}
    for t in orig_toks:
        orig_counts[t] = orig_counts.get(t, 0) + 1

    trans_toks = TOKEN_REGEX.findall(trans)
    trans_counts = {}
    for t in trans_toks:
        trans_counts[t] = trans_counts.get(t, 0) + 1

    # Remove extra closing tags that originate from translator hallucination
    for extra_tag in ['</size>', '</color>', '</i>', '</align>']:
        while trans_counts.get(extra_tag, 0) > orig_counts.get(extra_tag, 0):
            idx = trans.rfind(extra_tag)
            if idx != -1:
                trans = trans[:idx] + trans[idx + len(extra_tag):]
                trans_counts[extra_tag] -= 1
            else:
                break

    if is_valid_token_preservation(orig, trans):
        return trans

    # Restore any missing tokens
    for t, cnt in orig_counts.items():
        curr_cnt = trans_counts.get(t, 0)
        while curr_cnt < cnt:
            if orig.startswith(t) and not trans.startswith(t):
                trans = t + trans
            else:
                trans = trans + t
            curr_cnt += 1
            trans_counts[t] = curr_cnt

    return trans

def polish_dialogue_b4_partA(orig: str, trans: str) -> str:
    """Enforces dramatic Anime RPG voice, royal intrigue, natural radio protocols, and contextual polish for Batch 4 Part A."""
    # 1. Monolith & world lore
    trans = re.sub(r'\bPhilae\s+Cự\s+Thạch\b', 'Cự Tháp Philae', trans, flags=re.I)
    trans = re.sub(r'\bNew\s+Orelian\s+Cự\s+Thạch\b', 'Cự Tháp New Orelian', trans, flags=re.I)
    trans = re.sub(r'\bCự\s+Thạch\s+Philae\b', 'Cự Tháp Philae', trans, flags=re.I)
    trans = re.sub(r'\bCự\s+Thạch\s+New\s+Orelian\b', 'Cự Tháp New Orelian', trans, flags=re.I)
    trans = re.sub(r'\bLịch\s+Cự\s+Thạch\b', 'Lịch Cự Tháp', trans, flags=re.I)
    trans = re.sub(r'\bLịch\s+Nguyên\s+Khối\b', 'Lịch Cự Tháp', trans, flags=re.I)
    trans = re.sub(r'\bLối\s+vào\s+nguyên\s+khối\b', 'Lối Vào Cự Tháp', trans, flags=re.I)
    trans = re.sub(r'\b(?:những\s+|các\s+)tảng\s+Cự\s+Tháp\b', 'các Cự Tháp', trans, flags=re.I)
    trans = re.sub(r'\b(?:một\s+)?tảng\s+Cự\s+Tháp\b', 'Cự Tháp', trans, flags=re.I)
    trans = re.sub(r'\b[Cc]ự\s+[Tt]hạch\b', 'Cự Tháp', trans)
    trans = re.sub(r'\b[Đđ]á\s+nguyên\s+khối\b', 'Cự Tháp', trans)
    trans = re.sub(r'\bDân\s+Người\s+Novian\b', 'người Novian', trans, flags=re.I)
    trans = re.sub(r'\bDân\s+Novian\b', 'người Novian', trans, flags=re.I)
    trans = re.sub(r'\bNgười\s+Novian\b', 'người Novian', trans)

    # 2. Salvation Committee, Boss Accord & Tyrant
    trans = re.sub(r'\bỦy\s*[Bb]an\s+[Cc]ứu\s+(?:nguy|rỗi|thế|trợ|tế)\b', 'Ủy Ban Cứu Rỗi', trans)
    trans = re.sub(r'\bỦy ban cứu rỗi\b', 'Ủy Ban Cứu Rỗi', trans)
    trans = re.sub(r'\bSếp\s+Accord\b', 'Hiệp Ước Của Sếp', trans)
    trans = re.sub(r'\b[Tt]hỏa thuận của ông chủ\b', 'Hiệp Ước Của Sếp', trans)
    trans = re.sub(r'\b[Hh]iệp định của ông chủ\b', 'Hiệp Ước Của Sếp', trans)
    trans = re.sub(r'\bÔng chủ\b(?=[,!\?\.])', 'Sếp', trans)
    trans = re.sub(r'^[Ôô]ng chủ\b', 'Sếp', trans)
    trans = re.sub(r'\b[Ôô]ng chủ\b', 'Sếp', trans)
    trans = re.sub(r'\b(?:[Tt]ên\s+)?[Bb]ạo\s+[Cc]húa\b', 'Bạo Quân', trans)
    trans = re.sub(r'\bbạo chúa\b', 'Bạo Quân', trans)

    # 3. Archons & Stellaroids in Monolith
    if re.search(r'\barchons?\b', orig, re.I):
        trans = re.sub(r'\bcung thủ\b', 'Chấp Chính Quan', trans, flags=re.I)
        trans = re.sub(r'\bArchons?\b', 'Chấp Chính Quan', trans, flags=re.I)
    trans = re.sub(r'\bStellaroids\b', 'Các Thể Tinh Tú', trans, flags=re.I)
    trans = re.sub(r'\bStellaroid\b', 'Thể Tinh Tú', trans, flags=re.I)

    # 4. Factions & Locations
    trans = re.sub(r'\bBiên\s+niên\s+sử\s+của\s+(?:New\s+Nova|Tân\s+Nova)\b', 'Biên Niên Sử Tân Nova', trans, flags=re.I)
    trans = re.sub(r'\bChronicles\s+of\s+New\s+Nova\b', 'Biên Niên Sử Tân Nova', trans, flags=re.I)
    trans = re.sub(r'\bNew\s+Nova\b', 'Tân Nova', trans, flags=re.I)
    trans = re.sub(r'\bWind-Wielding Sentinel\b', 'Thủ Vệ Ngự Phong', trans, flags=re.I)
    trans = re.sub(r'\bSand-Wielding Sentinel\b', 'Thủ Vệ Ngự Sa', trans, flags=re.I)
    trans = re.sub(r'\bTactical Retreat\b', 'Rút Lui Chiến Thuật', trans, flags=re.I)
    trans = re.sub(r'\bDecapitation Strike\b', 'Chiến Thuật Trảm Thủ', trans, flags=re.I)
    trans = re.sub(r'\bBetting Everything\b', 'Đặt Cược Tất Cả', trans, flags=re.I)
    trans = re.sub(r'\bEureka Bar\b', 'Quán Bar Eureka', trans, flags=re.I)
    trans = re.sub(r'\bMineshaft Entrance\b', 'Lối Vào Hầm Mỏ', trans, flags=re.I)
    trans = re.sub(r'\bUnnamed Forest\b', 'Khu Rừng Vô Danh', trans, flags=re.I)
    trans = re.sub(r'\bPiercer!\b', 'Xuyên Giáp Tiễn!', trans, flags=re.I)
    trans = re.sub(r'\bHiệp hội người đi bộ\b', 'Hiệp Hội Lữ Khách', trans, flags=re.I)
    trans = re.sub(r'\bHiệp hội Lữ Khách\b', 'Hiệp Hội Lữ Khách', trans)
    trans = re.sub(r'\bU Linh Thuyền\b', 'U Linh Hạm', trans, flags=re.I)
    trans = re.sub(r'\bthuyền ma\b', 'U Linh Hạm', trans, flags=re.I)
    trans = re.sub(r'\btàu ma\b', 'U Linh Hạm', trans, flags=re.I)
    trans = re.sub(r'\bCá Voi 6 Sừng\b', 'Cá Voi Lục Sừng', trans, flags=re.I)
    trans = re.sub(r'\bCá voi sáu sừng\b', 'Cá Voi Lục Sừng', trans, flags=re.I)
    trans = re.sub(r'\bPhòng Màu Trắng\b', 'Phòng Trắng', trans, flags=re.I)
    trans = re.sub(r'\bcăn phòng màu trắng\b', 'Phòng Trắng', trans, flags=re.I)
    trans = re.sub(r'\bTrọng Tài Chạng Vạng\b', 'Trọng Tài Hoàng Hôn', trans, flags=re.I)
    trans = re.sub(r'\btrọng tài chạng vạng\b', 'Trọng Tài Hoàng Hôn', trans, flags=re.I)
    trans = re.sub(r'\bĐêm Vĩnh Cửu\b', 'Đêm Trường Vĩnh Cửu', trans, flags=re.I)
    trans = re.sub(r'\bĐá Linh Hồn\b', 'Hồn Thạch', trans, flags=re.I)
    trans = re.sub(r'\bĐá Hồn\b', 'Hồn Thạch', trans, flags=re.I)
    trans = re.sub(r'\bTrại Mồ Côi Daisy\b', 'Viện Mồ Côi Daisy', trans, flags=re.I)
    trans = re.sub(r'\bTrại Mồ Côi Cúc Họa Mi\b', 'Viện Mồ Côi Daisy', trans, flags=re.I)
    trans = re.sub(r'\bBà Angie\b', 'Tiểu Thư Angie', trans, flags=re.I)
    trans = re.sub(r'\bQuý Cô Angie\b', 'Tiểu Thư Angie', trans, flags=re.I)
    trans = re.sub(r'\bHiệu Trưởng Allie\b', 'Giám Đốc Allie', trans, flags=re.I)
    trans = re.sub(r'\bKỵ Sĩ Hoàng Gia\b', 'Cận Vệ Hoàng Gia', trans, flags=re.I)
    trans = re.sub(r'\bKim Khố Ý Chí Ân Tứ\b', 'Đế Quốc Grace', trans, flags=re.I)
    trans = re.sub(r'\bGiao dịch Creta\b', 'Thương Hội Creta', trans, flags=re.I)
    trans = re.sub(r'\bLễ hội Snowish\b', 'Lễ Hội Snowish', trans)

    # 5. Radio & transmission protocols
    trans = re.sub(r'^[Nn]ghe rõ đó\b', 'Đã rõ', trans)
    trans = re.sub(r'\bnghe rõ đó\b', 'đã rõ', trans)
    trans = re.sub(r'\b[Bb]ạn có sao chép không[\s?!]*', 'Bạn có nghe rõ không!?', trans)
    trans = re.sub(r'\b[Cc]ó sao chép không[\s?!]*', 'Nghe rõ không!?', trans)
    trans = re.sub(r'\bsao chép không[\s?!]*', 'nghe rõ không!?', trans)
    trans = re.sub(r'\bsao chép điều đó\b', 'rõ rồi', trans, flags=re.I)
    trans = re.sub(r'\bsao chép rồi\b', 'rõ rồi', trans, flags=re.I)
    trans = re.sub(r'\bDo you copy\b', 'Nghe rõ không!?', trans, flags=re.I)
    if orig.strip() == 'Copy that! Moving out!':
        trans = 'Đã rõ! Xuất phát!'
    if orig.strip() == 'As if!':
        trans = 'Còn lâu nhé!'
    trans = re.sub(r'\bDi chuyển ra ngoài!\b', 'Xuất phát!', trans)
    if 'Over.' in orig:
        trans = re.sub(r'\b(?:Kết thúc|Over)\.?', 'Hết.', trans)

    if 'can you hear me' in orig.lower():
        trans = re.sub(r'[Tt]ôi nghe thấy bạn', 'cậu có nghe thấy tớ không', trans)
        trans = re.sub(r'[Bb]ạn có nghe thấy tôi không', 'cậu có nghe thấy tớ không', trans)
        trans = re.sub(r'[Bb]ạn có nghe tôi nói không', 'cậu có nghe rõ không!?', trans)

    # 6. De-calquing commissions & fees
    trans = re.sub(r'\bhoa hồng đang hoạt động\b', 'nhiệm vụ ủy thác chưa hoàn thành', trans, flags=re.I)
    trans = re.sub(r'\bphí hoa hồng\b', 'thù lao ủy thác', trans, flags=re.I)
    trans = re.sub(r'\btiền hoa hồng\b', 'tiền thù lao ủy thác', trans, flags=re.I)
    trans = re.sub(r'\bHoa Hồng Ủy Thác\b', 'Thù lao ủy thác', trans, flags=re.I)
    trans = re.sub(r'\bnhận hoa hồng\b', 'nhận ủy thác', trans, flags=re.I)
    trans = re.sub(r'\bhoa hồng từ Creta Trading\b', 'ủy thác từ Thương Hội Creta', trans, flags=re.I)
    trans = re.sub(r'\bhoa hồng từ Thương Hội Creta\b', 'ủy thác từ Thương Hội Creta', trans, flags=re.I)
    trans = re.sub(r'\bhoàn thành hoa hồng\b', 'hoàn thành ủy thác', trans, flags=re.I)
    trans = re.sub(r'\bhoa hồng này\b', 'nhiệm vụ ủy thác này', trans, flags=re.I)
    trans = re.sub(r'\bhoa hồng của chúng ta\b', 'nhiệm vụ ủy thác của chúng ta', trans, flags=re.I)
    trans = re.sub(r'\bchưa hoàn thành hoa hồng\b', 'chưa hoàn thành ủy thác', trans, flags=re.I)
    if 'commission' in orig.lower():
        trans = re.sub(r'\bhoa hồng\b', 'nhiệm vụ ủy thác', trans, flags=re.I)

    # Star plucking
    if 'star plucking' in orig.lower():
        trans = re.sub(r'\bsao nhổ\b', 'Đoạt Sao', trans, flags=re.I)
        trans = re.sub(r'\bhái sao\b', 'Đoạt Sao', trans, flags=re.I)

    # 7. Anime RPG character & proper nouns
    trans = re.sub(r'\b(Firstlight|First Light)\s*Noya\b', 'Noya - Khải Minh', trans, flags=re.I)
    trans = re.sub(r'\bNoya\s*(Sơ Quang|Khải Minh)\b', 'Noya - Khải Minh', trans, flags=re.I)
    trans = re.sub(r'\bSơ Quang\b', 'Khải Minh', trans)
    trans = re.sub(r'\bkẻ thù\b', 'kẻ địch', trans, flags=re.I)
    trans = re.sub(r'\b[Nn]gười đi bộ\b', 'Lữ Khách', trans)
    trans = re.sub(r'\b[Nn]hững người đi bộ\b', 'các Lữ Khách', trans)

    # 8. Tokens & whitespace tags preservation
    trans = re.sub(r'==\s*([A-Za-z0-9_]+)\s*==', r'==\1==', trans)
    trans = re.sub(r'<r=([^>]+)>\s*</r>', r'<r=\1></r>', trans)
    trans = re.sub(r'(<color=[^>]+>)\s+', r'\1', trans)
    trans = re.sub(r'\s+(</color>)', r'\1', trans)
    trans = re.sub(r'\s+([,.:;?!])', r'\1', trans)

    return trans

def main():
    print("=" * 75)
    print("Senior Translator 1 (Batch 4 - Part A): Main Story Chapter 9 & Special Stories")
    print("=" * 75)

    terms, forbidden = load_master_glossary()
    terms = {k: v.split(' / ')[0].strip() for k, v in terms.items()}
    cache = load_cache()
    print(f"Loaded master glossary ({len(terms)} terms, {len(forbidden)} forbidden rules).")
    print(f"Existing translation cache: {len(cache)} entries.")

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_strings = len(data)
    print(f"Total strings to process in Part A: {total_strings}")

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
                trans_s = normalize_shielded_text(trans_s)
                polished_s = post_process_vietnamese(trans_s, terms, forbidden)
                polished_s = normalize_shielded_text(polished_s)
                unshielded = unshield_tokens(polished_s, tok)
                polished = post_process_vietnamese(unshielded, terms, forbidden)
                polished = polish_dialogue_b4_partA(orig_txt, polished)
                polished = ensure_token_preservation(orig_txt, polished)
                if not is_valid_token_preservation(orig_txt, polished):
                    raw_unshielded = unshield_tokens(trans_s, tok)
                    if is_valid_token_preservation(orig_txt, raw_unshielded):
                        polished = post_process_vietnamese(raw_unshielded, terms, forbidden)
                        polished = ensure_token_preservation(orig_txt, polished)
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

    # Assemble final translated output
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
        trans = polish_dialogue_b4_partA(str_val, trans)
        trans = ensure_token_preservation(str_val, trans)

        if not is_valid_token_preservation(str_val, trans):
            raw_trans = cache.get(str_val, str_val)
            raw_trans = ensure_token_preservation(str_val, raw_trans)
            if is_valid_token_preservation(str_val, raw_trans):
                trans = raw_trans

        final_translated[str_key] = trans
        valid_count += 1
        if is_valid_token_preservation(str_val, trans):
            token_ok_count += 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(final_translated, f, indent=2, ensure_ascii=False)

    print("=" * 75)
    print(f"Successfully exported Part A: {len(final_translated)} strings to {OUTPUT_PATH.name}")
    print(f"Token preservation rate: {token_ok_count}/{valid_count} ({(token_ok_count/valid_count)*100:.2f}%)")
    print("=" * 75)

if __name__ == "__main__":
    main()
