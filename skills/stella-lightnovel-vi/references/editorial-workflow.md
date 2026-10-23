# Thao tác biên tập cảnh

## Lựa chọn văn phong bên trong ràng buộc

Người dùng muốn nhịp light novel isekai/harem và hài Việt tiết chế. Câu đích nên có chủ ý về nhịp, tôn trọng cá tính từng người. Không có quota tiếng cười, kính ngữ hoặc câu cửa miệng. Không có quy tắc cấm toàn bộ bị/được/câu cụt. Giữ chức năng của câu nguồn và mức thông tin trước khi làm mượt.

Đại từ theo người nói/người nghe/quan hệ đã có căn cứ, không theo template tớ–cậu chung. Nguồn chưa rõ có thể lược đại từ nếu vẫn bảo toàn chủ thể, hoặc pending_context. Không mượn mẫu chuẩn của một cặp nhân vật để chốt cặp khác.

## Các lượt làm việc

1. Chốt source, locale/version, ID/field được sửa và kiểu nội dung. Xác nhận adapter giữ token/timing. Giữ prefix/tag lạ để điều tra, không xóa như rác regex.
2. Lập context cả cảnh: ai nói/ai nghe, nói thật/nội tâm/trích dẫn, nhánh và những điều mỗi người biết. Giữ unknown có lý do. Đừng coi thứ tự constant pool là event order.
3. Dịch ý trước: phủ định, chủ thể, người nhận, mức chắc chắn, số/điều kiện và ý đùa. Chỉnh câu Việt, đọc liền để thấy chủ ngữ lặp/mơ hồ và nhịp đáp.
4. So lại nguồn sau khi làm mượt. Đánh dấu từ/cấu trúc thêm vào có đổi thông tin, mức thân mật, văn hóa hoặc thái độ không. Bản địa hóa quá mức có thể xảy ra dù câu rất tự nhiên.
5. Ghi phương án khó và scope vào sổ quyết định; kiểm kỹ thuật, đóng băng và review độc lập. Chưa có ý kiến người dùng về mẫu gu thì không gọi đó là người dùng đã phê duyệt phong cách.

## Nhận diện lỗi quan trọng

Sai người làm/người nghe, bịa chi tiết/romance, hỏng ID/token hoặc nguồn không khớp là blocker. Tiếng lóng/cà khịa quá mức, điểm nhìn lệch hoặc đại từ làm đổi quan hệ cần sửa trước khi đưa làm mẫu. Preference nhẹ phải có lý do, không đổi vì reviewer thích một từ khác mà phá nhất quán.

Lời thoại “Please tell me you're joking” có thể diễn đạt theo quan hệ đã chốt mà không thêm chuyện quá khứ. Không tự sáng tác một tai nạn để làm câu đáp vui. Ví dụ nguồn tự tạo phải được gắn nhãn synthetic, không nhập vào corpus game đã duyệt.

## Kết hợp các tài nguyên

Project docs là revision đầy đủ của quy chuẩn. Character context cung cấp evidence nhân vật; golden corpus cung cấp ví dụ kỹ thuật dịch và rationale, không tạo canon mới. Một nguồn/update làm text/context đổi thì phải rebase và review lại. Cả hai nguồn cần được kiểm file/hash thay vì dựa tên thư mục.

## Glossary và sense thực thể

Trạng thái approved không làm một nghĩa áp dụng cho mọi từ đồng hình. Kiểm note/phạm vi thực thể và ngữ cảnh; nếu không khớp, ghi conflict và đề xuất có scope để reviewer xét. Giữ nguyên tên nguồn trong proposal có thể phù hợp hơn gán sai nghĩa, nhưng không tự đổi glossary chuẩn hay coi phân loại thực thể chưa biết là đã xác nhận.
