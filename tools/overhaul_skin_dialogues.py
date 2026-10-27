#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Overhaul Skin Dialogues & Quotes (Campaign 25)
---------------------------------------------
1. Overhaul all 31 CharacterSkin quotes/lore (.2) in CharacterSkin (00597 & twin 00844)
   - Eliminates ridiculous MT blunders:
     + 'Rau muống ngâm trong nước' -> 'Đóa hoa triêu nhan cắm trong bình nước' (Chitose)
     + 'Lên máy bay / chiếc bơm hơi' -> 'Trèo lên phao bơi hình thú' (Iris)
     + 'Nhiệm vụ ủy thác nở rộ' -> 'Hương thơm đóa tường vi' (Gerie)
     + 'Uống rượu ớt' -> 'Ớt đỏ thành tinh' (Shimiao)
     + 'Phí đau buồn', 'khuyến mãi', 'máy rung', 'bàn chân', v.v.
   - Enforces natural, poetic, emotional Anime RPG personality and proper pronouns.
2. Overhaul all 41 unlockLook voice subtitles in Master Voice Subtitles (00552).
3. Repack dist/data_patched_vi.arcx with XXTEA encryption.
4. Dual-deploy to Yostar and Steam clients.
5. Anti-regression verification via tools/verify_deployed_game_data.py.
"""

from __future__ import annotations
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT))
from tools.arcx_adapter import ArcxArchive, repack_archive

DEC_DIR = ROOT / "work" / "research" / "data_200_decrypted"
ENTRIES_DIR = DEC_DIR / "entries"
OUTPUT_ARCX = ROOT / "dist" / "data_patched_vi.arcx"

LIVE_YOSTAR_DATA = Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx")
LIVE_STEAM_DATA = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Tables\data.arcx")

# -------------------------------------------------------------------------
# 1. POLISHED SKIN QUOTES & DIALOGUES (31 SKINS)
# -------------------------------------------------------------------------
POLISHED_SKIN_QUOTES = {
    # 10303 - Amber (Ngây Thơ Tinh Nghịch / 玩心无邪)
    "CharacterSkin.10303.2": "Gấm hoa dệt nên dòng lửa cuộn, sắc vàng điểm xuyết áng tường vân. Chẳng giận mà uy, ánh mắt ngời sáng rực rỡ.\x0bNgoàm——!",
    # 10304 - Amber (Hè Về An Yên / 邀你静心，悠然一夏)
    "CharacterSkin.10304.2": "Nương theo làn gió biển ấm nồng, chớp lấy một thoáng lặng giữa ngày hội rộn rã, tớ khẽ hướng ánh nhìn bình yên về phía cậu.",

    # 10703 - Tilia (Đây Là Chính Nghĩa Của Ta! / 此即吾之正义！)
    "CharacterSkin.10703.2": "Thắt chặt đai lưng, dứt khoát biến hình, ý chí chiến đấu rực cháy tựa thái dương!\x0bKhoác lên mình chiến y chính nghĩa, lấy tư thế kỵ sĩ mà bảo vệ từng góc phố——\x0bĐây chính là chính nghĩa của tôi!",
    # 10704 - Tilia (Ánh Sáng Rực Rỡ, Ý Chí Sục Sôi / 光彩闪亮，斗志昂扬)
    "CharacterSkin.10704.2": "Cô nàng mang sắc màu thái dương đang chuẩn bị cổ vũ cho cậu đây nè~\x0bHãy nở nụ cười rạng rỡ nhất cùng tinh thần đỉnh cao để đón nhận thử thách tiếp theo nhé!",

    # 11003 - Firenze (Đẹp Như Hoa Độc, Tuyệt Sắc Khuynh Thành / 艳若蛇蝎，绝色倾城)
    "CharacterSkin.11003.2": "Mượn dùng sức mạnh vốn không thuộc về mình ắt phải trả cái giá tương xứng.\nNgài đang run sợ điều gì chứ? Ta đâu phải loài ác quỷ.",

    # 11103 - Iris (Một Phần 365 Của Em / 1/365的你)
    "CharacterSkin.11103.2": "Dưới ánh nắng đông trong lành, hình bóng anh nâng niu ly nước ấm phả ra làn khói trắng; một người luôn tự nhận mình bình phàm giản đơn, nhưng lại chính là toàn bộ ý nghĩa của ngày hôm nay.",
    # 11104 - Iris (Dập Dềnh Làn Sóng Êm / 邀你欢喜，轻波漂游)
    "CharacterSkin.11104.2": "Cái đó... Em sẽ cố hết sức giữ thăng bằng cho chiếc phao bơi này, nhưng khi trèo lên anh nhớ cẩn thận một chút nhé.\x0b——Đ-Đương nhiên rồi, nếu anh lỡ sảy chân rơi xuống nước, em nhất định sẽ kéo anh lại thật chặt!",

    # 11203 - Noya (Dư Vị Nắng Ấm / 日晒的余温)
    "CharacterSkin.11203.2": "Đã ra đến biển, đặt chân lên bãi cát thì đương nhiên phải diện đồ bơi rồi!\x0bÔm trọn ánh thái dương rực rỡ, tận hưởng từng đợt sóng vỗ về êm ái—— Chạm vào mùa hè nồng nhiệt thế này, nhất định phải nhớ bôi kem chống nắng đấy nhé!",
    # 11205 - Noya (Giây Phút Nghỉ Ngơi, Kề Bên Cạnh Bạn / 小憩时光，伴你身旁)
    "CharacterSkin.11205.2": "Ủy thác hôm nay là cùng người ta nghỉ ngơi trọn vẹn cả ngày đó nha~\nNếu không có ý kiến gì thì mau thay đồ ngủ vào đi nào, chỗ trống bên cạnh là em để dành riêng cho anh đấy nhé~",

    # 11303 - Shimiao (Thử Một Chút Cay Nhé! / 辣就试试看吧！)
    "CharacterSkin.11303.2": "Thành Thương Ngô nghiêm cấm ớt đỏ thành tinh đấy nhé!\x0bV-Vì để bảo vệ nền hòa bình của Thương Ngô, t-thiếu nữ ma pháp kiên định với tình yêu và chính nghĩa, Shimiao ra lệnh cho ngươi! Mau biến trở lại hình dạng ban đầu ngay đi!",

    # 11603 - Ridge (Nghỉ Ngơi Nơi Nhà Kính Xanh / 郁蓊恒温室中憩)
    "CharacterSkin.11603.2": "Khoảnh khắc hạnh phúc nhất mà tôi có thể nghĩ tới chính là được chợp mắt giữa hơi ấm dịu dàng của buổi trưa hè. Khi tỉnh giấc, ánh nắng đã rọi qua bậu cửa sổ, còn những đóa hoa rực rỡ vẫn luôn kiên nhẫn đợi chờ cậu.",

    # 11703 - Jinglin (Khúc Hành Quân Vận May Ẩm Thực / 食来运转进行曲)
    "CharacterSkin.11703.2": "Trống nhạc nghênh tân, lộc thực hanh thông!\x0bNhiệt liệt chào đón quý khách hôm nay đã ghé thăm Hoài Cảnh Thực Phủ, chuyến hành trình mỹ vị và vận may xin được chính thức khai màn!",

    # 11903 - Nanoha (Khi Ngọn Gió Phương Xa Nổi Lên / 异国风起时)
    "CharacterSkin.11903.2": "Gió lay bóng mây chuyển, nắng mai múa bụi trần. Khoảnh khắc cùng người sánh bước, chỉ có cánh hoa tường vi thầm lặng dõi theo.",

    # 12003 - Canace (Phương Trình Chiến Thắng / 胜利的方程式)
    "CharacterSkin.12003.2": "Tư duy cẩn mật, tính toán chuẩn xác, động tác đúng chuẩn sách giáo khoa.\x0bBứt tốc, bật nhảy, đập bóng! Mọi thứ đều theo đúng kế hoạch, thế nhưng cơ thể lại chẳng bắt kịp suy nghĩ!\x0b——Hửm? Cái vị trí Quán quân bảng bình chọn độ nổi tiếng này rốt cuộc là sao cơ chứ hả!?",

    # 12303 - Ann (Công Chúa Xứ Rừng Diệu Kỳ / 漫游奇境的森林公主)
    "CharacterSkin.12303.2": "Từ hốc cây cổ thụ rơi vào cõi diệu kỳ, nàng công chúa nhỏ lạc bước giữa mê cung thời gian ơi, chẳng việc gì phải vội vàng tìm lối ra đâu, bởi vì phong cảnh tuyệt mỹ nhất vốn ẩn giấu bên trong những giấc mộng ngỡ như hoang đường ấy.",

    # 12503 - Freesia (Món Quà Tuyết Rơi / 落雪的赠礼)
    "CharacterSkin.12503.2": "Tiết Nguyện Tuyết mà cô ấy hằng mong đợi chính là bếp lò bập bùng ấm áp, một chén rượu quả thơm nồng, tiếng cười rộn rã của bạn bè thân thiết, cùng một món quà độc nhất vô nhị đến từ người.",

    # 12603 - Flora (Sân Khấu Do Chính Tôi Dựng Xây / 我的舞台我建造)
    "CharacterSkin.12603.2": "Đèn chiếu đã sẵn sàng——\nTiến lên nào! Lần này, tôi nhất định sẽ cho cả thế giới thấy rằng sân khấu của tôi là do chính tôi tỏa sáng!",

    # 12703 - Teresa (Tân Binh Dũng Giả Đến Trình Diện / 新人勇者前来报到)
    "CharacterSkin.12703.2": "Cầm lấy thanh bảo kiếm tốt nhất trong làng, dũng giả Teresa bắt đầu chuyến đại mạo hiểm huyền thoại! Ồ~ Rương kho báu vàng lấp lánh này? Để tớ mở ra xem nào—— Oa oa oa—— Cái quái gì thế này hả trời?!",

    # 13203 - Minova (Mộng Ngày Chếnh Choáng / 微醺白日梦)
    "CharacterSkin.13203.2": "Cánh tay cảm nhận sự mát rượi của mặt bàn học, bờ lưng đón lấy hơi ấm của ánh nắng khẽ rơi.\x0bHương thơm trang sách khiến lòng say đắm—— Đây chính là một giấc mộng ngày chếnh choáng ngọt ngào.",
    # 13204 - Minova (Sóng Gương Lấp Lánh ☆ Nỗi Đau Đêm Tối / 粼粼镜影☆漆黑心伤)
    "CharacterSkin.13204.2": "Đứng trước gương tập luyện vẻ mặt lạnh lùng lần thứ một trăm linh một, thế nhưng khoảnh khắc quay đầu lại chạm phải ánh mắt cậu. Thế là mọi lớp ngụy trang sụp đổ hoàn toàn, chỉ còn lại sự ngượng ngùng bối rối.",

    # 13303 - Nazuka (Giọt Sương Đầu Hè / 清露微滴的初夏)
    "CharacterSkin.13303.2": "Một làn hương khẽ thoảng, những đóa hoa đầu hè lặng lẽ bung nở. Một cảm xúc chạm khẽ, tựa như bàn tay đang cùng người nắm chặt chiếc chong chóng quay tròn.",

    # 13403 - Fuyuka (Vượt Qua Kỳ Thử Việc! / 平安度过试用期！)
    "CharacterSkin.13403.2": "Điểm danh đúng giờ không đi muộn, chuẩn bị nguyên liệu thật chu toàn. Cần cù chăm chỉ, nơm nớp lo toan. Ấy da—— Oạch một cái, sao lại làm hỏng bét nữa rồi?!",

    # 13503 - Mistique (Đêm Ca Cao Ngọt Ngào / 可可甜心情与夜)
    "CharacterSkin.13503.2": "Say đắm trong vị ngọt ngào của ca cao, cán chổi vút qua bầu trời sao thăm thẳm, bỏ lại mọi âu lo phía sau lưng—— Đây chính là chuyến mạo hiểm lãng mạn chỉ thuộc về đôi ta.",
    # 13504 - Mistique (Thong Dong Hoàng Hôn / 悠悠哉哉，惬意夕阳)
    "CharacterSkin.13504.2": "Dẫu là phù thủy lấy chân tướng làm lẽ sống, thỉnh thoảng cũng cần một kỳ nghỉ thong dong nhàn nhã chứ.\x0bVươn vai lười biếng, ngắm nhìn ráng chiều tà—— Có gì trên đời an nhiên hơn thế này được nữa đâu?",

    # 14103 - Chixia (Nữ Hoàng Cơ Trong Gương / 镜中的红心皇后)
    "CharacterSkin.14103.2": "Ai bảo thế giới trong gương chỉ là hư ảo?\x0bKhoảnh khắc nàng đội lên chiếc vương miện hoàng hậu, vai chính cùng phản diện hoán đổi vị trí, sự hoang đường biến thành luật lệ, tâm điểm vũ đài chuyển dịch về phía nàng.\x0b——Hoan nghênh đã đặt chân tới cõi mộng kỳ ảo của Nữ Hoàng Cơ.",

    # 14203 - Cosette (Vị Hè Riêng Một Góc Trời / 夏日滋味，独享时分)
    "CharacterSkin.14203.2": "Bờ biển mùa hè thì cũng chỉ có nắng vàng, nước biển với bãi cát thôi mà, chẳng có gì đặc biệt cả——\x0bCái gì cơ?! Cậu bảo có món nước giải khát thanh mát độc quyền trên đảo á?! Thế thì tôi cũng phải đi nữa!",

    # 14403 - Chitose (Hoa Bìm Nở Rộ, Thiếu Nữ Tỉnh Giấc / 牵牛花开，少女初醒)
    # Triệt tiêu thảm họa "Rau muống ngâm trong nước"!
    "CharacterSkin.14403.2": "Đóa hoa triêu nhan cắm trong bình nước thanh khiết này—— sắc hoa tươi thắm cùng hương thơm thanh nhã ấy, liệu có thể lưu giữ được bao lâu đây?",

    # 14703 - Caramel (Tiếng Bass Ngọt Ngào / 梦萌贝斯音)
    "CharacterSkin.14703.2": "Tút tút te te tút, tránh đường nào! Buổi biểu diễn sắp sửa bắt đầu rồi đó——\nHãy lắng nghe nè—— Giấc mộng âm bass bồng bềnh, ngọt ngào rộn rã, tưng bừng đinh đang!",

    # 14903 - Gerie (Lời Hẹn Khi Tuyết Tan / 相约融雪后)
    # Triệt tiêu thảm họa "nhiệm vụ ủy thác nở rộ"!
    "CharacterSkin.14903.2": "Vị chua đắng của cà phê, hương thơm ngát của đóa tường vi, em muốn chia sẻ trọn vẹn mọi trải nghiệm mới mẻ này cùng với anh. Khi tuyết tan rồi, chúng mình cùng nhau hẹn hò một chuyến nhé?",

    # 15503 - Shia (Lời Mời Từ Biển San Hô / 珊瑚海的邀约)
    "CharacterSkin.15503.2": "Trong làn nước biển dạt dào, phảng phất hương vị của rạn san hô, và cả hương thơm quen thuộc của anh nữa. Khẽ nhắm mắt lại, ngỡ như đang được tất thảy sự dịu dàng này ôm trọn vào lòng vỗ về.",

    # 15603 - Nazuna (Tiệc Trà Tinh Quái / 古灵精怪茶话会)
    "CharacterSkin.15603.2": "Cuộc sống cũng chỉ cần có thế này thôi nhỉ: Thưởng thức một miếng bánh ngọt Opera, rồi hãm một ấm hồng trà thơm lừng. Giấc mơ đang dần nở rộ, cho đến khi vòi ấm trà phà ra những bọt bong bóng hơi nước dịu êm."
}

# -------------------------------------------------------------------------
# 2. POLISHED UNLOCKLOOK VOICE SUBTITLES (00552)
# -------------------------------------------------------------------------
POLISHED_UNLOCK_LOOK_VOICE = {
    "vo_103_ui_unlockLook_001": "Sếp ơi! Trông em thế này đã ngầu hơn chút nào chưa nè?",
    "vo_107_ui_unlockLook_001": "Ủa... Tiếng động cơ của Lapis Eagle nghe lạ quá... Oa oa oa——!",
    "vo_108_ui_unlockLook_001": "Đây là điều khoản thỏa thuận bổ sung trong hợp đồng. Cậu nhớ đọc kỹ từng chữ đấy nhé.",
    "vo_110_ui_unlockLook_001": "Để thắt chặt mối quan hệ giữa đôi ta, chi bằng chúng mình cùng xem lại bản khế ước một lần nữa nhé?",
    "vo_111_ui_unlockLook_001": "Túi xách này nặng lắm đó nha, cậu đừng có xem thường sức nặng của tri thức đấy!",
    "vo_112_ui_unlockLook_001": "Chuyến đi này, chúng mình hãy cùng nhau phiêu lưu mãi mãi nhé!",
    "vo_113_ui_unlockLook_001": "Làn nước có thể biến hóa thành muôn hình vạn trạng, cũng tức là tiềm năng của nó là vô cùng vô tận!",
    "vo_114_ui_unlockLook_001": "Sức mạnh hắc ám bị phong ấn nay đã được giải phóng tại đây! Nha~haha!",
    "vo_115_ui_unlockLook_001": "Em không còn là một đứa trẻ bình thường nữa đâu! Giờ em đã có thể bảo vệ tốt cho Ma Vương rồi!",
    "vo_116_ui_unlockLook_001": "Ước mơ lớn nhất của em là có được một mảnh đất thảo mộc của riêng mình.",
    "vo_117_ui_unlockLook_001": "Jinglin, màn xuất hiện hôm nay thật là hoành tráng rực rỡ!",
    "vo_118_ui_unlockLook_001": "Lưỡi hái sắc bén đang reo vang phấn khích... Có vẻ như tất cả chúng ta đều đang rất hào hứng đấy.",
    "vo_119_ui_unlockLook_001": "Xin hãy để em luôn được kề cận bên người. Tựa như chiếc bóng, tựa như một giấc chiêm bao...",
    "vo_120_ui_unlockLook_001": "Có lẽ tôi cần phải nghiêm túc hơn rồi, nếu muốn đáp ứng trọn vẹn kỳ vọng của cậu.",
    "vo_123_ui_unlockLook_001": "Ann, Coco và Bubble đều đã mạnh hơn nhiều rồi! Cố lên nào Big Boss ơi, nhanh chân xuất phát thôi, đánh cho đám kẻ xấu kia tơi bời hoa lá nào!",
    "vo_125_ui_unlockLook_001": "Vận may hôm nay tựa hồ đang đứng về phía chúng ta đấy.",
    "vo_126_ui_unlockLook_001": "Bất luận đứng trên sân khấu nào, tôi cũng sẽ dốc hết tâm huyết biểu diễn vì cậu.",
    "vo_127_ui_unlockLook_001": "Dũng giả Teresa đã sẵn sàng lên đường! Bất kể kẻ địch có là ma vương hùng mạnh đến đâu, tớ cũng quyết không lùi bước!",
    "vo_130_ui_unlockLook_001": "Vạn Tống Ốc đã chuẩn bị chu toàn! Hôm nay chúng ta sẽ chuyển phát nụ cười tới phương trời nào đây?",
    "vo_132_ui_unlockLook_001": "Đừng... đừng có nhìn chằm chằm vào tôi như thế chứ... Tôi chỉ tiện tay thay đổi chút phong cách thôi mà!",
    "vo_133_ui_unlockLook_001": "Làn gió ban mai thổi qua thật dễ chịu... Cảm ơn cậu đã luôn đồng hành bên cạnh tớ.",
    "vo_134_ui_unlockLook_001": "Nguyên liệu pha chế đã chuẩn bị xong xuôi! Lần này em nhất định sẽ không làm hỏng đâu!",
    "vo_135_ui_unlockLook_001": "Bí mật ẩn giấu dưới lớp áo choàng này... liệu cậu có đủ can đảm để giải mã không?",
    "vo_137_ui_unlockLook_001": "Tiền bối ơi! Em đã trang bị đầy đủ rồi, xin hãy chỉ đạo bước tiếp theo ạ!",
    "vo_139_ui_unlockLook_001": "Bất kể chủ nhân phân phó việc gì, hầu gái Allie cũng sẽ hoàn thành thật sạch sẽ tinh tươm!",
    "vo_140_ui_unlockLook_001": "Bánh Đội Trưởng phiên bản cải tiến đã hoàn tất! Cậu có muốn là người đầu tiên nếm thử không nè?",
    "vo_141_ui_unlockLook_001": "Bút vẽ trong tay, vung mực thành rồng! Cậu thấy phong thái này của tôi thế nào?",
    "vo_142_ui_unlockLook_001": "Khung cảnh này... cảm xúc này... Mau đứng yên đó, để tôi vẽ lại khoảnh khắc này vào tranh!",
    "vo_143_ui_unlockLook_001": "Trong bóng tối mịt mùng, lưỡi đao của ta sẽ là ánh sáng mở lối cho ngươi.",
    "vo_144_ui_unlockLook_001": "Kiếm ý thanh tịnh, tâm tựa mặt hồ. Xin người hãy chỉ giáo thêm.",
    "vo_145_ui_unlockLook_001": "Tấm màn nhung đã khép, nhưng vở kịch giữa đôi ta chỉ vừa mới bắt đầu.",
    "vo_147_ui_unlockLook_001": "Giai điệu này là dành riêng cho cậu đấy! Cùng hòa mình vào nhịp bass bùng nổ nào!",
    "vo_149_ui_unlockLook_001": "Tâm can rực cháy, xiềng xích vỡ vụn... Hãy để em cảm nhận nỗi đau ngọt ngào này nhiều hơn nữa!",
    "vo_150_ui_unlockLook_001": "Hừ, đừng tưởng khoác lên bộ cánh này là ta sẽ mềm lòng với ngươi đấy nhé!",
    "vo_155_ui_unlockLook_001": "Hương thơm của biển cả và nụ cười của anh... là những điều em trân quý nhất trần đời.",
    "vo_156_ui_unlockLook_001": "Chiếc ấm trà biết hát đã sôi sùng sục rồi kìa! Đến giờ thưởng thức tiệc trà tinh quái rồi!",
    "vo_157_ui_unlockLook_001": "Từng con sóng biển đang reo vui chúc mừng chúng ta đấy! Tiếp tục tiến lên thôi nào!",
    "vo_158_ui_unlockLook_001": "Đêm Thánh rực rỡ, món quà này... là ta đặc biệt chuẩn bị riêng cho ngươi đó.",
    "vo_159_ui_unlockLook_001": "Năm mới đón nhận sinh khí mới, để tôi bắt mạch kiểm tra sức khỏe đầu năm cho cậu nhé.",
    "vo_160_ui_unlockLook_001": "Ánh hoàng hôn trên mặt biển đẹp đến nao lòng... Thật may vì có cậu cùng ngắm nhìn.",
    "vo_162_ui_unlockLook_001": "Ánh sáng Khởi Nguyên soi rọi lối đi, ta sẽ mãi là thanh kiếm bảo vệ con đường của người."
}

def main():
    t0 = time.time()
    print("=" * 80)
    print("BẮT ĐẦU ĐẠI TU TOÀN DIỆN LỜI THOẠI CỦA CÁC SKIN (CAMPAIGN 25)")
    print("=" * 80)

    # ---------------------------------------------------------------------
    # 1. CẬP NHẬT CHARACTERSKIN (00597 & 00844)
    # ---------------------------------------------------------------------
    p_skin_en = ENTRIES_DIR / "00597_0xd79f78b562c5c75c.bin"
    p_skin_twin = ENTRIES_DIR / "00844_0xe9523ad410d60587.bin"
    assert p_skin_en.exists() and p_skin_twin.exists(), "CharacterSkin tables missing!"

    d_skin_en = json.loads(p_skin_en.read_text(encoding="utf-8"))
    d_skin_twin = json.loads(p_skin_twin.read_text(encoding="utf-8"))

    skin_quote_count = 0
    for k, v in POLISHED_SKIN_QUOTES.items():
        d_skin_en[k] = v
        d_skin_twin[k] = v
        skin_quote_count += 1

    p_skin_en.write_text(json.dumps(d_skin_en, indent=2, ensure_ascii=False), encoding="utf-8")
    p_skin_twin.write_text(json.dumps(d_skin_twin, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Đã cập nhật thành công {skin_quote_count} Lời thoại / Trích dẫn Skin vào CharacterSkin (00597 & 00844).")

    # ---------------------------------------------------------------------
    # 2. CẬP NHẬT MASTER VOICE SUBTITLES (00552)
    # ---------------------------------------------------------------------
    p_voice = ENTRIES_DIR / "00552_0x80911df3a563e0f3.bin"
    assert p_voice.exists(), "Master voice subtitles table missing!"

    d_voice = json.loads(p_voice.read_text(encoding="utf-8"))
    voice_update_count = 0

    for k, line_vi in POLISHED_UNLOCK_LOOK_VOICE.items():
        if k in d_voice:
            v_entry = d_voice[k]
            text_dict = v_entry.setdefault("text", {})
            # Update both female_jp and female_cn tracks so players using either voice hear/see proper Vietnamese
            text_dict["female_jp"] = [line_vi, "", "", ""]
            text_dict["female_cn"] = [line_vi, "", "", ""]
            voice_update_count += 1

    p_voice.write_text(json.dumps(d_voice, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Đã cập nhật thành công {voice_update_count} câu thoại giọng nói mở khóa Skin vào Master Voice (00552).")

    # ---------------------------------------------------------------------
    # 2.5. CẬP NHẬT MAINSKILL (00667 & 00914) - TRIỆT TIÊU 'PHƯỢT THỦ' & 'AUTO TẤN CÔNG'
    # ---------------------------------------------------------------------
    p_ms_en = ENTRIES_DIR / "00667_0x57e760255c1d3b2d.bin"
    p_ms_twin = ENTRIES_DIR / "00914_0xb09952a17d27201c.bin"
    if p_ms_en.exists() and p_ms_twin.exists():
        d_ms_en = json.loads(p_ms_en.read_text(encoding="utf-8"))
        d_ms_twin = json.loads(p_ms_twin.read_text(encoding="utf-8"))

        ms_fixes = {
            "MainSkill.405101.2": "Du Hành Giả Đa Năng hệ Quang mỗi khi ở trên sân 1 giây sẽ nhận được 1 tầng 「Tỷ Lệ Đồng Bộ」: Mỗi tầng tăng Sát Thương hệ Quang của bản thân thêm <color=#ec6d21>{1}</color> trong {2} giây, cộng dồn tối đa {3} tầng.\x0bKhi 「Tỷ Lệ Đồng Bộ」 đạt tối đa, gây sát thương sẽ gắn thêm 「Phản Ứng Thù Địch」 lên mục tiêu: Tăng Sát Thương Đòn Đánh Thường hệ Quang phải chịu thêm <color=#ec6d21>{4}</color> trong {5} giây.",
            "MainSkill.400301.2": "Du Hành Giả Đa Năng hệ Quang mỗi khi ở trên sân 1 giây sẽ nhận được 1 tầng 「Hạt Quang Học」: Mỗi tầng tăng Tấn Công của bản thân thêm <color=#ec6d21>{1}</color> trong {2} giây, cộng dồn tối đa {3} tầng.\x0bKhi 「Hạt Quang Học」 đạt tối đa, Du Hành Giả Chủ Lực hệ Quang sẽ nhận được 「Đôi Cánh Ánh Sáng」: Tăng Sát Thương Đòn Đánh Thường thêm <color=#ec6d21>{4}</color> trong {5} giây.",
            "MainSkill.400801.2": "Khi Du Hành Giả Đa Năng hệ Thủy gây Sát Thương Kỹ Năng, gắn 1 tầng 「Tình Lãng」 lên mục tiêu trong {1} giây, cộng dồn tối đa {2} tầng.\x0bKhi 「Tình Lãng」 đạt {3} tầng: Khiến Sát Thương Đòn Đánh Thường hệ Thủy mục tiêu phải chịu tăng <color=#ec6d21>{4}</color>;\x0bKhi 「Tình Lãng」 đạt {5} tầng: Khiến Sát Thương Kỹ Năng hệ Thủy mục tiêu phải chịu tăng thêm <color=#ec6d21>{6}</color>.",
        }
        for k, v in ms_fixes.items():
            d_ms_en[k] = v
            d_ms_twin[k] = v

        p_ms_en.write_text(json.dumps(d_ms_en, indent=2, ensure_ascii=False), encoding="utf-8")
        p_ms_twin.write_text(json.dumps(d_ms_twin, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✓ Đã cập nhật MainSkill (00667 & 00914): Chuẩn hóa 'Du Hành Giả Đa Năng', triệt tiêu hoàn toàn 'phượt thủ' và 'Auto Tấn Công'.")

    # ---------------------------------------------------------------------
    # 2.6. CẬP NHẬT UITEXT (00789 & 01036) - ĐỘ KHÓ & VƯỢT ẢI CHUẨN
    # ---------------------------------------------------------------------
    p_uitext_en = ENTRIES_DIR / "00789_0x87cc29ac0defc2d9.bin"
    p_uitext_twin = ENTRIES_DIR / "01036_0x363690c09b175230.bin"
    if p_uitext_en.exists() and p_uitext_twin.exists():
        d_ui_en = json.loads(p_uitext_en.read_text(encoding="utf-8"))
        d_ui_twin = json.loads(p_uitext_twin.read_text(encoding="utf-8"))

        ui_fixes = {
            "UIText.Diffculty_1.1": "Độ khó 1",
            "UIText.Diffculty_2.1": "Độ khó 2",
            "UIText.Diffculty_3.1": "Độ khó 3",
            "UIText.SkillInstance_PassConfition_1.1": "Thời gian vượt ải ≤ {0} s",
            "UIText.SkillInstance_PassConfition_2.1": "Vượt ải khi còn lại > {0} giây",
            "UIText.RegusBoss_Unlock.1": "Chưa mở khóa độ khó",
            "UIText.StarTower_Rank_Diff_Score.1": "Điểm độ khó",
        }
        for k, v in ui_fixes.items():
            d_ui_en[k] = v
            d_ui_twin[k] = v

        p_uitext_en.write_text(json.dumps(d_ui_en, indent=2, ensure_ascii=False), encoding="utf-8")
        p_uitext_twin.write_text(json.dumps(d_ui_twin, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✓ Đã cập nhật UIText (00789 & 01036): Chuẩn hóa 'Độ khó' và điều kiện vượt ải.")

    # ---------------------------------------------------------------------
    # 3. ĐÓNG GÓI LẠI DIST/DATA_PATCHED_VI.ARCX VỚI MÃ HÓA XXTEA
    # ---------------------------------------------------------------------
    print("\n-> Đang đóng gói lại dist/data_patched_vi.arcx với mã hóa XXTEA...")
    repack_archive(DEC_DIR, OUTPUT_ARCX, encrypt_payload=True)
    arc = ArcxArchive(OUTPUT_ARCX)
    new_sha = hashlib.sha256(OUTPUT_ARCX.read_bytes()).hexdigest()
    new_size = OUTPUT_ARCX.stat().st_size
    print(f"✓ Hoàn tất đóng gói canonical archive: {new_size:,} bytes")
    print(f"  SHA-256: {new_sha}")

    # ---------------------------------------------------------------------
    # 4. DUAL-DEPLOY TRỰC TIẾP VÀO CẢ 2 BẢN CÀI GAME
    # ---------------------------------------------------------------------
    print("\n-> Đang triển khai trực tiếp từ dist/ vào client game...")
    deploy_targets = [
        ("Yostar Standalone", LIVE_YOSTAR_DATA),
        ("Steam Installation", LIVE_STEAM_DATA)
    ]
    for label, target_path in deploy_targets:
        if target_path.parent.exists():
            shutil.copy2(OUTPUT_ARCX, target_path)
            deployed_sha = hashlib.sha256(target_path.read_bytes()).hexdigest()
            assert deployed_sha == new_sha, f"Deployment verification failed for {label}!"
            print(f"  [DEPLOYED] {label}: {target_path} ({deployed_sha[:12]}...)")
        else:
            print(f"  [SKIP] {label}: Đường dẫn không tồn tại ({target_path.parent})")

    # ---------------------------------------------------------------------
    # 5. CẬP NHẬT BÀI KIỂM THỬ CHỐNG THOÁI LUI VERIFY_DEPLOYED_GAME_DATA.PY
    # ---------------------------------------------------------------------
    print("\n-> Đang cập nhật và chạy kiểm chứng tự động qua verify_deployed_game_data.py...")
    verify_script = ROOT / "tools" / "verify_deployed_game_data.py"
    v_content = verify_script.read_text(encoding="utf-8")

    # Add checks for CharacterSkin in verify script if not present
    if "CharacterSkin.14403.2" not in v_content:
        # Add EXPECTED_SKIN_QUOTES
        skin_check_code = '''
EXPECTED_SKIN_QUOTES = {
    "CharacterSkin.14403.2": "Đóa hoa triêu nhan cắm trong bình nước thanh khiết này—— sắc hoa tươi thắm cùng hương thơm thanh nhã ấy, liệu có thể lưu giữ được bao lâu đây?",
    "CharacterSkin.14903.2": "Vị chua đắng của cà phê, hương thơm ngát của đóa tường vi, em muốn chia sẻ trọn vẹn mọi trải nghiệm mới mẻ này cùng với anh. Khi tuyết tan rồi, chúng mình cùng nhau hẹn hò một chuyến nhé?",
    "CharacterSkin.11104.2": "Cái đó... Em sẽ cố hết sức giữ thăng bằng cho chiếc phao bơi này, nhưng khi trèo lên anh nhớ cẩn thận một chút nhé.\\x0b——Đ-Đương nhiên rồi, nếu anh lỡ sảy chân rơi xuống nước, em nhất định sẽ kéo anh lại thật chặt!",
}
'''
        v_content = v_content.replace(
            "EXPECTED_GACHA_STORAGE = {",
            skin_check_code + "\nEXPECTED_GACHA_STORAGE = {"
        )
        # Add verification loop in verify_data_arcx
        skin_verify_block = '''
        # CharacterSkin (0xd79f78b562c5c75c)
        if e["hash"] == 0xd79f78b562c5c75c:
            data = xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY)
            d = json.loads(data.decode("utf-8"))
            print("  [PASS] Decrypted CharacterSkin table.")
            for k, expected_val in EXPECTED_SKIN_QUOTES.items():
                actual_val = d.get(k)
                if actual_val != expected_val:
                    raise AssertionError(f"Skin quote regression at {k}: expected '{expected_val}', got '{actual_val}'")
                print(f"    - {k}: '{actual_val[:40]}...' (MATCH)")
'''
        v_content = v_content.replace(
            '# Voice Subtitles (0x80911df3a563e0f3)',
            skin_verify_block + '\n        # Voice Subtitles (0x80911df3a563e0f3)'
        )

    verify_script.write_text(v_content, encoding="utf-8")

    res = subprocess.run([sys.executable, str(verify_script)], capture_output=True, text=True, encoding="utf-8")
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        sys.exit(1)

    elapsed = time.time() - t0
    print(f"\n[HOÀN THÀNH XUẤT SẮC TRONG {elapsed:.2f} GIÂY] ĐẠI TU TOÀN DIỆN LỜI THOẠI CỦA CÁC SKIN!")

if __name__ == "__main__":
    main()
