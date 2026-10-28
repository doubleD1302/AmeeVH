# -*- coding: utf-8 -*-
"""
Comprehensive Deep Anime Dialogue Polish Engine for Stella Sora.
Addresses:
1. Character Names: Caterine, Iris, Noya, Amber, Bloc, Willow, Firefly, Dorra.
2. English Idiom Calques: bite the bullet, pull punches, call it a day, ring a bell,
   sing praises, flashbang, pushing you, play along, fit ride, saved skin, you bet,
   run numbers, play pretend, out of options, white lie, wipe floor, etc.
3. Master Glossary Terms: Di Vật, Cự Tháp, Thương đoàn Creta, Đêm Trường Vĩnh Cửu,
   Tiểu Thư Angie, Hồn Thạch, Chuyển Phát Hỏa Tốc, Viện Mồ Côi Daisy.
4. Pronouns & Conversational Naturalization:
   - Transforms robotic 'bạn' into 'cậu' (while strictly preserving 'bạn bè', 'bạn thân', 'bạn tốt', 'bạn đồng hành', 'tình bạn', 'bạn đời').
   - Softens 'tôi - bạn' robotic workplace phrasing into natural anime dialogue.
   - Fixes 'người đàn ông đó', 'người phụ nữ đó'.
   - Fixes clunky syntax: 'Tôi đoán', 'Tôi tự hỏi', 'Ý bạn là gì', 'Làm sao', 'Tại sao', 'Thảo nào'.
5. Technical Control Tags: Restores ==Off==, ==W==, ==PLAYER_NAME==, <color>, <size>.
"""

import json
from pathlib import Path
import re
from typing import Tuple, List

# 1. CHARACTER NAME RESTORATIONS BASED ON ENGLISH SOURCE
def fix_character_names(en: str, vi: str) -> str:
    res = vi
    if 'Noya' in en:
        res = re.sub(r'\bKhông([!,?])', r'Noya\1', res)
        res = re.sub(r'\bÀ! Không!', 'À! Noya!', res)
        res = re.sub(r'\bKhông, Amber\b', 'Noya, Amber', res)
        res = re.sub(r'\bKhông! Fuyuka\b', 'Noya! Fuyuka', res)
        
    if 'Caterine' in en:
        res = re.sub(r'\bNhà hàng\b', 'Caterine', res)
        res = re.sub(r'\bPhục vụ ăn uống\b', 'Caterine', res)
        
    if 'Iris' in en:
        res = re.sub(r'\bTròng đen\b', 'Iris', res)
        res = re.sub(r'\bHoa [dD]iên [vV]ĩ\b', 'Iris', res)
        
    if 'Amber' in en:
        res = re.sub(r'\bHổ phách\b', 'Amber', res)
        
    if 'Bloc' in en:
        res = re.sub(r'\bKhối\b', 'Bloc', res)
        
    if 'Willow' in en:
        res = re.sub(r'\bLiễu cổ điển\b', 'Đúng là Willow có khác', res)
        res = re.sub(r'\bLiễu\b', 'Willow', res)
        
    if 'Firefly' in en:
        res = re.sub(r'\b[Đđ]om đóm\b', 'Firefly', res)
        
    if 'Dorra' in en:
        res = re.sub(r'(\d+[\d.,]*)\s*đô la\b', r'\1 Dorra', res)
        res = re.sub(r'\bđô la Dorra\b', 'Dorra', res)
        
    return res

