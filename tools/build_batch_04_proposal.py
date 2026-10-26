# -*- coding: utf-8 -*-
"""
Build script for BATCH_FIX_04_STORY_SHORT_LINES.json
Generates the complete proposal with 306 items:
- 19 token fixes
- 36 special idioms & lore recovery
- 58 calque fixes ('That's why' -> natural Vietnamese)
- 193 untranslated lines (short lines & missed dialogues)
"""

import os
import sys
import json
import unicodedata
import re
from pathlib import Path

ROOT = Path("C:/YostarGames/StellaSora_EN/StellaSora_VietHoa")
INPUT_FILE = ROOT / "work/batches/BATCH_04_INPUTS.json"
OUTPUT_FILE = ROOT / "work/batches/BATCH_FIX_04_STORY_SHORT_LINES.json"

tag_re = re.compile(r'<[^>]+>|\{[^{}]+\}|%\d*\$?[sdf]|==[A-Z0-9_]+==|\\n')

def extract_tokens(s):
    return tag_re.findall(s)

def normalize_nfc(s):
    return unicodedata.normalize('NFC', s)

# Load inputs
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    inputs = json.load(f)

assert len(inputs) == 306, f"Expected 306 items, got {len(inputs)}"

# Define G1: Token fixes (19 items)
G1_FIXES = {
    18: (
        "==W==<size=50>Oa!!",
        "Khôi phục cú pháp token gốc, loại bỏ thẻ đóng </size> không có trong source EN."
    ),
    19: (
        "Mình đang mơ sao ta?==RT====W==Khoan đã, không phải mơ! Sếp ơi? <size=40>Sếp ơi? <size=45>Sếp ơi, <size=50>Sếp ơi! <size=55>Sếp ơiii~!",
        "Bảo toàn chuỗi kích thước chữ động, loại bỏ thẻ đóng </size> không có trong source EN."
    ),
    20: (
        "Ann dạo này có ngoan ngoãn không đấy...==W==<size=50> Oái!",
        "Bảo toàn thẻ cỡ chữ <size=50> không có thẻ đóng, dịch tiếng thốt tự nhiên."
    ),
    21: (
        "==W==<size=50>Gàoooooo...",
        "Bảo toàn cấu trúc token ==W== và <size=50>, loại bỏ </size> thừa."
    ),
    22: (
        "==W==<size=50>Khoan đã Freesia, tôi chưa kịp chuẩn bị tinh thần— ",
        "Khôi phục token <size=50>, loại bỏ </size> không có trong source."
    ),
    23: (
        "==W==<size=50>Ngươi! Cút ngay khỏi đây cho ta! Ngươi nghe rõ chưa hả?",
        "Loại bỏ </size> thừa, bảo toàn cấu trúc token gốc."
    ),
    24: (
        "==W==<size=50>Tôi sẽ không đi đâu hết cho tới khi ông trả lại đúng những gì thuộc về tôi!",
        "Khôi phục đúng token nguồn, loại bỏ thẻ đóng </size> dư thừa."
    ),
    25: (
        "<size=50>Trúng đích rồi!",
        "Bảo toàn token <size=50>, loại bỏ </size> dư."
    ),
    26: (
        "<size=50>==W==Này—! Ở đây có chuyện gì thế hả? Sao chỗ này lại đông nghẹt thế này?!",
        "Bảo toàn thứ tự token <size=50>==W==, loại bỏ </size> thừa."
    ),
    27: (
        "==W==<size=50>C-Chuyện gì đang xảy ra thế này...?",
        "Khôi phục token ==W==<size=50>, loại bỏ </size> thừa."
    ),
    28: (
        "<size=35>Thực lòng mà nói, em vẫn đang đắn đo xem có nên nhờ Sếp giúp đỡ một chuyện mang tính riêng tư thế này không nữa...",
        "Khôi phục đúng token <size=35>, loại bỏ </size> thừa."
    ),
    29: (
        "<size=50>==W==Cứu với! Fannie! Fan—nie ơiiii!!",
        "Bảo toàn <size=50>==W==, loại bỏ </size> thừa."
    ),
    31: (
        "<size=50>Thôi chết rồi! Không xong rồi! Chỉ còn đúng hai tiếng nữa là mở màn thôi đấy!",
        "Bảo toàn token <size=50>, loại bỏ </size> thừa."
    ),
    32: (
        " <size=30>Đặc biệt là người, người đã vì tôi mà nỗ lực vất vả nhường ấy.",
        "Khôi phục khoảng trắng đầu dòng và thẻ <size=30>, loại bỏ </size> thừa."
    ),
    53: (
        "Sao nào?==W====RT== Chà, chà, chà, chà, chà...==W== Chẳng phải là Sếp yêu quý đó sao? ♪",
        "Loại bỏ thẻ lạ <r=mowang></r>, bảo toàn các token ==W==, ==RT==, dịch tự nhiên ngọt ngào."
    ),
    211: (
        "Không, đừng có mơ. Lũ kia, mau quay lại làm việc ngay!",
        "Loại bỏ điều khiển ==W== không có trong nguồn, diễn đạt dứt khoát tự nhiên."
    ),
    258: (
        "<r=My...>Hự! </r><r=My arms...>Hự! </r>Hự... <r=It hurts...>Á</r>... <r=It hurts...>Á</r>...",
        "Bảo toàn nguyên vẹn 100% token cú pháp ruby <r=...>, dịch tiếng rên đau đớn chân thực."
    ),
    259: (
        "<r=Legs...>Ư</r>... Ư<r=My legs...></r>—Ư...!==W== <r=Anyone... Please...>Khụ</r>...==W== <r=Help me...>Ư</r>...",
        "Bảo toàn nguyên vẹn 100% token cú pháp ruby <r=...>, ==W==, dịch tiếng thều thào nghẹn ngào."
    ),
    289: (
        "Tôi xin lỗi!==W== Xin hãy tha cho tôi đi mà!",
        "Khắc phục lỗi lặp câu và dư thừa thẻ ==W==, dịch tự nhiên van nài tha mạng."
    )
}

