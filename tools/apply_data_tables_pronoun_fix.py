# -*- coding: utf-8 -*-
"""
Script to apply gender-neutral pronoun fixes to data tables in work/research/data_200_decrypted/entries.
Replaces gendered "anh/chị" towards the player with neutral/respectful anime terms (Sếp, Đội trưởng, ngài, cậu, tôi).
"""

import json
from pathlib import Path
import re
import sys
import time

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))
from arcx_adapter import repack_archive

ENTRIES_DIR = ROOT / "work" / "research" / "data_200_decrypted" / "entries"
DEC_DIR = ROOT / "work" / "research" / "data_200_decrypted"
OUTPUT_ARCX = ROOT / "dist" / "data_patched_vi.arcx"

# Exact key replacements
EXACT_TABLE_REPLACEMENTS = {
    # ActivityStory
    "ActivityStory.101080208.2": "Bạo chúa, tôi đã dành cho ngài chỗ ngồi tốt nhất trong nhà.",

    # ActivityTask
    "ActivityTask.201030104.2": "Đọc truyện sự kiện: Trở Thành Đôi Tay Của Cậu",

    # Agent
    "Agent.300102.3": "Tôi nghe nói bạn khá giỏi trong việc theo đuổi điểm cao trong các trò chơi nhịp điệu... Tại sao không chỉ cho học sinh của tôi cách thực hiện? Tôi sẽ đổi giúp cậu những hộp đạn này. Một thỏa thuận khá tốt, phải không?",

    # CharacterArchiveContent
    "CharacterArchiveContent.10807.2": "Chiếc Tay Cầm Phủ Bụi\n\nMọi người trong Tiểu Đội Ba chúng em ai ai cũng mê chơi game hết á! Ngầu đúng không nè? Ghen tị lắm chứ gì?\nNhưng mà dạo gần đây, có một chuyện làm em đau đầu muốn xỉu luôn... Chiếc tay cầm chơi game yêu quý của em bỗng dưng bốc hơi mất tăm mất tích! Hic hic, không có nó thì làm sao em cày cuốc leo rank được nữa đây trời...\n\nEm đã lùng sục khắp nơi, từ phòng huấn luyện cho tới nhà ăn, thậm chí còn lục tung cả gầm giường của mấy đứa trong đội mà vẫn chẳng thấy tăm hơi đâu. Đang lúc tuyệt vọng nhất thì em chợt nhớ ra: hình như lần cuối cùng nhìn thấy nó là ở chỗ của chị đội trưởng!\nMà chị ấy thì nghiêm khắc có tiếng rồi, lúc nào cũng dặn phải tập trung huấn luyện, cấm được lơ là chểnh mảng. Giờ mà tự vác mặt đến xin lại chắc chắn sẽ bị chị ấy mắng cho một trận te tua, khéo còn bị phạt chạy mười vòng quanh sân tập cũng nên...\n\nSếp ơi, em có ý này hay lắm—nếu là Sếp đi mượn, biết đâu chị ấy lại nể tình mà trả lại ngay thì sao? Đi mà Sếp, giúp em một lần này thôi, em hứa từ giờ sẽ chăm chỉ làm việc mà!",
    "CharacterArchiveContent.12302.2": "Đội Trinh Sát trước đây từng có rất nhiều đàn anh đàn chị tham gia, nhưng mọi người dần dần đều chuyển đi nơi khác mất rồi, giờ chỉ còn lại một mình Ann thôi... Nhưng mà Ann không sợ đâu nhé! Ann sẽ thay mặt mọi người bảo vệ thật tốt cho cả đội!",

    # CharacterSkin
    "CharacterSkin.11103.2": "Dưới ánh nắng đông trong lành, hình bóng cậu nâng niu ly nước ấm phả ra làn khói trắng; một người luôn tự nhận mình bình phàm giản đơn, nhưng lại chính là toàn bộ ý nghĩa của ngày hôm nay.",
    "CharacterSkin.11104.2": "Cái đó... Em sẽ cố hết sức giữ thăng bằng cho chiếc phao bơi này, nhưng khi trèo lên Sếp nhớ cẩn thận một chút nhé. ——Đ-Đương nhiên rồi, nếu Sếp lỡ sảy chân rơi xuống nước, em nhất định sẽ kéo Sếp lại thật chặt!",
    "CharacterSkin.11205.2": "Ủy thác hôm nay là cùng người ta nghỉ ngơi trọn vẹn cả ngày đó nha~\nNếu không có ý kiến gì thì mau thay đồ ngủ vào đi nào, chỗ trống bên cạnh là em để dành riêng cho Sếp đấy nhé~",
    "CharacterSkin.14903.2": "Vị chua đắng của cà phê, hương thơm ngát của đóa tường vi, em muốn chia sẻ trọn vẹn mọi trải nghiệm mới mẻ này cùng với cậu. Khi tuyết tan rồi, chúng mình cùng nhau hẹn hò một chuyến nhé?",
    "CharacterSkin.15503.2": "Trong làn nước biển dạt dào, phảng phất hương vị của rạn san hô, và cả hương thơm quen thuộc của Đội trưởng nữa. Khẽ nhắm mắt lại, ngỡ như đang được tất thảy sự dịu dàng này ôm trọn vào lòng vỗ về.",

    # CharGetLines
    "CharGetLines.10301.1": "Em là Amber.\n...Iris có viết sẵn cho em một bản tự giới thiệu, lát nữa em sẽ gửi qua tin nhắn cho Sếp nhé.",
    "CharGetLines.10306.1": "Nương theo làn gió biển ấm nồng, chớp lấy một thoáng lặng giữa ngày hội rộn rã, em khẽ hướng ánh nhìn bình yên về phía Sếp.",
    "CharGetLines.11302.1": "Lại gặp nhau rồi, Đội trưởng! Có một ủy thác khẩn cấp cần đến sự trợ giúp của Đội trưởng, nội dung chi tiết em sẽ báo cáo cụ thể trên đường đi.",
    "CharGetLines.11401.1": "Hừ hừ hừ... Dưới sự dẫn dắt của số phận bóng tối, rốt cuộc chúng ta cũng đã tao ngộ! Kể từ hôm nay trở đi, sức mạnh diệt thế của đại nhân Chaton sẽ phụng sự cho ngài!",
    "CharGetLines.11402.1": "Ngạc nhiên chưa! Kẻ thừa kế bóng tối vĩ đại nhất đã đích thân đến tái ngộ cùng ngài đây!",
    "CharGetLines.11503.1": "Đội trưởng ơi, em không còn là con nít nữa đâu, em cũng có thể bảo vệ Đội trưởng mà.",
    "CharGetLines.11601.1": "Em... em là Ridge, quản lý nhà kính bên Nông Nghiệp Liên Hợp. Lần đầu gặp mặt... mong Sếp chỉ giáo thêm cho em ạ...",
    "CharGetLines.11602.1": "Lần này... em có đem chút quà cho Sếp nè! Toàn là rau củ tươi ngon do chính tay em chăm sóc đó, vừa mới hái ngoài vườn luôn á.",
    "CharGetLines.11701.1": "Chào Đội trưởng! Em là Jinglin, chưởng quầy của nhà hàng Hoài Cảnh Thực Phủ (Huaijing Bistro)! Sau này mong Đội trưởng chiếu cố việc làm ăn của quán em nhé!",
    "CharGetLines.11702.1": "Em sẽ bảo nhà bếp nấu riêng cho Đội trưởng một phần ăn đặc biệt nhé. Hì hì, không phiền hà gì đâu, Đội trưởng là khách quen quý giá của nhà em mà!",
    "CharGetLines.12301.1": "Sếp ơii~ Cuối cùng Ann cũng được gặp Sếp rồi! Hi hi, Sếp có thể dẫn Ann đi phiêu lưu cùng được không nào~",
    "CharGetLines.12302.1": "Oa~ Sếp lại tìm thấy Ann rồi nè~ Lần tới phải đổi lại thành lượt Ann đi tìm Sếp đấy nhé~",

    # DatingCharacterEvent
    "DatingCharacterEvent.107302.3": '"Xin lỗi nhé, chờ em gọi điện một lát... Hừ, đúng là phí hoài thời gian quý báu—hôm nay rõ ràng là ngày nghỉ của mình mà!"\n\nCác kỵ sĩ trực ban nhanh chóng có mặt tại hiện trường, giúp hai người có thể tiếp tục ngày nghỉ thảnh thơi. Bạn nhận thấy nụ cười của Tilia dường như rạng rỡ hơn trước một chút.',
    "DatingCharacterEvent.123301.3": '"Đây nhất định là món quà thần núi ban tặng riêng cho Ann đấy. Để tôi chỉ cho em cách dùng nhé."\nNhìn ánh mắt mong chờ của Ann, bạn đưa ra một lời giải thích thật ấm áp, khiến cô bé mừng rỡ reo vui.',
    "DatingCharacterEvent.132303.2": '"Xem này!" Cô bé rút ra cuốn "Nhập Môn Giám Định Di Vật". "Đọc cuốn này đi rồi cậu sẽ chẳng bao giờ bị mấy tay gian thương lọc lừa nữa đâu."\nCô bé trao sách cho bạn với nụ cười ngượng nghịu: "Mong là nó giúp ích cho hành trình của cậu."',
    "DatingCharacterEvent.135301.3": '“Cậu không định nhận nó à?” bạn hỏi.\n\n"Tin tức không chỉ ở trang nhất mà còn để bảo vệ sự thật."\n\nCó vẻ như cô ấy thực sự nghiêm túc về chuyện này.',
    "DatingCharacterEvent.137301.2": '“Xem ra Tiền bối có tiêu chuẩn khá khắt khe về bánh ngọt nhỉ.”\n"À thì, hiếm khi được đi chơi cùng em nên tôi muốn chọn quán nào được đánh giá cao một chút. Tôi không muốn đồ ăn làm em thất vọng."\n"Em đâu có kén ăn dữ dằn như tiền bối n... Ưm."\nChưa kịp nói dứt câu, một miếng bánh ngọt mềm mại đã được khéo léo đút thẳng vào miệng bạn.',
    "DatingCharacterEvent.139301.2": 'Cái nhìn trừng trừng của giáo sư dữ dội đến mức bạn không dám sửa lại lời ông ấy. Bạn nghiến răng đi theo giáo sư vào lớp.\n\nNgay khi...',
    "DatingCharacterEvent.140302.3": 'Sparkla khẽ vươn vai một cái thật sảng khoái.\nThoáng cái mà cả hai đã ở lỳ trong thư viện suốt cả ngày trời. Sparkla đầy tiếc nuối xếp lại những cuốn sách chưa đọc xong lên giá.\n"Ma Vương..."\n"Em..."\nCả hai đồng thanh cất lời cùng một lúc, rồi nhìn nhau mỉm cười đầy thấu hiểu.\n"Cậu vừa định rủ lần sau tụi mình lại ghé qua đây tiếp, đúng không nào?"',
    "DatingCharacterEvent.143302.2": 'Bạn tưởng mình đã đi vào ngõ cụt ở bức tường đá, nhưng Wraith đã bật một công tắc ẩn và tảng đá bị nghiền nát mở ra.\n\nTrước khi bạn kịp phản ứng, một nhà tắm tự nhiên hiện ra.\n\n"Tôi đã bỏ rất nhiều công sức để sửa chữa nơi này."\n\n"Nhưng nhìn thấy vẻ mặt đó của cậu à? Hoàn toàn xứng đáng."\n\n"Hãy nhảy vào. Đừng lo, nước rất trong lành."\n\nCô ấy biến mất sau tấm bình phong để tắm rửa. Không muốn tỏ ra thô lỗ, bạn quyết định thử cách tắm ngoài trời này. Tuy nhiên...',
    "DatingCharacterEvent.147302.3": 'Nàng lục tìm trong túi—ôi bất ngờ chưa, cô nàng lại cháy túi mất rồi. Bạn đành phì cười bất lực rồi rút tiền thanh toán hộ nàng.\n"Em nhất định sẽ đền đáp bằng một buổi biểu diễn miễn phí, producer đại nhân!"\nCô nàng tỏ ra vô cùng quyết tâm dùng tài năng âm nhạc để báo đáp món nợ ân tình này.',
    "DatingCharacterEvent.156303.2": '"Sự kiện bốc thăm lần này tặng gấu bông ước nguyện từ Tinh Tháp đấy, cực kỳ quý hiếm lại còn giới hạn số lượng, tôi nhất định phải rinh bằng được một con!"\nMiệng thì nói đầy tự tin, nhưng khi nhân viên cầm thùng phiếu bước đến, Nazuna lại lộ rõ vẻ chần chừ, đôi mắt long lanh đáng thương nhìn sang bạn.\n"Ý em là muốn tôi bốc thăm hộ à?"',
    "DatingCharacterEvent.156303.3": '"Được rồi, được rồi. Nhưng nếu tôi không hiểu thì đừng trách tôi..."\n\n"Yay! Tôi tin tưởng vào vận may tuyệt vời của Sếp mà!"\nMay mắn thay, bạn đã không làm Nazuna thất vọng. Nhìn cô bé vui sướng nhấc thú nhồi bông lên, bạn cũng không khỏi mỉm cười.',

    # DatingLandmarkEvent
    "DatingLandmarkEvent.1713.3": '"Rắc" một tiếng giòn giã vang lên, vách ngăn bằng tre giữa hai ban công bỗng nứt toác ra một khoảng trống vừa vặn cho một người chui lọt. "Hóa ra đây không phải là cửa sổ à..." ==DATING_CHARACTER== ngượng nghịu thò đầu sang. "Ủa? Sao ban công phòng cậu trông rộng hơn phòng tôi thế nhỉ? Tầm nhìn ngắm cảnh cũng xịn hơn nữa."\nNói đoạn, cô nàng liền trèo tót sang hẳn bên này. "Tối nay tôi ngủ lại bên phòng cậu được không?"\n\nBạn bỗng thấy mình bị phân tâm hoàn toàn trước lời đề nghị bất ngờ ấy, dẫu rằng lý trí mách bảo: chẳng phải việc cấp bách lúc này là giải quyết tấm vách ngăn bị vỡ trước sao?',
    "DatingLandmarkEvent.1801.3": '"Cuối cùng cũng nhận ra rồi nhé!" Nàng nhảy xuống đất. "Em cứ tưởng Sếp định đi lướt qua em thêm lần nữa cơ đấy."',
    "DatingLandmarkEvent.1805.2": '"Cho tôi cắn một miếng được không?"\n"Ơ... Em cắn dở rồi này, dính lắm đấy..."\n"Không sao cả!" Bạn đã dỗ ngọt thành công nửa quả lê thơm ngon từ tay nàng.',
    "DatingLandmarkEvent.1805.3": 'Một ý nghĩ bất chợt lóe lên, bạn quay sang nàng với vẻ mặt tỉnh bơ: "Sau này nếu thấy món đồ ngọt nào không có mật ong, cậu tuyệt đối đừng ăn nhé."\n"Cậu nói linh tinh gì thế... lại định lừa nốt nửa quả lê của tôi chứ gì!"',
    "DatingLandmarkEvent.1902.3": '"Cậu thích ngắm bầu trời thật đấy. Trên đó có gì sao?"\n"Chẳng có gì cả."\n"Thế thì có ý nghĩa gì chứ?"\n"Alina này, cuộc đời này đẹp chính bởi vì đôi khi nó chẳng cần lý do hay ý nghĩa gì cả."',
    "DatingLandmarkEvent.1903.3": 'Nếu bạn đã tồn tại ở nơi này, bạn không thể là một ai khác. Bạn không chấp nhận để bản ngã của mình mãi mơ hồ như thế.\n"Này? Cậu giận tôi đấy à?"',
    "DatingLandmarkEvent.1905.2": '"Cậu đồng ý nhanh thế, cứ như thể đã nói câu này cả triệu lần rồi ấy." Nàng nhấp một ngụm trà rồi đẩy tách ra xa: "Trà này có vị giống đào thật đấy."',
    "DatingLandmarkEvent.1906.2": '"Mỗi khi cảm thấy cô đơn, cậu hãy nhìn lên vầng trăng nhé," Alina bảo bạn. "Dù bao năm tháng trôi qua, ánh trăng vẫn chẳng hề đổi thay. Chỉ cần ngước nhìn lên, chúng ta sẽ luôn cùng ngắm chung một vầng trăng."',
    "DatingLandmarkEvent.2001.3": '"Em đợi Sếp mãi đấy!" Alina giục rồi kéo bạn bước vào trong nhà.',
    "DatingLandmarkEvent.2002.3": 'Nàng khẽ hà hơi ấm vào lòng bàn tay rồi áp nhẹ lên đôi má bạn: "Mặt Sếp lạnh ngắt rồi này!" Nàng khẽ thốt lên.\nBàn tay nàng ấm áp tựa như vầng dương dịu nhẹ, đưa bạn trở về một buổi chiều mùa hè êm đềm.',
    "DatingLandmarkEvent.611.1": '"Cho em nếm thử một miếng của Sếp được không?" ==DATING_CHARACTER== bất chợt hỏi.',

    # InfinityTowerMsg
    "InfinityTowerMsg.3005.2": "Một ông lão ở độ tuổi 70 tại Thành Phố Philae đã ăn 10 cây nấm đốm với hy vọng gặp lại người vợ đã khuất của mình. Sau đó ông đã được một bác sĩ phòng khám tư nhân cứu chữa kịp thời.",

    # Item
    "Item.10304.3": "Nương theo làn gió biển ấm nồng, chớp lấy một thoáng lặng giữa ngày hội rộn rã, em khẽ hướng ánh nhìn về phía Sếp. Khoảnh khắc ấy thật bình yên biết bao.",
    "Item.11103.1": "Mảnh Ghép 1/365 Của Cậu",
    "Item.11103.2": "Chứng chỉ mở khóa trang phục độc quyền của Iris: 'Mảnh Ghép 1/365 Của Cậu'!",
    "Item.11103.3": "Dưới ánh nắng đông nhàn nhạt, cậu cầm trên tay tách trà ấm, từng hơi thở khẽ phả thành làn sương mỏng manh. Người luôn tự nhận mình bình thường như cậu, lại chính là người thắp sáng ngày hôm nay trở nên thật đặc biệt.",
    "Item.11104.3": "Ừm... Em sẽ cố hết sức giữ chiếc phao này thăng bằng, nhưng Sếp nhớ cẩn thận khi bước lên nhé. —V-Và dĩ nhiên, lỡ Sếp có trượt chân rơi xuống nước, em nhất định sẽ kéo Sếp lên ngay!",
    "Item.130005.3": "Thời gian trôi mau nhưng tôi vẫn nhớ rõ bóng hình cậu trong lần đầu tiên ta gặp gỡ.",
    "Item.223022.3": "Đây là cửa ngõ vào Hỏa Ngục. Nó dẫn thẳng đến vực thẳm tội lỗi. Tôi đợi bên bờ sông, soi sáng chặng đường đau buồn phía trước của em, chúc em chìm vào tình yêu vĩnh hằng của tôi.",
    "Item.224002.3": "Như những cánh hoa, bóng hình người xưa dần tan biến. Dưới những đêm ngàn sao, lời thề của đôi ta vẫn sưởi ấm lòng bàn tay tôi. Những ngày ngát hương này lại khơi gợi ký ức về người, dẫu cho tâm trí tôi hằng chối từ.",
    "Item.224003.3": "Bay lên, bay lên, mãi vút bay lên. Tôi vượt qua mười hai tầng trời, ánh mắt người vẫn dõi theo. Không phải sự ràng buộc của trọng lực, mà là con đường ngàn sao dẫn lối về nhà.",
    "Item.224016.3": "Khi bình minh ló rạng đón chào ngày mới, cánh hoa cuối cùng lại khẽ rơi. Tôi kiếm tìm trong dòng chảy vô tận của thời gian, tìm kiếm những dấu vết xưa cũ đã phai mờ. Khi nhật nguyệt luân chuyển theo chu kỳ, và thời gian trôi như dòng sông sâu thẳm, qua ánh mắt người, mãi mãi sáng ngời, tôi sẽ nở hoa vĩnh hằng trong tầm mắt người.",
    "Item.224031.3": "Một tiếng chuông báo động vang lên khi lưỡi dao chạm vào chiếc rìu. Chiếc lồng vỡ tan và cô lao xuống vực thẳm. Qua cơn mưa đỏ thắm, cô ấy bắt gặp ánh mắt của người ấy.",
    "Item.224054.3": "Một thiên đường nhỏ chỉ của riêng chúng ta, cùng cô ấy chạy trong ánh đèn mờ ảo. Đừng sợ vấp ngã—Tôi sẽ nắm chặt tay em, cho đến khi chúng ta cùng nhau đi đến cuối cùng.",

    # MonsterManual
    "MonsterManual.1703100.2": "Hiệp sĩ lớn tuổi nhất trong Đội cận vệ Hoàng gia. Chiếc nỏ nặng mà ông mang theo vừa là thương hiệu của ông vừa là minh chứng cho khí phách tráng kiệt tuổi xế chiều.",

    # StarTowerBookEventReward
    "StarTowerBookEventReward.11002.2": "Phải rất lâu sau Firenze mới nhìn thấy lại chiếc hộp nhạc.\nCô đã nghe thấy giai điệu vui tươi quen thuộc đó và nhìn sang thì thấy chiếc hộp nhỏ đơn sơ trong tay một Du Hành Giả trung niên trong nhóm của cô.\nHọ đang nghỉ ngơi và người đàn ông trông rất hào hứng. Ông ấy nói rằng mình vừa tìm thấy chiếc hộp nhạc được giấu ở một góc và nghĩ rằng nó rất thú vị. Ông muốn mang nó về nhà cho con gái nhỏ của mình.\nTrong lúc hưng phấn, người đàn ông chợt nhận ra Firenze đang quan sát mình. Ông trở nên bối rối.\n\"Uh... Cô có bận tâm về điều này không?\"\n\"Không. Nó không hợp với tôi. Nếu ông muốn thì cứ giữ lấy.\"",
    "StarTowerBookEventReward.12502.2": "Sau vài tiếng sấm rền, mưa bắt đầu trút xuống như dự đoán.\nFreesia co ro dưới gốc cây, vài lá thư chưa gửi vẫn còn trong túi xách.\nMột lúc sau, cô nhét những lá thư vào trong áo khoác và ôm chặt chiếc túi vào ngực.\n\"Thế này sẽ giữ cho thư khô ráo.\"\n\nNgay khi cô chuẩn bị bước vào màn mưa như trút nước, bỗng nghe thấy tiếng bước chân vội vã chạy lại từ phía sau.\n\"Cuối cùng... tớ cũng tìm thấy cậu rồi!\"\nMột cô gái với mái tóc màu cam vừa thở hổn hển vừa chạy tới, tay cầm theo chiếc ô.\n\"Tớ thấy cậu để quên áo mưa lúc rời đi sáng nay.\"\n\"Nào, chúng mình cùng nhau đi phát nốt những lá thư còn lại nhé.\"",
    "StarTowerBookEventReward.14302.2": "Sự kết thúc của Cuộc săn lửa đánh dấu sự bắt đầu của một bữa tiệc. Khi rượu vang rót tràn ly và những bản ballad cổ xưa vang vọng, gia tộc tôn vinh những anh hùng đã mang Di Vật ánh sáng trở về.\nWraith trẻ tuổi luôn giành một vị trí ở hàng ghế đầu, ánh mắt dán chặt vào vị Trưởng cai ngục lừng danh của gia tộc—người ông kính yêu của cô.\nLần theo những vết sẹo phong sương trên cánh tay rắn rỏi của ông, cô bắt đầu mơ về ngày mình sẽ ngồi ở vị trí danh dự nơi đầu bàn ấy.\nCô cẩn thận thu xếp hành trang và dõi theo các toán đi săn, nhưng cô không mưu cầu vinh quang phù phiếm. Cô tới đó thuần túy là để học hỏi.\nWraith khắc sâu từng đường gươm dứt khoát và mọi biến ảo chuyển động của các Thể Tinh Thần vào tâm trí.\nCô kiên nhẫn bồi đắp kinh nghiệm ấy, lặng lẽ đợi chờ thời khắc mình có thể tự tin vung kiếm ra trận.",

    # StarTowerTalk
    "StarTowerTalk.917312.2": "Em đã ở đây chờ đợi Sếp, người chỉ huy vĩ đại của em! Và tôi sẽ cho Sếp một khoảng thời gian thực sự vui vẻ~",
    "StarTowerTalk.917314.2": "Bạn có chắc chắn có thể tin tưởng tôi không? Những lời ngọt ngào và cử chỉ dịu dàng của người... cũng có thể là cái bẫy để tôi quyến rũ ngài đấy~",
    "StarTowerTalk.917330.2": "Tôi thực sự say mê hương thơm... từ khát khao cháy bỏng của em~",
}

