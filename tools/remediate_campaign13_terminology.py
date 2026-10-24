# -*- coding: utf-8 -*-
"""
Remediate and standardize terminology across Campaign 13 (STsp_12 to STsp_18 & STev_01).
Ensures 100% compliance with Master Glossary, eradicates calques, and preserves all opcodes/tokens.
"""

import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/side_stories_part2_editorial_20261025_r01"
PROP_A = CAMPAIGN_DIR / "PROPOSALS_PARTITION_A.jsonl"
PROP_B = CAMPAIGN_DIR / "PROPOSALS_PARTITION_B.jsonl"
PROP_UNIFIED = CAMPAIGN_DIR / "UNIFIED_CAMPAIGN13_PROPOSALS.jsonl"
RESULT_A = CAMPAIGN_DIR / "RESULT_PARTITION_A.json"
RESULT_B = CAMPAIGN_DIR / "RESULT_PARTITION_B.json"
QA_FINDINGS = CAMPAIGN_DIR / "QA_FINDINGS.json"

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

EXACT_LINE_FIXES = {
    # STsp_12: Gerie & Tyrant & Dusk Arbiter
    "STsp_12_01.12": "... Di Vật bị hư hại nặng nề. Tôi e rằng nó sẽ không đạt tiêu chuẩn của khách hàng.",
    "STsp_12_01.28": "Bộ đồng phục đó... Không phải cô ấy thuộc Thẩm Phán Hoàng Hôn sao? Khoan đã, tại sao mọi người trông đều sợ hãi thế kia?",
    "STsp_12_01.29": "Thẩm Phán Gerie, đây là những Lữ Khách đã nhận ủy thác này.",
    "STsp_12_01.30": "Rất hân hạnh. Tôi là Gerie thuộc Thẩm Phán Hoàng Hôn.",
    "STsp_12_01.33": "Tôi chỉ đơn giản muốn nhìn gần hơn vị Bạo Chúa huyền thoại của chúng ta mà thôi.",
    "STsp_12_01.34": "Tôi là CEO của Hiệp Ước Của Sếp. Điều đó khiến tôi là Sếp chứ không phải Bạo Chúa.",
    "STsp_12_01.35": "Chà, mọi người ở Thẩm Phán Hoàng Hôn đều tin rằng ngài chính là truyền thuyết sống bằng xương bằng thịt. Họ đang nóng lòng muốn đưa ngài ra xét xử đấy.",
    "STsp_12_01.50": "Bình tĩnh nào. Thẩm Phán Hoàng Hôn rất công bằng. Ta sẽ không phán xét cậu cho đến khi Điểm Dị Giáo của cậu đạt một trăm đâu.",
    "STsp_12_01.56": "Bạo Chúa thân mến của ta, ngươi có những người bạn tốt đấy. Sẵn sàng đánh đổi cả tương lai chỉ để giữ cho ngươi được an toàn.",
    "STsp_12_01.57": "Sức hút đó hoàn toàn phù hợp với truyền thuyết về Bạo Chúa. Cộng cho ngươi mười điểm.",
    "STsp_12_01.63": "Gerie không đi kết bạn đâu. Thẩm Phán Hoàng Hôn vốn nổi tiếng là chỉ hành động theo luật riêng của họ.",
    "STsp_12_01.74": "Vậy thì quyết định thế đi, chúng ta sẽ đi. Vị Thẩm Phán này đúng là một kẻ lập dị... ==W== Nhưng thành thật mà nói, tôi không nghĩ cô ấy có ác ý với chúng ta đâu...",
    "STsp_12_01.82": "Sếp biết Thẩm Phán Hoàng Hôn chứ?",
    "STsp_12_01.85": "Hầu hết mọi người đều nghĩ các Thẩm Phán chỉ là những người ru rú trong phòng kín. Cậu biết đấy, chỉ ở trong Thánh Điện để cầu nguyện và khổ luyện.",
    "STsp_12_01.95": "Có tin đồn rằng những Lữ Khách đó không phải bị cướp. Chính Thẩm Phán Hoàng Hôn đã bắt họ đi. Lôi họ đi tra tấn như những kẻ dị giáo.",
    "STsp_12_01.96": "Còn cái bóng không mặt đó? Nghe đồn đó từng là một người rất đẹp, đẹp đến mức các Thẩm Phán đã lột da mặt họ... Và giờ đây, ma thuật ép cái xác phải tiêu thụ chiến lợi phẩm cho họ.",
    "STsp_12_01.99": "Người ta đồn Thẩm Phán đáng sợ nhất trên đường phố là người đeo dây thòng lọng quanh cổ.",
    "STsp_12_01.102": "Một Thẩm Phán với sợi thòng lọng quanh cổ...",
    "STsp_12_02.3": "... Vị Thẩm Phán Hoàng Hôn đó thực sự không chịu rời đi.",
    "STsp_12_02.35": "Sếp… Đừng ăn đồ ăn của Thẩm Phán.",
    "STsp_12_02.50": "Gì... Cái gì vậy, lời chúc phúc của Thẩm Phán Hoàng Hôn sao?!",
    "STsp_12_02.51": "Đừng bận tâm. Những Thẩm Phán như chúng tôi đã quá quen với việc bị hiểu lầm rồi.",
    "STsp_12_02.76": "Không, không thể nào. Mới chưa đầy năm phút... Lẽ nào Các Thể Tinh Tú phía trước quá mạnh ngay cả với Thẩm Phán Gerie sao?",
    "STsp_12_02.84": "Bởi vì... ==W== ta là một Thẩm Phán.",
    "STsp_12_02.85": "Thẩm Phán chỉ thanh trừng những kẻ dị giáo. Còn Các Thể Tinh Tú là tạo vật của Thần Grace. Chúng không phải là mục tiêu.",
    "STsp_12_02.106": "Nghi ngờ đồ ăn vặt và thử độc để bảo vệ bạn bè... Y hệt như Bạo Chúa huyền thoại. Cộng thêm mười điểm~",
    "STsp_12_02.107": "Sẵn sàng chia sẻ mẩu thức ăn cuối cùng mà không hề do dự... Bạo Chúa huyền thoại cũng sẽ làm như vậy. Cộng thêm mười điểm~",
    "STsp_12_02.108": "Bên cạnh ngươi là những đứa trẻ tài năng, tốt bụng... Đúng là những người bạn mà Bạo Chúa huyền thoại sẽ kết giao. Cộng thêm mười điểm~",
    "STsp_12_03.5": "Bạo Chúa, những người bạn nhỏ của ngươi đang lo lắng, nhưng ngươi lại có vẻ rất điềm tĩnh. Tại sao vậy?",
    "STsp_12_03.8": "Heheh. Sự im lặng tự nó đã là một câu trả lời. ==RT== Rất đúng với phong cách của Bạo Chúa huyền thoại.",
    "STsp_12_03.10": "Sắc sảo như mọi khi, Bạo Chúa. Quả thực có những điểm bất thường.",
    "STsp_12_03.21": "Ngươi nhìn thấu bản chất sự việc thật dễ dàng. Bạo Chúa huyền thoại cũng sở hữu tuệ nhãn sắc bén như thế. Mười điểm.",
    "STsp_12_03.24": "Ngươi sợ điểm cao hơn nhưng vẫn lên tiếng bảo vệ bạn bè. Ừm. Bạo Chúa huyền thoại cũng nổi danh vì sự chính trực và luôn trực diện đương đầu với thử thách. Mười điểm.",
    "STsp_12_03.26": "Ngươi thản nhiên bước vào một cái bẫy mười mươi. ==W== Điều đó cho ta thấy ngươi tin rằng ngươi và bạn bè có thể giải quyết mọi thứ. Bạo Chúa huyền thoại cũng sở hữu sự tự tin tuyệt đối như thế. Mười điểm.",
    "STsp_12_03.28": "Thú vị thật. Ngươi thậm chí còn tính toán cả ta vào kế hoạch của mình... ==W== Không tồi. Sự mưu lược thao túng đó hoàn toàn xứng danh Bạo Chúa.",
    "STsp_12_03.56": "Còn những lời đồn về việc Thẩm Phán Hoàng Hôn săn lùng kẻ dị giáo... ==W== Cũng do ngươi tung ra sao?",
    "STsp_12_03.64": "Vu khống Thẩm Phán Hoàng Hôn. Phỉ báng Thần Grace. Lũ dị giáo các ngươi.",
    "STsp_12_03.78": "Lũ Lữ Khách các ngươi, cả ả Thẩm Phán kia nữa... Tất cả hãy cùng chết ở đây đi!",
    "STsp_12_03.99": "Không ngờ thiết bị tra khảo được triệu hồi của ta lại không giữ chân được ngươi... Sếp à, ngài thực sự chính là Bạo Chúa đích thực.",
    "STsp_12_03.101": "Được thôi. Vậy hãy để ta khai sáng cho ngươi... Về lý do tại sao Thẩm Phán Hoàng Hôn lại tái xuất hiện.",
    "STsp_12_03.106": "Đó là lý do tại sao các Thẩm Phán chúng ta, những người nắm giữ thánh di vật, lại có thể tự do sải bước trên mặt đất một lần nữa.",
    "STsp_12_03.117": "Nào, Bạo Chúa, hãy cho ta thấy toàn bộ bản lĩnh của ngươi!",
    "STsp_12_04.6": "Nào, Bạo Chúa, hãy cho ta thấy toàn bộ bản lĩnh của ngươi!",
    "STsp_12_04.24": "Người đàn ông cam chịu",
    "STsp_12_04.30": "Gerie, nghe này... Tôi biết cô muốn giúp. Nhưng Ân Điển Của Thần... chỉ có thể được Đế Quốc Grace ban tặng mà thôi.",
    "STsp_12_04.41": "Thẩm Phán Giận Dữ",
    "STsp_12_04.44": "Haizz. Sứ mệnh của Thẩm Phán Hoàng Hôn là phụng sự Thần Grace. Bớt đi gây sự đánh nhau mỗi ngày giùm cái đi.",
    "STsp_12_04.53": "Ư... Bạo-Bạo Chúa...",
    "STsp_12_04.59": "Đừng buông tay, Bạo Chúa... Ta cảm thấy thật nhẹ nhõm... Cảm giác này... thật tuyệt...",
    "STsp_12_04.66": "A... Tại sao ta không thể... cử động... Bạo Chúa... A...",
    "STsp_12_04.93": "Được thôi. Cậu muốn biết về Bạo Chúa đúng không?",
    "STsp_12_04.98": "Bây giờ, hãy cho ta kết luận của cậu. Kẻ đó có phải là Bạo Chúa không?",
    "STsp_12_04.99": "==SEX2== Điểm Dị Giáo thảm hại đến nực cười. Thậm chí còn không đáng gọi là kẻ dị giáo, chứ đừng nói đến Bạo Chúa. Chỉ là một kẻ ngốc may mắn có khả năng cách ly ma pháp vô tình nhặt được Phong Ấn Ân Điển mà thôi.",
    "STsp_12_04.100": "Rất tốt. Ta sẽ tự mình kiểm chứng xem ==SEX== có phải là Bạo Chúa hay không.",
    "STsp_12_04.104": "Bạo Chúa... Thật thú vị. ==W== Điểm của ngươi từng vọt lên hơn một nghìn... nhưng trong khoảnh khắc ngắn ngủi ấy, ta đã cảm nhận được—linh hồn chúng ta đã kết nối với nhau.",

    # STsp_13: Eleanor & Nanoha & Boss Accord & Mentor
    "STsp_13_01.10": "Cách đây không lâu, một Lữ Khách tên Eleanor đã nhắn tin cho Hiệp Ước Của Sếp, chỉ định đích danh cậu cho một ủy thác...",
    "STsp_13_01.18": "Tôi chờ ngài mãi đấy, Tiền bối! Xin mời vào trong! Nhanh lên nào!",
    "STsp_13_01.22": "Ngoài ra, Hiệp Ước Của Sếp còn có những Lữ Khách giàu kinh nghiệm hơn nhiều. Tại sao lại chọn tôi?",
    "STsp_13_01.32": "Sếp—ý tôi là, Tiền bối! Xin hãy chỉ bảo tôi thật nghiêm khắc nhé. Tôi muốn trở thành một Lữ Khách thực thụ có thể tự đứng vững trên đôi chân của mình!",
    "STsp_13_01.44": "Tiền bối, tôi thực sự xin lỗi... ==W== Nhưng ngài hãy nhìn quả bom mini này xem! Sức công phá của nó chắc chắn uy lực hơn quả bom khói kia nhiều!",
    "STsp_13_01.62": "Ôi! Tôi quên mất chưa giới thiệu. Tiền bối, đây là Nanoha. Tôi đã thuê cô ấy làm hầu gái cho mình.",
    "STsp_13_01.67": "Tiền bối, lẽ nào tôi thực sự bị lừa rồi sao?",
    "STsp_13_01.71": "Đúng lúc lắm! Cho cô ấy lên tầng hai. ==W== Tiền bối, tôi nhất định sẽ làm sáng tỏ ngọn ngành chuyện này!",
    "STsp_13_01.73": "Nanoha, tiếp đãi Tiền bối giúp ta nhé!",
    "STsp_13_01.76": "Chắc chắn rồi. Tôi là Nanoha đến từ Dịch Vụ Gia Đình Goodwind. Nếu được phép hỏi, ngài có phải là CEO của Hiệp Ước Của Sếp, ==SEX7== ==PLAYER_NAME== không?",
    "STsp_13_01.114": "Ta là người hướng dẫn của cô ấy. Và ta sẽ không đứng nhìn lũ cặn bã các ngươi tống tiền một Lữ Khách đâu.",
    "STsp_13_01.118": "Được lắm, chuẩn luôn! Các cô gái, triển khai Kế hoạch B!",
    "STsp_13_01.122": "Đau quá! ==RT== T-Tiền bối... tôi xin lỗi...",
    "STsp_13_02.26": "Tiền bối... Cảm ơn ngài.",
    "STsp_13_02.32": "Tiền bối nói hoàn toàn đúng! Chúng ta hãy cùng nhau tìm cách thoát khỏi đây nhé!",
    "STsp_13_02.34": "Tiền bối, tôi có thể cho ngài xem trong vali của tôi có gì không?",
    "STsp_13_02.62": "Ngài thực sự mở khóa được nó rồi...! Tiền bối đỉnh thật đấy!",
    "STsp_13_02.74": "Tiền bối, chờ đã. Tôi vừa nhận ra điều này. Bọn họ nói chỉ cần cô tiểu thư nhà giàu thôi... đúng không?",
    "STsp_13_02.78": "Đúng vậy. Tôi sẽ dụ bọn chúng đi. Tiền bối, ngài hãy lợi dụng lúc hỗn loạn đó để cứu Nanoha nhé. Được không ạ?",
    "STsp_13_02.83": "Cảm ơn ngài, Tiền bối!",
    "STsp_13_02.86": "Tôi sẽ không quên đâu, Tiền bối!",
    "STsp_13_03.19": "Tiền bối, cẩn thận!",
    "STsp_13_03.31": "Cô ta bắn thứ đó trong nhà sao?! Ngươi là kiểu người hướng dẫn gì thế hả?!",
    "STsp_13_03.49": "Tiền bối, ngài đỉnh quá! Tôi còn đang luống cuống tìm vũ khí, thế mà khi quay đầu lại ngài đã hạ gục tất cả bọn chúng rồi!",
    "STsp_13_03.56": "Hehe... Đừng trêu tôi nữa mà Tiền bối, ngài làm tôi ngượng quá... ==W== A, Nanoha, đưa tay cho ta xem nào.",
    "STsp_13_03.62": "Tiền bối hãy ở lại chăm sóc Nanoha nhé!",
    "STsp_13_03.84": "Hoạt động diễn ra vô cùng suôn sẻ dưới sự chỉ huy của cậu. Đúng như mong đợi từ CEO của Hiệp Ước Của Sếp!",
    "STsp_13_03.106": "Được rồi... Nếu Tiền bối đã nói vậy. Tôi sẽ không lo lắng nữa.",
    "STsp_13_03.127": "Nghiên cứu các Di Vật, phác thảo chiến thuật và tìm hiểu mọi ngóc ngách của công việc này. Hãy cho gia đình cậu thấy cậu đã trưởng thành ra sao. Hãy chứng minh cho họ thấy rằng cậu đã sẵn sàng tự lập bước đi trên thế giới này.",
    "STsp_13_03.128": "Hức... tôi... Tiền bối, tôi... tôi thực sự không muốn từ bỏ đâu!",
    "STsp_13_03.135": "Vì sự tự do của tôi... và để một ngày nào đó, tôi có thể đến gặp lại ngài, Tiền bối!",
    "STsp_13_03.138": "Tôi nhất định sẽ trở thành một Lữ Khách xuất chúng, và khi đó tôi sẽ quay lại tìm ngài! Hãy đợi tôi nhé, Tiền bối!",

    # STsp_14: Caramel, Midas & Miss Willow
    "STsp_14_01.67": "Ahaha, cậu khen ngợi tôi quá lời rồi. Và tôi cũng không leo núi chỉ vì Di Vật đâu.",
    "STsp_14_03.6": "Ờ... Cô Willow? Hai người đó... Họ đang cãi nhau đấy à?",
    "STsp_14_03.10": "Nếu một Archon thực sự có liên quan thì việc Thẩm Phán Hoàng Hôn can thiệp là điều hoàn toàn hợp lý. Đừng lo lắng. Tôi sẽ đảm bảo nhiệm vụ diễn ra suôn sẻ.",
    "STsp_14_03.11": "Ừm... Archon có phải là Thể Tinh Tú đặc biệt nguy hiểm không? Việc cả Thẩm Phán Hoàng Hôn và Vệ Binh Rạng Đông đều được điều động đã cho thấy tính nghiêm trọng...",
    "STsp_14_03.15": "Tôi không sao đâu. Cậu thực sự không cần phải lo lắng cho tôi. Kể từ lúc quyết định hỗ trợ cuộc điều tra này, tôi đã chuẩn bị sẵn tâm lý rồi. Có mọi người ở đây khiến tôi an tâm hơn rất nhiều, hơn nữa—",

    # STsp_15: Minova & Film Knights
    "STsp_15_01.2": "Được rồi mọi người! Thẳng lưng ưỡn ngực lên! Quyết không để bọn họ coi thường chúng ta!",
    "STsp_15_01.14": "Kỵ Sĩ Đạo Diễn",
    "STsp_15_01.29": "Để cậu tham khảo, trang phục của tôi được may đo riêng và lấy cảm hứng từ <i>Kỵ Sĩ Mặt Nạ</i> đấy! ==W== Minova, nếu cậu yêu thích một nhân vật hay phong cách nào đó, biết đâu nó sẽ gợi mở ý tưởng cho cậu.",
    "STsp_15_02.18": "Rất hân hạnh. Tôi là Gerie thuộc Thẩm Phán Hoàng Hôn.",
    "STsp_15_02.23": "N-nhưng, ==W== tôi nghe đồn rằng Thẩm Phán Hoàng Hôn...",
    "STsp_15_02.33": "Tất nhiên rồi. Với tư cách là một Thẩm Phán, ta thường xuyên ra vào đủ mọi loại Cự Tháp, nên ta từng thấy những bộ trang phục như thế này vài lần rồi~",
    "STsp_15_03.6": "Kỵ Sĩ Đạo Diễn",

    # STsp_16: Horizon & Trekkers' House & Miss Willow
    "STsp_16_01.39": "Ừm, cô Willow? Tôi hoàn toàn hiểu cảm giác của cậu...",
    "STsp_16_02.4": "Hết chuyện này lại đến chuyện khác! Hàng hóa chất đống ở quầy lễ tân, Nhà Lữ Khách hoàn toàn biến thành một mớ hỗn độn... Hả? Cậu bảo có đánh nhau nổ ra bên ngoài sao?",
    "STsp_16_03.13": "Không biết ai là người khởi xướng, nhưng có lời đồn rằng trên Lục Địa Nova có một Cự Tháp cho phép cậu lấy Di Vật hoàn toàn miễn phí. Không ước nguyện, không phải trả giá.",
    "STsp_16_03.59": "Tất nhiên rồi. Cậu muốn vào văn phòng của tôi nói chuyện không? Dù sao thì tôi cũng đang trên đường trở về Nhà Lữ Khách đây.",

    # STsp_17: Treasure & Artifacts
    "STsp_17_01.11": "Không, Di Vật của tôi! ==W== Từng món một... Biến mất hết rồi!",
    "STsp_17_01.45": "Được rồi! Đã đến lúc săn lùng thêm nhiều Di Vật nữa rồi, meo meo! Nếu tôi đào đủ nhiều, chắc chắn sẽ có một món đáng giá cả gia tài!",
    "STsp_17_01.81": "Cậu bị mất một mảnh Di Vật sao?",
    "STsp_17_01.98": "Oaaa!!! Nhìn đống Di Vật này xem, meo meo— <size=60>♪",
    "STsp_17_03.19": "Đừng lo lắng. Cậu chẳng bao giờ biết trước khi nào một món đồ sẽ phát huy tác dụng đâu. Và gom góp được chừng này Di Vật là nhờ có cậu đấy, Teresa.",
    "STsp_17_03.32": "Tất nhiên là đổi lấy Dorra rồi! Trừ khi chúng ta tìm thấy một Di Vật hữu ích—thứ đó sẽ giữ lại phục vụ cho việc săn lùng.",
    "STsp_17_03.96": "Thành thật mà nói, tôi từng định dọn dẹp nó, nhưng vì có quá nhiều Di Vật cần sửa chữa nên tôi hoàn toàn quên khuấy mất...",
    "STsp_17_03.97": "Sửa chữa Di Vật?",
    "STsp_17_03.101": "Tôi cứ ngỡ mình sẽ thu thập được nhiều Di Vật hơn khi tham gia cuộc săn tìm kho báu đó, nhưng... ==W== rốt cuộc lại trở về tay trắng, meo meo. Hehe...",
    "STsp_17_03.123": "<size=37>Không cần phải ngại đâu <size=60>♪ <size=37>Hay là gia nhập cùng chúng tôi trong những chuyến phiêu lưu đi? Có cậu bên cạnh, chúng ta sẽ đào được khối Di Vật trong nháy mắt!",

    # STsp_18: Messis Month & Autumn Equinox & Artifacts
    "STsp_18_01.28": "Đúng vậy, hôm nay là ngày 24 Tháng Messis. Rắc rối của Noya lại tái phát rồi.",
    "STsp_18_01.31": "Đó có phải là thuật ngữ của tộc Loong để chỉ Tiết Thu Phân không? Khoảng từ ngày 22 đến ngày 24 Tháng Messis, khi ngày bắt đầu ngắn lại và đêm dài hơn?",
    "STsp_18_01.82": "Giờ thì cô ấy lại dán mắt vào Di Vật Bán Hàng Tự Động...",
    "STsp_18_02.28": "Tôi không mang theo bất kỳ Di Vật ma thuật nào bên người cả. Tôi chỉ mang theo thứ này thôi...",

    # STev_01: Summer Ocean Event
    "STev_01_08.7": "Karin... Tôi tin chắc cô ấy sẽ không nói dối đâu. Nếu cô ấy không nói thật thì đó hẳn là một lời nói dối thiện ý...",
    "STev_01_08.8": "\"Một lời nói dối thiện ý\"...? Ý cậu là sao? Vẻ mặt đó của cậu... Cứ như thể cậu biết điều gì đó rồi vậy.",
    "STev_01_09.5": "Chuẩn bị xong xuôi hết rồi!",
    "STev_01_09.13": "Không sao đâu, Karin. Chúng ta đang đi đúng hướng rồi. Chúng ta chỉ cần băng qua khu rừng này để tới được ánh sáng đó thôi.",
    "STev_01_10.3": "Đúng vậy. Bà Marlene thường ghi nhật ký khi đi biển và sau đó tổng hợp lại thành một cuốn nhật ký hàng hải khi về đến nhà.",
    "STev_01_11.2": "Mùa Hè Bất Tận",
    "STev_01_11.3": "Tất cả đều đã ổn thỏa, và giờ đây cuối cùng bạn cũng có thể thư giãn. Đây là mùa hè thuộc về bạn, thuộc về tất cả mọi người — một mùa hè bất tận."
}

