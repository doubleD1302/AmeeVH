# Vai trò nghiên cứu tài nguyên

Đọc `docs/FORMAT_RESEARCH.md`, `DATA_CONTRACT.md` và `LOCAL_DISCOVERY.md`. Mục tiêu đầu tiên là xác định cấu trúc `data.arcx` và chứng minh extract/no-op trên bản sao; không cần dịch toàn game trong bước này.

Chỉ dựa vào byte/metadata/parser thật, ghi offset và hash của mẫu. Bản ghi discovery chia observed / hypothesis / tested / unresolved. Chưa biết format thì kết quả hợp lệ là ghi rõ vùng chưa biết và phép kiểm tiếp theo, không tạo catalog giả.

Viết parser có bounds check, locator ổn định, limits, chống traversal và bảo toàn unknown fields. Thêm test malformed/truncated/duplicate/Unicode length và roundtrip. Không thực thi Hotfix.dll/lua lấy từ game. Không sửa nguồn đang cài.

Đầu ra: adapter + ghi chú format + fixtures tối thiểu + báo cáo test/readback + số entry thật. Chỉ cập nhật STATUS.arcx_adapter sau khi có bằng chứng tương ứng.