# Regex replacements across all data tables
TABLE_REGEX_RULES = [
    (r'\bmong anh/chị chỉ giáo\b', 'mong Sếp chỉ giáo'),
    (r'\bcho anh/chị nè\b', 'cho Sếp nè'),
    (r'\bcho anh/chị\b', 'cho Sếp'),
    (r'\banh/chị\b', 'Sếp'),
]

def apply_pronoun_fixes():
    print("=== APPLYING GENDER-NEUTRAL PRONOUN FIXES TO DATA TABLES ===")
    total_files_modified = 0
    total_keys_modified = 0

    for fpath in ENTRIES_DIR.glob("*.bin"):
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
        except Exception:
            continue

        file_modified = False
        for k, v in list(data.items()):
            if not isinstance(v, str):
                continue
            orig_v = v

            # 1. Exact map
            if k in EXACT_TABLE_REPLACEMENTS:
                v = EXACT_TABLE_REPLACEMENTS[k]

            # 2. Regex rules
            for pattern, repl in TABLE_REGEX_RULES:
                v = re.sub(pattern, repl, v)

            if v != orig_v:
                data[k] = v
                file_modified = True
                total_keys_modified += 1

        if file_modified:
            fpath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            total_files_modified += 1

    print(f"Data tables updated: {total_files_modified} files, {total_keys_modified} keys patched.")

def repack_data():
    print(f"\nRepacking data archive to {OUTPUT_ARCX}...")
    t0 = time.time()
    repack_archive(DEC_DIR, OUTPUT_ARCX, encrypt_payload=False)
    print(f"Repack completed in {time.time()-t0:.2f}s. Output size: {OUTPUT_ARCX.stat().st_size:,} bytes")

def main():
    apply_pronoun_fixes()
    repack_data()

if __name__ == "__main__":
    main()