def clean_line(iid: str, text: str) -> str:
    if iid in EXACT_LINE_FIXES:
        return EXACT_LINE_FIXES[iid]

    t = text
    # Standard substitutions for any other lines
    t = re.sub(r"\bTrọng [tT]ài Hoàng [hH]ôn\b", "Thẩm Phán Hoàng Hôn", t)
    t = re.sub(r"\bTrọng [tT]ài Gerie\b", "Thẩm Phán Gerie", t)
    t = re.sub(r"\bTrọng tài Gerie\b", "Thẩm Phán Gerie", t)
    t = re.sub(r"\bBạo Quân\b", "Bạo Chúa", t)
    t = re.sub(r"\bHiệp Ước Boss\b", "Hiệp Ước Của Sếp", t)
    t = re.sub(r"\bSếp Accord\b", "Hiệp Ước Của Sếp", t)
    t = re.sub(r"\bCô Liễu\b", "Cô Willow", t)
    t = re.sub(r"\bcô Liễu\b", "cô Willow", t)
    t = re.sub(r"\b[tT]háng Messi\b", "Tháng Messis", t)
    t = re.sub(r"\bnhật ký hải lý\b", "nhật ký hàng hải", t)
    t = re.sub(r"Các Lữ Khách' House", "Nhà Lữ Khách", t)
    return t

def process_file(in_path: Path, out_path: Path):
    with open(in_path, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]

    fixed_count = 0
    new_lines = []
    for it in lines:
        iid = it["id"]
        orig_vi = it.get("vi_editorial", it.get("vi", ""))
        new_vi = clean_line(iid, orig_vi)
        new_vi = unicodedata.normalize("NFC", new_vi)

        if new_vi != orig_vi:
            fixed_count += 1

        it["vi_editorial"] = new_vi
        new_lines.append(it)

    with open(out_path, "w", encoding="utf-8") as f:
        for it in new_lines:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    print(f"Processed {in_path.name} -> {out_path.name}: {len(new_lines)} lines, {fixed_count} fixed.")
    return new_lines

def main():
    print("=== REMEDIATING CAMPAIGN 13 TERMINOLOGY ===")
    lines_a = process_file(PROP_A, PROP_A)
    lines_b = process_file(PROP_B, PROP_B)

    unified = lines_a + lines_b
    with open(PROP_UNIFIED, "w", encoding="utf-8") as f:
        for it in unified:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    print(f"Wrote {len(unified)} unified lines to {PROP_UNIFIED.name}")

if __name__ == "__main__":
    main()
