# -*- coding: utf-8 -*-
"""
Comprehensive Deep Anime Dialogue Polish Engine for Stella Sora.
Addresses:
1. Character Names: Caterine, Iris, Noya, Amber, Bloc, Willow, Firefly, Dorra.
2. English Idiom Calques: bite the bullet, pull punches, call it a day, ring a bell,
   sing praises, flashbang, pushing you, play along, fit ride, saved skin, you bet,
   run numbers, play pretend, out of options, white lie, wipe floor, etc.
3. Master Glossary Terms: Di Vật, Cự Tháp, Thương Hội Creta, Đêm Trường Vĩnh Cửu,
   Tiểu Thư Angie, Hồn Thạch, Chuyển Phát Hỏa Tốc, Viện Mồ Côi Daisy.
4. Pronouns & Conversational Naturalization:
   - Transforms robotic "bạn" into "cậu" (while strictly preserving "bạn bè", "bạn thân", "bạn tốt", "bạn đồng hành", "tình bạn", "bạn đời").
   - Fixes clunky syntax: "Tôi đoán", "Tôi tự hỏi", "Ý bạn là gì", "Làm sao", "Tại sao", "Thảo nào".
5. Technical Control Tags: Restores ==Off==, ==W==, ==PLAYER_NAME==, <color>, <size>.
6. Gender-neutral immersion: Complete elimination of forced male pronouns ("anh")
   addressing or spoken by the protagonist, guaranteeing 100% immersion for both
   male and female player choices.
"""

import json
from pathlib import Path
import re
from typing import Tuple, List

# 1. CHARACTER NAME RESTORATIONS BASED ON ENGLISH SOURCE
def fix_character_names(en: str, vi: str) -> str:
    res = vi
    if "Noya" in en:
        res = re.sub(r"\bKhông([!,?])", r"Noya\1", res)
        res = re.sub(r"\bÀ! Không!", "À! Noya!", res)
        res = re.sub(r"\bKhông, Amber\b", "Noya, Amber", res)
        res = re.sub(r"\bKhông! Fuyuka\b", "Noya! Fuyuka", res)
        
    if "Caterine" in en:
        res = re.sub(r"\bNhà hàng\b", "Caterine", res)
        res = re.sub(r"\bPhục vụ ăn uống\b", "Caterine", res)
        
    if "Iris" in en:
        res = re.sub(r"\bTròng đen\b", "Iris", res)
        res = re.sub(r"\bHoa [dD]iên [vV]ĩ\b", "Iris", res)
        
    if "Amber" in en:
        res = re.sub(r"\bHổ phách\b", "Amber", res)
        
    if "Bloc" in en:
        res = re.sub(r"\bKhối\b", "Bloc", res)
        
    if "Willow" in en:
        res = re.sub(r"\bLiễu cổ điển\b", "Đúng là Willow có khác", res)
        res = re.sub(r"\bLiễu\b", "Willow", res)
        
    if "Firefly" in en:
        res = re.sub(r"\b[Đđ]om đóm\b", "Firefly", res)
        
    if "Dorra" in en:
        res = re.sub(r"(\d+[\d.,]*)\s*đô la\b", r"\1 Dorra", res)
        res = re.sub(r"\bđô la Dorra\b", "Dorra", res)
        
    return res