# Define G3: Special idioms & Lore (36 items)
G3_FIXES = {
    16: (
        "Bởi vậy trước đó chú Lizi mới hỏi xem liệu lần này cô ấy có đăng ký tham gia không. Ai mà bốc thăm trúng cô ấy ở vòng đầu thì coi như có thể chuẩn bị sẵn cho đối thủ ở vòng thứ hai luôn rồi.",
        "Sửa lỗi thành ngữ 'draws her in the first round' thành 'bốc thăm trúng cô ấy ở vòng đầu', khắc phục calque 'That's why'."
    ),
    55: (
        "Chết tiệt... Cứ theo đà này, kế hoạch làm cô ấy vui lên của mình sẽ đổ sông đổ bể mất...",
        "Sửa cụm từ lặp 'đổ bể mất bể mất' thành 'đổ sông đổ bể mất'."
    ),
    65: (
        "Làm tốt lắm! Bây giờ chúng ta sẽ tiến hành kiểm tra nhé~",
        "Trau chuốt 'Excellent work!' thành lời khen ngợi tự nhiên 'Làm tốt lắm!', loại bỏ calque danh từ 'Công việc tuyệt vời'."
    ),
    68: (
        "Có vẻ như cô ấy đang bấu víu vào tia hy vọng mong manh...",
        "Sửa thành ngữ 'grasping at straws' thành 'bấu víu vào tia hy vọng mong manh', loại bỏ nghĩa đen 'nắm ống hút'."
    ),
    70: (
        "Chính xác. Cuộc thẩm vấn đó thực sự khiến tôi căng thẳng vô cùng, người cứ gồng cứng đờ ra...==W== Giờ thì ê ẩm khắp cả người rồi, tôi rất cần ai đó xoa bóp giãn cơ giúp đây!",
        "Sửa thành ngữ 'work out those knots' thành 'xoa bóp giãn cơ', thoát ý câu 'ôm mình cứng đờ'."
    ),
    76: (
        "Hửm? Tưởng cậu cày cuốc cật lực thế này là để kiếm một kỳ nghỉ cơ mà?",
        "Chuốt lại câu văn mượt mà, thoát ý 'làm việc chăm chỉ này để có được một kỳ nghỉ'."
    ),
    78: (
        "Một cô bé ư? Nghe cũng thấy quen quen đấy...==W== Nhưng sao con bé lại viết thư cho tôi nhỉ?",
        "Sửa đúng thành ngữ 'ring a bell' thành 'nghe cũng thấy quen quen', loại bỏ calque 'đáng chú ý'."
    ),
    85: (
        "Từ chỗ này nhìn ra, góc ngắm đỉnh thật đấy!",
        "Sửa thành ngữ 'get a perfect view' thành 'góc ngắm đỉnh thật đấy', loại bỏ calque 'có được một cái nhìn hoàn hảo'."
    ),
    90: (
        "Cứ thuận theo tự nhiên đi! Biết đâu đấy? Có khi lại có mấy chú yêu tinh ma thuật lẻn vào làm nốt việc giúp cậu thì sao.",
        "Sửa thành ngữ 'go with the flow' thành 'thuận theo tự nhiên', loại bỏ nghĩa đen 'đi theo dòng chảy'."
    ),
    95: (
        "Tôi là Eleanor, \"Quý Cô Lữ Khách\". Những kỹ thuật vẽ vời của giới thượng lưu làm sao có thể lột tả được người Lữ Khách trong tôi ngày hôm nay? Tôi cần phải quên đi các công thức, lý thuyết và quy tắc... Tôi sẽ vẽ bằng cả trái tim.==W== Chỉ có như vậy mới thể hiện trọn vẹn con người tôi lúc này.",
        "Sửa 'high-society techniques' thành 'kỹ thuật vẽ vời của giới thượng lưu' và 'do justice' thành 'thể hiện trọn vẹn con người tôi'."
    ),
    100: (
        "Chương trình giảm giá bất ngờ khiến ai nấy đều sướng rơn lên. Trực giác mách bảo tôi đây là \"cạm bẫy\", nhưng mọi người đã đẩy tôi vào thang máy trước khi tôi kịp mở lời phản đối.",
        "Sửa thành ngữ 'My gut screams trap' thành 'Trực giác mách bảo tôi đây là cạm bẫy', loại bỏ nghĩa đen 'ruột tôi kêu lên'."
    ),
    127: (
        "Quanh đây có thể câu được cá quý hiếm và sò điệp khổng lồ đấy. Chúng bán được giá hời lắm, nên vài Lữ Khách thường tìm đến đây thử vận may.",
        "Sửa thành ngữ 'sell for a pretty penny' thành 'bán được giá hời lắm', thay đại từ 'họ' bằng 'chúng'."
    ),
    145: (
        "Sau các buổi lễ hội Tuyết, tôi luôn đến đây để dùng ma pháp vẽ nên những chú cá...==W== Và chúng cũng đáp lại tôi bằng ánh sáng lung linh rực rỡ... Có thế tôi mới yên tâm khép lại một ngày.",
        "Sửa thành ngữ 'call it a day' thành 'yên tâm khép lại một ngày', loại bỏ lỗi lặp từ 'lễ hội Lễ hội Tuyết'."
    ),
    147: (
        "Từ những kẻ buôn lậu, bạn biết được sự thật đằng sau việc những người bạn của mình mất tích. Bạn quyết định dấn thân giải cứu tại Thạch Cột, nhưng tên thủ lĩnh đã run rẩy đưa ra lời cảnh báo—\"Niên Thú\" huyền thoại đang ngự trị bên trong.",
        "Sửa 'trembling warning' thành 'run rẩy đưa ra lời cảnh báo', thống nhất đại từ xưng hô 'bạn'."
    ),
    155: (
        "Thật vô phép! Ở trường thầy cô chưa từng dạy ngươi không được cắt ngang lời người khác đang nói sao?!",
        "Thống nhất đại từ xưng hô 'ngươi', trau chuốt giọng điệu gay gắt kiêu hãnh chuẩn phong cách RPG."
    ),
    156: (
        "Sơ suất quá. Hồi đi học môn duy nhất ta quan tâm là thể dục thôi.",
        "Sửa lỗi thành ngữ 'My bad' thành 'Sơ suất quá', loại bỏ dịch thô 'Cái xấu của tôi'."
    ),
    157: (
        "Ta cũng ghét nhất cái loại đó.==W== Thế này thì tiễn ngươi lên đường khỏi thấy áy náy. Đỡ mất công.",
        "Sửa thành ngữ 'Saves me the trouble' thành 'Đỡ mất công', 'killing you guilt-free' thành 'tiễn ngươi lên đường khỏi thấy áy náy'."
    ),
    162: (
        "Ngươi đúng là không hổ danh Bạo Chúa, một mũi tên trúng hai đích. Rốt cuộc ngươi tham lam đến mức nào vậy hả?",
        "Sửa thành ngữ 'killing two birds with one stone' thành 'một mũi tên trúng hai đích', loại bỏ nghĩa đen 'giết hai con chim bằng một hòn đá'."
    ),
    163: (
        "Có vẻ như mọi người đều đồng lòng rồi nhỉ! Vậy thì, người dẫn dắt Cấp Tốc Bưu Cục, quyết định của cậu thế nào?",
        "Sửa thành ngữ 'on the same page' thành 'đồng lòng' và 'what's the call' thành 'quyết định của cậu thế nào'."
    ),
    170: (
        "Tôi đã âm thầm điều tra, tận dụng mọi mối quan hệ từ thời đại học để moi thông tin về Mắt Thần Grace...",
        "Sửa thành ngữ 'pulling every string' thành 'tận dụng mọi mối quan hệ', loại bỏ nghĩa đen 'lôi từng sợi dây'."
    ),
    175: (
        "Phải, ngoài kia đúng là một cơn ác mộng.==W== Nói ngắn gọn lại, chúng ta phải rời khỏi đây. Ngay lập tức.",
        "Sửa 'Now.' biểu thị mệnh lệnh khẩn cấp thành 'Ngay lập tức.', loại bỏ từ dịch sai thời thế 'Hiện nay'."
    ),
    179: (
        "Không cần đâu. Món này do đích thân Sparkla làm ra đấy.",
        "Chuốt lại thể bị động 'Điều này được thực hiện bởi Sparkla' thành văn nói tự nhiên."
    ),
    181: (
        "Sparkla! Liệu mà nhìn tình huống đi chứ?! Lúc này mà còn tâm trạng cho việc đó à?!",
        "Sửa thành ngữ 'Read the room' thành 'Liệu mà nhìn tình huống đi chứ?!', loại bỏ dịch thô 'Đã đọc phòng chưa'."
    ),
    184: (
        "Nơi này cũng không khác mấy so với những chỗ chúng ta từng đi qua. Nhưng nếu đem so với Huyễn Cảnh ư? Đúng là một trời một vực.",
        "Sửa thành ngữ 'night and day' thành 'một trời một vực', loại bỏ nghĩa đen 'đó là đêm và ngày'."
    ),
    192: (
        "Chaton, có kế gì không?!==W== Chúng ta ở ngoài này chẳng khác nào bia đỡ đạn cả!",
        "Sửa thành ngữ 'sitting ducks' thành 'chẳng khác nào bia đỡ đạn', khôi phục trọn vẹn ngữ nghĩa hiểm nguy."
    ),
    194: (
        "Tôi đã hỏi những bậc cao niên trong thị trấn rồi. Ai nấy đều bảo chuyện này là hoàn toàn vô vọng.",
        "Sửa thành ngữ 'lost cause' thành 'hoàn toàn vô vọng', loại bỏ calque 'nguyên nhân thất bại'."
    ),
    199: (
        "Tôi sẽ giới thiệu cho cậu hai vị chuyên gia. Nếu cậu muốn ra khơi vượt sóng, họ chính là sự lựa chọn tốt nhất đấy.",
        "Sửa lỗi đảo chiều nghĩa 'get out on the water' thành 'ra khơi vượt sóng', loại bỏ dịch ngược 'ra khỏi nước'."
    ),
    203: (
        "Tôi không thể ôm đồm quá sức mình thêm nữa. Tôi cần giữ đôi chân trên mặt đất và học hỏi xem thế giới Lữ Khách này vận hành ra sao.",
        "Sửa thành ngữ 'bite off more than I can chew' thành 'ôm đồm quá sức mình', loại bỏ nghĩa đen ăn uống."
    ),
    208: (
        "Thế nên Eleanor à, chúng tôi không muốn chỉ đứng đây giương mắt nhìn cậu bước đi một mình nữa. Chúng tôi muốn cùng kề vai sát cánh với cậu trên con đường này.",
        "Chuốt lại câu văn biểu đạt quyết tâm, khắc phục lỗi ngữ pháp cứng nhắc 'chúng tôi đã xong việc chỉ đứng đây'."
    ),
    239: (
        "Năm tới tình hình của chúng ta cũng ảm đạm không kém.==W== Các đối tác lâu năm đều đang lưỡng lự ngóng chờ, chỉ trực xâu xé tàn dư sau sự sụp đổ của Nông Nghiệp Liên Hợp.",
        "Sửa thành ngữ 'sitting on the fence' thành 'lưỡng lự ngóng chờ', loại bỏ nghĩa đen 'ngồi trên hàng rào'."
    ),
    246: (
        "Họ từng là cận vệ thân tín của Tiên Nữ Hoàng Nova. Hơn mười năm trước, họ đã phản bội và sát hại Nữ Hoàng. Đúng là một lũ đại ác nhân.",
        "Phục hồi lore gốc STm08_11: cận vệ thân tín phản bội và sát hại Tiên Nữ Hoàng, loại bỏ hoàn toàn nội dung chế về biểu diễn hoàng gia."
    ),
    247: (
        "Đế Quốc Grace đã thuê Cận Vệ Hoàng Gia truy lùng ráo riết. Đoàn Bạch Miêu vừa đánh vừa tháo chạy suốt chặng đường tới tận nơi này. Huyễn Cảnh chính là cứ điểm kháng cự cuối cùng của họ.",
        "Phục hồi lore gốc STm08_11: Cận Vệ Hoàng Gia truy lùng Đoàn Bạch Miêu và Huyễn Cảnh là nơi cố thủ cuối cùng, loại bỏ tình tiết tiền thưởng."
    ),
    248: (
        "Nghe đâu hồi đó Huyễn Cảnh giàu có, phồn hoa lắm. Nhưng những năm tháng chiến loạn liên miên đã biến nơi đây thành thế này. Giờ thì phần lớn thành phố chỉ còn là đống tàn tích hoang tàn.",
        "Phục hồi lore gốc STm08_11: Huyễn Cảnh từng phồn hoa tráng lệ trước khi bị chiến loạn tàn phá thành phế tích hoang tàn."
    ),
    302: (
        "Cứ tự nhiên đi. Nhưng chỉ phí công vô ích thôi, chúng tôi đã nhìn chằm chằm vào nó cả trăm lần rồi.",
        "Sửa thành ngữ 'Knock yourself out' thành 'Cứ tự nhiên đi', loại bỏ dịch máy nguy hại 'Hãy tự đánh gục mình'."
    ),
    303: (
        "Đã đến tận vạch đích rồi mà cậu lại chùn bước hả?! Thôi kệ, dẹp sang một bên để sếp cậu ra tay xử lý!",
        "Sửa thành ngữ 'getting cold feet' thành 'lại chùn bước', loại bỏ dịch nghĩa đen 'lạnh chân'."
    ),
    304: (
        "Tại sao chúng ta lại trở về vạch xuất phát thế này!!!?",
        "Sửa thành ngữ 'back to square one' thành 'trở về vạch xuất phát', loại bỏ dịch máy vô nghĩa 'quay lại hình vuông'."
    )
}

