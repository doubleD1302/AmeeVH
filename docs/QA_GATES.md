# Các tầng kiểm chứng

| Gate | Kiểm gì | Bằng chứng | Không chứng minh |
|---|---|---|---|
| Source | version, locator, hash, ID, context | catalog + inventory | nguồn runtime thực sự được chọn |
| Structural | token, số/dấu, ID, NFC, tag, dòng | audit.json + test log | dịch đúng nghĩa |
| Semantic | nguồn/đích/cảnh, giọng, glossary, điều kiện | per-ID review + proposal hash + reviewer thực | font/layout đúng |
| Native | no-op, parse lại, text/timing/nontext diff | adapter readback + artifact hash | game nhận bản vá |
| Visual | dấu tiếng Việt, glyph, fallback, clipping, xuống dòng | ảnh/video từng màn hình/build | gameplay toàn bộ |
| Runtime | bản đang chạy, nguồn được nạp, lỗi, cập nhật | log/phim/ảnh có version/hash | an toàn tài khoản hoặc mọi phiên bản tương lai |
| Gameplay | chuỗi tình huống cụ thể đúng nội dung/hiển thị | ma trận test có trạng thái | phạm vi chưa chơi/quan sát |

Review lỗi thì trả proposal về needs_changes, không sửa kết quả gate thành PASS. Tool chỉ sinh pending review; agent/human thực sự review mới điền approved. Không dùng tên reviewer giả hoặc script vòng lặp gán approved.

Kiểm cuối snapshot phải dùng đúng file cuối và hash mới. Nếu sửa tool, glossary hoặc proposal sau review, xem lại các gate chịu ảnh hưởng. Cập nhật progress không được xóa lỗi cũ; ghi revision và quyết định xử lý.

Khi báo “xong”, nêu phạm vi rõ: ví dụ `51 cue đã dịch, 51 đã review, 4 file staging; runtime not_tested`. Không báo phần trăm toàn game khi chưa biết tổng catalog.

## Tiêu chí kiểm cơ chế

Nguồn và bản VI phải giữ chủ thể/mục tiêu, trigger, phủ định, phạm vi, giá trị và dấu, stacking/cap, chu kỳ, duration và thứ tự sự kiện. Regex không phát hiện được “all allies” bị dịch thành “bản thân”; đây là trách nhiệm reviewer.

## Câu dài và source lỗi

Cảnh báo dài chưa chắc lỗi; reviewer có thể chấp nhận có lý do và để visual pending. Source issue như `dffd` cần quyết định từng ID dựa vào biến thể/cảnh; tuyệt đối không viết regex xóa toàn cục rồi gọi QA đạt.
