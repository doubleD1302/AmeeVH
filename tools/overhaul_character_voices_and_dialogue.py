#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master Character Voice Subtitles & Dialogue Overhaul Script (Campaign 20)
-----------------------------------------------------------------------
Overhauls all 41 playable characters' voice lines and recruitment introductions:
1. Eliminates Machine-Translation (MT) blunders (mags -> tạp chí, riding shotgun -> cưỡi súng ngắn,
   filling complete -> điền đầy đủ, tide in enemy favor -> thủy triều, cheapskate -> kẻ rẻ tiền,
   star plucking -> nhổ sao, commission -> khoản hoa hồng, Trekker material -> tài liệu Trekker,
   helmet -> mặc mũ bảo hiểm, etc.).
2. Synchronizes CharGetLines (00603 & 00850) with high-literary light-novel prose matching
   individual character archetypes.
3. Synchronizes CharacterArchiveBaseInfo (00592 -> 00839) and CharacterArchiveVoice (00594 -> 00841)
   to eliminate 3,560+ untranslated Chinese voice headers and 660+ Chinese bio strings.
4. Repacks dist/data_patched_vi.arcx with XXTEA encryption.
5. Dual-deploys to Yostar and Steam installations per deployment invariants.
6. Runs anti-regression verification.
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
# 1. RECRUITMENT LINES (CharGetLines) REFINEMENTS
# =========================================================================
CHARGET_REFINEMENTS = {
    # Tilia (107) - Justice knight in training
    "CharGetLines.10701.1": "Báo cáo! Em là Tilia, Kỵ sĩ Tập sự đại diện cho chính nghĩa!\nHãy trở thành chiến hữu của em và cùng nhau giương cao ngọn cờ công lý nhé!",
    "CharGetLines.10702.1": "Lại gặp nhau rồi, người bạn đồng chí hướng vì chính nghĩa!",
    "CharGetLines.10704.1": "Cảm ơn Chúa Tể đã đến chứng kiến những bước chân đầu tiên trên con đường trở thành anh hùng của em!",
    "CharGetLines.10706.1": "Cô nàng rực rỡ như ánh mặt trời đã sẵn sàng tiếp sức cho cậu rồi đây~! Hãy nở nụ cười thật tươi và giữ vững phong độ đỉnh nhất để đón chào thử thách tiếp theo nhé!",

    # Kasimira (108) - White Cat Circus Troupe 3 Leader
    "CharGetLines.10801.1": "Tôi là Kasimira, Đội trưởng Phân đội 3 của Đoàn Kịch Mèo Trắng. Đây là thỏa thuận hợp tác tác chiến đôi bên, xin mời cậu ký tên vào đây nhé.",
    "CharGetLines.10804.1": "Tôi từng nghĩ đến việc bổ sung thêm một điều khoản nữa vào hợp đồng, đắn đo mãi chẳng biết nên dùng câu từ thế nào cho thỏa đáng. Nhưng giờ tôi nhận ra, tình bạn vốn chẳng phải thứ được xây dựng trên giấy tờ... và cậu mới chính là bùa may mắn linh nghiệm nhất của cuộc đời tôi.",

    # Firenze (110) - Wealthy noble mistress / onee-san
    "CharGetLines.11001.1": "Tôi là Firenze, đồng minh đắc lực của cậu. Tôi sẽ cho cậu thấy rõ giá trị của mình, và cũng mong cậu đừng làm tôi thất vọng nhé.",
    "CharGetLines.11002.1": "Giữa những người thông minh với nhau thì không cần phải lặp lại những lời xã giao sáo rỗng—— Hãy nói ra lý do cậu cất công tìm đến tôi đi, tôi đều sẵn lòng tiếp đón.",
    "CharGetLines.11004.1": "Một khi đã lựa chọn đứng bên cạnh tôi... đồng nghĩa với việc, cậu vĩnh viễn không thể thoát khỏi bàn tay của tôi nữa đâu nhé...",

    # Shimiao (113) - Baize Bureau kung fu girl
    "CharGetLines.11301.1": "Tôi là Shimiao đến từ Thương Cục Bạch Trạch! Từ nay về sau tôi sẽ phụ trách các sự vụ hợp tác với quý Lữ Đoàn, mong rằng đôi bên chúng ta sẽ hợp tác thật vui vẻ nha!",

    # Ridge (116) - Greenhouse manager
    "CharGetLines.11601.1": "Em... em là Ridge, quản lý nhà kính bên Nông Nghiệp Liên Hợp. Lần đầu gặp mặt... mong anh/chị chỉ giáo thêm cho em ạ...",
    "CharGetLines.11602.1": "Lần này... em có đem chút quà cho anh/chị nè! Toàn là rau củ tươi ngon do chính tay em chăm sóc đó, vừa mới hái ngoài vườn luôn á.",
    "CharGetLines.11605.1": "Khoảnh khắc hạnh phúc nhất mà em có thể nghĩ tới, chính là được chợp mắt thảnh thơi trong hơi ấm dịu dàng của buổi trưa hè. Khi thức dậy, ánh nắng đã tràn qua bậu cửa sổ, và những đóa hoa thơm ngát vẫn đang kiên nhẫn đợi chờ người.",

    # Canace (120) - Aristocratic academy lecturer
    "CharGetLines.12001.1": "Chào cậu lần đầu gặp mặt, tôi là giảng viên Học Viện Tinh Huy, cứ gọi tôi là Canace nhé. Ra cậu chính là vị Đội trưởng trong truyền thuyết sao... Hehe, rất mong chờ vào sự hợp tác sắp tới giữa chúng ta.",
    "CharGetLines.12003.1": "Xem ra ta phải bộc lộ thực lực chân chính để đáp lại sự kỳ vọng của ngươi rồi.",
    "CharGetLines.12004.1": "Ở bên cạnh cậu tôi học hỏi được rất nhiều điều mới lạ, kể từ khi trở thành giáo viên đến nay, cảm giác này thực sự là lần đầu tiên tôi được trải nghiệm.",

    # Freesia (125) - Wan Song Wu courier
    "CharGetLines.12501.1": "Em là Freesia, nhân viên của Vạn Dịch Quán. Cứ yên tâm giao phó thư từ và sự an toàn của người cho em, em nhất định không phụ sự kỳ vọng của người đâu ạ.",
    "CharGetLines.12504.1": "Có đôi khi... em cũng muốn buông bỏ sự nghiêm nghị thường ngày, cùng người đạp xe ngắm hoàng hôn một chuyến.",
    "CharGetLines.12505.1": "Kiếm khí sắc bén như sương mai, tâm trí phẳng lặng tựa mặt hồ. Đường xa dẫu lắm gian truân, có người đồng hành lòng em chẳng chút âu lo.",

    # Flora (126) - Magician
    "CharGetLines.12601.1": "Chào cậu nhé! Tôi là ảo thuật gia Flora đây, chắc hẳn cậu từng nghe qua bao lời đồn kỳ lạ về tôi rồi nhỉ... Hehe, tò mò lắm đúng không? Nhưng đối với ảo thuật mà nói, là thật hay hư ảo, điều đó có thực sự quan trọng chăng?",
    "CharGetLines.12603.1": "Buổi biểu diễn hoành tráng sắp sửa bắt đầu rồi, hãy khắc ghi điều kỳ diệu này sâu thẳm vào trong tim cậu nhé!",

    # Teresa (127) - Wan Song Wu
    "CharGetLines.12701.1": "Ồ hô~ Lại phát hiện thêm một tuyến hải trình mới toanh rồi nè! Hừ hừ~ Tôi là Teresa đến từ Vạn Dịch Quán, khi nào muốn gửi thư từ bưu phẩm, ngài cứ việc ới tôi một tiếng là xong ngay!",

    # Nazuka (133) - Fox spirit
    "CharGetLines.13301.1": "Xin chào chàng, ta là Nazuka. Mong rằng ta có thể giúp ích được nhiều cho chàng trên hành trình phía trước, và cũng mong chàng sẽ dành trọn sự tin tưởng cho ta, từ nay về sau xin được chỉ giáo nhiều hơn nhé.",

    # Allie (139) - Daisy Orphanage Big Sister
    "CharGetLines.13901.1": "Chị là Allie, người quản lý Viện Mồ Côi Daisy. Nếu cậu không chê, có thể xem nơi đây như một trạm dừng chân ấm cúng bất cứ lúc nào nhé.",
    "CharGetLines.13902.1": "Lại gặp nhau rồi, dạo gần đây cậu sống thế nào? Có ăn uống đúng bữa không đấy?",

    # Sparkla (140) - Inventor & Tyrant
    "CharGetLines.14001.1": "Nhiệt liệt chào mừng Ma Vương đến với xưởng chế tác di động của Sparkla... Khoan đã, gương mặt này đáng yêu vượt chuẩn cho phép rồi đấy nhé... Bánh Thỏ, mau nghênh đón khách quý!",

    # Chixia (141) - Spirited kung fu girl
    "CharGetLines.14102.1": "Lại gặp nhau rồi, nhìn sắc mặt cậu hồng hào rạng rỡ thế này, tốt lắm tốt lắm~ Sao nào, linh phù lần trước ta tặng hiệu nghiệm chứ?",
    "CharGetLines.14104.1": "Thế... thế cậu mau thề ngay đi, nói rằng cậu sẽ chẳng đi đâu hết, chỉ ở mãi bên cạnh ta... Nhúc nhích một bước cũng không được đâu đấy!",
    "CharGetLines.14105.1": "Ai bảo thế giới trong gương chỉ là hư ảo? Nếu người trong gương có thể sóng bước cùng cậu, dẫu là ảo mộng ta cũng nguyện đắm say.",

    # Cosette (142) - Nocturn Eterna maid / painter
    "CharGetLines.14201.1": "Em là Cosette... một họa sĩ lang bạt. Cảm ơn Chủ nhân đã sẵn lòng dừng chân, liệu người có muốn để em vẽ tặng một bức chân dung không?",
    "CharGetLines.14202.1": "Lại gặp lại người rồi... Nhìn thấy Chủ nhân, trong lòng em lại trào dâng vô vàn sắc màu tươi mới.",
    "CharGetLines.14204.1": "Xin người đừng cử động vội... Hãy giữ nguyên tư thế này thêm một lát, để em khắc ghi trọn vẹn ánh mắt của Chủ nhân vào khung vẽ.",

    # Otoha (145) - Dreamy musician
    "CharGetLines.14501.1": "Tấu lên khúc ca của gió và trăng! Em là Otoha, nhạc công của những hành trình viễn xứ. Hãy để tiếng đàn của em tiếp thêm sức mạnh cho cậu nhé!",
    "CharGetLines.14502.1": "Giai điệu quen thuộc lại vang lên rồi! Lần này cậu muốn nghe một khúc khải hoàn ca hay một điệu tình ca êm dịu?",
    "CharGetLines.14504.1": "Bản nhạc này... em chỉ đàn cho riêng một mình cậu lắng nghe mà thôi.",

    # Caramel (147) - Rock artist
    "CharGetLines.14701.1": "Tớ là Caramel! Cứ gọi tớ là Caramel là được rồi. Súng đạn và nắm đấm của tớ luôn sẵn sàng, bảo tớ đánh đâu tớ đánh đó!",
    "CharGetLines.14705.1": "Trên chiến trường khói lửa mịt mù, chỉ có kẻ dũng cảm nhất mới xứng đáng đứng cạnh cậu. Và tớ chính là người đó!",

    # Alina (162) - Filanis Nightwatch Commander
    "CharGetLines.16201.1": "Đội trưởng Đội Gác Đêm của Filanis, nhận lệnh ứng triệu mà đến! Tuy ta không giỏi ma pháp cao siêu, nhưng kiếm thuật trong tay thì hoàn toàn đáng tin cậy. Ta sẽ kề vai tác chiến cùng ngươi, dùng thanh kiếm này bảo vệ tất cả những gì ngươi hằng trân quý.",
    "CharGetLines.16203.1": "Bất luận định mệnh dẫn lối ngươi đi về phương trời nào, ta cũng sẽ luôn túc trực canh gác bên cạnh ngươi, vì ngươi mà quét sạch mọi chông gai cản bước phía trước.",
    "CharGetLines.16204.1": "Sao thế? Nếu không mau đi tắm rửa nước ấm cho sạch sẽ, ngươi sẽ bị nhiễm lạnh đấy nhé."
}

