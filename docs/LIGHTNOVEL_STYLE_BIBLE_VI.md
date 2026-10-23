# Quy chuẩn văn phong light novel — Stella Sora VI

Revision 20261023_r01. Định hướng người dùng: light novel isekai/harem hiện đại, câu tiếng Việt tự nhiên, hài Việt tiết chế và hạn chế bản địa hóa quá mức. Đây là lựa chọn biên tập của dự án, không phải khẳng định Stella Sora thuộc thể loại hay quan hệ harem.

## Giọng đích

Lời kể gần nhân vật, đối thoại có tương tác và nhịp cảm xúc. Hấp dẫn nhờ lựa chọn từ, độ dài câu, khoảng lặng và góc nhìn có trong nguồn. Giữ mức thân mật, hiểu lầm, ngượng ngùng hoặc tự trào mà cảnh thực sự thể hiện. Không biến toàn bộ dàn nhân vật thành cùng một giọng dễ thương/cà khịa; không tự thêm người yêu, ghen tuông hoặc tán tỉnh.

Câu gọn khi phản ứng nhanh; câu dài hơn khi suy nghĩ/miêu tả cần độ ngân. Không có quota số chữ hoặc số câu đùa. Dịch linh hoạt cú pháp, giữ ai làm gì với ai, mức chắc chắn, thời điểm và quan hệ nhân quả. Có thể lược đại từ khi nghĩa rõ, không dùng văn Nhật/Anh phiên âm bằng từ Việt.

## Theo loại nội dung

| Loại | Cách viết | Điều cần giữ |
|---|---|---|
| Lời kể | Mạch lạc, gợi hình ở mức nguồn cho phép; giữ điểm nhìn | Người quan sát, mức biết, phủ định và phỏng đoán |
| Đối thoại | Tự nhiên, nhịp đáp theo nhân vật/cảnh; không lặp kính ngữ vô cớ | Speaker/listener, vai vế, hàm ý và sắc thái |
| Nội tâm | Có cá tính, có thể dí dỏm khi nguồn có tự trào | Không biến suy nghĩ thành lời nói, không thêm kết luận tâm lý |
| Hồ sơ/thư/chat | Giữ giọng của người viết, form và chữ ký; đối chiếu người nhận xét | Không xem mọi câu trong archive là lời nhân vật sở hữu hồ sơ |
| UI/hệ thống | Ngắn, rõ thao tác, đúng thuật ngữ | Không chèn tấu hài hoặc hoa mỹ cản thao tác |
| Cơ chế/kỹ năng | Chính xác, dễ đọc; tên theo glossary đã khóa | Điều kiện, mục tiêu, số/dấu, thời lượng, thứ tự |
| Subtitle/AVG | Chọn câu đọc được trong nhịp cảnh | Cue, timing, token, mapping ID; layout phải kiểm riêng |

## Tình huống và mức cảm xúc

Đời thường: lời nói nhẹ và linh hoạt. Hài: giữ câu dẫn, cú đáp và phản ứng đúng thứ tự. Căng thẳng: ưu tiên rõ, không đùa thêm để làm nhẹ hiểm nguy. Buồn/đau: tránh tự thêm lời văn bi lụy hoặc danh ngôn. Ngượng/thân mật: không nâng mức quan hệ chỉ để giống truyện harem. Khoảng lặng/dấu ba chấm chỉ giữ hoặc chọn khi có tác dụng đúng nguồn; không rải để tạo cá tính giả.

## Bản địa hóa tiết chế

Được thay trật tự từ, cấu trúc câu, cách xưng/gọi đã đủ căn cứ và thành ngữ tương đương về nghĩa/lực cảm xúc. Giữ tên thế giới, món ăn, địa danh, tiền tệ, tín ngưỡng và hình ảnh quan trọng của nguồn. Không tự thay bằng quán cóc, lương tháng, KPI, bài mạng xã hội hoặc meme Việt. Từ như “toang”, “cà khịa” không phải mặc định; chỉ xét nếu đúng register và người dùng cho phép trong cảnh cụ thể. Ưu tiên lối nói phổ thông bền theo thời gian.

Nếu câu đùa phụ thuộc chơi chữ, ghi cơ chế gây cười và các phương án. Chọn cách giữ thông tin và sắc thái tốt nhất; nếu không chuyển được, dùng cách trung tính hơn và note cho reviewer. Không bịa thêm sự kiện để tạo punchline. Ví dụ minh họa không được đưa vào game như thoại thật.

## Cách dùng bộ tài liệu

Đọc [quy chuẩn câu](VI_SENTENCE_EDITING_GUIDE.md), [hài tiết chế](HUMOR_LOCALIZATION_VI.md), [điểm nhìn](NARRATION_AND_CONTINUITY.md) và [rubric](EDITORIAL_QA_RUBRIC.md) theo phần việc. Tra Voice Bible/matrix của revision đang được dự án chấp nhận, kiểm hash; không suy rule từ status tổng hợp. Chọn mẫu cùng domain/cấu trúc trong [corpus mẫu](../work/editorial/lightnovel_editorial_20261023_r01/GOLDEN_SCENES_VI.jsonl) khi đã có review hợp lệ.

Glossary chuẩn khóa thuật ngữ; tài liệu này không đổi glossary. Nguồn/quan hệ nhân vật/giới hạn kỹ thuật là ràng buộc; văn phong là lựa chọn bên trong ràng buộc đó. Khi STYLE_GUIDE cũ mô tả “hào sảng”, áp dụng theo đúng tên/ngữ cảnh, không tự cổ trang hóa toàn game. Bị động, câu cụt, ngập ngừng vẫn dùng khi tự nhiên và đúng sắc thái.

Các tệp JSONL biên tập là tài liệu/sidecar, chưa có adapter tự áp dụng vào pipeline game. Đạt review tài liệu không đồng nghĩa đã được người dùng nghe/đọc và chốt gu, không thay kiểm runtime/layout.

Khi một từ trùng mặt chữ nhưng khác nghĩa hoặc thực thể, kiểm phạm vi sense của glossary trước. Không áp tên nghĩa kiến trúc cho ngữ cảnh sản phẩm/tổ chức chỉ vì cùng từ. Ghi conflict và quyết định có scope; có thể đề xuất giữ nguyên tên nguồn để tránh gán sai nghĩa, chờ review độc lập. Không tự sửa glossary khóa.