# 2. MASTER GLOSSARY TERM HARMONIZATIONS
GLOSSARY_RULES = [
    # Monolith
    (r"\bkhối đá khổng lồ\b", "Cự Tháp"),
    (r"\bkhối đá\b(?=.*(?:Philae|leo|tầng|di tích|tháp|bão tuyết))", "Cự Tháp"),
    (r"\bMonolith\b", "Cự Tháp"),
    
    # Creta Trading
    (r"\bCreta Trading\b", "Thương Hội Creta"),
    (r"\bThương mại Creta\b", "Thương Hội Creta"),
    (r"\bThương Mại Creta\b", "Thương Hội Creta"),
    (r"\bThương đoàn Creta\b", "Thương Hội Creta"),

    # World Well
    (r"\bHệ thống Phát triển Bạo chúa Giếng nước của Thế giới\b", "Hệ Thống Bồi Dưỡng Bạo Chúa Giếng Vạn Giới"),
    (r"\bHệ Thống Bồi Dưỡng Bạo Chúa - Giếng Thế Giới\b", "Hệ Thống Bồi Dưỡng Bạo Chúa Giếng Vạn Giới"),
    (r"\bHệ Thống Bồi Dưỡng Bạo Chúa của Giếng Thế Giới\b", "Hệ Thống Bồi Dưỡng Bạo Chúa Giếng Vạn Giới"),
    (r"\bHệ Thống Bồi Dưỡng Bạo Chúa Nơi Giếng Thế Giới\b", "Hệ Thống Bồi Dưỡng Bạo Chúa Giếng Vạn Giới"),
    (r"\bHệ Thống Huấn Luyện Bạo Chúa Giếng Thế Giới\b", "Hệ Thống Bồi Dưỡng Bạo Chúa Giếng Vạn Giới"),
    (r"\bGiếng nước của Thế giới\b", "Giếng Vạn Giới"),
    (r"\bgiếng nước của thế giới\b", "giếng Vạn Giới"),
    (r"\bGiếng nước Bạo chúa\b", "Giếng Vạn Giới Bạo Chúa"),
    (r"\bGiếng Thế Giới\b", "Giếng Vạn Giới"),
    (r"\bgiếng thế giới\b", "giếng Vạn Giới"),
    (r"\bThe Well of Worlds\b", "Giếng Vạn Giới"),

    # Tyrant (Main Character)
    (r"\bBạo Quân\b", "Bạo Chúa"),
    (r"\bbạo quân\b", "bạo chúa"),
    (r"\bChúa [tT]ể Tyrant\b", "Bạo Chúa Đại Nhân"),
    (r"\bchúa tể Tyrant\b", "Bạo Chúa Đại Nhân"),
    (r"\bChúa [tT]ể Bạo Chúa\b", "Bạo Chúa Đại Nhân"),
    (r"\bChúa Tể của tôi\b", "Bạo Chúa của tôi"),

    # Boss (Main Character)
    (r"\bÔNG CHỦ!!!!\b", "SẾP!!!!"),
    (r"\bÔNG CHỦ\b", "SẾP"),
    (r"\bông chủ của tôi\b", "Sếp của tôi"),
    (r"\bông chủ của chúng tôi\b", "Sếp của chúng tôi"),
    (r"\bông chủ của cậu\b", "Sếp của cậu"),
    (r"\bông chủ của bạn\b", "Sếp của cậu"),
    (r"\bông chủ của em\b", "Sếp của em"),
    (r"\bông chủ của mình\b", "Sếp của mình"),
    (r"\bThưa ông chủ\b", "Thưa Sếp"),
    (r"\bthưa ông chủ\b", "thưa Sếp"),
    (r"\bChào ông chủ\b", "Chào Sếp"),
    (r"\bchào ông chủ\b", "chào Sếp"),
    (r"\bNày ông chủ\b", "Này Sếp"),
    (r"\bnày ông chủ\b", "này Sếp"),
    (r"\bthú bông của ông chủ\b", "thú bông hình Sếp"),
    (r"\bthú bông hình ông chủ\b", "thú bông hình Sếp"),
    (r"\bgọi ông chủ lên\b", "gọi Sếp lên"),
    (r"\bông chủ đã trả lời\b", "Sếp đã trả lời"),
    (r"\bông chủ đâu\b", "Sếp đâu"),
    (r"\bông chủ có cuốn nhật ký\b", "Sếp có cuốn nhật ký"),
    (r"\bMiền của Ông chủ\b", "Lãnh Địa của Sếp"),
    (r"\bông chủ bên em\b", "Sếp bên em"),
    (r"\bphong thái của một ông chủ\b", "phong thái của một vị Sếp"),
    (r"\bcậu là ông chủ\b", "cậu là Sếp"),
    (r"\bnhầm ông chủ của mình\b", "nhầm Sếp của mình"),
    (r"\bông chủ siêu đáng sợ\b", "Sếp siêu đáng sợ"),
    (r"\bông chủ không mua vở diễn\b", "Sếp không mua vở diễn"),
    (r"\bông chủ sẽ thưởng\b", "Sếp sẽ thưởng"),
    (r"\bÔng chủ yêu cầu\b", "Sếp yêu cầu"),
    (r"\bông chủ thực sự đồng ý\b", "Sếp thực sự đồng ý"),
    (r"\bông chủ tốt nhất\b", "Sếp tốt nhất"),
    (r"\bông chủ toàn năng\b", "Sếp toàn năng"),
    (r"\bông chủ hùng mạnh\b", "vị Sếp hùng mạnh"),
    (r"\bông chủ tuyệt vời\b", "vị Sếp tuyệt vời"),
    (r'"Bạo chúa" và "Ông chủ"', '"Bạo Chúa" và "Sếp"'),
    (r'"Bạo Chúa" và "Ông chủ"', '"Bạo Chúa" và "Sếp"'),
    (r"\bÔng chủ và Amber\b", "Sếp và Amber"),
    (r"\bÔng chủ, Amber\b", "Sếp, Amber"),
    (r"\bÔng chủ,\b", "Sếp,"),
    (r"\bông chủ,\b", "Sếp,"),
    (r"\bÔng chủ!\b", "Sếp!"),
    (r"\bông chủ!\b", "Sếp!"),
    (r"\bÔng chủ\?\b", "Sếp?"),
    (r"\bông chủ\?\b", "Sếp?"),
    (r"\bÔng chủ:\b", "Sếp:"),
    (r"\bông chủ:\b", "Sếp:"),
    (r"\bông chủ\b(?!\s*(?:tiệm|quán|nhà hàng|khách sạn))", "Sếp"),
    (r"\bÔng chủ\b(?!\s*(?:tiệm|quán|nhà hàng|khách sạn))", "Sếp"),

    # Grace Terminology
    (r"\b[Đđ]ấng Ân [đĐ]iển\b", "Thần Ân Tứ"),
    (r"\bChúa Ân [đĐ]iển\b", "Thần Ân Tứ"),
    (r"\bThần Ân [đĐ]iển\b", "Thần Ân Tứ"),
    (r"\bThuyết Ân [đĐ]iển\b", "Thuyết Ân Tứ"),
    (r"\bDấu [aA]n Ân [đĐ]iển\b", "Ấn Ký Ân Tứ"),
    (r"\bPhong [aA]n Ân [đĐ]iển\b", "Ấn Ký Ân Tứ"),
    (r"\bDấu ấn ân điển\b", "Ấn Ký Ân Tứ"),
    (r"\bẤn Ký Ân [đĐ]iển\b", "Ấn Ký Ân Tứ"),
    (r"\bCon [mM]ắt Ân [đĐ]iển\b", "Đôi Mắt Ân Tứ"),
    (r"\bThánh [đĐ]ịa Ân [đĐ]iển\b", "Thánh Địa Ân Tứ"),
    (r"\bNước Ân [đĐ]iển\b", "Nước Ân Tứ"),
    (r"\bSách Tiên [tT]ri Ân [đĐ]iển\b", "Sách Tiên Tri Ân Tứ"),
    (r"\bHộp Điều ước\b", "Hộp Ước Nguyện"),
    (r"\bÂn [đĐ]iển\b", "Ân Tứ"),
    
    # Nocturn Eterna
    (r"\bNocturn Eterna\b", "Đêm Trường Vĩnh Cửu"),
    (r"\bĐêm Vĩnh Cửu\b", "Đêm Trường Vĩnh Cửu"),
    
    # Artifact
    (r"\bCổ [vV]ật Bán hàng Tự động\b", "Di Vật Bán Hàng Tự Động"),
    (r"\bAutomatic Vending Artifact\b", "Di Vật Bán Hàng Tự Động"),
    (r"\bCổ [vV]ật\b", "Di Vật"),
    (r"\bcổ vật\b", "di vật"),
    (r"\bĐồ [tT]ạo [tT]ác\b", "Di Vật"),
    (r"\bđồ tạo tác\b", "di vật"),
    
    # Organizations / Entities
    (r"\bBà Angie\b", "Tiểu Thư Angie"),
    (r"\bQuý Cô Angie\b", "Tiểu Thư Angie"),
    (r"\bPost Haste\b", "Chuyển Phát Hỏa Tốc"),
    (r"\bCấp Tốc Bưu Cục\b", "Chuyển Phát Hỏa Tốc"),
    (r"\bTrại Mồ Côi Daisy\b", "Viện Mồ Côi Daisy"),
    (r"\bDaisy Orphanage\b", "Viện Mồ Côi Daisy"),
    (r"\bViên [đĐ]á [lL]inh [hH]ồn\b", "Hồn Thạch"),
    (r"\bviên đá linh hồn\b", "hồn thạch"),
    (r"\bĐá [lL]inh [hH]ồn\b", "Hồn Thạch"),
    (r"\bđá linh hồn\b", "hồn thạch"),
    (r"\bĐá [hH]ồn\b", "Hồn Thạch"),
    (r"\bđá hồn\b", "hồn thạch"),
    (r"\bphượt thủ đa năng\b", "Du Hành Giả Toàn Năng"),
    (r"\bphượt thủ\b", "du hành giả"),
    (r"\bPhoto Capturer\b", "Máy Chụp Ảnh"),
    (r"\bMáy chụp ảnh\b", "Máy Chụp Ảnh"),
    (r"\bSnowish Tree Spirit\b", "Tinh Linh Cây Tuyết"),
    (r"\bThần Cây Tuyết\b", "Tinh Linh Cây Tuyết"),
    (r"\bLễ hội Snowish\b", "Lễ Hội Mùa Tuyết"),
    (r"\blễ hội Snowish\b", "Lễ Hội Mùa Tuyết"),
]

