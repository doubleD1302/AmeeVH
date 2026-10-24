#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compiles complete polished Light Novel Vietnamese for STsp_08 (271 items).
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

# Load existing translations from trans_stsp_08_mod.py if any
import sys
sys.path.append(str(ROOT / "tools/campaign12"))
from trans_stsp_08_mod import D as D_01

T = dict(D_01)

# Curated translations for STsp_08_02 (86 items)
T["STsp_08_02.3"] = "Hai tháng trước khi Coronis bị bắt giam—"
T["STsp_08_02.4"] = "Hừm. Phòng thí nghiệm đang cần một Di Vật kính hiển vi độ phóng đại cao mới. Thêm nữa, dung dịch bảo quản mẫu vật của mình cũng sắp cạn rồi..."
T["STsp_08_02.5"] = "À đúng rồi. Chị Igna cũng đang muốn có một bộ dao mổ mới. Tiện chuyến đi tới Cự Tháp này, mình sẽ ước luôn cả bộ dao mổ cho chị ấy."
T["STsp_08_02.6"] = "Cơ mà... mình cần một lý do ngụy trang thật kín kẽ. Nếu để chị Igna biết mình lén mò vào vùng nguy hiểm thế này..."
T["STsp_08_02.7"] = "Hửm? Tiếng động gì thế kia?"
T["STsp_08_02.8"] = "Ủa? Một Thể Tinh Tú sao?"
T["STsp_08_02.9"] = "Sao chúng lại tràn ra ngoài Cự Tháp thế này?==W=="
T["STsp_08_02.11"] = "Hừ... Rất tốt. Cự Tháp này sẽ lụi tàn trong vài ngày tới.==RT==Rút lui ngay trước khi đợt sóng xung kích quét tới."
T["STsp_08_02.12"] = "Rõ ạ. Nhưng mà... tôi thấy lo quá. Số lượng của chúng đông quá mức.==RT==Nếu người vô tội quanh đây bị cuốn vào đợt bùng nổ năng lượng..."
T["STsp_08_02.13"] = "'Vô tội' ư? Quanh Cự Tháp chỉ toàn lũ Lữ Khách lảng vảng thôi.==RT==Toàn là đám liều mạng bị lòng tham làm mờ mắt, sẵn sàng lao vào chỗ chết để săn quái vật."
T["STsp_08_02.14"] = "Một khi đã tự bước chân vào hang cọp thì phải chấp nhận bị cọp vồ.==RT==Sống chết của bọn chúng không phải việc chúng ta cần bận tâm."
T["STsp_08_02.15"] = "Tuyệt đối tuân lệnh đi. Đừng để lòng trắc ẩn ủy mị của cậu làm hỏng việc lớn."
T["STsp_08_02.18"] = "Chậc. Phiền phức thật đấy."
T["STsp_08_02.19"] = "Hửm? Tiếng động gì thế kia?==W== Phát ra từ phía thang máy..."
T["STsp_08_02.20"] = "Nhìn đống tàn tích Thể Tinh Tú này xem... Có ai đó bị mắc kẹt ở đây sao?"
T["STsp_08_02.21"] = "Không thấy thi thể nào cả. Chắc họ đã chạy thoát rồi...==W====RT==Khoan đã. Kia là... một Lữ Khách bị thương?!"
T["STsp_08_02.22"] = "Thương thế nặng quá... Nếu không cầm máu kịp thời thì nguy to."
T["STsp_08_02.23"] = "Này, tỉnh lại đi! Cậu có nghe thấy tôi nói không?!"
T["STsp_08_02.24"] = "Grào—!"
T["STsp_08_02.25"] = "Chậc—lại thêm một bầy Thể Tinh Tú nữa...==RT==Bám chặt vào tôi! Tôi sẽ đưa cậu ra khỏi đây!"
T["STsp_08_02.26"] = "Một bóng người bất ngờ lao tới từ trong bóng tối!"
T["STsp_08_02.27"] = "Đường kiếm ma thuật sắc lẹm xé toạc không gian, chém tan bầy quái vật chỉ trong chớp mắt."
T["STsp_08_02.28"] = "Kinh ngạc thật... Một sức mạnh áp đảo hoàn toàn."
T["STsp_08_02.29"] = "Người đó quay lại, vung tay thi triển một luồng ánh sáng dịu êm bao bọc lấy vết thương của Lữ Khách."
T["STsp_08_02.30"] = "Vết rách sâu hoắm dần khép miệng lại như có phép màu."
T["STsp_08_02.31"] = "Cô cầm máu bằng ma thuật sao?==RT====W==Khoan đã! Cô đang trị thương hoàn toàn bằng ma thuật đấy ư?!"
T["STsp_08_02.32"] = "Không cần dùng đến bất kỳ Hồn Thạch nào?!"
T["STsp_08_02.33"] = "Người thiếu nữ bí ẩn không trả lời, chỉ lạnh lùng liếc nhìn tôi."
T["STsp_08_02.34"] = "Đôi mắt tím biếc thẳm sâu tựa màn đêm vô tận, cùng đôi sừng cong thanh thoát trên mái tóc bạc."
T["STsp_08_02.35"] = "Dung mạo đó... Cấu trúc sinh học đó..."
T["STsp_08_02.36"] = "Cô ấy... thuộc về Đêm Trường Vĩnh Cửu!"
T["STsp_08_02.37"] = "Chủng tộc huyền thoại trong các truyền thuyết cổ xưa!"
T["STsp_08_02.38"] = "Cơ hội nghìn năm có một! Một mẫu đối tượng nghiên cứu sống sờ sờ ngay trước mắt!"
T["STsp_08_02.39"] = "Thiếu nữ xoay người toan rời đi."
T["STsp_08_02.40"] = "Xin chờ một chút! Đừng đi vội!"
T["STsp_08_02.41"] = "Cô vừa cứu mạng người này, đúng không?"
T["STsp_08_02.42"] = "Cơ chế ma thuật vừa rồi vận hành như thế nào vậy? Cô có thể giải thích cho tôi được không?!"
T["STsp_08_02.43"] = "Thiếu nữ khẽ nhíu mày, có vẻ ngạc nhiên trước thái độ không hề biết sợ hãi của tôi."
T["STsp_08_02.44"] = "Này, cô có thể làm lại lần nữa—==W==à xin lỗi, tôi quên mất chưa tự giới thiệu."
T["STsp_08_02.45"] = "Tôi là Coronis. Tôi có thể hân hạnh được biết quý danh của cô không?==RT==Cô không bắt buộc phải trả lời đâu, nhưng... tôi thực sự muốn biết ai đã ra tay tương cứu."
T["STsp_08_02.46"] = "Tên ta là...==W==<size=30> Noctiluna</size>."
T["STsp_08_02.47"] = "Noctiluna... Cái tên tuyệt đẹp làm sao."
T["STsp_08_02.48"] = "Tôi đưa tay chạm vào vùng cơ vừa được chữa lành của người Lữ Khách."
T["STsp_08_02.49"] = "Không có tế bào hoại tử, không có dấu vết xung đột năng lượng thần thánh."
T["STsp_08_02.50"] = "Toàn bộ mô tế bào đều tái sinh một cách tự nhiên nhờ dòng chảy sinh mệnh thuần khiết!"
T["STsp_08_02.51"] = "... Kỳ diệu thật. Thủy tinh thể vỡ nát tuy không tự phục hồi, nhưng mô xung quanh đã lành lặn tự nhiên. Cơn đau cũng biến mất hoàn toàn...==W== Như vậy có nghĩa là chỉ cần cấu trúc nguyên vẹn, cơ thể hoàn toàn có thể hồi phục 100%?!"
T["STsp_08_02.52"] = "Một thứ ma thuật không thể tin nổi!==RT==Noctiluna, rốt cuộc cơ chế này vận hành kiểu gì thế?!"
T["STsp_08_02.53"] = "Ngươi không sợ ta sao?"
T["STsp_08_02.54"] = "Sợ ư? Tại sao tôi phải sợ một sinh linh tuyệt mỹ và sở hữu tri thức vĩ đại như cô chứ?"
T["STsp_08_02.55"] = "Con người Novia các ngươi... lúc nào cũng xem chúng ta là quái vật dị giáo."
T["STsp_08_02.56"] = "Đó là đám ngu muội bị giáo điều tẩy não thôi! Còn tôi là một nhà khoa học chân chính!"
T["STsp_08_02.57"] = "Với tôi, chân lý và sự thật vượt lên trên mọi định kiến tầm thường!"
T["STsp_08_02.58"] = "<size=30>Được rồi, cô ả này chắc chắn là có vấn đề về đầu óc rồi!!</size>==W====RT==... Thế ra, ngươi thực sự không sợ bọn ta sao?"
T["STsp_08_02.59"] = "Tuyệt đối không! Thậm chí tôi còn muốn mời cô về phòng thí nghiệm của tôi để đàm đạo học thuật nữa kìa!"
T["STsp_08_02.60"] = "Noctiluna thở dài bất lực, nhưng ánh mắt đã bớt đi vài phần cảnh giác."
T["STsp_08_02.61"] = "Ngươi đúng là một kẻ kỳ quặc nhất mà ta từng gặp."
T["STsp_08_02.62"] = "Cảm ơn lời khen của cô! Tôi luôn xem sự lập dị là lời tán dương cao nhất cho một học giả."
T["STsp_08_02.63"] = "Này, cô có thể cho tôi một chút máu để làm mẫu thử được không? Chỉ một giọt thôi cũng được!"
T["STsp_08_02.64"] = "Đừng có được đằng chân lân đằng đầu."
T["STsp_08_02.65"] = "Thôi mà, đi mà... Vì sự tiến bộ của nền văn minh nhân loại mà!"
T["STsp_08_02.66"] = "Ta phải đi rồi. Cự Tháp sắp sụp đổ rồi đấy."
T["STsp_08_02.67"] = "Khoan đã! Ít nhất hãy cho tôi biết làm sao để gặp lại cô chứ!"
T["STsp_08_02.68"] = "Nếu có duyên, chúng ta sẽ tự khắc tương phùng dưới bóng trăng."
T["STsp_08_02.69"] = "Noctiluna tung mình biến mất vào khoảng không tăm tối."
T["STsp_08_02.70"] = "A... Đi mất rồi."
T["STsp_08_02.71"] = "Nhưng bấy nhiêu cũng là quá đủ cho một khám phá chấn động địa cầu!"
T["STsp_08_02.72"] = "Tôi cẩn thận thu thập những mẫu máu vương vãi trên nền đá vào lọ thủy tinh tiệt trùng."
T["STsp_08_02.73"] = "Bằng chứng sống động nhất về một hệ thống ma thuật độc lập!"
T["STsp_08_02.74"] = "Á! Úi chà!"
T["STsp_08_02.75"] = "Tôi không cố ý đâu. Mắt phải của tôi bị hỏng, tầm nhìn hẹp và khả năng nhận biết độ sâu bị liệt hoàn toàn... Tôi chỉ vô tình trượt chân thôi.==W== Noctiluna ơi, mau chữa—"
T["STsp_08_02.76"] = "Quên mất, cô ấy đi rồi."
T["STsp_08_02.77"] = "Coronis tự bật cười trước sự đãng trí của chính mình."
T["STsp_08_02.78"] = "Cô tập tễnh cõng người Lữ Khách bị thương ra khỏi Cự Tháp."
T["STsp_08_02.79"] = "Chuyến đi này quả thực thu hoạch vượt ngoài mọi kỳ vọng."
T["STsp_08_02.80"] = "Một luận văn mang tính cách mạng đang dần hình thành trong tâm trí cô."
T["STsp_08_02.81"] = "Luận văn sẽ làm sụp đổ hoàn toàn tín điều của Giáo hội Đế Quốc Grace."
T["STsp_08_02.82"] = "Và đừng có tự làm mình bị thương nữa đấy. Ta nói thật đấy—đây là lần cuối cùng.==W== Đừng xem thường việc này; nó tiêu tốn một lượng ma lực đáng kể đấy."
T["STsp_08_02.83"] = "Lời dặn dò xa xăm của Noctiluna như vẫn còn văng vẳng bên tai."
T["STsp_08_02.84"] = "Một thiếu nữ ngoài lạnh trong ấm."
T["STsp_08_02.85"] = "Đêm Trường Vĩnh Cửu... Quả thực là một chủng tộc cao quý."
T["STsp_08_02.86"] = "Tôi nhất định sẽ đưa sự thật này ra ngoài ánh sáng."
T["STsp_08_02.87"] = "Dù có phải đối đầu với toàn bộ thế giới."
T["STsp_08_02.88"] = "Đó là lời thề danh dự của một học giả chân chính."
T["STsp_08_02.89"] = "Ta chỉ nói cho ngươi điều này: Những người thuộc Đêm Trường Vĩnh Cửu chúng ta chẳng hề cần thứ mà đám người Novia các ngươi gọi là 'Ân Điển'.==W== Bọn ta không bao giờ hạ mình sử dụng thứ ma thuật chắp vá vay mượn."
T["STsp_08_02.90"] = "Thứ ma thuật tự thân vĩ đại..."
T["STsp_08_02.91"] = "Tôi sẽ chứng minh cho tất cả thấy cô đã đúng, Noctiluna."
T["STsp_08_02.92"] = "Cứ đợi đấy."
T["STsp_08_02.93"] = "Ánh bình minh sẽ sớm ló rạng trên bầu trời đêm."

