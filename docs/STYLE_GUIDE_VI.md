# Quy chuẩn bản dịch tiếng Việt

## Nguồn và giọng văn

- EN là nguồn có thật trong bản cài hiện tại. Với JP/CN bổ sung, ghi locale, version, ID và quan hệ đối chiếu; không tự tuyên bố nguồn gốc kịch bản.
- Thoại tự nhiên, gọn, có nhịp cảm xúc của cảnh. Giữ tính cách người nói; xưng hô cần quan hệ nhân vật, địa vị và ngữ cảnh trước/sau. Không thêm meme, tiếng lóng theo trend hoặc tình tiết mới.
- UI dùng từ ngắn, hành động rõ. Cơ chế ưu tiên chính xác hơn câu chữ hoa mỹ. Lời bài hát/subtitle cần giữ hình ảnh và nghĩa; không buộc vần nếu làm sai nội dung.
- **Quy tắc phân định Hán-Việt và Thuần Việt**:
  * **Với Danh từ (Tên chiêu thức, Kỹ năng, Tổ chức, Bang phái, Chức danh, Quái vật/Boss, Danh từ riêng)**: Được phép và khuyến khích dùng từ **Hán-Việt hào sảng, uy phong, đậm chất Anime RPG** (ví dụ: *Bạo Viêm Quyền, Dung Viêm Phá, Viêm Khải, Ám Triều, Cấm Vệ Thương Khung, Phủ Bạch Trạch, Lữ Đoàn Tân Tinh, Cận Vệ Đế Quốc, Linh Thú Cuồng Bạo*).
  * **Với Văn miêu tả cơ chế, Lời thoại đối thoại, Hướng dẫn hệ thống**: Ưu tiên **thuần Việt, trong sáng, tự nhiên, dễ hiểu**. Tuyệt đối không nhồi nhét Hán-Việt cổ lỗ sĩ vào văn nói thường ngày, không dịch word-by-word, loại bỏ hoàn toàn thể bị động rườm rà (ví dụ: dùng *Lật ngược tình thế, Khép chặt vòng vây, Khi thi triển Bạo Viêm Quyền sẽ tăng sát thương...*).
- Tên riêng nhân vật giữ theo chữ Latin gốc của bản EN (Amber, Freesia, Flora, Willow, Kasimira, v.v., không tự Hán hóa tên nhân vật).
- `config/glossary.json` có trạng thái proposed/approved. Chỉ approved là thuật ngữ khóa. Mỗi thay đổi thuật ngữ cần ví dụ nguồn, phạm vi áp dụng và review tác động.

## Cơ chế cần giữ nguyên

Với từng câu, kiểm đủ: ai thực hiện → điều kiện kích hoạt → hành động → đối tượng → giá trị/dấu → đơn vị → thời lượng → giới hạn/lượt → thứ tự sự kiện. Phân biệt sát thương gây ra/nhận vào, tăng/giảm, cộng/trừ, %/điểm phần trăm, xác suất/bảo đảm, tối đa/ít nhất, mỗi lượt/mỗi lần.

Không dịch khóa lập trình, ID, tag, URL, tham số, tên sprite, tên liên kết hoặc công thức như văn xuôi. Ví dụ `{0}`, `{name}`, `${value}`, `%s`, `%1$d`, `<color=#FFCC00>`, `<sprite=2>`, `\n` phải giữ. Nếu gặp cú pháp mới mà checker chưa nhận, mở issue và bổ sung parser/test trước khi chấp nhận hàng loạt.

## Subtitle

- Giữ cue number và timestamp, đúng biến thể JPVA/CNVA. Tool giữ BOM, CRLF/LF và khoảng trắng ngoài body.
- Mặc định giữ số dòng body. Muốn đổi ngắt dòng phải bổ sung policy/QA có chủ đích; không sửa checker chỉ để bỏ qua lỗi.
- 48 ký tự/dòng là ngưỡng cảnh báo tạm thời, không phải giới hạn được xác minh trong Stella Sora. Cần runtime để chốt kích thước, số dòng và tốc độ đọc.
- Không copy thời gian hoặc toàn bộ proposal JPVA sang CNVA. Có thể tham khảo nghĩa sau khi đối chiếu cue thực tế.

## Review bắt buộc

Reviewer ghi ngắn theo từng ID: nghĩa nào đã đối chiếu, lựa chọn xưng hô/thuật ngữ, token/số đã bảo toàn, source issue/warning xử lý thế nào. Không dùng cùng một câu “đúng nghĩa” cho mọi mục. Nếu thiếu ngữ cảnh: needs_changes hoặc pending_context, không đoán rồi approved.

Không được coi đầu ra máy dịch tự động, audit 0 lỗi hoặc bản dịch đọc trôi chảy là bằng chứng đủ về nghĩa.