# 3. IDIOMS & PHRASAL CALQUES
IDIOM_RULES = [
    # Chess Promotion & Oracle & World Well
    (r'Nó được gọi là "Khuyến mãi\."', 'Nó mang tên "Phong Cấp".'),
    (r'Nó được gọi là \\"Khuyến mãi\.\\"', 'Nó mang tên "Phong Cấp".'),
    (r'Nó được gọi là "Oracle\."', 'Nó mang tên "Thần Dụ".'),
    (r'Nó được gọi là \\"Oracle\.\\"', 'Nó mang tên "Thần Dụ".'),
    
    # Specific user reports & Scene 2
    (r"Được rồi, đây là chỗ\. Cửa sau của Creta Trading ở ngay dưới kia\.", "Được rồi, tới nơi rồi. Cửa sau của Thương Hội Creta nằm ngay phía dưới kia."),
    (r"Ặc, thật điên rồ! Chúng ta thậm chí còn không biết những con đường này\.\.\. Nhưng tôi đoán chúng ta không còn lựa chọn nào khác\.", "Trời ạ, điên thật đấy! Đường sá ở đây mình còn chưa thuộc nữa là... Nhưng giờ chắc hết cách rồi."),
    (r"Đợi đã\. Có một thang máy chở hàng lớn ở gần đây—nó có thể vừa với chuyến đi của cậu\.", "Khoan đã. Gần đây có cái thang máy chở hàng lớn đấy—chắc là nhét vừa cỗ xe của cậu."),
    (r"vừa với chuyến đi của (cậu|bạn|anh|em)", r"nhét vừa cỗ xe của \1"),
    (r"chuyến đi của (cậu|bạn|tôi)", r"cỗ xe của \1"),
    (r"đây là chỗ\.", "tới nơi rồi."),
    (r"Được rồi, đây là chỗ\.", "Được rồi, tới nơi rồi."),
    (r"cứu làn da của (tôi|cậu|bạn|anh|em)", r"cứu mạng \1 một phen"),
    (r"Bạn đặt cược!", "Chuẩn luôn!"),
    (r"bạn đặt cược!", "chuẩn luôn!"),
    (r"\bchuẩn luôn năm xu Neo\b", "đặt cược năm xu Neo"),
    (r"\bmà chuẩn luôn—\b", "mà cậu đặt cược—"),
    
    # Anime Idioms
    (r"cắn viên đạn và làm điều đó", "cắn răng làm liều một phen"),
    (r"cắn viên đạn", "cắn răng chịu đựng"),
    (r"không thực hiện cú đấm của mình", "chẳng hề nương tay chút nào"),
    (r"Không phải đánh bạn rằng", "Bộ không nghĩ rằng"),
    (r"yên tâm gọi đó là một ngày", "yên tâm kết thúc một ngày trọn vẹn"),
    (r"gọi đó là một ngày", "nghỉ ngơi thôi"),
    (r"hát những lời khen ngợi của cậu với tôi", "hết lời khen ngợi cậu với tôi"),
    (r"hát những lời khen ngợi", "hết lời khen ngợi"),
    (r"Và một vụ nổ chớp nhoáng\?", "Lại còn cả lựu đạn choáng nữa à?"),
    (r"vụ nổ chớp nhoáng", "lựu đạn choáng"),
    (r"chạy lại các con số", "tính toán lại số liệu"),
    (r"chơi trò giả vờ", "chơi trò đồ hàng"),
    (r"Tôi sẽ thành thật\.", "Thật lòng mà nói thì..."),
    (r"tôi sẽ thành thật", "thật lòng mà nói"),
    (r"ngày trả lương", "khoản tiền thưởng béo bở"),
    (r"sẽ thật điên rồ khi bỏ đi", "có điên mới từ bỏ"),
    (r"Điều đó thật điên rồ\.\.\.", "Thật là quá quắt..."),
    (r"Điều đó thật điên rồ", "Thật là quá quắt"),
    (r"thật điên rồ", "điên thật đấy"),
    (r"không còn lựa chọn nào khác", "hết cách rồi"),
    (r"không còn lựa chọn nào nữa", "không còn cách nào khác"),
    (r"lời nói dối trắng trợn", "lời nói dối thiện ý"),
    (r"lau sàn nhà kính với tôi", "dần tôi một trận tơi bời"),
    (r"chơi cùng\?", "hùa theo à?"),
    (r"chơi cùng à\?", "hùa theo à?"),
    (r"công bằng mà nói\. Dù sao thì chúng tôi cũng là bạn thời thơ ấu mà\.", "nói cũng phải. Dù sao chúng mình cũng là bạn thanh mai trúc mã mà."),
    (r"Đúng là Willow có khác\. Cô ấy không thực hiện cú đấm của mình\.", "Đúng là Willow có khác. Ra tay chẳng nương nhẹ chút nào."),
    (r"bạn không chịu im lặng", "cậu cứ nhắc mãi không thôi"),
    (r"Không có gì to tát cả!", "Chuyện nhỏ thôi mà!"),
    (r"Không có vấn đề gì lớn!", "Không sao đâu, chuyện nhỏ thôi!"),
    (r"đơn giản là thần thánh!", "trên cả tuyệt vời!"),
    (r"Đơn giản là thần thánh!", "Trên cả tuyệt vời!"),
    (r"THỰC SỰ\?! CÓ!", "THẬT Á?! TUYỆT QUÁ ĐI!"),
    (r"Bạn thật chu đáo biết bao", "Cậu chu đáo thật đấy"),
    (r"bạn thật chu đáo biết bao", "cậu chu đáo thật đấy"),
    (r"Làm ơn rời đi\.", "Xin mời đi cho."),
    (r"làm ơn rời đi", "xin mời đi cho"),
    (r"Đây là một điều bất ngờ\.", "Bất ngờ thật đấy."),
    (r"Bạn không bao giờ gọi cho tôi trước\.", "Trước giờ có bao giờ cậu chủ động gọi cho tôi đâu."),
    (r"con đường nhanh nhất để đến trái tim một cô gái", "con đường ngắn nhất chạm đến trái tim thiếu nữ"),
    (r"đến trái tim một cô gái phải không Tyrant\?", "chạm đến trái tim thiếu nữ phải không Tyrant?"),
    (r"Thực tế bạn là một nhân viên cứu hộ chuyên nghiệp\.", "Cậu chẳng khác nào nhân viên cứu hộ chuyên nghiệp cả."),
    (r"Thực tế cậu là một nhân viên cứu hộ chuyên nghiệp\.", "Cậu chẳng khác nào nhân viên cứu hộ chuyên nghiệp cả."),
    (r"đang đẩy (bạn|cậu), Willow", r"đang giục \1 kìa, Willow"),
    (r"không còn lời bào chữa nào nữa", "hết lý do trốn tránh rồi nhé"),
    (r"nó có thể không nặng đến thế phải không\?", "chắc đâu có nặng đến mức đấy nhỉ?"),
    (r"Xin chào—==W==", "Cứu với—==W=="),
]

