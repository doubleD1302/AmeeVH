import json

# Define the complete translations mapping
# For Plot (240 items)
PLOT_MAP = {
    # 1. Amber (10301 - 10303)
    "Plot.10301.1": ("Chú Mèo Lạc Lối: Phần Ⅰ", "Trau chuốt tiêu đề thi vị, chuẩn hóa cấu trúc chương."),
    "Plot.10301.2": ("Một lần “săn đuổi”, một phen lỡ bước, cùng đôi mắt ngây thơ vô tội.", "Khắc phục dịch thô máy dịch, tạo cảm xúc văn học anime RPG."),
    "Plot.10302.1": ("Chú Mèo Lạc Lối: Phần Ⅱ", "Trau chuốt tiêu đề thi vị, chuẩn hóa cấu trúc chương."),
    "Plot.10302.2": ("Chuyến đại phiêu lưu của mèo nhỏ, thiếu nữ và bạn.", "Nâng cao chất lượng câu văn tự nhiên, mượt mà theo nguyên tác 猫与少女与你的大冒险."),
    "Plot.10303.1": ("Chú Mèo Lạc Lối: Phần Ⅲ", "Trau chuốt tiêu đề thi vị, chuẩn hóa cấu trúc chương."),
    "Plot.10303.2": ("Lời tự đáy lòng được thổ lộ, cùng lời ước hẹn khắc sâu.", "Văn phong giàu chất trữ tình cho cao trào thức tỉnh."),

    # 2. Tilia (10701 - 10703)
    "Plot.10701.1": ("Kỵ Sĩ Mặt Nạ Tilia! Phần Ⅰ", "Chuẩn hóa danh xưng Kỵ Sĩ Mặt Nạ Tilia theo phong cách anime anh hùng."),
    "Plot.10701.2": ("Nguy cơ cận kề! Giông bão chẳng hề ngơi nghỉ.", "Khắc phục dịch máy 'Khủng hoảng sắp xảy ra! Những cơn bão không bao giờ ngừng'."),
    "Plot.10702.1": ("Kỵ Sĩ Mặt Nạ Tilia! Phần Ⅱ", "Chuẩn hóa danh xưng Kỵ Sĩ Mặt Nạ Tilia."),
    "Plot.10702.2": ("Trái tim chính nghĩa thức tỉnh! Vị kỵ sĩ săn lùng cự nhân.", "Sửa 'người khổng lồ' thành 'cự nhân', câu văn hào sảng."),
    "Plot.10703.1": ("Kỵ Sĩ Mặt Nạ Tilia!, Phần Ⅲ", "Chuẩn hóa danh xưng Kỵ Sĩ Mặt Nạ Tilia."),
    "Plot.10703.2": ("Tình bạn và mối liên kết! Người anh hùng cưỡi tuấn ưng khải hoàn.", "Sửa 'Falcon' thành 'tuấn ưng' (骏鹰), ngữ khí hào hùng chiến thắng."),

    # 3. Kasimira (10801 - 10803)
    "Plot.10801.1": ("Ngày May Mắn: Phần Ⅰ", "Chuẩn hóa tiêu đề chương cốt truyện."),
    "Plot.10801.2": ("Đánh mất bùa may mắn ư? Đó chẳng phải là chuyện hệ trọng bậc nhất sao!", "Khắc phục câu chữ dịch thô cứng nhắc."),
    "Plot.10802.1": ("Ngày May Mắn: Phần Ⅱ", "Chuẩn hóa tiêu đề chương cốt truyện."),
    "Plot.10802.2": ("Biết tìm bùa may mắn mới ở đâu bây giờ? Nơi Vùng Hoang Dã? Hay là tiệm bánh quy may mắn?", "Áp dụng thuật ngữ chuẩn Vùng Hoang Dã (Wilds)."),
    "Plot.10803.1": ("Ngày May Mắn: Phần Ⅲ", "Chuẩn hóa tiêu đề chương cốt truyện."),
    "Plot.10803.2": ("Để không đánh mất đôi giày của mình! Chạy mau đi nào! Ma Vương!", "Giữ đúng danh xưng Ma Vương (魔王) và giọng văn vui tươi, kịch tính."),

    # 4. Firenze (11001 - 11003)
    "Plot.11001.1": ("Kỳ Nghỉ Tại Philae: Phần Ⅰ", "Chuẩn hóa địa danh Thành Phố Philae theo glossary."),
    "Plot.11001.2": ("Khía cạnh khác nơi nàng mà bạn chưa từng được thấy.", "Văn phong tinh tế gợi cảm xúc tò mò."),
    "Plot.11002.1": ("Kỳ Nghỉ Tại Philae: Phần Ⅱ", "Chuẩn hóa địa danh Thành Phố Philae."),
    "Plot.11002.2": ("“Tỷ tỷ đại nhân” siêu nổi tiếng sắp xuất hiện sao?!", "Giữ đúng sắc thái nguyên tác 超人气“姐姐大人”登场."),
    "Plot.11003.1": ("Kỳ Nghỉ Tại Philae: Phần Ⅲ", "Chuẩn hóa địa danh Thành Phố Philae."),
    "Plot.11003.2": ("Muốn cùng bạn thưởng thức phong vị ấy, bởi nó từng gắn liền với những ký ức xưa.", "Trau chuốt câu từ sâu lắng, gợi cảm giác hoài niệm."),

    # 5. Iris (11101 - 11103)
    "Plot.11101.1": ("Đại Chiến Mua Sắm: Phần Ⅰ", "Dịch thoát ý sôi nổi, đúng chất 购物大作战."),
    "Plot.11101.2": ("Nguy to rồi! Đặt cược tất thảy, quyết cứu lấy tương lai của Iris!", "Sửa lỗi dịch ngược tai hại của máy dịch ('Mọi thứ đều ổn' -> 'Nguy to rồi/Đặt cược tất thảy'). Tuyệt đối giữ tên Iris."),
    "Plot.11102.1": ("Đại Chiến Mua Sắm: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.11102.2": ("Thời gian là sinh mệnh, tốc độ quyết định sống còn, dẫu có ngập ngừng cũng chẳng thể dừng bước!", "Khắc phục dịch vụn vặt từng chữ, câu văn nhịp nhàng dồn dập."),
    "Plot.11103.1": ("Đại Chiến Mua Sắm: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.11103.2": ("Gạt bỏ ủ rũ và muộn phiền sang một bên, đắm chìm trong hương thơm ngọt ngào của bơ và đường cát nào!", "Văn phong êm dịu, ấm áp đầy hương vị ngọt ngào."),

    # 6. Noya (11201 - 11203)
    "Plot.11201.1": ("Vòng Quay Tốc Độ: Phần Ⅰ", "Dịch chuẩn tên chương 极速环游."),
    "Plot.11201.2": ("Sau khi nâng cấp thành công Loxy, Noya nhiệt tình mời bạn cùng tham gia một chuyến dạo chơi “thư thái”.", "Giữ đúng tên xe Loxy và nhân vật Noya, diễn đạt dí dỏm."),
    "Plot.11202.1": ("Vòng Quay Tốc Độ: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.11202.2": ("Phong cách lái xe bạt mạng của nàng khiến bạn không khỏi lo lắng cho tính mạng. Và rồi, linh cảm chẳng lành ấy quả nhiên ứng nghiệm...", "Trau chuốt văn phong chân thực, giàu tính biểu cảm."),
    "Plot.11203.1": ("Vòng Quay Tốc Độ: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.11203.2": ("Các bạn bị cuốn vào một cuộc rượt đuổi nghẹt thở với đám quái xế. Giữa thời khắc ngàn cân treo sợi tóc, Noya đã đưa ra lựa chọn của mình...", "Tăng kịch tính cho trường đoạn cao trào thức tỉnh."),

    # 7. Shimiao (11301 - 11303)
    "Plot.11301.1": ("Chân Tình Trong Nồi Lẩu: Phần Ⅰ", "Dịch chuẩn tiêu đề 锅中见真情."),
    "Plot.11301.2": ("Ủy thác từ Shimiao: Điều tra vụ án... Khoan đã, sao nghe có vẻ nguy hiểm vậy?!", "Sửa lỗi dịch Commission thành 'Ủy ban' sang 'Ủy thác'."),
    "Plot.11302.1": ("Chân Tình Trong Nồi Lẩu: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.11302.2": ("Bước đầu phá án: Lần theo dấu vết hành tung của các Huyền Sư!", "Sửa lỗi dịch máy 'Huyền Thực' thành 'Huyền Sư' (玄师)."),
    "Plot.11303.1": ("Chân Tình Trong Nồi Lẩu: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.11303.2": ("Khi chân tướng vụ án vừa sáng tỏ, ủy thác mới lại bất ngờ ập đến?!", "Khắc phục câu chữ khô cứng, giữ nhịp điệu sinh động."),

    # 8. Chaton (11401 - 11403)
    "Plot.11401.1": ("Ủy Thác “Thử Thách Ma Vương”: Phần Ⅰ", "Sửa 'Ủy ban: Thử thách bạo chúa' thành 'Ủy Thác Thử Thách Ma Vương'."),
    "Plot.11401.2": ("Để giải phóng sức mạnh thực sự của bạn, Chaton mời bạn cùng thực hiện một ủy thác.", "Sửa 'làm nhiệm vụ' thành văn phong nhập vai chuẩn xác."),
    "Plot.11402.1": ("Ủy Thác “Thử Thách Ma Vương”: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.11402.2": ("Muốn bồi dưỡng quân đoàn Ma Vương, ắt phải rèn luyện ngay từ thuở ấu thơ.", "Sửa dịch thô 'bắt đầu từ trẻ' thành 'rèn luyện ngay từ thuở ấu thơ'."),
    "Plot.11403.1": ("Ủy Thác “Thử Thách Ma Vương”: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.11403.2": ("Tinh thần phấn chấn, phong độ đỉnh cao! Đây chính là thời cơ vàng để lập kỷ lục mới!", "Sửa lỗi calque ngớ ngẩn 'trên một cuộn' (on a roll) thành 'phong độ đỉnh cao'."),

    # 9. Firefly (11501 - 11503)
    "Plot.11501.1": ("Đi Tìm Bạn Mới: Phần Ⅰ", "Dịch tự nhiên theo bài ca thiếu nhi 找呀找呀找朋友."),
    "Plot.11501.2": ("Bạn quyết định giúp Firefly tìm một người bạn mới.", "Giữ chuẩn tên Firefly (không dịch thành Đom Đóm)."),
    "Plot.11502.1": ("Đi Tìm Bạn Mới: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.11502.2": ("Đã tìm thấy ứng viên bạn mới rồi! Nhưng mà... dường như có gì đó sai sai?", "Văn phong gần gũi, hóm hỉnh."),
    "Plot.11503.1": ("Đi Tìm Bạn Mới: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.11503.2": ("Trêu chọc, giận dỗi hờn ghen, rồi lại làm hòa trong chớp mắt.", "Nhịp câu gọn gàng, đậm chất tình bạn tuổi trẻ."),

    # 10. Ridge (11601 - 11603)
    "Plot.11601.1": ("Nhà Kính Phi Điển Hình: Phần Ⅰ", "Dịch chuẩn tiêu đề 非典型温室."),
    "Plot.11601.2": ("Được mời tới thăm nhà kính của Ridge, nhưng khoan đã... nơi này thực sự có thể gọi là nhà kính sao?", "Trau chuốt giọng điệu ngạc nhiên, dí dỏm."),
    "Plot.11602.1": ("Nhà Kính Phi Điển Hình: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.11602.2": ("Cùng Ridge tóm gọn những kẻ trộm lương thực. Hả? Hóa ra lũ trộm cũng có nỗi khổ tâm riêng.", "Sửa dịch máy thô 'vì sự cần thiết' thành 'có nỗi khổ tâm riêng'."),
    "Plot.11603.1": ("Nhà Kính Phi Điển Hình: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.11603.2": ("Nhờ Ridge thúc đẩy, đám đậu Hà Lan lớn nhanh như thổi, nhưng liệu thế này có quá khổng lồ không? Trời đất ơi, mầm đậu muốn nuốt chửng người kìa!", "Diễn đạt sống động, hài hước."),

    # 11. Jinglin (11701 - 11703)
    "Plot.11701.1": ("Kẹo Ngọt Nơi Lời Hẹn: Phần Ⅰ", "Dịch giàu chất thơ cho 糖果藏在约定里."),
    "Plot.11701.2": ("“Quán ăn trước mặt người chính là nhà hàng hút khách số một Philae đó nha!” — Tiểu điếm trưởng vừa phe phẩy đuôi vừa tự hào giới thiệu.", "Lời thoại nhân vật đáng yêu, chuẩn địa danh Philae."),
    "Plot.11702.1": ("Kẹo Ngọt Nơi Lời Hẹn: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.11702.2": ("Đánh bại cao thủ Long tộc trên bàn mạt chược ư? Thử thách này với Ma Vương chắc chắn chỉ là chuyện nhỏ!", "Sửa lỗi calque 'miếng bánh dễ ăn' (piece of cake) thành 'chuyện nhỏ', Loong thành Long tộc."),
    "Plot.11703.1": ("Kẹo Ngọt Nơi Lời Hẹn: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.11703.2": ("“Cảm ơn người... Đã chịu ở bên một kẻ lông bông như tôi~”", "Giữ trọn giọng điệu nũng nịu, ngọt ngào của Jinglin."),

    # 12. Coronis (11801 - 11803)
    "Plot.11801.1": ("Khối Xương Đen: Phần Ⅰ", "Dịch chuẩn sát nghĩa 黑色的骨头, tạo cảm giác kỳ bí."),
    "Plot.11801.2": ("Để xác nhận Ma Vương có thực sự mắc bệnh nan y hay không, mọi người trong lữ đoàn đã tới phòng khám của Coronis. Nhìn sắc mặt ba người họ, bạn chợt nhận ra dường như ngày tàn của mình đã cận kề...", "Văn phong nhập vai hồi hộp, dí dỏm."),
    "Plot.11802.1": ("Khối Xương Đen: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.11802.2": ("Được giữ lại dưỡng bệnh, bạn đã tận mắt chứng kiến y thuật cao siêu của Coronis. Sở hữu năng lực bực này, liệu nàng có thể cải tử hoàn sinh...", "Sửa 'lừa được tử thần' thành 'cải tử hoàn sinh' chuẩn văn phong anime."),
    "Plot.11803.1": ("Khối Xương Đen: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.11803.2": ("Trước phút chia tay, Coronis đã trao tặng bạn mẫu vật trân quý mà nàng cất giữ bấy lâu.", "Sửa 'ban tặng' nghe xa cách thành trao tặng trân trọng."),

    # 13. Nanoha (11901 - 11903)
    "Plot.11901.1": ("Nhiệm Vụ Bí Mật Của Hầu Gái: Phần Ⅰ", "Dịch chuẩn tiêu đề 女仆的秘密任务."),
    "Plot.11901.2": ("Nhiệm vụ hầu gái thứ nhất: Trao gửi ngọt ngào.", "Lời văn ngắn gọn, dễ thương."),
    "Plot.11902.1": ("Nhiệm Vụ Bí Mật Của Hầu Gái: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.11902.2": ("Nhiệm vụ hầu gái thứ hai: Đoạt giải thưởng lớn.", "Trau chuốt chuẩn xác."),
    "Plot.11903.1": ("Nhiệm Vụ Bí Mật Của Hầu Gái: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.11903.2": ("Nhiệm vụ hầu gái thứ ba: ...Lừa người thôi, làm gì có nhiệm vụ nào đâu!", "Bắt trọn cú 'quay xe' tinh nghịch của hầu gái ninja Nanoha."),

    # 14. Canace (12001 - 12003)
    "Plot.12001.1": ("Luận Án Bí Mật Sau Giờ Học: Phần Ⅰ", "Dịch chuẩn tiêu đề 课后的秘密论文."),
    "Plot.12001.2": ("Chưa từng nghe ai bảo Lữ Khách Tự Do mà cũng phải viết luận án cả!", "Sửa lỗi dịch 'write papers' thành 'viết báo' sang 'viết luận án', dùng chuẩn Lữ Khách Tự Do."),
    "Plot.12002.1": ("Luận Án Bí Mật Sau Giờ Học: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.12002.2": ("Đột phá! Bất ngờ!! Khách không mời mà đến!!!", "Giữ trọn 3 dấu chấm than dồn dập của nguyên tác."),
    "Plot.12003.1": ("Luận Án Bí Mật Sau Giờ Học: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.12003.2": ("Còn ai nhớ mục đích ban đầu chúng ta đến đây là để viết luận án không vậy?!", "Sửa 'viết báo' thành 'viết luận án', sắc thái dở khóc dở cười."),

    # 15. Ann (12301 - 12303)
    "Plot.12301.1": ("Tiểu Thủ Hộ Giả Mất Ngủ: Phần Ⅰ", "Dịch chuẩn tiêu đề 睡不着的小守护者."),
    "Plot.12301.2": ("Nghề thủ hộ giả bảo vệ rừng xanh làm gì có giới hạn tuổi tác đâu.", "Văn phong tự nhiên, trong sáng."),
    "Plot.12302.1": ("Tiểu Thủ Hộ Giả Mất Ngủ: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.12302.2": ("Xử lý bẫy rập, giã thuốc trị thương, giao tiếp với muông thú. Đừng ngạc nhiên, đây đều là kỹ năng bắt buộc cả đấy.", "Sửa 'mài thuốc' thành 'giã thuốc trị thương' chuẩn xác."),
    "Plot.12303.1": ("Tiểu Thủ Hộ Giả Mất Ngủ: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.12303.2": ("Chuyện gì nghĩ mãi không thông thì cứ ngủ một giấc đã, rồi sẽ có ngày thấu tỏ.", "Câu văn thấm thía, ấm áp."),

    # 16. Combatant (12501 - 12503)
    "Plot.12501.1": ("Quy Tắc Kẻ Thắng: Phần Ⅰ", "Dịch chuẩn tiêu đề 胜利者法则."),
    "Plot.12501.2": ("Cái giá phải trả để trở thành “khách mời đặc biệt” của Vạn Tống Ốc là gì?", "Chuẩn hóa tên tổ chức Vạn Tống Ốc (Post Haste)."),
    "Plot.12502.1": ("Quy Tắc Kẻ Thắng: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.12502.2": ("Khoảnh khắc thiếu nữ vung chiếc cự phủ, đại địa cũng phải rung chuyển.", "Sửa 'chiếc rìu vĩ đại/trái đất rung chuyển' thành văn phong hào tráng anime."),
    "Plot.12503.1": ("Quy Tắc Kẻ Thắng: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.12503.2": ("Lần này, người đứng phía đối diện trên lôi đài... chính là bạn.", "Tạo cảm giác đối đầu kịch tính nghẹt thở."),

    # 17. Teresa (12601 - 12603)
    "Plot.12601.1": ("Điệp Thuyết: Phần Ⅰ", "Dịch thoát nghĩa thanh lịch theo 蝶说."),
    "Plot.12601.2": ("Trên sân khấu hoa lệ của bậc thầy ảo thuật, hôm nay vinh hạnh mời bạn tới làm thượng khách.", "Sửa 'pháp sư' thành 'bậc thầy ảo thuật' (魔术大师) đúng ngữ cảnh."),
    "Plot.12602.1": ("Điệp Thuyết: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.12602.2": ("Cơ hội trở thành trợ lý thân cận của đại minh tinh, nhất định phải nắm thật chắc đấy.", "Văn phong gần gũi, khích lệ."),
    "Plot.12603.1": ("Điệp Thuyết: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.12603.2": ("Trút bỏ hào quang rực rỡ, nàng hé lộ cho bạn bí mật thực sự phía sau “ảo thuật”.", "Sửa 'phép thuật' thành 'ảo thuật', câu văn gợi mở lắng đọng."),

    # 18. Messenger (12701 - 12703)
    "Plot.12701.1": ("Tín Sứ Nhanh Nhẹn Bất Khả Thương Tổn: Phần Ⅰ", "Dịch chuẩn tiêu đề 机敏信使不会受伤."),
    "Plot.12701.2": ("Dẫu bảo đi đêm lắm có ngày gặp ma, thường đứng bên sông sao tránh khỏi ướt giày, nhưng thế này thì...", "Việt hóa thành ngữ mượt mà theo 常在河边走哪有不湿鞋."),
    "Plot.12702.1": ("Tín Sứ Nhanh Nhẹn Bất Khả Thương Tổn: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.12702.2": ("Luôn có những kẻ phát triển thiên phú kỳ lạ đến mức thượng thừa.", "Diễn đạt tự nhiên, hóm hỉnh."),
    "Plot.12703.1": ("Tín Sứ Nhanh Nhẹn Bất Khả Thương Tổn: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.12703.2": ("Băng cá nhân có thể che đi miệng vết thương, nhưng chẳng thể xóa nhòa sự thật rằng người đã bị tổn thương.", "Câu văn giàu cảm xúc, chạm tới trái tim."),

    # 19. Donna (13001 - 13003)
    "Plot.13001.1": ("Một Donna Khác Biệt: Phần Ⅰ", "Dịch chuẩn tiêu đề 不一样的多娜."),
    "Plot.13001.2": ("Tín sứ Donna thấu hiểu từng ngóc ngách của thị trấn, đó là một Donna mà bạn vốn quen thuộc.", "Khắc phục diễn đạt lủng củng của máy dịch."),
    "Plot.13002.1": ("Một Donna Khác Biệt: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.13002.2": ("Donna của Vạn Tống Ốc rất thích chải chuốt làm đẹp cho mọi người, nhìn kìa, đây là bộ trang phục mới do chính tay nàng may đó!", "Sửa đoạn sót tiếng Anh 'Donna of Vạn Tống Ốc loves to dress everyone up'."),
    "Plot.13003.1": ("Một Donna Khác Biệt: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.13003.2": ("Vậy Donna mà bạn đang thấy trước mắt, là phương diện nào của nàng đây?", "Câu hỏi gợi mở tâm tình thiếu nữ."),

    # 20. Delinquent Girl (13201 - 13203)
    "Plot.13201.1": ("Một Ngày Của Thiếu Nữ Cá Biệt: Phần Ⅰ", "Sửa lỗi dịch thô 'phạm pháp' thành 'thiếu nữ cá biệt' (不良少女)."),
    "Plot.13201.2": ("Hẹn đấu một trận cược cả danh dự lẫn địa bàn vốn là công việc thường nhật của thiếu nữ cá biệt.", "Sửa 'hạ bệ danh dự và địa vị' thành câu văn giàu cá tính đường phố."),
    "Plot.13202.1": ("Một Ngày Của Thiếu Nữ Cá Biệt: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.13202.2": ("Chiến trường giữa bút và giấy chính là giờ tăng ca tự nguyện của thiếu nữ cá biệt.", "Giữ nét tương phản thú vị trong tính cách nhân vật."),
    "Plot.13203.1": ("Một Ngày Của Thiếu Nữ Cá Biệt: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.13203.2": ("“Bom”, thêm nhiều “bom” nữa, chính là sở thích thầm kín của thiếu nữ cá biệt.", "Sửa câu sót tiếng Anh 'Phantom Bomb Rider are her secret hobby'."),

    # 21. Whispers (13301 - 13303)
    "Plot.13301.1": ("Lời Mật Ngọt Trong Gió: Phần Ⅰ", "Dịch thơ mộng theo 风中密语."),
    "Plot.13301.2": ("Ý nghĩa của chiếc chong chóng này là bí mật, tuyệt đối không nói cho người biết đâu.", "Diễn đạt nũng nịu, ngọt ngào."),
    "Plot.13302.1": ("Lời Mật Ngọt Trong Gió: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.13302.2": ("Lý do thực sự của việc đến muộn là bí mật, ta chỉ muốn san sẻ gánh nặng cùng người mà thôi.", "Khắc phục câu chữ vụng về của máy dịch."),
    "Plot.13303.1": ("Lời Mật Ngọt Trong Gió: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.13303.2": ("Những lời nói ngày hôm ấy là bí mật, rồi sẽ có một ngày ta giãi bày trọn vẹn chân tâm cùng người.", "Sửa đoạn sót tiếng Anh 'What I said that day is a secret'."),

    # 22. First Snow (13401 - 13403)
    "Plot.13401.1": ("Khi Tuyết Đầu Mùa Rơi: Phần Ⅰ", "Dịch thơ mộng theo 初雪来时."),
    "Plot.13401.2": ("Chuyến phiêu lưu tạm khép lại, trưởng thành mang theo những nỗi phiền muộn mới. Dưới làn tuyết bay tại Philae, bạn hội ngộ cùng thiếu nữ tóc trắng rụt rè năm ấy.", "Sửa câu sót tiếng Anh 'Growth has brought on new troubles', chuẩn địa danh Philae."),
    "Plot.13402.1": ("Khi Tuyết Đầu Mùa Rơi: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.13402.2": ("Nỗ lực của nàng tuy vụng về nhưng lại vô cùng chân thành, đổi thay đang thầm lặng diễn ra tự lúc nào chẳng hay.", "Sửa câu sót tiếng Anh 'Her efforts may be clumsy, but they're sincere'."),
    "Plot.13403.1": ("Khi Tuyết Đầu Mùa Rơi: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.13403.2": ("Dùng bài diễn thuyết trên lễ đài để cáo biệt quá khứ, dưới sự đồng hành chở che của bạn, nàng đã giãi bày trọn vẹn con người thật của mình.", "Văn phong truyền cảm, giàu tính nhân văn."),

    # 23. Witch Interview (13501 - 13503)
    "Plot.13501.1": ("Phỏng Vấn Đặc Biệt Của Ma Nữ: Phần Ⅰ", "Dịch chuẩn tiêu đề 魔女的特别专访."),
    "Plot.13501.2": ("Cảm nhận thấy luồng khí lạnh sau gáy, bạn phát hiện Ma Nữ đang lén lút tiếp cận — hóa ra nàng đang toan tính giật tít một tin giật gân!", "Sửa 'mụ ta' thành danh xưng Ma Nữ vừa quyến rũ vừa bí ẩn."),
    "Plot.13502.1": ("Phỏng Vấn Đặc Biệt Của Ma Nữ: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.13502.2": ("Ma Vương cùng Ma Nữ hẹn gặp phỏng vấn riêng tư, kẻ gian bí ẩn bỗng dưng chen ngang phá rối!", "Sửa 'ông chủ và phù thủy' thành 'Ma Vương cùng Ma Nữ' đúng bối cảnh."),
    "Plot.13503.1": ("Phỏng Vấn Đặc Biệt Của Ma Nữ: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.13503.2": ("Sau cuộc trải lòng chân thành với Ma Nữ! Bí mật đặc biệt nhất của cả hai sắp sửa được hé lộ nơi đây!", "Tạo kịch tính và cảm giác thắt chặt mối quan hệ."),

    # 24. Junior's Troubles (13701 - 13703)
    "Plot.13701.1": ("Ngày Phiền Muộn Của Hậu Bối (Phần Ⅰ)", "Dịch sát nghĩa 后辈的烦恼日."),
    "Plot.13701.2": ("Vô tình lạc bước vào buổi trà thoại của các thiên kim tiểu thư... dường như bạn đã thấy được một khía cạnh khác nơi nàng.", "Văn phong lịch thiệp, quý phái."),
    "Plot.13702.1": ("Ngày Phiền Muộn Của Hậu Bối (Phần Ⅱ)", "Chuẩn hóa tiêu đề chương."),
    "Plot.13702.2": ("Kẻ quá mức nghiêm túc rất dễ tự dồn ép bản thân tới giới hạn chịu đựng.", "Câu từ sâu sắc, thấu hiểu tâm lý."),
    "Plot.13703.1": ("Ngày Phiền Muộn Của Hậu Bối (Phần Ⅲ)", "Chuẩn hóa tiêu đề chương."),
    "Plot.13703.2": ("Hãy nắm lấy bàn tay nàng, cùng khiêu vũ một vũ điệu lộng lẫy say đắm lòng người!", "Tăng tính lãng mạn cho trường đoạn khiêu vũ."),

    # 25. Allie (13901 - 13903)
    "Plot.13901.1": ("Trò Chơi Kết Hôn: Phần Ⅰ", "Dịch chuẩn tiêu đề 结婚过家家."),
    "Plot.13901.2": ("Dẫu đã trở thành mẹ, nhưng Allie chưa từng yêu đương, cũng chưa từng kết hôn... Liệu một người như nàng có thể thực sự trở thành “người mẹ” không?", "Sửa câu sót tiếng Anh 'Can she really call herself one?'."),
    "Plot.13902.1": ("Trò Chơi Kết Hôn: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.13902.2": ("Dù không giỏi việc nhà, dù chưa từng mang nặng đẻ đau, Allie vẫn sẽ là một “người mẹ đích thực”.", "Khắc phục diễn đạt máy dịch, giữ trọn tình cảm ấm áp."),
    "Plot.13903.1": ("Trò Chơi Kết Hôn: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.13903.2": ("Dù ốm đau hay khỏe mạnh, dù nghèo khó hay giàu sang, hai người cùng nguyện thề sẽ mãi mãi yêu thương, kính trọng và chở che cho nhau.", "Sửa câu sót tiếng Anh 'For richer or poorer, in sickness and in health'."),

    # 26. Sparkla (14001 - 14003)
    "Plot.14001.1": ("Nỗi Phiền Não Của Sparkla: Phần I", "Chuẩn hóa tiêu đề theo tên Sparkla."),
    "Plot.14001.2": ("Nhà phát minh thiên tài bất ngờ rơi vào giai đoạn cạn kiệt ý tưởng, biết đi đâu để tìm nguồn cảm hứng mới bây giờ?", "Sửa 'bức tường sáng tạo' thành 'cạn kiệt ý tưởng' tự nhiên."),
    "Plot.14002.1": ("Nỗi Phiền Não Của Sparkla: Phần II", "Chuẩn hóa tiêu đề chương."),
    "Plot.14002.2": ("Ta chỉ công nhận những ai thực sự hiểu được các phát minh của ta thôi nha~", "Sửa 'thừa nhận' thành 'công nhận', giữ sắc thái nhí nhảnh."),
    "Plot.14003.1": ("Nỗi Phiền Não Của Sparkla: Phần III", "Chuẩn hóa tiêu đề chương."),
    "Plot.14003.2": ("Ma Vương, người muốn thêm tính năng gì vào Bánh Phái Ma Vương nào? Ta đây đều chiều được hết nhé~", "Sửa 'Sếp' thành 'Ma Vương', 'Tyrant Pie' thành 'Bánh Phái Ma Vương'."),

    # 27. Haunted Village (14101 - 14103)
    "Plot.14101.1": ("Kinh Hoàng Thôn Hoang: Phần Ⅰ", "Dịch chuẩn tiêu đề 荒村惊魂."),
    "Plot.14101.2": ("Thôn làng hoang phế ngoài thành liên tục xảy ra chuyện quái dị, dấy lên nghi vấn có “ma ám”. Vị Huyền Sư nhát gan nhận lệnh lúc hiểm nghèo, nhưng vừa đặt chân tới đầu thôn đã la hét thất thanh—", "Sửa lỗi máy dịch 'Huyền Thực hèn nhát được giao nhiệm vụ xảy ra vụ việc' thành câu văn kiếm hiệp kỳ bí."),
    "Plot.14102.1": ("Kinh Hoàng Thôn Hoang: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.14102.2": ("Liệu cuốn nhật ký cũ kỹ có ghi lại niềm nuối tiếc khôn nguôi về hôn lễ dang dở ấy chăng? Bóng đen kỳ dị thoắt ẩn thoắt hiện, chẳng lẽ thực sự có “ma”?", "Trau chuốt văn phong ma mị, gợi mở."),
    "Plot.14103.1": ("Kinh Hoàng Thôn Hoang: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.14103.2": ("Bí mật giấu kín trong màn đêm rốt cuộc là “ma quái” tác oai hay do con người trêu đùa? Ánh nến chập chờn rọi sáng đoạn dĩ vãng phủ dưới tấm lụa đỏ thắm.", "Văn phong giàu chất điện ảnh cổ phong."),

    # 28. The Date (14201 - 14203)
    "Plot.14201.1": ("Sóng Gió “Hẹn Hò”: Phần Ⅰ", "Sửa lỗi dịch máy tai hại 'Ngày, Phần Ⅰ' (Date = ngày) thành 'Sóng Gió Hẹn Hò'."),
    "Plot.14201.2": ("Bảo là lời mời hẹn hò... nhưng tuyệt đối chẳng phải là buổi hẹn hò bình thường đâu nhỉ?!", "Khắc phục diễn đạt vụng về."),
    "Plot.14202.1": ("Sóng Gió “Hẹn Hò”: Phần Ⅱ", "Sửa lỗi dịch Date thành Ngày."),
    "Plot.14202.2": ("Luôn phải khắc ghi mục đích hàng đầu của cuộc “hẹn hò” này là thám thính tin tức... Ơ kìa?? Thức uống gì thế này??!", "Bắt trọn phản ứng bất ngờ, ngơ ngác."),
    "Plot.14203.1": ("Sóng Gió “Hẹn Hò”: Phần Ⅲ", "Sửa lỗi dịch Date thành Ngày."),
    "Plot.14203.2": ("Cuộc “hẹn hò” này dường như cũng vui vẻ đấy chứ... Chết dở! Quên béng mất nhiệm vụ rồi!", "Giọng điệu hài hước, tự nhiên."),

    # 29. The You I Know (14301 - 14303)
    "Plot.14301.1": ("Người Mà Ta Từng Biết: Phần Ⅰ", "Dịch chuẩn tiêu đề 我所认识的你."),
    "Plot.14301.2": ("Chiến binh tinh nhuệ ắt cũng có chiếc dạ dày tinh nhuệ... Hả? Sao bảo quên ăn cơm mà suýt nữa chết đói vậy?", "Khắc phục câu chữ dịch thô kiểu 'sự thèm ăn ưu tú'."),
    "Plot.14302.1": ("Người Mà Ta Từng Biết: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.14302.2": ("Bảo là đi săn chút đồ rừng, nhưng nguyên cả con GẤU to tướng này là thế nào đây?!", "Khắc phục dịch máy 'toàn bộ GẤU này là sao'."),
    "Plot.14303.1": ("Người Mà Ta Từng Biết: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.14303.2": ("Phải cởi ra sao!? Ngay bây giờ!? Ở ngay chỗ này á?!", "Bắt trọn sự hoảng hốt bối rối tột độ của tình huống."),

    # 30. Chitose (14401 - 14403)
    "Plot.14401.1": ("Tu Luyện Nhân Đao Hợp Nhất: Phần Ⅰ", "Dịch chuẩn tiêu đề 人刀合一的修行."),
    "Plot.14401.2": ("Tình cờ chạm mặt Chitose trên phố, rồi hai người trò chuyện về việc tu luyện cảnh giới “Nhân Đao Hợp Nhất”...", "Sửa 'trạng thái Đồng nhất' thành 'cảnh giới Nhân Đao Hợp Nhất'."),
    "Plot.14402.1": ("Tu Luyện Nhân Đao Hợp Nhất: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.14402.2": ("Tương truyền nếu nín thở ngưng thần, nhìn sâu vào mắt nhau thì tâm ý sẽ tương thông... Liệu hai kẻ vốn luôn lệch nhịp có thể nỗ lực thành công?", "Trau chuốt nhịp văn kiếm hiệp tình duyên mượt mà."),
    "Plot.14403.1": ("Tu Luyện Nhân Đao Hợp Nhất: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.14403.2": ("Mưa như trút nước, nàng thoáng chút ủ rũ tiêu điều. Khoảnh khắc ấy, bạn chợt nhận ra trách nhiệm thiêng liêng với tư cách là “Kẻ Cầm Đao”...", "Sửa lỗi dịch máy tai hại 'Người cầm quyền' thành 'Kẻ Cầm Đao' (持刀人)."),

    # 31. Myriad Faces (14501 - 14503)
    "Plot.14501.1": ("Diễn Viên Nghìn Mặt I", "Sửa lỗi ngớ ngẩn 'Ca sĩ thể hiện Myriad Faces I'."),
    "Plot.14501.2": ("Mang theo tâm đồ khó lường, nàng dầy công sắp đặt một cuộc hội ngộ tình cờ.", "Sửa dịch thô 'những thiết kế ẩn giấu thiết kế lối đi'."),
    "Plot.14502.1": ("Diễn Viên Nghìn Mặt II", "Sửa Myriad Faces thành Diễn Viên Nghìn Mặt."),
    "Plot.14502.2": ("Bạn bước theo từng chỉ dẫn của nàng, từng bước dấn thân lên sân khấu đã sớm được bài trí công phu.", "Khắc phục diễn đạt cứng nhắc."),
    "Plot.14503.1": ("Diễn Viên Nghìn Mặt III", "Sửa Myriad Faces thành Diễn Viên Nghìn Mặt."),
    "Plot.14503.2": ("Sau khi bức màn nhung khép lại, chân thật và dối trá, rốt cuộc biết phân định làm sao?", "Câu hỏi triết lý lắng đọng đầy ám ảnh."),

    # 32. Caramel (14701 - 14703)
    "Plot.14701.1": ("Dư Âm Giữa Sao Trời Và Trái Tim: Phần Ⅰ", "Dịch thơ mộng theo 星与心的回响."),
    "Plot.14701.2": ("Tiếp nhận ủy thác “chữa lành vết thương lòng cho các Lữ Khách”, Ma Vương đang phiền muộn bỗng bắt gặp một giai điệu thân quen tại Flavio...", "Sửa 'Lữ Khách đầy chiến tranh/một Boss gặp rắc rối' thành câu văn nhập vai mượt mà."),
    "Plot.14702.1": ("Dư Âm Giữa Sao Trời Và Trái Tim: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.14702.2": ("Caramel nhờ bạn làm nhà sản xuất cho nàng, và câu trả lời để tìm kiếm nguồn cảm hứng mà bạn đưa ra là...", "Khắc phục lối dịch dịch vụn chữ."),
    "Plot.14703.1": ("Dư Âm Giữa Sao Trời Và Trái Tim: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.14703.2": ("Tại Doanh Trại Lữ Khách dưới chân Cự Tháp, bạn và Caramel cùng bước lên sân khấu. Huyền thoại tiếp theo của Flavio sắp sửa được viết nên nơi đây...", "Sửa 'Lữ Khách Camp' thành Doanh Trại Lữ Khách, giữ chuẩn Cự Tháp."),

    # 33. Collar and Rope (14901 - 14903)
    "Plot.14901.1": ("Vòng Cổ Và Dây Thừng: Phần Ⅰ", "Dịch chuẩn tiêu đề 项圈与绳索."),
    "Plot.14901.2": ("Một đoạn nghiệt duyên chẳng thể dứt bỏ, một cuộc tái ngộ ngoài mọi dự liệu.", "Dịch thoát nghĩa sâu sắc theo 一段无法斩断的孽缘."),
    "Plot.14902.1": ("Vòng Cổ Và Dây Thừng: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.14902.2": ("Đằng sau ánh mắt cuồng loạn bất kham, cợt nhã thế gian ấy, ẩn giấu bí mật ghê gớm đến mức nào?", "Văn phong gai góc, bí ẩn."),
    "Plot.14903.1": ("Vòng Cổ Và Dây Thừng: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.14903.2": ("Dây cương của định mệnh đã trao trọn vào tay bạn, bạn sinh ra là để thuần hóa con quái thú đói khát trước mắt này.", "Khắc phục câu dịch máy khô cứng."),

    # 34. Laru (15001 - 15003)
    "Plot.15001.1": ("Rắc Rối Khoai Tây Chiên: Phần Ⅰ", "Sửa lỗi dịch máy buồn cười 'Món chiên tuyệt vời' (Fry-tastrophe) thành 'Rắc Rối Khoai Tây Chiên'."),
    "Plot.15001.2": ("Giờ trốn việc đi câu cá không bàn chuyện công vụ nha, nhưng nếu người câu được cá thì Laru sẵn lòng lắng nghe đôi chút~", "Bắt trọn tính cách lười biếng, tinh nghịch của Laru."),
    "Plot.15002.1": ("Rắc Rối Khoai Tây Chiên: Phần Ⅱ", "Sửa lỗi dịch Fry-tastrophe."),
    "Plot.15002.2": ("Dù chỉ câu được cọng rong cũng không tính là tay trắng ra về, cơ mà bảo đặt hàng khoai tây chiên, khoai tây chiên gì cơ chứ?!", "Dịch thoát nghĩa thuật ngữ câu cá 空军 thành 'tay trắng ra về'."),
    "Plot.15003.1": ("Rắc Rối Khoai Tây Chiên: Phần Ⅲ", "Sửa lỗi dịch Fry-tastrophe."),
    "Plot.15003.2": ("Chuyện đã đến nước này, tương lai của Laru chỉ còn biết trông cậy vào người thôi đấy...!", "Diễn đạt cầu cứu vừa đáng thương vừa hài hước."),

    # 35. Nostalgic Scent (15501 - 15503)
    "Plot.15501.1": ("Dấu Vết Hương Thơm Kỷ Niệm: Phần Ⅰ", "Dịch thơ mộng theo 气味的痕迹."),
    "Plot.15501.2": ("Hương thơm vương vấn trong ngọn gió biển, khơi dậy những hoài niệm khôn nguôi.", "Khắc phục câu chữ dịch thô vụn vặt."),
    "Plot.15502.1": ("Dấu Vết Hương Thơm Kỷ Niệm: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.15502.2": ("Mùi hương từng vang vọng khắp ngõ ngách phố xưa, nay đã tan biến tự thuở nào.", "Văn phong hoài niệm man mác buồn."),
    "Plot.15503.1": ("Dấu Vết Hương Thơm Kỷ Niệm: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.15503.2": ("Mùi hương áp sát sau lưng người, vĩnh viễn chẳng hề phai nhạt.", "Gợi mở cảm giác gắn bó kề cận ấm áp."),

    # 36. Big Cleanup (15601 - 15603)
    "Plot.15601.1": ("Tổng Vệ Sinh Căn Phòng Nhỏ: Phần Ⅰ", "Dịch chuẩn tiêu đề 小房间大扫除."),
    "Plot.15601.2": ("Tử thần đã tuyên án phán quyết cuối cùng, sự hủy diệt cận kề. Đúng lúc ấy, người đó đã xuất hiện.", "Sửa 'Death K' thành 'Tử thần' (死神), tăng sức nặng kịch tính."),
    "Plot.15602.1": ("Tổng Vệ Sinh Căn Phòng Nhỏ: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.15602.2": ("Dẫu đôi mắt bị dục vọng che mờ, linh hồn bị thời gian dày vò, người đó vẫn chưa từng chùn bước.", "Trau chuốt văn phong hào hùng, kiên định."),
    "Plot.15603.1": ("Tổng Vệ Sinh Căn Phòng Nhỏ: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.15603.2": ("Nguy cơ đã được hóa giải. Dõi theo dấu chân người ấy, chuyến phiêu lưu của nàng chỉ vừa mới bắt đầu.", "Khép lại chương bằng niềm hy vọng rạng ngời."),

    # 37. Three-Legged Race (15701 - 15703)
    "Plot.15701.1": ("Cuộc Đua Hai Người Ba Chân Ⅰ", "Dịch chuẩn tên trò chơi 二人三脚 (cuộc đua hai người ba chân)."),
    "Plot.15701.2": ("Để tạo cho Shia một bất ngờ lớn, cố lên nào Karin — Khoan đã! Không phải đi hướng đó đâu!", "Khắc phục diễn đạt máy dịch, giữ sự sôi nổi đáng yêu."),
    "Plot.15702.1": ("Cuộc Đua Hai Người Ba Chân Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.15702.2": ("Dù kỹ năng sở trường tự hào bị phong ấn cũng chớ lo lắng, chẳng phải nơi đây vẫn còn một người nữa kề bên sao~", "Sửa 'kỹ năng chữ ký' (signature skill) thành 'kỹ năng sở trường'."),
    "Plot.15703.1": ("Cuộc Đua Hai Người Ba Chân Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.15703.2": ("Tới vạch đích rồi, dĩ nhiên phải thưởng một chút chứ. Nhưng phản ứng ngượng ngùng của nàng cũng là một “mỹ vị” khác đấy nha~", "Dịch tinh tế theo 她的反应也是另一种美味."),

    # 38. Gifts on Delivery (15801 - 15803)
    "Plot.15801.1": ("Món Quà Chuyển Phát: Phần Ⅰ", "Dịch chuẩn tiêu đề 派送的礼物."),
    "Plot.15801.2": ("Lễ Nguyện Tuyết đã qua đi, nhưng công việc thì không bao giờ kết thúc, nhiệm vụ mới lại là... Hả? Đại pháo á?!", "Sửa 'Lễ hội Tuyết' thành 'Lễ Nguyện Tuyết' (雪愿节)."),
    "Plot.15802.1": ("Món Quà Chuyển Phát: Phần Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.15802.2": ("Lần đầu thử nghiệm hệ thống chuyển phát bằng đại pháo, khoang hàng bắn đi rồi... sao lại bay ngược trở về thế này?!", "Diễn đạt hài hước, đúng chất anime."),
    "Plot.15803.1": ("Món Quà Chuyển Phát: Phần Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.15803.2": ("Nếu món quà tri ân chính là bản thân tôi... thì dĩ nhiên chỉ là nói đùa thôi nha!", "Bắt trọn sự lém lỉnh, trêu chọc của nhân vật."),

    # 39. Secret Digestive Recipe (15901 - 15903)
    "Plot.15901.1": ("Bí Phương Tiêu Thực I", "Dịch chuẩn tiêu đề 消食秘方."),
    "Plot.15901.2": ("Tới Thương Ngô nghỉ dưỡng, nàng lại thuận tay kê thêm vài đơn thuốc.", "Sửa 'Thương Ô' thành 'Thương Ngô' (苍梧) chuẩn Hán-Việt."),
    "Plot.15902.1": ("Bí Phương Tiêu Thực II", "Chuẩn hóa tiêu đề chương."),
    "Plot.15902.2": ("Chỉ vì một chén trà tiêu thực mà bác sĩ rơi vào thế tiến thoái lưỡng nan — “Trợ lý” ơi, mau tới cứu nàng một tay!", "Diễn đạt dí dỏm, sống động."),
    "Plot.15903.1": ("Bí Phương Tiêu Thực III", "Chuẩn hóa tiêu đề chương."),
    "Plot.15903.2": ("Nhắc tới thuật dưỡng sinh trứ danh nhất của Long tộc — thì tự nhiên phải là xoa bóp bấm huyệt rồi.", "Sửa 'người Loong' thành 'Long tộc' theo văn phong phương Đông."),

    # 40. A Hustling Holiday (16001 - 16003)
    "Plot.16001.1": ("Kỳ Nghỉ Bận Rộn Ⅰ", "Dịch chuẩn tiêu đề 奔忙的假期."),
    "Plot.16001.2": ("Kỳ nghỉ quý giá vừa bắt đầu, nhưng sự đời chẳng như mong muốn, những biến cố bất ngờ lại lấp kín toàn bộ thời gian.", "Sửa lỗi máy dịch 'bùng nổ với những bộ phim ngẫu nhiên' (random drama)."),
    "Plot.16002.1": ("Kỳ Nghỉ Bận Rộn Ⅱ", "Chuẩn hóa tiêu đề chương."),
    "Plot.16002.2": ("Công việc ư?? Nghỉ dưỡng ư?? Đừng hòng mơ tưởng nữa, lại có biến cố mới xảy ra rồi kìa!", "Sửa lỗi OCR/dịch máy 'Ⅴđịa điểm'."),
    "Plot.16003.1": ("Kỳ Nghỉ Bận Rộn Ⅲ", "Chuẩn hóa tiêu đề chương."),
    "Plot.16003.2": ("Đây là một kỳ nghỉ hiếm có khó tìm, chi bằng tạm gác lại bộn bề công việc mà tận hưởng ngày nghỉ đi nào.", "Khắc phục câu dịch máy 'kỳ nghỉ khó đến/dừng lại một lần'."),
}

# For Story (57 items)
STORY_MAP = {
    "Story.1010.2": ("Tựa thành đồng lũy sắt, nàng sừng sững hiên ngang chẳng hề lay chuyển.", "Trau chuốt câu từ hào sảng, giàu chất kiên định anime RPG."),
    "Story.106.2": ("Đây là câu chuyện của nàng, và cũng là khúc ca của Khu Tro Tàn.", "Sửa thuật ngữ chuẩn Khu Tro Tàn (Ash District)."),
    "Story.1101.1": ("Tái Hiện Ngày Qua", "Dịch tiêu đề còn sót tiếng Anh theo 昨日重现."),
    "Story.1101.2": ("Thêm một lần tỉnh giấc, lại mở ra một kiếp nhân sinh mới.", "Dịch câu cốt truyện còn sót tiếng Anh theo 又一次醒来，又一段新的人生."),
    "Story.1102.1": ("Đứa Con Bị Rừng Sâu Ruồng Bỏ", "Dịch tiêu đề còn sót tiếng Anh theo 森林弃子."),
    "Story.1102.2": ("Nàng lao về phía trước — dáng hình dứt khoát và sắc lạnh.", "Dịch câu cốt truyện còn sót tiếng Anh theo 她冲了上去——身影果决而凌厉."),
    "Story.1103.1": ("Thành Trì Hoàn Mỹ", "Dịch tiêu đề còn sót tiếng Anh theo 完璧之城."),
    "Story.1103.2": ("Vật đổi sao dời, trên phố phường chẳng còn bóng hình cảnh sắc thân quen...", "Dịch câu cốt truyện còn sót tiếng Anh theo 物是人非，街道上并没有你熟悉的风景……"),
    "Story.1104.1": ("Nhà Tắm và Kẻ Nô Lệ", "Dịch tiêu đề còn sót tiếng Anh theo 浴场与奴隶."),
    "Story.1104.2": ("“Nguyện người dẫn lối đưa các bạn đồng hành của ta lên tận trời cao...”", "Dịch câu cốt truyện còn sót tiếng Anh theo “愿你将我的同伴接入高天之上……”"),
    "Story.1105.1": ("Thử Nghiệm Nhà Tắm", "Dịch tiêu đề còn sót tiếng Anh theo 浴场测试."),
    "Story.1105.2": ("Ma lực tràn trề, nhưng bụng dạ lại trống rỗng...", "Dịch câu cốt truyện còn sót tiếng Anh theo 魔力满满，胃里空空……"),
    "Story.1106.1": ("Insula", "Địa danh Insula giữ nguyên theo nguyên tác 因苏拉."),
    "Story.1106.2": ("Mảnh đất đâm chồi từ tuyệt vọng chẳng thể nào gặt hái được hy vọng.", "Dịch câu cốt truyện còn sót tiếng Anh theo 以绝望为基的土地并不能收获希望."),
    "Story.1107.1": ("Ý Nghĩa Của Thánh Nữ", "Dịch tiêu đề còn sót tiếng Anh theo 圣女的意义."),
    "Story.1107.2": ("“Vận mệnh sinh ra là để xoay chuyển.”", "Dịch câu cốt truyện còn sót tiếng Anh theo “命运就是用来改变的。”"),
    "Story.1108.1": ("Ngày Thường Của Người Gác Đêm", "Dịch tiêu đề còn sót tiếng Anh theo 守夜人的日常."),
    "Story.1108.2": ("Người đẹp vì lụa, là bởi vì... nơi đây người ta chỉ nhìn vào xiêm y.", "Dịch câu cốt truyện còn sót tiếng Anh theo 人靠衣装，是因为……这里只看得见衣装."),
    "Story.1109.1": ("Nguyện Ước Cấm Kỵ", "Dịch tiêu đề còn sót tiếng Anh theo 禁忌的愿望."),
    "Story.1109.2": ("— Chôn sâu cùng với nó chính là quá khứ và vết thương lòng của nàng.", "Dịch câu cốt truyện còn sót tiếng Anh theo ——与此一同深埋的是，她的过去与伤痛."),
    "Story.1110.1": ("Đấu Sĩ", "Dịch tiêu đề còn sót tiếng Anh theo 角斗士."),
    "Story.1110.2": ("“Xin lỗi... Chúng ta rõ ràng đã thắng mà. Đáng lẽ chúng ta đã chiến thắng rồi mới phải...”", "Dịch câu cốt truyện còn sót tiếng Anh theo “对不起……我们明明赢了。明明已经赢了才对……”"),
    "Story.1111.1": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1111.2": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1112.1": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1112.2": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1113.1": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1113.2": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1114.1": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1114.2": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1115.1": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1115.2": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1116.1": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1116.2": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1117.1": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1117.2": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1118.1": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1118.2": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1119.1": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1119.2": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1120.1": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1120.2": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1121.1": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1121.2": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1122.1": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1122.2": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1123.1": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.1123.2": ("Xin hãy chờ đón", "Dịch Stay tuned còn sót tiếng Anh theo 敬请期待."),
    "Story.305.1": ("Vita", "Tên nhân vật Vita giữ nguyên theo Project Glossary."),
    "Story.504.4": ("Khúc Đệm Chuyển Tiếp", "Dịch chuẩn tiêu đề 幕间 (Interlude)."),
    "Story.515.1": ("Joseph", "Tên nhân vật Joseph giữ nguyên theo Project Glossary."),
    "Story.617.1": ("Firenze", "Tên nhân vật Firenze giữ nguyên theo Project Glossary."),
    "Story.621.2": ("Nàng nuốt trọn bao ngọn lửa hận hờn, để rồi tiếng gầm thét chợt tắt lịm ngay khoảnh khắc ấy.", "Khắc phục câu dịch máy thô 'nuốt chửng quá nhiều ngọn lửa thịnh nộ'."),
    "Story.804.1": ("Bảo Hiểm Thiên Khung", "Dịch chuẩn danh xưng tổ chức Thiên Khung (Omnisky Aegis - 天穹保险)."),
    "Story.816.2": ("Giữa màn sương biến ảo khôn lường, nàng vẫn luôn là bến đỗ bình yên cho tâm hồn bạn.", "Trau chuốt văn phong sâu sắc, giàu hình ảnh gợi cảm."),
    "Story.818.2": ("Cuối cùng, nàng cũng đã cùng bạn chung ngắm trọn vẹn bầu trời này.", "Sửa lỗi dịch máy thô 'chia sẻ bầu trời' thành 'cùng bạn chung ngắm trọn vẹn bầu trời'."),
    "Story.903.2": ("Rút quyền trượng này, chỉ vì muốn thấu tỏ chân tâm của người.", "Sửa lỗi dịch calque tai hại 'Tôi vẽ vương trượng này' (draw scepter) thành 'Rút quyền trượng này'."),
}

# For StarTowerTalk (120 items)
# All are NPC speaker tags: Portia, Beatrixa, Bernina, Virigia
STT_MAP = {
    "Portia": ("Portia", "Giữ nguyên tên nhân vật Portia theo Project Glossary."),
    "Beatrixa": ("Beatrixa", "Giữ nguyên tên nhân vật Beatrixa theo Project Glossary."),
    "Bernina": ("Bernina", "Giữ nguyên tên nhân vật Bernina theo Project Glossary."),
    "Virigia": ("Virigia", "Giữ nguyên tên nhân vật Virigia theo Project Glossary."),
}

input_path = "StellaSora_VietHoa/work/batches/dialogue_batch6_awakening_talk.json"
output_path = "StellaSora_VietHoa/work/batches/dialogue_batch6_awakening_talk_approved.json"

data = json.load(open(input_path, encoding="utf-8"))
print(f"Loaded {len(data)} items from {input_path}")

approved_list = []
missing_keys = []

for idx, it in enumerate(data):
    tbl = it["table"]
    key = it["key"]
    en = it["en"]
    zh = it.get("zh", "")
    before = it.get("current_vi", "")

    approved_vi = ""
    reason = ""

    if tbl == "Plot":
        if key in PLOT_MAP:
            approved_vi, reason = PLOT_MAP[key]
        else:
            missing_keys.append((tbl, key, en))
    elif tbl == "Story":
        if key in STORY_MAP:
            approved_vi, reason = STORY_MAP[key]
        else:
            missing_keys.append((tbl, key, en))
    elif tbl == "StarTowerTalk":
        if en in STT_MAP:
            approved_vi, reason = STT_MAP[en]
        else:
            missing_keys.append((tbl, key, en))
    else:
        missing_keys.append((tbl, key, en))

    approved_list.append({
        "table": tbl,
        "key": key,
        "en": en,
        "zh": zh,
        "before": before,
        "approved_vi": approved_vi,
        "reason": reason
    })

if missing_keys:
    print(f"ERROR: {len(missing_keys)} missing keys!")
    for mk in missing_keys[:10]:
        print("  -", mk)
else:
    print(f"SUCCESS: All {len(approved_list)} items mapped perfectly!")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(approved_list, f, ensure_ascii=False, indent=2)
    print(f"Wrote approved output to {output_path}")
