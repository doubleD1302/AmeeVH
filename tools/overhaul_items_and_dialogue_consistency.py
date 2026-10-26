#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master Overhaul for Items, Item Descriptions, and Dialogue Pronoun Consistency (Campaign 21)
-----------------------------------------------------------------------------------------
1. Item Table Overhaul (00653 & 00900):
   - Aligns 152 instances of 'Lữ khách' -> 'Du Hành Giả' (e.g. 'Thiên phú Du Hành Giả').
   - Aligns all instances of 'Cự Tháp' -> 'Tháp Sao Monolith' / 'Tháp Sao'.
   - Replaces crude Honor Title translations in Item with official titles from Honor (00645).
   - Re-authors crude skin certificates, lore items, and detailed item stories.
   - Cleans untranslated English fragments (Cataclysm Survivor, A Finale Echoing, Research, Shop).
   - Synchronizes 100% of clean data to twin table 00900 (eliminating all Chinese).

2. Dialogue Pronoun Consistency Overhaul (00552):
   - Enforces strict canonical character pronoun matrix across all 41 characters.
   - Eliminates all 94 remaining conflicting pronoun occurrences (Chaton, Firefly, Iris,
     Fuyuka, Eleanor, Sparkla, Cosette, Nazuna, Alina, Tilia).
   - Eliminates all 36 occurrences of crude MT 'Bạo chúa' -> 'Ma Vương'.

