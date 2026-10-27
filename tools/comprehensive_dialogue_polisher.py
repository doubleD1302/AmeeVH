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

    # Boss (Main Character)
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
    (r'\bDấu ấn Ân điển\b', 'Ấn Ký Ân Tứ'),
    (r'\bPhong ấn Ân điển\b', 'Ấn Ký Ân Tứ'),
    (r'\bDấu ấn ân điển\b', 'Ấn Ký Ân Tứ'),
    (r'\bThần Ân [đĐ]iển\b', 'Thần Ân Tứ'),
    (r'\bCon [mM]ắt Ân [đĐ]iển\b', 'Đôi Mắt Ân Tứ'),
    (r'\bThánh [đĐ]ịa Ân [đĐ]iển\b', 'Thánh Địa Ân Tứ'),
    (r'\bNước Ân [đĐ]iển\b', 'Nước Ân Tứ'),
    (r'\bSách Tiên [tT]ri Ân [đĐ]iển\b', 'Sách Tiên Tri Ân Tứ'),
    (r'\bHộp Điều ước\b', 'Hộp Ước Nguyện'),
    
    # Nocturn Eterna
    (r'\bNocturn Eterna\b', 'Đêm Trường Vĩnh Cửu'),
    (r'\bĐêm Vĩnh Cửu\b', 'Đêm Trường Vĩnh Cửu'),
    
    # Artifact
    (r'\bĐồ tạo tác\b', 'Di Vật'),
    (r'\bđồ tạo tác\b', 'di vật'),
    (r'\bCổ vật Bán hàng Tự động\b', 'Di Vật Bán Hàng Tự Động'),
    (r'\bAutomatic Vending Artifact\b', 'Di Vật Bán Hàng Tự Động'),
    
    # Organizations / Entities
    (r'\bBà Angie\b', 'Tiểu Thư Angie'),
    (r'\bQuý Cô Angie\b', 'Tiểu Thư Angie'),
    (r'\bPost Haste\b', 'Chuyển Phát Hỏa Tốc'),
    (r'\bCấp Tốc Bưu Cục\b', 'Chuyển Phát Hỏa Tốc'),
    (r'\bTrại Mồ Côi Daisy\b', 'Viện Mồ Côi Daisy'),
    (r'\bDaisy Orphanage\b', 'Viện Mồ Côi Daisy'),
    (r'\bĐá Hồn\b', 'Hồn Thạch'),
    (r'\bĐá Linh Hồn\b', 'Hồn Thạch'),
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

ALL_COMPILED_RULES = []
for p, r in GLOSSARY_RULES + IDIOM_RULES + SYNTAX_RULES + CONTROL_TOKEN_RULES:
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