# Define G2: That's why calque fixes (58 items)
G2_FIXES = {
    30: (
        "Tôi thực sự rất ghét cảm giác bất lực này! Chính vì thế tôi mới muốn giao cho người một ủy thác đặc biệt, ==PLAYER_NAME==!",
        "Khắc phục calque 'That's why' thành 'Chính vì thế', văn phong tự nhiên."
    ),
    54: (
        "Bởi vậy tôi mới giấu kín sự tồn tại của cậu trước Phán Quan Hoàng Hôn.",
        "Thay thế calque 'Đó là lý do tại sao' bằng 'Bởi vậy'."
    ),
    56: (
        "Màn đêm che giấu mọi hiểm họa của biển cả—không như ban ngày, ban đêm người ta chẳng thể nhìn thấy các dòng hải lưu.==W== Chính vì thế mà cả du khách lẫn dân bản địa đều tránh xa bãi biển khi trời tối.",
        "Thay thế calque 'Đó là lý do tại sao' bằng 'Chính vì thế mà'."
    ),
    59: (
        "Tôi chỉ muốn tạo cho mình một kỷ niệm thật đẹp thôi. Thế nên tôi mới kéo cậu đi lướt sóng cùng... Chỉ có vậy thôi.",
        "Khắc phục calque, dùng 'Thế nên' tạo nhịp điệu lời thoại tự nhiên nhẹ nhàng."
    ),
    61: (
        "Tuyệt quá! Thế nên cậu mới là người tớ yêu quý nhất đấy, ==PLAYER_NAME==!",
        "Chuyển ngữ hào hứng tự nhiên, dùng 'Thế nên'."
    ),
    63: (
        "Bởi vậy chúng tôi mới tới đây để thu thập thêm chút thông tin từ các Lữ Khách khác.",
        "Thay thế calque bằng 'Bởi vậy'."
    ),
    67: (
        "Ồ, là tin nhắn từ Albedo.==W== Chắc Bastelina đang bận rộn với quả cây đại thụ rồi. Thế nên cô ấy mới nhờ Albedo liên lạc với tôi.",
        "Thay thế calque 'Đó là lý do tại sao' bằng 'Thế nên'."
    ),
    79: (
        "Chính vì thế tôi mới trở thành một người giao liên. Tôi muốn chuyển phát những bức thư giống như họ đã từng làm. Nghĩ bụng biết đâu trên hành trình đó, tôi lại có thể cứu vớt được ai khác.",
        "Khắc phục calque, dùng 'Chính vì thế' mang giọng văn tâm sự sâu lắng."
    ),
    80: (
        "Tôi biết mà. Thế nên tôi mới đến trước một bước để giúp các bạn một tay đây.",
        "Thay thế calque bằng 'Thế nên'."
    ),
    83: (
        "Tôi không có…==W== Tôi chỉ không muốn uổng phí nó thôi. Bởi vậy tôi mới muốn kiểm tra thử, được chứ?",
        "Thay thế calque bằng 'Bởi vậy'."
    ),
    86: (
        "Thế nên tôi mới luôn thấp thỏm không yên đấy chứ!==W====RT==Mà này, sao anh lại dẫn tôi đến tận đây vậy?",
        "Thay thế calque bằng 'Thế nên' và chuốt ngữ điệu đối thoại tự nhiên."
    ),
    87: (
        "Đó đều là những ký ức vô giá giữa chúng ta. Chính vì thế tôi mới cố hết sức tìm kiếm nó...",
        "Thay thế calque bằng 'Chính vì thế'."
    ),
    89: (
        "Tìm thấy rồi!==W== Một mình tôi không bê nổi nó. Bởi vậy tôi mới phải nhờ cậu giúp một tay.",
        "Thay thế calque bằng 'Bởi vậy'."
    ),
    92: (
        "Tất nhiên là tôi nhớ chứ. Chính vì vậy mà ngày hôm đó mới có ý nghĩa thiêng liêng nhất đối với tôi.",
        "Thay thế calque bằng 'Chính vì vậy mà'."
    ),
    99: (
        "Đây là câu chuyện của riêng cậu, cậu có thể lấp đầy nó bằng những giấc mơ của mình.==W== Thế nên nó mới được gọi là Sách Khởi Đầu Mới.",
        "Thay thế calque bằng 'Thế nên'."
    ),
    125: (
        "Iris bảo rằng điều kiện nơi này cực kỳ lý tưởng để dong buồm ra khơi. Chính vì thế mới có nhiều Lữ Khách đi biển chọn nơi đây làm căn cứ hoạt động.",
        "Thay thế calque bằng 'Chính vì thế mới'."
    ),
    129: (
        "Bởi vậy trong chuyến hải trình này, chúng ta phải liên tục xác định phương hướng, dõi theo hướng gió và sẵn sàng ứng phó với bất kỳ biến động bất ngờ nào.",
        "Thay thế calque bằng 'Bởi vậy'."
    ),
    131: (
        "Thế nên tôi mới cần phải đi do thám trước, nắm rõ địa hình để còn chuẩn bị cho những bước tiếp theo.==W== Sếp có thể giúp tôi tạm thời giấu kín chuyện này với Karin được không?",
        "Thay thế calque bằng 'Thế nên tôi mới cần', bảo toàn token ==W==."
    ),
    132: (
        "Có khi nào bà nghĩ họ là ma không nhỉ? C-Cũng giống như con lúc đầu vậy... Bởi thế bà mới làm ra con búp bê này để bảo vệ bản thân.",
        "Thay thế calque bằng 'Bởi thế'."
    ),
    134: (
        "Chính vì thế mà suốt mấy năm qua chẳng ai còn nhìn thấy ánh sáng ấy nữa.",
        "Thay thế calque bằng 'Chính vì thế mà'."
    ),
    135: (
        "Thảo nào hôm qua lúc quay về mặt cô ấy lại đỏ bừng như gấc thế kia.",
        "Khắc phục calque 'So that's why' thành 'Thảo nào'."
    ),
    136: (
        "Ra là vậy. Thảo nào đến cả đệ nhất lười biếng như cô cũng bị bắt phải đích thân nhúng tay vào làm việc.",
        "Khắc phục calque thành ngữ điệu trêu đùa tự nhiên 'Thảo nào'."
    ),
    138: (
        "Chính vì thế tụi em mới không hé răng với ai.==W== Nếu sau này, anh có thể ghé qua thăm và mang theo một tách trà ngon...",
        "Thay thế calque bằng 'Chính vì thế'."
    ),
    139: (
        "Nhưng quý cô Tinh Linh trông có vẻ cô đơn quá. Bởi vậy tụi em mới muốn giúp cô ấy tìm lại những người bạn của mình.",
        "Thay thế calque bằng 'Bởi vậy'."
    ),
    144: (
        "Thế nên ngươi mới đinh ninh rằng có thể dễ dàng bắt cóc được ta chứ gì!",
        "Thay thế calque bằng 'Thế nên', giọng điệu đối thoại tự nhiên."
    ),
    148: (
        "Chính vì thế, cứ mỗi dịp Lễ Tầm Xuân, chúng tôi lại mang theo chiếc chuông quay trở về Thạch Cột.",
        "Thay thế calque bằng 'Chính vì thế'."
    ),
    149: (
        "Bởi vậy trong dịp lễ hội, chúng ta mới phải đốt pháo nổ vang trời dậy đất đấy chứ.",
        "Thay thế calque bằng 'Bởi vậy'."
    ),
    152: (
        "Hóa ra là vì thế nên anh mới ở đây. Nhưng Norstheim cách nơi này cả một quãng đường xa vạn dặm cơ mà? Sao anh lại cất công lặn lội tới tận đây?",
        "Thay thế calque bằng 'Hóa ra là vì thế nên'."
    ),
    153: (
        "Nocturn Eterna đã tàn phá thành phố này tan hoang từ nhiều năm trước, nhưng những dị thường gần đây của Thạch Cột cho thấy chúng có thể vẫn đang lẩn khuất quanh đây.==W== Chính vì thế chúng ta mới phải đi đôi với nhau—hãy thật cảnh giác khi đi tuần tra khắp thành phố để tìm kiếm bất kỳ dấu vết quay trở lại nào của chúng.",
        "Thay thế calque bằng 'Chính vì thế', bảo toàn token ==W==."
    ),
    158: (
        "Bởi vậy cậu mới dồn ép bản thân tới bước đường cùng. Làm bất cứ điều gì chỉ để xoa dịu đi nỗi đau ấy.",
        "Thay thế calque bằng 'Bởi vậy'."
    ),
    159: (
        "Nhưng nghiêm túc mà nói, mọi người tin tưởng cậu đến vậy cơ mà. Thế nên tôi mới muốn lắng nghe xem cậu nghĩ sao.",
        "Thay thế calque bằng 'Thế nên'."
    ),
    161: (
        "Chính vì thế... tôi mới quyết định trở thành một người giao liên.",
        "Thay thế calque bằng 'Chính vì thế... tôi mới'."
    ),
    164: (
        "Cú Cuồng Phong bay quá nhanh. Một khi nó chộp lấy mồi, chúng ta sẽ mất dấu trước khi kịp lần theo nó về tổ.==B====W== Bởi vậy tôi mới đề xuất dùng tiếng kêu giả, hy vọng có thể khiến nó lơ là mất cảnh giác.",
        "Thay thế calque bằng 'Bởi vậy tôi mới đề xuất', bảo toàn token ==B====W==."
    ),
    165: (
        "Bởi vì họ đặt trọn niềm tin vào Cấp Tốc Bưu Cục. Họ tin rằng chúng tôi sẽ trao tận tay từng bức thư đến đúng người nhận!==B====W== Không một phong thư nào bị bỏ lại, không một nỗi niềm nào bị chôn giấu...==W== Chính vì thế mà họ mới gửi gắm những cánh thư của mình cho chúng tôi.",
        "Thay thế calque bằng 'Chính vì thế mà họ mới', bảo toàn token ==B====W== và ==W==."
    ),
    167: (
        "Bố ra đi... là vì gia đình sao? Là vì con ư? Hóa ra đó là lý do bố trở thành một Lữ Khách...",
        "Thay thế calque bằng câu văn thổ lộ cảm xúc tự nhiên."
    ),
    168: (
        "Chính vì thế...==W== tôi mới sợ rằng Cấp Tốc Bưu Cục rồi cũng sẽ rơi vào kết cục thảm thương như vậy.",
        "Thay thế calque bằng 'Chính vì thế...==W== tôi mới sợ'."
    ),
    171: (
        "Bởi vậy tôi mới muốn nhờ cậu giúp một việc, ==PLAYER_NAME==. Cậu có thể làm bạn với Firefly được không?",
        "Thay thế calque bằng 'Bởi vậy'."
    ),
    174: (
        "Thế nên tôi mới cần những người ngoài cuộc như cậu và tên Bạo Quân kia ra tay can thiệp.",
        "Thay thế calque bằng 'Thế nên'."
    ),
    178: (
        "Nghe nói mục tiêu của nhà đầu tư là chế tạo ra một cỗ máy tự động có đủ sức mạnh để trấn áp những sinh vật hung hãn. Chính vì thế dự án này mới được rót một nguồn kinh phí khổng lồ đến vậy.",
        "Thay thế calque bằng 'Chính vì thế'."
    ),
    180: (
        "Tất nhiên, việc tháo dỡ Cổ Vật vốn bị coi là đại cấm kỵ và Đế Quốc Grace tuyệt đối nghiêm cấm điều đó. Bởi vậy bọn chúng mới phải dùng đến những thủ đoạn mờ ám nơi chợ đen như thế này.",
        "Thay thế calque bằng 'Bởi vậy'."
    ),
    191: (
        "Hóa ra ả ta giao cho ta công việc thợ mỏ giả mạo này... là để dụ các ngươi xuống đây thanh trừng ta!",
        "Chuyển ngữ thấu hiểu âm mưu thành 'Hóa ra... là để'."
    ),
    196: (
        "Chuẩn luôn~ Thế nên tôi tuyệt đối sẽ không để bất cứ thứ gì phá hỏng chuyến đi của chúng ta đâu.",
        "Thay thế calque bằng 'Thế nên tôi tuyệt đối'."
    ),
    197: (
        "Chính vì thế tôi đã quyết định thức trắng vài ngày liền. Thể nào tôi cũng sẽ tóm sống được kẻ đang tung tin đồn ma quái này.",
        "Thay thế calque bằng 'Chính vì thế'."
    ),
    198: (
        "Ngoại trừ mấy kẻ hiếu kỳ thích cảm giác mạnh tìm đến vì những câu chuyện rùng rợn, khách trọ bình thường đều đã sợ mất mật rồi. Bởi vậy đơn đặt phòng mới liên tục bị hủy như thế đấy.",
        "Thay thế calque bằng 'Bởi vậy'."
    ),
    200: (
        "Tôi đời nào làm thế. Chính vì vậy tôi mới tìm đến nhờ cậu đây.",
        "Thay thế calque bằng 'Chính vì vậy'."
    ),
    201: (
        "Thế nên tôi mới cần đích thân đi khảo sát từng tấc đất của Nova. Tôi muốn có được dữ liệu chuẩn xác nhất để vẽ nên những tấm bản đồ hoàn hảo.",
        "Thay thế calque bằng 'Thế nên'."
    ),
    209: (
        "Chính vì thế em mới muốn giúp đỡ họ...==W== Dẫu biết điều này nghe có vẻ táo bạo, nhưng em muốn noi theo tấm gương của Người Hướng Dẫn. Cho dù chỉ có thể giúp được một chút, em cũng muốn dốc hết sức mình vì họ.",
        "Thay thế calque bằng 'Chính vì thế em mới muốn'."
    ),
    241: (
        "Chuẩn xác là như vậy. Thế nên khoản vay này mới không đứng tên Nông Nghiệp Liên Hợp Philae, mà sẽ thuộc về Hiệp Ước Của Sếp.",
        "Thay thế calque bằng 'Thế nên khoản vay này mới'."
    ),
    274: (
        "D-Dạ em hiểu rồi. Quả không hổ danh là Sư Phụ! Em lại được học thêm một bài học quý giá nữa rồi!",
        "Chuyển ngữ cảm thán sùng kính 'Quả không hổ danh là Sư Phụ!' thay vì dịch máy 'Đó là lý do tại sao bạn là Master'."
    ),
    276: (
        "A, tôi hiểu rồi! Thảo nào chúng ta lại nhờ Hiệp Hội Lữ Khách xử lý toàn bộ các ủy thác Cổ Vật cùng một lúc. Tự mình chạy đến từng Nhà Lữ Khách một thì đúng là phí thời gian kinh khủng!",
        "Chuyển ngữ vỡ lẽ 'Thảo nào chúng ta lại'."
    ),
    280: (
        "So với việc phải chi cả một gia tài để thuê Lữ Khách cầu nguyện ở Cự Tháp, đồ phục chế của chúng ta rẻ hơn biết bao nhiêu! Quả đúng là Sếp có khác! Đầu óc kinh doanh của Sếp đỉnh thật đấy!",
        "Chuyển ngữ nịnh sếp tự nhiên 'Quả đúng là Sếp có khác!' thay vì dịch máy."
    ),
    281: (
        "Nếu chuyện này cứ kéo dài, gia đình có thể sẽ tìm ra tôi. Tôi muốn cùng ==SEX4== cao chạy xa bay càng sớm càng tốt, mà muốn thế thì cần rất nhiều tiền. Chính vì vậy tôi mới đưa ==SEX4== đến đây làm việc cùng.",
        "Thay thế calque bằng 'Chính vì vậy', bảo toàn token ==SEX4==."
    ),
    282: (
        "Và rồi kiểu gì cũng có kẻ cắn câu. Bởi vậy nên mấy phường lừa đảo mới chẳng bao giờ tuyệt tích được.",
        "Thay thế calque bằng 'Bởi vậy nên'."
    ),
    285: (
        "Yên tâm đi, cậu không chịu thiệt đâu. Thế nên tôi mới chỉ cung cấp tin tức cho riêng Đế Quốc Grace thôi đấy!",
        "Thay thế calque bằng 'Thế nên tôi mới'."
    ),
    287: (
        "Bởi vậy em mới chọn bộ đồ này đấy... Trông dễ thương đúng không nào?! Tăng thêm độ đáng yêu trước mặt người ấy là chuyện hết sức tự nhiên mà, phải không?!",
        "Thay thế calque bằng 'Bởi vậy em mới chọn'."
    ),
    293: (
        "Chính vì thế mà các Thẩm Phán chúng ta, những người nắm giữ thánh di vật, mới có thể một lần nữa tự do sải bước trên mặt đất.",
        "Thay thế calque bằng 'Chính vì thế mà'."
    ),
    295: (
        "Cậu sở hữu năng lực lãnh đạo và sự quyết đoán mà tôi đang tìm kiếm. Chính vì thế, tôi muốn cậu dẫn dắt những bước đi đầu tiên của tôi trên con đường làm Lữ Khách!",
        "Thay thế calque bằng 'Chính vì thế'."
    ),
    299: (
        "Hóa ra đó là lý do cậu cố hết sức giấu giếm ư.==W== Đừng lo, tôi xin thề trước Thần Ân Điển, tôi tuyệt đối sẽ không hé răng với bất kỳ ai đâu.",
        "Chuyển ngữ 'So that's why' thành 'Hóa ra đó là lý do... ư'."
    )
}

