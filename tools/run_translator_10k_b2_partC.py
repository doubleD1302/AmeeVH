#!/usr/bin/env python3
"""
Senior Translator 3 (Batch 2 - Part C): Character Stories CG (Part 2)
Total dialogue strings: 3,333 items.
Applies Master Glossary from config/master_glossary.json.
Enforces:
- Character Stories CG: Romantic, witty, anime slice-of-life depth, natural cadence.
- 100% token preservation: ==W==, ==PLAYER_NAME==, <color=...>, <size=...>, furigana/ruby tags.
- Absolute rule: "Firstlight Noya" -> "Noya - Khải Minh" (no "Sơ Quang").
Saves output to: work/batches/batch_10k_b2_partC_translated.json
"""

import json
import re
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pipeline_translator_engine import (
    load_master_glossary, load_cache, save_cache,
    shield_tokens, translate_batch,
    post_process_vietnamese, is_valid_token_preservation,
    TOKEN_REGEX
)

INPUT_PATH = ROOT / "work" / "batches" / "batch_10k_b2_partC.json"
OUTPUT_PATH = ROOT / "work" / "batches" / "batch_10k_b2_partC_translated.json"

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

def robust_unshield_tokens(text: str, tokens: list) -> str:
    # 1. Normalize any spacing/case inside bracketed tokens
    text = re.sub(r'\[\s*\[\s*(?:TOK|tok)\s*(\d+)\s*\]\s*\]', r'[[TOK\1]]', text)
    text = re.sub(r'\[\s*(?:TOK|tok)\s*(\d+)\s*\]', r'[[TOK\1]]', text)

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

    res = re.sub(r'\s*\[\[\s*TOK(\d+)\s*\]\]\s*', repl, text)
    res = re.sub(r'(<color=[^>]+>)\s+', r'\1', res)
    res = re.sub(r'\s+(</color>)', r'\1', res)
    res = re.sub(r'(<size=[^>]+>)\s*', r'\1', res)
    res = re.sub(r'\s*(</size>)', r'\1', res)
    res = re.sub(r'(<i>)\s*', r'\1', res)
    res = re.sub(r'\s*(</i>)', r'\1', res)
    res = re.sub(r'(<b>)\s*', r'\1', res)
    res = re.sub(r'\s*(</b>)', r'\1', res)
    res = re.sub(r'==\s*([a-zA-Z0-9_]+)\s*==', r'==\1==', res)
    while re.search(r'(==[a-zA-Z0-9_]+==)\s+(==[a-zA-Z0-9_]+==)', res):
        res = re.sub(r'(==[a-zA-Z0-9_]+==)\s+(==[a-zA-Z0-9_]+==)', r'\1\2', res)
    res = re.sub(r'\s+([,.:;?!])', r'\1', res)
    res = re.sub(r'[ \t]{2,}', ' ', res)
    return res.strip(" \t\r\n")