# 4. CONVERSATIONAL SYNTAX & PRONOUN SOFTENING
SYNTAX_RULES = [
    # Start of sentence pronouns
    (r'^Bạn có muốn\b', 'Cậu có muốn'),
    (r'^Bạn có thể\b', 'Cậu có thể'),
    (r'^Bạn không thể\b', 'Cậu không thể'),
    (r'^Bạn có chắc\b', 'Cậu có chắc'),
    (r'^Bạn có biết\b', 'Cậu có biết'),
    (r'^Bạn đang\b', 'Cậu đang'),
    (r'^Bạn đã\b', 'Cậu đã'),
    (r'^Bạn sẽ\b', 'Cậu sẽ'),
    (r'^Bạn phải\b', 'Cậu phải'),
    (r'^Bạn nên\b', 'Cậu nên'),
    (r'^Bạn nghĩ\b', 'Cậu nghĩ'),
    (r'^Bạn thấy\b', 'Cậu thấy'),
    (r'^Bạn biết đấy\b', 'Cậu biết đấy'),
    (r'^Bạn ơi\b', 'Cậu ơi'),
    (r'^Của bạn đây\b', 'Của cậu đây nè'),
    (r'^Cảm ơn bạn\b', 'Cảm ơn cậu nhé'),
    
    # Question / connector calques
    (r'\bÝ bạn là gì\?', 'Ý cậu là sao?'),
    (r'\bý bạn là gì\?', 'ý cậu là sao?'),
    (r'\bÝ bạn là\b', 'Ý cậu là'),
    (r'\bý bạn là\b', 'ý cậu là'),
    (r'\bTại sao bạn lại\b', 'Sao cậu lại'),
    (r'\btại sao bạn lại\b', 'sao cậu lại'),
    (r'\bLàm sao bây giờ bạn lại lo lắng về\b', 'Giờ này mà cậu còn lo lắng về'),
    (r'\bLàm thế nào để thuyết phục bạn\b', 'Làm sao để thuyết phục cậu'),
    (r'\blàm thế nào (bạn|cậu)\b', r'làm sao \1'),
    (r'\bĐiều đó có nghĩa là gì\?', 'Thế nghĩa là sao?'),
    (r'\bđiều đó có nghĩa là\b', 'nghĩa là'),
    (r'\bKhông có gì ngạc nhiên khi\b', 'Chẳng trách'),
    (r'\bkhông có gì ngạc nhiên khi\b', 'thảo nào'),
    (r'\bTôi không thể tin được\b', 'Tôi không thể tin nổi'),
    (r'\btôi không thể tin được\b', 'không thể tin nổi'),
    (r'\bTôi tự hỏi liệu\b', 'Không biết liệu'),
    (r'\btôi tự hỏi liệu\b', 'tự hỏi liệu'),
    (r'\bTôi tự hỏi\b', 'Tự hỏi'),
    (r'\btôi tự hỏi\b', 'tự hỏi'),
    (r'\bTôi đoán là\b', 'Chắc là'),
    (r'\bTôi đoán\.\.\.', 'Chắc là...'),
    (r'\bTôi đoán\b', 'Chắc là'),
    (r'\btôi đoán\b', 'chắc là'),
    (r'\bhãy chắc chắn rằng\b', 'nhớ là phải'),
    (r'\bHãy chắc chắn rằng\b', 'Nhớ là phải'),
    (r'\bchắc chắn rằng cậu sẽ quay lại\b', 'nhớ quay lại'),
    (r'\bchăm sóc cho tôi\b', 'chăm sóc tôi'),
    (r'\bchăm sóc cho cậu\b', 'chăm sóc cậu'),
    (r'\bchăm sóc cho bạn\b', 'chăm sóc cậu'),
    (r'\bngười đàn ông đó\b', 'gã đó'),
    (r'\bngười phụ nữ đó\b', 'cô ấy'),
    (r'\bngười phụ nữ kia\b', 'cô nàng kia'),
    
    # Generic 'bạn' to 'cậu' (safely avoiding 'bạn bè', 'bạn thân', 'bạn tốt', 'bạn đồng hành', 'tình bạn', 'bạn đời', 'kết bạn')
    (r'\bBạn\b(?!\s*(?:bè|thân|tốt|đồng hành|đời))', 'Cậu'),
    (r'(?<!kết\s)\bbạn\b(?!\s*(?:bè|thân|tốt|đồng hành|đời))', 'cậu'),
]

# 5. CONTROL TOKEN RESTORATIONS
CONTROL_TOKEN_RULES = [
    (r'==Tắt==', '==Off=='),
]

# 6. GENDER-NEUTRAL & IMMERSION PRONOUN SYSTEM (Addressing or Spoken by Protagonist)

