# Hợp đồng patch và rollback cho giai đoạn sau

Bộ khởi tạo **không có installer live**. Tài liệu này là tiêu chí để viết installer sau khi adapter và nguồn nạp được xác minh; không phải hướng dẫn copy đè ngay.

## Trước khi cài candidate

- Xác định client/game/resource version, nguồn load thực và hash từng file sẽ thay. File game đã đổi → từ chối patch cũ, tạo baseline mới.
- Danh mục thay đổi chỉ gồm tài nguyên được phê duyệt cho candidate. Không cập nhật toàn bộ folder, không xóa unknown files, không sửa executable/DLL/anti-cheat.
- Mỗi đường dẫn phải nằm trong allowlist, không tuyệt đối/traversal/junction; từ chối file đang dùng hoặc nguồn đã đổi trong lúc chuẩn bị.
- Backup đúng từng file gốc vào `backups/<run>` kèm hash/size; kiểm đọc lại backup trước thao tác live. Không ghi đè backup cũ.
- Candidate phải vượt structural/semantic/native gates; việc áp dụng lên game và kiểm runtime phải nằm trong phạm vi được người dùng giao. Không cần hỏi lại từng file nếu việc triển khai đã được giao rõ.

## Transaction tối thiểu

Preflight toàn bộ → kiểm đủ dung lượng → backup + readback → journal trạng thái trước từng file → ghi file tạm cùng volume → atomic replace → verify hash → đánh dấu installed. Dừng/rollback khi lỗi; không ghi installed nếu chỉ mới copy một phần. Đóng game/launcher theo tình trạng thực trước thao tác, không kill ứng dụng bừa bãi.

## Rollback

Chỉ khôi phục khi file hiện tại khớp hash candidate đã cài và backup khớp hash gốc. Nếu game update hoặc người dùng thay file, dừng đường rollback đó và báo conflict; không ghi bản cũ đè bản mới. Rollback có journal, có hash đọc lại, không xóa history.

Launcher có thể sửa/tải lại tài nguyên. Chưa có thử nghiệm nào trong bộ này xác định hành vi đó. Không gọi một candidate là “an toàn”, “không bị phát hiện” hoặc tương thích mọi update dựa trên static checks.

Phát hành sau này chỉ gồm công cụ/patch cần thiết và giấy phép phù hợp; không tự upload archive/binary nguyên game hay log cá nhân lên mạng.