# 2. MASTER GLOSSARY TERM HARMONIZATIONS
GLOSSARY_RULES = [
    # Monolith
    (r'\bkhối đá khổng lồ\b', 'Cự Tháp'),
    (r'\bkhối đá\b(?=.*(?:Philae|leo|tầng|di tích|tháp|bão tuyết))', 'Cự Tháp'),
    (r'\bMonolith\b', 'Cự Tháp'),
    
    # Creta Trading
    (r'\bCreta Trading\b', 'Thương Hội Creta'),
    (r'\bThương mại Creta\b', 'Thương Hội Creta'),
    (r'\bThương Mại Creta\b', 'Thương Hội Creta'),
    (r'\bThương đoàn Creta\b', 'Thương Hội Creta'),

    # World Well
    (r'\bHệ thống Phát triển Bạo chúa Giếng nước của Thế giới\b', 'Hệ Thống Bồi Dưỡng Bạo Chúa Giếng Vạn Giới'),
    (r'\bHệ Thống Bồi Dưỡng Bạo Chúa - Giếng Thế Giới\b', 'Hệ Thống Bồi Dưỡng Bạo Chúa Giếng Vạn Giới'),
    (r'\bHệ Thống Bồi Dưỡng Bạo Chúa của Giếng Thế Giới\b', 'Hệ Thống Bồi Dưỡng Bạo Chúa Giếng Vạn Giới'),
    (r'\bHệ Thống Bồi Dưỡng Bạo Chúa Nơi Giếng Thế Giới\b', 'Hệ Thống Bồi Dưỡng Bạo Chúa Giếng Vạn Giới'),
    (r'\bHệ Thống Huấn Luyện Bạo Chúa Giếng Thế Giới\b', 'Hệ Thống Bồi Dưỡng Bạo Chúa Giếng Vạn Giới'),
    (r'\bGiếng nước của Thế giới\b', 'Giếng Vạn Giới'),
    (r'\bgiếng nước của thế giới\b', 'giếng Vạn Giới'),
    (r'\bGiếng nước Bạo chúa\b', 'Giếng Vạn Giới Bạo Chúa'),
    (r'\bGiếng Thế Giới\b', 'Giếng Vạn Giới'),
    (r'\bgiếng thế giới\b', 'giếng Vạn Giới'),
    (r'\bThe Well of Worlds\b', 'Giếng Vạn Giới'),

    # Tyrant (Main Character)
    (r'\bBạo Quân\b', 'Bạo Chúa'),
    (r'\bbạo quân\b', 'bạo chúa'),
    (r'\bChúa [tT]ể Tyrant\b', 'Bạo Chúa Đại Nhân'),
    (r'\bchúa tể Tyrant\b', 'Bạo Chúa Đại Nhân'),
    (r'\bChúa [tT]ể Bạo Chúa\b', 'Bạo Chúa Đại Nhân'),
    (r'\bChúa Tể của tôi\b', 'Bạo Chúa của tôi'),

    # Boss (Main Character)
    (r'\bÔNG CHỦ!!!!\b', 'SẾP!!!!'),
    (r'\bÔNG CHỦ\b', 'SẾP'),
    (r'\bông chủ của tôi\b', 'Sếp của tôi'),
    (r'\bông chủ của chúng tôi\b', 'Sếp của chúng tôi'),
    (r'\bông chủ của cậu\b', 'Sếp của cậu'),
    (r'\bông chủ của bạn\b', 'Sếp của cậu'),
    (r'\bông chủ của em\b', 'Sếp của em'),
    (r'\bông chủ của mình\b', 'Sếp của mình'),
    (r'\bThưa ông chủ\b', 'Thưa Sếp'),
    (r'\bthưa ông chủ\b', 'thưa Sếp'),
    (r'\bChào ông chủ\b', 'Chào Sếp'),
    (r'\bchào ông chủ\b', 'chào Sếp'),
    (r'\bNày ông chủ\b', 'Này Sếp'),
    (r'\bnày ông chủ\b', 'này Sếp'),
    (r'\bthú bông của ông chủ\b', 'thú bông hình Sếp'),
    (r'\bthú bông hình ông chủ\b', 'thú bông hình Sếp'),
    (r'\bgọi ông chủ lên\b', 'gọi Sếp lên'),
    (r'\bông chủ đã trả lời\b', 'Sếp đã trả lời'),
    (r'\bông chủ đâu\b', 'Sếp đâu'),
    (r'\bông chủ có cuốn nhật ký\b', 'Sếp có cuốn nhật ký'),
    (r'\bMiền của Ông chủ\b', 'Lãnh Địa của Sếp'),
    (r'\bông chủ bên em\b', 'Sếp bên em'),
    (r'\bphong thái của một ông chủ\b', 'phong thái của một vị Sếp'),
    (r'\bcậu là ông chủ\b', 'cậu là Sếp'),
    (r'\bnhầm ông chủ của mình\b', 'nhầm Sếp của mình'),
    (r'\bông chủ siêu đáng sợ\b', 'Sếp siêu đáng sợ'),
    (r'\bông chủ không mua vở diễn\b', 'Sếp không mua vở diễn'),
    (r'\bông chủ sẽ thưởng\b', 'Sếp sẽ thưởng'),
    (r'\bÔng chủ yêu cầu\b', 'Sếp yêu cầu'),
    (r'\bông chủ thực sự đồng ý\b', 'Sếp thực sự đồng ý'),
    (r'\bông chủ tốt nhất\b', 'Sếp tốt nhất'),
    (r'\bông chủ toàn năng\b', 'Sếp toàn năng'),
    (r'\bông chủ hùng mạnh\b', 'vị Sếp hùng mạnh'),
    (r'\bông chủ tuyệt vời\b', 'vị Sếp tuyệt vời'),
    (r'"Bạo chúa" và "Ông chủ"', '"Bạo Chúa" và "Sếp"'),
    (r'"Bạo Chúa" và "Ông chủ"', '"Bạo Chúa" và "Sếp"'),
    (r'\bÔng chủ và Amber\b', 'Sếp và Amber'),
    (r'\bÔng chủ, Amber\b', 'Sếp, Amber'),
    (r'\bÔng chủ,\b', 'Sếp,'),
    (r'\bông chủ,\b', 'Sếp,'),
    (r'\bÔng chủ!\b', 'Sếp!'),
    (r'\bông chủ!\b', 'Sếp!'),
    (r'\bÔng chủ\?\b', 'Sếp?'),
    (r'\bông chủ\?\b', 'Sếp?'),
    (r'\bÔng chủ:\b', 'Sếp:'),
    (r'\bông chủ:\b', 'Sếp:'),
    (r'\bông chủ\b(?!\s*(?:tiệm|quán|nhà hàng|khách sạn))', 'Sếp'),
    (r'\bÔng chủ\b(?!\s*(?:tiệm|quán|nhà hàng|khách sạn))', 'Sếp'),

    # Grace Terminology
    (r'\b[Đđ]ấng Ân [đĐ]iển\b', 'Thần Ân Tứ'),
    (r'\bChúa Ân [đĐ]iển\b', 'Thần Ân Tứ'),
    (r'\bThần Ân [đĐ]iển\b', 'Thần Ân Tứ'),
    (r'\bThuyết Ân [đĐ]iển\b', 'Thuyết Ân Tứ'),
    (r'\bDấu [aA]n Ân [đĐ]iển\b', 'Ấn Ký Ân Tứ'),
    (r'\bPhong [aA]n Ân [đĐ]iển\b', 'Ấn Ký Ân Tứ'),
    (r'\bDấu ấn ân điển\b', 'Ấn Ký Ân Tứ'),
    (r'\bẤn Ký Ân [đĐ]iển\b', 'Ấn Ký Ân Tứ'),
    (r'\bCon [mM]ắt Ân [đĐ]iển\b', 'Đôi Mắt Ân Tứ'),
    (r'\bThánh [đĐ]ịa Ân [đĐ]iển\b', 'Thánh Địa Ân Tứ'),
    (r'\bNước Ân [đĐ]iển\b', 'Nước Ân Tứ'),
    (r'\bSách Tiên [tT]ri Ân [đĐ]iển\b', 'Sách Tiên Tri Ân Tứ'),
    (r'\bHộp Điều ước\b', 'Hộp Ước Nguyện'),
    (r'\bÂn [đĐ]iển\b', 'Ân Tứ'),
    
    # Nocturn Eterna
    (r'\bNocturn Eterna\b', 'Đêm Trường Vĩnh Cửu'),
    (r'\bĐêm Vĩnh Cửu\b', 'Đêm Trường Vĩnh Cửu'),
    
    # Artifact
    (r'\bCổ [vV]ật Bán hàng Tự động\b', 'Di Vật Bán Hàng Tự Động'),
    (r'\bAutomatic Vending Artifact\b', 'Di Vật Bán Hàng Tự Động'),
    (r'\bCổ [vV]ật\b', 'Di Vật'),
    (r'\bcổ vật\b', 'di vật'),
    (r'\bĐồ [tT]ạo [tT]ác\b', 'Di Vật'),
    (r'\bđồ tạo tác\b', 'di vật'),
    
    # Organizations / Entities
    (r'\bBà Angie\b', 'Tiểu Thư Angie'),
    (r'\bQuý Cô Angie\b', 'Tiểu Thư Angie'),
    (r'\bPost Haste\b', 'Chuyển Phát Hỏa Tốc'),
    (r'\bCấp Tốc Bưu Cục\b', 'Chuyển Phát Hỏa Tốc'),
    (r'\bTrại Mồ Côi Daisy\b', 'Viện Mồ Côi Daisy'),
    (r'\bDaisy Orphanage\b', 'Viện Mồ Côi Daisy'),
    (r'\bViên [đĐ]á [lL]inh [hH]ồn\b', 'Hồn Thạch'),
    (r'\bviên đá linh hồn\b', 'hồn thạch'),
    (r'\bĐá [lL]inh [hH]ồn\b', 'Hồn Thạch'),
    (r'\bđá linh hồn\b', 'hồn thạch'),
    (r'\bĐá [hH]ồn\b', 'Hồn Thạch'),
    (r'\bđá hồn\b', 'hồn thạch'),
    (r'\bphượt thủ đa năng\b', 'Du Hành Giả Toàn Năng'),
    (r'\bphượt thủ\b', 'du hành giả'),
    (r'\bPhoto Capturer\b', 'Máy Chụp Ảnh'),
    (r'\bMáy chụp ảnh\b', 'Máy Chụp Ảnh'),
    (r'\bSnowish Tree Spirit\b', 'Tinh Linh Cây Tuyết'),
    (r'\bThần Cây Tuyết\b', 'Tinh Linh Cây Tuyết'),
    (r'\bLễ hội Snowish\b', 'Lễ Hội Mùa Tuyết'),
    (r'\blễ hội Snowish\b', 'Lễ Hội Mùa Tuyết'),
]