# Curated translations for STsp_08_03 (87 items)
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
T["STsp_08_03.15"] = "Một phát hiện vô giá. Nhưng sao em không mang nó đến cho chị?==W== Tại sao lại viết một bản luận văn công kích toàn bộ hệ thống Ân Điển rồi ngạo nghễ gửi thẳng lên cho bàn dân thiên hạ cùng thấy chứ?"
T["STsp_08_03.16"] = "Bởi vì đó là chân lý. Chân lý không phải là thứ để giấu giếm hay vụ lợi cá nhân."
T["STsp_08_03.17"] = "Em ngây thơ lắm, Coronis. Sự thật trần trụi chỉ đem lại cái chết cho em thôi."
T["STsp_08_03.18"] = "Nếu cái chết có thể đánh thức những bộ óc đang mê muội, thì đó là một cái giá quá hời."
T["STsp_08_03.19"] = "Gió rít gào bên ngoài khung cửa sổ phòng giam."
T["STsp_08_03.20"] = "Tôi nhớ lại cuộc đối thoại cuối cùng với Igna trước khi bước lên phiên tòa."
T["STsp_08_03.21"] = "Chị ấy đã cố gắng khuyên can tôi, nhưng tôi đã chọn con đường của riêng mình."
T["STsp_08_03.22"] = "Và bây giờ, tôi đang nằm đây, trên cỗ xe tang đưa tiễn một kẻ tử tội."
T["STsp_08_03.23"] = "Nhưng tôi không hề chết."
T["STsp_08_03.24"] = "Trái tim tôi vẫn đang đập, dù chậm rãi đến mức mắt thường không thể phát hiện."
T["STsp_08_03.25"] = "Độc dược của Igna thực sự là một kiệt tác hóa dược học."
T["STsp_08_03.26"] = "Tôi thầm ghi nhớ từng biến đổi sinh lý trong trạng thái chết giả."
T["STsp_08_03.27"] = "Nhiệt độ cơ thể giảm dần về mức môi trường."
T["STsp_08_03.28"] = "Mạch đập khoảng ba nhịp một phút."
T["STsp_08_03.29"] = "Dòng chảy ma lực ngưng trệ hoàn toàn."
T["STsp_08_03.30"] = "Một bản ghi chép thực nghiệm vô giá được lưu trữ trong tâm trí."
T["STsp_08_03.31"] = "Bỗng nhiên, chiếc xe ngựa khựng lại đột ngột!"
T["STsp_08_03.32"] = "Tiếng ngựa hí vang lên thất thanh."
T["STsp_08_03.33"] = "Em thực sự biết quá nhiều rồi đấy.==W== Cầm lấy đi."
T["STsp_08_03.34"] = "Một âm thanh quen thuộc vang lên bên ngoài cỗ xe."
T["STsp_08_03.35"] = "Tiếng kim loại va chạm leng keng, sau đó là tiếng bước chân vội vã tháo chạy của tên phu xe."
T["STsp_08_03.36"] = "Kế hoạch giải cứu đã được kích hoạt."
T["STsp_08_03.37"] = "Tấm vải liệm thô ráp bị lật tung sang một bên."
T["STsp_08_03.38"] = "Một bàn tay ấm áp đặt lên cổ tôi, cẩn thận kiểm tra động mạch cảnh."
T["STsp_08_03.39"] = "Vẫn còn sống. Tốt lắm."
T["STsp_08_03.40"] = "Thuốc giải dạng lỏng mát lạnh được đổ vào miệng tôi."
T["STsp_08_03.41"] = "Dòng nước thuốc nhanh chóng kích hoạt lại hệ tuần hoàn."
T["STsp_08_03.42"] = "==A4==Vị hơi ngọt. Dễ nuốt.==P====RT====A4==Nhưng một cái lưỡi sành sỏi vẫn có thể phát hiện ra được. Lần sau hãy điều chế nó không màu không mùi vị nhé.==P====RT====RT====A4==Hai mươi giây trôi qua. Cảm giác chóng mặt bắt đầu ập tới.==P====RT====RT====A4==Năm mươi giây. Tay chân tê cóng. Tầm nhìn mờ dần...==P====RT====A4==Tác dụng nhanh. Không hộc máu... Để lại một cái xác nguyên vẹn sạch sẽ. Rất tốt."
T["STsp_08_03.43"] = "Đó là những dòng nhật ký suy nghĩ cuối cùng trước khi tôi thiếp đi trong ngục tối."
items_map = {it["id"]: it for it in items}
T["STsp_08_03.44"] = items_map["STsp_08_03.44"]["en"]  # Binary control line
T["STsp_08_03.45"] = "Và bây giờ, tôi đang dần tỉnh lại giữa âm thanh lọc cọc của bánh xe lăn trên sỏi đá."
T["STsp_08_03.46"] = "Mùi sương đêm thanh khiết tràn ngập lồng ngực."
T["STsp_08_03.47"] = "Tôi mở mắt ra."
T["STsp_08_03.48"] = "Không còn là bốn bức tường ngục tối u uất nữa."
T["STsp_08_03.49"] = "Trước mắt tôi là bầu trời đêm bao la với muôn vàn vì tinh tú lấp lánh."
T["STsp_08_03.50"] = "Ha! Vẫn còn đang mơ mộng đấy à?==RT==Rất tiếc phải dập tắt ảo tưởng của cô, thưa Tiểu thư, nhưng đây không phải là cỗ xe ma đâu nhé. Nhìn kìa—Thành Phố Philae đang ở ngay phía trước rồi."
T["STsp_08_03.51"] = "Một người lái xe lạ mặt mỉm cười nói với tôi."
T["STsp_08_03.52"] = "Philae... Thành phố của sự tự do và những khởi đầu mới."
T["STsp_08_03.53"] = "Tôi ngồi dậy, phát hiện bên cạnh mình có một phong thư niêm phong sáp đỏ."
T["STsp_08_03.54"] = "Phong thư của Igna."
T["STsp_08_03.55"] = "Tôi cẩn thận bóc dấu niêm phong ra."
T["STsp_08_03.56"] = "Bên trong là một bức thư tay cùng với một chiếc chìa khóa đồng và một tấm thẻ căn cước mới."
T["STsp_08_03.57"] = "Tên mới của tôi: Bác sĩ Coronis."
T["STsp_08_03.58"] = "Chủ nhân của một phòng khám tư nhân tại khu ổ chuột Philae."
T["STsp_08_03.59"] = "Một thân phận che mắt hoàn hảo cho các hoạt động nghiên cứu bí mật."
T["STsp_08_03.60"] = "Tôi đọc lướt qua những dòng chữ nắn nót quen thuộc của người tiền bối."
T["STsp_08_03.61"] = "Từng câu từng chữ đều thấm đượm sự chu đáo và kỳ vọng lớn lao."
T["STsp_08_03.62"] = "Chiếc xe chầm chậm lăn bánh qua cổng thành Philae."
T["STsp_08_03.63"] = "Thành phố rực rỡ ánh đèn ma đạo hiện ra trước mắt."
T["STsp_08_03.64"] = "Một luồng sinh khí mới mẻ, tách biệt hoàn toàn khỏi sự ngột ngạt giáo điều của Đế Quốc Grace."
T["STsp_08_03.65"] = "Nơi đây sẽ là khởi đầu cho một hành trình vĩ đại."
T["STsp_08_03.66"] = "(Địa chỉ này trùng khớp hoàn hảo.==W== Quả nhiên nằm ẩn mình rất sâu trong khu dân cư.)"
T["STsp_08_03.67"] = "Tôi bước xuống xe, đứng trước một căn nhà nhỏ hai tầng bằng gạch đỏ."
T["STsp_08_03.68"] = "Tấm biển hiệu bằng gỗ ghi dòng chữ: 'Phòng Khám Philae'."
T["STsp_08_03.69"] = "Tôi tra chiếc chìa khóa đồng vào ổ khóa."
T["STsp_08_03.70"] = "Cạch một tiếng thanh thoát, cánh cửa mở ra."
T["STsp_08_03.71"] = "Bên trong là đầy đủ dụng cụ y tế, bàn mổ, và cả một giá sách đầy ắp tư liệu nghiên cứu."
T["STsp_08_03.72"] = "==RT==Coronis, chúc mừng em.==RT==Kể từ hôm nay, em chính thức là thành viên của Hiệp Hội Nghiên Cứu Sự Sống."
T["STsp_08_03.73"] = "Những dòng chữ trong thư vang lên trong tâm tưởng tôi."
T["STsp_08_03.74"] = "==RT==Chúng ta là một tập thể tinh hoa bí mật hoạt động ngay trong lòng Mắt Grace,==RT==chuyên tâm nghiên cứu những chủ đề bị Đế Quốc cấm đoán—ví dụ như Hồn Thạch và cội nguồn ma thuật.==P====RT====RT==Chị tin rằng em sẽ tiếp tục hành trình theo đuổi chân lý tại mảnh đất Philae này.==RT==Chúng tôi rất mong chờ được chia sẻ những phát hiện kỳ thú mà em sắp sửa khai quật được."
T["STsp_08_03.75"] = "Một nụ cười tự hào khẽ nở trên môi tôi."
T["STsp_08_03.76"] = "==RT==Chị đã cho người chuyển toàn bộ đồ đạc của em đến phòng khám rồi.==RT==Trên hồ sơ chính thức của triều đình, chúng đã bị ghi nhận là 'đốt thành tro bụi'.==RT==Nếu cần thêm bất cứ thứ gì, hãy gửi thư cho chị—nhưng nhớ dùng mật danh.==P====RT====RT==Trong mắt của Mắt Grace, cái tên Coronis hiện tại đã hoàn toàn biến mất khỏi cõi đời này."
T["STsp_08_03.77"] = "==RT==Dù sao đi nữa, vật giá ở Philae chẳng hề rẻ rúng chút nào đâu. Mau chóng dọn dẹp phòng khám rồi mở cửa kinh doanh đi nhé. Nhanh lên đấy.==P====RT====RT==Kể từ ngày em rời đi, chị cũng đã tính đến chuyện bỏ việc để ra mở phòng khám riêng rồi.==RT==Thiếu mất em, công việc ở Mắt Grace đúng là tẻ nhạt đến phát rồ."
T["STsp_08_03.78"] = "==RT====RT==Bảo trọng nhé, em gái ở Philae.==RT==—Igna."
T["STsp_08_03.79"] = "Không ngờ chị ấy lại bản lĩnh đến mức này... Vừa trót lọt buôn lậu một tử tội qua mặt đám Thẩm Phán Hoàng Hôn, lại vừa lấy lại được con mắt giả bị tịch thu cho mình...==W== Chị quả thực phi thường đấy, Tiền bối Igna."
T["STsp_08_03.80"] = "Dày công bày binh bố trận vì mình đến thế này. Không biết hồi còn học đại học chị ấy có từng ủ mưu mổ não mình ra để nghiên cứu không nữa...?==W== Theo như những gì viết trong thư này thì xem ra mình chẳng có mấy lựa chọn rồi."
T["STsp_08_03.81"] = "Tôi đeo chiếc kính bảo hộ quen thuộc lên mắt."
T["STsp_08_03.82"] = "Cảm giác sắc bén và lạnh lẽo quen thuộc đã trở lại."
T["STsp_08_03.83"] = "Đã đến lúc bắt tay vào việc rồi."
T["STsp_08_03.84"] = "Phòng khám này sẽ là nơi tôi cứu chữa cho những kẻ khốn cùng..."
T["STsp_08_03.85"] = "... và cũng là căn cứ để vén màn những bí mật vĩ đại nhất của tạo hóa."
T["STsp_08_03.86"] = "Rầm!"
T["STsp_08_03.87"] = "Đột nhiên, cánh cửa phòng khám bị đẩy bật ra một cách thô bạo."
T["STsp_08_03.88"] = "Một bóng người thở hổn hển lao vào, trên lưng cõng theo một người bị thương đầy máu me."
T["STsp_08_03.89"] = "Minova?!"
T["STsp_08_03.90"] = "Một gương mặt quen thuộc của Lữ Đoàn Tân Tinh!"
T["STsp_08_03.91"] = "Bác sĩ! Có bác sĩ ở đây không?!"
T["STsp_08_03.92"] = "Cô chỉ nghe những gì cô muốn nghe thôi đấy à.==W== Được rồi. Nhưng tôi sẽ gọi món đắt đỏ nhất trên thực đơn đấy nhé."
T["STsp_08_03.93"] = "Làm ơn cứu người với!"
T["STsp_08_03.94"] = "Người này bị quái vật trong Cự Tháp tấn công, mất máu nhiều quá rồi!"
T["STsp_08_03.95"] = "Tôi lập tức khoác lên mình chiếc áo blouse trắng, tác phong chuyên nghiệp tái hiện trong tích tắc."
T["STsp_08_03.96"] = "Bác sĩ ơi! Làm ơn, người nhất định phải cứu lấy ==SEX4== với!"
T["STsp_08_03.97"] = "Đặt bệnh nhân lên bàn mổ ngay! Chuẩn bị dao mổ và gạc vô trùng cho tôi!"
T["STsp_08_03.98"] = "Minova, này, bình tĩnh lại đi. Tôi thấy bản thân vẫn ổn mà, thật đấy.==W== Đừng có hoảng loạn làm ầm ĩ lên thế."
T["STsp_08_03.99"] = "Người bệnh nhân thều thào lên tiếng trấn an Minova."
T["STsp_08_03.100"] = "Im lặng và nằm yên đó. Ở đây tôi là người quyết định ai sống ai chết."
T["STsp_08_03.101"] = "Ca phẫu thuật đầu tiên tại Philae... chính thức bắt đầu!"

