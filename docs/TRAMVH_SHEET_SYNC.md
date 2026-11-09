# TrạmVH: đối chiếu trực tiếp Google Sheet

Web đọc tab `01. Glossary` qua `/api/glossary` và `/api/sync_glossary`. Những dòng cùng EN nhưng có ID nguồn khác được giữ riêng. Trạng thái review giữ theo Sheet; API lỗi không được báo là đã đồng bộ thành công.

Trang đối chiếu Merge đọc bốn tab `Chuong_STm00`, `Chuong_STm01`, `Chuong_STm02`, `03_BangText_UI_KyNang` qua `/api/sheet_reference`. Backend xác minh schema, khóa và thứ tự trước khi trả; không dùng bản JSON cũ để giả là dữ liệu mới khi Sheet lỗi.

Khi mở một chương cũ, backend đối chiếu Sheet theo `line_id` duy nhất và EN chính xác. CN/JP và VI trên Sheet được đưa vào dưới dạng nguồn tham khảo; dòng trùng ID hoặc EN không khớp không được nối. Chương 0 dùng tab Merge `Chuong_STm00`, ghép theo đúng `file_id` và EN duy nhất trong file vì tab cũ `Chương 0 - Mở Đầu` dùng ID SRT/BBm khác dữ liệu web. Các dòng không có cặp an toàn vẫn để trống. API báo `sheet_sync` và giao diện báo khi không thể đọc Sheet.

Đọc Sheet có bộ nhớ đệm trong Worker trong 15 giây để tránh mỗi lần mở chương lại gọi toàn bộ tab; cache chỉ giữ kết quả đọc thành công và lỗi/Schema sai vẫn trả về trạng thái không khả dụng. Một phản hồi quá 10 MB bị từ chối để tránh kéo dữ liệu bất thường vào Worker.

Web không ghi đè VI, revision, trạng thái hay đề xuất trong D1 từ Sheet. Thay phiên dữ liệu cộng tác vẫn thực hiện theo `TRAMVH_DATASET_RELEASE.md`. Đồng bộ hai chiều về bản dịch và ghi glossary trực tiếp lên Sheet chưa được triển khai; `/api/add_glossary_term` trả về trạng thái chỉ đọc rõ ràng thay vì gọi Apps Script cũ. Sheet cần được chia sẻ công khai ở mức đọc cho đường Google Visualization; nếu quyền truy cập đổi, web báo không kết nối được.