# Define G4: Untranslated short lines & missed lines (193 items)
G4_MAPPINGS = {
    # Item 0
    0: ("Cái gì cơ?!", "Dịch câu thoại cảm thán bất ngờ của tên côn đồ trong trận hỗn chiến."),
    # Item 1
    1: ("T-Thật sao?", "Dịch câu hỏi lắp bắp ngạc nhiên."),
    # Item 2
    2: ("Cái gì cơ?!", "Dịch câu cảm thán ngạc nhiên."),
    # Item 3
    3: ("KHÔNG ĐỜI NÀO!", "Dịch câu dứt khoát từ chối bán giày."),
    # Item 4
    4: ("Xin lỗi nha!", "Dịch câu xin lỗi tự nhiên."),
    # Item 5
    5: ("X-Xin chào!", "Dịch lời chào rụt rè của nữ sinh e thẹn."),
    # Item 6
    6: ("Vâng?", "Dịch lời đáp nhẹ nhàng."),
    # Item 7
    7: ("C-Cái gì cơ?", "Dịch phản ứng lắp bắp ngạc nhiên."),
    # Item 8
    8: ("Thật đấy à?", "Dịch câu hỏi nghi hoặc."),
    # Item 9
    9: ("KHÔNG ĐÂU!", "Dịch câu dứt khoát từ chối đi xe."),
    # Item 10
    10: ("C-Cái gì cơ?", "Dịch phản ứng lắp bắp ngạc nhiên."),
    # Item 11
    11: ("Ý em là...?", "Dịch câu hỏi gặng ý tứ của Chaton."),
    # Item 12
    12: ("Dạ?", "Dịch lời đáp của nhân vật."),
    # Item 13
    13: ("Hửm?", "Dịch phản ứng ngạc nhiên nhẹ."),
    # Item 14
    14: ("Cái gì cơ?!", "Dịch phản ứng hoảng hốt."),
    # Item 15
    15: ("T-Thật sao?", "Dịch câu hỏi lắp bắp ngạc nhiên."),
    # Item 17
    17: ("Cái gì cơ?!", "Dịch câu cảm thán giật mình."),
    # Item 33
    33: ("Tại sao cơ?", "Dịch câu hỏi thắc mắc."),
    # Item 34
    34: ("Sao thế anh?", "Dịch câu hỏi quan tâm tự nhiên."),
    # Item 35
    35: ("Thật sao...?", "Dịch câu hỏi nghi vấn lắng đọng."),
    # Item 36
    36: ("Ở đây ư?", "Dịch câu hỏi địa điểm."),
    # Item 37
    37: ("Tại sao cơ?!", "Dịch câu hỏi bất ngờ gay gắt."),
    # Item 38
    38: ("Gì cơ?", "Dịch câu hỏi ngơ ngác."),
    # Item 39
    39: ("Thật sao?!", "Dịch lời cảm thán vui mừng ngạc nhiên."),
    # Item 40
    40: (
        "Hát ru cho tôi nghe ư?==W== Hmmm...==W== Ừm.==W== Có tiếng đàn của Bánh Pie Bạo Quân,==W== chắc chắn đêm nào tôi cũng sẽ có những giấc mơ thật ngọt ngào...",
        "Dịch câu thoại dài bị bỏ sót do bắt đầu bằng 'Play'."
    ),
    # Item 41
    41: (
        "Hát ru cho tôi nghe ư?==W== Có tiếng đàn của Bánh Pie Bạo Quân,==W== chắc chắn đêm nào tôi cũng sẽ có những giấc mơ thật ngọt ngào...",
        "Dịch câu thoại dài bị bỏ sót do bắt đầu bằng 'Play'."
    ),
    # Item 42
    42: ("Sẵn sàng chưa?", "Dịch câu hỏi chuẩn bị."),
    # Item 43
    43: ("Sẵn sàng rồi!", "Dịch câu xác nhận sẵn sàng."),
    # Item 44
    44: ("K-Không có gì đâu!", "Dịch câu chối khéo ngượng ngùng."),
    # Item 45
    45: ("Thật sao?!", "Dịch câu ngạc nhiên vui sướng."),
    # Item 46
    46: ("K-Không có gì đâu!", "Dịch phản ứng chối khéo."),
    # Item 47
    47: ("Tại sao chứ?", "Dịch câu hỏi thắc mắc."),
    # Item 48
    48: ("Thật sao...?", "Dịch lời băn khoăn trăn trở."),
    # Item 49
    49: ("Gì cơ?", "Dịch phản ứng ngạc nhiên."),
    # Item 50
    50: (
        "Tạm gác chuyện đó lại đã,==W== chẳng lẽ cậu không tò mò==W== xem tôi đang có thứ gì sao?",
        "Dịch câu thoại bị bỏ sót do bắt đầu bằng 'Set'."
    ),
    # Item 51
    51: (
        "Tấu nhạc cho biển cả hay những vì sao—thật đẹp đẽ biết bao, và điều đó thực sự rất giống với con người cậu.",
        "Dịch câu thoại bị bỏ sót do bắt đầu bằng 'Playing'."
    ),
    # Item 52
    52: (
        "Trật tự nào, mau xếp hàng vào đi chứ~",
        "Dịch câu nhắc nhở trật tự xếp hàng."
    ),
    # Item 57
    57: (
        "Tạm không bàn tới chuyện \"ôm thật chặt\" nhé... Tôi sẽ cố gắng hết sức để ở bên cạnh cậu.",
        "Dịch câu thoại bị bỏ sót do bắt đầu bằng 'Setting aside'."
    ),
    # Item 58
    58: ("Tại sao vậy?", "Dịch câu hỏi nhẹ nhàng."),
    # Item 60
    60: ("Được không mà...?", "Dịch câu nài nỉ dễ thương."),
    # Item 62
    62: (
        "Chơi gắp thú thì không sao,==W== nhưng đến lúc dọn dẹp phòng,==W== chẳng phải Nazuna nên tự mình làm lấy ư?==W== Chúng ta đã thống nhất điều đó ngay từ đầu rồi cơ mà?",
        "Dịch câu thoại bị bỏ sót do bắt đầu bằng 'Playing'."
    ),
    # Item 64
    64: ("Tại sao chứ?", "Dịch câu thắc mắc."),
    # Item 66
    66: ("C-Cứu với!", "Dịch tiếng kêu cứu lắp bắp hoảng hốt."),
    # Item 69
    69: ("Cái gì cơ?!", "Dịch câu cảm thán giật mình."),
    # Item 71
    71: ("Người Nghe Tinh Nghịch", "Dịch nhãn danh xưng nhân vật."),
    # Item 72
    72: ("Thật sao?!", "Dịch câu hỏi ngạc nhiên phấn khởi."),
    # Item 73
    73: ("Cái gì cơ?!", "Dịch câu cảm thán giật mình."),
    # Item 74
    74: ("K-Kẻ dối trá sao?", "Dịch câu lắp bắp hoài nghi."),
    # Item 75
    75: (
        "Đóng giả làm thổ phỉ... Thật là một thủ đoạn đê hèn. Làm sao các người có thể quyết định dứt khoát như vậy? Sao không hề có chút do dự nào thế hả?",
        "Dịch câu thoại chất vấn gay gắt bị bỏ sót do bắt đầu bằng 'Playing'."
    ),
    # Item 77
    77: ("Cái gì cơ???", "Dịch câu cảm thán ngạc nhiên tột cùng."),
    # Item 81
    81: ("KHÔNG ĐƯỢC!", "Dịch tiếng kêu ngăn cản khi đang thay đồ."),
    # Item 82
    82: ("Đúng vậy!", "Dịch câu khẳng định."),
    # Item 84
    84: ("Đằng kia kìa!", "Dịch tiếng chỉ điểm 'There!'."),
    # Item 88
    88: ("Chuẩn luôn!", "Dịch lời tán thành 'Yes!'."),
    # Item 91
    91: ("T-Thật sao?!", "Dịch câu hỏi lắp bắp ngạc nhiên."),
    # Item 93
    93: ("Cái gì cơ?!", "Dịch câu cảm thán ngạc nhiên."),
    # Item 94
    94: ("Tại sao cơ?!", "Dịch câu hỏi bất ngờ gay gắt."),
    # Item 96
    96: ("Thật sao?!", "Dịch lời ngạc nhiên."),
    # Item 97
    97: ("Đ-Đứng im!", "Dịch tiếng hô đứng lại giật thót."),
    # Item 98
    98: ("T-Thật sao...?", "Dịch câu hỏi rụt rè."),
    # Item 101
    101: ("Ở đâu cơ?", "Dịch câu hỏi nơi chốn."),
    # Item 102
    102: ("Chơi với tôi một trò chơi nhỏ nhé~", "Dịch lời rủ rê dễ thương."),
    # Item 103 (PM)
    103: ("Thật không đấy?", "Dịch tin nhắn hỏi lại bán tín bán nghi."),
    # Item 104 (PM)
    104: ("Đi mà~", "Dịch tin nhắn nài nỉ dễ thương."),
    # Item 105 (PM)
    105: ("Sao thế?", "Dịch tin nhắn hỏi thăm ngắn gọn."),
    # Item 106 (PM)
    106: ("Vâng?", "Dịch tin nhắn đáp lời."),
    # Item 107 (PM)
    107: ("T-Thật không đấy?", "Dịch tin nhắn ngạc nhiên khi trúng thưởng."),
    # Item 108 (PM)
    108: ("Chuẩn luôn!", "Dịch tin nhắn tán thưởng."),
    # Item 109 (PM)
    109: ("Giúp tớ với nha?", "Dịch tin nhắn nhờ vả dễ thương."),
    # Item 110 (PM)
    110: ("Vâng!", "Dịch tin nhắn xác nhận."),
    # Item 111 (PM)
    111: ("Thật vậy ư...?", "Dịch tin nhắn băn khoăn."),
    # Item 112 (PM)
    112: ("Không phải sao...?", "Dịch tin nhắn hỏi dò."),
    # Item 113 (PM)
    113: ("Thật mà!", "Dịch tin nhắn khẳng định chắc nịch."),
    # Item 114 (PM)
    114: ("Cảm ơn cậu nhiều nha!", "Dịch tin nhắn cảm ơn thân mật."),
    # Item 115 (PM)
    115: ("thật đấy!", "Dịch tin nhắn chữ thường tự nhiên."),
    # Item 116 (PM)
    116: ("thật á!?", "Dịch tin nhắn ngạc nhiên."),
    # Item 117 (PM)
    117: ("thật á?", "Dịch tin nhắn hỏi lại."),
    # Item 118 (PM)
    118: ("S-sao cơ!?", "Dịch tin nhắn hốt hoảng."),
    # Item 119 (PM)
    119: ("Dạ?", "Dịch tin nhắn đáp lễ phép."),
    # Item 120 (PM)
    120: ("Có... có lẽ thế?", "Dịch tin nhắn ngập ngừng."),
    # Item 121 (PM)
    121: ("Tại sao cơ?", "Dịch tin nhắn hỏi lý do."),
    # Item 122 (PM)
    122: ("Không không không!", "Dịch tin nhắn xua tay lia lịa."),
    # Item 123 (PM)
    123: ("Sao thế ạ?", "Dịch tin nhắn hỏi khách sáo."),
    # Item 124 (PM)
    124: ("Sao thế?", "Dịch tin nhắn hỏi chuyện."),
    # Item 126
    126: ("Cái gì cơ?!", "Dịch phản ứng giật mình."),
    # Item 128
    128: ("Cái gì cơ?!", "Dịch câu cảm thán ngạc nhiên."),
    # Item 130
    130: ("Ý... ý là sao...?", "Dịch câu hỏi lắp bắp ngơ ngác."),
    # Item 133
    133: ("Cái gì cơ?!", "Dịch câu cảm thán giật mình."),
    # Item 137
    137: ("Cảm ơn nhé!", "Dịch lời cảm ơn."),
    # Item 140
    140: ("K-Khoan đã!", "Dịch tiếng gọi giật lại lắp bắp."),
    # Item 141
    141: ("Cái gì cơ?!", "Dịch phản ứng bất ngờ."),
    # Item 142
    142: ("Cái gì cơ...?", "Dịch câu hỏi ngỡ ngàng."),
    # Item 143
    143: ("T-Thật sao?!", "Dịch phản ứng lắp bắp sửng sốt."),
    # Item 146
    146: ("Gì cơ?", "Dịch câu hỏi thắc mắc."),
    # Item 150
    150: ("Cái gì cơ?!", "Dịch phản ứng ngạc nhiên."),
    # Item 151
    151: ("Đang chơi Mạt Chược.", "Dịch lời đáp ngắn gọn."),
    # Item 154
    154: ("Sao cơ?", "Dịch câu hỏi bất ngờ."),
    # Item 160
    160: ("Gì cơ?", "Dịch câu hỏi ngắn."),
    # Item 166
    166: ("T-Thật sao?!", "Dịch câu hỏi ngạc nhiên xúc động."),
    # Item 169
    169: (
        "Chơi cùng Bạo Quân vui lắm.==W== Điều đó chứng tỏ Bạo Quân là người tốt.",
        "Dịch câu thoại trẻ thơ bị bỏ sót do bắt đầu bằng 'Playing'."
    ),
    # Item 172
    172: ("Alo?", "Dịch tiếng gọi kiểm tra liên lạc."),
    # Item 173
    173: ("Đúng vậy!", "Dịch câu khẳng định dõng dạc."),
    # Item 176
    176: ("Sao cơ...?", "Dịch câu hỏi ngỡ ngàng."),
    # Item 177
    177: ("Tuyệt quá!!", "Dịch tiếng reo vui sướng."),
    # Item 182
    182: (
        "Ngươi muốn định giá thế nào tùy ý, Bloc. Nhưng trong ba tháng tới ta sẽ tập trung hoàn toàn vào các phát minh mới, thế nên đừng có đùn đẩy đơn hàng mới cho ta nữa đấy.",
        "Dịch câu thoại đàm phán dứt khoát bị bỏ sót do bắt đầu bằng 'Set'."
    ),
    # Item 183
    183: ("KHÔNGGGGG!!!!", "Dịch tiếng thét hoảng hốt tột cùng."),
    # Item 185
    185: ("Cái gì cơ?!", "Dịch câu cảm thán ngạc nhiên."),
    # Item 186
    186: ("Thật không đấy?", "Dịch câu hỏi nghi hoặc."),
    # Item 187
    187: ("Sao cơ?", "Dịch câu hỏi ngơ ngác."),
    # Item 188
    188: ("Nghiêm túc đấy à?", "Dịch câu hỏi chất vấn."),
    # Item 189
    189: ("Tuyệt cú mèooo!", "Dịch tiếng reo mừng 'Yesss!'."),
    # Item 190
    190: ("Thật đấy à?", "Dịch câu hỏi bán tín bán nghi."),
    # Item 193
    193: ("Sẵn sàng chưa...?", "Dịch câu hỏi chuẩn bị nhẹ nhàng."),
    # Item 195
    195: ("Ý cậu là...?", "Dịch câu hỏi làm rõ ý tứ."),
    # Item 202
    202: ("Cái gì cơ?!", "Dịch câu cảm thán giật mình."),
    # Item 204
    204: ("Vâng!", "Dịch lời đáp."),
    # Item 205
    205: ("Cái gì cơ?!", "Dịch phản ứng hoảng hốt."),
    # Item 206
    206: ("Thật sao?!", "Dịch lời ngạc nhiên."),
    # Item 207
    207: ("Vâng!", "Dịch lời đáp quả quyết."),
    # Item 210
    210: ("Cái gì cơ?!", "Dịch tiếng kêu bất ngờ."),
    # Item 212
    212: ("KHÔNG ĐƯỢC!", "Dịch tiếng từ chối quyết liệt."),
    # Item 213
    213: ("Cảm ơn nhiều nha!", "Dịch lời cảm ơn."),
    # Item 214
    214: ("Cái gì cơ?!", "Dịch tiếng kêu bất ngờ."),
    # Item 215
    215: ("Đằng kia kìa!", "Dịch tiếng phát hiện mục tiêu."),
    # Item 216
    216: ("C-Cái gì cơ?", "Dịch tiếng lắp bắp hoang mang."),
    # Item 217
    217: ("B-Bị sa thải sao...?", "Dịch tiếng run rẩy khi nghe tin bị đuổi việc."),
    # Item 218
    218: ("M-Mẹo sao?", "Dịch tiếng thắc mắc ngập ngừng."),
    # Item 219
    219: ("Cái gì cơ?!", "Dịch tiếng kêu bất ngờ."),
    # Item 220
    220: (
        "Tạm gác chuyện đó lại đã... Cậu có lợi thế không nhỏ khi đối đầu với Vườn Ký Sinh đấy nhỉ.",
        "Dịch câu thoại bị bỏ sót do bắt đầu bằng 'Setting that aside'."
    ),
    # Item 221
    221: ("Đ-Đúng vậy!", "Dịch lời đáp ngập ngừng."),
    # Item 222
    222: ("T-Tại sao cơ?!", "Dịch câu hỏi lắp bắp ngỡ ngàng."),
    # Item 223
    223: ("Mau giả chết đi!", "Dịch lời giục giã khẩn cấp."),
    # Item 224
    224: ("Xin chào? Có ai ở đây không?", "Dịch tiếng gọi hoang mang của khách hàng."),
    # Item 225
    225: ("Sao cơ?", "Dịch câu hỏi thắc mắc."),
    # Item 226
    226: ("Goo-goo. <r=Here you are.></r>Goo-ga!", "Bảo toàn nguyên vẹn tiếng bập bẹ và token ruby."),
    # Item 227
    227: ("Tại sao chứ?", "Dịch câu hỏi thắc mắc."),
    # Item 228
    228: ("Sao cơ...?", "Dịch câu hỏi ngỡ ngàng."),
    # Item 229
    229: ("Hôm qua ư?", "Dịch câu hỏi xác nhận thời gian."),
    # Item 230
    230: ("Vâng ạ!!", "Dịch tiếng đáp reo vui."),
    # Item 231
    231: ("Hùa theo", "Dịch lựa chọn hành động kịch bản."),
    # Item 232
    232: (
        "Hùa theo thì cũng hấp dẫn đấy, nhưng tôi cần phải dập tắt chuyện này trước khi nó vượt tầm kiểm soát.",
        "Dịch độc thoại nội tâm bị bỏ sót do bắt đầu bằng 'Playing along'."
    ),
    # Item 233
    233: ("R-Rõ rồi ạ!", "Dịch tiếng đáp tuân lệnh dứt khoát."),
    # Item 234
    234: ("Vâng!", "Dịch tiếng đáp quả quyết."),
    # Item 235
    235: ("Sao cơ?", "Dịch câu hỏi thắc mắc."),
    # Item 236
    236: ("C-Cái gì cơ?!", "Dịch phản ứng lắp bắp kinh ngạc."),
    # Item 237
    237: (
        "Tạm thời không bàn chuyện đó, ngay cả khi chúng ta muốn mua lại số cổ phần kia, nguồn vốn vẫn là một rào cản khổng lồ...",
        "Dịch câu thoại phân tích tài chính bị bỏ sót do bắt đầu bằng 'Setting that aside'."
    ),
    # Item 238
    238: (
        "Chưa tính tới nguồn quỹ của Nông Nghiệp Liên Hợp Philae, chỉ riêng việc nghĩ tới phía Hiệp Ước Của Sếp thôi cũng thấy như đang gánh một món nợ cả thế kỷ rồi...",
        "Dịch câu thoại bị bỏ sót do bắt đầu bằng 'Setting United Harvest'."
    ),
    # Item 240
    240: (
        "Nếu cậu cứ dây dưa giấu giếm nó, đến cả tôi cũng chẳng bao che nổi cho cậu đâu.",
        "Dịch câu thoại cảnh báo bị bỏ sót do bắt đầu bằng 'Play keep-away'."
    ),
    # Item 242
    242: ("Cái gì cơ?!", "Dịch phản ứng ngạc nhiên."),
    # Item 243
    243: ("Vâng!", "Dịch lời đáp."),
    # Item 244
    244: ("Sao cơ?", "Dịch câu hỏi ngắn."),
    # Item 245
    245: ("C-Cứng ngắc á?!", "Dịch phản ứng giật mình xấu hổ khi bị chê cứng nhắc."),
    # Item 249
    249: ("M-Mẹ ơi...?", "Dịch tiếng gọi mẹ ngỡ ngàng ngập ngừng."),
    # Item 250
    250: ("Dì ơi!", "Dịch tiếng gọi dì mừng rỡ."),
    # Item 251
    251: ("D-Dì ơi...?", "Dịch tiếng gọi dì nghẹn ngào xúc động."),
    # Item 252
    252: (
        "Cứ thuận nước đẩy thuyền đi. Hãy tỏ ra như cậu muốn cứu rỗi thế giới và tiêu diệt Bạo Quân. Ả ta sẽ vội vã lôi kéo cậu ngay thôi.",
        "Dịch câu thoại mưu kế bị bỏ sót do bắt đầu bằng 'Play along'."
    ),
    # Item 253
    253: ("Mẹ ơi!", "Dịch tiếng gọi mẹ thiết tha."),
    # Item 254
    254: ("Khoan đã!", "Dịch tiếng gọi ngăn cản."),
    # Item 255
    255: (
        "Làm chó săn cho một con rắn độc rồi liếm láp đồ thừa của ả ư?==W== Đừng có mơ.==W== Sếp đã nhìn thấu trò mèo của ả rồi, đúng không?",
        "Dịch câu thoại khinh bỉ đanh thép bị bỏ sót do bắt đầu bằng 'Play lapdog'."
    ),
    # Item 256
    256: ("Mẹ ơi!", "Dịch tiếng gọi mẹ nghẹn ngào."),
    # Item 257
    257: ("Sẵn sàng rồi!", "Dịch lời hô sẵn sàng xung trận."),
    # Item 260
    260: ("Sao cơ?", "Dịch câu hỏi ngắn."),
    # Item 261
    261: ("Sao cơ?", "Dịch câu hỏi ngơ ngác."),
    # Item 262
    262: ("Tại sao chứ?", "Dịch câu hỏi lý do."),
    # Item 263
    263: ("Sao cơ?", "Dịch câu hỏi thắc mắc."),
    # Item 264
    264: ("Sao cơ?", "Dịch câu hỏi ngắn."),
    # Item 265
    265: ("T-Thật sao?", "Dịch câu hỏi lắp bắp ngạc nhiên."),
    # Item 266
    266: ("Sao cơ?", "Dịch câu hỏi ngắn."),
    # Item 267
    267: ("N-Nói dối sao?", "Dịch câu lắp bắp nghi hoặc."),
    # Item 268
    268: ("C-Cái gì cơ?", "Dịch phản ứng lắp bắp kinh ngạc."),
    # Item 269
    269: ("Không—!", "Dịch tiếng kêu ngắt quãng."),
    # Item 270
    270: ("Đã xong rồi sao?", "Dịch câu hỏi ngạc nhiên vì hoàn thành quá nhanh."),
    # Item 271
    271: ("Cái gì cơ?!", "Dịch phản ứng sửng sốt."),
    # Item 272
    272: ("Đi mà~", "Dịch lời nài nỉ ngọt ngào."),
    # Item 273
    273: ("K-Khoan đã!", "Dịch tiếng gọi giữ lại lắp bắp."),
    # Item 275
    275: ("Cái gì cơ?!", "Dịch phản ứng ngạc nhiên."),
    # Item 277
    277: ("C-Cái gì cơ?", "Dịch tiếng lắp bắp ngạc nhiên."),
    # Item 278
    278: ("Vâng?", "Dịch tiếng đáp lời."),
    # Item 279
    279: ("Thật sao?!", "Dịch phản ứng phấn khởi ngạc nhiên."),
    # Item 283
    283: ("Suỵt—im lặng nào!", "Dịch tiếng nhắc giữ im lặng."),
    # Item 284
    284: (
        "Hùa theo là hùa theo thế nào? Ý anh không phải là chúng ta thực sự...",
        "Dịch câu thoại ngại ngùng bị bỏ sót do bắt đầu bằng 'Play along'."
    ),
    # Item 286
    286: ("Cái gì cơ?!", "Dịch phản ứng giật mình."),
    # Item 288
    288: (
        "Giả ngu cũng vô ích thôi!==W== Ngươi đã bị bắt quả tang tay cầm quả cà chua rành rành ra đó rồi!",
        "Dịch câu vạch mặt bị bỏ sót do bắt đầu bằng 'Playing dumb'."
    ),
    # Item 290
    290: ("Đứng im!", "Dịch khẩu lệnh trấn áp dứt khoát."),
    # Item 291
    291: ("Ý ngài là...?", "Dịch câu hỏi gặng ý tứ tôn kính."),
    # Item 292
    292: ("Tại sao chứ?", "Dịch câu hỏi thắc mắc."),
    # Item 294
    294: ("Cái gì—?", "Dịch câu ngắt lời ngạc nhiên."),
    # Item 296
    296: ("K-Khoan đã...!", "Dịch tiếng gọi ngăn cản ngập ngừng."),
    # Item 297
    297: ("R-Rõ rồi!", "Dịch tiếng nhận lệnh quả quyết."),
    # Item 298
    298: ("Cái gì...?!", "Dịch phản ứng sửng sốt bàng hoàng."),
    # Item 300
    300: ("Thật sao...!?", "Dịch câu hỏi kinh ngạc tột độ."),
    # Item 301
    301: (
        "Thống nhất thế nhé. Giờ thì bắt tay vào việc thôi.",
        "Dịch câu kết luận hành động bị bỏ sót do bắt đầu bằng 'Settled'."
    ),
    # Item 305
    305: ("T-Thật sao...?", "Dịch câu hỏi rụt rè hoài nghi.")
}

