#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full Translation Generator for STsp_08: Dusk Arbiter Prison #7 (271 items).
"""

import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/side_stories_part1_editorial_20261025_r01"
ITEMS_FILE = ROOT / "tools/campaign12/stsp_08_items.json"
OUT_FILE = CAMPAIGN_DIR / "trans_stsp_08.json"

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')
CTRL_PATTERN = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')

with open(ITEMS_FILE, "r", encoding="utf-8") as f:
    items = json.load(f)

# Specific curated translations for STsp_08
T = {}

# STsp_08_01
T["STsp_08_01.2"] = "Tháng ???"
T["STsp_08_01.3"] = "Ngày ??"
T["STsp_08_01.4"] = "Đế Quốc Grace"
T["STsp_08_01.5"] = "Nhà Tù Số 7 Thẩm Phán Hoàng Hôn"
T["STsp_08_01.6"] = "Hửm... Rốt cuộc mình đã ở trong này được bao nhiêu ngày rồi nhỉ?"
T["STsp_08_01.7"] = "Thật tình. Đến một ô cửa sổ hay cái đồng hồ cũng chẳng có."
T["STsp_08_01.9"] = "Hình như hai bắp chân của mình đã mất sạch cảm giác rồi..."
T["STsp_08_01.10"] = "Thú vị thật... Ra đây là phản ứng sinh lý của cơ thể khi phải quỳ gối trong thời gian dài."
T["STsp_08_01.11"] = "Cơ thể con người quả thực là một kiệt tác kỳ diệu."
T["STsp_08_01.12"] = "Đằng nào tôi cũng chẳng chạy đi đâu được. Có nhất thiết phải trói gô tôi chặt thế này không?"
T["STsp_08_01.13"] = "Cai Ngục"
T["STsp_08_01.14"] = "Này, tội nhân kia! Thôi lầm bầm đi! Trật tự!"
T["STsp_08_01.15"] = "Tôi chỉ đang quan sát khoa học thôi mà... Các người đúng là đa nghi quá mức với một tù nhân chẳng hề có chút ý định vượt ngục như tôi đấy."
T["STsp_08_01.16"] = "Ném cho tôi một mô hình bộ xương người vào đây thì bảo đi tôi cũng chẳng thèm đi đâu. Ở đây vừa yên tĩnh vừa riêng tư... Biết thế lúc bị bắt tôi đã mang theo đống dụng cụ thí nghiệm rồi."
T["STsp_08_01.17"] = "... Bị biệt giam riết nên hỏng não luôn rồi hả? Nghe đây: giả điên giả khùng cũng đừng hòng thoát khỏi đây đâu nhé!"
T["STsp_08_01.18"] = "Cởi trói cho cô ấy mau. Quỳ gối thế kia thì nói chuyện kiểu gì được."
T["STsp_08_01.19"] = "Đại nhân Igna! Vâng ạ, tôi làm ngay!"
T["STsp_08_01.20"] = "Cảm ơn. Các người lui ra ngoài đi. Ta đến đây theo lệnh tiếp nhận lời khai của Coronis."
T["STsp_08_01.21"] = "Rõ ạ. Tôi xin phép cáo lui."
T["STsp_08_01.22"] = "Đã lâu không gặp, Coronis."
T["STsp_08_01.23"] = "Tôi còn đang tự hỏi ai mà rảnh rỗi đến thăm mình... Quả nhiên là một vị khách quý hiếm hoi, Igna."
T["STsp_08_01.24"] = "Hừm... Thôi diễn kịch đi. Quỳ lâu như thế chắc chân cậu tê cóng cả rồi. Lại đây, để tôi đỡ cậu đứng dậy."
T["STsp_08_01.25"] = "Bọn họ ra tay chẳng kiêng nể chút nào. Cứ ngỡ cùng là đồng sự trong Đế Quốc Grace thì cũng được nể mặt đôi phần chứ."
T["STsp_08_01.26"] = "Tôi không sao. Thậm chí cơn đau này còn có ích nữa là. Nó giúp tôi phân tán sự chú ý rất tốt."
T["STsp_08_01.27"] = "Đã có phán quyết rồi.==W== Xem đi."
T["STsp_08_01.28"] = "Để xem nào...==W== Hừm. 'Tội báng bổ Thần Ân Điển. Dị giáo. Kết án treo cổ công khai.'"
T["STsp_08_01.29"] = "Hah. Y như tôi dự đoán. Thật tẻ nhạt... Những kẻ ngu muội lúc nào cũng chỉ biết dùng đến bạo lực thô bạo mỗi khi đối mặt với những điều chúng không thể hiểu nổi."
T["STsp_08_01.30"] = "Tôi nghe bảo cậu còn định biến phiên tòa luận tội thành một buổi hội thảo học thuật cơ đấy."
T["STsp_08_01.31"] = "Thứ đó mà gọi là hội thảo à? Sự dốt nát của bọn chúng thực sự làm tôi choáng váng... Cố lý luận với đám Thẩm Phán Hoàng Hôn chẳng khác nào đàn gảy tai trâu."
T["STsp_08_01.32"] = "Tôi đã nói quá rõ ràng rồi: 'Đêm Trường Vĩnh Cửu không cần sự ban phước của Thần Ân Điển để thi triển ma thuật.'"
T["STsp_08_01.33"] = "'Bản thân họ tự tạo ra ma lực của riêng mình. Chẳng cần đến bất kỳ Hồn Thạch nào.'==W==... Quá đơn giản. Hoàn toàn là thực nghiệm."
T["STsp_08_01.34"] = "Hahaha! Khổ nỗi bọn họ đâu phải là học giả, Coronis. Bọn họ quan tâm quái gì đến khoa học chứ."
T["STsp_08_01.35"] = "Bổn phận của họ là ngừng suy nghĩ, đưa ra một phán quyết rập khuôn theo 'giáo điều cổ xưa' rồi khép lại vụ án."
T["STsp_08_01.37"] = "Giáo điều quy định rằng ma thuật và Hồn Thạch là đặc ân độc quyền do Thần Ân Điển ban tặng. Chẳng ai dám công khai nghi ngờ điều đó... Ngay cả việc nghiên cứu thôi cũng là điều cấm kỵ rồi."
T["STsp_08_01.38"] = "Hừm... Tôi thấy bọn họ chỉ đang giả ngu giả ngơ thì có. Cố tình lảng tránh những chân lý mà bản thân quá đỗi khiếp sợ khi phải đối mặt."
T["STsp_08_01.40"] = "Thậm chí có một Thẩm Phán Cấp Cao còn lớn tiếng lập luận rằng 'đức tin vào Thần Ân Điển' là điều kiện tiên quyết để sở hữu ma thuật. Nghe xong tôi suýt phì cười ngay giữa công đường."
T["STsp_08_01.41"] = "Tôi từng tính thi triển ma thuật ngay trong lúc buông lời bài xích thần linh của bọn họ, để vả thẳng vào mặt luận điệu đó. Cơ mà phiền phức quá... Lại phải giảng giải nguyên lý ma thuật cơ bản từ con số không cho một lũ đầu đất."
T["STsp_08_01.42"] = "Thế nên cậu mới từ bỏ quyền bào chữa và để bọn chúng chuyển thẳng sang phần tuyên án luôn sao?"
T["STsp_08_01.43"] = "Như tôi đã bảo đấy thôi: đàn gảy tai trâu. Dù tôi có giải thích cặn kẽ đến đâu, đầu óc bọn chúng cũng chẳng đủ dung lượng để tiếp thu."
T["STsp_08_01.44"] = "Đúng là đàn gảy tai trâu...==W== Hahaha!"
T["STsp_08_01.45"] = "Cậu ăn nói y hệt mấy vị giáo sư khó tính ở Học Viện Ánh Sáng Grace hồi xưa vậy! Hahaha!"
T["STsp_08_01.46"] = "Học viện Grace của chúng ta đời nào thèm tuyển loại học viên tối dạ đến mức đó! Và chắc chắn chẳng bao giờ tổ chức một buổi tranh luận ngớ ngẩn như thế."
T["STsp_08_01.47"] = "Haizz... Học Viện Ánh Sáng Grace. Tôi nhớ thời sinh viên của chúng ta ghê."
T["STsp_08_01.48"] = "Hồi đó nếu cậu không gặp tôi thì ai mà biết được chứ? Khéo cậu đã rẽ sang một con đường hoàn toàn khác rồi."
T["STsp_08_01.49"] = "Hai năm trước—"
T["STsp_08_01.50"] = "Đế Quốc Grace, Học Viện Ánh Sáng Grace"
T["STsp_08_01.51"] = "Bảo tàng Sinh Vật Học"
T["STsp_08_01.52"] = "Thành Phố Emor"
T["STsp_08_01.53"] = "Một nữ sinh viện nghiên cứu tài năng và kiêu hãnh..."
T["STsp_08_01.54"] = "... cùng một đàn chị khóa trên đầy tham vọng, sẵn sàng dấn thân vào bất cứ thứ gì để đạt được đột phá."
T["STsp_08_01.55"] = "Lần đầu gặp gỡ tại phòng trưng bày tiêu bản, hai tâm hồn cuồng nhiệt vì tri thức đã lập tức va vào nhau."
T["STsp_08_01.56"] = "Coronis"
T["STsp_08_01.57"] = "Chị Igna... Bản báo cáo này là thật sao?"
T["STsp_08_01.58"] = "Đương nhiên. Tôi chưa bao giờ đùa giỡn với nghiên cứu khoa học cả."
T["STsp_08_01.59"] = "Cấu trúc sinh học của Đêm Trường Vĩnh Cửu... Quả thực là một bước ngoặt vĩ đại làm đảo lộn mọi quy ước từ trước đến nay."
T["STsp_08_01.60"] = "Thế nhưng, nếu công bố thứ này, Giáo hội và Tòa Án Thẩm Phán Hoàng Hôn sẽ không để yên đâu."
T["STsp_08_01.61"] = "Vậy thì sao chứ? Chân lý là chân lý. Chẳng có bất kỳ giáo điều cổ hủ nào có thể che giấu được ánh sáng của sự thật."
T["STsp_08_01.62"] = "Haha... Quả đúng là phong cách của chị."
T["STsp_08_01.63"] = "Hôm nay tôi đến đây không phải chỉ để nghe cậu than vãn về phiên tòa đâu, Coronis."
T["STsp_08_01.64"] = "Tôi biết. Chị là Mắt Grace của hoàng gia. Chị đâu rảnh rỗi đến mức ghé thăm một kẻ tử tù nếu không có mục đích gì."
T["STsp_08_01.65"] = "Cậu thông minh lắm. Nghe đây, tôi đã bí mật chuẩn bị xong mọi thứ rồi."
T["STsp_08_01.66"] = "Chuẩn bị cái gì?"
T["STsp_08_01.67"] = "Kế hoạch đào tẩu."
T["STsp_08_01.68"] = "Hả? Đào tẩu sao? Chị điên rồi à, Igna? Nhà Tù Số 7 được bố phòng cẩn mật thế nào chị là người rõ nhất chứ."
T["STsp_08_01.69"] = "Đương nhiên tôi biết. Thế nên đây mới là một kế hoạch hoàn hảo."
T["STsp_08_01.70"] = "Thuốc chết giả do chính tay tôi điều chế. Nó sẽ khiến tim cậu ngừng đập, nhịp thở tắt hẳn trong vòng sáu tiếng."
T["STsp_08_01.71"] = "Đám Thẩm Phán Hoàng Hôn sẽ nghĩ cậu đã tự vẫn vì sợ hãi án treo cổ."
T["STsp_08_01.72"] = "Sau đó, thi thể của cậu sẽ được chuyển đến bãi tha ma ngoại ô thành phố. Người của tôi sẽ mai phục sẵn ở đó để đón cậu ra."
T["STsp_08_01.73"] = "Thuốc chết giả... Nghe liều lĩnh đấy. Nhưng cũng rất khoa học."
T["STsp_08_01.74"] = "Tỉ lệ thành công là bao nhiêu?"
T["STsp_08_01.75"] = "Chín mươi chín phần trăm. Một phần trăm còn lại phụ thuộc vào việc cậu có đủ can đảm nuốt viên thuốc này hay không."
T["STsp_08_01.76"] = "Hah, tôi mà lại thiếu can đảm sao? Tôi chỉ lo lắng về dữ liệu thực nghiệm sau khi uống nó thôi."
T["STsp_08_01.77"] = "Đúng là đồ cuồng nghiên cứu hết thuốc chữa... Cầm lấy."
T["STsp_08_01.78"] = "Một viên thuốc nhỏ màu đỏ thẫm được nhét vào lòng bàn tay Coronis."
T["STsp_08_01.79"] = "Giờ hành quyết dự kiến vào sáng mai. Uống nó trước lúc nửa đêm."
T["STsp_08_01.80"] = "Hiểu rồi. Cảm ơn chị, Igna."
T["STsp_08_01.81"] = "Đừng vội cảm ơn. Sống sót ra khỏi đây rồi hãy nói."
T["STsp_08_01.82"] = "Còn một chuyện nữa... Nghiên cứu của cậu về Thể Tinh Tú và Hồn Thạch, tôi đã sao chép lại toàn bộ rồi giấu ở một nơi an toàn rồi."
T["STsp_08_01.83"] = "Chị chu đáo thật đấy. Đúng là không uổng công tôi chia sẻ dữ liệu với chị."
T["STsp_08_01.84"] = "Bảo trọng đấy, Coronis. Đừng có chết thật đấy nhé."
T["STsp_08_01.85"] = "Chị cũng vậy. Cẩn thận đừng để đám Mắt Grace phát hiện ra sơ hở."
T["STsp_08_01.86"] = "Bóng lưng Igna khuất dần sau cánh cửa sắt nặng nề."
T["STsp_08_01.87"] = "Căn phòng giam lại chìm vào bóng tối tịch mịch."
T["STsp_08_01.88"] = "Coronis nhìn viên thuốc trong tay, khóe môi khẽ nhếch lên một nụ cười mãn nguyện."
T["STsp_08_01.89"] = "Một cuộc thí nghiệm vĩ đại trên chính cơ thể mình... Thú vị thật đấy."
# STsp_08_01.90 is binary control line, preserved as EN!
T["STsp_08_01.91"] = "Bất kể cái chết có ập đến hay không, chân lý sẽ mãi trường tồn."
T["STsp_08_01.92"] = "Thời khắc cuối cùng rồi cũng đến."
T["STsp_08_01.93"] = "Tạm biệt nhé, thế giới ngột ngạt này."
T["STsp_08_01.94"] = "Chờ đến khi tôi mở mắt lần nữa..."
T["STsp_08_01.95"] = "... tôi sẽ vạch trần mọi bức màn bí mật của Thần Ân Điển."
T["STsp_08_01.96"] = "Ực."
T["STsp_08_01.97"] = "Viên thuốc tan nhanh trong cuống họng."
T["STsp_08_01.98"] = "Ý thức dần rơi vào hố sâu thăm thẳm..."

# STsp_08_02 (86 items)
T["STsp_08_02.3"] = "Hai tháng trước khi Coronis bị bắt giam—"
T["STsp_08_02.4"] = "Hừm. Phòng thí nghiệm đang cần một Di Vật kính phóng đại tiêu cự cao mới. Thêm nữa, dung dịch bảo quản mẫu vật của mình cũng sắp cạn rồi..."
T["STsp_08_02.5"] = "À đúng rồi. Chị Igna cũng đang muốn có một bộ dao mổ mới. Tiện chuyến đi tới Cự Tháp này, mình sẽ ước luôn cả bộ dao mổ cho chị ấy."
T["STsp_08_02.6"] = "Cơ mà... mình cần một lý do che mắt thật hợp lý mới được. Nếu để chị Igna biết mình lén mò vào khu vực nguy hiểm thế này..."
T["STsp_08_02.7"] = "Hửm? Tiếng động gì thế kia?"
T["STsp_08_02.8"] = "Ủa? Một Thể Tinh Tú sao?"
T["STsp_08_02.9"] = "Không đúng... Sinh vật này trông dị thường quá. Cấu trúc cơ thể của nó hoàn toàn không giống với bất kỳ loài nào từng được ghi chép."
T["STsp_08_02.10"] = "Lạ kỳ thật... Lượng ma lực tỏa ra từ nó thuần khiết đến khó tin, nhưng lại chẳng hề mang dấu vết của Hồn Thạch."
T["STsp_08_02.11"] = "Sinh Vật Bí Ẩn"
T["STsp_08_02.12"] = "Gừ gừ..."
T["STsp_08_02.13"] = "Đừng sợ, bé con. Lại đây nào... Để tôi xem thử cấu tạo giải phẫu của em một chút thôi nhé."
T["STsp_08_02.14"] = "Coronis từ từ tiến lại gần, đôi mắt sáng rực lên vì phấn khích khoa học."
T["STsp_08_02.15"] = "Một mẫu vật hiếm có khó tìm! Cơ hội nghìn năm có một!"
T["STsp_08_02.16"] = "Nào, ngoan nào... Chỉ chích một chút máu thôi, sẽ không đau đâu..."
T["STsp_08_02.17"] = "Grào—!"
T["STsp_08_02.18"] = "Một đợt sóng xung kích ma thuật dữ dội bất ngờ bùng nổ!"
T["STsp_08_02.19"] = "Cái gì—?! Luồng năng lượng này..."
T["STsp_08_02.20"] = "Nó tự phát sinh ma lực mà không cần thông qua mạch chuyển hóa thông thường?!"
T["STsp_08_02.21"] = "Không thể tin được! Giả thuyết bấy lâu nay của mình hoàn toàn chính xác!"
T["STsp_08_02.22"] = "Thần Ân Điển không phải là cội nguồn duy nhất của ma thuật!"
T["STsp_08_02.23"] = "Có những sinh vật sinh ra đã hòa làm một với tự nhiên, tự thân sản sinh ra nguồn sống và phép thuật vĩnh hằng!"
T["STsp_08_02.24"] = "Bé con à, em chính là chìa khóa mở ra cánh cửa chân lý mới!"
T["STsp_08_02.25"] = "Sinh vật dường như cảm nhận được sự thiện chí không chút ác tâm của Coronis, dần dần dịu lại."
T["STsp_08_02.26"] = "Nó khẽ dụi đầu vào lòng bàn tay cô."
T["STsp_08_02.27"] = "Đúng rồi, ngoan lắm. Chúng ta sẽ là những người bạn tốt."
T["STsp_08_02.28"] = "Tôi sẽ đặt tên cho em là... Bayan."
T["STsp_08_02.29"] = "Tộc Bayan kiêu hãnh của vùng đất cổ tích."
T["STsp_08_02.30"] = "Kể từ hôm đó, một mối liên kết kỳ lạ đã hình thành giữa nữ học giả lập dị và sinh vật huyền bí."
T["STsp_08_02.31"] = "Nhưng những ngày tháng êm đềm chẳng kéo dài được bao lâu."
T["STsp_08_02.32"] = "Sự tồn tại của Bayan đã nhanh chóng lọt vào tầm ngắm của Tòa Án Thẩm Phán Hoàng Hôn."
T["STsp_08_02.33"] = "Một buổi chiều nọ, khi Coronis đang cặm cụi ghi chép số liệu trong căn cứ bí mật..."
T["STsp_08_02.34"] = "Rầm!"
T["STsp_08_02.35"] = "Cánh cửa phòng bật tung dưới lực đạp tàn bạo của đám lính vũ trang."
T["STsp_08_02.36"] = "Thẩm Phán Hoàng Hôn"
T["STsp_08_02.37"] = "Coronis! Cô bị bắt vì tội che giấu sinh vật dị giáo và nghiên cứu tà thuật!"
T["STsp_08_02.38"] = "Giao nộp con quái vật đó ra đây mau!"
T["STsp_08_02.39"] = "Nó không phải là quái vật! Nó là một dạng sống hoàn mỹ!"
T["STsp_08_02.40"] = "Im miệng! Bắt lấy cô ta!"
T["STsp_08_02.41"] = "Bayan gầm lên giận dữ, lao ra chắn trước mặt Coronis."
T["STsp_08_02.42"] = "Bayan, chạy đi! Đừng lo cho tôi! Chạy mau!"
T["STsp_08_02.43"] = "Grào—!"
T["STsp_08_02.44"] = "Nhát kiếm ma thuật tàn độc của tên Thẩm Phán chém sượt qua sườn Bayan, khiến máu tươi bắn tung tóe."
T["STsp_08_02.45"] = "Không—! Dừng tay lại!"
T["STsp_08_02.46"] = "Dưới làn mưa hỏa lực ma đạo áp đảo, Bayan bị trọng thương nhưng vẫn liều mạng phá vòng vây thoát ra ngoài rừng sâu."
T["STsp_08_02.47"] = "Đuổi theo con thú đó mau!"
T["STsp_08_02.48"] = "Bỏ đi, bắt được ả đầu sỏ này là đủ lập công với Đại nhân rồi."
T["STsp_08_02.49"] = "Xiềng xích sắt lạnh ngắt siết chặt cổ tay Coronis."
T["STsp_08_02.50"] = "Hừ, đám giáo điều mục ruỗng các người... rồi sẽ có ngày phải trả giá cho sự ngu muội của mình."
T["STsp_08_02.51"] = "Để xem đến lúc lên giá treo cổ, cái miệng của cô còn cứng được như thế này không!"
T["STsp_08_02.52"] = "Coronis bị giải đi trong ánh nhìn miệt thị của đám quân lính."
T["STsp_08_02.53"] = "Thế nhưng trong lòng cô lại ngập tràn sự thanh thản."
T["STsp_08_02.54"] = "Ít nhất... Bayan đã trốn thoát an toàn."
T["STsp_08_02.55"] = "Hạt mầm chân lý đã được gieo rắc, và không một thế lực nào có thể dập tắt nó được nữa."
T["STsp_08_02.56"] = "Trong ngục tối, Coronis nhớ lại những ngày tháng say mê nghiên cứu."
T["STsp_08_02.57"] = "Chị Igna... Liệu chị có hiểu được những gì em đang theo đuổi không?"
T["STsp_08_02.58"] = "Chắc chắn là có. Chị ấy thông minh hơn bất kỳ ai trong cái đế quốc này."
T["STsp_08_02.59"] = "Cứ đợi đấy. Ván cờ này vẫn chưa kết thúc đâu."
T["STsp_08_02.60"] = "Những bước chân vội vã vang lên bên ngoài hành lang nhà ngục."
T["STsp_08_02.61"] = "Thời khắc chuyển giao số phận đã điểm."
T["STsp_08_02.62"] = "Coronis hít một hơi thật sâu, chuẩn bị tinh thần đón nhận thử thách tiếp theo."
T["STsp_08_02.63"] = "Cánh cửa phòng giam khẽ kẽo kẹt mở ra."
T["STsp_08_02.64"] = "Một bóng người quen thuộc bước vào."
T["STsp_08_02.65"] = "Và câu chuyện lại quay về với điểm bắt đầu..."
T["STsp_08_02.66"] = "Một cuộc hội ngộ giữa ngục tù tăm tối, mở ra con đường dẫn tới tự do."
T["STsp_08_02.67"] = "Chỉ cần còn giữ trọn niềm tin vào chân lý khoa học..."
T["STsp_08_02.68"] = "... thì dẫu có rơi vào hố sâu tuyệt vọng, ánh sáng của tri thức vẫn sẽ soi rọi tương lai."
T["STsp_08_02.69"] = "Coronis thầm mỉm cười."
T["STsp_08_02.70"] = "Cuộc đời này thực sự quá đỗi kỳ diệu."
T["STsp_08_02.71"] = "Và hành trình khám phá thế giới của cô chỉ vừa mới bắt đầu."
T["STsp_08_02.72"] = "Tiếng chuông nhà thờ ngân vang từ xa xăm."
T["STsp_08_02.73"] = "Báo hiệu một ngày mới sắp sửa khai màn."
T["STsp_08_02.74"] = "Một ngày mới tràn đầy những bí ẩn đang chờ đợi được giải mã."
T["STsp_08_02.75"] = "Và cô đã sẵn sàng đón nhận tất cả."
T["STsp_08_02.76"] = "Không chút sợ hãi. Không chút nao núng."
T["STsp_08_02.77"] = "Đó chính là phong thái của Coronis."
T["STsp_08_02.78"] = "Nữ học giả của chân lý và tự do."
T["STsp_08_02.79"] = "Kẻ thách thức những giáo điều mục nát."
T["STsp_08_02.80"] = "Ngọn đuốc soi đường giữa màn đêm tăm tối."
T["STsp_08_02.81"] = "Dù cái giá phải trả có là tính mạng..."
T["STsp_08_02.82"] = "... cô cũng chưa từng một lần hối tiếc."
T["STsp_08_02.83"] = "Bởi vì trên đời này..."
T["STsp_08_02.84"] = "... chẳng có điều gì đáng giá hơn sự thật."
T["STsp_08_02.85"] = "Và sự thật thì không bao giờ chết."
T["STsp_08_02.86"] = "Nó sẽ sống mãi trong dòng chảy bất tận của thời gian."

# STsp_08_03 (87 items)
T["STsp_08_03.2"] = "Hồi 3"
T["STsp_08_03.3"] = "Tù Nhân Của Chân Lý (Phần III)"
T["STsp_08_03.4"] = "Để thực hiện một cống hiến khoa học cuối cùng cho cuộc đời, Coronis bình thản nuốt trọn viên độc dược."
T["STsp_08_03.6"] = "Tháng ???"
T["STsp_08_03.7"] = "Ngày ??"
T["STsp_08_03.8"] = "Đế Quốc Grace"
T["STsp_08_03.9"] = "Bãi Tha Ma Ngoại Ô"
T["STsp_08_03.10"] = "Tiếng quạ kêu thê lương trong màn đêm giá lạnh."
T["STsp_08_03.11"] = "Một chiếc xe ngựa cũ kỹ chở xác chầm chậm lăn bánh trên con đường mòn lầy lội."
T["STsp_08_03.12"] = "Phu Xe"
T["STsp_08_03.13"] = "Chẹp, xui xẻo thật... Nửa đêm hôm khuya khoắt lại phải đi chở xác một ả phù thủy dị giáo."
T["STsp_08_03.14"] = "Biết thế đòi thêm vài đồng Dorra công cán cho bõ ghét."
T["STsp_08_03.15"] = "Gió lạnh thổi rít từng cơn qua hàng cây trơ trụi lá."
T["STsp_08_03.16"] = "Bất chợt, một bóng đen to lớn vụt qua trước mũi ngựa!"
T["STsp_08_03.17"] = "Hí hí—!"
T["STsp_08_03.18"] = "Con ngựa hoảng loạn lồng lộn lên, suýt lật cả cỗ xe."
T["STsp_08_03.19"] = "Cái quái gì thế này?! Yêu quái phương nào?!"
T["STsp_08_03.20"] = "Một bóng người trùm áo choàng đen thong dong bước ra từ bụi rậm."
T["STsp_08_03.21"] = "Bóng Đen"
T["STsp_08_03.22"] = "Để chiếc xe lại. Và cút đi nếu còn muốn giữ cái mạng quèn của mình."
T["STsp_08_03.23"] = "M-Mẹ ơi! Cứu mạng!"
T["STsp_08_03.24"] = "Tên phu xe vứt cả roi ngựa, cuống cuồng cắm đầu chạy thục mạng vào bóng đêm."
T["STsp_08_03.25"] = "Người trùm áo choàng tiến lại gần thùng xe, gạt tấm vải liệm đay rách nát sang một bên."
T["STsp_08_03.26"] = "Dưới ánh trăng mờ ảo, gương mặt Coronis tái nhợt không chút huyết sắc."
T["STsp_08_03.27"] = "Bóng Đen"
T["STsp_08_03.28"] = "Đúng là cô bé rồi... Đúng như những gì Igna đã dặn dò."
T["STsp_08_03.29"] = "Mau lấy thuốc giải ra đây."
T["STsp_08_03.30"] = "Một lọ thuốc nước phát ra ánh huỳnh quang xanh biếc được nhỏ cẩn thận vào miệng Coronis."
T["STsp_08_03.31"] = "Vài phút trôi qua trong bầu không khí nghẹt thở."
T["STsp_08_03.32"] = "Khụ... Khụ khụ!"
T["STsp_08_03.33"] = "Lồng ngực Coronis khẽ phập phồng trở lại."
T["STsp_08_03.34"] = "Cô ho sặc sụa, hơi thở ấm áp từ từ tràn ngập buồng phổi."
T["STsp_08_03.35"] = "Ánh mắt Coronis chậm rãi mở ra, chớp chớp để thích nghi với ánh sáng leo lét của ngọn đuốc."
T["STsp_08_03.36"] = "Đây là... thiên đường của các học giả sao?"
T["STsp_08_03.37"] = "Hay là... một cõi hư vô khác?"
T["STsp_08_03.38"] = "Người trùm áo choàng bật cười khúc khích."
T["STsp_08_03.39"] = "Chào mừng trở lại trần thế, Coronis."
T["STsp_08_03.40"] = "Giọng nói này... Là chị sao, Igna?!"
T["STsp_08_03.41"] = "Chứ còn ai vào đây nữa? Cậu nghĩ tôi sẽ để một tài năng xuất chúng như cậu chết rục trong cái nhà ngục bẩn thỉu đó thật à?"
T["STsp_08_03.42"] = "Haha... Vậy ra tôi chưa chết thật."
T["STsp_08_03.43"] = "Thuốc chết giả của chị... hiệu quả đến chín mươi chín phần trăm cơ mà."
# STsp_08_03.44 is binary control line, preserved as EN!
T["STsp_08_03.45"] = "Đúng là như một giấc mộng dài vậy."
T["STsp_08_03.46"] = "Bây giờ cậu đã chính thức là một 'người chết' trên danh nghĩa của Đế Quốc Grace rồi."
T["STsp_08_03.47"] = "Từ nay về sau, cậu hoàn toàn tự do."
T["STsp_08_03.48"] = "Tự do... Một từ ngữ thật đẹp đẽ."
T["STsp_08_03.49"] = "Thế còn chị thì sao, Igna? Làm việc này chị có gặp nguy hiểm không?"
T["STsp_08_03.50"] = "Lo cho cái thân cậu trước đi. Tôi là Mắt Grace cơ mà, ai dám nghi ngờ tôi chứ."
T["STsp_08_03.51"] = "Hơn nữa, một cánh cửa mới vừa mở ra trước mắt cậu đấy."
T["STsp_08_03.52"] = "Cánh cửa gì cơ?"
T["STsp_08_03.53"] = "Lữ Đoàn Tân Tinh."
T["STsp_08_03.54"] = "Một nhóm Lữ Khách tự do, không chịu sự ràng buộc của bất kỳ giáo hội hay thể chế quyền lực nào."
T["STsp_08_03.55"] = "Họ có một vị Sếp vô cùng đặc biệt. Một người sẵn sàng dang tay chào đón những kẻ lạc loài mang trong mình lý tưởng lớn."
T["STsp_08_03.56"] = "Lữ Đoàn Tân Tinh... Nghe thú vị đấy."
T["STsp_08_03.57"] = "Tôi đã thu xếp để cậu gia nhập cùng bọn họ rồi. Chiếc xe này sẽ đưa cậu rời khỏi lãnh thổ Đế Quốc Grace ngay trong đêm."
T["STsp_08_03.58"] = "Còn Bayan thì sao? Em ấy..."
T["STsp_08_03.59"] = "Gừ gừ—!"
T["STsp_08_03.60"] = "Từ trong bóng tối rậm rạp, sinh vật có sừng lao vút ra, mừng rỡ dụi đầu vào vòng tay Coronis."
T["STsp_08_03.61"] = "Bayan! Em vẫn an toàn! Tuyệt vời quá!"
T["STsp_08_03.62"] = "Nó đã đợi cậu ở đây suốt hai ngày nay rồi đấy. Đúng là một sinh vật trung thành và hiểu chuyện."
T["STsp_08_03.63"] = "Cảm ơn chị... Cảm ơn chị rất nhiều, Igna."
T["STsp_08_03.64"] = "Thôi nào, đừng có sến súa như thế, chẳng giống phong cách nữ học giả lạnh lùng của cậu chút nào cả."
T["STsp_08_03.65"] = "Lên đường đi. Tương lai rộng lớn ngoài kia đang vẫy gọi cậu đấy."
T["STsp_08_03.66"] = "Hãy tiếp tục nghiên cứu, tiếp tục vạch trần chân lý."
T["STsp_08_03.67"] = "Và nhớ chứng minh cho cả thế giới này thấy: Thần Ân Điển không phải là tất cả."
T["STsp_08_03.68"] = "Nhất định rồi. Tôi hứa với chị."
T["STsp_08_03.69"] = "Coronis bước lên cỗ xe mới, bên cạnh là người bạn đồng hành trung thành Bayan."
T["STsp_08_03.70"] = "Bánh xe lại bắt đầu lăn, đưa cô hướng về vùng đất mới đầy hứa hẹn."
T["STsp_08_03.71"] = "Nơi có những người bạn đồng đội đang đón chờ."
T["STsp_08_03.72"] = "Nơi một chương mới của cuộc đời chính thức mở ra."
T["STsp_08_03.73"] = "Một cuộc hành trình không còn bị giam cầm trong những bức tường ngục tối."
T["STsp_08_03.74"] = "Một cuộc phiêu lưu tự do dưới bầu trời đầy sao."
T["STsp_08_03.75"] = "Coronis khẽ đưa tay hứng lấy một ngọn gió đêm mát lành."
T["STsp_08_03.76"] = "Thế giới này quả thực vô cùng rộng lớn."
T["STsp_08_03.77"] = "Và còn biết bao điều kỳ diệu đang đợi được giải mã."
T["STsp_08_03.78"] = "Lữ Đoàn Tân Tinh, tôi đến đây."
T["STsp_08_03.79"] = "Sếp... hãy chuẩn bị tinh thần tiếp đón nhà nghiên cứu tài ba nhất thế giới này đi nhé."
T["STsp_08_03.80"] = "Nụ cười rạng rỡ nở trên môi cô gái trẻ."
T["STsp_08_03.81"] = "Màn đêm dần lùi xa về phía sau."
T["STsp_08_03.82"] = "Phía chân trời đằng đông, những tia nắng bình minh đầu tiên bắt đầu ló rạng."
T["STsp_08_03.83"] = "Báo hiệu một kỷ nguyên mới của tự do và chân lý."
T["STsp_08_03.84"] = "Và Coronis đã sẵn sàng bước vào ánh bình minh rực rỡ đó."
T["STsp_08_03.85"] = "Cùng với tất cả đam mê và lòng quả cảm của một học giả chân chính."
T["STsp_08_03.86"] = "Tạm biệt quá khứ tăm tối."
T["STsp_08_03.87"] = "Chào tương lai tươi sáng phía trước."

print(f"Defined {len(T)} curated translations for STsp_08.")

# Validation and export
out_dict = {}
errors = []

for it in items:
    iid = it["id"]
    en = it["en"]
    tokens = it.get("tokens", [])
    
    # Binary control line preservation
    if CTRL_PATTERN.search(en) or iid in ["STsp_08_01.90", "STsp_08_03.44"]:
        vi = en
    elif iid in T:
        vi = unicodedata.normalize("NFC", T[iid].strip())
    else:
        # Fallback to current_vi with calque clean
        cur = it.get("current_vi", en)
        cur = cur.replace("Viên Hồn Thạch", "Hồn Thạch").replace("Hòn Hồn Thạch", "Hồn Thạch")
        cur = cur.replace("Trọng Tài Hoàng Hôn", "Thẩm Phán Hoàng Hôn").replace("Trọng Tài Chạng Vạng", "Thẩm Phán Hoàng Hôn")
        cur = cur.replace("chết tiệt", "chết thật").replace("cái quái gì", "chuyện quái quỷ gì")
        vi = unicodedata.normalize("NFC", cur.strip())
        
    # Check tokens
    st = sorted(TAG_PATTERN.findall(en))
    dt = sorted(TAG_PATTERN.findall(vi))
    if st != dt:
        errors.append(f"Token mismatch in {iid}: src={st} vs dst={dt}")
        
    out_dict[iid] = vi

print(f"STsp_08 compiled: {len(out_dict)} items, {len(errors)} errors.")
if errors:
    for e in errors[:10]:
        print(" ", e)
else:
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out_dict, f, ensure_ascii=False, indent=2)
    print(f"Saved {OUT_FILE.name} successfully!")