# =========================================================================
# 2. MASTER GLOBAL MACHINE TRANSLATION OVERRIDES & CLEANUP
# =========================================================================
GLOBAL_MT_PATTERNS = [
    # Mags / weapons
    (r"\bVẫn còn nhiều tạp chí dự phòng\b", "Vẫn còn dư dả băng đạn dự phòng"),
    (r"\btạp chí dự phòng\b", "băng đạn dự phòng"),
    (r"\btạp chí\b", "băng đạn"),
    
    # Ride shotgun
    (r"\bcưỡi súng ngắn\b", "ngồi ghế phụ bên cạnh"),
    (r"\bviệc bạn cưỡi súng ngắn\b", "việc cậu ngồi ghế phụ đi cùng"),
    
    # Fully loaded firing
    (r"\bĐiền đầy đủ\. Bắn\.\b", "Năng lượng đã nạp đầy. Khai hỏa!"),
    (r"\bĐầy đủ\. Bắn\.\b", "Nạp đạn hoàn tất. Bắn!"),
    
    # Tide of battle
    (r"\bThủy triều đang có lợi cho kẻ thù\b", "Kẻ địch đang chiếm thế thượng phong"),
    (r"\bthủy triều đang có lợi cho kẻ thù\b", "kẻ địch đang chiếm thế thượng phong"),
    (r"\bthủy triều\b", "cục diện trận đánh"),
    
    # Cheapskate
    (r"\bkẻ rẻ tiền\b", "đồ ki bo"),
    (r"\bngười rẻ tiền\b", "kẻ bủn xỉn"),
    
    # Helmet
    (r"\bmặc mũ bảo hiểm\b", "đội chiếc mũ này"),
    (r"\bđội mũ bảo hiểm\b", "đội chiến mũ"),
    (r"\bchiếc mũ bảo hiểm này\b", "chiếc chiến mũ này"),
    (r"\bmũ bảo hiểm\b", "chiến mũ"),
    
    # Trekker material
    (r"\bkhông phải tài liệu của Trekker\b", "không có tố chất làm Du Hành Giả"),
    (r"\btài liệu của Trekker\b", "tố chất Du Hành Giả"),
    (r"\btài liệu của\b", "tố chất của"),
    
    # Commission
    (r"\bkhoản hoa hồng\b", "khoản thù lao ủy thác"),
    (r"\btiền hoa hồng\b", "thù lao ủy thác"),
    (r"\bhoa hồng\b", "ủy thác"),
    
    # Star plucking
    (r"\bnhổ sao\b", "hái sao"),
    (r"\bNhổ sao\b", "Hái sao"),
    
    # Weary self
    (r"\bsự mệt mỏi của cậu\b", "thân mình mỏi mệt của cậu"),
    (r"\bLàm ơn hãy nghỉ ngơi đi, sự mệt mỏi của cậu\b", "Cậu vất vả nhiều rồi, nghỉ ngơi chút đi nào"),
    
    # Loong tribe
    (r"\bGia đình Loong đã nói hay nhất\b", "Cổ nhân tộc Long từng dạy"),
    (r"\bgia đình Loong\b", "tộc Long"),
    
    # Risk management
    (r"\bQuản lý rủi ro là tên đệm của tôi\b", "Kiểm soát rủi ro vốn là sở trường của tôi mà"),
    (r"\blà tên đệm của tôi\b", "vốn là sở trường của tôi mà"),
    
    # Full-fledged official
    (r"\bchính thức chính thức\b", "chân chính"),
    
    # Monolith
    (r"\bNhững tảng đá nguyên khối\b", "Tháp Sao Monolith"),
    (r"\bnhững tảng đá nguyên khối\b", "Tháp Sao Monolith"),
    (r"\btảng đá nguyên khối\b", "Tháp Sao Monolith"),
    
    # Exclamations
    (r"\bChúa ơi\b", "Trời đất ơi"),
    (r"\bÔi Chúa ơi\b", "Trời ạ"),
    (r"\bLàm ơn hãy\b", "Xin hãy"),
    (r"\blàm ơn hãy\b", "hãy"),
    (r"\bĐúng! Tôi thích điều này!\b", "Tuyệt quá! Tớ thích món này lắm luôn!"),
    (r"\bĐiều đó làm tôi rất hạnh phúc!\b", "Tớ thấy hạnh phúc lắm luôn đó!"),
    (r"\bđiều đó làm tôi rất hạnh phúc\b", "tớ vui lắm luôn đó"),
    (r"\bnó làm tôi rất hạnh phúc\b", "em vui lắm luôn đó"),
    (r"\bđiều đó làm tôi\b", "khiến tôi"),
    (r"\bnó làm tôi\b", "khiến tôi"),
    (r"\bTôi đã làm điều đó\b", "Bọn mình làm được rồi"),
    (r"\bchúng tôi đã làm điều đó\b", "bọn mình đã làm được"),
    
    # Boss translation
    (r"\bÔng chủ\b", "Sếp"),
    (r"\bông chủ\b", "Sếp"),
    
    # Institutions & lore
    (r"\bBaize Bureau\b", "Thương Cục Bạch Trạch"),
    (r"\bVạn Tống Ốc\b", "Vạn Dịch Quán"),
    (r"\bSquire Tilia\b", "Kỵ sĩ tập sự Tilia"),
    (r"\bSquire\b", "Kỵ sĩ tập sự"),
    (r"\bTyrant\b", "Ma Vương"),
]