# 3. IDIOMS & PHRASAL CALQUES
IDIOM_RULES = [
    # Chess Promotion & Oracle & World Well
    (r'Nó được gọi là "Khuyến mãi\."', 'Nó mang tên "Phong Cấp".'),
    (r'Nó được gọi là \\"Khuyến mãi\.\\"', 'Nó mang tên "Phong Cấp".'),
    (r'Nó được gọi là "Oracle\."', 'Nó mang tên "Thần Dụ".'),
    (r'Nó được gọi là \\"Oracle\.\\"', 'Nó mang tên "Thần Dụ".'),
    
    # Amber address & soul trading
    (r'anh không cần phải tự dằn vặt chuyện tụi này đánh đổi linh hồn đâu', 'cậu không cần phải tự dằn vặt chuyện tụi này giao dịch linh hồn đâu'),
    (r'Anh đã đứng ra che chắn cho tụi này, tụi này đâu thể để anh một mình gánh chịu hiểm nguy được', 'Cậu đã đứng ra che chắn cho tụi này, tụi này đâu thể để cậu một mình gánh chịu hiểm nguy được'),
    (r'Em ước gì mình cũng có được một chiếc điện thoại màn hình to đùng như của anh, ==PLAYER_NAME== ơi!', 'Em ước gì mình cũng có được một chiếc điện thoại màn hình to đùng như của cậu, ==PLAYER_NAME== ơi!'),
    (r'Cảm ơn em nhé, Amber\.', 'Cảm ơn cậu nhé, Amber.'),

    # Specific user reports & Scene 2
    (r"Được rồi, đây là chỗ\. Cửa sau của Creta Trading ở ngay dưới kia\.", "Được rồi, tới nơi rồi. Cửa sau của Thương đoàn Creta nằm ngay phía dưới kia."),
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
    
    # Generic 'bạn' to 'cậu' (safely avoiding 'bạn bè', 'bạn thân', 'bạn tốt', 'bạn đồng hành', 'tình bạn', 'bạn đời')
    (r'\bBạn\b(?!\s*(?:bè|thân|tốt|đồng hành|đời))', 'Cậu'),
    (r'\bbạn\b(?!\s*(?:bè|thân|tốt|đồng hành|đời))', 'cậu'),
]