T["STsp_08_01.99"] = "Có lẽ ngày ấy tôi không nên ngăn cản cậu. Biết đâu nếu cứ chuyên tâm vào môn sinh học thì mọi chuyện đã tốt hơn rồi."
T["STsp_08_01.100"] = "Giải phẫu học hay sinh học... rốt cuộc cũng chẳng có gì khác biệt. Sớm muộn gì tôi cũng sẽ đi đến cùng một kết luận, và tự đặt ra cùng một câu hỏi ấy thôi."
T["STsp_08_01.101"] = "Cũng đúng. Thôi được rồi, hàn huyên thế là đủ. Vào việc chính thôi."
T["STsp_08_01.102"] = "Tôi đến đây theo lệnh của Tòa Án Trọng Tài Hoàng Hôn. Tôi cần ghi lại toàn bộ lời khai của cậu."
T["STsp_08_01.103"] = "Trọng Tài Hoàng Hôn đã ra phán quyết rồi, nhưng chúng ta vẫn phải tuân thủ đúng quy trình thủ tục."
T["STsp_08_01.104"] = "Cậu nói là \"thủ tục\", nhưng thực chất Thiên Nhãn Grace đang sốt sắng muốn biết tôi đã tìm ra được những gì, đúng không?"
T["STsp_08_01.105"] = "Chính xác. Thiên Nhãn Grace chưa bao giờ bỏ qua tri thức.==W== Cho dù đó là tri thức cấm kỵ đi chăng nữa."
T["STsp_08_01.106"] = "Và bản thân cậu cũng đâu muốn phát hiện của mình bị chôn vùi trong bóng tối, đúng chứ Coronis?"
T["STsp_08_01.107"] = "Thế nên xin mời,==W== hãy chia sẻ những phát hiện của cậu đi.==W== Càng cặn kẽ,==W== càng tỉ mỉ càng tốt."

print(f"Total T keys for STsp_08: {len(T)}")

# Export and validation
out_dict = {}
errors = []

for it in items:
    iid = it["id"]
    en = it["en"]
    
    if CTRL_PATTERN.search(en) or iid in ["STsp_08_01.90", "STsp_08_03.44"]:
        vi = en
    elif iid in T:
        vi = unicodedata.normalize("NFC", T[iid].strip())
    else:
        errors.append(f"MISSING TRANSLATION: {iid}")
        vi = it.get("current_vi", en)
        
    st = sorted(TAG_PATTERN.findall(en))
    dt = sorted(TAG_PATTERN.findall(vi))
    if st != dt:
        errors.append(f"Token mismatch in {iid}: src={st} vs dst={dt}")
        
    out_dict[iid] = vi

print(f"STsp_08 compilation result: {len(out_dict)} items, {len(errors)} errors.")
if errors:
    for e in errors[:15]:
        print("  ", e)
else:
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out_dict, f, ensure_ascii=False, indent=2)
    print(f"SUCCESS: Saved {OUT_FILE.name} with 100% token parity!")
