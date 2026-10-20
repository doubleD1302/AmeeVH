#!/usr/bin/env python3
"""
Senior Translator C: Cốt Truyện Nhân Vật Lữ Khách CG_* (2,666 items)
Translates all character stories (CG_*) prioritizing:
- Noya (CG_112_*)
- Amber (CG_103_*)
- Iris (CG_107_*)
- Chitose (CG_111_*, CG_144_*)
- Tilia (CG_115_*)
- Firefly (CG_118_*)
- Coronis (CG_120_*)
- Teresa (CG_127_*)
- Fuyuka (CG_134_*)

Enforces:
- "Firstlight Noya" -> "Noya - Khải Minh" (Strictly no "Sơ Quang")
- Noya sword skills: Tấn Phong Thiểm, Thăng Long Trảm, Tàn Phong Trảm, Trì Phong Kích, Liệt Không Đoạn Phá Trảm, Đại Kiếm Khí...
- Anime RPG narrative voice: emotional, natural, poetic yet clean and unpretentious
- 100% Technical token preservation: ==W==, ==PLAYER_NAME==, <color=...>, <size=...>, etc.
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

INPUT_PATH = ROOT / "work" / "batches" / "batch_10k_partC_character_stories.json"
OUTPUT_PATH = ROOT / "work" / "batches" / "batch_10k_partC_translated.json"

SPECIAL_LUA_OPCODES_MAP = {
    '\x04\x07se_095\x14*Come on, snap out of it, ==PLAYER_NAME==?\x04\x04End\x01\x00\x00\x00\x01\x00\x00':
        '\x04\x07se_095\x14*Tỉnh lại đi nào, ==PLAYER_NAME==?\x04\x04End\x01\x00\x00\x00\x01\x00\x00',
    '\x04\x18Oh, he crashed into it.\x14+Wow... That sounds like it really hu':
        '\x04\x18Ồ, hắn đâm sầm vào rồi.\x14+Oa... Nghe đau điếng người luôn á.',
    '\x04\x10SetMainRoleTalk\x04\x04012\x04\x06close\x04\x02y\x04\tavg3_100\x04\x08SetTalk\x13\x02\x00\x00\x00\x00\x00\x00\x00\x04\x01\x14':
        '\x04\x10SetMainRoleTalk\x04\x04012\x04\x06close\x04\x02y\x04\tavg3_100\x04\x08SetTalk\x13\x02\x00\x00\x00\x00\x00\x00\x00\x04\x01\x14',
    "\x04\x07se_126\x04\x04016\x04\x11avg_emoji_symbol\x04&Smoke...?!==W== I can't see anything!\x04\x07se_275\x04\nCtrlStage\x04\txiaozhen\x04\x07se_096\x04\x04007\x04\x06Ouch!\x04\x14avg_emoji_resentful\x04\x08jushou2\x04\x1bWho stomped me on my head?\x04\x07se_095\x04\x08chij":
        "\x04\x07se_126\x04\x04016\x04\x11avg_emoji_symbol\x04&Khói...?!==W== Tôi chẳng thấy gì cả!\x04\x07se_275\x04\nCtrlStage\x04\txiaozhen\x04\x07se_096\x04\x04007\x04\x06Ái da!\x04\x14avg_emoji_resentful\x04\x08jushou2\x04\x1bAi vừa giẫm lên đầu tôi thế?\x04\x07se_095\x04\x08chij",
    '\x14sLet me double-check the details of this commission for you...':
        '\x14sĐể tôi kiểm tra kỹ lại chi tiết ủy thác này cho bạn nhé...',
    "==W==I nagged at No<r=Seina></r>ya ==W==for eating in bed this morning,==W== and now I'm doing the same...==W== Boss,==W== please help me keep this a secret!":
        "==W==Tôi đã cằn nhằn No<r=Seina></r>ya ==W==vì ăn trên giường sáng nay,==W== thế mà giờ tôi lại làm y hệt...==W== Boss ơi,==W== xin hãy giúp tôi giữ bí mật chuyện này!",
    "\x14@That is a lot, Tyrant, what is this cheating that you speak of?\x03\x00\x00\x00\x00\x00\x00\x14@\x04\x07se_122\x14KI didn't hit you with Avalanche just now, so it doesn't count as cheating.\x04\x0favg_emoji_sigh\x04\x1c... Fine. Whate":
        "\x14@Nhiều thật đấy, Bạo Chúa, gian lận mà ngươi nói là sao?\x03\x00\x00\x00\x00\x00\x00\x14@\x04\x07se_122\x14KVừa nãy tôi đâu có dùng Tuyết Lở đánh ngươi, nên không tính là ăn gian nhé.\x04\x0favg_emoji_sigh\x04\x1c... Thôi được rồi. Sao cũng",
    "\x04\x14A good opportunity?\x04\x04003\x04\x10avg_emoji_happy\x04\x08daintou\x14FListening to other people's troubles is a common way to make friends.\x04\x04009\x04\x15avg_emoji_speechless\x03\x00\x00\x00\x00\x00\x00\x14@\x04\x0eA common way?\x04\x06close\x04\x0favg_emoj":
        "\x04\x14Một cơ hội tốt sao?\x04\x04003\x04\x10avg_emoji_happy\x04\x08daintou\x14FLắng nghe tâm sự của người khác là cách thông thường để kết bạn đấy.\x04\x04009\x04\x15avg_emoji_speechless\x03\x00\x00\x00\x00\x00\x00\x14@\x04\x0eMột cách thông thường?\x04\x06close\x04\x0favg_emoj",
    "\x14FMisha... You don't want to go to the Monolith with me anymore":
        "\x14FMisha... Cậu không muốn cùng tôi đến Cự Tháp nữa sao",
    "Gѿ\x148Mm. I'll score you on your head-patting skills, Tyrant.\x14;Even though Firefly's expression stayed as calm as ever...\x14bDuring that quiet, peaceful moment, I kept gently==":
        "Gѿ\x148Ừm. Ta sẽ chấm điểm kỹ năng xoa đầu của ngươi, Bạo Chúa.\x14;Dù vẻ mặt của Firefly vẫn điềm tĩnh như mọi khi...\x14bTrong khoảnh khắc yên bình, tĩnh lặng đó, tôi tiếp tục nhẹ nhàng==",
    '\x04\x14AvgStageEffect_eyes\x14/Hey...!==W== Wake up! ==PLAYER_NAME==?! ':
        '\x04\x14AvgStageEffect_eyes\x14/Này...!==W== Tỉnh lại đi! ==PLAYER_NAME==?!',
    "\x04\tSetStage\x13\x0c\x00\x00\x00\x00\x00\x00\x00\x141It's time for a double wall-kick here ... ":
        "\x04\tSetStage\x13\x0c\x00\x00\x00\x00\x00\x00\x00\x141Đã đến lúc thực hiện cú đạp tường kép ở đây... ",
    "\x04\x07se_365\x04\tlengzhan\x14_I gather my courage and meet Chitose's gaze":
        "\x04\x07se_365\x04\tlengzhan\x14_Tôi lấy hết can đảm đối diện ánh mắt của Chitose",
    '\x04\x08SetTalk\x04\x01\x13\x01\x00\x00\x00\x00\x00\x00\x00\x14SA damp breeze drifts through the outpost,':
        '\x04\x08SetTalk\x04\x01\x13\x01\x00\x00\x00\x00\x00\x00\x00\x14SLàn gió ẩm thổi qua tiền đồn,',
}

def is_code_identifier(s: str) -> bool:
    """Check if string is a Lua code identifier / asset key rather than narrative text."""
    s_clean = s.strip()
    return bool(re.match(r'^[A-Za-z0-9_]+$', s_clean))

def is_valid_translation(orig: str, trans: str) -> bool:
    if not trans or not trans.strip():
        return False
    if is_code_identifier(orig):
        return orig.strip() == trans.strip()
    if orig in SPECIAL_LUA_OPCODES_MAP:
        return True
    if orig == trans:
        words = re.findall(r'[a-zA-Z]{2,}', orig)
        has_vi = bool(re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]', trans))
        if len(words) >= 2 and not has_vi:
            return False
    return True

def polish_character_story_dialogue(text: str, terms: dict, forbidden: dict) -> str:
    """Specialized deep polish for Character Stories CG_*."""
    # 1. Base post-processing
    text = post_process_vietnamese(text, terms, forbidden)

    # 2. Strict Firstlight Noya standard
    text = re.sub(r'\b(Firstlight|First Light)\s*Noya\b', 'Noya - Khải Minh', text, flags=re.IGNORECASE)
    text = re.sub(r'\bNoya\s*(Sơ Quang|Khải Minh)\b', 'Noya - Khải Minh', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(Sơ Quang|Khải Minh)\s*Noya\b', 'Khải Minh Noya', text, flags=re.IGNORECASE)
    text = re.sub(r'\bNoya\s*[-–—]\s*Sơ Quang\b', 'Noya - Khải Minh', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSơ Quang\b', 'Khải Minh', text)

    # 3. Noya Swordplay & Skills
    skill_rules = [
        (r'\bSwift Wind Flash\b', 'Tấn Phong Thiểm'),
        (r'\b[Tt]ia chớp gió nhanh\b', 'Tấn Phong Thiểm'),
        (r'\b(Rising )?Dragon Slash\b', 'Thăng Long Trảm'),
        (r'\b[Cc]hém [Rr]ồng\b', 'Thăng Long Trảm'),
        (r'\b[Đđ]òn chém rồng\b', 'Thăng Long Trảm'),
        (r'\b(Ruin|Withered) Wind Slash\b', 'Tàn Phong Trảm'),
        (r'\b(Ruin|Withered) Wind\b', 'Tàn Phong'),
        (r'\b[Cc]ơn gió tàn khốc\b', 'Tàn Phong'),
        (r'\b[Gg]ió tàn phá\b', 'Tàn Phong'),
        (r'\bGalloping Wind Strike\b', 'Trì Phong Kích'),
        (r'\b[Đđ]òn đánh gió phi nước đại\b', 'Trì Phong Kích'),
        (r'\bSky Splitter Void Rupture Slash\b', 'Liệt Không Đoạn Phá Trảm'),
        (r'\bCross Great Sword Aura\b', 'Thập Tự Đại Kiếm Khí'),
        (r'\bGreat Sword Aura\b', 'Đại Kiếm Khí'),
        (r'\bMulti Sword Aura\b', 'Đa Trọng Kiếm Khí'),
        (r'\bMinor Sword Aura\b', 'Tiểu Kiếm Khí'),
        (r'\bSword Aura\b', 'Kiếm Khí'),
        (r'\bhào quang kiếm lớn\b', 'Đại Kiếm Khí'),
        (r'\bhào quang thanh kiếm lớn\b', 'Đại Kiếm Khí'),
        (r'\bhào quang (bằng |thanh )?kiếm\b', 'kiếm khí'),
        (r'\bluồng khí kiếm\b', 'luồng kiếm khí'),
        (r'\bNoname\b', 'Vô Danh'),
        (r'\bLucky Oasis\b', 'Ốc Đảo Lai Phúc'),
    ]
    for pat, rep in skill_rules:
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)

    # 4. Contextual Dialogue & Narrative nuance (Anime RPG voice)
    narrative_rules = [
        # Commission meaning 'ủy thác' (errand/contract/quest)
        (r'\bphí hoa hồng\b', 'thù lao ủy thác'),
        (r'\btiền hoa hồng\b', 'thù lao ủy thác'),
        (r'\bnhững khoản hoa hồng\b', 'các nhiệm vụ ủy thác'),
        (r'\bkhoản hoa hồng\b', 'nhiệm vụ ủy thác'),
        (r'\b(nhận|làm)\s+hoa hồng\b', r'\1 ủy thác'),
        (r'\bnhận một số hoa hồng\b', 'nhận vài ủy thác'),
        (r'\btrả hoa hồng\b', 'thực hiện ủy thác'),
        (r'\bHoa hồng của Lữ Khách\b', 'Ủy thác của Lữ Khách'),
        (r'\bhoa hồng của Lữ Khách\b', 'ủy thác của Lữ Khách'),
        (r'\bHoa hồng hôm nay\b', 'Ủy thác hôm nay'),
        (r'\bhoa hồng hôm nay\b', 'ủy thác hôm nay'),
        (r'\bHoa hồng này\b', 'Ủy thác này'),
        (r'\bhoa hồng này\b', 'ủy thác này'),
        (r'\bHoa hồng của cô ấy\b', 'Ủy thác của cô ấy'),
        (r'\bhoa hồng của cô ấy\b', 'ủy thác của cô ấy'),
        (r'\bkhông có hoa hồng nào được xếp hàng\b', 'không có ủy thác nào cần làm'),
        (r'\bkhông có ủy thác nào được xếp hàng\b', 'không có ủy thác nào cần làm'),
        (r'\bkhông có hoa hồng nào\b', 'không có ủy thác nào'),
        (r'\bnhận được hoa hồng\b', 'lo xong vụ ủy thác'),
        (r'\bvề khoản hoa hồng\b', 'về nhiệm vụ ủy thác'),
        (r'\bvề hoa hồng\b', 'về ủy thác'),
        (r'\btìm kiếm những khoản hoa hồng\b', 'tìm kiếm các ủy thác'),
        (r'\btìm kiếm hoa hồng\b', 'tìm kiếm ủy thác'),
        (r'\bMột khoản hoa hồng\b', 'Một ủy thác'),
        (r'\bmột khoản hoa hồng\b', 'một ủy thác'),

        # Noya & Loxy campervan dialogue
        (r'\ban toàn còn hơn xin lỗi\b', 'cẩn thận vẫn hơn'),
        (r'\bđưa bạn đi chơi Loxy\b', 'rủ cậu đi lượn một vòng trên Loxy'),
        (r'\bđi chơi Loxy\b', 'lượn một vòng trên Loxy'),
        (r'\bchơi một vòng trong Loxy\b', 'lượn một vòng trên Loxy'),
        (r'\bchơi một vòng với Loxy\b', 'lượn một vòng trên Loxy'),
        (r'\bchơi Loxy\b', 'lái xe Loxy'),
        (r'\btò mò giết chết con mèo\b', 'tò mò hại thân'),
        (r'\btò mò hại chết mèo\b', 'tò mò hại thân'),
        (r'\bthoát khỏi việc đánh Loxy\b', 'đụng vào Loxy mà yên ổn thoát được'),
        (r'\bBay ra khỏi chỗ ngồi của tôi\?!\b', 'Bị văng khỏi ghế á?!'),
        (r'\bchấp nhận anh ấy là một tài xế giao đậu phụ thực thụ\b', 'công nhận anh ấy là một tay lái giao đậu hũ chân chính'),

        # Chitose blade & oath dialogue
        (r'\bOneness between wielder and blade\b', 'đao nhân hợp nhất'),
        (r'\bOneness between blade and wielder\b', 'nhân kiếm hợp nhất'),
        (r'\bsự hợp nhất giữa lưỡi kiếm và người sử dụng\b', 'cảnh giới nhân kiếm hợp nhất'),
        (r'\bsự hợp nhất giữa người cầm kiếm và lưỡi kiếm\b', 'cảnh giới nhân kiếm hợp nhất'),
        (r'\bsự thống nhất giữa người sử dụng và lưỡi dao\b', 'cảnh giới đao nhân hợp nhất'),
        (r'\bsự thống nhất giữa lưỡi kiếm và người sử dụng\b', 'cảnh giới nhân kiếm hợp nhất'),
        (r'\blưỡi dao chưa được bọc\b', 'lưỡi đao chưa tra vào bao'),
        (r'\blưỡi dao chưa có vỏ\b', 'lưỡi đao chưa tra vào bao'),
        (r'\bbẻ gãy lưỡi dao của chính mình\b', 'bẻ gãy chính lưỡi kiếm của mình'),
        (r'\bbẻ gãy lưỡi kiếm của mình\b', 'bẻ gãy chính thanh kiếm của mình'),
        (r'\bbẻ gãy lưỡi dao\b', 'bẻ kiếm tạ tội'),
        (r'\bngười mang lưỡi dao\b', 'người nắm giữ lưỡi kiếm'),
        (r'\bngười cầm kiếm\b', 'người nắm giữ lưỡi kiếm'),
        (r'\bngười sử dụng thanh kiếm\b', 'người nắm giữ thanh kiếm'),
        (r'\bgió kiếm\b', 'kiếm phong'),

        # General tone & RPG terms
        (r'\bTrekkers?\b', 'Lữ Khách'),
        (r'\bngười đi bộ\b', 'Lữ Khách'),
        (r'\bnhững người đi bộ\b', 'các Lữ Khách'),
        (r'\bngười du hành\b', 'Lữ Khách'),
        (r'\bngười đi phượt\b', 'Lữ Khách'),
        (r'\bMonolith\b', 'Cự Tháp'),
        (r'\bcự tháp\b', 'Cự Tháp'),
        (r'\bWilds\b', 'Vùng Hoang Dã'),
        (r'\bvùng hoang dã\b', 'Vùng Hoang Dã'),
        (r'\bTyrant\b', 'Bạo Chúa'),
        (r'\bbạn tình\b', 'đồng đội'),
        (r'\bngười bạn đồng hành\b', 'bạn đồng hành'),
        (r'\bNo\s*(<r=[^>]+>.*?</r>)\s*ya\b', r'No\1ya'),
    ]
    for pat, rep in narrative_rules:
        text = re.sub(pat, rep, text)

    # 5. Clean consecutive tokens and spacing
    while re.search(r'(==[a-zA-Z0-9_]+==)\s+(==[a-zA-Z0-9_]+==)', text):
        text = re.sub(r'(==[a-zA-Z0-9_]+==)\s+(==[a-zA-Z0-9_]+==)', r'\1\2', text)

    # Clean punctuation spacing
    text = re.sub(r'\s+([,.:;?!])', r'\1', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)

    return text.strip(" \t\r\n")

def main():
    print("=" * 70)
    print("Senior Translator C: Truyện Nhân Vật Lữ Khách CG_* (2,666 items)")
    print("=" * 70)

    terms, forbidden = load_master_glossary()
    cache = load_cache()
    print(f"Loaded master glossary ({len(terms)} terms, {len(forbidden)} forbidden rules).")
    print(f"Existing translation cache: {len(cache)} entries.")

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_strings = len(data)
    print(f"Total strings to process in Part C: {total_strings}")

    # Register special opcode mappings into cache
    for orig, trans in SPECIAL_LUA_OPCODES_MAP.items():
        cache[orig] = trans

    exact_lookup = {k.lower(): v for k, v in terms.items()}
    exact_lookup.update(terms)

    to_translate = []
    code_ids_count = 0
    resolved_count = 0

    for str_key, str_val in data.items():
        if not str_val or not str_val.strip():
            continue
        
        # 1. Preserve Lua engine identifiers & fx assets verbatim
        if is_code_identifier(str_val):
            cache[str_val] = str_val
            code_ids_count += 1
            resolved_count += 1
            continue

        # 2. Check special lua opcodes map
        if str_val in SPECIAL_LUA_OPCODES_MAP:
            cache[str_val] = SPECIAL_LUA_OPCODES_MAP[str_val]
            resolved_count += 1
            continue

        # 3. Check Master Glossary exact match
        if str_val in exact_lookup:
            cache[str_val] = exact_lookup[str_val]
            resolved_count += 1
        elif str_val.lower() in exact_lookup:
            cache[str_val] = exact_lookup[str_val.lower()]
            resolved_count += 1
        # 4. Check existing valid cache
        elif str_val in cache and is_valid_translation(str_val, cache[str_val]):
            resolved_count += 1
            continue
        else:
            to_translate.append(str_val)

    unique_to_translate = list(dict.fromkeys(to_translate))
    print(f"Direct code identifiers preserved: {code_ids_count}")
    print(f"Special opcode sequences handled: {len(SPECIAL_LUA_OPCODES_MAP)}")
    print(f"Strings already resolved via cache/glossary: {resolved_count}")
    print(f"Strings to translate via API: {len(unique_to_translate)}")

    if unique_to_translate:
        batch_size = 25
        batches = [unique_to_translate[i : i + batch_size] for i in range(0, len(unique_to_translate), batch_size)]
        print(f"Translating {len(unique_to_translate)} strings across {len(batches)} batches...")

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
                polished = polish_character_story_dialogue(unshielded, terms, forbidden)
                if not is_valid_token_preservation(orig_txt, polished):
                    polished = polish_character_story_dialogue(orig_txt, terms, forbidden)
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
                if completed_batches % 10 == 0 or completed_batches == len(batches):
                    print(f"  Completed batch {completed_batches}/{len(batches)} ({completed_batches/len(batches)*100:.1f}%)")
                    save_cache(cache)

        save_cache(cache)
        print("API translation complete and updated into cache.")

    # Apply full polish across all 2,666 Part C items
    print("\nApplying comprehensive character story polish across all Part C entries...")
    translated_data = {}
    valid_count = 0
    token_mismatch_count = 0

    for str_key, str_val in data.items():
        if not str_val or not str_val.strip():
            translated_data[str_key] = str_val
            continue

        if is_code_identifier(str_val):
            translated_data[str_key] = str_val
            valid_count += 1
            continue

        if str_val in SPECIAL_LUA_OPCODES_MAP:
            translated_data[str_key] = SPECIAL_LUA_OPCODES_MAP[str_val]
            valid_count += 1
            continue

        trans = cache.get(str_val, str_val)
        trans = polish_character_story_dialogue(trans, terms, forbidden)

        if not is_valid_token_preservation(str_val, trans):
            token_mismatch_count += 1
            trans = polish_character_story_dialogue(str_val, terms, forbidden)

        translated_data[str_key] = trans
        valid_count += 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(translated_data, f, ensure_ascii=False, indent=2)

    save_cache(cache)

    print(f"\nPart C translation finished successfully!")
    print(f"- Total entries: {len(translated_data)} / {total_strings}")
    print(f"- Valid entries: {valid_count}")
    print(f"- Token mismatch fallbacks: {token_mismatch_count}")
    print(f"- Saved output file: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
