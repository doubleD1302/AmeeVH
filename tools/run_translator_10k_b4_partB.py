#!/usr/bin/env python3
"""
Senior Translator 2 (Batch 4 - Part B): Special Stories (STsp_02_02 to STsp_13_*)
Total dialogue strings: 3,333 items.
Applies Master Glossary from config/master_glossary.json.
Enforces:
- Anime RPG voice: humorous side stories, character banter, mystery investigations, warm daily interactions.
- Radio / communication: "Do you copy?" -> "Bạn có nghe rõ không!?" / "Nghe rõ không!?".
- Characters & Honorifics: "Tiểu Thư Angie", "Phu Nhân Firenze", "Dì Allie", "Cô Caramel", "Cô Laru".
- De-calquing: "commission" -> "nhiệm vụ ủy thác / thù lao ủy thác", "toast" -> "tiêu đời", "bánh mì nướng" eliminated.
- Standardized character names: Chixia, Amber, Willow, Jinglin, Noya, Donna.
- 100% token preservation: ==W==, ==PLAYER_NAME==, <color=...>, <size=...>, ==RT==, ==SEX==, etc.
Saves output to: work/batches/batch_10k_b4_partB_translated.json
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

INPUT_PATH = ROOT / "work" / "batches" / "batch_10k_b4_partB.json"
OUTPUT_PATH = ROOT / "work" / "batches" / "batch_10k_b4_partB_translated.json"

LABEL_AND_TITLE_FIXES = {
    # Acts
    "Act One": "Hồi 1",
    "Act Two": "Hồi 2",
    "Act Three": "Hồi 3",
    "Act Four": "Hồi 4",
    # Story Titles
    "Your Name, Unknown to My Heart (Part IV)": "Tên Cậu, Trái Tim Tôi Chưa Từng Biết (Phần IV)",
    "A Thousand Blossoms by Night (Part I)": "Đêm Vạn Hoa (Phần I)",
    "A Thousand Blossoms by Night (Part III)": "Đêm Vạn Hoa (Phần III)",
    "Matcha Dreaming (Part I)": "Giấc Mộng Matcha (Phần I)",
    "The Old Timer and the Newcomer (Part III)": "Tiền Bối và Tân Binh (Phần III)",
    "Soul of a Guard, Heart of a Knight (Part I)": "Hồn Cận Vệ, Tâm Kỵ Sĩ (Phần I)",
    "Soul of a Guard, Heart of a Knight (Part III)": "Hồn Cận Vệ, Tâm Kỵ Sĩ (Phần III)",
    "Wish in the Snow (Part I)": "Điều Ước Dưới Tuyết (Phần I)",
    "Wish in the Snow (Part II)": "Điều Ước Dưới Tuyết (Phần II)",
    "Wish in the Snow (Part III)": "Điều Ước Dưới Tuyết (Phần III)",
    "Captive of Truth (Part III)": "Tù Nhân Của Chân Lý (Phần III)",
    "One-Day Partner (Part I)": "Cộng Sự Một Ngày (Phần I)",
    "One-Day Partner (Part II)": "Cộng Sự Một Ngày (Phần II)",
    "One-Day Partner (Part III)": "Cộng Sự Một Ngày (Phần III)",
    "A Day of Harvest (Part I)": "Một Ngày Thu Hoạch (Phần I)",
    "A Day of Harvest (Part III)": "Một Ngày Thu Hoạch (Phần III)",
    "Slipping into Sunlight (Part I)": "Chạm Vào Ánh Nắng (Phần I)",
    "Slipping into Sunlight (Part II)": "Chạm Vào Ánh Nắng (Phần II)",
    "You, In My Eyes (Part Ⅰ)": "Hình Bóng Cậu Trong Mắt Tôi (Phần Ⅰ)",
    "You, In My Eyes (Part Ⅳ)": "Hình Bóng Cậu Trong Mắt Tôi (Phần Ⅳ)",
    "The Missy and the Saucy Maid (Part I)": "Tiểu Thư và Hầu Gái Tinh Quái (Phần I)",
    "The Missy and the Saucy Maid (Part II)": "Tiểu Thư và Hầu Gái Tinh Quái (Phần II)",
    "The Missy and the Saucy Maid (Part III)": "Tiểu Thư và Hầu Gái Tinh Quái (Phần III)",
    # Speakers & Character Labels
    "The Boss": "Sếp",
    "Suspicious Sidekick": "Tên Đàn Em Khả Nghi",
    "Gold District Visitor": "Vị Khách Khu Hoàng Kim",
    "Cocky Mercenary": "Lính Đánh Thuê Ngạo Mạn",
    "Stern Captain": "Đội Trưởng Nghiêm Nghị",
    "Hungry Mercenary": "Lính Đánh Thuê Đói Bụng",
    "Director Knight": "Kỵ Sĩ Đạo Diễn",
    "Imperial Guard Knight": "Kỵ Sĩ Cận Vệ Hoàng Gia",
    "Mysterious Witch": "Phù Thủy Bí Ẩn",
    "Dusk Arbiter Prison #7": "Nhà Tù Phán Quan Hoàng Hôn Số 7",
    "Stall Vendor": "Chủ Quầy Hàng",
    "Suspicious Trekker": "Lữ Khách Khả Nghi",
    "Travelling Trekker": "Lữ Khách Viễn Du",
    "Excited Child": "Đứa Trẻ Hào Hứng",
    "Well-Behaved Child": "Đứa Trẻ Ngoan Ngoãn",
    "Naughty Child": "Đứa Trẻ Nghịch Ngợm",
    "Concerned Voice": "Giọng Nói Lo Lắng",
    "Flavor Dread": "Vị Nỗi Khiếp Sợ"
}

HANDCRAFTED_FIXES = {
    # Toast / Cheers
    "STsp_10_02.90": "Không biết liệu Quán Ăn Của Jing và Liên Hợp Thu Hoạch có cơ hội hợp lực cùng nhau hay không...==W== Nhưng tôi xin nâng ly chúc mừng cho một tương lai nơi mọi người ở Philae đều được ăn no mặc ấm...==W== Cạn ly!",
    # Contract Copy
    "STsp_05_01.34": "À, phải rồi... Hôm nay tôi đến đây thực ra là để trả lại bản hợp đồng này. Sau chuyến câu cá hôm qua, tôi lỡ cầm nhầm bản sao của bạn theo. Thật lòng xin lỗi nhé.",
    # Radio / Roger
    "STsp_11_03.7": "Rõ! Chiến dịch: Bắt giữ Donna chính thức bắt đầu!",
    # Commissions
    "STsp_11_03.76": "Không đời nào! Hôm nay cậu phải nghỉ ngơi, cấm cãi. Bọn tớ sẽ lo liệu hết các nhiệm vụ ủy thác và việc làm thêm của cậu!",
    "STsp_12_01.16": "Ủy thác là ủy thác. Chúng tôi phải có trách nhiệm giải trình với thân chủ.",
    "STsp_13_01.99": "Cậu đã nghĩ ra nhiệm vụ ủy thác nào chưa?",
    "STsp_09_01.69": "Vậy... Bây giờ tôi có thể tham gia vào phi vụ ăn chia hoa hồng béo bở đó được chưa?",
    "STsp_09_02.20": "Kẻ cầm đầu không chỉ bán Cổ Vật giả. Ả ta còn bắt đám tay chân lôi kéo người khác vào đường dây, hứa hẹn trả tiền hoa hồng và tiền thưởng nếu dụ thêm được nhiều người.",
    # Characters & Banter
    "STsp_14_01.40": "Cô có sao không, Cô Caramel?",
    "STsp_10_01.44": "Tôi thành thật xin lỗi, Phu Nhân Firenze. Tôi...",
    "STsp_05_02.16": "Vậy Cô Laru cứ ở lại đây nhé. Tôi xin phép về trước, ở Cửa Hàng Linh Hồn còn nhiều việc phải làm lắm.",
    "STsp_02_04.54": "Noya! Iris! Amber!",
    "STsp_12_03.36": "Noya! Cẩn thận sau lưng kìa!",
    "STsp_07_03.83": "Donna?! Teresa?!",
    "STsp_11_01.22": "Donna?! Cậu lại đi sớm thế này nữa à?",
    "STsp_03_03.98": "<size=48>Shimiao! Jinglin! Cứu tớ vớiiiiiii!==W==</size>",
    "STsp_12_02.6": "Còn một con! Amber, nó lao tới cậu kìa!",
    "STsp_12_02.99": "Amber. Tay súng thiện xạ. Một đứa trẻ ngoan. Điểm dị giáo: Không.",
    "STsp_11_03.3": "Hôm nay, Donna này vẫn là cô nàng giao hàng dễ thương nhất, thông minh nhất, chăm chỉ nhất của Chuyển Phát Hỏa Tốc Post Haste! Cố lên tôi ơi!"
}

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
    return True

def polish_dialogue_b4_partB(str_key: str, orig: str, trans: str) -> str:
    """Enforces Anime RPG voice, natural comedic timing, warmth, and correct lore terms for Batch 4 Part B."""
    if str_key in HANDCRAFTED_FIXES:
        res = HANDCRAFTED_FIXES[str_key]
        if is_valid_token_preservation(orig, res):
            return res

    orig_clean = orig.strip()
    if orig_clean in LABEL_AND_TITLE_FIXES:
        return LABEL_AND_TITLE_FIXES[orig_clean]

    has_tokens = bool(TOKEN_REGEX.search(trans))
    if has_tokens:
        text, tok_list = shield_tokens(trans)
    else:
        text = trans
        tok_list = []

    # 1. Monolith & World Lore
    text = re.sub(r'\bPhilae\s+Cự\s+Thạch\b', 'Cự Tháp Philae', text, flags=re.I)
    text = re.sub(r'\bNew\s+Orelian\s+Cự\s+Thạch\b', 'Cự Tháp New Orelian', text, flags=re.I)
    text = re.sub(r'\bCự\s+Thạch\s+Philae\b', 'Cự Tháp Philae', text, flags=re.I)
    text = re.sub(r'\bCự\s+Thạch\s+New\s+Orelian\b', 'Cự Tháp New Orelian', text, flags=re.I)
    text = re.sub(r'\bLịch\s+Cự\s+Thạch\b', 'Lịch Cự Tháp', text, flags=re.I)
    text = re.sub(r'\bLịch\s+Nguyên\s+Khối\b', 'Lịch Cự Tháp', text, flags=re.I)
    text = re.sub(r'\bLối\s+vào\s+nguyên\s+khối\b', 'Lối Vào Cự Tháp', text, flags=re.I)
    text = re.sub(r'\bThành\s+phố\s+(?:vạn\s+)?(?:khối\s+đá\s+nguyên\s+khối|Cự\s+Thạch)\b', 'Thành Phố Vạn Tháp', text, flags=re.I)
    text = re.sub(r'\bCự\s+Thạch\b', 'Cự Tháp', text)
    text = re.sub(r'\bĐá\s+nguyên\s+khối\b', 'Cự Tháp', text)
    text = re.sub(r'\bđá\s+nguyên\s+khối\b', 'Cự Tháp', text)
    text = re.sub(r'\bnguyên\s+khối\b', 'Cự Tháp', text)
    text = re.sub(r'\bStellaroids?\b', 'Thể Tinh Tú', text, flags=re.I)
    text = re.sub(r'\b[Nn]gười đi bộ\b', 'Lữ Khách', text)
    text = re.sub(r'\b[Nn]hững người đi bộ\b', 'các Lữ Khách', text)
    text = re.sub(r'\b[Nn]gười du hành\b', 'Lữ Khách', text)
    text = re.sub(r'\b[Nn]gười đi phượt\b', 'Lữ Khách', text)
    text = re.sub(r'\bSpace Walker\b', 'Kẻ Dạo Bước Không Gian', text, flags=re.I)

    # 2. Characters & Honorifics
    text = re.sub(r'\b(Firstlight|First Light)\s*Noya\b', 'Noya - Khải Minh', text, flags=re.I)
    text = re.sub(r'\bNoya\s*(Sơ Quang|Khải Minh)\b', 'Noya - Khải Minh', text, flags=re.I)
    text = re.sub(r'\b(Sơ Quang|Khải Minh)\s*Noya\b', 'Noya - Khải Minh', text, flags=re.I)
    text = re.sub(r'\bSơ Quang\b', 'Khải Minh', text)
    text = re.sub(r'\b(?:Lady|Miss)\s+Angie\b', 'Tiểu Thư Angie', text, flags=re.I)
    text = re.sub(r'\b(?:Quý\s+bà|Quý\s+cô|Bà|Cô|bà|cô)\s+Angie\b', 'Tiểu Thư Angie', text)
    text = re.sub(r'\bLady\s+Firenze\b', 'Phu Nhân Firenze', text, flags=re.I)
    text = re.sub(r'\b(?:Quý\s+bà|Quý\s+cô|Bà|bà)\s+Firenze\b', 'Phu Nhân Firenze', text)
    text = re.sub(r'\bLady\s+Darcia\b', 'Phu Nhân Darcia', text, flags=re.I)
    text = re.sub(r'\b(?:Quý\s+bà|Quý\s+cô|Bà|bà)\s+Darcia\b', 'Phu Nhân Darcia', text)
    text = re.sub(r'\bAunt\s+Allie\b', 'Dì Allie', text, flags=re.I)
    text = re.sub(r'\b(?:Bác|Cô|bác|cô)\s+Allie\b', 'Dì Allie', text)
    text = re.sub(r'\bDirector\s+Allie\b', 'Giám Đốc Allie', text, flags=re.I)
    text = re.sub(r'\bMiss\s+Caramel\b', 'Cô Caramel', text, flags=re.I)
    text = re.sub(r'\b(?:Quý\s+cô|Nàng|cô)\s+Caramel\b', 'Cô Caramel', text)
    text = re.sub(r'\bMiss\s+Laru\b', 'Cô Laru', text, flags=re.I)
    text = re.sub(r'\b(?:Quý\s+cô|Nàng|cô)\s+Laru\b', 'Cô Laru', text)
    text = re.sub(r'\b[Xx]ích\s*[Hh]ạ\b', 'Chixia', text)
    text = re.sub(r'\b[Xx]íchxia\b', 'Chixia', text)
    text = re.sub(r'\b[Tt]rì\s+[Hh]ạ\b', 'Chixia', text)
    text = re.sub(r'\b[Cc]ảnh\s+[Ll]âm\b', 'Jinglin', text)
    text = re.sub(r'\b[Hh]ổ\s+[Pp]hách\b', 'Amber', text)
    text = re.sub(r'\b[Cc]ô\s+Liễu\b', 'Cô Willow', text)
    text = re.sub(r'\bLiễu\b', 'Willow', text)
    text = re.sub(r'\bSoul\s+Cửa\s+Hàng\b', 'Cửa Hàng Linh Hồn', text, flags=re.I)
    text = re.sub(r'\bArtifact\b', 'Cổ Vật', text)
    text = re.sub(r'\bhiện vật\b', 'Cổ Vật', text)

    # 3. Factions & Organizations
    text = re.sub(r'\bBoss Accord\b', 'Hiệp Ước Của Sếp', text, flags=re.I)
    text = re.sub(r'\bNew Star Guild\b', 'Lữ Đoàn Tân Tinh', text, flags=re.I)
    text = re.sub(r'\bHội Ngôi Sao Mới\b', 'Lữ Đoàn Tân Tinh', text, flags=re.I)
    text = re.sub(r'\bBang Hội Ngôi Sao Mới\b', 'Lữ Đoàn Tân Tinh', text, flags=re.I)
    text = re.sub(r'\bImperial Guards?\b', 'Cận Vệ Hoàng Gia', text, flags=re.I)
    text = re.sub(r'\bVệ binh Hoàng gia\b', 'Cận Vệ Hoàng Gia', text, flags=re.I)
    text = re.sub(r'\bĐội cận vệ Hoàng gia\b', 'Cận Vệ Hoàng Gia', text, flags=re.I)
    text = re.sub(r'\bTrekker Association\b', 'Hiệp Hội Lữ Khách', text, flags=re.I)
    text = re.sub(r'\bGoodwind Homecare\b', 'Chăm Sóc Gia Đình Goodwind', text, flags=re.I)
    text = re.sub(r'(?:Chuyển Phát Hỏa Tốc\s*)+Post Haste', 'Chuyển Phát Hỏa Tốc Post Haste', text)
    text = re.sub(r'\bUnited Harvest\b', 'Liên Hợp Thu Hoạch', text, flags=re.I)
    text = re.sub(r'\bSoul Shop\b', 'Cửa Hàng Linh Hồn', text, flags=re.I)
    text = re.sub(r'\bSwimming Fish Festival\b', 'Hội Hoa Đăng Du Ngư', text, flags=re.I)
    text = re.sub(r'\bLễ Hội Cá Bơi\b', 'Hội Hoa Đăng Du Ngư', text, flags=re.I)
    text = re.sub(r'\bLễ hội [Tt]uyết\b', 'Lễ Hội Snowish', text)
    text = re.sub(r'\bLễ Hội [Tt]uyết\b', 'Lễ Hội Snowish', text)

    # 4. Radio & Communication
    text = re.sub(r'^[Nn]ghe rõ đó\b', 'Đã rõ', text)
    text = re.sub(r'\bnghe rõ đó\b', 'đã rõ', text)
    text = re.sub(r'\bDo you copy\?\b', 'Bạn có nghe rõ không!?', text, flags=re.I)
    text = re.sub(r'\bDo you copy\b', 'Nghe rõ không!?', text, flags=re.I)
    text = re.sub(r'\b[Bb]ạn có sao chép không[\s?!]*', 'Bạn có nghe rõ không!?', text)
    text = re.sub(r'\b[Cc]ó sao chép không[\s?!]*', 'Nghe rõ không!?', text)
    text = re.sub(r'\bsao chép không[\s?!]*', 'nghe rõ không!?', text)
    text = re.sub(r'\bCopy that\.?\b', 'Rõ rồi.', text, flags=re.I)

    # 5. De-calquing Commissions & Expressions
    text = re.sub(r'\bThree Grand Commissions\b', 'Ba Đại Nhiệm Vụ Ủy Thác', text, flags=re.I)
    text = re.sub(r'\bBa Đại Hoa Hồng\b', 'Ba Đại Nhiệm Vụ Ủy Thác', text, flags=re.I)
    text = re.sub(r'\bhoa hồng đang hoạt động\b', 'nhiệm vụ ủy thác chưa hoàn thành', text)
    text = re.sub(r'\bphí hoa hồng\b', 'thù lao ủy thác', text)
    text = re.sub(r'\btiền hoa hồng\b', 'tiền thù lao ủy thác', text)
    text = re.sub(r'\bnhận hoa hồng\b', 'nhận ủy thác', text)
    text = re.sub(r'\bhoàn thành hoa hồng\b', 'hoàn thành ủy thác', text)
    text = re.sub(r'\bkhoản hoa hồng\b', 'nhiệm vụ ủy thác', text)
    text = re.sub(r'\bhoa hồng quái vật\b', 'ủy thác săn quái', text)
    text = re.sub(r'\bngập chìm\b', 'bận tối mắt tối mũi', text)
    text = re.sub(r'\bbánh mì nướng\b', 'tiêu đời', text)

    # 6. Anime comedic banter
    text = re.sub(r'\b(Haha\.\.\.|Hahaha\.\.\.)', 'Haha...', text)
    text = re.sub(r'\bUh\.\.\.\b', 'Ừm...', text)
    text = re.sub(r'\bHaaah—\b', 'Hầy—', text)
    text = re.sub(r'\bGo me!\b', 'Cố lên tôi ơi!', text)

    if has_tokens:
        text = unshield_tokens(text, tok_list)

    # 7. Formatting & Token preservation cleanup
    text = re.sub(r'==\s*([A-Za-z0-9_]+)\s*==', r'==\1==', text)
    text = re.sub(r'<r=([^>]+)>\s*</r>', r'<r=\1></r>', text)
    text = re.sub(r'(<color=[^>]+>)\s+', r'\1', text)
    text = re.sub(r'\s+(</color>)', r'\1', text)
    text = re.sub(r'\s+([,.:;?!])', r'\1', text)

    return text.strip(" \t\r\n")

def main():
    print("=" * 75)
    print("Senior Translator 2 (Batch 4 - Part B): Special Stories (STsp)")
    print("=" * 75)

    terms, forbidden = load_master_glossary()
    cache = load_cache()
    print(f"Loaded master glossary ({len(terms)} terms, {len(forbidden)} forbidden rules).")
    print(f"Existing translation cache: {len(cache)} entries.")

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_strings = len(data)
    print(f"Total strings to process in Part B: {total_strings}")

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
        if str_key in HANDCRAFTED_FIXES:
            cache[str_val] = HANDCRAFTED_FIXES[str_key]
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
                polished_s = post_process_vietnamese(trans_s, terms, forbidden)
                unshielded = unshield_tokens(polished_s, tok)
                polished = post_process_vietnamese(unshielded, terms, forbidden)
                polished = polish_dialogue_b4_partB("", orig_txt, polished)
                if not is_valid_token_preservation(orig_txt, polished):
                    raw_unshielded = unshield_tokens(trans_s, tok)
                    if is_valid_token_preservation(orig_txt, raw_unshielded):
                        polished = post_process_vietnamese(raw_unshielded, terms, forbidden)
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

        raw_trans = cache.get(str_val, str_val)
        trans = post_process_vietnamese(raw_trans, terms, forbidden)
        trans = polish_dialogue_b4_partB(str_key, str_val, trans)

        if not is_valid_token_preservation(str_val, trans):
            if is_valid_token_preservation(str_val, raw_trans):
                trans = raw_trans
            else:
                # Shield and force restore tokens
                s_orig, tok_orig = shield_tokens(str_val)
                s_trans, tok_trans = shield_tokens(trans)
                if len(tok_orig) == len(tok_trans):
                    trans = unshield_tokens(s_trans, tok_orig)

        final_translated[str_key] = trans
        valid_count += 1
        if is_valid_token_preservation(str_val, trans):
            token_ok_count += 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(final_translated, f, indent=2, ensure_ascii=False)

    print("=" * 75)
    print(f"Successfully exported Part B: {len(final_translated)} strings to {OUTPUT_PATH.name}")
    print(f"Token preservation rate: {token_ok_count}/{valid_count} ({(token_ok_count/valid_count)*100:.2f}%)")
    print("=" * 75)

if __name__ == "__main__":
    main()