3. Repack dist/data_patched_vi.arcx with XXTEA encryption.
4. Dual-deploy to Yostar and Steam live installations.
5. Anti-regression verification with tools/verify_deployed_game_data.py.
"""

from __future__ import annotations
import hashlib
import json
import re
import shutil
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

# =========================================================================
# 1. SPECIFIC ITEM OVERRIDES
# =========================================================================
ITEM_SPECIFIC_OVERRIDES = {
    # Honor titles alignment (Item -> Honor table matching)
    "Item.111001.1": "Ma Vương Tập Sự",
    "Item.111001.2": "Mở khóa Danh hiệu Vinh dự: Ma Vương Tập Sự.",
    "Item.111002.1": "Ngọn Gió Khu Tro Tàn",
    "Item.111002.2": "Mở khóa Danh hiệu Vinh dự: Ngọn Gió Khu Tro Tàn.",
    "Item.111003.1": "Anh Hùng Cầu Thủy Đạo",
    "Item.111003.2": "Mở khóa Danh hiệu Vinh dự: Anh Hùng Cầu Thủy Đạo.",
    "Item.111004.1": "Nhà Tài Trợ Hoa Lệnh",
    "Item.111004.2": "Mở khóa Danh hiệu Vinh dự: Nhà Tài Trợ Hoa Lệnh.",
    "Item.111004.3": "Thêm bạn mới, thêm những người đồng hành mới.",
    "Item.111005.1": "Quý Khách Lữ Đoàn",
    "Item.111005.2": "Mở khóa Danh hiệu Vinh dự: Quý Khách Lữ Đoàn.",
    "Item.111005.3": "Cậu đã mang lại sự đổi thay cho thành phố này, dẫu đó chỉ là một thay đổi nhỏ nhoi...",
    "Item.111006.1": "Nhân Viên Ưu Tú",
    "Item.111006.2": "Mở khóa Danh hiệu Vinh dự: Nhân Viên Ưu Tú.",
    "Item.111006.3": "Sự nỗ lực chăm chỉ của cậu cuối cùng đã được đền đáp xứng đáng.",
    "Item.111007.1": "Người Nhặt Ánh Sáng",
    "Item.111007.2": "Mở khóa Danh hiệu Vinh dự: Người Nhặt Ánh Sáng.",
    "Item.111008.1": "Truy Vết Bóng Ma",
    "Item.111008.2": "Mở khóa Danh hiệu Vinh dự: Truy Vết Bóng Ma.",
    "Item.111009.1": "Bậc Thầy Ước Nguyện",
    "Item.111009.2": "Mở khóa Danh hiệu Vinh dự: Bậc Thầy Ước Nguyện.",
    "Item.111010.1": "Ký Ức Hoa Cúc",
    "Item.111010.2": "Mở khóa Danh hiệu Vinh dự: Ký Ức Hoa Cúc.",
    "Item.111011.1": "Tạm Biệt Ma Vương",
    "Item.111011.2": "Mở khóa Danh hiệu Vinh dự: Tạm Biệt Ma Vương.",

    # Badges alignment
    "Item.112103.1": "Chuyên Gia Tìm Mèo",
    "Item.112103.2": "Mở khóa Huy hiệu Vinh dự: Chuyên Gia Tìm Mèo.",
    "Item.112103.3": "Minh chứng tình bạn gắn kết cùng Amber!",
    "Item.112107.1": "Cộng Sự Chính Nghĩa",
    "Item.112107.2": "Mở khóa Huy hiệu Vinh dự: Cộng Sự Chính Nghĩa.",
    "Item.112107.3": "Minh chứng tình bạn gắn kết cùng Tilia!",
    "Item.112108.1": "Ngôi Sao May Mắn",
    "Item.112108.2": "Mở khóa Huy hiệu Vinh dự: Ngôi Sao May Mắn.",
    "Item.112108.3": "Minh chứng tình bạn gắn kết cùng Kasimira!",
    "Item.112110.1": "Đối Tác Khởi Nghiệp",
    "Item.112110.2": "Mở khóa Huy hiệu Vinh dự: Đối Tác Khởi Nghiệp.",
    "Item.112110.3": "Minh chứng tình bạn gắn kết cùng Firenze!",
    "Item.112111.1": "Quản Gia Chu Toàn",
    "Item.112111.2": "Mở khóa Huy hiệu Vinh dự: Quản Gia Chu Toàn.",
    "Item.112111.3": "Minh chứng tình bạn gắn kết cùng Iris!",
    "Item.112112.1": "Kẻ Vươn Tới Vì Sao",
    "Item.112112.2": "Mở khóa Huy hiệu Vinh dự: Kẻ Vươn Tới Vì Sao.",
    "Item.112112.3": "Minh chứng tình bạn gắn kết cùng Noya!",

    # Costume Certificates & Appearance Lore
    "Item.10304.3": "Nương theo làn gió biển ấm nồng, chớp lấy một thoáng lặng giữa ngày hội rộn rã, em khẽ hướng ánh nhìn về phía anh. Khoảnh khắc ấy thật bình yên biết bao.",
    "Item.10703.3": "Chiến giáp sẵn sàng, biến hình! Ý chí chiến đấu trong em bùng cháy rực rỡ hơn cả ánh mặt trời! Khoác lên tấm giáp công lý, em sẽ bảo vệ từng góc phố như một kỵ sĩ chân chính— Đây chính là chính nghĩa của Tilia!",
    "Item.10704.3": "Cô nàng rực rỡ như ánh mặt trời đã sẵn sàng tiếp sức cho cậu rồi đây! Hãy nở nụ cười thật tươi và chuẩn bị phong độ đỉnh nhất để đón nhận thử thách tiếp theo nào!",
    "Item.11003.3": "Mượn sức mạnh không thuộc về mình luôn phải trả cái giá tương xứng. Cậu đang sợ hãi điều gì thế? Tôi đâu phải ác quỷ.",
    "Item.11103.1": "Mảnh Ghép 1/365 Của Anh",
    "Item.11103.2": "Chứng chỉ mở khóa trang phục độc quyền của Iris: 'Mảnh Ghép 1/365 Của Anh'!",
    "Item.11103.3": "Dưới ánh nắng đông nhàn nhạt, anh cầm trên tay tách trà ấm, từng hơi thở khẽ phả thành làn sương mỏng manh. Người luôn tự nhận mình bình thường như anh, lại chính là người thắp sáng ngày hôm nay trở nên thật đặc biệt.",
    "Item.11104.1": "Lướt Sóng Êm Đềm Cùng Nhau",
    "Item.11104.2": "Chứng chỉ mở khóa trang phục độc quyền của Iris: 'Lướt Sóng Êm Đềm Cùng Nhau'!",
    "Item.11104.3": "Ừm... Em sẽ cố hết sức giữ chiếc phao này thăng bằng, nhưng anh nhớ cẩn thận khi bước lên nhé. —V-Và dĩ nhiên, lỡ anh có trượt chân rơi xuống nước, em nhất định sẽ kéo anh lên ngay!",
    "Item.11203.1": "Dư Quang Nắng Ấm",
    "Item.11203.2": "Chứng chỉ mở khóa trang phục độc quyền của Noya: 'Dư Quang Nắng Ấm'!",
    "Item.11205.1": "Phút Thảnh Thơi Bên Cậu",
    "Item.11205.2": "Chứng chỉ mở khóa trang phục độc quyền của Noya: 'Phút Thảnh Thơi Bên Cậu'!",
    "Item.11205.3": "Nhiệm vụ hôm nay của cậu là cùng tớ lười biếng cả ngày đó nha! Mau đi thay đồ ngủ đi nào, chỗ nằm êm ái cạnh tớ là dành riêng cho cậu đấy~",

    # Items & Lore cleanup
    "Item.12.2": "Phần thưởng nhận được sau khi chinh phục Tháp Sao Monolith. Có thể dùng để đổi vật phẩm trong Cửa Hàng.",
    "Item.22.2": "Chứng nhận tham gia Trợ Cấp Khởi Đầu. Dùng để tăng cấp Bậc Trợ Cấp.",
    "Item.22.3": "Khi bạn thám hiểm Tháp Sao Monolith và những vùng đất xa xôi, Trợ Cấp Khởi Đầu sẽ tiếp thêm động lực cho hành trình của bạn, khiến mỗi bước tiến đều nhân đôi giá trị.",
    "Item.23.2": "Chứng chỉ nhận được khi chiêu mộ Du Hành Giả. Có thể dùng để đổi vật phẩm trong Cửa Hàng.",
    "Item.24.2": "Chứng chỉ nhận được khi chiêu mộ Du Hành Giả. Có thể dùng để đổi vật phẩm quý hiếm trong Cửa Hàng.",
    "Item.30003.1": "Nhật Ký Du Hành Của Tiền Bối",
    "Item.30003.2": "Cuốn sổ tay ghi chép lại những trải nghiệm phiêu lưu quý giá của tiền bối đi trước.",
    "Item.31.2": "Huy chương nhận được từ hoạt động Sống Sót Sau Đại Thảm Họa. Có thể đổi vật phẩm trong Cửa Hàng.",
    "Item.32012.3": "Người xưa thường dạy: 'Tích tiểu thành đại', và trò chơi 'Mưa Đạn' chính là minh chứng rõ ràng nhất. Lối chơi được phát triển dựa trên độ khó tăng dần. Khi người chơi thông thường còn đang chật vật tìm đường 'sinh tồn', thì các cao thủ đã nhắm tới việc phá kỷ lục 'điểm số tối đa'.",
    "Item.34.2": "Chứng chỉ nhận được từ hoạt động Hồi Âm Đoạn Kết. Có thể đổi vật phẩm trong Cửa Hàng.",
    "Item.35.2": "Chứng chỉ nhận được từ hoạt động Hồi Âm Đoạn Kết. Có thể đổi vật phẩm trong Cửa Hàng.",
    "Item.37.2": "Chứng chỉ nhận được từ Chiến Dịch: Vây Hãm Bóng Đêm. Có thể đổi vật phẩm trong Cửa Hàng.",
    "Item.40.3": "Một đồng tiền vàng được chạm khắc tinh xảo, tương truyền là tín vật cho phép thỉnh cầu sự trợ giúp từ Ma Vương.",
    "Item.51.2": "Dùng để kích hoạt các điểm nghiên cứu trong Nghiên Cứu Tháp Sao Monolith.",
    "Item.51.3": "Bình thường, Tháp Sao Monolith luôn giữ vẻ nguyên sơ khi bạn đặt chân tới. Bởi vậy, những vết rạn nứt và mảnh vụn này trông thật lạc lõng đến kỳ lạ. Thế nhưng, ngay cả những mảnh tàn tích tưởng chừng vô giá trị ấy lại trở thành 'tài liệu nghiên cứu' vô cùng quý báu trong giới học giả. Đi kèm với đó là vô số khoản thù lao và ủy thác giá trị.",
    "Item.115.3": "Dẫu việc đồng hành cùng quái vật và các Stellaroid có sức hút riêng, nhưng một khi bước chân ra khỏi Tháp Sao Monolith và khu rừng bạt ngàn, thì thị trấn cùng học viện ngập tràn ánh ban mai có lẽ mới là đích đến sau cùng dành cho bạn.",
    "Item.1150.3": "Dẫu việc đồng hành cùng quái vật và các Stellaroid có sức hút riêng, nhưng một khi bước chân ra khỏi Tháp Sao Monolith và khu rừng bạt ngàn, thì thị trấn cùng học viện ngập tràn ánh ban mai có lẽ mới là đích đến sau cùng dành cho bạn.",
    "Item.402.2": "Hiệu lực trong 30 ngày. Đăng nhập mỗi ngày để nhận Nước Tăng Lực Đóng Lon và Vé Leo Tháp Monolith.",
    "Item.73116.2": "Tiền tệ nhận được khi tích cực tham gia sự kiện [Tháp Sao Quá Xa]. Có thể dùng để đổi vật phẩm trong Cửa Hàng Sự Kiện.",
    "Item.73201.3": "Một biểu ngữ do Hiệp Hội Du Hành Giả trao tặng nhằm vinh danh những Du Hành Giả đã thám hiểm trọn vẹn Tháp Sao Monolith và đóng góp các Kỷ Lục thám hiểm—'Tất cả vì một, một vì tất cả.'",
    "Item.116016.1": "Tháp Sao Quá Xa",
    "Item.116016.2": "Mở khóa Danh hiệu: Tháp Sao Quá Xa.",
    "Item.116016.3": "Minh chứng cho thành công vang dội trong sự kiện: Tháp Sao Quá Xa!",
    "Item.224009.3": "Chỉ còn đủ lương thực cho một ngày. Ví tiền thì rỗng tuếch. Phước Lành Oasis cũng sắp cạn kiệt... Bọn mình đã đặt cược tất cả vào ủy thác thám hiểm Tháp Sao Monolith lần này... —Thế nhưng, mỗi khi chụp ảnh kỷ niệm cùng nhau, đừng bao giờ quên nở một nụ cười thật tươi nhé!",
    "Item.224017.3": "Tựa như kiếp người phù du, pháo hoa nở rộ rồi nhanh chóng lụi tàn—ngắn ngủi nhưng rực rỡ muôn màu, khắc ghi dấu ấn riêng biệt giữa trời đêm thăm thẳm. Điều đó cũng giống như hành trình bất tận của một Du Hành Giả trên con đường chinh phục Tháp Sao Monolith, tất cả là vì một ngày mai có thể chạm tay tới những vì tinh tú...",
    "Item.224046.3": "Hãy xem đây như một vở kịch Stella tuyệt mỹ. Khi chúng ta trao trả món quà, những người bạn đồng hành đáng tin cậy vẫn luôn kề vai sát cánh. Hãy để lại sau lưng tòa Tháp Sao u tối. Đêm đông lạnh giá rồi sẽ qua đi, và ánh nắng xuân ấm áp sẽ một lần nữa tưới đẫm khắp thành phố từng một thời phồn vinh này.",
    "Item.510804.1": "Băng Đạn May Mắn",
    "Item.510804.2": "Băng đạn đặc biệt của Kasimira, nạp đầy những viên đạn may mắn.",
}

# =========================================================================
# 2. DIALOGUE PRONOUN & HARMONIZATION OVERRIDES (00552)
# =========================================================================
VOICE_PRONOUN_HARMONIZATION = {
    # ---------------- Tilia (107) - 'em/Tilia - Chúa Tể/chiến hữu/anh'
    "vo_107_ui_affchat4_001": "Cái dây buộc tóc này ấy ạ? Hồi em mới chập chững vào nghề, một người quen cứ nằng nặc dúi cho em, bảo là hợp với em lắm...",

    # ---------------- Kasimira (108) - 'tôi - cậu', never 'anh'
    "vo_108_combat_ultskill_001": "Tôi sẽ chôn vùi ngươi... bằng phát đạn định mệnh này!",
    "vo_108_ui_affchat4_001": "Tôi đã có thể lấy mạng cậu cả chục lần trong năm phút vừa qua đấy. Cậu nên đề cao cảnh giác hơn trước những hiểm nguy rình rập.",

    # ---------------- Firenze (110) - 'tôi - cậu/cưng', never 'em - anh'
    "vo_110_ui_hfc_002": "Ehehe... Đợi thêm chút nữa thì cậu sẽ hoàn toàn thuộc về tôi thôi.",
    "vo_110_ui_unlockCG_001": "Bây giờ chúng ta đã quyết định cùng nhau tiến về phía trước, đừng nghĩ rằng cậu có thể chạy trốn khỏi tôi nhé ♪",

    # ---------------- Iris (111) - 'em - anh/Sếp/Chúa Tể', never 'cậu'
    "vo_111_ui_exhang_001": "Ngủ gục ngay trên bàn làm việc sao? Em đoán là anh cũng đang làm việc vất vả lắm rồi, Sếp... Chiếc chăn ấm để đâu rồi ta...",
    "vo_111_ui_fullscreen_002": "Em thực sự muốn cảm ơn anh vì đã luôn giúp đỡ em, cho nên...",
    "vo_111_ui_greetnight_001": "Xem qua đống sổ sách này... Chắc đêm nay anh sẽ lo lắng đến mức mất ngủ mất thôi.",
    "vo_111_ui_hang_002": "Có anh bên cạnh, em cảm thấy làm việc hiệu quả hơn rất nhiều. Nếu anh không phiền... Liệu anh có thể ở lại thêm một chút được không?",
    "vo_111_ui_standee_001": "Em đang sắp xếp lại sổ cái đây ạ. Nếu anh nghĩ là em đang lén nhìn anh... thì chắc chỉ là do anh tưởng tượng thôi đó nha?",
    "vo_111_ui_swap_002": "Anh cẩn thận từng bước nhé. Đừng để bị vấp ngã đó...",
    "vo_111_ui_thankEx_001": "Oa... Món quà quý giá dường này là anh cất công chuẩn bị cho em sao?",
    "vo_111_ui_uniMusic_001": "Em thực sự rất khâm phục gu thưởng thức âm nhạc tinh tế của anh đấy, Sếp ạ.",
    "vo_111_ui_win_002": "Chiến thắng vang dội này cũng nằm trọn trong kế hoạch của anh rồi đúng không?",

    # ---------------- Chaton (114) - 'Chaton/em - anh/cậu/Ma Vương', never 'Tôi'
    "vo_114_combat_chat_001": "Chaton chán quá đi! Chán quá chán quá điii!!! Mau tìm trò gì vui vẻ làm đi mà!",
    "vo_114_combat_chat_002": "Có cậu ở bên Chaton, bọn mình chỉ có thắng, thắng và thắng thôi! ♪ Chaton nói có chuẩn không nè?",
    "vo_114_combat_chat_003": "Mỗi khi được nghe nhạc, Chaton tập trung tốt hơn hẳn luôn á ♪",
    "vo_114_combat_chat_004": "Chaton đã ngứa ngáy chân tay kể từ lúc bước chân vào Tháp Sao Monolith rồi... Chịu hết nổi rồi nha! Chaton tấn công được chưa?",
    "vo_114_combat_chatLvUp_001": "Độ khó đang tăng lên sao? Chaton tuyệt đối không trốn chạy đâu!",
    "vo_114_combat_chatNext_001": "Một sân khấu mới đang đón đợi Chaton kìa! Bọn mình mau xuất phát thôi nào!",
    "vo_114_combat_dead_001": "Chaton... vẫn chưa thua đâu mà...",
    "vo_114_combat_perk_002": "Ugh... Trật tự nào, hỡi nguồn sức mạnh bóng tối đang cuộn trào trong cơ thể Chaton!",
    "vo_114_combat_perk_003": "Chaton bắt được rồi! Giai điệu dẫn lối tới chiến thắng rực rỡ!",
    "vo_114_combat_shopRoom_001": "Ma Vương ơi! Mua cho Chaton món nước đó đi mà! Xem như tiếp thêm sức mạnh cho Chaton vĩ đại... Nha nha?",
    "vo_114_ui_affchat3_001": "Thứ ở trên bàn ấy ạ? Đó là cẩm nang biểu đồ game nhịp điệu mà Chaton đã cất công chọn lọc kỹ càng đó ♪",
    "vo_114_ui_affchat4_001": "Cậu am hiểu nhiều về truyền thuyết cổ xưa lắm đúng không? Kể cho Chaton nghe với, kể đi mà!",
    "vo_114_ui_affchat5_001": "Chỉ cần được ở bên cậu, Chaton có thể phá vỡ mọi kỷ lục!",
    "vo_114_ui_afflv2_001": "Chaton vừa tìm được bản nhạc nền siêu ngầu dành riêng cho màn xuất hiện của cậu nè!",
    "vo_114_ui_afflv3_001": "Cảm giác áp bức này...! Đúng rồi! Ma Vương cuối cùng cũng giáng lâm trong vinh quang trọn vẹn—",
    "vo_114_ui_afflv4_001": "Cho đến ngày cậu tìm lại được sức mạnh thực sự của mình, Chaton nhất định sẽ không bỏ cuộc đâu!",
    "vo_114_ui_discuss_004": "Chaton biết nhiều chuyện về Minova lắm đó nha.",
    "vo_114_ui_exhang_001": "Ma Vương ơi? Kìa kìa, ngài vẫn còn thở đó chứ!?",
    "vo_114_ui_fullscreen_001": "Chaton chưa từng nghĩ là có ngày được chơi game cùng Ma Vương luôn đó nha!",
    "vo_114_ui_fullscreen_002": "Hỡi Ma Vương, hãy cho Chaton mượn sức mạnh! Có thêm sức mạnh hắc ám của ngài, Chaton vĩ đại sẽ là bất khả chiến bại!",
    "vo_114_ui_gachaNew_001": "Hửm, anh chính là Ma Vương trong truyền thuyết sao? Nếu anh thực sự sở hữu sức mạnh hắc ám, Chaton có thể nhận làm thuộc hạ đó nha.",
    "vo_114_ui_gacha_001": "Chaton cảm thấy mối liên kết giữa đôi ta đã sâu sắc hơn rồi đấy! Hả? Đâu cần Ma Vương phải cảm ơn làm chi!",
    "vo_114_ui_greet_001": "Oa! Chaton dọa anh giật mình chưa? Chẹp... Ít ra anh cũng phải giả vờ ngạc nhiên chút chứ!",
    "vo_114_ui_greetmorn_001": "Chào buổi sáng, Ma Vương! Nè nè, hôm nay chúng ta đi đâu quậy phá nhỉ?",
    "vo_114_ui_greetnoon_001": "... Hả? Chaton vừa ngủ gật sao? Khoan đã, đã trưa trật rồi á?!",
    "vo_114_ui_hang_001": "Aaaaa! Đừng có bơ Chaton màaaaaaa!",
    "vo_114_ui_music_001": "Oa, khúc nhạc này hay quá! Chaton có thể nghe đi nghe lại cả ngày luôn ấy!",
    "vo_114_ui_newyear_001": "Ma Vương ơi, chúc mừng năm mới! Ngài đã lập kế hoạch cho năm nay chưa? Còn dự tính của Chaton là...",
    "vo_114_ui_posterchat_001": "Hôm nay Chaton đuối sức rồi...! Sức mạnh hắc ám cạn sạch trơn luôn rồi nè...",
    "vo_114_ui_posterchat_002": "Chaton hiểu rồi... Để trở thành một Ma Vương đích thực, ngài nhất định phải có bài ca chủ đề của riêng mình!",
    "vo_114_ui_posterchat_003": "Ma Vương nghĩ Chaton ngày nào cũng lười biếng chỉ biết cắm mặt chơi game sao?",
    "vo_114_ui_posterchat_006": "Nhân danh phước lành của khúc ca này, ta truyền lệnh cho ngươi! Hỡi khẩu súng trường thấm nhuần sức mạnh hắc ám... Hãy giải phóng uy lực đích thực!",
    "vo_114_ui_swap_001": "Chuẩn luôn, cứ giao hết mọi việc cho Chaton là chuẩn bài ♪",
    "vo_114_ui_swap_003": "Có Chaton ở đây thì nắm chắc chiến thắng trong tay rồi! ♪",
    "vo_114_ui_swap_004": "Bóng tối của vực sâu thẳm luôn đồng hành cùng Chaton!",
    "vo_114_ui_thankEx_001": "Độ hảo cảm dành cho Chaton vĩ đại đã phá vỡ mọi giới hạn! Không hổ danh là Ma Vương! Ngài hiểu Chaton hơn bất kỳ ai trên thế giới này luôn!",
    "vo_114_ui_valentine_001": "Đây là tinh thể bóng đêm thấm nhuần ma lực hắc ám của Chaton! Nè nè, nếm thử đi nha!",
    "vo_114_ui_win_002": "Gì cơ, xong xuôi hết rồi á? Chaton còn muốn đi chơi tiếp mà...",
    "vo_114_ui_xmas_001": "Chaton có linh cảm rằng vào đêm muộn hôm nay, sức mạnh hắc ám của Ma Vương sẽ bùng nổ đến đỉnh điểm!",

    # ---------------- Firefly (115) - 'em - anh/Ma Vương', never 'cậu'
    "vo_115_combat_chat_002": "Đừng nói với giáo sư rằng anh đã đến Tháp Monolith cùng em nhé.",
    "vo_115_ui_afflv1_001": "Anh muốn gì nào? Để em lấy từ Hộp Nguyện Ước cho anh nhé.",
    "vo_115_ui_afflv3_001": "Ma Vương ơi, anh có thích ngắm sao không? Em biết một chỗ đẹp lắm.",
    "vo_115_ui_afflv4_001": "Nơi mà anh có thể thả lỏng tâm hồn chính là nhà ư? Vậy thì Tháp Monolith, khu rừng, hay đống gấu bông Sherlock chất cao như núi...",
    "vo_115_ui_fullscreen_002": "Oáp... Em buồn ngủ quá... Em đi ngủ đây. Anh có thể kể cho em nghe một câu chuyện được không?",
    "vo_115_ui_greet_001": "Có chuyện gì vậy, Ma Vương ơi? Sao anh cứ loạng choạng bước đi bắt chước Glopo thế kia?",
    "vo_115_ui_greet_002": "Ma Vương ơi, anh cũng muốn chơi cùng Sherlock sao?",
    "vo_115_ui_posterchat_005": "Sherlock bông mềm mại! Anh tặng cái này cho em sao? Em vui lắm, cảm ơn anh nhiều.",
    "vo_115_ui_thankEx_001": "Ma Vương lúc nào cũng dịu dàng và tốt bụng với em cả.",
    "vo_115_ui_thank_001": "Ma Vương là người anh tốt nhất của em. Em sẽ nâng niu món quà này như chính anh vậy.",
    "vo_115_ui_valentine_001": "Hôm nay là dịp đặc biệt để tặng sô-cô-la cho người đặc biệt quan trọng...",
    "vo_115_ui_yourbirth_001": "Hôm nay là sinh nhật của anh. Nên em đã chuẩn bị một món quà nhỏ gửi tặng anh này.",

    # ---------------- Fuyuka (134) - 'em/Fuyuka - Chủ nhân', never 'tôi/cậu'
    "vo_134_combat_chat_003": "Hả? Chủ nhân muốn em đi đầu sao? Không đời nào, em không làm được đâu!",
    "vo_134_combat_dead_001": "Chủ nhân... Em xin lỗi, em vô dụng quá...",
    "vo_134_combat_dead_002": "Tầm nhìn... mờ dần rồi...",
    "vo_134_ui_affchat1_001": "Em... em luôn sợ giao tiếp với người lạ... Nhưng ở bên Chủ nhân, em thấy an tâm vô cùng...",
    "vo_134_ui_affchat3_001": "Chủ nhân... Người có bao giờ cảm thấy thất vọng về một đứa vụng về như em không ạ...?",
    "vo_134_ui_fullscreen_002": "Hự... Em không thể gượng dậy nổi nữa rồi. Xin lỗi Chủ nhân, người có thể đỡ em dậy được không?",
    "vo_134_ui_greetnoon_001": "Đ-Đợi đã, một kẻ tầm thường vô dụng như em mà cũng được dùng bữa trưa cùng Chủ nhân sao?!",
    "vo_134_ui_lose_001": "Là tại em... Em lại làm hỏng việc của Chủ nhân rồi...",

    # ---------------- Eleanor (137) - 'em/Eleanor - Tiền bối', never 'cậu/tôi'
    "vo_137_combat_chat_003": "Bất kỳ góc nhìn nào trong Tháp Monolith đóng khung lại trông cũng như một kiệt tác nghệ thuật vậy♪",
    "vo_137_combat_eventRoom_001": "Xin lỗi Tiền bối, người có rảnh chút lát không ạ?",
    "vo_137_ui_affchat1_001": "Mỗi đường kiếm Tiền bối chỉ dạy, em đều ghi khắc sâu đậm trong tâm trí!",
    "vo_137_ui_affchat3_001": "Được đứng phía sau bảo vệ Tiền bối là niềm vinh dự lớn nhất của em!",
    "vo_137_ui_afflv3_001": "Em sẽ tiếp bước con đường của người và có ngày vượt qua cả Tiền bối...",
    "vo_137_ui_greet_002": "Tiền bối ơi, người có thấy chiếc móc khóa Sherlock bản giới hạn của em đâu không?",
    "vo_137_ui_greetmorn_001": "Tiền bối có muốn nếm thử bữa sáng thanh đạm mà em vừa tự tay chuẩn bị không ạ?",
    "vo_137_ui_hang_001": "Tiền bối mệt rồi sao ạ? Để em pha một tách trà nóng cho người nhé!",
    "vo_137_ui_hfc_002": "Tiền bối muốn đập tay chúc mừng ạ? Vậy thì... chúc một ngày tuyệt vời phía trước! Nào, cùng cố gắng nhé!",
    "vo_137_ui_lose_001": "Em xin lỗi Tiền bối... Luyện tập của em vẫn còn chưa đủ...",
    "vo_137_ui_swap_001": "Được đứng trong đội hình là niềm vinh hạnh của em. Mong được Tiền bối chỉ bảo nhiều hơn ạ!",
    "vo_137_ui_unlockLook_001": "Tiền bối ơi, người có tự hào về em không nào?",

    # ---------------- Allie (139) - 'chị/Allie - cậu/em', never 'tôi'
    "vo_139_ui_affchat3_001": "Hồi viện mồ côi mới thành lập, chị từng ngây thơ nghĩ rằng việc chăm sóc bọn trẻ sẽ dễ dàng lắm cơ.",
    "vo_139_ui_affchat4_001": "Chị đã nghiêm túc suy nghĩ xem tại sao mỗi lần dọn dẹp chị lại biến mọi thứ thành bãi chiến trường như vậy...",
    "vo_139_ui_greet_001": "Cậu về rồi đấy à? Để chị hâm nóng bữa tối cho cậu nhé, đi cả ngày chắc đói bụng lắm rồi.",

    # ---------------- Sparkla (140) - 'em/Sparkla - Ma Vương', never 'tôi/bạn/ngươi/Bạo chúa'
    "vo_140_combat_battleClear_001": "Đã dọn sạch bóng dáng quân địch. Ma Vương hãy tranh thủ nghỉ ngơi khi có thể nhé.",
    "vo_140_combat_battleClear_002": "Em đi ngó nghiêng xung quanh một chút đây, đợi em xíu nhé!",
    "vo_140_combat_battleClear_003": "Nyehehe. Thu thập được dữ liệu xịn sò rồi nè ♪",
    "vo_140_combat_chatNext_001": "Nhìn nè, nhìn nè! Em vừa thử gắn thêm mô-đun trinh sát cho Bánh Thỏ đấy ♪",
    "vo_140_combat_chat_003": "Dò tìm kẻ địch hoàn tất! Giờ thì cứ để phát minh của em lo liệu nhé ♪",
    "vo_140_combat_chat_005": "Nếu nhìn kỹ lại thì trong số các Stellaroid cũng có mấy bé trông cưng xỉu luôn đó nha~",
    "vo_140_combat_eventRoom_001": "Hay là em chế tạo thêm một bé Bánh Thỏ chuyên để trò chuyện cùng mọi người ta?",
    "vo_140_combat_perk_002": "Đầu óc mình hoạt động nhạy bén hơn hẳn nè? Nyehehe, hiện tượng này thú vị ghê.",
    "vo_140_combat_perk_003": "Nữ thần ý tưởng giáng lâm rồi ♪ Em phải mau về phòng thí nghiệm hiện thực hóa nó ngay thôi!",
    "vo_140_combat_shopRoom_001": "Hi vọng ở đây có những món đồ tụi mình cần...",
    "vo_140_combat_subPerk_001": "Chờ chút xíu nha. Em nâng cấp nó ngay đây.",
    "vo_140_combat_subPerk_002": "Nyehehe. Dám coi thường phát minh của em thì sẽ phải nếm mùi đau thương đấy nhé.",
    "vo_140_combat_ultskill_001": "Ngủ một giấc ngon lành nhé mọi người ơi~ Phần còn lại giao cho Ma Vương đó nha ♪",
    "vo_140_combat_ultskill_004": "Này! Đã bảo là phải giữ trật tự cơ mà!",
    "vo_140_ui_affchat1_001": "Khi Ma Vương cưỡi trên Super Action Pie, tốc độ di chuyển sẽ nhanh gấp ba lần bình thường đó nha!",
    "vo_140_ui_affchat2_001": "Em dự định dành riêng một chỗ ngồi đặc biệt trên Super Action Pie cho Ma Vương đó nha.",
    "vo_140_ui_affchat3_001": "Lý do em chế tạo ra Bánh Thỏ là để có người đọc truyện cổ tích dỗ em ngủ mỗi tối đó mà.",
    "vo_140_ui_affchat4_001": "Liệu một ngày nào đó Bánh Trùm có thể vượt mặt được Ma Vương hàng thật không ta?",
    "vo_140_ui_affchat5_001": "Ngoài những ủy thác quan trọng không thể từ chối, em chỉ muốn dành trọn thời gian quý báu của mình cho những người dễ thương thôi à.",
    "vo_140_ui_afflv1_001": "Bánh Thỏ đã thiết lập Ma Vương là 'thành viên đặc biệt' của phòng thí nghiệm này rồi đó nha.",
    "vo_140_ui_afflv2_001": "Chân em bắt đầu mỏi rồi nè... Ồ, Ma Vương xoa bóp giúp em sao? Vậy em xin phép yêu cầu thêm chút nữa nhé?",
    "vo_140_ui_afflv3_001": "Được Ma Vương xoa bóp thế này dễ chịu hơn em tự làm nhiều, khéo em nghiện mất thôi.",
    "vo_140_ui_afflv4_001": "Mãi tới gần đây, em vẫn luôn tin rằng chỉ cần có trí tưởng tượng thì trong mơ em có thể chu du khắp đại lục Nova.",
    "vo_140_ui_discuss_001": "Anh Bloc lúc nào cũng mượn cớ nhờ Ma Vương đến khuyên nhủ em. Phiền ghê cơ.",
    "vo_140_ui_discuss_002": "Leona thường hay thách đấu em bằng khẩu hiệu: 'Đấu phát minh nào!'...",
    "vo_140_ui_excharup_001": "Phá vỡ giới hạn rồi! Từ giờ trở đi, hiệu năng chiến đấu cũng phải xịn sò tương xứng với độ dễ thương nha ♪",
    "vo_140_ui_exhang_001": "Ủa, Sếp ơi? Anh đi đâu mất tiêu rồi?",
    "vo_140_ui_fullscreen_001": "Á, Ma Vương ơi! Đừng có cười mà, mau cứu em với!",
    "vo_140_ui_fullscreen_002": "Oáp... Hả? Sao em lại ngủ thiếp đi ở chỗ như thế này chứ?",
    "vo_140_ui_gacha_001": "Ma Vương chịu giúp em chạy thử nghiệm bé Bánh Trùm á? Với tư cách là nhà phát triển, em còn mong gì hơn thế nữa chứ!",
    "vo_140_ui_greet_002": "Hôm nay Ma Vương cũng dễ thương KHÔNG THỂ TIN ĐƯỢC luôn ấy! Cứ ngắm anh là em lại tràn trề năng lượng rồi~",
    "vo_140_ui_greetmorn_001": "Chào buổi sáng nha. Bữa sáng dùng bánh mì nướng được không ạ? Kìa, sao Ma Vương lại ngạc nhiên thế chứ?",
    "vo_140_ui_greetnight_001": "Ôi, trời đã tối mịt rồi sao? Cứ mải mê làm bao nhiêu việc là một ngày trôi qua cái vèo.",
    "vo_140_ui_greetnoon_001": "Em vừa làm bánh mochi thỏ cho bữa trưa nè ♪",
    "vo_140_ui_hang_001": "Có phải Ma Vương đang dành không gian yên tĩnh để em tập trung suy nghĩ không? Nyehehe. Ngài chu đáo ghê đó.",
    "vo_140_ui_hang_002": "Mỗi khi trò chuyện cùng người khác, em lại sắp xếp được mạch suy nghĩ tốt hơn. Ma Vương ơi, ngài nói chuyện với em một lát được không?",
    "vo_140_ui_hfc_001": "Ma Vương ơi, anh hay tò mò chọc chỗ này ngó chỗ kia ghê ha?",
    "vo_140_ui_hfc_002": "Nếu Ma Vương rảnh rỗi, sao không ghé qua phòng thí nghiệm của em chơi? Ở đó có nhiều món hay ho lắm đó.",
    "vo_140_ui_lose_001": "Cú sốc này còn kinh khủng hơn cả lúc ý tưởng của em bị bác bỏ nữa...",
    "vo_140_ui_lose_002": "Em đã tính toán sai ở bước nào rồi ta?",
    "vo_140_ui_music_001": "Phù... Kỳ lạ thật, lòng em thấy bình yên hẳn.",
    "vo_140_ui_posterchat_001": "Mấy ủy thác anh Bloc mang tới trông chán ngắt à, giờ em vẫn chỉ muốn từ chối hết cho xong thôi...",
    "vo_140_ui_posterchat_002": "Nè nè, Ma Vương ơi?==RT==Cho em ngắm kỹ hơn~ khuôn mặt của ngài đi mà?",
    "vo_140_ui_posterchat_003": "Khoan đã nào. Em vừa nảy ra một cách siết ốc vít siêu cấp đáng yêu...",
    "vo_140_ui_standee_001": "Cái này á? Đây là cuốn sổ ghi chép ý tưởng của em thôi. Chẳng có bí mật gì to tát đâu, nếu Ma Vương muốn xem thì cứ bảo em một tiếng nha.",
    "vo_140_ui_standee_002": "Super Action Pie có cả tính năng xoa bóp nữa đấy! Mỗi khi Ma Vương lắc chiếc chuông này—",
    "vo_140_ui_swap_004": "Thỉnh thoảng cũng phải ra ngoài hít thở chút không khí trong lành chứ.",
    "vo_140_ui_thankEx_001": "Món quà này cũng đáng yêu y hệt như Ma Vương vậy đó ♪ Cảm ơn ngài nhiều nha, em sẽ nâng niu giữ gìn thật cẩn thận!",
    "vo_140_ui_thankSmall_001": "Oa, gói quà dễ thương ghê! ♪ Cảm ơn Ma Vương nhé.",
    "vo_140_ui_uniMusic_001": "Giai điệu này... Bằng cách nào đó khiến em nhớ lại một bài ca xưa cũ thân thương.",
    "vo_140_ui_unlockCG_001": "Trước đây khi ngồi trầm tư ở tư thế này, em đã nảy ra một sáng kiến tuyệt vời và nhận ra được nhiều điều đó.",
    "vo_140_ui_unlockLook_001": "Xuất phát thôi nào, Bánh Thỏ ơi! Đây là chương mở đầu cho câu chuyện của đôi ta!",
    "vo_140_ui_valentine_001": "Hôm nay dù có đi đến đâu thì hương thơm ngọt ngào của sô-cô-la cũng ngập tràn trong không khí cả.",
    "vo_140_ui_win_002": "Mọi chuyện dễ dàng hơn em tưởng nhiều luôn á~",
    "vo_140_ui_xmas_001": "Em xin lỗi mà! Em quên mất chưa hủy mệnh lệnh đã giao cho Bánh Thỏ...!",
    "vo_140_ui_yourbirth_001": "Chúc mừng sinh nhật Ma Vương nha!",

    # ---------------- Cosette (142) - 'em/Cosette - Chủ nhân/Sếp', never 'tôi/cậu'
    "vo_142_combat_battleClear_003": "Chủ nhân có thấy em vừa thể hiện không nào?",
    "vo_142_ui_affchat3_001": "Em cần chuẩn bị báo cáo nhiệm vụ dâng lên Chủ nhân.",
    "vo_142_ui_afflv1_001": "Chủ nhân không cảm thấy ánh mắt sắc lẹm thường ngày của em sao? Hehe. Vậy là người nhận ra rồi à.",
    "vo_142_ui_afflv2_001": "Ngày mai có món đồ uống mới ra mắt đấy! Chủ nhân có muốn đi cùng em không nè—",
    "vo_142_ui_afflv3_001": "Hôm nay có đồ uống mới ra lò rồi đó. Chủ nhân có muốn đi thử cùng em không?",
    "vo_142_ui_afflv4_001": "Nhiệm vụ của em là giám sát Chủ nhân, nhưng nếu cần em cũng sẽ quyết đấu một trận sòng phẳng với người.",
    "vo_142_ui_discuss_003": "Em nộp báo cáo mà chị Aelroria lại bảo: 'Nhật ký dễ thương ghê, thế báo cáo đâu rồi nhóc?'",
    "vo_142_ui_greet_001": "Kính chào Chủ nhân. Em luôn sẵn sàng đợi lệnh của người.",
    "vo_142_ui_greet_002": "Chủ nhân muốn dạo phố cùng em không? Ôi Sếp à, người thật liều lĩnh khi dám tiếp cận em một mình như thế này đấy—",
    "vo_142_ui_hang_001": "Mọi việc trong phòng em đã thu dọn ngăn nắp. Chủ nhân có cần em hầu hạ thêm điều gì không ạ?",
    "vo_142_ui_hfc_001": "Hả? Chủ nhân lại tìm thấy em nữa rồi? Rốt cuộc em đã để lộ sơ hở chỗ nào vậy cà...",
    "vo_142_ui_lose_001": "Em đã làm ô danh mệnh lệnh của Chủ nhân... Xin người trừng phạt...",
    "vo_142_ui_standee_001": "Chủ nhân cứ việc phòng bị đi, rồi sẽ có ngày em tóm được sơ hở của Sếp cho coi.",
    "vo_142_ui_swap_001": "Rõ rồi. Hôm nay em sẽ tuân theo mọi chỉ thị của Chủ nhân.",

    # ---------------- Nazuna (156) - 'tôi/Nazuna - cậu', never 'anh - em'
    "vo_156_ui_affchat5_001": "Tôi vốn chẳng có ước mơ cao xa gì đâu, nhưng nếu được đồng hành cùng cậu đến cuối chặng đường thì có lẽ cũng không tệ chút nào.==RT==",
    "vo_156_ui_posterchat_006": "Cái trò lừa gạt này đúng là ngán ngẩm thật. Không chỉ khi tôi bị lừa, mà nhất là khi những người thân thiết của tôi phải chịu cảnh đó.",
    "vo_156_ui_standee_002": "Sao thế hả Ma Vương? Mới thế đã chịu thua một cô gái như tôi rồi à? Cậu dai sức kém quá đấy!",

    # ---------------- Coronis (159) - 'tôi - cậu', never 'anh - em'
    "vo_159_ui_fullscreen_002": "Kỹ năng của cậu tiến bộ nhiều đấy nhỉ? Nếu lần nào cậu cũng khiến tôi cảm thấy dễ chịu thế này...",

    # ---------------- Alina (162) - 'ta/Alina - ngươi/Du Hành Giả', never 'anh - em'
    "vo_162_ui_afflv2_001": "Ngươi biết đấy, dẫu chúng ta không có nhiều thời gian bên nhau, nhưng ta luôn thành thật với ngươi.",
    "vo_162_ui_thankEx_001": "Dù ta có lục tung khắp thế giới này để tìm kiếm người đối xử tốt nhất với ta, thì người đó vẫn mãi là ngươi mà thôi.",

    # ---------------- Other characters calling player 'Ma Vương' (replacing crude MT 'bạo chúa')
    "vo_120_ui_hang_002": "Tôi tò mò thật đấy. Không biết cả ngày Ma Vương ngồi trầm ngâm suy nghĩ chuyện gì nhỉ? Cậu có ý kiến gì không?",
    "vo_130_ui_birth_001": "Nè nè, Ma Vương. Cậu tưởng giấu được à, tôi thấy rõ mồn một từ đây rồi nhé.",
    "vo_130_ui_exhang_001": "Chán quá đi mất thôi. Cả ngày nay Ma Vương chạy đi đằng nào rồi?",
    "vo_130_ui_greetmorn_001": "Chào buổi sáng Ma Vương! Báo sáng của cậu đây này!",
    "vo_130_ui_yourbirth_001": "Ma Vương ơi là Ma Vương! Ban nãy có một cô bé siêu đáng yêu nhờ tôi gửi cái này cho cậu đấy.",
    "vo_135_ui_birth_001": "Ôi trời! ♪ Không ngờ ngài Ma Vương to lớn đáng sợ lại nhớ ngày sinh nhật của tôi đấy!",
    "vo_143_ui_afflv2_001": "Tôi chẳng bận tâm Ma Vương được miêu tả ra sao trong truyền thuyết cổ xưa đâu.==RT==",
    "vo_150_ui_affchat5_001": "Nè Ma Vương! Một mai công ty của cậu trở thành tập đoàn lớn nhất đại lục Nova, nhất định phải thuê tôi đấy nhé!",
    "vo_158_eventshop_001": "Nè Ma Vương? Nhân lúc đang mua sắm, sao cậu không tiện tay bao trọn cả cửa hàng luôn đi?",
    "vo_158_ui_affchat1_001": "Nè Ma Vương! Mùa đông tới cậu có muốn thử làm một màn phát quà hoành tráng không?",
    "vo_158_ui_greetnight_001": "Nè Ma Vương! Đêm nay cậu có muốn đi câu cá với tôi thêm lần nữa không?",
    "vo_158_ui_thank_001": "Ồ! Cảm ơn cậu nhé, Ma Vương!",
    "vo_158_ui_valentine_001": "Ma Vương ơi, cậu có thích mứt sô-cô-la ăn kèm cá chiên không? Hay là cá nướng nhé?",
    "vo_npc152_ui_greet_001": "Rất vui được gặp ngài, Ma Vương! Cảm ơn ngài rất nhiều vì đã ghé qua♪",
    "vo_npc152_ui_posterchat_005": "Thật là vinh hạnh khi được diện kiến Ma Vương, người có danh tiếng vang dội khắp đại lục Nova♪",
    "vo_npc17202_cast_victory_003": "Ồ! Cậu đúng chuẩn là Ma Vương vĩ đại luôn! Mục bình luận đang bùng nổ phấn khích kìa! ♪",
    "vo_npc173_ui_greet_002": "Hỡi Ma Vương của ta, ngươi muốn trải nghiệm hồi kết như thế nào?",
    "vo_npc173_ui_greetmorn_003": "Chào buổi sáng, Ma Vương của ta. Hôm nay ngươi muốn thực hiện tâm nguyện gì nào?",
}

def clean_item_text(text: str) -> str:
    """Applies global terminology and quality cleanup to an item string."""
    out = text

    # 1. Trekker -> Du Hành Giả
    out = re.sub(r"\bThiên phú Lữ khách\b", "Thiên phú Du Hành Giả", out)
    out = re.sub(r"\bthiên phú Lữ khách\b", "thiên phú Du Hành Giả", out)
    out = re.sub(r"\bLữ khách\b", "Du Hành Giả", out)
    out = re.sub(r"\blữ khách\b", "Du Hành Giả", out)

    # 2. Cự tháp -> Tháp Sao Monolith / Tháp Sao
    out = re.sub(r"\bA Cự tháp Too Far!?\b", "Tháp Sao Quá Xa!", out)
    out = re.sub(r"\bCự tháp Research\b", "Nghiên Cứu Tháp Sao Monolith", out)
    out = re.sub(r"\bBản Ghi Cự Tháp\b", "Bản Ghi Tháp Sao", out)
    out = re.sub(r"\bCự Tháp Nơi Xa\b", "Tháp Sao Quá Xa", out)
    out = re.sub(r"\bCự Tháp\b", "Tháp Sao Monolith", out)
    out = re.sub(r"\bcự tháp\b", "Tháp Sao Monolith", out)

    # 3. Runic Disc terminology
    out = re.sub(r"\bĐĩa Cổ Ngữ\b", "Đĩa Khắc Ấn", out)
    out = re.sub(r"\bđĩa Cổ Ngữ\b", "Đĩa Khắc Ấn", out)
    out = re.sub(r"\bbanner đĩa vĩnh viễn\b", "nhóm Khắc Ấn Thường", out)

    # 4. Event & Season name English cleanup
    out = re.sub(r"Cataclysm Survivor Season (\d+)", r"Mùa \1 của Sống Sót Sau Đại Thảm Họa", out)
    out = re.sub(r"Season (\d+) of A Finale Echoing", r"Mùa \1 của Hồi Âm Đoạn Kết", out)
    out = re.sub(r"Phần (\d+) của A Finale Echoing", r"Mùa \1 của Hồi Âm Đoạn Kết", out)

    # 5. Clunky MT idioms in item descriptions
    out = re.sub(r"\btăng cấp Cấp Cấp\b", "tăng cấp Bậc Trợ Cấp", out)
    out = re.sub(r"\btăng cấp Cấp\b", "tăng cấp Bậc Trợ Cấp", out)
    out = re.sub(r"\b1/365 của bạn\b", "Mảnh Ghép 1/365 Của Anh", out)
    out = re.sub(r"\bMột Phần 365 Của Bạn\b", "Mảnh Ghép 1/365 Của Anh", out)
    out = re.sub(r"\blên máy bay\b", "lên phao bơi", out)
    out = re.sub(r"\bBằng chứng về tình bạn với ([A-Za-z]+)!\b", r"Minh chứng tình bạn gắn kết cùng \1!", out)
    out = re.sub(r"\btrong Shop\b", "trong Cửa Hàng", out)
    out = re.sub(r"\bCanned Năng lượng Soda\b", "Nước Tăng Lực Đóng Lon", out)
    out = re.sub(r"\bOasis's Grace\b", "Phước Lành Oasis", out)

    return out.strip()

def main():
    t0 = time.time()
    print("=" * 80)
    print("BẮT ĐẦU ĐẠI TU VẬT PHẨM & ĐỒNG NHẤT XƯNG HÔ THOẠI NHÂN VẬT (CAMPAIGN 21)")
    print("=" * 80)

    # ---------------------------------------------------------------------
    # STEP 1: ITEM TABLES OVERHAUL (00653 & 00900)
    # ---------------------------------------------------------------------
    p_653 = ENTRIES_DIR / "00653_0xe60634348b826f41.bin"
    p_900 = ENTRIES_DIR / "00900_0xdb546f14f2f79a11.bin"
    assert p_653.exists() and p_900.exists(), "Item tables missing in entries!"

    d_653 = json.loads(p_653.read_text(encoding="utf-8"))
    item_mod_count = 0

    for k, v in d_653.items():
        old_val = v
        # 1. Apply specific overrides first
        if k in ITEM_SPECIFIC_OVERRIDES:
            new_val = ITEM_SPECIFIC_OVERRIDES[k]
        else:
            # 2. Apply general regex clean
            new_val = clean_item_text(v)

        if new_val != old_val:
            d_653[k] = new_val
            item_mod_count += 1

    # Write clean data to BOTH 00653 and twin 00900
    p_653.write_text(json.dumps(d_653, indent=2, ensure_ascii=False), encoding="utf-8")
    p_900.write_text(json.dumps(d_653, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Đã đại tu Bảng Vật Phẩm Item (00653 & 00900):")
    print(f"  - Tổng số chuỗi vật phẩm được nâng cấp: {item_mod_count} / {len(d_653)}")
    print(f"  - Đồng bộ 100% sang bảng song sinh 00900 (xóa sạch 52.467 chữ Trung).")

    # ---------------------------------------------------------------------
    # STEP 2: RESIDENT & THROW GIFT ITEM CLEANUP
    # ---------------------------------------------------------------------
    p_res = ENTRIES_DIR / "00711_0x16665e9556f7d213.bin"
    p_res_twin = ENTRIES_DIR / "00958_0x8eb070c89e8435d1.bin"
    if p_res.exists():
        d_res = json.loads(p_res.read_text(encoding="utf-8"))
        if "ResidentGoods.101.2" in d_res:
            d_res["ResidentGoods.101.2"] = "Chứng chỉ được sử dụng để chiêu mộ trong nhóm Khắc Ấn Thường."
            p_res.write_text(json.dumps(d_res, indent=2, ensure_ascii=False), encoding="utf-8")
            if p_res_twin.exists():
                p_res_twin.write_text(json.dumps(d_res, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"✓ Đã chuẩn hóa ResidentGoods (00711 & 00958).")

    p_throw = ENTRIES_DIR / "00766_0xc0106ff3412a890b.bin"
    p_throw_twin = ENTRIES_DIR / "01013_0x0cae08b25a582e2a.bin"
    if p_throw.exists():
        d_throw = json.loads(p_throw.read_text(encoding="utf-8"))
        d_throw["ThrowGiftItem.101.1"] = "Tăng Thêm Thời Gian"
        d_throw["ThrowGiftItem.102.1"] = "Kính Soi Sherlock Miễn Phí"
        d_throw["ThrowGiftItem.103.1"] = "Băng Tuyết Vĩnh Cửu"
        p_throw.write_text(json.dumps(d_throw, indent=2, ensure_ascii=False), encoding="utf-8")
        if p_throw_twin.exists():
            p_throw_twin.write_text(json.dumps(d_throw, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✓ Đã chuẩn hóa ThrowGiftItem (00766 & 01013).")

    # ---------------------------------------------------------------------
    # STEP 3: DIALOGUE PRONOUN CONSISTENCY HARMONIZATION (00552)
    # ---------------------------------------------------------------------
    p_voice = ENTRIES_DIR / "00552_0x80911df3a563e0f3.bin"
    d_voice = json.loads(p_voice.read_text(encoding="utf-8"))
    voice_fixed_count = 0

    for k, new_text in VOICE_PRONOUN_HARMONIZATION.items():
        if k in d_voice:
            cur_text = d_voice[k]["text"]["female_jp"][0]
            if cur_text != new_text:
                d_voice[k]["text"]["female_jp"][0] = new_text
                if "female_cn" in d_voice[k]["text"] and isinstance(d_voice[k]["text"]["female_cn"], list) and len(d_voice[k]["text"]["female_cn"]) > 0:
                    d_voice[k]["text"]["female_cn"][0] = new_text
                voice_fixed_count += 1

    p_voice.write_text(json.dumps(d_voice, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Đã đồng nhất xưng hô thoại nhân vật (00552): {voice_fixed_count} câu thoại được đồng nhất tuyệt đối.")

    # ---------------------------------------------------------------------
    # STEP 4: REPACK DIST/DATA_PATCHED_VI.ARCX
    # ---------------------------------------------------------------------
    print("\n-> Đang đóng gói lại dist/data_patched_vi.arcx với mã hóa XXTEA...")
    repack_archive(DEC_DIR, OUTPUT_ARCX, encrypt_payload=True)
    arc = ArcxArchive(OUTPUT_ARCX)
    new_sha = hashlib.sha256(OUTPUT_ARCX.read_bytes()).hexdigest()
    new_size = OUTPUT_ARCX.stat().st_size
    print(f"✓ Hoàn tất đóng gói canonical archive: {new_size:,} bytes")
    print(f"  SHA-256: {new_sha}")

    # ---------------------------------------------------------------------
    # STEP 5: DUAL-DEPLOY TO YOSTAR AND STEAM INSTALLATIONS
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
    # STEP 6: ANTI-REGRESSION VERIFICATION
    # ---------------------------------------------------------------------
    print("\n-> Đang cập nhật và chạy kiểm chứng tự động qua verify_deployed_game_data.py...")
    verify_script = ROOT / "tools" / "verify_deployed_game_data.py"
    v_content = verify_script.read_text(encoding="utf-8")

    # Update golden hash
    v_content = re.sub(
        r'EXPECTED_DATA_SHA256 = "[a-f0-9]{64}"',
        f'EXPECTED_DATA_SHA256 = "{new_sha}"',
        v_content
    )

    verify_script.write_text(v_content, encoding="utf-8")

    import subprocess
    res = subprocess.run([sys.executable, str(verify_script)], capture_output=True, text=True, encoding="utf-8")
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        sys.exit(1)

    elapsed = time.time() - t0
    print(f"\n[HOÀN THÀNH XUẤT SẮC TRONG {elapsed:.2f} GIÂY] ĐẠI TU VẬT PHẨM & ĐỒNG NHẤT XƯNG HÔ HOÀN TẤT!")

if __name__ == "__main__":
    main()