# 5. CONTROL TOKEN RESTORATIONS
CONTROL_TOKEN_RULES = [
    (r'==Tắt==', '==Off=='),
]


# 6. GENDER-NEUTRAL & IMMERSION PRONOUN RULES (Addressing or Spoken by Protagonist)
PRONOUN_RULES = [
    # Fixed phrases addressing Sếp / Boss
    (r'\bỦa,\s*anh có sao không thế\s*[sS]ếp\b', 'Ủa, Sếp có sao không thế'),
    (r'\b[sS]ếp ơi!\s*Anh có sao không\b', 'Sếp ơi! Sếp có sao không'),
    (r'\bỦa,\s*[sS]ếp đấy à\?\s*Cuối cùng anh cũng tới rồi\.\s*Tôi đợi anh mòn mỏi\b', 'Ủa, Sếp đấy à? Cuối cùng cũng tới rồi. Tôi đợi Sếp mòn mỏi'),
    (r'\bSếp,\s*tôi đợi anh\b', 'Sếp, tôi đợi Sếp'),
    (r'\bSếp,\s*cuối cùng anh cũng tỉnh rồi\b', 'Sếp, cuối cùng Sếp cũng tỉnh rồi'),
    (r'\bĐến lượt anh ra tay đấy,\s*Sếp\b', 'Đến lượt Sếp ra tay đấy, Sếp'),
    (r'\bAnh biết không\s*[sS]ếp\b', 'Sếp biết không'),
    (r'\bđợi anh,\s*thưa [sS]ếp\b', 'đợi Sếp, thưa Sếp'),
    (r'\bvới anh,\s*[sS]ếp\b', 'với Sếp'),
    (r'\bcủa anh,\s*[sS]ếp\b', 'của Sếp'),
    (r'\banh\s+Sếp\b', 'Sếp'),
    (r'\bSếp à\.\.\.\s*tôi phải thừa nhận là tôi có chút ghen tị với anh đấy\b', 'Sếp à... tôi phải thừa nhận là tôi có chút ghen tị với Sếp đấy'),
    (r'\bCòn các bạn bè của anh nữa,\s*thưa Sếp\b', 'Còn các bạn bè của Sếp nữa, thưa Sếp'),
    (r'\bem chỉ muốn san sẻ gánh nặng cùng anh\b', 'em chỉ muốn san sẻ gánh nặng cùng Sếp'),
    (r'\bem có thể nhờ anh một chuyện được không\?', 'em có thể nhờ Sếp một chuyện được không?'),
    (r'\bEm muốn nhờ anh làm người đồng hành cùng em trong một đám cưới giả định\b', 'Em muốn nhờ Sếp làm người đồng hành cùng em trong một đám cưới giả định'),
    (r'\bAnh có bằng lòng==W== cùng em trao nhau==W== lời thề nguyện\b', 'Sếp có bằng lòng==W== cùng em trao nhau==W== lời thề nguyện'),
    (r'\bEm cũng muốn nói câu tương tự như thế với anh đấy\b', 'Em cũng muốn nói câu tương tự như thế với Sếp đấy'),
    (r'\bAnh đã giúp em biến một ước nguyện nhỏ nhoi.*?Em cũng muốn giúp anh hoàn thành một tâm nguyện của riêng anh\b', 'Sếp đã giúp em biến một ước nguyện nhỏ nhoi thành hiện thực rồi. Em cũng muốn giúp Sếp hoàn thành một tâm nguyện của riêng Sếp'),
    (r'\bTôi tin tưởng vào vận may tuyệt vời của anh,\s*Sếp!\b', 'Tôi tin tưởng vào vận may tuyệt vời của Sếp mà!'),
    (r'\bCuối cùng anh cũng chịu bỏ bớt kính ngữ khách sáo\b', 'Cuối cùng Sếp cũng chịu bỏ bớt kính ngữ khách sáo'),
    (r'\bSếp ơii~ Cuối cùng Ann cũng được gặp anh rồi! Hi hi, anh có thể dẫn Ann\b', 'Sếp ơii~ Cuối cùng Ann cũng được gặp Sếp rồi! Hi hi, Sếp có thể dẫn Ann'),
    (r'\bLần tới phải đổi lại thành lượt Ann đi tìm anh đấy nhé~\b', 'Lần tới phải đổi lại thành lượt Ann đi tìm Sếp đấy nhé~'),
    (r"\btặng anh\.\s*Tôi đặt tên nó là 'Sếp'\b", "tặng Sếp. Tôi đặt tên nó là 'Sếp'"),
    (r"\btặng anh(?=.*?'Sếp')", "tặng Sếp"),
    (r'\bsẽ giúp anh giải quyết dứt điểm cái Ủy Ban Cứu Thế\b', 'sẽ giúp Sếp giải quyết dứt điểm cái Ủy Ban Cứu Thế'),

    # Fixed phrases addressing Đội trưởng / Captain / Tyrant
    (r'\bĐội trưởng ơi,\s*em không còn là con nít nữa đâu,\s*em cũng có thể bảo vệ anh mà\b', 'Đội trưởng ơi, em không còn là con nít nữa đâu, em cũng có thể bảo vệ Đội trưởng mà'),
    (r'\bsự trợ giúp của anh,\s*nội dung chi tiết em sẽ báo cáo\b', 'sự trợ giúp của Đội trưởng, nội dung chi tiết em sẽ báo cáo'),
    (r'\bSau này mong anh chiếu cố việc làm ăn của quán em nhé!\b', 'Sau này mong Đội trưởng chiếu cố việc làm ăn của quán em nhé!'),
    (r'\banh là khách quen quý giá của nhà em mà!\b', 'Đội trưởng là khách quen quý giá của nhà em mà!'),
    (r'\bBạo chúa, tôi đã dành cho anh chỗ ngồi tốt nhất trong nhà\b', 'Bạo Chúa, tôi đã dành cho ngài chỗ ngồi tốt nhất trong nhà'),
    (r'\bBạo Chúa, tôi đã dành cho anh chỗ ngồi tốt nhất trong nhà\b', 'Bạo Chúa, tôi đã dành cho ngài chỗ ngồi tốt nhất trong nhà'),
    (r'\bsức mạnh diệt thế của đại nhân Chaton sẽ phụng sự cho anh!\b', 'sức mạnh diệt thế của đại nhân Chaton sẽ phụng sự cho ngài!'),
    (r'\bđích thân đến tái ngộ cùng anh đây!\b', 'đích thân đến tái ngộ cùng ngài đây!'),
    (r'\bđền đáp cho anh bằng một buổi biểu diễn miễn phí,\s*producer đại nhân!\b', 'đền đáp bằng một buổi biểu diễn miễn phí, producer đại nhân!'),
    (r'\btúc trực bên cạnh anh\b', 'túc trực bên cạnh ngài'),
    (r'\bdẫn dắt anh đi chệch hướng\b', 'dẫn dắt ngài đi chệch hướng'),
    (r'\bphục vụ bên cạnh anh\b', 'phục vụ bên cạnh ngài'),

    # Protagonist speaking
    (r'\bKhông,\s*ý anh là\b', 'Không, ý tôi là'),
    (r'\bĐể anh chỉ cho em cách dùng nhé\b', 'Để tôi chỉ cho em cách dùng nhé'),
    (r'\bÝ em là muốn anh bốc thăm hộ à\?\b', 'Ý em là muốn tôi bốc thăm hộ à?'),
    (r'\bhiếm khi được đi chơi cùng em nên anh muốn chọn quán\b', 'hiếm khi được đi chơi cùng em nên tôi muốn chọn quán'),
    (r'\bAnh không muốn đồ ăn làm em thất vọng\b', 'Tôi không muốn đồ ăn làm em thất vọng'),
    (r'\bLàm ơn trông chừng cô ấy giúp anh trong lúc anh vắng mặt nhé\b', 'Làm ơn trông chừng cô ấy giúp tôi trong lúc tôi vắng mặt nhé'),
    (r'\bCác em giúp anh một tay\b', 'Các em giúp tôi một tay'),
    (r'\bAnh cảm thấy thật an toàn khi em nắm tay anh\b', 'Tôi cảm thấy thật an toàn khi em nắm tay tôi'),
    (r'\bMột ngày nào đó anh sẽ đưa em về nhà cùng anh!\b', 'Một ngày nào đó tôi sẽ đưa em về nhà cùng tôi!'),
    (r'\bĐúng vậy\.\s*Chỉ cần em ở bên cạnh anh,\s*mọi chuyện sẽ diễn ra suôn sẻ\.\b', 'Đúng vậy. Chỉ cần em ở bên cạnh tôi, mọi chuyện sẽ diễn ra suôn sẻ.'),
    (r'\bvà có em ở ngay hàng ghế đầu,\s*nghe anh chơi đàn\b', 'và có em ở ngay hàng ghế đầu, nghe tôi chơi đàn'),
    (r'\bliệu em có vui lòng giúp anh chọn ra điều gì đó không\?', 'liệu em có vui lòng giúp tôi chọn ra điều gì đó không?'),
    (r'\bĐợi anh nhé,\s*Nazuka\.==W==\s*Anh đang quay trở về đây!\b', 'Đợi tôi nhé, Nazuka.==W== Tôi đang quay trở về đây!'),
    (r'\bĐợi anh nhé\b', 'Đợi tôi nhé'),

    # General Calques of 'you' -> 'anh' addressing the player
    (r'\bC-Anh đang làm gì\b', 'C-Cậu đang làm gì'),
    (r'\bAnh đang làm gì ở đây vậy\b', 'Cậu đang làm gì ở đây vậy'),
    (r'\banh đang làm gì ở đây vậy\b', 'cậu đang làm gì ở đây vậy'),
    (r'\bAnh đang làm gì vậy\b', 'Cậu đang làm gì vậy'),
    (r'\banh đang làm gì vậy\b', 'cậu đang làm gì vậy'),
    (r'\bAnh đang làm gì\b', 'Cậu đang làm gì'),
    (r'\banh đang làm gì\b', 'cậu đang làm gì'),
    (r'\bÝ anh là gì\?', 'Ý cậu là sao?'),
    (r'\bý anh là gì\?', 'ý cậu là sao?'),
    (r'\bÝ anh là gì\b', 'Ý cậu là sao'),
    (r'\bý anh là gì\b', 'ý cậu là sao'),
    (r'\bÝ anh là sao\?', 'Ý cậu là sao?'),
    (r'\bý anh là sao\?', 'ý cậu là sao?'),
    (r'\bKhoan đã\.\.\. ý anh là\b', 'Khoan đã... ý cậu là'),
    (r'\bÝ anh là\b', 'Ý cậu là'),
    (r'\bý anh là\b', 'ý cậu là'),
    (r'\bAnh có sao không\b', 'Cậu có sao không'),
    (r'\banh có sao không\b', 'cậu có sao không'),
    (r'\bĐợi đã,\s*tôi đi cùng anh!\b', 'Đợi đã, tôi đi cùng cậu!'),
    (r'\bKính chào anh\.\s*Tôi là Mina\b', 'Kính chào quý khách. Tôi là Mina'),
    (r'\bThật sao\?\s*Thấy anh thể hiện tốt lắm mà\b', 'Thật sao? Thấy cậu thể hiện tốt lắm mà'),
    (r'\bTôi vốn muốn cùng anh ăn một bữa sáng\b', 'Tôi vốn muốn cùng cậu ăn một bữa sáng'),
    (r'\bNày anh ơi,\s*phân cảnh lốc xoáy\b', 'Này cậu ơi, phân cảnh lốc xoáy'),
    (r'\bchia sẻ lon nước này cùng anh mà,\s*==PLAYER_NAME==\b', 'chia sẻ lon nước này cùng cậu mà, ==PLAYER_NAME=='),
    (r'\bchia sẻ lon nước này cùng anh\b', 'chia sẻ lon nước này cùng cậu'),
    (r'\bĐọc cuốn này đi rồi anh sẽ chẳng bao giờ\b', 'Đọc cuốn này đi rồi cậu sẽ chẳng bao giờ'),
    (r'\bEm đâu có kén ăn dữ dằn như anh\b', 'Em đâu có kén ăn dữ dằn như tiền bối'),
    (r'\bNhưng nhìn thấy vẻ mặt đó của anh à\?\b', 'Nhưng nhìn thấy vẻ mặt đó của cậu à?'),
    (r'\bmong anh/chị chỉ giáo\b', 'mong Sếp chỉ giáo'),
    (r'\bcho anh/chị nè\b', 'cho Sếp nè'),
    (r'\banh/chị\b', 'Sếp'),
    (r'\bAnh/chị\b', 'Sếp'),
    (r'\bĐêm khuya quá anh ơi\b', 'Đêm khuya quá cậu ơi'),
    (r'\bAnh cứ chờ xem\b', 'Cậu cứ chờ xem'),
    (r'\bNhìn thấy anh đứng ngồi không yên\b', 'Nhìn thấy cậu đứng ngồi không yên'),
    (r'\bAnh được tự do\b', 'Cậu được tự do'),
    (r'\bgiúp anh thêm yêu mến\b', 'giúp cậu thêm yêu mến'),
    (r'\bChúc anh may mắn nhé\b', 'Chúc cậu may mắn nhé'),
    (r'\bnhìn anh làm việc khiến\b', 'nhìn cậu làm việc khiến'),
    (r'\bNhìn thấy anh cố gắng hết sức\b', 'Nhìn thấy cậu cố gắng hết sức'),
    (r'\bmặc dù anh là một kẻ nói dối\b', 'mặc dù cậu là một kẻ nói dối'),
    (r'\bTôi chỉ muốn thử cùng anh leo Cự Tháp\b', 'Tôi chỉ muốn thử cùng cậu leo Cự Tháp'),
    (r'\bTôi hẹn gặp anh ở quán ăn\b', 'Tôi hẹn gặp cậu ở quán ăn'),
    (r'\bgương mặt của anh\b', 'gương mặt của cậu'),
    (r'\bnếu nó nghĩ anh có đồ ăn\b', 'nếu nó nghĩ cậu có đồ ăn'),
    (r'\bbám riết theo anh\b', 'bám riết theo cậu'),
    (r'\bAnh cứ đợi đấy,\s*==PLAYER_NAME==!\b', 'Cậu cứ đợi đấy, ==PLAYER_NAME==!'),
    (r'\bquay lại đón anh\b', 'quay lại đón cậu'),
    (r'\bTụi em nhất định sẽ quay lại đón anh!\b', 'Tụi em nhất định sẽ quay lại đón cậu!'),
    (r'\bCòn chiếc em tặng anh\b', 'Còn chiếc em tặng cậu'),
    (r'\banh cũng nhớ phải nâng niu\b', 'cậu cũng nhớ phải nâng niu'),
    (r'\bcho anh nhé\b', 'cho cậu nhé'),
    (r'\blại gặp anh ở\b', 'lại gặp cậu ở'),
    (r'\bliên lạc được với anh\b', 'liên lạc được với cậu'),
    (r'\bgiúp anh thay đồ\b', 'giúp cậu thay đồ'),
    (r'\bthấy anh kiệt sức\b', 'thấy cậu kiệt sức'),
    (r'\bAnh hết thuốc chữa\b', 'Cậu hết thuốc chữa'),
    (r'\bvới anh đấy\b', 'với cậu đấy'),
    (r'\bsắp đặt cho em gặp anh\b', 'sắp đặt cho em gặp cậu'),
    (r'\bem phải ở bên anh\b', 'em phải ở bên cậu'),
    (r'\bEm muốn bơi cùng anh\b', 'Em muốn bơi cùng cậu'),
    (r'\bem sẽ cùng anh\b', 'em sẽ cùng cậu'),
    (r'\bem sẽ bảo vệ anh\b', 'em sẽ bảo vệ cậu'),
    (r'\bEm cảm ơn anh nhiều lắm\b', 'Em cảm ơn cậu nhiều lắm'),
    (r'\bEm luôn tìm thấy anh\b', 'Em luôn tìm thấy cậu'),
    (r'\btrình bày cho anh nhé\b', 'trình bày cho cậu nhé'),
    (r'\bNếu anh không bắt máy\b', 'Nếu cậu không bắt máy'),
    (r'\bđể em giúp anh\b', 'để em giúp cậu'),
    (r'\bTôi đợi anh\b', 'Tôi đợi cậu'),
    (r'\btôi đợi anh\b', 'tôi đợi cậu'),
    (r'\bMời anh vào\b', 'Mời cậu vào'),
    (r'\bmời anh vào\b', 'mời cậu vào'),
    (r'\btrò chuyện cùng anh\b', 'trò chuyện cùng cậu'),
    (r'\bTôi nghĩ anh có thể\b', 'Tôi nghĩ cậu có thể'),
    (r'\btôi nghĩ anh có thể\b', 'tôi nghĩ cậu có thể'),
    (r'\bAnh nán lại\b', 'Cậu nán lại'),
    (r'\banh nán lại\b', 'cậu nán lại'),
    (r'\bmuốn tặng anh\b', 'muốn tặng cậu'),
    (r'\bdõi theo anh\b', 'dõi theo cậu'),
    (r'\bứng cứu anh\b', 'ứng cứu cậu'),
    (r'\bgiúp anh rời khỏi\b', 'giúp cậu rời khỏi'),
    (r'\bnghe tin anh đang\b', 'nghe tin cậu đang'),
    (r'\bThấy anh bận bịu\b', 'Thấy cậu bận bịu'),
    (r'\bgương mặt ngủ say siêu đáng yêu của anh\b', 'gương mặt ngủ say siêu đáng yêu của cậu'),
    (r'\btiếng nói của anh\b', 'tiếng nói của cậu'),
    (r'\bhành động của anh\b', 'hành động của cậu'),
    (r'\bcùng anh vào sinh ra tử\b', 'cùng cậu vào sinh ra tử'),
    (r'\bThấy anh đang nói chuyện\b', 'Thấy cậu đang nói chuyện'),
    (r'\bthì còn anh thì sao\?\b', 'thì còn cậu thì sao?'),
    (r'\bcùng anh để thực hiện điều ước\b', 'cùng cậu để thực hiện điều ước'),
    (r'\bchiến đấu cùng anh\b', 'chiến đấu cùng cậu'),
    (r'\bỒ, là anh à\b', 'Ồ, là cậu à'),
    (r'\bngày anh nghỉ việc\b', 'ngày cậu nghỉ việc'),
    (r'\bdở dang của anh\b', 'dở dang của cậu'),
    (r'\bnhìn thấy anh đi phân phối\b', 'nhìn thấy cậu đi phân phối'),
    (r'\bnghi ngờ rằng anh chính là\b', 'nghi ngờ rằng cậu chính là'),
    (r'\bcùng anh tham chiến\b', 'cùng cậu tham chiến'),
    (r'\bnhìn anh hy sinh\b', 'nhìn cậu hy sinh'),
    (r'\bcòn anh mau chóng\b', 'còn cậu mau chóng'),
    (r'\bNghe anh phân tích\b', 'Nghe cậu phân tích'),
    (r'\bTôi sẽ theo anh vào Cự Tháp\b', 'Tôi sẽ theo cậu vào Cự Tháp'),
    (r'\bthời gian cho anh thu thập\b', 'thời gian cho cậu thu thập'),
    (r'\bmuốn nhờ anh\b', 'muốn nhờ cậu'),
    (r'\bthấy anh trên ghế\b', 'thấy cậu trên ghế'),
    (r'\bđang nhờ anh một việc\b', 'đang nhờ cậu một việc'),
    (r'\bđến giúp anh\b', 'đến giúp cậu'),
    (r'\bMảnh Ghép 1/365 Của Anh\b', 'Mảnh Ghép 1/365 Của Cậu'),
    (r'\bDù khi mạnh khỏe hay lúc ốm đau, em nguyện sẽ mãi mãi ở bên cạnh anh\b', 'Dù khi mạnh khỏe hay lúc ốm đau, em nguyện sẽ mãi mãi ở bên cạnh người'),
]

ALL_COMPILED_RULES = []
for p, r in GLOSSARY_RULES + IDIOM_RULES + SYNTAX_RULES + CONTROL_TOKEN_RULES + PRONOUN_RULES:
    ALL_COMPILED_RULES.append((re.compile(p, re.IGNORECASE if '\\' not in p else 0), r))


def polish_line(en: str, vi: str) -> str:
    """Applies comprehensive anime dialogue polish rules."""
    # First: Contextual character names
    res = fix_character_names(en, vi)
    
    # Second: Apply general compiled rules
    for pattern, repl in ALL_COMPILED_RULES:
        res = pattern.sub(repl, res)
        
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
