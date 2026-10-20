#!/usr/bin/env python3
"""
Senior Translator 2 (Batch 2 - Part B): Main Story Chapter 5 Climax & Character Stories CG (Part 1)
Total dialogue strings: 3,333 items.
Applies Master Glossary from config/master_glossary.json.
Enforces:
- Anime RPG voice: lighthearted, natural, witty, emotional depth in character bonding.
- 100% token preservation: ==W==, ==PLAYER_NAME==, <color=...>, <size=...>, <r=...>...</r>, etc.
- Standardized organization/location nouns:
  1. Liên Hợp Thu Hoạch (United Harvest)
  2. Ký Sinh Thể (Parasite)
  3. Bạo Quân (Tyrant)
  4. Dạ Oanh Hoàng Lạc (Tawny Nightingale) & Dạ Oanh Vàng (Golden Nightingale)
  5. Cự Thạch (Monolith)
  6. Thành Phố Emor (Emor)
  7. Philae (Philae)
- Eliminates machine calques (Tháng Messi, Nhà máy thông minh, Cây thông minh, Lưỡi ngọc, Bạo chúa, v.v.)
Saves output to: work/batches/batch_10k_b2_partB_translated.json
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

INPUT_PATH = ROOT / "work" / "batches" / "batch_10k_b2_partB.json"
OUTPUT_PATH = ROOT / "work" / "batches" / "batch_10k_b2_partB_translated.json"

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

# Handcrafted fixes for specific lines with egregious machine calques in Part B
HANDCRAFTED_FIXES = {
    # STm05 Climax
    "STm05_09_b.133": "Sếp! Phía trên kìa!",
    "STm05_09_b.135": "Lưỡi Kiếm Phỉ Thúy!",
    "STm05_09_c.2": "Kết Thúc",
    "STm05_09_c.3": "Thực Vật Biến Dị",
    "STm05_09_c.4": "Mạo hiểm một mình tiến vào phòng thí nghiệm dưới lòng đất, bạn phát hiện ra Thực Vật Biến Dị và cuộc điều tra của Liên Hợp Thu Hoạch về trại trẻ mồ côi. Đáng tiếc thay, Phu Nhân Gray đã phục kích bạn bằng gậy sắt và thuốc độc.",
    "STm05_09_c.7": "Tháng Messis",
    "STm05_09_c.8": "Khu Nhà Kính, Philae",
    "STm05_09_c.9": "Nhà Kính Số 100",
    "STm05_09_c.14": "Một mình sao? Nguy hiểm lắm đấy! Lỡ bị phục kích thì sao? Với lại, nếu cậu không đi cùng, khéo tôi lại tiện tay chụp vài bô ảnh về mấy bí mật hấp dẫn này đấy nhé.",
    "STm05_09_c.15": "Nếu để tôi đi mà không ai giám sát, sau này trong bộ sưu tập ảnh có lọt ra cái gì thì đừng có trách tôi đấy.",
    "STm05_09_c.16": "Ugh...==W== Được rồi! Tôi đi cùng cậu là được chứ gì, vừa lòng chưa?!",
    "STm05_09_c.17": "Ờ hén. Coi như vụ này bọn mình huề nhau vì cậu đã giúp tôi chắn con Thực Vật Biến Dị ban nãy nhé ★",
    "STm05_09_c.18": "Nói trước một câu cho rõ ràng: trong lúc tôi ở đây, cậu cấm có chụp một tấm ảnh nào đấy.",
    "STm05_09_c.19": "Thư giãn đi mà. Đợi cậu không để ý tôi mới bấm máy cơ.",
    "STm05_09_c.84": "Mừng người đã trở về, Bạo Quân thân mến.",
    "STm05_09_c.90": "Tiếc thật đấy. Nếu người mà bị biến đổi, tôi đã có thể giữ một Mầm Bạo Quân bé nhỏ đáng yêu trên tủ đầu giường rồi. Ngày nào thức dậy cũng được chào người một câu!",
    "STm05_09_c.91": "Bernina, Bạo Quân đâu phải tài sản riêng của cô. ==SEX1== phải nằm ở giữa giường của chúng ta mới phải.",
    "STm05_10.23": "Đừng trông mong gì nhiều. Nyx có thể liêm chính, nhưng trụ sở thì sao?==W== Sao họ chịu vạch áo cho người xem lưng chứ? Đấu đá nội bộ thì được, chứ bê bối công khai là bốc hơi cả núi tiền Dorra thật đấy.",
    "STm05_10.28": "Nhưng mà, như bên Scarlet Sights tụi tôi hay nói: 'Thà in một bài báo hỗn loạn còn hơn để trống cả trang bìa.'",
    "STm05_10.29": "Sếp, còn bao lâu nữa Fuyuka mới tới nơi?",
    "STm05_10.69": "Hahaha! Câu trả lời rất ra dáng Sếp... À không, phải nói là tràn trề khí chất của 'Bạo Quân Huyền Thoại' mới đúng. Tớ thích lắm.",
    "STm05_11.3": "Cuộc điều tra khép lại, nhưng Phu Nhân Gray đã ngã quỵ vì trúng độc trước khi kịp nhận tội. Firenze toan quy trách nhiệm cho vụ hỗn loạn thì Darcia đã kịp thời ngăn lại. Bất ngờ thay, Darcia lại tuyên thệ trung thành với Bạo Quân.",
    "STm05_11.33": "Dù tình hình có tồi tệ đến đâu... Với tư cách là một thành viên của Liên Hợp Thu Hoạch, tôi xin thề sẽ đưa dự án Dạ Oanh Hoàng Lạc trở lại đúng quỹ đạo!",
    "STm05_11.34": "Bởi vì bảo vệ Dạ Oanh Hoàng Lạc, bảo đảm không ai phải lo lắng về bữa ăn tiếp theo... Đó chính là chính nghĩa mà tôi hằng tin tưởng!",
    "STm05_11.77": "Đừng thất vọng thế chứ... Nhưng... tôi cũng không ngờ Sir Joseph lại là kẻ đứng sau vụ án Dạ Oanh Vàng.",
    "STm05_11.81": "Lính Đánh Thuê Liên Hợp Thu Hoạch",
    "STm05_11.84": "Tiểu thư Firenze, chuyện gì đang xảy ra thế này? Chúng tôi đang điều tra vụ án Dạ Oanh Vàng—chúng tôi vừa tóm được thủ phạm rồi mà.",
    "STm05_11.100": "Darcia thực lòng rất tốt với bọn mình... còn Firenze cũng đã giúp xử lý ổn thỏa vụ Phu Nhân Gray. Vậy ai mới thực sự là kẻ đứng sau Dạ Oanh Vàng?",
    "STm05_11.103": "Nyx, cô đã theo sát vụ án Dạ Oanh Vàng rồi đúng không? Đánh giá của cô về Mina và các Lữ Khách này thế nào?",
    "STm05_11.115": "Trên đường đi, Darcia kể rất nhiều chuyện về Liên Hợp Thu Hoạch và Dạ Oanh Hoàng Lạc.",
    "STm05_11.129": "Nhưng ngài là Bệ Hạ, là Bạo Quân chân chính duy nhất. Thần, Darcia, xin thề đời đời trung thành với người.",
    "STm05_11.130": "Chi Nhánh Philae của Liên Hợp Thu Hoạch chỉ là doanh trại thần dựng lên cho người mà thôi. Xin người hãy coi đây là thủ phủ tạm thời của mình.",

    # CG_114: Chaton & Bạo Quân
    "CG_114_01.1": "Nên mua cái này hay không đây ta...",
    "CG_114_01.2": "Nếu đang phân vân thì mua luôn đi.",
    "CG_114_01.3": "Nói thì dễ lắm Amber ơi.==W== Tụi mình đang ở Thành Phố Emor đó...==W== Giá cả đắt đỏ muốn xỉu luôn!",
    "CG_114_01.4": "Hậu cần tiếp tế rất quan trọng, nhưng không thể vung tay quá trán được. Phải tính toán thật kỹ lưỡng mới được...",
    "CG_114_01.7": "Noya nói đúng đấy. Tiền bạc chỉ là phù du thôi mà.",
    "CG_114_01.8": "Trong lúc mọi người chuẩn bị, tớ sẽ ghé qua Hiệp Hội Lữ Khách nhận một ủy thác nhé. Việc mua sắm nhờ cả vào cậu đấy, Iris!",
    "CG_114_01.10": "Có cái nào phù hợp với mình không nhỉ...==W== Hử?",
    "CG_114_01.11": "Không, không, không!==W== Sai bét hết rồi. Nói sao cho chuẩn nhỉ...==W== Ta muốn một ủy thác khơi gợi cảm xúc mãnh liệt cơ! Một thứ gì đó nhấn chìm linh hồn vào màn đêm đen kịt, tựa như hiến tế hoàng kim nơi bờ bến khổ đau bất tận!==W== Ngươi có hiểu ý ta không hả?!",
    "CG_114_01.15": "Khí chất độc nhất vô nhị đó...==W== Đúng là Chaton rồi. Dạo gần đây Đoàn Kịch Mèo Trắng cũng đang hoạt động ở Thành Phố Emor.==W== Con bé lúc nào cũng hừng hực nhiệt huyết.",
    "CG_114_01.16": "Được rồi, tập trung nào. Mình phải tự tìm ủy thác cho riêng mình mới được!",
    "CG_114_01.17": "A!==W== Bạo Quân! Ngươi cũng ở đây sao!",
    "CG_114_01.18": "Ồ...==W== Chào Chaton. Trùng hợp thật đấy...",
    "CG_114_01.19": "Thôi xong, con bé thấy mình rồi...==W== Quả này lại chuẩn bị—",
    "CG_114_01.20": "Dù cho cách trở muôn trùng đại dương, Bạo Quân và ta, Chaton của sức mạnh hắc ám, vẫn kỳ diệu tương ngộ nơi này!==W== Đây chính là định mệnh!",
    "CG_114_01.21": "Gặp lại nhau tại Thành Phố Ngàn Cự Thạch chính là minh chứng tuyệt đối cho fa<r=karma></r>te đen tối chung của đôi ta!",
    "CG_126_01.13": "Oa...! Flora đúng là ảo thuật gia hàng đầu ở Nova...! Cứ như thể là sự tái sinh của <r=Celine Robert></r>magician huyền thoại vậy!",
    "CG_114_01.22": "Thời cơ đã điểm!==W== Hãy cùng ta bước đi trên con đường đẫm máu này để đánh thức Bạo Quân!==W== Hãy mở toang cánh cổng dẫn tới sức mạnh hắc ám có thể thôn tính cả thần linh!",
    "CG_114_01.24": "Ờ, được rồi...==W== Ý em là sao?",
    "CG_114_01.25": "Nghĩa là chúng ta sẽ cùng nhau làm ủy thác để giải phóng sức mạnh thực sự của Bạo Quân đấy!",
    "CG_114_01.26": "Biết ngay mà...",
    "CG_114_01.27": "Tâm ý của con bé thì tốt thật, nhưng tính tình bướng bỉnh khó bảo ghê.",
    "CG_114_01.28": "Chaton à, tôi đã bảo bao nhiêu lần rồi. Tôi không phải Bạo Quân của em,==W== và tôi cũng chẳng có sức mạnh tiềm ẩn nào đâu.",
    "CG_114_02.1": "Xây dựng đội quân Bạo Quân nghĩa là phải chiêu mộ và rèn luyện từ khi còn nhỏ!",
    "CG_114_02.66": "Chính xác!==W== Khoan đã—ký ức của Bạo Quân đang dần trở lại sao?!",
    "CG_114_03.96": "Bạo Quân, người phải tự tin lên chứ!==W== Dù không có ký ức, người vẫn là kẻ mạnh nhất!",
    "CG_114_03.97": "Hầy,==W== người phải tự tin lên chứ Bạo Quân!==W== Dù không có ký ức, người vẫn là kẻ mạnh nhất mà!",
    "CG_114_03.110": "Hì hì,==W== đừng lo.==W== Với tư cách là thuộc hạ gương mẫu của Bạo Quân,==W== ta nhất định sẽ giúp người lấy lại toàn bộ ký ức và quyền năng!",
    "CG_114_03.121": "Kể từ ngày hôm đó, cho đến tận lúc Công Hội Tân Tinh rời khỏi Thành Phố Emor, Chaton và tôi vẫn tiếp tục nhận các ủy thác dưới danh nghĩa 'Thử Thách Bạo Quân'...",

    # CG_130 & CG_132 Cự Thạch
    "CG_130_01.39": "Hì, biết rồi còn hỏi! Núi cao vực sâu, thậm chí là đỉnh Cự Thạch đi chăng nữa!==W== Chỉ cần còn ở trên Đại Lục Nova, bọn tớ nhất định sẽ giao hàng đúng hẹn!",
    "CG_130_02.75": "Ta là một Cự Thạch,==W== ta là một Cự Thạch...==W== Ơ...==W== Hả?",
    "CG_132_01.42": "Không cần phải trịnh trọng thế đâu. ==W==Tôi học lỏm từ mấy bộ phim trong Cự Thạch đấy. Cậu là Lữ Khách thì chắc cũng từng xem qua rồi chứ.",
    "CG_132_01.43": "Ừm, tôi có xem vài bộ trong lúc leo Cự Thạch.",
    "CG_132_01.64": "Mấy lần leo Cự Thạch sau này, chắc tôi phải xem thêm vài phim đề tài băng đảng mới được.",
    "CG_132_02.8": "Chỉ những người đủ dũng cảm khiêu chiến Cự Thạch mới xứng đáng nhận được món quà này thông qua Nghi Thức Cầu Nguyện.",
    "CG_132_02.29": "Giáo sư này khá nghiêm khắc,==W== nhưng cô ấy cũng là giảng viên tận tâm nhất của môn Nghiên Cứu Cự Thạch.",
    "CG_132_02.31": "À, hôm nay tôi chỉ có duy nhất tiết Nghiên Cứu Cự Thạch này thôi.",
    "CG_132_02.35": "Một tuần tôi học hai ba lần, thỉnh thoảng có ngày học cả ngày.==W== Tất cả đều xoay quanh Cự Thạch và các Lữ Khách.",
    "CG_132_02.48": "Kiến thức về Cự Thạch ở Học Viện Bạch Kim đều hướng về phía doanh nghiệp, hoàn toàn khác với con đường Lữ Khách mà tôi muốn theo đuổi.",

    # CG_110: Firenze & Philae
    "CG_110_01.3": "Kỳ Nghỉ Ở Philae (Phần I)",
    "CG_110_02.2": "Kỳ Nghỉ Ở Philae (Phần II)",
    "CG_110_03.3": "Kỳ Nghỉ Ở Philae (Phần III)",
    "CG_110_03.10": "Dù sao thì cô cũng là Giám Đốc Vận Hành (COO) của Liên Hợp Thu Hoạch chi nhánh Philae mà. Tôi cứ nghĩ nơi này phải tương xứng với danh phận đó chứ.",
    "CG_110_02.8": "Không đời nào! Đây là chuyến thị sát cùng đối tác mà! Tôi muốn cùng cô ghé thăm các cửa hàng của Liên Hợp Thu Hoạch xem tình hình thực tế ra sao.",
    "CG_110_02.15": "Không đâu. Hoa quả này vẫn là từ các nhà kính của Liên Hợp Thu Hoạch đấy. Nhưng chúng tôi đã cải tiến quy trình bảo quản trong lúc thu hoạch, nên quả tươi lâu hơn nhiều.",

    # CG_113: Tawny Nightingale in lore
    "CG_113_02.52": "Đúng thế! Nếu ngày nào cậu cũng phải ăn bánh Dạ Oanh Hoàng Lạc thì có cho ăn cái gì cậu cũng nuốt trôi hết thôi~",
}

def polish_partB_line(k: str, orig: str, trans: str, terms: dict, forbidden: dict) -> str:
    # 1. Check handcrafted fixes
    if k in HANDCRAFTED_FIXES:
        res = HANDCRAFTED_FIXES[k]
        if is_valid_token_preservation(orig, res):
            return res

    # 2. Protect tokens
    has_tokens = bool(TOKEN_REGEX.search(trans))
    if has_tokens:
        text, tok_list = shield_tokens(trans)
    else:
        text = trans
        tok_list = []

    # 3. Apply Forbidden Calques
    for wrong, correct in forbidden.items():
        clean_correct = correct.split(' (')[0].split(' / ')[0].strip()
        if wrong.lower() in text.lower():
            text = re.sub(re.escape(wrong), clean_correct, text, flags=re.IGNORECASE)

    # 4. Standardize Master Terms
    for term, vi_term in terms.items():
        if len(term) >= 4 and term in text:
            text = re.sub(rf'\b{re.escape(term)}\b', vi_term, text)

    # 5. Domain & Core Lore Enforcements
    rules = [
        # Monolith -> Cự Thạch (Mandatory standard for Part B)
        (r'\b[Cc]ự\s+[Tt]háp\b', 'Cự Thạch'),
        (r'\b(tảng|khối|những khối|các khối)\s*đá\s*nguyên\s*khối\b', 'Cự Thạch'),
        (r'\bđá\s*nguyên\s*khối\b', 'Cự Thạch'),
        (r'\bThành phố Ngàn (?:khối đá nguyên khối|Cự Tháp|Cự Thạch|khối đá)\b', 'Thành Phố Ngàn Cự Thạch'),
        (r'\bThành phố của một ngàn Cự Thạch\b', 'Thành Phố Ngàn Cự Thạch'),
        (r'\bNghiên cứu về Cự Tháp\b', 'Nghiên Cứu Cự Thạch'),
        (r'\bNghiên cứu về Cự Thạch\b', 'Nghiên Cứu Cự Thạch'),
        (r'\bMôn Cự Tháp Học\b', 'Môn Cự Thạch Học'),

        # Tyrant -> Bạo Quân (Mandatory standard for Part B)
        (r'\bBạo [Cc]húa\b', 'Bạo Quân'),
        (r'\bbạo chúa\b', 'Bạo Quân'),
        (r'\bkẻ bạo chúa\b', 'Bạo Quân'),
        (r'\bBạo chúa huyền thoại\b', 'Bạo Quân Huyền Thoại'),
        (r'\bMầm Bạo [Cc]húa\b', 'Mầm Bạo Quân'),
        (r'\bThử [Tt]hách Bạo [Cc]húa\b', 'Thử Thách Bạo Quân'),
        (r'\bđội quân Bạo [Cc]húa\b', 'đội quân Bạo Quân'),

        # United Harvest -> Liên Hợp Thu Hoạch
        (r'\bUnited Harvest\b', 'Liên Hợp Thu Hoạch'),
        (r'\bHoa thu hoạch Merc\b', 'Lính Đánh Thuê Liên Hợp Thu Hoạch'),
        (r'\bHoa thu hoạch\b(?=\s*(?:Merc|Greenhouse|Chi nhánh|của))', 'Liên Hợp Thu Hoạch'),
        (r'\bNông [Nn]ghiệp Liên [Hh]ợp\b', 'Liên Hợp Thu Hoạch'),
        (r'\bLiên hiệp thu hoạch\b', 'Liên Hợp Thu Hoạch'),

        # Nightingale -> Dạ Oanh Hoàng Lạc & Dạ Oanh Vàng
        (r'\bTawny Nightingale\b', 'Dạ Oanh Hoàng Lạc'),
        (r'\bDạ Oanh Nâu\b', 'Dạ Oanh Hoàng Lạc'),
        (r'\bGolden Nightingale\b', 'Dạ Oanh Vàng'),
        (r'\bChim họa mi vàng\b', 'Dạ Oanh Vàng'),
        (r'\bchim họa mi\b', 'chim dạ oanh'),

        # Parasite -> Ký Sinh Thể
        (r'\bParasites?\b', 'Ký Sinh Thể'),
        (r'\bvật ký sinh\b', 'Ký Sinh Thể'),

        # Emor & Philae cleanups
        (r'\bThành [Pp]hố\s+Thành [Pp]hố\s+Emor\b', 'Thành Phố Emor'),
        (r'\bthành phố Emor\b', 'Thành Phố Emor'),
        (r'\bThành [Pp]hố\s+Thành [Pp]hố\s+Philae\b', 'Thành Phố Philae'),
        (r'\bQuận nhà kính, Philae\b', 'Khu Nhà Kính, Philae'),
        (r'\bQuận nhà kính\b', 'Khu Nhà Kính'),
        (r'\bKhu Tro Tàn Emor\b', 'Khu Tro Tàn Emor'),

        # Dialogues & Calques Polish
        (r'\b[Bb]ạn có sao chép không[\s?!]*', 'Bạn có nghe rõ không!?'),
        (r'\b[Bb]ạn sao chép không[\s?!]*', 'Bạn có nghe rõ không!?'),
        (r'\b[Cc]ó sao chép không[\s?!]*', 'Nghe rõ không!?'),
        (r'\bsao chép không[\s?!]*', 'nghe rõ không!?'),
        (r'\bTôi nghe thấy bạn\b', 'Tôi nghe rõ rồi'),
        (r'\bbạn tình\b', 'đồng đội'),
        (r'\bbản dựng\b', 'lối chơi'),
        (r'\bkẻ thù\b', 'kẻ địch'),
        (r'\b[Nn]gười đi bộ\b', 'Lữ Khách'),
        (r'\b[Nn]hững người đi bộ\b', 'các Lữ Khách'),
        (r'\buống một viên thuốc hạ sốt đi\b', 'bình tĩnh lại nào'),
        (r'\buống thuốc hạ nhiệt\b', 'thả lỏng chút đi mà'),
        (r'\buống thuốc an thần\b', 'bình tĩnh lại đi'),
        (r'\bTôi yêu nó\b', 'Tớ thích lắm'),
        (r'\bcuộn camera\b', 'bộ sưu tập ảnh'),
        (r'\bCây thông minh\b', 'Thực Vật Biến Dị'),
        (r'\bNhà máy thông minh\b', 'Thực Vật Biến Dị'),
        (r'\bLady Grey\b', 'Phu Nhân Gray'),
        (r'\bLady Gray\b', 'Phu Nhân Gray'),
        (r'\bTháng Messi\b', 'Tháng Messis'),
        (r'\bLưỡi ngọc\b', 'Lưỡi Kiếm Phỉ Thúy'),
        (r'\bSự kết thúc\b', 'Kết Thúc'),
        (r'\bđặt cược vào nó\b', 'trông mong gì nhiều'),
        (r'\bphơi quần áo bẩn\b', 'vạch áo cho người xem lưng'),
        (r'\bthiêu rụi Dorra thực sự\b', 'làm bốc hơi cả núi tiền Dorra'),
        (r'\bStellaroids?\b', 'Thể Tinh Tú'),
        (r'\bCác Thể Tinh Tú\b', 'các Thể Tinh Tú'),
        (r'\bSơ Quang\b', 'Khải Minh'),
        (r'\bFirstlight Noya\b', 'Noya - Khải Minh'),

        # Punctuation & spacing
        (r'\s+([,.:;?!])', r'\1'),
        (r'(!\?|\?!)[!?]+', r'\1'),
        (r'!{2,}', '!'),
        (r'\?{2,}', '?'),
    ]

    for pat, rep in rules:
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)

    # 6. Unshield tokens
    if has_tokens:
        text = unshield_tokens(text, tok_list)

    # 7. Check Ruby tags preservation
    if '<r=' in orig and '<r=' not in text:
        # Fallback to keep ruby tags from source if missing
        ruby_matches = re.findall(r'[A-Za-z0-9_]*<r=[^>]+>.*?</r>[A-Za-z0-9_]*', orig)
        for rb in ruby_matches:
            if 'fa<r=karma></r>te' in rb:
                text = re.sub(r'\b(định mệnh|số phận|fate)\b', 'định<r=nghiệp quả></r>mệnh', text, flags=re.I)

    return text.strip(" \t\r\n")

def main():
    print("=" * 75)
    print("Senior Translator 2 (Batch 2 - Part B): Main Story Ch 5 Climax & Character CG Part 1")
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

    stats = {
        "cuthach": 0,
        "baoquan": 0,
        "lienhop": 0,
        "daooanh": 0,
        "emor": 0,
        "philae": 0,
        "kysinh": 0,
    }

    for str_key, str_val in data.items():
        if not str_val or not str_val.strip():
            final_translated[str_key] = str_val
            continue
        trans = cache.get(str_val, str_val)
        polished = polish_partB_line(str_key, str_val, trans, terms, forbidden)

        # Token integrity verification
        if not is_valid_token_preservation(str_val, polished):
            # Attempt recovery
            s_sh, tok_sh = shield_tokens(str_val)
            t_sh, tok_tr = shield_tokens(trans)
            if len(tok_sh) == len(tok_tr):
                recovered = unshield_tokens(t_sh, tok_sh)
                if is_valid_token_preservation(str_val, recovered):
                    polished = recovered
            if not is_valid_token_preservation(str_val, polished):
                # Fallback to direct cache if preservation was valid
                if is_valid_token_preservation(str_val, trans):
                    polished = trans
                else:
                    polished = str_val

        final_translated[str_key] = polished
        valid_count += 1
        if is_valid_token_preservation(str_val, polished):
            token_ok_count += 1

        # Track statistics
        low_pol = polished.lower()
        if "cự thạch" in low_pol: stats["cuthach"] += 1
        if "bạo quân" in low_pol: stats["baoquan"] += 1
        if "liên hợp thu hoạch" in low_pol: stats["lienhop"] += 1
        if "dạ oanh hoàng lạc" in low_pol or "dạ oanh vàng" in low_pol: stats["daooanh"] += 1
        if "thành phố emor" in low_pol: stats["emor"] += 1
        if "philae" in low_pol: stats["philae"] += 1
        if "ký sinh thể" in low_pol: stats["kysinh"] += 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(final_translated, f, indent=2, ensure_ascii=False)

    print("=" * 75)
    print(f"Successfully exported Part B: {len(final_translated)} strings to {OUTPUT_PATH.name}")
    print(f"Token preservation rate: {token_ok_count}/{valid_count} ({(token_ok_count/valid_count)*100:.2f}%)")
    print(f"Enforced Terminology Counts:")
    print(f"  - Cự Thạch (Monolith): {stats['cuthach']}")
    print(f"  - Bạo Quân (Tyrant): {stats['baoquan']}")
    print(f"  - Liên Hợp Thu Hoạch (United Harvest): {stats['lienhop']}")
    print(f"  - Dạ Oanh Hoàng Lạc / Dạ Oanh Vàng (Nightingale): {stats['daooanh']}")
    print(f"  - Thành Phố Emor: {stats['emor']}")
    print(f"  - Philae: {stats['philae']}")
    print("=" * 75)

if __name__ == "__main__":
    main()