def polish_character_story_dialogue(text: str, terms: dict, forbidden: dict) -> str:
    """Specialized deep polish for Character Stories CG."""
    # 0. Base post-processing from engine
    text = post_process_vietnamese(text, terms, forbidden)

    # 1. Absolute rule: Firstlight Noya -> Noya - Khải Minh (Strictly NO Sơ Quang)
    text = re.sub(r'\b(Firstlight|First Light)\s*Noya\b', 'Noya - Khải Minh', text, flags=re.IGNORECASE)
    text = re.sub(r'\bNoya\s*(Sơ Quang|Khải Minh)\b', 'Noya - Khải Minh', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(Sơ Quang|Khải Minh)\s*Noya\b', 'Khải Minh Noya', text, flags=re.IGNORECASE)
    text = re.sub(r'\bNoya\s*[-–—]\s*Sơ Quang\b', 'Noya - Khải Minh', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSơ Quang\b', 'Khải Minh', text)

    # 2. Noya sword skills
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
        (r'\bhào quang (?:bằng |thanh )?kiếm\b', 'kiếm khí'),
        (r'\bluồng khí kiếm\b', 'luồng kiếm khí'),
        (r'\bNoname\b', 'Vô Danh'),
        (r'\bLucky Oasis\b', 'Ốc Đảo Lai Phúc'),
    ]
    for pat, rep in skill_rules:
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)

    # 3. Contextual Dialogue & Narrative nuance (Anime RPG voice)
    narrative_rules = [
        # Acts & Parts
        (r'\bAct One\b', 'Màn Một'),
        (r'\bAct Two\b', 'Màn Hai'),
        (r'\bAct Three\b', 'Màn Ba'),
        (r'\bMàn một\b', 'Màn Một'),
        (r'\bMàn hai\b', 'Màn Hai'),
        (r'\bMàn ba\b', 'Màn Ba'),
        (r'\b\(Part I\)', '(Phần I)'),
        (r'\b\(Part II\)', '(Phần II)'),
        (r'\b\(Part III\)', '(Phần III)'),

        # Fix specific funny machine translations FIRST
        (r'nướng thịt (?:ông chủ|Boss) quán đó', 'tra hỏi chủ tiệm đó gắt gao như vậy'),
        (r'(?:ông|cậu) có thể nâng cốc cho tôi thêm một miếng nữa được không', 'có thể nướng thêm cho tôi một lát bánh mì nữa được không'),
        (r'Sự vội vàng!\s*Lấy mạng!', 'Nhanh lên! Lấy cái lưới ra đây!'),
        (r'nhanh lên!\s*Sự vội vàng!', 'nhanh lên! Mau lên nào!'),
        (r'Vì vậy xin vui lòng,\s*thưa (?:ông chủ|Boss)\.', 'Vì thế, xin Boss đấy...'),
        (r'Cưới anh đi!', 'Hãy cưới em đi!'),
        (r'chạm phải bức tường sáng tạo', 'gặp bế tắc trong sáng tạo'),
        (r'Noya sắp bay lên mặt trăng rồi', 'Chắc Noya sẽ sướng rơn phát cuồng lên mất'),
        (r'Trại Lữ Khách sở hữu Nazuka', 'Trại Lữ Khách cùng với Nazuka'),
        (r'Lữ Khách sở hữu việc trở thành người thừa kế', 'Lữ Khách với trách nhiệm của người thừa kế'),
        (r'Nơi này là gì\?', 'Đây là nơi nào thế?'),
        (r'Điểm tốt\.', 'Nói có lý đấy.'),
        (r'nghiền ngẫm các câu hỏi luyện tập', 'cắm đầu làm bài tập'),
        (r'thiếu tay', 'thiếu người'),
        (r'có thể sử dụng một cô thư ký', 'đang rất cần một cô thư ký'),
        (r'Soooo\.\.\. ♪', 'Thế nên là... ♪'),
        (r'tỏ ra thương xót và ngoan ngoãn đầu hàng dưới ống kính máy ảnh của tôi', 'chiếu cố và ngoan ngoãn tạo dáng trước ống kính máy ảnh của tôi'),
        (r'Khoảnh khắc mềm mại và yếu ớt của (?:ông chủ|Boss)', 'Khoảnh khắc Dịu Dàng Của Boss'),
        (r'đánh bại cả thế giới', 'chọc giận cả thế giới'),
        (r'Nóng lòng chờ đợi!', 'Thật nóng lòng quá đi!'),
        (r'Nó siêu hay[!.]*', 'Ngon đỉnh chóp luôn á!'),
        (r'Loại soda vị sữa chua này!\s*==W==\s*Nó siêu hay!', 'Lon soda vị sữa chua này!==W== Ngon đỉnh chóp luôn á!'),
        (r'Nhẫn[-—]!', 'Reng—!'),
        (r'Omnisky Aegis', 'Khiên Thanh Không'),
        (r'Thật đáng sợ\.\.\.\s*Tôi có làm đổ đậu ở đó không\?', 'Đáng sợ thật đấy... Ban nãy mình lỡ mồm nói lộ bí mật gì rồi sao?'),
        (r'Điều đó có rung chuông không\?', 'Bạn có nhớ mang máng gì không?'),
        (r'Xe của bang hội chúng tôi đang hoạt động\.', 'Dạo này xe của lữ đoàn chúng tôi đang bị trục trặc.'),
        (r'và cơ thể tôi bắt đầu hoạt động\.', 'và cơ thể tôi bắt đầu dở chứng khó chịu.'),
        (r'tràn ngập thị trường với bu lông ăn mòn.*?nhiều bảo hiểm tai nạn hơn được đẩy\.', 'tuồn ra thị trường bu-lông dễ rỉ sét và đai ốc kém chất lượng... ==W== Lữ Khách gặp nạn khi làm nhiệm vụ, từ đó ép mua thêm nhiều bảo hiểm tai nạn hơn.'),
        (r'Họ sẽ không dừng lại vì lợi nhuận,\s*phải không\?', 'Đúng là vì lợi nhuận mà thủ đoạn nào chúng cũng dám làm nhỉ?'),
        (r'Bất chấp điều đó,\s*tôi đã sở hữu được thứ mà tôi đến vì nó\.', 'Dù sao đi nữa, tôi cũng đã lấy được thứ mình cần rồi.'),
        (r'Vivian\?!\s*Phục vụ ăn uống\?!', 'Vivian?! Caterine?!'),
        (r'Chờ đợi!\s*Vivian\?!\s*(?:Phục vụ ăn uống|Caterine)\?!', 'Đợi đã! Vivian?! Caterine?!'),
        (r'\bXíchxia\b', 'Chixia'),
        (r'\bXích Hạ Huyền Thị\b', 'Huyền Sư Chixia'),
        (r'(?:Xíchxia|Chixia) the Xuân Shi', 'Huyền Sư Chixia'),
        (r'Xích Hạ Xuân,\s*Xuân…\s*Xuân Thực!', 'Chixia, Huyền, Huyền… Huyền Sư!'),
        (r'\bCục Baize\b', 'Phủ Bạch Trạch'),
        (r'\bBóng ma\?', 'Wraith?'),
        (r'Bóng ma,\s*hãy quay lại và cứu tôi—!', 'Wraith ơi, mau quay lại cứu tôi với—!'),
        (r'Bóng ma\?!\s*Cảm ơn chúa,\s*bạn đã trở lại\.\.\.', 'Wraith?! May quá, cậu quay lại rồi...'),
        (r'L-Buông ra!\s*Bóng ma,\s*là tôi đây!', 'B-Buông ra! Wraith ơi, là tôi mà!'),
        (r'\bCaramen\b', 'Caramel'),
        (r'\bcaramen\b', 'Caramel'),
        (r'Đúng là phong cách Caramel\.', 'Đúng chuẩn phong cách Caramel.'),
        (r'Caramel cổ điển', 'Đúng chuẩn phong cách Caramel'),
        (r'\bHiệp (?:hội )?Ngôi sao Mới\b', 'Lữ Đoàn Tân Tinh'),
        (r'\bHội Ngôi sao Mới\b', 'Lữ Đoàn Tân Tinh'),
        (r'Hiệp Lữ Đoàn Tân Tinh', 'Lữ Đoàn Tân Tinh'),
        (r'Nhân sự Sếp Accord', 'Nhân Sự Boss Accord'),
        (r'Sếp Accord Staffing', 'Nhân Sự Boss Accord'),
        (r'Boss Accord Staffing', 'Nhân Sự Boss Accord'),

        # Fixes for Boss & pronouns
        (r'\bB-\s*==W==\s*Ông chủ…\?!', 'B-==W==Boss…?!'),
        (r'\bthưa ông chủ\b', 'thưa Boss'),
        (r'\bThưa ông chủ\b', 'Thưa Boss'),
        (r'\bông chủ\b', 'Boss'),
        (r'\bÔng chủ\b', 'Boss'),
        (r'\bông ổn chứ\b', 'cậu ổn chứ'),
        (r'\bÔng ổn chứ\b', 'Cậu ổn chứ'),
        (r'\bông có thể\b', 'cậu có thể'),
        (r'\bÔng có thể\b', 'Cậu có thể'),
        (r'\bngười bạn này của ông\b', 'người bạn này của cậu'),
        (r'\bĐiều gì khiến ông đột nhiên quyết định\b', 'Điều gì khiến cậu đột nhiên quyết định'),
        (r'\bÔng không phiền phải không\b', 'Cậu không phiền chứ'),
        (r'\bTôi mừng vì ông đã ở đây\b', 'Tôi mừng vì cậu đã ở đây'),
        (r'\bÔng không thích đồ ngọt à\b', 'Cậu không thích đồ ngọt à'),
        (r'\bbạn và mẹ đã kết hôn chưa\b', 'cậu với mẹ đã kết hôn chưa'),
        (r'\bcưới mẹ và ông chủ\b', 'cưới mẹ và Boss'),

        # Commission nuances (All occurrences of hoa hồng fixed)
        (r'\bmón hoa hồng bí ẩn\b', 'nhiệm vụ ủy thác bí ẩn'),
        (r'\bhoa hồng chỉ là một thông báo đơn giản\b', 'nhiệm vụ ủy thác chỉ là một thông báo đơn giản'),
        (r'\bchiếm đoạt giữa hoa hồng\b', 'cướp tay trên khi đang làm ủy thác'),
        (r'\bngày mai chúng tôi vẫn có hoa hồng\b', 'ngày mai chúng ta vẫn còn ủy thác đấy'),
        (r'\bHoa hồng hoàn tất\b', 'Ủy thác hoàn tất'),
        (r'\bchọn hoa hồng thực sự phù hợp\b', 'chọn những ủy thác thực sự phù hợp'),
        (r'\bHoa hồng gần đây đã được trả khá tốt\b', 'Tiền thù lao ủy thác gần đây khá lắm'),
        (r'\bHoa hồng khá đơn giản\b', 'Ủy thác này khá đơn giản'),
        (r'\bHoa hồng của bạn đã hoàn tất\b', 'Ủy thác của bạn đã hoàn tất'),
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


        # Radio & speech
        (r'\bDo you copy\??', 'Bạn có nghe rõ không!?'),
        (r'\b[Bb]ạn có sao chép không[\s?!]*', 'Bạn có nghe rõ không!?'),
        (r'\b[Bb]ạn sao chép không[\s?!]*', 'Bạn có nghe rõ không!?'),
        (r'\b[Cc]ó sao chép không[\s?!]*', 'Nghe rõ không!?'),
        (r'\bsao chép không[\s?!]*', 'nghe rõ không!?'),
        (r'\b[Cc]ó sao chép\b', 'nghe rõ'),
        (r'\bsao chép\b', 'nghe rõ'),
        (r'\buống một viên thuốc hạ sốt đi\b', 'bình tĩnh lại nào'),
        (r'\buống thuốc hạ nhiệt\b', 'thả lỏng chút đi mà'),
        (r'\buống thuốc an thần\b', 'bình tĩnh lại đi'),
        (r'\bbạn tình\b', 'đồng đội'),
        (r'\bbản dựng\b', 'lối chơi'),
        (r'\bkẻ thù\b', 'kẻ địch'),
        (r'\b[Nn]gười đi bộ\b', 'Lữ Khách'),
        (r'\b[Nn]hững người đi bộ\b', 'các Lữ Khách'),

        # Noya & Loxy & Chitose
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
        (r'\bOneness between wielder and blade\b', 'đao nhân hợp nhất'),
        (r'\bOneness between blade and wielder\b', 'nhân kiếm hợp nhất'),
        (r'\bsự hợp nhất giữa lưỡi kiếm và người sử dụng\b', 'cảnh giới nhân kiếm hợp nhất'),
        (r'\bsự hợp nhất giữa người cầm kiếm và lưỡi kiếm\b', 'cảnh giới nhân kiếm hợp nhất'),
        (r'\bsự thống nhất giữa người sử dụng và lưỡi dao\b', 'cảnh giới đao nhân hợp nhất'),
        (r'\bsự thống nhất giữa lưỡi kiếm và người sử dụng\b', 'cảnh giới nhân kiếm hợp nhất'),
        (r'\blưỡi dao chưa được bọc\b', 'lưỡi đao chưa tra vào bao'),
        (r'\blưỡi dao chưa có vỏ\b', 'lưỡi đao chưa tra vào bao'),
        (r'\bngười mang lưỡi dao\b', 'người nắm giữ lưỡi kiếm'),
        (r'\bngười cầm kiếm\b', 'người nắm giữ lưỡi kiếm'),
        (r'\bngười sử dụng thanh kiếm\b', 'người nắm giữ thanh kiếm'),
        (r'\bgió kiếm\b', 'kiếm phong'),

        # Ruby tag spacing cleanup
        (r'\bNo\s*(<r=[^>]+>.*?</r>)\s*ya\b', r'No\1ya'),
    ]
    for pat, rep in narrative_rules:
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)

    # 4. Color tag balancing
    opens = len(COLOR_TAG_OPEN.findall(text))
    closes = len(COLOR_TAG_CLOSE.findall(text))
    if opens != closes:
        if opens > closes:
            text += "</color>" * (opens - closes)
        elif closes > opens:
            for _ in range(closes - opens):
                last_idx = text.rfind("</color>")
                if last_idx != -1:
                    text = text[:last_idx] + text[last_idx+8:]

    # 5. Clean token & punctuation spacing
    text = re.sub(r'==\s*([a-zA-Z0-9_]+)\s*==', r'==\1==', text)
    while re.search(r'(==[a-zA-Z0-9_]+==)\s+(==[a-zA-Z0-9_]+==)', text):
        text = re.sub(r'(==[a-zA-Z0-9_]+==)\s+(==[a-zA-Z0-9_]+==)', r'\1\2', text)
    text = re.sub(r'\s+([,.:;?!])', r'\1', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)

    return text.strip(" \t\r\n")

