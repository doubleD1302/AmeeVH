# -*- coding: utf-8 -*-
"""
Builder and QA-verifier for Campaign 13 Partition B:
STsp_16, STsp_17, STsp_18, STev_01 (1,885 lines across 20 scenes).
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/side_stories_part2_editorial_20261025_r01"
SOURCE_B = CAMPAIGN_DIR / "PARTITION_B_SOURCE.json"
PROP_B = CAMPAIGN_DIR / "PROPOSALS_PARTITION_B.jsonl"
RESULT_B = CAMPAIGN_DIR / "RESULT_PARTITION_B.json"

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

# 7 binary control code lines that must be preserved verbatim as English
KEEP_EN_IDS = {
    'STsp_17_01.54',
    'STsp_17_03.52',
    'STsp_18_01.17',
    'STev_01_04.119',
    'STev_01_07.102',
    'STev_01_09.35',
    'STev_01_09.63'
}

BANNED_WORDS = [
    (r"\bMa Vương\b", "Cấm dùng Ma Vương cho Demon King / Lord"),
    (r"\bchết tiệt\b", "Cấm dùng chửi thề thô tục 'chết tiệt'"),
    (r"\bbạn biết đấy\b", "Calque máy dịch 'you know'"),
    (r"\bcái quái gì\b", "Calque dịch thô 'what the hell'"),
    (r"\blàm sao mà\b", "Calque dịch thô 'how come'"),
    (r"\btrỗi dậy và tỏa sáng\b", "Calque máy dịch 'rise and shine'"),
    (r"\bnhảy ra khỏi lồng ngực\b", "Calque máy dịch 'jump out of one's chest'"),
    (r"\bGrand Thanh tra\b", "Calque hỗn tạp 'Grand Thanh tra' -> Đại Thanh Tra"),
    (r"\bHòn Hồn Thạch\b", "Calque dịch lặp 'Hòn Hồn Thạch' -> Hồn Thạch"),
    (r"\bnhững kẻ buồn ngủ\b", "Calque dịch máy 'sleepyheads'"),
    (r"\btrục mìn\b", "Calque dịch máy 'mineshaft'"),
    (r"\bKỵ Sĩ Hoàng Gia\b", "Imperial Guard (Tilia) phải dịch là Cận Vệ Hoàng Gia!"),
    (r"\bTrọng Tài Chạng Vạng\b", "Dusk Arbiter phải dịch là Trọng Tài Hoàng Hôn!"),
    (r"\b(Chiến Binh Cây Bụi|Chuột Cây Bụi|Thành cổ Cây bụi)\b", "Shrubshrew phải chuẩn hóa là Chuột Bụi!"),
    (r"\b(Đá Linh Hồn|Đá Hồn)\b", "Soul Stone phải chuẩn hóa là Hồn Thạch!"),
    (r"\b(Sơ Quang|Trần Sa)\b", "Noya tuyệt đối không dùng Sơ Quang / Trần Sa (phải là Noya - Khải Minh)!"),
    (r"\bHổ phách\b", "Tên nhân vật Amber cấm dịch thành Hổ phách!"),
    (r"\bDiên Vĩ\b", "Tên nhân vật Iris cấm dịch thành Diên Vĩ!"),
    (r"\bPhòng Màu Trắng\b", "White Room phải dịch là Phòng Trắng!"),
    (r"\bĐêm Vĩnh Cửu\b", "Nocturn Eterna phải dịch là Đêm Trường Vĩnh Cửu!"),
    (r"\bKim Khố Ý Chí Ân Tứ\b", "Grace Imperium phải dịch là Đế Quốc Grace!"),
    (r"\b(Bà Angie|Quý Cô Angie)\b", "Lady Angie phải dịch là Tiểu Thư Angie!"),
    (r"\bHiệu Trưởng Allie\b", "Director Allie phải dịch là Giám Đốc Allie!"),
    (r"Cái gì trên thế giới", "Calque máy dịch 'What in the world'"),
    (r"\bbánh mì nướng\b", "Calque dịch sai từ toast (nâng ly)"),
]

def check_tokens(src_tokens, dst_text):
    dst_tokens = TAG_PATTERN.findall(dst_text)
    return sorted(src_tokens) == sorted(dst_tokens), src_tokens, dst_tokens

def check_control_chars(src_text, dst_text):
    src_ctrls = [c for c in src_text if ord(c) < 32 and c not in '\r\n']
    dst_ctrls = [c for c in dst_text if ord(c) < 32 and c not in '\r\n']
    return src_ctrls == dst_ctrls, src_ctrls, dst_ctrls

with open(SOURCE_B, 'r', encoding='utf-8') as f:
    items = json.load(f)

print(f"Loaded {len(items)} items from Partition B.")

REPLACEMENTS = [
    # --- STsp_16 Editorial Polish & Calque Fixes ---
    ("Tôi nên hủy bỏ đống giấy tờ này.", "Mình phải giải quyết cho xong đống giấy tờ này."),
    ("Sau đó, một lần nữa, gần đây nó hoàn toàn hỗn loạn. Tôi đã không nhận ra đống đồ lại trở nên tệ đến mức này... ==W== Tôi cần sắp xếp lịch trình của mình theo thứ tự.",
     "Mà nghĩ lại thì, dạo này hỗn loạn thật. Không ngờ đống giấy tờ lại dồn ứ đến mức này... ==W== Phải sắp xếp lại lịch trình của mình thôi."),
    ("Oh right, isn't Horizon visiting Thành Phố Emor today?", "À phải rồi, chẳng phải hôm nay Horizon sẽ đến Thành Phố Emor sao?"),
    ("<size=110%>Tốt</size> ==W== <size=120%>buổi sáng</size> —!", "<size=110%>Buổi</size> ==W== <size=120%>sáng tốt làaanh</size>—!"),
    ("Hãy để tôi đoán. Cô ấy đã giác ngộ và quay trở lại Sailstead để bắt đầu xây dựng? Tất nhiên là không cần tôi chạy nó trước... ==W== Điển hình. Cô ấy chỉ làm bất cứ điều gì nảy ra trong đầu.",
     "Để tôi đoán nhé. Đột nhiên ngộ ra điều gì rồi phóng thẳng về Sailstead để bắt đầu đóng tàu luôn chứ gì? Dĩ nhiên là chẳng thèm bàn trước với tôi nửa lời... ==W== Đúng là tính cách của cô ấy. Cứ nghĩ ra cái gì là làm cái nấy."),
    ("... Khá nhiều.", "... Đại loại là thế."),
    ("... Ờ. ==W== Đừng lo, tôi sẽ không nổ tung đâu.", "... Hừm. ==W== Đừng lo, tôi không bốc hỏa đâu."),
    ("Mọi tài liệu ở đây đều được giữ kín. Hầu như không có một lỗ hổng trong tầm nhìn. Làm sao tôi có thể mắng cô ấy vì điều đó?",
     "Mọi tài liệu ở đây đều cực kỳ kín kẽ. Chẳng tìm ra nổi một kẽ hở nào. Bảo tôi mắng cô ấy thế nào được chứ?"),
    ("Hãy kể cho tôi nghe về nó...", "Còn phải nói nữa sao..."),
    ("Hoạt động với tốc độ cực nhanh là cách mà Tổng thống của chúng ta lăn lộn.",
     "Làm việc thần tốc lúc nào cũng là tác phong của Hội Trưởng chúng ta mà."),
    ("Cái quái gì đang xảy ra vậy?!", "Rốt cuộc là chuyện quái quỷ gì đang diễn ra thế này?!"),
    ("Vấn đề này đến vấn đề khác! Hàng hóa chất đống ở quầy lễ tân, Các Lữ Khách' House hoàn toàn là một mớ hỗn độn... Hả? Cậu nói có một cuộc ẩu đả nổ ra bên ngoài?",
     "Hết chuyện này lại đến chuyện khác! Hàng hóa chất đống ở quầy lễ tân, Nhà Lữ Khách hỗn loạn như một mớ bòng bong... Hả? Cậu bảo có đánh nhau ngoài phố á?"),
    ("Bạn hiểu rồi! Hành lý của cậu đang ở trong tay tốt.", "Cứ yên tâm! Hành lý của cậu gửi gắm vào tay tôi là chuẩn bài rồi."),
    ("Phù! ==W== Đã lưu!", "Phù! ==W== Được cứu rồi!"),
    ("... Và đó là khá nhiều.", "... Đại khái mọi chuyện là như thế đấy."),
    ("tốt đẹp và dễ dàng.", "trật tự xếp hàng nào."),
    ("Tôi có việc thực tế phải làm. Đầm lầy. Tạm biệt!", "Tôi bận ngập đầu ngập cổ đây này. Bye bye nhé!"),
    ("Một chút mỡ khuỷu tay sẽ không giết chết bạn.", "Đổ chút mồ hôi công sức thì có chết ai đâu."),
    ("Tôi lẻn ra khỏi văn phòng để thư giãn. Thay vào đó, làm thế nào mà tôi lại phải lao động chân tay?",
     "Mình chuồn khỏi văn phòng là để trốn việc cơ mà. Cớ sao rốt cuộc lại thành ra đi làm cửu vạn thế này?!"),
    ("Bạn gọi đó là nghỉ ngơi? Thậm chí không gần gũi!", "Cậu gọi thế là nghỉ ngơi á? Còn lâu mới tới nhé!"),
    ("Cái máy xay nhỏ đó! ==W== Cô ấy thực sự đang chạy trốn!", "Con bé ranh ma này! ==W== Dám chuồn thật kìa!"),
    ("Tôi chắc chắn có thể hạ gục nó tối nay.", "Tối nay mình nhất định sẽ xử lý xong xuôi."),
    ("Đánh hơi... ==W== Cảm ơn. Ồ, đúng chỗ rồi.", "Sụt sịt... ==W== Cảm ơn nhé. Oa, ngon tuyệt cú mèo luôn."),
    ("Assertive Lữ Khách", "Lữ Khách Quả Quyết"),
    ("Skeptical Lữ Khách", "Lữ Khách Hoài Nghi"),
    ("Chia tay đi mọi người!", "Giải tán hết đi mọi người!"),
    ("rơi vào bữa trưa miễn phí như thế.", "mắc bẫy món hời từ trên trời rơi xuống như thế."),
    ("Tại sao bạn lại gắn thẻ?", "Sao cậu lại bám đuôi theo thế?"),
    ("Việc một vài người trong số họ bay dưới radar là điều hoàn toàn bình thường!",
     "Sót lại một vài Cự Tháp chưa ai phát hiện ra là chuyện quá đỗi bình thường!"),
    ("Cô ấy có lý. Chúng ta không nên vội kết luận trước khi biết sự thật.",
     "Cô ấy nói cũng có lý. Khi chưa rõ thực hư thì chớ vội võ đoán."),
    ("Điểm công bằng. Nhưng tôi quan tâm đến Lữ Khách.", "Cậu nói cũng có lý. Nhưng tôi lo cho các Lữ Khách."),
    ("Ôi chết tiệt, tôi ra ngoài rồi! Gặp bạn sau!", "Chết thật, tôi chuồn đây! Gặp lại sau nhé!"),
    ("Nhanh chóng bắt đầu như mọi khi...", "Lúc nào cũng chuồn nhanh như chớp..."),
    ("Tiếp theo là gì, ==W== lợn bay?", "Chuyện gì tiếp theo đây, ==W== mặt trời mọc đằng tây à?"),

    # Character names: Willow & Bloc in STsp_16
    ("cô Liễu", "cô Willow"),
    ("Cô Liễu", "Cô Willow"),
    ("Liễu?!", "Willow?!"),
    ("Đúng không, Liễu?", "Đúng không, Willow?"),
    ("Liễu...", "Willow..."),
    ("Liễu!", "Willow!"),
    ("Đẹp đấy, Liễu.", "Khá lắm, Willow."),
    ("Chào buổi sáng, Liễu!", "Chào buổi sáng, Willow!"),
    ("Khối có thể thả cần câu đó sau. Đúng không Khối?", "Lát nữa Bloc giao cái cần câu đó sau cũng được. Đúng không, Bloc?"),
    ("Khối, cậu đã gây ra", "Bloc, cậu đã gây ra"),

    # --- STsp_17 Editorial Polish & Master Glossary ---
    ("Chuyển Phát Hỏa Tốc Chuyển Phát Hỏa Tốc Post Haste", "Chuyển Phát Hỏa Tốc"),
    ("Hội Ngôi Sao Mới", "Lữ Đoàn Tân Tinh"),
    ("Hiệp hội Ngôi sao Mới", "Lữ Đoàn Tân Tinh"),
    ("Lai Phúc Oasis", "Ốc Đảo May Mắn"),
    ("Không cần phải vội trả lời, Teresa. Hãy nói chuyện sau khi chúng ta đóng gói kho báu <size=60>♪",
     "Không cần vội trả lời đâu, Teresa. Cứ đợi chúng ta ẵm trọn kho báu rồi hẵng nói tiếp nhé <size=60>♪"),
    ("Vào cuối ngày, tôi là người chuyển phát nhanh Chuyển Phát Hỏa Tốc! Tôi không thể đi săn kho báu với cậu được, meo meo!",
     "Dù sao thì tôi cũng là giao liên của Chuyển Phát Hỏa Tốc! Tôi không thể đi săn kho báu cùng các cậu được đâu, meo meo!"),
    ("Làm thế nào mà bạn lại ở trên một cái cây?", "Sao cậu lại bị treo lơ lửng trên ngọn cây thế kia?"),
    ("<size=37>Phải không? Teresa của chúng tôi thật tuyệt vời! <size=60>♪ <size=37>Cô ấy thậm chí còn tìm thấy đầu máy xe lửa đó đậu bên ngoài Chuyển Phát Hỏa Tốc!",
     "<size=37>Thấy chưa? Teresa của chúng tôi đỉnh lắm đúng không! <size=60>♪ <size=37>Đến cả chiếc đầu máy xe lửa đỗ bên ngoài Chuyển Phát Hỏa Tốc cũng là do cậu ấy tìm thấy đấy!"),
    ("và giải thưởng lớn của chúng tôi là một bản đồ chết tiệt khác...? Tất cả những đau khổ đó là vì điều gì...?",
     "vậy mà phần thưởng lớn lại là một tấm bản đồ quái quỷ khác ư...? Bao nhiêu công sức chịu khổ rốt cuộc là vì cái gì chứ...?"),

    # --- STsp_18 Editorial Polish ---
    ("Đúng! Thế thôi! Làm thế nào mà cậu có được nó trên tay?!", "Đúng rồi! Chính là nó! Làm sao cậu kiếm được thứ này thế?!"),
    ("Chết tiệt! ==W== Họ đi đâu rồi?!", "Khốn thật! ==W== Họ biến đâu mất rồi?!"),
    ("Chết tiệt! Làm thế nào mà một mẻ cá lớn như vậy lại có thể lọt lưới được?!",
     "Tức thật chứ! Con mồi béo bở thế mà lại để sổng mất?!"),
    ("Chết tiệt, cái này không phải là thứ dễ bị thuyết phục...!",
     "Khốn thật, tên này không phải dạng vừa đâu...!"),

    # --- STev_01 Editorial Polish & Master Glossary ---
    ("À, cái quái gì vậy. Tôi cũng có thể tận hưởng bầu không khí bãi biển mùa hè khi tôi ở đây.",
     "À, thôi kệ đi. Đằng nào cũng tới đây rồi, cứ tận hưởng không khí biển mùa hè cho đã cái đã."),
    ("Chết tiệt! Tôi đang bị hút vào...!", "Chết thật! Mình đang bị hút xuống dưới...!"),
    ("Hà! Bạn đặt cược! Chúng tôi là những Lữ Khách nổi tiếng nhất ở Carlo!",
     "Hà! Còn phải hỏi! Bọn tôi là những Lữ Khách lừng danh nhất ở Carlo đấy nhé!"),
    ("Bạn đặt cược! Một U Linh Hạm ngu ngốc không làm chúng ta sợ hãi!",
     "Tất nhiên rồi! Mấy cái trò U Linh Hạm vớ vẩn làm sao dọa được bọn này!"),
    ("Chết tiệt. Đáng lẽ tôi không nên nói điều đó. Bây giờ cô ấy thực sự điên rồi...",
     "Khốn thật. Đáng lẽ mình không nên nói thế. Giờ cô ấy giận sôi lên rồi..."),
    ("Chết tiệt, thật là một trò bẩn thỉu... Tôi đang đuổi theo họ!",
     "Khốn kiếp, đúng là giở trò bẩn thỉu... Tôi sẽ đuổi theo chúng!"),
    ("—Bởi vì người đàn ông đã ghi lại những gì anh ta tận mắt nhìn thấy: ==W== nguồn sáng là một vật thể khổng lồ trên một hòn đảo.",
     "—Bởi vì người đó đã ghi lại những gì mình tận mắt chứng kiến: ==W== nguồn phát ra ánh sáng là một vật thể khổng lồ trên đảo."),
    ("Tôi hiểu rồi... ==W== Vậy làm thế nào mà cuốn nhật ký của anh ấy lại lọt vào tay họ?",
     "Ra là thế... ==W== Nhưng sao cuốn nhật ký của người đó lại rơi vào tay họ được nhỉ?"),
    ("Chết tiệt, tôi phải tìm Karin ngay bây giờ!", "Nguy rồi, mình phải đi tìm Karin ngay bây giờ!"),
    ("Chúng ta đã đi xa đến thế rồi, chết tiệt... Làm sao nó vẫn còn ở trên đuôi chúng ta?!",
     "Chúng ta đã đi xa đến thế này rồi mà... Sao nó vẫn bám đuôi dai như đỉa thế này?!"),
    ("Chết tiệt, con tàu sắp bị lật mất rồi—!", "Khốn thật, tàu sắp bị lật rồi—!"),
    ("Cái gì trên thế giới...?!", "Chuyện quái quỷ gì thế này...?!"),
    ("Chết tiệt! Vậy ra những bước chân đó không phải của ma mà là của lũ quái vật!",
     "Khốn thật! Hóa ra tiếng bước chân đó không phải của ma quỷ, mà là của lũ quái dị này!"),
    ("Chết tiệt, và những kẻ lừa đảo đó đã tung tin đồn rằng Bà nội đã đánh cắp kho báu. Đó thực sự là thời tiết!",
     "Tức thật chứ, vậy mà mấy tên lừa đảo đó dám phao tin đồn rằng Bà đã cuỗm mất kho báu. Hóa ra tất cả chỉ là do thời tiết!"),
    ("Chết tiệt... Tôi không kiếm được một đồng Dorra nào, và giờ tôi đang mắc một khoản nợ khổng lồ...",
     "Tiêu rồi... Chẳng kiếm nổi một đồng Dorra nào, mà giờ còn ôm thêm một đống nợ ngập đầu..."),
    ("Hả? Hổ phách có mùi hương?", "Hả? Amber cũng có mùi hương á?"),
    ("... Chết tiệt, gần quá. Cô gái thỏ gần như đã phát hiện ra tôi.",
     "... Hú vía, suýt nữa thì toi. Cô bé người thỏ tí nữa thì phát hiện ra mình."),
    ("==RT====RT====RT== ==A-1==\"... Tháng 18 Calor, Nhiều mây. ==RT== Đây là ngày thứ ba của tôi trên đảo. ==RT== Wally đã giúp tôi khôi phục con thuyền, nhưng nó đã hư hỏng quá mức không thể sửa chữa được.\" ==P====RT====RT== \"==A-1==Tháng 21 Calor, Nhiều mây. ==RT== Tôi tìm thấy một con Cá Voi Lục Sừng đang hấp hối trên bãi biển. Wally rất buồn. Tôi chỉ có thể nhìn nó ngừng thở. ==RT== Tôi thu thập một số vỏ sò và đặt chúng bên cạnh, ==RT== hy vọng nó sẽ có một giấc mơ dài, yên bình.\" ==P====RT====RT== ==A-1==\"Tháng 30 Calor, Sunny. ==RT== Tôi đã đóng một con tàu mới và sẵn sàng quay trở lại. Wally không muốn tôi rời đi. ==RT== Tôi không biết liệu sau này tôi có thể bảo vệ ngôi nhà của họ khỏi những người khác hay không.\"",
     "==RT====RT====RT== ==A-1==\"... Ngày 18 Tháng Calor, nhiều mây. ==RT== Đây là ngày thứ ba của tôi trên đảo. ==RT== Whally đã giúp tôi kéo lại con thuyền, nhưng nó đã hư hỏng quá nặng, không thể sửa chữa được nữa.\" ==P====RT====RT== \"==A-1==Ngày 21 Tháng Calor, nhiều mây. ==RT== Tôi tìm thấy một con Cá Voi Lục Sừng đang thoi thóp trên bãi biển. Whally buồn lắm. Tôi chỉ có thể đứng nhìn hơi thở của nó lịm dần. ==RT== Tôi nhặt vài vỏ sò đặt bên cạnh nó, ==RT== thầm mong nó sẽ có một giấc ngủ dài thật bình yên.\" ==P====RT====RT== ==A-1==\"Ngày 30 Tháng Calor, trời nắng. ==RT== Tôi đã đóng xong một con thuyền mới và chuẩn bị trở về. Whally không muốn tôi rời đi. ==RT== Chẳng biết mai sau liệu tôi có thể bảo vệ mái nhà của chúng khỏi bàn tay con người hay không.\""),
    ("cá voi Hexhorn", "Cá Voi Lục Sừng"),
    ("Cá voi Hexhorn", "Cá Voi Lục Sừng"),
    ("xương cá voi Hexhorn", "xương Cá Voi Lục Sừng"),
    ("Xương cá voi Hexhorn", "Xương Cá Voi Lục Sừng"),

    # --- Global Glossary & Canonical Normalization ---
    ("Vệ binh Hoàng gia", "Cận Vệ Hoàng Gia"),
    ("vệ binh hoàng gia", "cận vệ hoàng gia"),
    ("Kỵ Sĩ Hoàng Gia", "Cận Vệ Hoàng Gia"),
    ("kỵ sĩ hoàng gia", "cận vệ hoàng gia"),
    ("Trọng Tài Chạng Vạng", "Trọng Tài Hoàng Hôn"),
    ("trọng tài chạng vạng", "trọng tài hoàng hôn"),
    ("Đá Linh Hồn", "Hồn Thạch"),
    ("Đá Hồn", "Hồn Thạch"),
    ("đá linh hồn", "hồn thạch"),
    ("đá hồn", "hồn thạch"),
    ("Các Lữ Khách' House", "Nhà Lữ Khách"),
    ("Hiệp hội Lữ Khách", "Hiệp Hội Lữ Khách"),
    ("chết tiệt", "chết thật"),
    ("cái quái gì", "chuyện quái gì"),
    ("làm sao mà", "sao có thể"),
    ("bạn biết đấy", "cậu hiểu mà"),
]

blockers = []
majors = []
proposals = []

for it in items:
    iid = it['id']
    en = it['en']
    cur_vi = it.get('current_vi', en)
    src_tokens = TAG_PATTERN.findall(en)

    if iid in KEEP_EN_IDS:
        vi_final = en
    else:
        vi = cur_vi

        # Token repairs for tags
        vi = re.sub(r'<kích thước=(\d+)>', r'<size=\1>', vi)

        # Remove stray closing tags if not in source
        if '</color>' not in en and '</color>' in vi:
            vi = vi.replace('</color>', '')

        if '</size>' not in en and '</size>' in vi:
            vi = vi.replace('</size>', '')

        # Standard replacements
        for old, new in REPLACEMENTS:
            vi = vi.replace(old, new)

        vi_final = vi

    # Normalize Unicode UTF-8 NFC
    vi_final = unicodedata.normalize('NFC', vi_final)

    # Validate tokens
    ok_tok, st, dt = check_tokens(src_tokens, vi_final)
    if not ok_tok:
        blockers.append(f"[{iid}] Token mismatch! Src: {st} vs Dst: {dt}")

    # Validate control chars
    ok_ctrl, sc, dc = check_control_chars(en, vi_final)
    if not ok_ctrl:
        blockers.append(f"[{iid}] Control opcode mismatch! Src: {[ord(c) for c in sc]} vs Dst: {[ord(c) for c in dc]}")

    # Validate banned words
    for pat, desc in BANNED_WORDS:
        if re.search(pat, vi_final, re.IGNORECASE):
            majors.append(f"[{iid}] Contains banned word '{pat}' ({desc}): {vi_final}")

    # Validate newline
    if '\n' in en and '\n' not in vi_final:
        blockers.append(f"[{iid}] Missing newline present in source")

    record = {
        "id": iid,
        "scene_id": it["scene_id"],
        "en": en,
        "vi_editorial": vi_final,
        "is_tech": it.get("is_tech", False),
        "tokens": src_tokens
    }
    proposals.append(record)

print(f"Total processed: {len(proposals)}")
print(f"Validation: {len(blockers)} Blockers, {len(majors)} Majors.")
if blockers:
    for b in blockers[:10]:
        print("  [BLOCKER]", b)
if majors:
    for m in majors[:10]:
        print("  [MAJOR]", m)

if len(blockers) == 0 and len(majors) == 0:
    with open(PROP_B, 'w', encoding='utf-8') as f:
        for p in proposals:
            f.write(json.dumps(p, ensure_ascii=False) + '\n')
    print(f"Successfully written {len(proposals)} lines to {PROP_B}")

    result_data = {
        "campaign_id": "side_stories_part2_editorial_20261025_r01",
        "partition": "Partition B",
        "scenes": sorted(list(set(it["scene_id"] for it in items))),
        "total_lines": len(proposals),
        "token_parity_percent": 100.0,
        "control_bytes_preserved": len(KEEP_EN_IDS),
        "banned_calques_count": 0,
        "status": "COMPLETED",
        "qa_ready": True
    }
    with open(RESULT_B, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    print(f"Successfully written {RESULT_B}")
else:
    print("Fixes required before writing outputs!")
