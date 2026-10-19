# Nhiệm vụ nghiên cứu format cho agent kỹ thuật

## Đầu vào cụ thể

- `Persistent_Store/Tables/data.arcx`, `Persistent_Store/Scripts/lua.arcx`: header `1a424152`; decoder/repacker chưa có.
- `Persistent_Store/Scripts/hotfix.arch`: signature ZIP; có thể kiểm danh mục trên bản sao bằng thư viện ZIP chuẩn, không chạy DLL.
- `Persistent_Store/ss_win.mani` và manifest cài sẵn: văn bản có version và record phân tách `|`; chưa xác định hết trường checksum/flags.
- `StellaSora_Data/data.unity3d`, bundle UI/localization và `font.unity3d`: UnityFS 2022.3.62f2. Bundle cập nhật có thể khác bản cài sẵn.

## Trình tự bắt buộc

1. Lấy inventory mới, chọn file theo hash/version; copy **chỉ mẫu cần thiết** vào `work/research/<run>/`, ghi nguồn + SHA256 + kích thước. Không nhân bản toàn bộ gần 30GB tài nguyên để thử một bảng.
2. Kiểm magic/header/offset/kích thước; phân biệt dữ liệu thực với giả thuyết. Ghi giả thuyết và phép kiểm có thể bác bỏ nó. Không suy thuật toán mã hóa từ entropy hoặc phần mở rộng.
3. Tìm cấu trúc đọc tài nguyên trong code/metadata có sẵn bằng phân tích tĩnh nếu cần. Không inject, hook process, sửa DLL hay tắt bảo vệ. Nếu một hướng đòi can thiệp bảo vệ, báo giới hạn và tiếp tục phần tài nguyên offline khả thi.
4. Viết parser đọc trước: giới hạn độ dài/số entry, kiểm offset nằm trong file, chống path traversal, không trùng ID, không thực thi nội dung trích.
5. Xác định bảng text và các cột thực: ID, locale, text, speaker, scene, references, variant. Trích văn bản có ý nghĩa, không dịch mọi chuỗi nhị phân tìm được bằng strings.
6. Adapter trả record theo `docs/DATA_CONTRACT.md`. Token grammar phải lấy từ mẫu của game. Tạo fixture tối thiểu tự sinh khi có thể; không commit toàn bộ archive game.
7. Repack trên bản sao: no-op phải byte-identical nếu format cho phép. Nếu serializer không bảo toàn byte, so sánh nội dung từng object/entry và chứng minh vì sao khác; không bỏ qua checksum/offset hoặc nontext drift.
8. Thay một câu thử trong staging, giải lại bằng parser độc lập hoặc cách đọc thứ hai, đối chiếu chỉ field cho phép thay đổi. Chưa chứng minh loader chấp nhận cho đến khi có runtime thực.

## Hợp đồng adapter tương lai

`probe(path)` → format/version/unsupported reason; `extract(path)` → catalog + source manifest; `repack(source, reviewed_changes, out)` → candidate; `readback(candidate)` → data chuẩn hóa để đối chiếu.

Yêu cầu riêng: offsets theo byte UTF-8, kích thước sau encode, alignment, endianness, compression, entry order, checksum và version. Không dùng độ dài ký tự Python thay cho số byte. Giữ unknown fields, duplicate-text IDs và linked text references.

Thêm subcommand sau khi có test thật; không tạo stub trả success, không đặt `adapter_ready=true` chỉ vì đã viết interface. Những cú pháp chưa biết để `unsupported` kèm mẫu, không tự dịch byte không đọc được.

## Nghiên cứu Unity/font

UnityPy là lựa chọn để thử đọc Unity assets, chưa được cài hoặc kiểm chứng trên bộ bundle này. Nếu dùng, tạo `.venv` riêng, ghim phiên bản thực tế đã thử, giữ yêu cầu và license; không tự nâng môi trường Python dùng cho công cụ lõi. Tham khảo primary source trong `docs/REFERENCES.md`.