print(f"Total G1 defined: {len(G1_FIXES)}")
print(f"Total G2 defined: {len(G2_FIXES)}")
print(f"Total G3 defined: {len(G3_FIXES)}")
print(f"Total G4 defined: {len(G4_MAPPINGS)}")

all_keys = set(G1_FIXES.keys()) | set(G2_FIXES.keys()) | set(G3_FIXES.keys()) | set(G4_MAPPINGS.keys())
print(f"Total keys covered: {len(all_keys)}")
assert len(all_keys) == 306, f"Expected 306 unique indices, got {len(all_keys)}"
assert len(G1_FIXES) + len(G2_FIXES) + len(G3_FIXES) + len(G4_MAPPINGS) == 306, "Overlapping keys found!"

entries = []
token_errors = []
nfc_errors = []

for idx, item in enumerate(inputs):
    en_source = item["source_en"]
    if idx in G1_FIXES:
        text_vi, notes = G1_FIXES[idx]
    elif idx in G2_FIXES:
        text_vi, notes = G2_FIXES[idx]
    elif idx in G3_FIXES:
        text_vi, notes = G3_FIXES[idx]
    elif idx in G4_MAPPINGS:
        text_vi, notes = G4_MAPPINGS[idx]
    else:
        raise ValueError(f"Index {idx} not found in any fix dictionary!")
    
    # Normalize NFC
    text_vi_nfc = normalize_nfc(text_vi)
    if text_vi_nfc != text_vi:
        nfc_errors.append(idx)
        text_vi = text_vi_nfc
        
    # Check tokens
    en_tokens = sorted(extract_tokens(en_source))
    vi_tokens = sorted(extract_tokens(text_vi))
    if en_tokens != vi_tokens:
        token_errors.append((idx, item.get("scene_id"), item.get("locator"), en_tokens, vi_tokens))

    entry = {
        "id": item["locator"],
        "scene_id": item.get("scene_id"),
        "entry_hash": item.get("entry_hash"),
        "source_en": en_source,
        "text_vi": text_vi,
        "notes": notes
    }
    entries.append(entry)

proposal = {
    "batch_id": "BATCH_FIX_04_STORY_SHORT_LINES",
    "translator": "TRANSLATOR_VI_STORY",
    "total_items": len(entries),
    "entries": entries
}

# Write output file
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(proposal, f, ensure_ascii=False, indent=2)

print(f"Successfully generated proposal to {OUTPUT_FILE}")
print(f"Total entries: {len(entries)}")
print(f"Token errors count: {len(token_errors)}")
if token_errors:
    for err in token_errors[:5]:
        print("Token error:", err)
print(f"NFC errors fixed: {len(nfc_errors)}")