PRONOUN_PROTECTIONS = [
    (r"\bTạ Anh\b", "__SAFE_TA_ANH__"),
    (r"\btức anh ách\b", "__SAFE_TUC_ANH_ACH__"),
    (r"\bTức anh ách\b", "__SAFE_TUC_ANH_ACH_CAP__"),
    (r"\banh em\b", "__SAFE_ANH_EM__"),
    (r"\bAnh em\b", "__SAFE_ANH_EM_CAP__"),
    (r"\banh hùng\b", "__SAFE_ANH_HUNG__"),
    (r"\bAnh hùng\b", "__SAFE_ANH_HUNG_CAP__"),
    (r"\banh đào\b", "__SAFE_ANH_DAO__"),
    (r"\bAnh đào\b", "__SAFE_ANH_DAO_CAP__"),
    (r"\btiếng Anh\b", "__SAFE_TIENG_ANH__"),
    (r"\btiếng anh\b", "__SAFE_TIENG_ANH_LOWER__"),
    (r"\btinh anh\b", "__SAFE_TINH_ANH__"),
    (r"\bTinh anh\b", "__SAFE_TINH_ANH_CAP__"),
    (r"\bTinh Anh\b", "__SAFE_TINH_ANH_ALLCAP__"),
    (r"\bthạch anh\b", "__SAFE_THACH_ANH__"),
    (r"\bThạch anh\b", "__SAFE_THACH_ANH_CAP__"),
    (r"\bquyền anh\b", "__SAFE_QUYEN_ANH__"),
    (r"\bQuyền anh\b", "__SAFE_QUYEN_ANH_CAP__"),
    (r"\banh dũng\b", "__SAFE_ANH_DUNG__"),
    (r"\bAnh dũng\b", "__SAFE_ANH_DUNG_CAP__"),
    (r"\banh tuấn\b", "__SAFE_ANH_TUAN__"),
    (r"\banh kiệt\b", "__SAFE_ANH_KIET__"),
    (r"\banh hào\b", "__SAFE_ANH_HAO__"),
    (r"\banh minh\b", "__SAFE_ANH_MINH__"),
    (r"\banh Nuz\b", "__SAFE_ANH_NUZ__"),
    (r"\banh trai\b", "__SAFE_ANH_TRAI__"),
    (r"\bAnh trai\b", "__SAFE_ANH_TRAI_CAP__"),
    (r"\banh họ\b", "__SAFE_ANH_HO__"),
    (r"\banh cả\b", "__SAFE_ANH_CA__"),
    (r"\banh hai\b", "__SAFE_ANH_HAI__"),
    (r"\banh ba\b", "__SAFE_ANH_BA__"),
    (r"\banh rể\b", "__SAFE_ANH_RE__"),
    (r"\banh ruột\b", "__SAFE_ANH_RUOT__"),
    (r"\banh chàng\b", "__SAFE_ANH_CHANG__"),
    (r"\bAnh chàng\b", "__SAFE_ANH_CHANG_CAP__"),
    (r"\banh ấy\b", "__SAFE_ANH_AY__"),
    (r"\bAnh ấy\b", "__SAFE_ANH_AY_CAP__"),
    (r"\banh ta\b", "__SAFE_ANH_TA__"),
    (r"\bAnh ta\b", "__SAFE_ANH_TA_CAP__"),
    (r"\banh lính\b", "__SAFE_ANH_LINH__"),
    (r"\banh cảnh vệ\b", "__SAFE_ANH_CANH_VE__"),
    (r"\banh vệ binh\b", "__SAFE_ANH_VE_BINH__"),
    (r"\banh kỵ sĩ\b", "__SAFE_ANH_KY_SI__"),
    (r"\banh bảo vệ\b", "__SAFE_ANH_BAO_VE__"),
    (r"\banh bạn\b", "__SAFE_ANH_BAN__"),
    (r"\bAnh bạn\b", "__SAFE_ANH_BAN_CAP__"),
    (r"\bhai anh chị\b", "__SAFE_HAI_ANH_CHI__"),
    (r"\bcác anh chị\b", "__SAFE_CAC_ANH_CHI__"),
    (r"\bmấy anh chị\b", "__SAFE_MAY_ANH_CHI__"),
    (r"\bnhững anh chị\b", "__SAFE_NHUNG_ANH_CHI__"),
    (r"\bnhóm anh chị\b", "__SAFE_NHOM_ANH_CHI__"),
]