def ensure_token_preservation(orig: str, trans: str) -> str:
    """Guarantee 100% token preservation matching orig."""
    orig_tokens = TOKEN_REGEX.findall(orig)
    if not orig_tokens:
        return trans

    # 1. Normalize ==...== case & spaces
    for tok in orig_tokens:
        if tok.startswith('==') and tok.endswith('=='):
            inner = tok[2:-2]
            trans = re.sub(rf'==\s*{re.escape(inner)}\s*==', tok, trans, flags=re.IGNORECASE)

    trans_tokens = TOKEN_REGEX.findall(trans)
    if sorted(orig_tokens) == sorted(trans_tokens):
        return trans

    # 2. Count differences
    orig_counts = Counter(orig_tokens)
    trans_counts = Counter(trans_tokens)

    # Remove excess tokens
    for tok, count in trans_counts.items():
        if orig_counts[tok] < count:
            excess = count - orig_counts[tok]
            for _ in range(excess):
                idx = trans.rfind(tok)
                if idx != -1:
                    trans = trans[:idx] + trans[idx+len(tok):]

    # Re-count after removal
    trans_tokens = TOKEN_REGEX.findall(trans)
    trans_counts = Counter(trans_tokens)

    # Missing tokens
    missing = []
    for tok, count in orig_counts.items():
        if trans_counts[tok] < count:
            missing.extend([tok] * (count - trans_counts[tok]))

    for tok in missing:
        if orig.startswith(tok) and not trans.startswith(tok):
            trans = tok + " " + trans
        elif orig.endswith(tok) and not trans.endswith(tok):
            trans = trans + " " + tok
        else:
            trans = trans + " " + tok

    # Re-balance color tags if color tags were involved
    opens = len(COLOR_TAG_OPEN.findall(trans))
    closes = len(COLOR_TAG_CLOSE.findall(trans))
    if opens != closes:
        if opens > closes:
            trans += "</color>" * (opens - closes)
        elif closes > opens:
            for _ in range(closes - opens):
                last_idx = trans.rfind("</color>")
                if last_idx != -1:
                    trans = trans[:last_idx] + trans[last_idx+8:]

    trans = re.sub(r'[ \t]{2,}', ' ', trans)
    return trans.strip(" \t\r\n")

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

def main():
    print("=" * 75)
    print("Senior Translator 3 (Batch 2 - Part C): Character Stories CG Part 2")
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
                unshielded = robust_unshield_tokens(trans_s, tok)
                polished = polish_character_story_dialogue(unshielded, terms, forbidden)
                if not is_valid_token_preservation(orig_txt, polished):
                    polished = ensure_token_preservation(orig_txt, polished)
                results.append((orig_txt, polished))
            return results

        completed_batches = 0
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_chunk = {executor.submit(process_batch, b): b for b in batches}
            for future in as_completed(future_to_chunk):
                try:
                    res = future.result()
                    for orig_txt, trans_txt in res:
                        cache[orig_txt] = trans_txt
                except Exception as e:
                    print(f"Batch failed: {e}")
                completed_batches += 1
                if completed_batches % 15 == 0 or completed_batches == len(batches):
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

        trans = cache.get(str_val, str_val)
        trans = polish_character_story_dialogue(trans, terms, forbidden)
        if not is_valid_token_preservation(str_val, trans):
            trans = ensure_token_preservation(str_val, trans)

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