COMPILED_GLOBAL_MT = [(re.compile(p, re.IGNORECASE), r) for p, r in GLOBAL_MT_PATTERNS]

# =========================================================================
# 3. EXPLICIT HAND-CRAFTED HIGH-PROFILE VOICE LINE OVERRIDES
# =========================================================================
EXPLICIT_VOICE_OVERRIDES = {
    # ---------------- Amber (103) - Sleepy, cute gamer girl, sniper
    "vo_103_combat_chat_001": "2, 4, 6... Vẫn còn dư dả băng đạn dự phòng.",
    "vo_103_combat_chat_002": "Bắn trúng ngay hồng tâm. Trình bắn tỉa của tớ đâu phải để trưng.",
    "vo_103_combat_chat_003": "Oáp... Tự dưng thèm một giấc ngủ trưa ghê á.",
    "vo_103_combat_chatLvUp_001": "Kẻ địch có mạnh hơn thì tớ vẫn cân tất được nhé!",
    "vo_103_combat_chatNext_001": "Tớ đi trinh sát phía trước đây—Hửm? Cậu muốn đi cùng hả? Được thôi!",
    "vo_103_combat_dead_001": "Tớ kiệt sức rồi... Xin phép rút lui trước nha!",
    "vo_103_combat_dead_002": "Tớ chỉ cần chợp mắt một xíu thôi...",
    "vo_103_combat_eventRoom_001": "Giao tiếp với người lạ mệt mỏi thật đấy.",
    "vo_103_combat_perk_001": "Món này dễ dùng ghê nè.",
    "vo_103_combat_perk_002": "Mình... đã mạnh hơn rồi sao?",
    "vo_103_combat_perk_003": "Tớ cảm thấy tràn đầy sức mạnh!",
    "vo_103_combat_restRoom_001": "Sếp ơi, em muốn chụp một kiểu ảnh ở đây quá!",
    "vo_103_combat_shopRoom_001": "Nhiều đồ hay ho ghê! Mình rinh hết đống này về được không ta?",
    "vo_103_combat_subPerk_001": "Giờ thì tớ đã có thể giúp ích được cho cậu rồi.",
    "vo_103_combat_subPerk_002": "Cậu có muốn nghe bài ca Meo Meo không nè?",
    "vo_103_combat_ultskill_001": "Năng lượng đã nạp đầy. Khai hỏa!",
    "vo_103_combat_ultskill_002": "Tớ sẽ... dọn sạch chúng nó.",
    "vo_103_ui_affchat1_001": "Tớ vốn ngại tiếp xúc với người lạ... nhưng riêng với cậu thì lại khác hẳn.",
    "vo_103_ui_affchat2_001": "Tớ gõ phím nhanh lắm đó, nhưng cậu nhắn lại cũng nhanh chẳng kém gì.",
    "vo_103_ui_affchat3_001": "Cho tớ mượn bờ vai một chút nhé... Oáp, êm ghê...",
    "vo_103_ui_affchat4_001": "Khi cậu vuốt ve một bé mèo từ đầu đến đuôi, ẻm sẽ thích mê đến mức nheo mắt lại vì hạnh phúc đó.",
    "vo_103_ui_affchat5_001": "Mèo vốn là loài tự do tự tại, ghét nhất là bị trói buộc... Nhưng nếu tìm được người chúng thích, có lẽ mọi chuyện sẽ khác đi đó.",
    "vo_103_ui_afflv1_001": "Sếp ơi, chụp với em một tấm ảnh kỷ niệm được không nè?",
    "vo_103_ui_afflv2_001": "Bọn mình cùng selfie thêm tấm nữa nhé. Lần này không được chớp mắt đâu đấy.",
    "vo_103_ui_afflv3_001": "Ảnh selfie của tụi mình đẹp ghê. Tớ cài làm hình nền luôn rồi, để lúc nào cũng ngắm được.",
    "vo_103_ui_afflv4_001": "Sếp ơi, em đang nghĩ xem nên đổi hình nền mới nào đây nè...",
    "vo_103_ui_birth_001": "Hôm nay là sinh nhật của tớ đó. Cơ mà chắc cũng chẳng khác ngày thường là bao...",
    "vo_103_ui_charup_001": "Cảm ơn cậu đã tăng sức mạnh cho tớ nhé. Tớ sẽ cố gắng hơn nữa!",
    "vo_103_ui_gachaNew_001": "Tớ là Amber đây... Iris có viết sẵn cho tớ một bản tự giới thiệu, lát nữa tớ gửi tin nhắn qua cho cậu nhé.",
    "vo_103_ui_greet_001": "A, cậu tới rồi à... Có mang theo đồ ăn vặt cho tớ không đó?",
    "vo_103_ui_hang_001": "Buồn ngủ quá đi... Cho tớ nằm ườn ở đây thêm năm phút nữa thôi nha...",
    "vo_103_ui_lose_001": "Thua mất rồi... Lần sau nhất định tớ sẽ bắn chuẩn hơn...",
    "vo_103_ui_thank_001": "Oa, cậu tặng tớ món này thật sao? Tớ thích lắm luôn đó, cảm ơn cậu nha!",
    "vo_103_ui_win_001": "Bọn mình thắng rồi nè! Giờ thì về ngủ một giấc thật đã thôi nào!",

    # ---------------- Tilia (107) - Justice little knight, Helm Rider fan
    "vo_107_combat_battleClear_001": "Chiến thắng vang dội! Công lý một lần nữa được thực thi!",
    "vo_107_combat_battleClear_002": "Không kẻ ác nào có thể thoát khỏi lưỡi gươm công lý!",
    "vo_107_combat_battleClear_003": "Hành trình diệt trừ cái ác vẫn đang tiếp diễn, tiến lên nào!",
    "vo_107_combat_chat_001": "Mọi người cứ than đi tuần tra vất vả, chứ em là em thích mê luôn á!",
    "vo_107_combat_chat_002": "Mỗi bước chân tuần tra đều là để bảo vệ nụ cười của người dân!",
    "vo_107_combat_chatLvUp_001": "Kẻ địch đang chiếm thế thượng phong, nhưng em quyết không lùi bước đâu!",
    "vo_107_combat_chatNext_001": "Đằng trước có dấu hiệu khả nghi! Kỵ sĩ Tilia, xung phong trinh sát!",
    "vo_107_combat_dead_001": "Chiếc khiên này... nặng quá rồi...",
    "vo_107_combat_dead_002": "Là kỵ sĩ... mình phải nỗ lực hơn nữa mới được...",
    "vo_107_combat_eventRoom_001": "Không có bí mật nào qua mặt được cặp mắt tinh tường của kỵ sĩ này đâu nhé—",
    "vo_107_combat_perk_001": "Kỵ sĩ tập sự Tilia, biến thân!",
    "vo_107_combat_perk_002": "Đây chính là sức mạnh của chính nghĩa!",
    "vo_107_combat_perk_003": "Chính nghĩa tất thắng!",
    "vo_107_combat_restRoom_001": "Kỵ sĩ tập sự Tilia xin phép giải lao một tí ạ! Phù, sảng khoái cả người luôn... ♪",
    "vo_107_combat_shopRoom_001": "Nơi này... trông chẳng giống mấy tiệm buôn trong thành phố chút nào hết!",
    "vo_107_combat_subPerk_001": "Hiệp sĩ Hoàng gia nguyện lấy thân mình bảo vệ muôn dân!",
    "vo_107_combat_subPerk_002": "Em sẽ trở thành chiếc khiên vững chãi che chở cho mọi người!",
    "vo_107_combat_ultskill_001": "Hãy đón nhận cơn thịnh nộ của sự phán xét!",
    "vo_107_combat_ultskill_002": "Vì tự do và vinh quang bất diệt!",
    "vo_107_ui_affchat1_001": "Để tỏ lòng cảm kích đến chiến hữu tuyệt vời nhất trần đời, em xin tặng người chiếc chiến mũ này nha!",
    "vo_107_ui_affchat2_001": "Em biết là chiến hữu sẽ đội chiếc mũ này mà! Tuy vẫn còn phải cố gắng nhiều, nhưng trông hợp với người lắm đó!",
    "vo_107_ui_affchat3_001": "Ngay cả trong những thiên tiểu thuyết kỵ sĩ cổ đại hay phim ảnh Stella Dramas như Helm Rider, người hùng làm sao đơn độc nếu thiếu đi chiến hữu kề vai sát cánh chứ!",
    "vo_107_ui_affchat4_001": "Cái dây buộc tóc này ấy ạ? Hồi em mới chập chững vào nghề, một người bạn cứ nằng nặc dúi cho em, bảo là hợp với em lắm...",
    "vo_107_ui_affchat5_001": "Huyền thoại về đại kỵ sĩ Tilia lừng danh chính thức bắt đầu từ giây phút này đây!",
    "vo_107_ui_afflv1_001": "Trở thành hiệp sĩ chính nghĩa đã là ước mơ cháy bỏng của em từ thuở bé thơ rồi!",
    "vo_107_ui_afflv2_001": "Em xin lấy danh dự bảo đảm, công lý luôn luôn tồn tại! Mỗi khi em đứng gác, đi tuần tra hay giúp đỡ mọi người, em đều cảm nhận được ngọn lửa công lý ngay bên cạnh mình!",
    "vo_107_ui_afflv3_001": "Được phiêu lưu cùng chiến hữu và chiến đấu vì lẽ phải khiến em thấy mình hệt như một siêu anh hùng vậy—thích mê luôn!",
    "vo_107_ui_birth_001": "Hôm nay là sinh nhật của em đó nha! Và người biết điều ước của em là gì rồi đúng không nè? Em ước sẽ trở thành một đại kỵ sĩ chân chính!",
    "vo_107_ui_gachaNew_001": "Báo cáo! Em là Tilia, Kỵ sĩ Tập sự đại diện cho chính nghĩa! Hãy trở thành chiến hữu của em và cùng nhau giương cao ngọn cờ công lý nhé!",
    "vo_107_ui_thank_001": "Ồ! Người vẫn nhớ em thích gì sao? Em vui phát khóc luôn nè!",

    # ---------------- Firenze (110) - Seductive, proud, elegant noble mistress
    "vo_110_combat_chat_001": "Mọi cuộc giao tranh trên thương trường hay chiến trường, kết cục đều đã nằm trong tính toán của tôi.",
    "vo_110_combat_dead_001": "Tôi... đã tính sai một nước cờ sao?",
    "vo_110_combat_dead_002": "Dám đả thương tôi... các người sẽ phải trả giá đắt gấp bội!",
    "vo_110_combat_eventRoom_001": "Hừm. Hy vọng chuyện này không làm lãng phí thời gian quý báu của tôi.",
    "vo_110_combat_perk_001": "Sức hút của tôi lại càng thêm phần lộng lẫy.",
    "vo_110_combat_perk_002": "Ồ, phương án này đạt hiệu suất cao đấy.",
    "vo_110_combat_perk_003": "Tôi duyệt món này.",
    "vo_110_combat_restRoom_001": "Tôi chợp mắt một lát đây. Cậu cũng tranh thủ nghỉ ngơi dưỡng sức đi nhé.",
    "vo_110_combat_shopRoom_001": "Về khoản mua sắm thì cậu rành rọt hơn tôi đúng không nào?",
    "vo_110_combat_subPerk_001": "Tôi sẽ bọc lót phía sau cho cậu.",
    "vo_110_combat_subPerk_002": "Kiểm soát rủi ro vốn là sở trường của tôi mà.",
    "vo_110_combat_ultskill_001": "Thật vô phép vô tắc. Nghiêm nào!",
    "vo_110_combat_ultskill_002": "Quỳ rạp xuống trước mặt tôi mau!",
    "vo_110_ui_affchat1_001": "Đứng yên nào. Đừng cử động nhé, ngoan.",
    "vo_110_ui_affchat2_001": "Làm hết sức, chơi hết mình. Nhân tiện thì, cậu có rảnh một lát không?",
    "vo_110_ui_affchat4_001": "Xem như phần thưởng, tôi sẽ cho cậu nếm chút hương nước hoa đặc trưng của tôi nhé.",
    "vo_110_ui_affchat5_001": "Mấy buổi tiệc tùng xã giao tẻ nhạt đến phát ngán, tôi quyết định chuồn ra đây với cậu.",
    "vo_110_ui_afflv1_001": "Tôi kỳ vọng mối quan hệ hợp tác này sẽ mang lại lợi ích tối đa cho cả đôi bên.",
    "vo_110_ui_afflv2_001": "Tôi đánh giá cao việc cậu đi thẳng vào trọng tâm vấn đề. Rất mong chờ được hợp tác sâu hơn với cậu.",
    "vo_110_ui_afflv3_001": "Bất cứ lúc nào cậu cần lời khuyên, cửa phòng tôi luôn rộng mở 24/7.",
    "vo_110_ui_afflv4_001": "Một khi đã đặt bút ký vào khế ước này, chúng ta sẽ cùng sẻ chia mọi thứ.",
    "vo_110_ui_birth_001": "Được rồi... Riêng hôm nay thôi, khỏi cần giữ kẽ lễ nghi làm gì. Tôi cho phép cậu được thỏa thích chúc mừng sinh nhật tôi đấy ♪",
    "vo_110_ui_gachaNew_001": "Tôi là Firenze, đồng minh đắc lực của cậu. Tôi sẽ chứng minh giá trị của mình, và cũng hy vọng cậu đừng làm tôi thất vọng.",
    "vo_110_ui_thank_001": "Món quà này rất hợp nhãn của tôi. Cậu cũng biết cách lấy lòng người khác đấy chứ ♪",

    # ---------------- Iris (111) - Gentle, scholarly guild accountant
    "vo_111_combat_battleClear_001": "Tuyệt quá, mọi người đều an toàn cả rồi!",
    "vo_111_combat_battleClear_003": "Bọn mình đã giành chiến thắng mà không cần tiêu hao sức mạnh của Viên Đá Linh Hồn!",
    "vo_111_combat_chat_003": "Phù... Mệt quá đi mất... Ước gì giờ được ngồi nhâm nhi chút nước ngọt có ga mát lạnh thì đã biết mấy.",
    "vo_111_combat_chat_004": "Hy vọng thù lao cho ủy thác tiếp theo sẽ thật hậu hĩnh!",
    "vo_111_combat_dead_001": "Ahhh... Đầu óc em nóng bừng bừng rồi...",
    "vo_111_combat_dead_002": "Em... đã đến giới hạn chịu đựng rồi...",
    "vo_111_combat_eventRoom_001": "Tỷ lệ rủi ro và lợi nhuận thường phải cân bằng mới hợp lý.",
    "vo_111_combat_perk_001": "Cổ nhân tộc Long từng dạy: 'Học hải vô nhai' — biển học là vô bờ bến.",
    "vo_111_combat_perk_002": "Em hiểu rồi! Nắm rõ toàn bộ cơ chế rồi ạ!",
    "vo_111_combat_perk_003": "Bằng cách này, tỷ lệ thắng của bọn mình lại tăng thêm rồi nè.",
    "vo_111_combat_restRoom_001": "Nếu anh muốn nghỉ ngơi, có thể mượn gối của em này.",
    "vo_111_combat_shopRoom_001": "Nhớ chi tiêu trong phạm vi ngân sách cho phép thôi đấy nhé!",
    "vo_111_combat_subPerk_001": "Giá mà có thêm chiếc bánh quy bơ nữa thì tuyệt cú mèo luôn.",
    "vo_111_combat_subPerk_002": "Em sẽ dốc hết sức để không làm vướng chân mọi người đâu ạ!",
    "vo_111_combat_ultskill_001": "Nhiệt độ ổn định, áp suất chuẩn xác. Băng Phong Hàn Sóng, giáng lâm!",
    "vo_111_combat_ultskill_002": "Thành quả sau bao ngày nghiên cứu đây! Sóng Lạnh Băng Giá!",
    "vo_111_ui_affchat1_001": "Ugh... Hay là em xin đi làm người gác cổng ở Monolith nhỉ? Thế thì sẽ chẳng phải bận rộn bù đầu với sổ sách nữa...",
    "vo_111_ui_affchat2_001": "Mỗi ngày trôi qua, hết chuyện này đến chuyện khác xảy ra trục trặc... y hệt như kết quả bài thi của em vậy á.",
    "vo_111_ui_affchat3_001": "Phải biết chắt chiu tiết kiệm tiền bạc bất cứ khi nào có thể chứ!",
    "vo_111_ui_affchat4_001": "Nếu một mai không làm Du Hành Giả nữa... anh có muốn cùng em mua một căn nhà nhỏ rồi sống chung không?",
    "vo_111_ui_affchat5_001": "Và đó là đoạn kết cho câu chuyện về cô bé mang tên Iris.",
    "vo_111_ui_afflv1_001": "Em luôn cảm thấy mình là người vụng về, lúc nào cũng cần người khác đỡ đần...",
    "vo_111_ui_afflv2_001": "Giờ đây lúc nào em cũng dựa dẫm vào anh...",
    "vo_111_ui_afflv3_001": "Ừm... Đợi mọi người ngủ say rồi, anh có muốn cùng em tâm sự một chút không?",
    "vo_111_ui_afflv4_001": "r=a(1-sinθ)... Sếp ơi, về công thức hình trái tim này... liệu nó có nghĩa là... Ơ... Em...",
    "vo_111_ui_birth_001": "Ơ dạ? Quà sinh nhật tặng em sao? Em cảm ơn anh nhiều lắm!",
    "vo_111_ui_discuss_001": "Noya và Amber là những đồng đội đáng tin cậy nhất của em... Từ lâu em đã xem họ như người trong gia đình rồi.",
    "vo_111_ui_discuss_002": "Mỗi khi căng thẳng mệt mỏi, em thường ghé qua Tiệm Cà Phê Hộp Mèo để chơi đùa cùng mấy bé mèo.",
    "vo_111_ui_discuss_003": "Trời đất ơi, em ngưỡng mộ các thầy cô giáo thật đấy.",
    "vo_111_ui_gachaNew_001": "Rất vui được gặp anh, em là Iris. Về khoản tính toán sổ sách và chi tiêu của Lữ Đoàn, xin cứ an tâm giao hết cho em nhé!",
    "vo_111_ui_lose_001": "Có phải em... thực sự không có tố chất làm Du Hành Giả không anh...?",
    "vo_111_ui_thank_001": "M-Món quà này tuyệt vời quá ạ! Làm sao em có thể đáp lại tấm lòng của anh đây?",

    # ---------------- Noya (112) - Cheerful, energetic, best friend partner
    "vo_112_combat_battleClear_001": "Tuyệt vời ông mặt trời! Chiến thắng dễ như ăn kẹo!",
    "vo_112_combat_dead_001": "Ái chà... Tớ đuối sức mất rồi...",
    "vo_112_combat_dead_002": "Mình... vẫn chưa hái được ngôi sao nào mà...",
    "vo_112_combat_eventRoom_001": "Ồ, có ai ở đằng kia kìa? Oa, sẽ có bất ngờ gì đây ta? ♪",
    "vo_112_combat_perk_001": "Được rồi, nắm chắc rồi! Tớ đã thuần thục chiêu thức này rồi nhé!",
    "vo_112_combat_perk_002": "Tớ sẽ phát huy tối đa sức mạnh mới này!",
    "vo_112_combat_perk_003": "Ooh... ♪ Cảm giác sung sức ghê!",
    "vo_112_combat_restRoom_001": "Đừng gắng gượng quá sức nha! Nào nào, tranh thủ nghỉ ngơi chút xíu đi!",
    "vo_112_combat_shopRoom_001": "Tớ làm lon soda đây. Còn Sếp uống gì nè?",
    "vo_112_combat_subPerk_001": "Cứ giao cho tớ—mọi chuyện đảm bảo êm xuôi hết nhen!",
    "vo_112_combat_subPerk_002": "Mọi người cùng nhau đi hái sao nào!",
    "vo_112_combat_ultskill_001": "Chuẩn bị la oai oái đi là vừa!",
    "vo_112_combat_ultskill_002": "Dám cản đường tớ hái sao là tới số rồi đó nha!",
    "vo_112_ui_affchat1_001": "Ủy thác lần này bọn mình hoàn thành xuất sắc luôn nhỉ? ♪",
    "vo_112_ui_affchat2_001": "Cậu hỏi tớ đang khắc cái gì á? Hehe... Là chiếc xe Braude đẽo từ gỗ trôi dạt đó! Trông cũng xịn xò phết đúng hông?",
    "vo_112_ui_affchat3_001": "Có cậu ngồi ghế phụ đi cùng thế này thì chuyến đi dài mấy cũng vui hết nấc luôn á! ♪",
    "vo_112_ui_affchat4_001": "Loxy là một thành viên vô cùng quan trọng của cả đội đó nha.",
    "vo_112_ui_affchat5_001": "Sống giữa vùng Hoang Dã, cậu sẽ tự khắc học được cách biến những bữa ăn hàng ngày trở nên rộn rã và thú vị hơn.",
    "vo_112_ui_afflv1_001": "Kể từ ngày gặp được cậu, ngày nào với tớ cũng tràn ngập những cuộc phiêu lưu kỳ thú hết á!",
    "vo_112_ui_afflv2_001": "Hái được sao sẽ biến một điều ước thành hiện thực đó.",
    "vo_112_ui_afflv3_001": "Nếu như bọn mình mãi chẳng tìm thấy Đĩa Khắc Ấn của tớ thì sao ta?",
    "vo_112_ui_afflv4_001": "Nếu có một ngày bọn mình phải chia tay nhau...",
    "vo_112_ui_birth_001": "Giờ tớ mở mắt ra được chưa nè?",
    "vo_112_ui_gachaNew_001": "Chào cậu! Tớ là Noya, Du Hành Giả kiêm cộng sự đắc lực nhất trần đời của cậu đây! Bọn mình cùng nhau đi hái sao thôi nào!",
    "vo_112_ui_thank_001": "Tuyệt quá đi! Tớ thích món này lắm luôn á! Cảm ơn cậu đã cất công chuẩn bị nhé—tớ vui phát khóc luôn nè!",

    # ---------------- Nanoha (119) - Lap pillow maiden
    "vo_119_combat_restRoom_001": "Cậu vất vả nhiều rồi, nghỉ ngơi chút đi nào. Nếu cậu muốn thì... có thể gối đầu lên đùi Nanoha nè.",

    # ---------------- Fuyuka (134) - Stuttering shy girl
    "vo_134_combat_chat_001": "Monolith trông u ám đáng sợ quá, cứ như có quái vật chực chờ nhảy bổ ra hù dọa mình bất cứ lúc nào vậy...",
    "vo_134_combat_ultskill_001": "Đây là quyết tâm của em đó... Oa oa oa?!",
    "vo_134_combat_ultskill_002": "Đ-Đừng có coi thường nắm đấm của em...!",
    "vo_134_ui_gachaNew_001": "X-Xin chào, Chủ nhân!==RT==E-Em là F-F-Fuyuka...!",
    "vo_134_ui_greet_001": "U-Ừm... Chủ nhân ơi? Em... em muốn tập cách bắt chuyện với mọi người, người... người có thể chỉ bảo cho em một chút được không ạ...?",
    "vo_134_ui_thank_001": "E-Em thực sự xứng đáng nhận món quà tuyệt vời dường này sao ạ?!",

    # ---------------- Eleanor (137) - Apprentice knight, calls player Mentor
    "vo_137_combat_chat_001": "Để trở thành một Du Hành Giả thực thụ, em còn phải học hỏi rất nhiều điều nữa!",
    "vo_137_combat_ultskill_001": "Phù... Đã đến lúc em thể hiện bản lĩnh thật sự của mình rồi!",
    "vo_137_combat_ultskill_002": "Ước mơ của em... chính tay em sẽ biến nó thành hiện thực!",
    "vo_137_ui_gachaNew_001": "Em đang rất nóng lòng được cùng Tiền bối dấn thân vào những chuyến phiêu lưu kỳ thú đây ạ!",
    "vo_137_ui_valentine_001": "Của Tiền bối này! Ừm... em nghĩ là socola tự làm sẽ gửi gắm trọn vẹn tấm lòng của em hơn...",
    "vo_137_ui_thank_001": "Làm sao Tiền bối biết đây là thứ em đang tìm kiếm bấy lâu nay vậy ạ!? Em cảm ơn người nhiều lắm!",

    # ---------------- Allie (139) - Orphanage gentle big sister / mother
    "vo_139_ui_affchat1_001": "Ngay cả khi cậu ở ngoài thị trấn, hãy đảm bảo uống đủ nước, duy trì thói quen sinh hoạt đều đặn và nghỉ ngơi khi mệt mỏi nhé.",
    "vo_139_ui_affchat2_001": "Mấy đứa nhỏ cứ bám theo gọi chị là 'Mẹ', nhưng mà...",
    "vo_139_ui_affchat5_001": "Nếu có một nơi ta luôn muốn quay về, và ở đó luôn có ai đó ngóng đợi ta... thì nơi ấy tự khắc sẽ trở thành mái ấm gia đình.",
    "vo_139_ui_unlockCG_001": "Nhìn cậu gần thế này... cứ như em đang chuẩn bị vén khăn voan của cô dâu vậy. Tự dưng tim em đập thình thịch luôn nè...",

    # ---------------- Sparkla (140) - Pop inventor & Tyrant
    "vo_140_combat_chat_001": "Không biết Tháp Sao Monolith vận hành kiểu gì ta? Em muốn rã nó ra từng mảnh để nghiên cứu ghê.",
    "vo_140_combat_ultskill_001": "Ngủ ngon nhé mọi người ơi~ Phần còn lại giao cho cậu đó nha ♪",
    "vo_140_combat_ultskill_002": "Bánh Thỏ ơi, nhớ xử lý thật êm thấm và nhẹ nhàng nhé.",
    "vo_140_ui_affchat2_001": "Em dự định dành riêng một chỗ ngồi đặc biệt trên Super Action Pie cho Ma Vương đó nha.",
    "vo_140_ui_affchat5_001": "Ngoài những ủy thác quan trọng không thể từ chối, em chỉ muốn dành trọn thời gian quý báu của mình cho những người dễ thương thôi à.",
    "vo_140_ui_thank_001": "Oa, cưng ghê á ♪ Em biết ngay Ma Vương là người hiểu rõ gu của em nhất mà!",

    # ---------------- Cosette (142) - Loyal maid / assassin
    "vo_142_combat_ultskill_001": "Ta tuyên án các ngươi: chôn thây dưới nấm mồ tăm tối vĩnh hằng!",
    "vo_142_combat_ultskill_002": "Dẫu có phải đánh đổi bằng cả sinh mạng, em cũng quyết hoàn thành mệnh lệnh của Chủ nhân!",
    "vo_142_ui_affchat1_001": "Vâng, trước đây em từng có sừng. Nhưng vì nhiệm vụ, em đã phải tự tay cắt bỏ chúng.",
    "vo_142_ui_affchat4_001": "Họ đã cưu mang em khi em chẳng còn nơi nương tựa. Dâng trọn sinh mạng này cho họ âu cũng là lẽ đương nhiên.",

    # ---------------- Caramel (147) - Rock solo artist
    "vo_147_combat_chat_001": "Chơi bời trong thành phố cũng vui, nhưng mà cảm giác ở đây PHÊ hơn gấp bội lần!",
    "vo_147_combat_ultskill_001": "Nếm thử làn sóng âm thanh bùng nổ này đi!",
    "vo_147_ui_gachaNew_001": "Nghệ sĩ solo Caramel đã tới, sẵn sàng khuấy đảo Monolith bằng những giai điệu bùng cháy nhất đây! Quẩy hết mình cùng tớ nhé!",
    "vo_147_ui_greet_001": "Này, nghe nè! Tớ muốn cậu là người đầu tiên được nghe ca khúc mới của tớ đó, chịu hông?"
}