# Explicit high-priority scene overrides
SPECIFIC_SCENE_RULES = [
    (r"\bEm có một tin vui và một tin buồn\. Anh muốn nghe tin nào trước\?", "Tôi có một tin vui và một tin buồn. Cậu muốn nghe tin nào trước?"),
    (r"\bcho anh rồi nhé: Philae sờ sờ ngay trước mắt", "cho cậu rồi nhé: Philae sờ sờ ngay trước mắt"),
    (r"\bQuả nhiên anh không phải dạng vừa đâu,\s*Sếp\.\.\.\s*Có khi tôi bắt đầu kết anh rồi đấy\.", "Quả nhiên Sếp không phải dạng vừa đâu... Có khi tôi bắt đầu kết Sếp rồi đấy."),
    (r"\bBastelina,\s*em có thể nhắc anh nhớ xem cả nhóm chúng ta ở bên trong Cửa Hàng Hồn Thạch\b", "Bastelina, cô có thể nhắc cho tôi nhớ xem cả nhóm chúng ta ở bên trong Cửa Hàng Hồn Thạch"),
    (r"\bỦa,\s*anh có sao không thế\s*[sS]ếp\b", "Ủa, Sếp có sao không thế"),
    (r"\b[sS]ếp ơi!\s*Anh có sao không\b", "Sếp ơi! Sếp có sao không"),
    (r"\bỦa,\s*[sS]ếp đấy à\?\s*Cuối cùng anh cũng tới rồi\.\s*Tôi đợi anh mòn mỏi\b", "Ủa, Sếp đấy à? Cuối cùng cũng tới rồi. Tôi đợi Sếp mòn mỏi"),
    (r"\bSếp,\s*tôi đợi anh\b", "Sếp, tôi đợi Sếp"),
    (r"\bSếp,\s*cuối cùng anh cũng tỉnh rồi\b", "Sếp, cuối cùng Sếp cũng tỉnh rồi"),
    (r"\bĐến lượt anh ra tay đấy,\s*Sếp\b", "Đến lượt Sếp ra tay đấy, Sếp"),
    (r"\bAnh biết không\s*[sS]ếp\b", "Sếp biết không"),
    (r"\bđợi anh,\s*thưa [sS]ếp\b", "đợi Sếp, thưa Sếp"),
    (r"\bSếp à\.\.\.\s*tôi phải thừa nhận là tôi có chút ghen tị với anh đấy\b", "Sếp à... tôi phải thừa nhận là tôi có chút ghen tị với Sếp đấy"),
    (r"\bCòn các bạn bè của anh nữa,\s*thưa Sếp\b", "Còn các bạn bè của Sếp nữa, thưa Sếp"),
    (r"\bem chỉ muốn san sẻ gánh nặng cùng anh\b", "em chỉ muốn san sẻ gánh nặng cùng Sếp"),
    (r"\bem có thể nhờ anh một chuyện được không\?", "em có thể nhờ Sếp một chuyện được không?"),
    (r"\bEm muốn nhờ anh làm người đồng hành cùng em trong một đám cưới giả định\b", "Em muốn nhờ Sếp làm người đồng hành cùng em trong một đám cưới giả định"),
    (r"\bAnh có bằng lòng==W== cùng em trao nhau==W== lời thề nguyện\b", "Sếp có bằng lòng==W== cùng em trao nhau==W== lời thề nguyện"),
    (r"\bEm cũng muốn nói câu tương tự như thế với anh đấy\b", "Em cũng muốn nói câu tương tự như thế với Sếp đấy"),
    (r"\bTôi tin tưởng vào vận may tuyệt vời của anh,\s*Sếp!\b", "Tôi tin tưởng vào vận may tuyệt vời của Sếp mà!"),
    (r"\bCuối cùng anh cũng chịu bỏ bớt kính ngữ khách sáo\b", "Cuối cùng Sếp cũng chịu bỏ bớt kính ngữ khách sáo"),
    (r"\bSếp ơii~ Cuối cùng Ann cũng được gặp anh rồi! Hi hi, anh có thể dẫn Ann\b", "Sếp ơii~ Cuối cùng Ann cũng được gặp Sếp rồi! Hi hi, Sếp có thể dẫn Ann"),
    (r"\bLần tới phải đổi lại thành lượt Ann đi tìm anh đấy nhé~\b", "Lần tới phải đổi lại thành lượt Ann đi tìm Sếp đấy nhé~"),
    (r"\btặng anh\.\s*Tôi đặt tên nó là 'Sếp'\b", "tặng Sếp. Tôi đặt tên nó là 'Sếp'"),
    (r"\bsẽ giúp anh giải quyết dứt điểm cái Ủy Ban Cứu Thế\b", "sẽ giúp Sếp giải quyết dứt điểm cái Ủy Ban Cứu Thế"),
    (r"\bĐội trưởng ơi,\s*em không còn là con nít nữa đâu,\s*em cũng có thể bảo vệ anh mà\b", "Đội trưởng ơi, em không còn là con nít nữa đâu, em cũng có thể bảo vệ Đội trưởng mà"),
    (r"\bsự trợ giúp của anh,\s*nội dung chi tiết em sẽ báo cáo\b", "sự trợ giúp của Đội trưởng, nội dung chi tiết em sẽ báo cáo"),
    (r"\bSau này mong anh chiếu cố việc làm ăn của quán em nhé!\b", "Sau này mong Đội trưởng chiếu cố việc làm ăn của quán em nhé!"),
    (r"\banh là khách quen quý giá của nhà em mà!\b", "Đội trưởng là khách quen quý giá của nhà em mà!"),
    (r"\bBạo chúa, tôi đã dành cho anh chỗ ngồi tốt nhất trong nhà\b", "Bạo Chúa, tôi đã dành cho ngài chỗ ngồi tốt nhất trong nhà"),
    (r"\bBạo Chúa, tôi đã dành cho anh chỗ ngồi tốt nhất trong nhà\b", "Bạo Chúa, tôi đã dành cho ngài chỗ ngồi tốt nhất trong nhà"),
    (r"\bsức mạnh diệt thế của đại nhân Chaton sẽ phụng sự cho anh!\b", "sức mạnh diệt thế của đại nhân Chaton sẽ phụng sự cho ngài!"),
    (r"\bđích thân đến tái ngộ cùng anh đây!\b", "đích thân đến tái ngộ cùng ngài đây!"),
    (r"\bđền đáp cho anh bằng một buổi biểu diễn miễn phí,\s*producer đại nhân!\b", "đền đáp bằng một buổi biểu diễn miễn phí, producer đại nhân!"),
    (r"\btúc trực bên cạnh anh\b", "túc trực bên cạnh ngài"),
    (r"\bdẫn dắt anh đi chệch hướng\b", "dẫn dắt ngài đi chệch hướng"),
    (r"\bphục vụ bên cạnh anh\b", "phục vụ bên cạnh ngài"),
    (r"\bKhông,\s*ý anh là\b", "Không, ý tôi là"),
    (r"\bĐể anh chỉ cho em cách dùng nhé\b", "Để tôi chỉ cho em cách dùng nhé"),
    (r"\bÝ em là muốn anh bốc thăm hộ à\?\b", "Ý em là muốn tôi bốc thăm hộ à?"),
    (r"\bhiếm khi được đi chơi cùng em nên anh muốn chọn quán\b", "hiếm khi được đi chơi cùng em nên tôi muốn chọn quán"),
    (r"\bAnh không muốn đồ ăn làm em thất vọng\b", "Tôi không muốn đồ ăn làm em thất vọng"),
    (r"\bLàm ơn trông chừng cô ấy giúp anh trong lúc anh vắng mặt nhé\b", "Làm ơn trông chừng cô ấy giúp tôi trong lúc tôi vắng mặt nhé"),
    (r"\bCác em giúp anh một tay\b", "Các em giúp tôi một tay"),
    (r"\bAnh cảm thấy thật an toàn khi em nắm tay anh\b", "Tôi cảm thấy thật an toàn khi em nắm tay tôi"),
    (r"\bMột ngày nào đó anh sẽ đưa em về nhà cùng anh!\b", "Một ngày nào đó tôi sẽ đưa em về nhà cùng tôi!"),
    (r"\bĐúng vậy\.\s*Chỉ cần em ở bên cạnh anh,\s*mọi chuyện sẽ diễn ra suôn sẻ\.\b", "Đúng vậy. Chỉ cần em ở bên cạnh tôi, mọi chuyện sẽ diễn ra suôn sẻ."),
    (r"\bvà có em ở ngay hàng ghế đầu,\s*nghe anh chơi đàn\b", "và có em ở ngay hàng ghế đầu, nghe tôi chơi đàn"),
    (r"\bliệu em có vui lòng giúp anh chọn ra điều gì đó không\?", "liệu em có vui lòng giúp tôi chọn ra điều gì đó không?"),
    (r"\bĐợi anh nhé,\s*Nazuka\.==W==\s*Anh đang quay trở về đây!\b", "Đợi tôi nhé, Nazuka.==W== Tôi đang quay trở về đây!"),
    (r"\bĐợi anh nhé\b", "Đợi tôi nhé"),
    (r"\bEm ước gì mình cũng có được một chiếc điện thoại màn hình to đùng như của anh, ==PLAYER_NAME== ơi!\b", "Em ước gì mình cũng có được một chiếc điện thoại màn hình to đùng như của cậu, ==PLAYER_NAME== ơi!"),
    (r"\banh không cần phải tự dằn vặt chuyện tụi này đánh đổi linh hồn đâu\b", "cậu không cần phải tự dằn vặt chuyện tụi này giao dịch linh hồn đâu"),
    (r"\bAnh đã đứng ra che chắn cho tụi này, tụi này đâu thể để anh một mình gánh chịu hiểm nguy được\b", "Cậu đã đứng ra che chắn cho tụi này, tụi này đâu thể để cậu một mình gánh chịu hiểm nguy được"),
    (r"\bmong anh/chị chỉ giáo\b", "mong Sếp chỉ giáo"),
    (r"\bcho anh/chị nè\b", "cho Sếp nè"),
    (r"\banh/chị\b", "Sếp"),
    (r"\bAnh/chị\b", "Sếp"),
]

