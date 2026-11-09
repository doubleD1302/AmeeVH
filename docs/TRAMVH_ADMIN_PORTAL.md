# Admin Portal TrạmVH

Admin Portal mở tại `web/story_translator/admin.html`. Nút **Công cụ → Admin Portal** trong workspace dịch mở form reviewer; sau khi mã đúng, key được giữ trong `sessionStorage` của cùng tab và portal mở ngay, không yêu cầu nhập lại.

Portal production yêu cầu reviewer key qua `X-Reviewer-Key`. Bản xem trước local chỉ bật khi hostname là `localhost`, `127.0.0.1` hoặc `::1` và URL có `?preview=1`; cờ này không tạo quyền ghi vào Worker.

## API chính

- `GET /api/admin/overview`: thống kê server-side.
- `GET /api/admin/queue`: hàng chờ review có pagination.
- `GET /api/admin/issues`: issue từ history và trạng thái `needs_review`.
- `POST /api/admin/exports`: tạo snapshot, delta hoặc handoff bất biến.
- `GET /api/admin/exports`: lịch sử export đã lưu D1.
- `GET /api/admin/exports/:id/download?file=...`: tải đúng bytes của file đã khóa.
- `GET /api/admin/audit`: lịch sử review và chuyển phase.

Chạy migration `0003_admin_portal.sql` và `0004_admin_auth_rate_limit.sql` sau migration dataset identity trước khi deploy Worker. Export được lưu trong D1; nếu phạm vi vượt giới hạn lưu trữ của D1, cần chuyển file payload sang R2 trước khi mở rộng batch lớn.

Gói handoff luôn ghi rõ dataset version, export ID, hash từng file, issue và điều kiện dừng. Worker vẫn là nơi kiểm tra revision, source hash, dataset version và quyền reviewer.
