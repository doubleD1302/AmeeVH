#!/usr/bin/env python3
"""
Senior Translator 2 (Batch 3 - Part B): Main Story Chapters 7 & 8 (STm07*, STm08*)
Total dialogue strings: 3,333 items.
Applies Master Glossary from config/master_glossary.json.
Enforces:
- Anime RPG voice: grand, emotional, natural dialogue, royal intrigue and sacred pacts.
- Standardized organization/lore terms:
  1. Đế Quốc Grace (Grace Imperium)
  2. Bạo Quân (Tyrant)
  3. Cận Vệ Hoàng Gia (Imperial Guard)
  4. Hiệp Ước Của Sếp (Boss Accord)
  5. Khiên Thanh Không (Omnisky Aegis)
  6. Lữ Đoàn Tân Tinh (New Star Guild)
  7. Viện Thiên Không (Sky Institute)
  8. Quang Nhãn Grace (Eye of Grace)
  9. Cửa Hàng Linh Hồn (Soul Shop)
  10. Cận Vệ Bình Minh (Sentinels of Dawn)
  11. Phán Quan Hoàng Hôn (Dusk Arbiter)
  12. Tứ Đại Khía Cạnh (Tetrad Aspects)
  13. Sách Tiên Tri Grace (Book of Grace Prophecies)
  14. Phong Ấn Ân Điển (Seal of Grace)
  15. Cự Thạch (Monolith) & Thành Phố Philae
- 100% token preservation: ==W==, ==PLAYER_NAME==, <color=...>, <size=...>, <r=...>...</r>, <i>...</i>, etc.
Saves output to: work/batches/batch_10k_b3_partB_translated.json
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

INPUT_PATH = ROOT / "work" / "batches" / "batch_10k_b3_partB.json"
OUTPUT_PATH = ROOT / "work" / "batches" / "batch_10k_b3_partB_translated.json"

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

# Handcrafted fixes for high-impact lines in Chapters 7 & 8
HANDCRAFTED_FIXES = {
    "STm07_02.117": "Hiệp Ước Của Sếp không phải là sân khấu độc diễn của riêng tôi. Tôi còn phải nghĩ cho anh em của mình nữa.",
    "STm07_02.118": "Tôi hiểu... Tôi đã hy vọng tránh phải dùng đến đòn đánh vào lòng trắc ẩn.",
    "STm07_03.8": "Sếp, đây là hợp đồng chuyển nhượng cổ phần chi nhánh Philae của Liên Hợp Thu Hoạch.",
    "STm07_03.9": "Bốn mươi mốt phần trăm nhà kính,==W== tòa nhà,==W== và đồng ruộng ngoài kia giờ đã thuộc về Hiệp Ước Của Sếp.",
    "STm07_03.16": "Hả?==W== Không có Hiệp Ước Của Sếp trong tên gọi sao?",
    "STm07_03.17": "Thông thường,==W== một thương vụ sáp nhập thế này sẽ có tên là \"Liên Doanh Philae Liên Hợp Thu Hoạch và Hiệp Ước Của Sếp\",==W== hoặc một cái tên ghép như \"Boss Harvest\".",
    "STm07_03.18": "Không cần thiết đâu. Lúc này Hiệp Ước Của Sếp tốt nhất nên giữ kín tiếng.==W== Hơn nữa, việc đổi thương hiệu quy mô lớn có thể làm gián đoạn vận hành,==W== mà chi phí thay mới bảng hiệu cũng đắt đỏ lắm.",
    "STm07_03.35": "Nhưng giờ đã có Hiệp Ước Của Sếp chống lưng, bọn họ không thể muốn làm gì thì làm được nữa.",
    "STm07_03.39": "Anh đã gánh khoản nợ ba mươi tỷ Dorra vì số cổ phần đó, giờ lại còn tham gia đấu thầu. Đúng là liên doanh thật,==W== nhưng chẳng phải mọi rủi ro đều do Hiệp Ước Của Sếp gánh hết sao?",
    "STm07_03.40": "Nếu phi vụ này thành công, chúng ta sẽ giành được sự tin tưởng của cả anh lẫn ngài Đại Thanh Tra.==W== Đối với tương lai của Hiệp Ước Của Sếp,==W== sự hậu thuẫn đó là vô giá.",
    "STm07_03.51": "Xin thứ lỗi vì đã làm phiền, Bạo Quân.==W== Thần có tin quan trọng cần bẩm báo.",
    "STm07_03.52": "Hệ Thống Bồi Dưỡng Bạo Quân Tỉnh Thế đã ban hành mục tiêu mới.==W== Nhiệm vụ thứ hai của người là sở hữu một Cự Thạch.",
    "STm07_03.54": "Không hẳn đâu, Bạo Quân.",
    "STm07_03.58": "Bạo Quân, tôi nhận thấy có sự chuyển biến trong thái độ của người đối với hệ thống và các nhiệm vụ của nó.",
    "STm07_03.81": "Chuẩn rồi. Với tư cách là cổ đông, Hiệp Ước Của Sếp hoàn toàn ủng hộ việc bỏ thầu của Liên Hợp Thu Hoạch chi nhánh Philae.",
    "STm07_03.86": "Có vẻ Đế Quốc Grace đã mở cuộc đấu thầu Cự Thạch này trong thời gian gấp rút,==W== lợi dụng việc đại diện của tất cả các công ty đều đã có mặt ở Philae để dọ thám vụ Darcia.",
    "STm07_03.89": "Đây chẳng phải lần đầu Đế Quốc Grace giở trò như vậy.==W== Cứ ngồi yên nghỉ ngơi đi. Tôi sẽ liên hệ vài đầu mối từ các công ty khác xem moi được gì không.",
    "STm07_04.4": "Trước khi bỏ thầu, Bastelina tóm tắt cho bạn về các đối thủ chính: Tài Chính Biển Sâu, Cận Vệ Hoàng Gia, và Khiên Thanh Không.",
    "STm07_04.27": "Vị phu nhân khoác chiến giáp đằng kia chính là Quý Cô Greyhorn, Đoàn Trưởng Kỵ Sĩ Cận Vệ Hoàng Gia.",
    "STm07_04.29": "Đoàn Trưởng Kỵ Sĩ, Cận Vệ Hoàng Gia",
    "STm07_04.47": "Đó là Mercurio, đại diện duy nhất của Khiên Thanh Không.",
    "STm07_04.49": "Đại Diện Duy Nhất, Khiên Thanh Không",
    "STm07_04.65": "Phù Thủy Phong Đăng Philae, Scarlet Sights",
    "STm07_05_a.15": "Còn về phía bạn, Khiên Thanh Không biết rõ họ không thể thắng nổi bạn và Lữ Đoàn Tân Tinh trong việc cầu nguyện ước nguyện.",
    "STm07_05_a.19": "Hãy đối mặt với sự thật đi Sếp, giờ anh nổi như cồn rồi.==W== Với một mục tiêu lộ liễu như vậy trên lưng, Khiên Thanh Không muốn bám đuôi Hiệp Ước Của Sếp quá là dễ dàng.",
    "STm07_05_b.108": "Vậy nên tôi mới ở lại điều hành công ty. Lữ Đoàn Tân Tinh đã lấy Philae làm căn cứ==RT==và tiếp tục theo đuổi các huyền thoại.",
    "STm07_05_c.70": "Lữ Đoàn... Tân Tinh ư. Tại sao?",
    "STm07_08.84": "Đế Quốc Grace sẽ nhắm mắt làm ngơ trừ khi sự việc leo thang nghiêm trọng. Sự kình địch giữa các công ty hiếm khi diễn ra trong hòa bình—tuốt vũ khí là thủ tục tiêu chuẩn rồi.",
    "STm07_12.121": "Hợp đồng này đảm bảo đơn hàng ngũ cốc trị giá 8 tỷ Dorra từ chi nhánh Philae và Cảng Goldfinch của họ. Khoản tạm ứng 4 tỷ sẽ về tài khoản của chúng ta vào ngày mai.",
    "STm07_14.16": "Chính xác. Đối với một phe thường xuyên chinh chiến như Cận Vệ Hoàng Gia, thanh toán bằng kim cương pha lê thay vì Dorra đúng là một mũi tên trúng hai đích.",
    "STm07_14.77": "Bậy nào! Chúng ta hoàn toàn có thể tìm ra 80 triệu mà!==W== Một nhà sưu tập đã trả giá rất cao cho...",
    "STm07_14.86": "Lữ Đoàn Tân Tinh, ở lại đây. Hãy đảm bảo tiền Dorra thực sự vào tài khoản của chúng ta.",
    "STm07_14.118": "Bạn đã hợp tác với Lữ Đoàn Hoa Lệnh cho các Đại Ủy Thác. Bạn đã ngăn chặn Thực Vật Biến Dị và hạ gục đám cướp đường.",
    "STm07_14.119": "Hiệp Ước Của Sếp hay Khiên Thanh Không ư? Chuyện đó rõ như ban ngày rồi. Này, cầm lấy đi—",
    "STm07_16.99": "Nghĩ lại thì... Nếu lúc đó chúng ta chặn được 80 triệu kia là thắng rồi...==W== Rốt cuộc Giám đốc Viện Thiên Không đang toan tính điều gì chứ?",
    "STm07_16.139": "Bạn đã giải phóng Hiệp Ước Của Sếp huyền thoại. Bạn sở hữu nhiều Phong Ấn Ân Điển, trong đó có một ấn ký thậm chí chưa từng được ghi chép trong sử sách.",
    "STm07_16.146": "Chẳng hạn như,==W== bạn đã khơi mào một cuộc chiến công ty vì Lữ Đoàn Tân Tinh và Bộ Tộc Tàn Phong.==W== Trên thực tế, một khi đã nắm giữ Phong Ấn Ân Điển, bạn hoàn toàn có thể yêu cầu Thương Hội Creta đối đãi tôn trọng với bạn đồng hành của mình chỉ thông qua vài trung gian có thế lực.==W== Nước đi đó thông minh hơn nhiều.",
    "STm08_01.23": "Nghĩa là ngươi đang sợ \"Dũng Giả\"==RT==trong lời tiên tri sẽ hạ gục ngươi chứ gì. Ta nói đúng không hả, Bạo Quân?",
    "STm08_01.78": "Tiểu thư Albedo, tình hình nguy cấp rồi. Khách sạn đang bị bao vây bởi Cận Vệ Bình Minh và Cận Vệ Hoàng Gia. Bên ngoài là các Phán Quan Hoàng Hôn.",
    "STm08_01.82": "Không, đó là một phe phái bí mật bên trong Đế Quốc Grace. Tên chính thức là \"Ủy Ban Đặc Biệt Cứu Rỗi Đại Lục Nova Và Thanh Trừng Bạo Quân\". Sứ mệnh của họ là tiêu diệt Bạo Quân huyền thoại và ngăn chặn ngày tận thế được báo trước trong lời tiên tri.",
    "STm08_01.83": "Được rồi, họ đang truy lùng Bạo Quân huyền thoại chứ đâu phải vị Sếp của Hiệp Ước Của Sếp. Nhưng làm sao chúng ta giết được một huyền thoại cơ chứ?",
    "STm08_01.103": "Còn ngươi, với tư cách là Cận Vệ Bình Minh, sao dám tự ý tấn công Giám Đốc Điều Hành của Hiệp Ước Của Sếp khi chưa được Tứ Đại Khía Cạnh phê chuẩn hả?",
    "STm08_02.3": "Gươm Tuốt Vỏ",
    "STm08_02.13": "Chúng liên tục đổi vị trí để tránh bị khóa mục tiêu. Hừ... Giám Đốc Điều Hành của Hiệp Ước Của Sếp chuẩn bị kỹ lưỡng thật đấy.",
    "STm08_02.29": "Ngươi thì biết cái gì! Sách Tiên Tri Grace không bao giờ sai. Bạo Quân phải bị xử tử vì sự tồn vong của toàn thể người dân Novian—",
    "STm08_02.69": "Lại bắt đầu rồi đấy... Vẫn là bài ca tiên tri muôn thuở. Sự diệt vong của Nova chỉ là mực in trên giấy thôi. Sao các người cứ phải bám riết lấy nó thế?",
    "STm08_02.98": "Cô ấy giấu nhẹm chuyện đó với tất cả mọi người trong Viện Thiên Không, bao gồm cả tôi. Thông báo đó==RT==từ trên trời rơi xuống, khiến chúng tôi trở tay không kịp để chuẩn bị hội trường.",
    "STm08_02.120": "Cô ấy làm theo Sách Tiên Tri Grace đến từng câu từng chữ và lần theo mọi dấu vết của Bạo Quân.",
    "STm08_02.121": "Tôi chẳng tin vào mấy truyền thuyết hay lời tiên tri nhảm nhí, và tôi cũng chịu không biết làm sao mà Giám đốc Angie lại đi đến kết luận rằng anh là Bạo Quân...",
    "STm08_03.79": "Chà, dùng danh xưng \"<color=#bd3059>Sếp</color>\" có vẻ phù hợp hơn trong các công việc chính thức, xét đến vị trí của chúng tôi là nhân viên của \"Hiệp Ước Của Sếp\".",
    "STm08_03.95": "Giám Đốc Điều Hành của Hiệp Ước Của Sếp",
    "STm08_03.114": "Tôi là chính tôi,==W== một Lữ Khách đã cùng mọi người sát cánh bảo vệ Philae,==W== và là Giám Đốc Điều Hành của Hiệp Ước Của Sếp.==W==",
    "STm08_03.118": "Dù sao đi nữa, tôi cũng chỉ mang danh xưng Sếp thôi,==W== chứ chẳng phải tên bạo quân tận thế nào trong lời tiên tri đâu.==W==",
    "STm08_03.151": "Với tất cả sự tôn kính, tôi xin đính chính nhận định vô lý đó. Sách Tiên Tri Grace là thánh điển do chư Thần ban tặng. Lời trong kinh mang chân lý tuyệt đối.",
    "STm08_03.153": "Phán Quan Hoàng Hôn muốn thay mặt Đế Quốc Grace tiến hành một cuộc điều tra chính thức để xác minh thân phận Bạo Quân trong lời tiên tri của người. Xin hãy yên tâm, cuộc điều tra sẽ diễn ra hoàn toàn khách quan và công bằng.",
    "STm08_03.156": "Theo Sách Tiên Tri Grace, Bạo Quân có thực, và sự tồn tại của kẻ đó đe dọa đến chính vận mệnh của toàn bộ Nova.",
    "STm08_04.14": "Hahaha... Lũ già các người suốt ngày tụng niệm cầu nguyện, giờ đến đầu óc cũng mụ mẫm rồi. Đang tự biến mình thành trò cười đấy.==W== Nói thật đi, thời buổi này còn ai tin vào cuốn Sách Tiên Tri Grace cổ lỗ sĩ đó nữa chứ?",
    "STm08_04.42": "\"Giám Đốc Viện Thiên Không Angie Cảnh Báo Về Tận Thế Sắp Giáng Xuống! Thề Sẽ Tiêu Diệt Bạo Quân Tà Ác Đằng Sau Hiệp Ước Của Sếp!\"==W== Mistique,==W== bài báo nhảm nhí kiểu gì thế này?!",
    "STm08_04.62": "Yên tâm đi Sếp.==W== Tôi sẽ tuân thủ nghiêm ngặt quy tắc của Đế Quốc Grace và quyền hạn của mình, tuyệt đối không tiến hành bất kỳ hành động tấn công nào. Phân tích của tôi sẽ chỉ dựa trên thông tin công khai,==W== và tôi sẽ không đếm xỉa gì đến Sách Tiên Tri Grace.",
    "STm08_04.108": "Nhưng không cần phải lo lắng đâu.==W== Gia Chính Cốc Phong luôn hợp tác chặt chẽ với cả Liên Hợp Thu Hoạch Philae và Hiệp Ước Của Sếp. Dù trong hoàn cảnh nào chúng tôi cũng sẽ đứng về phía anh.",
    "STm08_04.109": "(Chỉ có kẻ ngốc mới tin vào loại tin đồn thất thiệt đó.==W== Hơn nữa,==W== chừng nào chưa tìm ra tung tích của Otoha, tôi vẫn cần Hiệp Ước Của Sếp duy trì hoạt động bình thường.)",
    "STm08_05.98": "Được rồi...==W== Nazuna, tôi giao lại mọi chuyện cho cô nhé...==W== À không, từ giờ tôi phải gọi cô là Sếp mới đúng.==W== Tôi chính thức bổ nhiệm cô làm Giám Đốc Điều Hành của Hiệp Ước Của Sếp trong thời gian tôi vắng mặt.",
    "STm08_10.64": "Hơn nữa, trượt kỳ thi đó mới là lý do tôi gia nhập Hiệp Ước Của Sếp. Ước mơ trở thành nhân viên công ty của tôi rốt cuộc cũng thành hiện thực rồi mà!==W== Việc bỏ lỡ bài kiểm tra đó hẳn là sự an bài của Thần Ân Điển."
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

    # 5. Core Factions, Lore, and Royal/Treaty Terms
    rules = [
        # Boss Accord -> Hiệp Ước Của Sếp
        (r'\b(?:Giám đốc điều hành|CEO)\s+của\s+(?:Sếp Accord|Hiệp Ước Của Sếp)\b', 'Giám Đốc Điều Hành của Hiệp Ước Của Sếp'),
        (r'\b(?:Sếp Accord|Hiệp định ông chủ|Hiệp định của sếp|Hiệp định Boss|Hiệp ước Boss|Boss Accord)\b', 'Hiệp Ước Của Sếp'),
        (r'\bphi hành đoàn\b(?=.*(?:Hiệp Ước Của Sếp|của mình|của tôi))', 'anh em'),

        # New Star Guild -> Lữ Đoàn Tân Tinh
        (r'\b(?:Hội Ngôi Sao Mới|Bang hội Ngôi sao Mới|Hiệp hội Ngôi sao Mới|Hội Ngôi sao Mới|Bang Hội Ngôi Sao Mới|Công Hội Tân Tinh|New Star Guild)\b', 'Lữ Đoàn Tân Tinh'),

        # Imperial Guard -> Cận Vệ Hoàng Gia
        (r'\bKnight Commander(?:,\s*|\s+of\s+the\s+)Imperial Guard\b', 'Đoàn Trưởng Kỵ Sĩ Cận Vệ Hoàng Gia'),
        (r'\bChỉ huy Hiệp sĩ,\s*(?:Vệ binh Hoàng gia|Cận Vệ Hoàng Gia)\b', 'Đoàn Trưởng Kỵ Sĩ, Cận Vệ Hoàng Gia'),
        (r'\b(?:Kỵ Sĩ Hoàng Gia|Vệ binh hoàng gia|Vệ binh Hoàng gia|Lực lượng Vệ binh Hoàng gia|Lực lượng bảo vệ hoàng gia|Đội cận vệ Hoàng gia|Đội cận vệ hoàng gia|Imperial Guard|The Imperial Guard|Imperial Guards)\b', 'Cận Vệ Hoàng Gia'),

        # Tyrant -> Bạo Quân
        (r'\bHệ thống bồi dưỡng bạo chúa\b', 'Hệ Thống Bồi Dưỡng Bạo Quân'),
        (r'\bHệ Thống Bồi Dưỡng Bạo Chúa\b', 'Hệ Thống Bồi Dưỡng Bạo Quân'),
        (r'\b(?:Bạo chúa|bạo chúa|Bạo Chúa|kẻ bạo chúa|Kẻ bạo chúa)\b', 'Bạo Quân'),
        (r'\btên bạo chúa\b', 'kẻ Bạo Quân'),

        # Grace Imperium -> Đế Quốc Grace
        (r'\b(?:Đế chế Grace|Grace Đế Quốc|Grace Imperium)\b', 'Đế Quốc Grace'),
        (r'\bĐế quốc Grace\b', 'Đế Quốc Grace'),

        # Omnisky Aegis -> Khiên Thanh Không
        (r'\b(?:Omnisky Aegis|Aegis toàn cảnh|Aegis Bầu Trời)\b', 'Khiên Thanh Không'),

        # Grace Divisions & Institutions
        (r'\b(?:Sky Institute|Học Viện Sky|Viện Sky|Viện Bầu trời|Viện Bầu Trời)\b', 'Viện Thiên Không'),
        (r'\b(?:Eye of Grace|Con mắt Ân điển|Con mắt ân sủng|Grace Eye)\b', 'Quang Nhãn Grace'),
        (r'\b(?:Soul Shop|Soul Cửa Hàng|Cửa hàng Soul)\b', 'Cửa Hàng Linh Hồn'),
        (r'\b(?:Sentinels of Dawn|Sentinel of Dawns|Sentinel of Dawn)\b', 'Cận Vệ Bình Minh'),
        (r'\b(?:Dusk Arbiters?)\b', 'Phán Quan Hoàng Hôn'),
        (r'\b(?:Tetrad Aspects?)\b', 'Tứ Đại Khía Cạnh'),

        # Book of Grace Prophecies -> Sách Tiên Tri Grace
        (r'\b(?:Sách Tiên tri Ân điển|Sách Tiên tri về Ân điển|Sách Ân điển|Book of Grace Prophecies)\b', 'Sách Tiên Tri Grace'),
        (r'\bLời tiên tri về Sách Ân điển\b', 'Lời tiên tri trong Sách Tiên Tri Grace'),

        # Seal of Grace -> Phong Ấn Ân Điển
        (r'\b(?:Seal of Grace|Dấu ấn ân sủng|Ấn Ân Ân Sủng|Ấn Tín Ân Sủng)\b', 'Phong Ấn Ân Điển'),

        # Monolith -> Cự Thạch / Cự Tháp
        (r'\b(tảng|khối|những khối|các khối)\s*đá\s*nguyên\s*khối\b', 'Cự Thạch'),
        (r'\bđá\s*nguyên\s*khối\b', 'Cự Thạch'),
        (r'\bThành phố Ngàn (?:khối đá nguyên khối|Cự Tháp|Cự Thạch|khối đá)\b', 'Thành Phố Ngàn Cự Thạch'),
        (r'\bThành phố của một ngàn Cự Thạch\b', 'Thành Phố Ngàn Cự Thạch'),

        # Idioms & Dialogues Polish
        (r'\bgiết chết hai con chim bằng một viên đá\b', 'một mũi tên trúng hai đích'),
        (r'\btấn công vào tài khoản\b', 'vào tài khoản'),
        (r'\bđến từng bức thư\b', 'đến từng câu từng chữ'),
        (r'\bTại Daggers Drawn\b', 'Gươm Tuốt Vỏ'),
        (r'\bGrand Commission\b', 'Đại Ủy Thác'),
        (r'\bngười Dân Người Novian\b', 'người dân Novian'),
        (r'\bDân Người Novian\b', 'dân Novian'),
        (r'\b(?:Cây thông minh|Nhà máy thông minh)\b', 'Thực Vật Biến Dị'),
        (r'\bhành động xúc phạm\b(?=.*(?:quyền hạn|chỉ dựa trên|quy tắc))', 'hành động tấn công'),
        (r'\bxe tải Artifact\b', 'chiếc xe Cổ Vật'),
        (r'\bxe Artifact\b', 'xe Cổ Vật'),
        (r'\bB-Bull!\b', 'Nhảm nhí!'),
        (r'\bJing\'s Bistro\b', 'Quán Ăn Jing'),
        (r'\b[Bb]ạn có sao chép không[\s?!]*', 'Bạn có nghe rõ không!?'),
        (r'\b[Bb]ạn sao chép không[\s?!]*', 'Bạn có nghe rõ không!?'),
        (r'\b[Cc]ó sao chép không[\s?!]*', 'Nghe rõ không!?'),
        (r'\bsao chép không[\s?!]*', 'nghe rõ không!?'),
        (r'\bTôi nghe thấy bạn\b', 'Tôi nghe rõ rồi'),
        (r'\bnghe thấy bạn\b', 'nghe thấy cậu'),
        (r'\bngười đi bộ\b', 'Lữ Khách'),
        (r'\bnhững người đi bộ\b', 'các Lữ Khách'),
        (r'\bkẻ thù\b', 'kẻ địch'),
        (r'\bSơ Quang\b', 'Khải Minh'),
        (r'\bFirstlight Noya\b', 'Noya - Khải Minh'),

        # Punctuation & spaces
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

    # Clean up excessive spaces around dialogue tags while preserving tokens
    text = re.sub(r'(\S)\s+(==[A-Z0-9_]+==)', r'\1\2', text)
    text = re.sub(r'(==[A-Z0-9_]+==)\s+(\S)', r'\1\2', text)
    text = re.sub(r'[ \t]{2,}', ' ', text).strip(" \t\r\n")

    # Final token safety fallback
    if not is_valid_token_preservation(orig, text):
        raw_safe = unshield_tokens(trans, tok_list) if has_tokens else trans
        if is_valid_token_preservation(orig, raw_safe):
            return raw_safe
        return orig

    return text

def main():
    print("=" * 75)
    print("Senior Translator 2 (Batch 3 - Part B): Main Story Chapters 7 & 8")
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

    for str_key, str_val in data.items():
        if not str_val or not str_val.strip():
            final_translated[str_key] = str_val
            continue
        raw_trans = cache.get(str_val, str_val)
        polished = polish_partB_line(str_key, str_val, raw_trans, terms, forbidden)
        final_translated[str_key] = polished
        valid_count += 1
        if is_valid_token_preservation(str_val, polished):
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
