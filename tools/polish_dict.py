#!/usr/bin/env python3
"""Polisher for DictionaryDiagram table (430 items).
Applies Master Glossary, fixes machine translation artifacts,
ensures 100% token preservation, and natural Vietnamese phrasing.
"""

import json
import re
from pathlib import Path
from token_validator import extract_tokens

def polish_dict_entries(items):
    """Takes list of DictionaryDiagram items and returns dict {key: polished_vi}."""
    
    # Custom exact mappings for critical sections
    EXACT_MAP = {
        "DictionaryDiagram.10010101.1": "Tổng Quan Lữ Khách",
        "DictionaryDiagram.10010101.2": "Mỗi Lữ Khách đều sở hữu <color=#0abec5>Thuộc Tính Nguyên Tố</color> và <color=#0abec5>Phong Cách Tác Chiến</color> riêng biệt. Hãy kết giao với nhiều Lữ Khách hơn và linh hoạt phối hợp đội hình để vượt qua muôn vàn thử thách.",
        "DictionaryDiagram.10020101.1": "Tăng Cấp",
        "DictionaryDiagram.10020101.2": "Dùng đạo cụ EXP để nâng <color=#0abec5>Cấp Lữ Khách</color>, gia tăng đáng kể các thuộc tính cơ bản.",
        "DictionaryDiagram.10020102.1": "Đột Phá Bậc",
        "DictionaryDiagram.10020102.2": "Mỗi khi Lữ Khách tăng <color=#0abec5>10</color> cấp sẽ đạt giới hạn cấp độ.\nTiêu hao nguyên liệu để tiến hành <color=#0abec5>Đột Phá Bậc</color>, gia tăng thuộc tính và <color=#0abec5>mở khóa giới hạn cấp độ mới</color>.",
        "DictionaryDiagram.10020103.1": "Thức Tỉnh",
        "DictionaryDiagram.10020103.2": "Khi Lữ Khách đạt <color=#0abec5>Bậc 3</color>, sẽ mở khóa <color=#0abec5>Ngoại Hình Thức Tỉnh</color> hoàn toàn mới và có thể cài đặt làm hình nền Sảnh Chờ.",
        "DictionaryDiagram.10030101.1": "Tổng Quan Kỹ Năng",
        "DictionaryDiagram.10030101.2": "Mỗi Lữ Khách sở hữu bộ kỹ năng khác nhau, phân loại thành:\nĐòn Đánh Thường, Kỹ Năng Chủ Động, Kỹ Năng Hỗ Trợ và Tuyệt Kỹ.",
        "DictionaryDiagram.10030102.1": "Cường Hóa Kỹ Năng",
        "DictionaryDiagram.10030102.2": "Tiêu hao nguyên liệu tăng cấp kỹ năng để nâng cao cấp độ và hiệu quả chiến đấu của kỹ năng.",
        "DictionaryDiagram.10040102.1": "Mở Khóa Dòng Thuộc Tính",
        "DictionaryDiagram.10040102.2": "Huy hiệu sở hữu số dòng thuộc tính ngẫu nhiên cùng Thẻ Lữ Khách tương ứng. Cường hóa Huy hiệu đến cấp chỉ định sẽ mở khóa loại thuộc tính của dòng ngẫu nhiên.",
        "DictionaryDiagram.10040103.1": "Độ Tương Thích Dòng Thuộc Tính",
        "DictionaryDiagram.10040103.2": "Khi Thẻ Lữ Khách trùng khớp với dòng thuộc tính ngẫu nhiên trên Huy hiệu, thuộc tính dòng đó sẽ được tăng thêm.",
        "DictionaryDiagram.10050101.1": "Tiềm Năng",
        "DictionaryDiagram.10050101.2": "Mỗi Lữ Khách ở vị trí Chính hoặc Hỗ Trợ đều sở hữu Tiềm Năng chuyên biệt riêng. Thám hiểm Cự Tháp để rút và kích hoạt Tiềm Năng. Những cách phối hợp Tiềm Năng khác nhau của cùng một Lữ Khách sẽ định hình nên các trường phái chiến đấu đặc sắc.",
        "DictionaryDiagram.10060101.1": "Tổng Quan Thiên Phú",
        "DictionaryDiagram.10060101.2": "Chiêu mộ Lữ Khách trùng lặp sẽ nhận được <color=#0abec5>Chìa Khóa Tâm Hồn</color>. Tiêu hao Chìa Khóa Tâm Hồn có thể kích hoạt <color=#0abec5>Thiên Phú</color>, gia tăng thuộc tính và mở khóa hiệu ứng hình ảnh đặc biệt. Ngoài chiêu mộ, Chìa Khóa Tâm Hồn còn có thể nhận qua các phương thức khác.",
        "DictionaryDiagram.10060102.1": "Hiệu Quả Thiên Phú",
        "DictionaryDiagram.10060102.2": "Kích hoạt <color=#0abec5>Thiên Phú</color> giúp Lữ Khách nhận nhiều loại tăng ích thuộc tính. Khi kích hoạt toàn bộ Thiên Phú trong cùng một tầng, sẽ mở khóa thêm năng lực đặc biệt và mở ra tầng Thiên Phú kế tiếp.",
        "DictionaryDiagram.10070101.1": "Tổng Quan Độ Thân Mật",
        "DictionaryDiagram.10070101.2": "Lữ Khách có thể tích lũy dần <color=#0abec5>Điểm Thân Mật</color>. Cấp Thân Mật càng cao sẽ càng mở khóa thêm nhiều hồ sơ, giọng nói và cốt truyện cá nhân. Hoàn thành toàn bộ cốt truyện để mở khóa <color=#0abec5>Hồi Ức Đặc Tả</color>. Tăng cấp Thân Mật còn tăng nhẹ thuộc tính cho Lữ Khách.",
        "DictionaryDiagram.10070102.1": "Tăng Thân Mật - Nhiệm Vụ Đồng Hành",
        "DictionaryDiagram.10070102.2": "Mỗi Lữ Khách có các <color=#0abec5>Mục Tiêu Đồng Hành</color> riêng. Hoàn thành mục tiêu này sẽ nhận được Điểm Thân Mật. Ngoài chiến đấu và làm nhiệm vụ, bạn còn có thể tăng Độ Thân Mật thông qua <color=#0abec5>Hẹn Gặp, Tặng Quà</color>.",
        "DictionaryDiagram.10080101.1": "Huy Hiệu Lữ Khách",
        "DictionaryDiagram.10080101.2": "Mỗi Lữ Khách sở hữu 3 ô Huy hiệu mở khóa ở các cấp độ khác nhau. Sau khi mở, có thể khảm nạm Huy hiệu để gia tăng thực lực nhân vật.",
        "DictionaryDiagram.10080102.1": "Nguyên Liệu Huy Hiệu",
        "DictionaryDiagram.10080102.2": "Sau khi kích hoạt ô Huy hiệu, cần tiêu hao nguyên liệu chỉ định để đúc. Những nguyên liệu này có thể nhận qua Thử Luyện Huy Hiệu.",
        "DictionaryDiagram.10080103.1": "Thiên Hướng Huy Hiệu",
        "DictionaryDiagram.10080103.2": "Loại Huy hiệu và thứ tự mở khóa ô của mỗi Lữ Khách không theo quy luật cố định.",
        "DictionaryDiagram.10080104.1": "Đúc Huy Hiệu",
        "DictionaryDiagram.10080104.2": "Đúc Huy hiệu sẽ nhận ngẫu nhiên các dòng thuộc tính. Huy hiệu Trung Cấp (mở khóa ở Lữ Khách cấp 80) có tỷ lệ xuất hiện dòng tăng cấp Kỹ Năng, Huy hiệu Cao Cấp (mở khóa ở Lữ Khách cấp 90) có tỷ lệ xuất hiện dòng tăng cấp Tiềm Năng.",
        "DictionaryDiagram.10080105.1": "Đúc Lại Huy Hiệu",
        "DictionaryDiagram.10080105.2": "Tiêu hao nguyên liệu chỉ định để Đúc Lại Huy hiệu, tái tạo toàn bộ một bộ dòng thuộc tính ngẫu nhiên mới.",
        "DictionaryDiagram.10080106.1": "Khóa Đúc Lại",
        "DictionaryDiagram.10080106.2": "Trong quá trình Đúc Lại có thể dùng đạo cụ khóa dòng. Dòng thuộc tính bị khóa chắc chắn sẽ được giữ lại ở lần Đúc Lại tiếp theo. Mỗi lần đúc lại được khóa tối đa 2 dòng thuộc tính.",
        "DictionaryDiagram.10080107.1": "Đột Phá Huy Hiệu",
        "DictionaryDiagram.10080107.2": "Dùng Giọt Thánh Khiết để Đột Phá Huy hiệu, cường hóa dòng thuộc tính chỉ định. Mỗi Huy hiệu tối đa Đột Phá 2 lần. Khi đúc lại Huy hiệu, nếu không khóa dòng đã Đột Phá thì hiệu ứng Đột Phá sẽ bị hoàn trả và không hoàn lại Giọt Thánh Khiết đã dùng.",
        "DictionaryDiagram.20010101.1": "Cấp Ủy Quyền",
        "DictionaryDiagram.20010101.2": "Tiêu hao Thể Lực hoàn thành chiến đấu để tăng Cấp Ủy Quyền và nhận phần thưởng tiếp tế dồi dào!",
        "DictionaryDiagram.20020101.1": "Cự Tháp - Tổng Quan",
        "DictionaryDiagram.20020101.2": "Sau khi hoàn thành Thám Hiểm Cự Tháp, có thể lưu trữ「Kỷ Lục」để sử dụng khi khiêu chiến các chế độ phụ bản khác.",
        "DictionaryDiagram.20020102.1": "Cự Tháp - Tiềm Năng",
        "DictionaryDiagram.20020102.2": "Trong quá trình <color=#0abec5>Thám Hiểm Cự Tháp</color>, hãy chọn và thu thập các <color=#0abec5>Tiềm Năng</color> để cường hóa Lữ Khách. Các Tiềm Năng thu được sẽ được lưu vào「Kỷ Lục」.",
        "DictionaryDiagram.20020103.1": "Cự Tháp - Nốt Nhạc",
        "DictionaryDiagram.20020103.2": "Trong quá trình <color=#0abec5>Thám Hiểm Cự Tháp</color>, bạn có thể thu thập <color=#0abec5>Nốt Nhạc</color> để nhận các chỉ số tăng ích nguyên tố. Nốt Nhạc cũng sẽ được lưu vào Kỷ Lục để dùng trong các chế độ chơi khác.",
        "DictionaryDiagram.20020104.1": "Cự Tháp - Kỹ Năng Hợp Tấu",
        "DictionaryDiagram.20020104.2": "Thu thập Nốt Nhạc còn dùng để kích hoạt <color=#0abec5>Kỹ Năng Hợp Tấu</color> của Bí Văn, cung cấp hiệu ứng tăng ích cho toàn đội. Kỹ Năng Hợp Tấu đã kích hoạt cũng sẽ được lưu vào Kỷ Lục.",
        "DictionaryDiagram.20020105.1": "Cự Tháp - Biến Cố",
        "DictionaryDiagram.20020105.2": "Các sự kiện ngẫu nhiên gặp phải khi <color=#0abec5>Thám Hiểm Cự Tháp</color> sẽ mang lại nhiều phần thưởng tùy theo lựa chọn của bạn.",
        "DictionaryDiagram.20020107.1": "Cự Tháp - Kỷ Lục",
        "DictionaryDiagram.20020107.2": "Hoàn thành <color=#0abec5>Thám Hiểm Cự Tháp</color> có thể lưu trữ Kỷ Lục để dùng cho nhiều chế độ chơi khác. Kỷ Lục bao gồm đội hình thành viên, Tiềm Năng và Nốt Nhạc của chuyến thám hiểm đó.",
        "DictionaryDiagram.20020201.1": "Tổng Quan Nghiên Cứu",
        "DictionaryDiagram.20020201.2": "Tiến hành <color=#0abec5>Thám Hiểm Cự Tháp</color> hoặc hoàn thành <color=#0abec5>Kế Hoạch Nghiên Cứu</color> để nhận nguyên liệu Nghiên Cứu Cự Tháp. Tiêu hao nguyên liệu để kích hoạt <color=#0abec5>Nút Nghiên Cứu</color>, mang lại nhiều bùa lợi tăng ích cho các chuyến thám hiểm tiếp theo.",
        "DictionaryDiagram.20020202.1": "Tầng Nghiên Cứu",
        "DictionaryDiagram.20020202.2": "Nghiên Cứu Cự Tháp gồm 3 <color=#0abec5>Tầng Cấp</color>. Cần hoàn thành <color=#0abec5>toàn bộ nghiên cứu</color> ở tầng trước mới có thể tiếp tục tiến sâu vào các tầng kế tiếp.",
        "DictionaryDiagram.20020203.1": "Điều Kiện Nghiên Cứu",
        "DictionaryDiagram.20020203.2": "Cần mở khóa tầng nghiên cứu hiện tại và hoàn thành <color=#0abec5>tất cả các nút tiên quyết</color> mới có thể nghiên cứu nút tương ứng.",
        "DictionaryDiagram.20030101.1": "Tổng Quan Kỷ Lục",
        "DictionaryDiagram.20030101.2": "Sau khi kết thúc Thám Hiểm Cự Tháp có thể lưu trữ Kỷ Lục, ghi nhận Lữ Khách và Bí Văn tham chiến. Khi sử dụng Kỷ Lục, thông tin bồi dưỡng của Lữ Khách và Bí Văn sẽ được đồng bộ theo thời gian thực.",
        "DictionaryDiagram.20030102.1": "Tiềm Năng & Chúc Phúc",
        "DictionaryDiagram.20030102.2": "Kỷ Lục cũng lưu giữ các Tiềm Năng và Nốt Nhạc đã kích hoạt trong chuyến Thám Hiểm Cự Tháp. Sau khi lưu, Tiềm Năng và Nốt Nhạc sẽ không thay đổi nữa.",
        "DictionaryDiagram.20030201.1": "Cài Đặt Sẵn Tiềm Năng",
        "DictionaryDiagram.20030201.2": "Tại giao diện chọn Lữ Khách, bạn có thể thiết lập trước Cài Đặt Tiềm Năng!",
        "DictionaryDiagram.20030202.1": "Cài Đặt Sẵn Tiềm Năng",
        "DictionaryDiagram.20030202.2": "Trong giao diện Cài Đặt Sẵn Tiềm Năng, có thể chọn cấu hình mẫu đã lưu hoặc tạo mới!",
        "DictionaryDiagram.20030203.1": "Cài Đặt Sẵn Tiềm Năng",
        "DictionaryDiagram.20030203.2": "Tiềm Năng và cấp độ được chọn trong cấu hình mẫu sẽ được đánh dấu nhắc nhở trong suốt chuyến Thám Hiểm Cự Tháp.",
        "DictionaryDiagram.20030204.1": "Chia Sẻ & Nhập Mã Cài Đặt",
        "DictionaryDiagram.20030204.2": "Ma Vương có thể tự do chia sẻ và nhập mã Cài Đặt Sẵn Tiềm Năng!",
        "DictionaryDiagram.20080103.1": "Sân Khấu Đỉnh Cao",
        "DictionaryDiagram.20080103.2": "Trong Sân Khấu Đỉnh Cao, bạn có thể tự tay chọn các dòng từ điều độ khó để tăng thử thách.\nHãy chọn dòng độ khó và chinh phục những màn chơi thử thách hơn nào!",
        "DictionaryDiagram.20080201.1": "Sân Khấu Đỉnh Cao",
        "DictionaryDiagram.20080201.2": "Nhấp Bắt Đầu Quyết Đấu để mở màn thử thách đỉnh cao.\nCó thể tùy ý chọn các dòng thuộc tính để điều chỉnh độ khó!",
        "DictionaryDiagram.20080202.1": "Sân Khấu Đỉnh Cao",
        "DictionaryDiagram.20080202.2": "Sau khi vượt qua thử thách, phần thưởng sẽ tích lũy dựa theo độ khó cao nhất đã vượt, tối đa tích lũy 48 giờ thưởng.",
        "DictionaryDiagram.20080203.1": "Sân Khấu Đỉnh Cao",
        "DictionaryDiagram.20080203.2": "Ba loại đạo cụ thu được từ phần thưởng tích lũy có thể dùng để Đua Top, gia tăng Điểm Cống Hiến Fan và Độ Hot phòng phát sóng của Lilibea!",
        "DictionaryDiagram.20080204.1": "Sân Khấu Đỉnh Cao",
        "DictionaryDiagram.20080204.2": "Trong thời gian sự kiện sẽ diễn ra Quyết Đấu Độ Hot!\nKhi kết toán mỗi ngày, nếu độ hot vượt qua đối thủ sẽ nhận thưởng lớn, hãy mau tới cổ vũ cho Lilibea nhé!",
        "DictionaryDiagram.20090101.1": "Tăng Ích Thuộc Tính Bí Văn",
        "DictionaryDiagram.20090101.2": "Khi bước vào Cự Tháp, mang theo Bí Văn sẽ cung cấp các bùa lợi thuộc tính tương ứng cho toàn bộ Lữ Khách trong đội hình.",
        "DictionaryDiagram.20090102.1": "Vị Trí Chính - Kỹ Năng Giai Điệu",
        "DictionaryDiagram.20090102.2": "Nếu Bí Văn trang bị ở Vị Trí Chính: Khi vào Cự Tháp sẽ tự động kích hoạt Kỹ Năng Giai Điệu. Kỹ năng này có hiệu lực cực mạnh, gia tăng vượt bậc thực lực tác chiến của Lữ Khách. Cấp độ kỹ năng đồng bộ theo số sao Điệp Thanh của Bí Văn, sao càng cao cấp kỹ năng càng lớn.",
        "DictionaryDiagram.20090103.1": "Vị Trí Chính - Kỹ Năng Hợp Tấu",
        "DictionaryDiagram.20090103.2": "Nếu Bí Văn trang bị ở Vị Trí Chính: Cần thu thập đủ chủng loại và số lượng Nốt Nhạc Nguyên Tố chỉ định trong chuyến Thám Hiểm Cự Tháp để kích hoạt Kỹ Năng Hợp Tấu.",
        "DictionaryDiagram.20090104.1": "Vị Trí Phụ - Nốt Nhạc Khởi Đầu",
        "DictionaryDiagram.20090104.2": "Nếu Bí Văn trang bị ở Vị Trí Phụ: Khi vào Cự Tháp sẽ nhận ngay các Nốt Nhạc đặc định của Bí Văn đó làm nốt khởi đầu. Những nốt nhạc này cũng dùng để kích hoạt Kỹ Năng Hợp Tấu của Bí Văn ở Vị Trí Chính.",
        "DictionaryDiagram.20100101.1": "Danh Bạ Lữ Khách",
        "DictionaryDiagram.20100101.2": "Các Lữ Khách bạn gặp gỡ và chiêu mộ trong hành trình sẽ được thêm vào Danh Bạ Liên Lạc Tâm Liên, định kỳ hoặc theo biến cố cốt truyện sẽ tự động kích hoạt cuộc trò chuyện.",
        "DictionaryDiagram.20100102.1": "Hội Thoại",
        "DictionaryDiagram.20100102.2": "Trong cuộc trò chuyện, bạn có thể chọn các phương án đối đáp khác nhau để mở ra những phản hồi thú vị riêng biệt.",
        "DictionaryDiagram.20100103.1": "Chuyển Đổi Hội Thoại",
        "DictionaryDiagram.20100103.2": "Mọi cuộc trò chuyện đã kích hoạt của từng người liên hệ đều được lưu trong danh sách, có thể chuyển đổi hiển thị giữa các phiên đã hoàn tất hoặc đang diễn ra.",
        "DictionaryDiagram.20110101.1": "Giới Thiệu Thể Lực",
        "DictionaryDiagram.20110101.2": "Tham gia Thử Luyện Treo Thưởng và một số ải sự kiện cần tiêu hao Thể Lực. Tiêu hao Thể Lực sẽ giúp tăng Cấp Ủy Quyền.",
        "DictionaryDiagram.20110102.1": "Hồi Phục Thể Lực",
        "DictionaryDiagram.20110102.2": "Thể Lực tự nhiên hồi phục 1 điểm mỗi 6 phút. Ngoài ra có thể đổi bằng Cát Sao hoặc dùng Nước Năng Lượng để hồi phục.",
        "DictionaryDiagram.20110103.1": "Dự Trữ Thể Lực",
        "DictionaryDiagram.20110103.2": "Khi Thể Lực đã đầy, cứ 18 phút sẽ tích trữ 1 điểm vào Kho Dự Trữ Thể Lực, tối đa tích trữ 2,400 điểm. Thể Lực dự trữ có thể rút ra sử dụng bất cứ lúc nào.",
        "DictionaryDiagram.20120101.1": "Tổng Quan Lối Chơi",
        "DictionaryDiagram.20120101.2": "Lôi Đài phân thành nhiều độ khó và thuộc tính, Lữ Khách cần vượt qua từ bậc thấp nhất trở lên.\nHoàn thành khiêu chiến Lôi Đài sẽ nhận được phần thưởng phong phú.",
        "DictionaryDiagram.20120102.1": "Quy Tắc Lôi Đài",
        "DictionaryDiagram.20120102.2": "Mỗi Lôi Đài có các hạn chế quy tắc riêng tùy theo thuộc tính và độ khó.\nQuy tắc Lôi Đài có thể ảnh hưởng đến chiến thuật hoặc lựa chọn Lữ Khách, hãy linh hoạt điều chỉnh nhé!",
        "DictionaryDiagram.20130101.1": "Phòng Tuyến Tai Họa",
        "DictionaryDiagram.20130101.2": "Phòng Tuyến Tai Họa gồm nhiều ải với các cấp độ khó khác nhau để bạn tùy chọn khiêu chiến.",
        "DictionaryDiagram.20130102.1": "Phòng Tuyến Tai Họa - Đội Hình",
        "DictionaryDiagram.20130102.2": "Phòng Tuyến Tai Họa yêu cầu 2 Kỷ Lục riêng biệt để khiêu chiến, và hai Kỷ Lục không được chứa Lữ Khách trùng lặp!",
        "DictionaryDiagram.20130103.1": "Phòng Tuyến Tai Họa - Thưởng",
        "DictionaryDiagram.20130103.2": "Trong tác chiến Phòng Tuyến Tai Họa, điểm số tích lũy dựa theo số kẻ địch bị tiêu diệt. Khi điểm mỗi mùa đạt mục tiêu sẽ nhận thưởng tương ứng.",
        "DictionaryDiagram.20130104.1": "Phòng Tuyến Tai Họa - Thiên Phú",
        "DictionaryDiagram.20130104.2": "Thu thập Thẻ Định Mệnh sẽ nhận Điểm Thiên Phú Phòng Tuyến Tai Họa, dùng để kích hoạt Cây Thiên Phú.\nCây Thiên Phú sẽ cung cấp nhiều bùa lợi tăng ích cho các chuyến khiêu chiến tiếp theo.",
        "DictionaryDiagram.20130201.1": "Phòng Tuyến Tai Họa - Cấp Độ",
        "DictionaryDiagram.20130201.2": "Trong chiến đấu Phòng Tuyến Tai Họa, thu thập EXP để tăng cấp! Khi tăng cấp sẽ nhận ngẫu nhiên Thẻ Định Mệnh gia tăng thuộc tính nội trận.\nThẻ Định Mệnh có thể kế thừa thời gian và hiệu lực giữa hai hiệp trên và dưới!",
        "DictionaryDiagram.20130202.1": "Phòng Tuyến Tai Họa - Thưởng Đặc Biệt",
        "DictionaryDiagram.20130202.2": "Sau khi kích hoạt Thiên Phú Tai Họa, trong trận nếu thu thập đủ số lượng thẻ từ cùng một gói sẽ nhận được Thẻ Định Mệnh Đặc Biệt cực mạnh!",
        "DictionaryDiagram.20130203.1": "Phòng Tuyến Tai Họa - Cơ Chế Đặc Biệt",
        "DictionaryDiagram.20130203.2": "Chịu ảnh hưởng bởi thế lực bí ẩn, trong Phòng Tuyến Tai Họa, nhấn giữ Né Tránh sẽ không vào trạng thái Tốc Biến Lướt Nhanh!",
        "DictionaryDiagram.20140101.1": "Cảnh Giới Thử Luyện",
        "DictionaryDiagram.20140101.2": "Chế độ Cảnh Giới Thử Luyện mở ra nhiều Thủ Lĩnh để khiêu chiến hàng tuần. Mỗi tuần có 3 lượt khiêu chiến, làm mới vào thứ Hai. Khi hết lượt sẽ không nhận được phần thưởng thường.",
        "DictionaryDiagram.20140102.1": "Thu Thập Nguyên Liệu",
        "DictionaryDiagram.20140102.2": "Mỗi Thủ Lĩnh rơi ra nguyên liệu bồi dưỡng đặc thù riêng. Nhu cầu bồi dưỡng của mỗi Lữ Khách khác nhau, hãy khiêu chiến đúng Thủ Lĩnh để thu thập nguyên liệu cần thiết.",
        "DictionaryDiagram.20150101.1": "Liên Minh Thảo Phạt",
        "DictionaryDiagram.20150101.2": "Liên Minh Thảo Phạt làm mới theo chu kỳ, mỗi chu kỳ chỉ định 2 nhiệm vụ thảo phạt mang quy tắc đặc biệt để các Lữ Khách tham chiến.",
        "DictionaryDiagram.20150102.1": "Tính Tổng Số Sao",
        "DictionaryDiagram.20150102.2": "Mỗi nhiệm vụ thảo phạt ghi nhận số sao riêng, tổng số sao của cả hai nhiệm vụ chính là tổng sao đạt được của bạn trong kỳ.",
        "DictionaryDiagram.20150103.1": "Quy Tắc Phần Thưởng",
        "DictionaryDiagram.20150103.2": "Dựa trên tổng số sao đạt được trong kỳ để nhận thưởng Đá Quý phong phú.",
        "DictionaryDiagram.20150104.1": "Cách Thức Tính Điểm",
        "DictionaryDiagram.20150104.2": "Cần gây càng nhiều sát thương càng tốt trong thời gian quy định, lượng sát thương gây ra sẽ quy đổi thành điểm số. Thao tác chuẩn xác theo cơ chế của Thủ Lĩnh sẽ nhận thêm điểm kỹ thuật.",
        "DictionaryDiagram.20150105.1": "Quy Tắc Quy Đổi Sao",
        "DictionaryDiagram.20150105.2": "Khi điểm số đạt mốc chỉ định sẽ nhận số sao tương ứng và lưu vào kỷ lục thảo phạt lần này.",
        "DictionaryDiagram.20150106.1": "Cơ Chế Khóa Đội Hình",
        "DictionaryDiagram.20150106.2": "Khi hoàn thành thảo phạt và tải điểm lên, Lữ Khách tham chiến sẽ bị khóa vào nhiệm vụ đó. Nếu dùng Lữ Khách đã khóa cho nhiệm vụ khác và nộp điểm, điểm và sao ở nhiệm vụ cũ sẽ bị xóa bỏ.",
        "DictionaryDiagram.20160101.1": "Tuyệt Xướng Tận Cùng",
        "DictionaryDiagram.20160101.2": "Khiêu chiến Thủ Lĩnh cần tiêu hao <color=#0abec5>Hiệu Lệnh Quyết Chiến</color>. Đạo cụ này mỗi ngày trong thời gian sự kiện sẽ tự động hồi phục về mức tối đa.",
        "DictionaryDiagram.20160102.1": "Độ Khó Khiêu Chiến",
        "DictionaryDiagram.20160102.2": "Tùy chọn Thủ Lĩnh ở bất kỳ <color=#0abec5>độ khó</color> nào để bắt đầu khiêu chiến. Thông qua <color=#0abec5>Trận Chiến Mô Phỏng</color> có thể diễn tập chiến đấu với Thủ Lĩnh mà không tiêu tốn Vé Khiêu Chiến.",
        "DictionaryDiagram.20160201.1": "Hiệp Lực Tác Chiến",
        "DictionaryDiagram.20160201.2": "Dù chưa thể hạ gục Thủ Lĩnh trong trận đầu, bạn vẫn có thể cử tiếp đội hình chi viện vào khiêu chiến. Trong các trận sau, Kỷ Lục được chọn không được chứa Lữ Khách đã từng xuất trận.",
        "DictionaryDiagram.20170101.1": "Tổng Quan Săn Bóng Vây Hãm",
        "DictionaryDiagram.20170101.2": "Săn Bóng Vây Hãm là cơ chế tác chiến mới do Iori từ Hiệp Hội Địa Lý phát động. Bằng cách truy bắt mục tiêu vây hãm mỗi kỳ, bạn sẽ nhận được Chứng Nhận Cống Hiến——Huy Chương Thợ Săn.",
        "DictionaryDiagram.20170102.1": "Cấp Ủy Thác",
        "DictionaryDiagram.20170102.2": "Hiệp Hội Địa Lý sẽ căn cứ theo mức độ hoạt động (tiêu hao Thể Lực) của từng Lữ Đoàn để trao Thư Ủy Thác Truy Vết / Giấy Phép Vây Hãm. Loại trước dùng để truy vết tìm manh mối, loại sau dùng để hỗ trợ các Lữ Đoàn khác cùng tiêu diệt mục tiêu.",
        "DictionaryDiagram.20170103.1": "Truy Vết",
        "DictionaryDiagram.20170103.2": "Tiêu hao Thư Ủy Thác Truy Vết để tiến hành truy vết, quá trình sẽ kích phát nhiều tình huống khác nhau. Khi tiến độ truy vết đạt tối đa, có thể phát động chiến dịch thảo phạt mục tiêu.",
        "DictionaryDiagram.20170104.1": "Hiệp Lực Thảo Phạt",
        "DictionaryDiagram.20170104.2": "Chiến đấu thảo phạt sẽ tích lũy điểm, kết toán dựa theo điểm để nhận đánh giá sao. Đạt tối đa sao sẽ kết thúc đợt thảo phạt. Mục tiêu vây hãm cần nhiều đợt thảo phạt mới hạ gục được, do đó cần nhiều Lữ Đoàn hiệp lực tương trợ.",
        "DictionaryDiagram.20170105.1": "Cấp Độ Vây Hãm",
        "DictionaryDiagram.20170105.2": "Tham gia vây hãm giúp tăng cấp Vây Hãm mùa giải và mở khóa nhiều hiệu ứng tăng ích. Khi làm mới bảng treo thưởng, cấp Vây Hãm sẽ được thiết lập lại.",
        "DictionaryDiagram.30010101.1": "Thao Tác Cơ Bản",
        "DictionaryDiagram.30010101.2": "Lữ Khách sẽ tự động tấn công kẻ địch trong phạm vi.\nNhấn nút <color=#0abec5>Kỹ Năng</color> để thi triển chiêu thức.\nKhi Tuyệt Kỹ tích đầy năng lượng, nhấn nút <color=#0abec5>Tuyệt Kỹ</color> để tung đòn kết liễu.",
        "DictionaryDiagram.30010501.1": "Thao Tác Tác Chiến: Đòn Đánh Thường",
        "DictionaryDiagram.30010501.2": "Khi mục tiêu tiến vào tầm đánh, Lữ Khách sẽ tự động thực hiện Đòn Đánh Thường.",
        "DictionaryDiagram.30010601.1": "Thao Tác Tác Chiến: Kỹ Năng Chính",
        "DictionaryDiagram.30010601.2": "Chạm nhấn nút Kỹ Năng Chính để thi triển chiêu thức chủ đạo.",
        "DictionaryDiagram.30010701.1": "Thao Tác Tác Chiến: Tích Lũy Năng Lượng",
        "DictionaryDiagram.30010701.2": "Mọi Đòn Đánh Thường và kỹ năng do <color=#0abec5>Lữ Khách Chính</color> tung ra trúng kẻ địch đều có thể tích lũy năng lượng cho Tuyệt Kỹ.",
        "DictionaryDiagram.30010801.1": "Thao Tác Tác Chiến: Né Tránh",
        "DictionaryDiagram.30010801.2": "Chạm nhấn nút Né Tránh để né đòn tấn công của quái vật. Trong thời gian né tránh hoàn toàn miễn nhiễm sát thương.",
        "DictionaryDiagram.30010901.1": "Thao Tác Tác Chiến: Lướt Nhanh",
        "DictionaryDiagram.30010901.2": "Nhấn giữ nút Né Tránh để vào trạng thái Lướt Nhanh Tốc Biến, trong thời gian di chuyển nhân vật sẽ không tự động tấn công.",
        "DictionaryDiagram.30011001.1": "Thao Tác Tác Chiến: Kỹ Năng Hỗ Trợ",
        "DictionaryDiagram.30011001.2": "Chạm nhấn nút Kỹ Năng Hỗ Trợ của Lữ Khách hỗ trợ để thi triển chiêu thức tương trợ.",
        "DictionaryDiagram.30011101.1": "Thao Tác Tác Chiến: Tuyệt Kỹ Hỗ Trợ",
        "DictionaryDiagram.30011101.2": "Chạm nhấn nút Tuyệt Kỹ của Lữ Khách hỗ trợ để tung ra đại chiêu.",
        "DictionaryDiagram.30011201.1": "Thuộc Tính Nguyên Tố: Ấn Ký",
        "DictionaryDiagram.30011201.2": "Lữ Khách có thể gắn Ấn Ký lên mục tiêu hoặc kích hoạt Ấn Ký sẵn có để gây nhiều hiệu ứng đặc biệt.\nMỗi Lữ Khách đối với cùng một mục tiêu mỗi giây kích hoạt Ấn Ký tối đa 1 lần.",
        "DictionaryDiagram.30011202.1": "Ấn Ký Nguyên Tố: Phối Hợp Đội",
        "DictionaryDiagram.30011202.2": "Lữ Khách định vị Hỗ Trợ hoặc Cân Bằng ở vị trí Hỗ Trợ có thể gắn kèm Ấn Ký nguyên tố tương ứng.\nLữ Khách định vị Tiên Phong cùng hệ nguyên tố ở vị trí Chính có thể kích hoạt Ấn Ký đó.",
        "DictionaryDiagram.30011301.1": "Thuộc Tính Nguyên Tố: Điểm Yếu & Kháng Tính",
        "DictionaryDiagram.30011301.2": "Khi Lữ Khách tấn công quái vật, lượng sát thương gây ra sẽ thay đổi tùy theo Điểm Yếu hay Kháng Tính nguyên tố của quái vật.",
        "DictionaryDiagram.30011302.1": "Thuộc Tính Nguyên Tố: Điểm Yếu & Kháng Tính",
        "DictionaryDiagram.30011302.2": "Khi Lữ Khách tấn công quái vật, lượng sát thương gây ra sẽ thay đổi tùy theo Điểm Yếu hay Kháng Tính nguyên tố của quái vật.",
        "DictionaryDiagram.30011401.1": "Thuộc Tính Nguyên Tố: Đề Cử",
        "DictionaryDiagram.30011401.2": "Khi công phá ải, hãy chú ý đến thuộc tính nguyên tố được ải đề cử nhé!",
        "DictionaryDiagram.30011501.1": "Kiên Định",
        "DictionaryDiagram.30011501.2": "Khi mục tiêu sở hữu Kiên Định, hành vi sẽ không bị ngoại lực ngắt quãng. Khi chịu sát thương, Kiên Định sẽ bị bào mòn.",
        "DictionaryDiagram.30011601.1": "Phá Vỡ Kiên Định",
        "DictionaryDiagram.30011601.2": "Sau khi bị Phá Vỡ Kiên Định, mục tiêu sẽ rơi vào trạng thái tê liệt cứng đờ kéo dài, Lữ Khách có thể gây thêm lượng lớn sát thương.",
        "DictionaryDiagram.30011701.1": "Thuộc Tính Nguyên Tố: Kích Hoạt Ấn Ký",
        "DictionaryDiagram.30011701.2": "Khi mục tiêu đã bị gắn Ấn Ký, hãy thử dùng kỹ năng cùng hệ nguyên tố có khả năng kích hoạt để tấn công mục tiêu!",
        "DictionaryDiagram.30011801.1": "Nguồn Thu Thập Nốt Nhạc",
        "DictionaryDiagram.30011801.2": "Trong quá trình công phá Cự Tháp, có thể nhận Nốt Nhạc qua chiến đấu, mua ở Cửa Hàng, hoặc qua các Biến Cố ngẫu nhiên.",
    }

    # Polish every item
    results = {}
    for it in items:
        k = it['key']
        en = it['en']
        cn = it.get('cn', '')
        vi = it.get('vi_current', it.get('vi', ''))

        if en == '!NONEED!':
            results[k] = '!NONEED!'
            continue

        if k in EXACT_MAP:
            results[k] = EXACT_MAP[k]
            continue

        # Clean up systematically using rules
        polished = vi
        
        # Terms replacements
        polished = polished.replace('Thăng thiên', 'Thám Hiểm Cự Tháp')
        polished = polished.replace('thăng thiên', 'Thám Hiểm Cự Tháp')
        polished = polished.replace('Hồ sơ', 'Kỷ Lục')
        polished = polished.replace('hồ sơ', 'Kỷ Lục')
        polished = polished.replace('bản ghi', 'Kỷ Lục')
        polished = polished.replace('Bản ghi', 'Kỷ Lục')
        polished = polished.replace('Tài năng', 'Thiên Phú')
        polished = polished.replace('tài năng', 'Thiên Phú')
        polished = polished.replace('phụ kiện', 'dòng thuộc tính')
        polished = polished.replace('Phụ kiện', 'Dòng thuộc tính')
        polished = polished.replace('biểu tượng', 'Huy hiệu')
        polished = polished.replace('Biểu tượng', 'Huy hiệu')
        polished = polished.replace('khoản trợ cấp', 'nhận được')
        polished = polished.replace('Những phím này', 'Chìa Khóa Tâm Hồn này')
        polished = polished.replace('phím này', 'chìa khóa này')
        polished = polished.replace('Mối quan hệ', 'Độ Thân Mật')
        polished = polished.replace('mối quan hệ', 'Độ Thân Mật')
        polished = polished.replace('Ảnh chụp nhanh bộ nhớ', 'Hồi Ức Đặc Tả')
        polished = polished.replace('ảnh chụp nhanh bộ nhớ', 'Hồi Ức Đặc Tả')
        polished = polished.replace('Đĩa Runic', 'Bí Văn')
        polished = polished.replace('Đĩa', 'Bí Văn')
        polished = polished.replace('đĩa', 'Bí Văn')
        polished = polished.replace('Cơ chế khóa', 'Cơ Chế Khóa Đội Hình')
        polished = polished.replace('Boss Blitz', 'Liên Minh Thảo Phạt')
        polished = polished.replace('Cataclysm Survivor', 'Phòng Tuyến Tai Họa')
        polished = polished.replace('Người sống sót sau thảm họa', 'Phòng Tuyến Tai Họa')
        polished = polished.replace('người sống sót sau thảm họa', 'Phòng Tuyến Tai Họa')
        polished = polished.replace('Proving Grounds', 'Cảnh Giới Thử Luyện')
        polished = polished.replace('Căn cứ chứng minh', 'Cảnh Giới Thử Luyện')
        polished = polished.replace('Summit Show', 'Sân Khấu Đỉnh Cao')
        polished = polished.replace('Hội nghị thượng đỉnh', 'Sân Khấu Đỉnh Cao')
        polished = polished.replace('Chương trình Hội nghị thượng đỉnh', 'Sân Khấu Đỉnh Cao')
        polished = polished.replace('Vòng cung dồi dào', 'Đường Cong Quà Tặng')
        polished = polished.replace('Cú nảy bội thu', 'Cú Nảy Vỡ Tinh Cầu')
        polished = polished.replace('Phòng thủ cờ vua', 'Thủ Thành Cờ Chiến')
        polished = polished.replace('Cờ Vua Phòng Thủ', 'Thủ Thành Cờ Chiến')
        polished = polished.replace('Cờ Tướng Phòng Thủ: Boss Cân', 'Thủ Thành Cờ Chiến: Thể Trọng Thủ Lĩnh')
        polished = polished.replace('Trọng lượng ưu tú', 'Thể Trọng Tinh Anh')
        polished = polished.replace('Theo dõi người ưu tú', 'Chú Ý Kẻ Địch Tinh Anh')
        polished = polished.replace('Theo dõi Boss', 'Chú Ý Thủ Lĩnh')
        polished = polished.replace('Canned Stormcloud', 'Mây Bão Đóng Hộp')
        polished = polished.replace('Soulcalling Lantern', 'Đèn Gọi Hồn')
        polished = polished.replace('Beacon', 'Hải Đăng')
        polished = polished.replace('Beacons', 'Hải Đăng')
        polished = polished.replace('Vật lộn tìm kho báu', 'Móc Câu Tìm Báu')
        polished = polished.replace('vật lộn', 'móc câu')
        polished = polished.replace('Trạm cung cấp làm mát', 'Trạm Tiếp Tế Mát Lạnh')
        polished = polished.replace('Chế độ sốt', 'Giờ Vàng Sôi Động')
        polished = polished.replace('Chế độ Sốt', 'Giờ Vàng Sôi Động')
        polished = polished.replace('muỗng kem', 'viên kem')
        polished = polished.replace('lớp phủ bên trên', 'topping')
        polished = polished.replace('Vàng tài năng', 'Vàng Hiền Tài')
        polished = polished.replace('Thiên phú Gold', 'Vàng Hiền Tài')
        polished = polished.replace('Through Hostile Depths', 'Tiên Phong Hãm Trận')
        polished = polished.replace('Xuyên qua độ sâu thù địch', 'Tiên Phong Hãm Trận')
        polished = polished.replace('Qua vực sâu thù địch', 'Tiên Phong Hãm Trận')
        polished = polished.replace('Vệ sinh (SAN)', 'Điểm Tỉnh Táo (SAN)')
        polished = polished.replace('Sự tỉnh táo (SAN)', 'Điểm Tỉnh Táo (SAN)')
        polished = polished.replace('Điểm bạo chúa', 'Điểm Ma Vương')
        polished = polished.replace('Điểm Bạo chúa', 'Điểm Ma Vương')
        polished = polished.replace('Tăng trưởng bạo chúa', 'Ma Vương Bồi Dưỡng')
        polished = polished.replace('Tyrant Development', 'Ma Vương Bồi Dưỡng')
        polished = polished.replace('Tài trợ khởi nghiệp', 'Quỹ Khởi Nghiệp')
        polished = polished.replace('Tài trợ ưu tú', 'Trợ Cấp Tôn Vinh')
        polished = polished.replace('Trợ cấp Khởi nghiệp', 'Quỹ Khởi Nghiệp')
        polished = polished.replace('Startup Grant', 'Quỹ Khởi Nghiệp')
        polished = polished.replace('Cấp Cấp', 'Cấp Quỹ')
        polished = polished.replace('Dodge', 'Né Tránh')
        polished = polished.replace('Dash', 'Lướt Nhanh')
        polished = polished.replace('Auto Attack', 'Đòn Đánh Thường')
        polished = polished.replace('Tấn công tự động', 'Đòn Đánh Thường')
        polished = polished.replace('Đòn đánh thường kẻ thù', 'tự động tấn công kẻ thù')

        # Passive voice & clunky phrasing cleanup
        polished = polished.replace('có thể được sử dụng để', 'dùng để')
        polished = polished.replace('có thể được sử dụng trong', 'dùng trong')
        polished = polished.replace('có thể được phân loại thành:', 'phân loại thành:')
        polished = polished.replace('có thể được', 'có thể')
        polished = polished.replace('được sử dụng', 'sử dụng')
        polished = polished.replace('được kích hoạt bởi', 'kích hoạt từ')
        polished = polished.replace('được áp dụng bởi', 'gắn từ')
        polished = polished.replace('được cấp bởi', 'nhận từ')
        polished = polished.replace('được tạo ra bởi', 'tạo ra từ')
        polished = polished.replace('bị gây ra bởi', 'gây ra từ')

        results[k] = polished

    return results

if __name__ == '__main__':
    root = Path(__file__).parent.parent
    with open(root / 'work' / 'polish' / 'audit_dict.json', 'r', encoding='utf-8') as f:
        items = json.load(f)

    res = polish_dict_entries(items)
    print(f"Polished {len(res)} DictionaryDiagram entries.")

    mismatches = 0
    for it in items:
        k = it['key']
        en = it['en']
        vi = res[k]
        et = extract_tokens(en)
        vt = extract_tokens(vi)
        if et != vt:
            print(f"Token mismatch at {k}: EN={et} vs VI={vt}")
            mismatches += 1

    print(f"Token mismatches in DictionaryDiagram: {mismatches}")
