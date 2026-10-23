# Rubric review văn phong và cảnh mẫu

Đọc nguồn, context rồi bản VI của cả cảnh/đơn vị tài nguyên; không duyệt chỉ vì câu trôi chảy hoặc checker pass. Đây là rubric biên tập của dự án, không phải thang điểm chứng nhận toàn game.

## Nội dung phải xem

| Mặt kiểm | Câu hỏi thực tế |
|---|---|
| Nghĩa | Ai làm gì với ai? Có thêm/bớt ý, sai phủ định, mức chắc chắn, số, điều kiện hoặc trình tự không? |
| Giọng/quan hệ | Đúng người nói/người nghe, vai vế và scope rule? Có tự thêm ngượng ngùng/tán tỉnh/biệt danh không? |
| Tiếng Việt | Câu có tự nhiên, rõ chủ thể và thuận nhịp? Có bám cú pháp nguồn, lặp đại từ hoặc Hán–Việt không cần thiết? |
| Hài và tiết chế | Nguồn có chức năng hài đó không? Có thêm meme, tiếng lóng hay thay văn hóa quá mức không? |
| Cảnh/điểm nhìn | Giữ nhịp câu dẫn–đáp–phản ứng, mức biết, nội tâm/hội thoại, khoảng lặng và nhánh truyện? |
| Kỹ thuật | ID/source/hash, token/ruby/tag, Unicode NFC VI, ngắt dòng/timing theo adapter có được giữ? |
| Chứng cứ | Nguồn exact row/locator, attribution, quyết định và hash bản được duyệt có đọc lại được? |

## Mức lỗi và quyết định

Blocker: sai nghĩa trọng yếu/quan hệ/speaker, thêm sự kiện hoặc romance, hỏng token/ID, nguồn không có thật hoặc review không gắn snapshot. Phải sửa trước khi dùng mẫu.

Major: câu khó hiểu, giọng lệch, hài quá đà, điểm nhìn sai, register hoặc xưng hô không có căn cứ làm đổi sắc thái. Needs_changes nếu còn ảnh hưởng rõ.

Minor: nhịp chưa mượt hoặc từ chưa gọn nhưng nghĩa/giọng vẫn giữ. Ghi cụ thể và xử lý trước khi chọn làm mẫu chuẩn; không dùng tổng điểm cao bù blocker/major. “Tôi thích cách khác hơn” là preference, cần giải thích chứ không mặc nhiên là lỗi.

Quyết định từng scene/claim/edge: accepted_for_calibration, needs_changes, pending_context hoặc excluded_not_representative. Chấp nhận sample không tự approved mọi rule của nhân vật. Một bộ có thể có mẫu được chấp nhận và gap coverage chưa giải quyết; báo tách số lượng.

## Hợp đồng reviewer

Reviewer khác tác giả và chưa sửa input; đọc toàn nguồn/đích/ngữ cảnh và ghi rationale cụ thể cho từng scene. Source/hash đã khóa trước review. Nếu reviewer tự viết lại, người đó thành tác giả phần sửa và cần reviewer khác; cách thường dùng là trả finding để tác giả sửa revision.

Báo cáo có scene_id, candidate_file_sha256, content_sha256 theo hợp đồng corpus, quyết định, lỗi và các mặt đã kiểm, reviewer ID thật. Không sinh approval hàng loạt. File cuối có thể thêm metadata review từ quyết định thật, nhưng content hash phải khớp; đổi chữ/context làm review tương ứng hết hiệu lực.

Không có reviewer độc lập thì giữ pending_review, vẫn tiếp tục soạn/audit. Native readback, font/layout, runtime và gameplay là gate riêng, không nằm trong approval mẫu văn phong.