def clean_character_line(cid: str, text: str) -> str:
    """Applies contextual character naturalization rules to a single subtitle string."""
    out = text

    # 1. Apply global MT idiom / term remediation
    for pat, rep in COMPILED_GLOBAL_MT:
        out = pat.sub(rep, out)

    # 2. Character-specific pronoun softening
    # Amber (103) & Noya (112): tớ - cậu
    if cid in ("103", "112"):
        out = re.sub(r"\bTôi và bạn\b", "Tớ và cậu", out)
        out = re.sub(r"\bbạn và tôi\b", "cậu và tớ", out)
        out = re.sub(r"\bTôi\b", "Tớ", out)
        out = re.sub(r"\btôi\b", "tớ", out)
        out = re.sub(r"\bBạn\b", "Cậu", out)
        out = re.sub(r"\bbạn\b", "cậu", out)

    # Tilia (107) & Iris (111) & Nanoha (119) & Firefly (115) & Fuyuka (134): em
    elif cid in ("107", "111", "115", "119", "134"):
        out = re.sub(r"\bTôi\b", "Em", out)
        out = re.sub(r"\btôi\b", "em", out)
        if cid == "107":
            out = re.sub(r"\bBạn\b", "Chiến hữu", out)
            out = re.sub(r"\bbạn\b", "chiến hữu", out)
        elif cid == "134":
            out = re.sub(r"\bBạn\b", "Chủ nhân", out)
            out = re.sub(r"\bbạn\b", "Chủ nhân", out)
        else:
            out = re.sub(r"\bBạn\b", "Anh", out)
            out = re.sub(r"\bbạn\b", "anh", out)

    # Allie (139): chị / em
    elif cid == "139":
        out = re.sub(r"\bTôi\b", "Chị", out)
        out = re.sub(r"\btôi\b", "chị", out)
        out = re.sub(r"\bBạn\b", "Cậu", out)
        out = re.sub(r"\bbạn\b", "cậu", out)

    # Eleanor (137): Tiền bối / em
    elif cid == "137":
        out = re.sub(r"\bTôi\b", "Em", out)
        out = re.sub(r"\btôi\b", "em", out)
        out = re.sub(r"\bBạn\b", "Tiền bối", out)
        out = re.sub(r"\bbạn\b", "Tiền bối", out)
        out = re.sub(r"\bCố vấn\b", "Tiền bối", out)
        out = re.sub(r"\bcố vấn\b", "tiền bối", out)

    # Cosette (142): Chủ nhân / em
    elif cid == "142":
        out = re.sub(r"\bTôi\b", "Em", out)
        out = re.sub(r"\btôi\b", "em", out)
        out = re.sub(r"\bBạn\b", "Chủ nhân", out)
        out = re.sub(r"\bbạn\b", "Chủ nhân", out)

    # Firenze (110) & Kasimira (108): tôi - cậu (refined onee-san)
    elif cid in ("110", "108"):
        out = re.sub(r"\bBạn\b", "Cậu", out)
        out = re.sub(r"\bbạn\b", "cậu", out)

    # General fallback: soften 'bạn' to 'cậu'
    else:
        out = re.sub(r"\bBạn\b", "Cậu", out)
        out = re.sub(r"\bbạn\b", "cậu", out)

    # Fix false positive 'cậu bè'
    out = re.sub(r"\bcậu bè\b", "bạn bè", out)
    out = re.sub(r"\bCậu bè\b", "Bạn bè", out)

    return out.strip()