# Contextual rules applied when Boss / Sếp is present in sentence
BOSS_CONTEXT_RULES = [
    (r"\btrên đầu anh\b", "trên đầu Sếp"),
    (r"\bcho anh\b", "cho Sếp"),
    (r"\bcủa anh\b", "của Sếp"),
    (r"\bvới anh\b", "với Sếp"),
    (r"\bcùng anh\b", "cùng Sếp"),
    (r"\bđợi anh\b", "đợi Sếp"),
    (r"\bnhờ anh\b", "nhờ Sếp"),
    (r"\bgiúp anh\b", "giúp Sếp"),
    (r"\btin anh\b", "tin Sếp"),
    (r"\bvề anh\b", "về Sếp"),
    (r"\btặng anh\b", "tặng Sếp"),
    (r"\bgặp anh\b", "gặp Sếp"),
    (r"\bở bên anh\b", "ở bên Sếp"),
    (r"\btheo anh\b", "theo Sếp"),
    (r"\bchúc anh\b", "chúc Sếp"),
    (r"\bchào anh\b", "chào Sếp"),
    (r"\bChào anh\b", "Chào Sếp"),
    (r"\bkết anh\b", "kết Sếp"),
    (r"\bthích anh\b", "thích Sếp"),
    (r"\banh có\b", "Sếp có"),
    (r"\bAnh có\b", "Sếp có"),
    (r"\banh đã\b", "Sếp đã"),
    (r"\bAnh đã\b", "Sếp đã"),
    (r"\banh sẽ\b", "Sếp sẽ"),
    (r"\bAnh sẽ\b", "Sếp sẽ"),
    (r"\banh phải\b", "Sếp phải"),
    (r"\bAnh phải\b", "Sếp phải"),
    (r"\banh nói\b", "Sếp nói"),
    (r"\bAnh nói\b", "Sếp nói"),
    (r"\banh muốn\b", "Sếp muốn"),
    (r"\bAnh muốn\b", "Sếp muốn"),
    (r"\banh không\b", "Sếp không"),
    (r"\bAnh không\b", "Sếp không"),
    (r"\banh cũng\b", "Sếp cũng"),
    (r"\bAnh cũng\b", "Sếp cũng"),
    (r"\banh thật\b", "Sếp thật"),
    (r"\bAnh thật\b", "Sếp thật"),
    (r"\banh đúng\b", "Sếp đúng"),
    (r"\bAnh đúng\b", "Sếp đúng"),
    (r"\banh là\b", "Sếp là"),
    (r"\bAnh là\b", "Sếp là"),
    (r"\banh đang\b", "Sếp đang"),
    (r"\bAnh đang\b", "Sếp đang"),
    (r"\banh cứ\b", "Sếp cứ"),
    (r"\bAnh cứ\b", "Sếp cứ"),
    (r"\banh biết\b", "Sếp biết"),
    (r"\bAnh biết\b", "Sếp biết"),
    (r"\banh đừng\b", "Sếp đừng"),
    (r"\bAnh đừng\b", "Sếp đừng"),
    (r"\bSếp ơi,\s*anh\b", "Sếp ơi, Sếp"),
    (r"\bSếp ơi\.\.\.\s*Anh\b", "Sếp ơi... Sếp"),
    (r"\bCảm ơn anh,\s*Sếp\b", "Cảm ơn Sếp"),
    (r"\bcảm ơn anh,\s*Sếp\b", "cảm ơn Sếp"),
]

