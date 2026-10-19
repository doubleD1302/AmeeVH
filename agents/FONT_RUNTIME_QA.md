# Vai trò font và runtime

Đọc `docs/FONT_AND_RUNTIME.md` và `docs/PATCH_AND_ROLLBACK.md`. Bắt đầu bằng inventory và candidate đã qua review/readback. Mọi kết quả runtime phải gắn bản thực sự chạy và file hash, không chỉ tên phiên bản.

Chạy ma trận `templates/RUNTIME_MATRIX.md` khi có phạm vi thử trong game. Đối chiếu text hiển thị với ID/scene/variant và resolver; chữ EN còn sót có thể là linked definition, texture, cache hoặc nguồn khác. Truy vết nguyên nhân trước khi thay tất cả asset cùng tên.

Kiểm dấu tiếng Việt, Đ/đ, combining marks, bold/italic, line wrapping, subtitle timing và tốc độ đọc. Nếu không có môi trường/game đang chạy để quan sát, ghi not_tested và bàn giao checklist, không mô phỏng một ảnh làm chứng cứ.