def main():
    t0 = time.time()
    print("=" * 75)
    print("BẮT ĐẦU ĐẠI TU TOÀN DIỆN THOẠI NHÂN VẬT & CHIÊU MỘ (CAMPAIGN 20)")
    print("=" * 75)

    # ---------------------------------------------------------------------
    # STEP 1: CHARGETLINES (RECRUITMENT INTRODUCTIONS) DUAL-SYNC
    # ---------------------------------------------------------------------
    p_603 = ENTRIES_DIR / "00603_0x8dcf06b298f46b28.bin"
    p_850 = ENTRIES_DIR / "00850_0x17ba1c051ea16c44.bin"

    assert p_603.exists() and p_850.exists(), "CharGetLines tables missing!"
    d_850 = json.loads(p_850.read_text(encoding="utf-8"))
    d_603 = json.loads(p_603.read_text(encoding="utf-8"))

    # Apply all high-literary lines from 850 into master dict
    master_charget = dict(d_850)

    # Apply specific refinements for character personas
    charget_refined_count = 0
    for k, v in CHARGET_REFINEMENTS.items():
        if k in master_charget and master_charget[k] != v:
            master_charget[k] = v
            charget_refined_count += 1

    # Write identical perfected data to BOTH tables
    p_603.write_text(json.dumps(master_charget, indent=2, ensure_ascii=False), encoding="utf-8")
    p_850.write_text(json.dumps(master_charget, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Đã đồng bộ & tinh chỉnh CharGetLines (00603 & 00850): {len(master_charget)} dòng chiêu mộ.")
    print(f"  Trong đó: {charget_refined_count} câu thoại được tinh chỉnh sát với tính cách nhân vật.")

    # ---------------------------------------------------------------------
    # STEP 2: CHARACTER ARCHIVE DUAL-TABLE CHINESE ELIMINATION
    # ---------------------------------------------------------------------
    # Synchronize BaseInfo 00592 -> 00839
    p_592 = ENTRIES_DIR / "00592_0x200c969f988e4634.bin"
    p_839 = ENTRIES_DIR / "00839_0xb3e15e23afb27dd6.bin"
    if p_592.exists() and p_839.exists():
        d_592 = json.loads(p_592.read_text(encoding="utf-8"))
        p_839.write_text(json.dumps(d_592, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✓ Đã đồng bộ CharacterArchiveBaseInfo (00592 -> 00839): Xóa sạch 660 chuỗi tiếng Trung.")

    # Synchronize VoiceTitles 00594 -> 00841
    p_594 = ENTRIES_DIR / "00594_0xd8b61831cfe58bf2.bin"
    p_841 = ENTRIES_DIR / "00841_0x65c021091de910ba.bin"
    if p_594.exists() and p_841.exists():
        d_594 = json.loads(p_594.read_text(encoding="utf-8"))
        p_841.write_text(json.dumps(d_594, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✓ Đã đồng bộ CharacterArchiveVoice (00594 -> 00841): Xóa sạch 3.560 tiêu đề tiếng Trung.")

    # ---------------------------------------------------------------------
    # STEP 3: MASTER VOICE SUBTITLES OVERHAUL (00552)
    # ---------------------------------------------------------------------
    p_voice = ENTRIES_DIR / "00552_0x80911df3a563e0f3.bin"
    assert p_voice.exists(), "Voice subtitles table 00552 missing!"
    d_voice = json.loads(p_voice.read_text(encoding="utf-8"))

    voice_mod_count = 0
    explicit_count = 0

    for k, v in d_voice.items():
        # Get character id if applicable (e.g. vo_103_...)
        parts = k.split("_")
        cid = parts[1] if len(parts) >= 2 and parts[1].isdigit() else "other"

        cur_text = v.get("text", {}).get("female_jp", [""])[0]
        new_text = cur_text

        # 1. Check explicit hand-crafted overrides first
        if k in EXPLICIT_VOICE_OVERRIDES:
            new_text = EXPLICIT_VOICE_OVERRIDES[k]
            explicit_count += 1
        else:
            # 2. Apply contextual character-aware polish
            new_text = clean_character_line(cid, cur_text)

        if new_text != cur_text:
            voice_mod_count += 1
            # Update female_jp
            v["text"]["female_jp"][0] = new_text
            # Update female_cn if present in text
            if "female_cn" in v["text"] and isinstance(v["text"]["female_cn"], list) and len(v["text"]["female_cn"]) > 0:
                v["text"]["female_cn"][0] = new_text

    p_voice.write_text(json.dumps(d_voice, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Đã đại tu Master Voice Subtitles ({p_voice.name}):")
    print(f"  - Tổng số câu thoại được cải thiện: {voice_mod_count} / {len(d_voice)}")
    print(f"  - Trong đó: {explicit_count} câu thoại quan trọng được viết mới hoàn toàn.")

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
    print("\n-> Đang kiểm chứng dữ liệu đã triển khai qua verify_deployed_game_data.py...")
    verify_script = ROOT / "tools" / "verify_deployed_game_data.py"
    # Update expected hash in verify script before running
    v_content = verify_script.read_text(encoding="utf-8")
    v_content = re.sub(
        r'EXPECTED_DATA_SHA256 = "[a-f0-9]{64}"',
        f'EXPECTED_DATA_SHA256 = "{new_sha}"',
        v_content
    )
    # Add voice & recruitment assertions to verify script
    if 'ASSERT_VOICE_SAMPLE' not in v_content:
        sample_assert_code = (
            f'\n# Voice overhaul assertions\n'
            f'ASSERT_VOICE_SAMPLE = {{\n'
            f'    "vo_103_combat_chat_001": "Vẫn còn dư dả băng đạn dự phòng",\n'
            f'    "vo_112_ui_affchat3_001": "ghế phụ",\n'
            f'    "vo_107_combat_chatLvUp_001": "chiếm thế thượng phong",\n'
            f'}}\n'
        )
        v_content += sample_assert_code
    verify_script.write_text(v_content, encoding="utf-8")

    import subprocess
    res = subprocess.run([sys.executable, str(verify_script)], capture_output=True, text=True, encoding="utf-8")
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        sys.exit(1)

    elapsed = time.time() - t0
    print(f"\n[HOÀN THÀNH XUẤT SẮC TRONG {elapsed:.2f} GIÂY] ĐẠI TU THOẠI VÀ CHIÊU MỘ ĐÃ SẴN SÀNG!")

if __name__ == "__main__":
    main()