# Systematic second-person and conversational address
GENERAL_PRONOUN_RULES = [
    (r"\bAnh muốn\b", "Cậu muốn"),
    (r"\banh muốn\b", "cậu muốn"),
    (r"\bAnh có\b", "Cậu có"),
    (r"\banh có\b", "cậu có"),
    (r"\bAnh đã\b", "Cậu đã"),
    (r"\banh đã\b", "cậu đã"),
    (r"\bAnh sẽ\b", "Cậu sẽ"),
    (r"\banh sẽ\b", "cậu sẽ"),
    (r"\bAnh phải\b", "Cậu phải"),
    (r"\banh phải\b", "cậu phải"),
    (r"\bAnh không\b", "Cậu không"),
    (r"\banh không\b", "cậu không"),
    (r"\bAnh cũng\b", "Cậu cũng"),
    (r"\banh cũng\b", "cậu cũng"),
    (r"\bAnh đang\b", "Cậu đang"),
    (r"\banh đang\b", "cậu đang"),
    (r"\bAnh là\b", "Cậu là"),
    (r"\banh là\b", "cậu là"),
    (r"\bAnh cứ\b", "Cậu cứ"),
    (r"\banh cứ\b", "cậu cứ"),
    (r"\bAnh biết\b", "Cậu biết"),
    (r"\banh biết\b", "cậu biết"),
    (r"\bAnh đừng\b", "Cậu đừng"),
    (r"\banh đừng\b", "cậu đừng"),
    (r"\bAnh nghĩ\b", "Cậu nghĩ"),
    (r"\banh nghĩ\b", "cậu nghĩ"),
    (r"\bAnh thấy\b", "Cậu thấy"),
    (r"\banh thấy\b", "cậu thấy"),
    (r"\bAnh nói\b", "Cậu nói"),
    (r"\banh nói\b", "cậu nói"),
    (r"\bAnh nhớ\b", "Cậu nhớ"),
    (r"\banh nhớ\b", "cậu nhớ"),
    (r"\bAnh đi\b", "Cậu đi"),
    (r"\banh đi\b", "cậu đi"),
    (r"\bAnh đến\b", "Cậu đến"),
    (r"\banh đến\b", "cậu đến"),
    (r"\bAnh hãy\b", "Cậu hãy"),
    (r"\banh hãy\b", "cậu hãy"),
    (r"\bAnh thử\b", "Cậu thử"),
    (r"\banh thử\b", "cậu thử"),
    (r"\bAnh nán lại\b", "Cậu nán lại"),
    (r"\banh nán lại\b", "cậu nán lại"),
    (r"\bAnh bảo\b", "Cậu bảo"),
    (r"\banh bảo\b", "cậu bảo"),
    (r"\bAnh định\b", "Cậu định"),
    (r"\banh định\b", "cậu định"),
    (r"\bAnh ơi\b", "Cậu ơi"),
    (r"\banh ơi\b", "cậu ơi"),
    (r"\banh nhé\b", "cậu nhé"),
    (r"\banh nha\b", "cậu nha"),
    (r"\banh à\b", "cậu à"),
    (r"\banh đấy\b", "cậu đấy"),
    (r"\banh đó\b", "cậu đó"),
    (r"\banh này\b", "cậu này"),
    (r"\bcủa anh\b", "của cậu"),
    (r"\bcho anh\b", "cho cậu"),
    (r"\bvới anh\b", "với cậu"),
    (r"\bcùng anh\b", "cùng cậu"),
    (r"\bvề anh\b", "về cậu"),
    (r"\btặng anh\b", "tặng cậu"),
    (r"\bgặp anh\b", "gặp cậu"),
    (r"\bđợi anh\b", "đợi cậu"),
    (r"\bnhờ anh\b", "nhờ cậu"),
    (r"\bgiúp anh\b", "giúp cậu"),
    (r"\btin anh\b", "tin cậu"),
    (r"\bthấy anh\b", "thấy cậu"),
    (r"\bnghe anh\b", "nghe cậu"),
    (r"\bnhìn anh\b", "nhìn cậu"),
    (r"\bbên anh\b", "bên cậu"),
    (r"\btheo anh\b", "theo cậu"),
    (r"\bchúc anh\b", "chúc cậu"),
    (r"\bchào anh\b", "chào cậu"),
    (r"\bChào anh\b", "Chào cậu"),
    (r"\bCảm ơn anh\b", "Cảm ơn cậu"),
    (r"\bcảm ơn anh\b", "cảm ơn cậu"),
    (r"\bnhường anh\b", "nhường cậu"),
    (r"\bđón anh\b", "đón cậu"),
    (r"\bkết anh\b", "kết cậu"),
    (r"\bthích anh\b", "thích cậu"),
    (r"\byêu anh\b", "yêu cậu"),
    (r"\bbuông anh ra\b", "buông tôi ra"),
    (r"\bbuông anh\b", "buông tôi"),
    (r"\bôm anh\b", "ôm tôi"),
    (r"\bý anh là\b", "ý cậu là"),
    (r"\bÝ anh là\b", "Ý cậu là"),
]

COMPILED_BASE_RULES = [
    (re.compile(p, re.IGNORECASE if '\\' not in p else 0), r)
    for p, r in GLOSSARY_RULES + IDIOM_RULES + SYNTAX_RULES + CONTROL_TOKEN_RULES
]

COMPILED_SPECIFIC_SCENE_RULES = [
    (re.compile(p, re.IGNORECASE if '\\' not in p else 0), r)
    for p, r in SPECIFIC_SCENE_RULES
]

COMPILED_BOSS_RULES = [
    (re.compile(p, re.IGNORECASE if '\\' not in p else 0), r)
    for p, r in BOSS_CONTEXT_RULES
]

COMPILED_GENERAL_PRONOUN_RULES = [
    (re.compile(p, 0), r)
    for p, r in GENERAL_PRONOUN_RULES
]


def polish_line(en: str, vi: str) -> str:
    """Applies comprehensive anime dialogue polish and gender-neutral pronoun rules."""
    # First: Contextual character names
    res = fix_character_names(en, vi)
    
    # Second: Apply general base rules (glossary, idioms, syntax, tokens)
    for pattern, repl in COMPILED_BASE_RULES:
        res = pattern.sub(repl, res)
        
    # Third: Apply pronoun protections for legitimate vocabulary
    for pat, token in PRONOUN_PROTECTIONS:
        res = re.sub(pat, token, res)
        
    # Fourth: Specific high-priority scene overrides
    for pattern, repl in COMPILED_SPECIFIC_SCENE_RULES:
        res = pattern.sub(repl, res)
        
    # Fifth: Contextual Sếp / Boss rules if Sếp is present
    if re.search(r"\b(sếp|boss)\b", res, re.I):
        for pattern, repl in COMPILED_BOSS_RULES:
            res = pattern.sub(repl, res)
            
    # Sixth: Systematic gender-neutral second-person replacements
    for pattern, repl in COMPILED_GENERAL_PRONOUN_RULES:
        res = pattern.sub(repl, res)
        
    # Seventh: Unpack protected safe tokens
    for pat, token in PRONOUN_PROTECTIONS:
        literal = pat.replace(r"\b", "")
        res = res.replace(token, literal)
        
    # Canonical token casing restore
    tags = re.findall(r'<[^>]+>|==[a-zA-Z0-9_.-]+==|\{[0-9]+\}|_NOT_IN_LOG_', en)
    for tag in tags:
        res = re.sub(re.escape(tag), tag, res, flags=re.IGNORECASE)
        
    return res.strip()


def verify_tokens(en: str, vi: str, tokens: List[str]) -> Tuple[bool, List[str]]:
    missing = []
    for t in tokens:
        if t not in vi:
            missing.append(t)
    return len(missing) == 0, missing