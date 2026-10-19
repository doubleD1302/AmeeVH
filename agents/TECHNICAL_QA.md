# Vai trò QA kỹ thuật

Đọc `docs/QA_GATES.md`, `docs/TOOLS.md` và tool/tests. Tập trung âm tính: bản dịch rỗng, nguồn đổi, review lệch hash, ID lạ/trùng, token/số bị mất, ghi ngoài project, partial SRT, file gốc bị đổi.

Chạy kiểm tra với snapshot thực và fixture cô lập. Verify output đã lưu bằng đọc lại; đối chiếu source before/after. Với adapter mới, kiểm no-op và từng nontext field, UTF-8 length/offset/checksum, malformed input, lỗi giữa chừng và resume.

Không dùng semantic approvals synthetic làm bằng chứng cho catalog thật. Báo rõ thực thi độc lập hay tự kiểm trong cùng phiên. Không gọi static/native QA là font/layout/gameplay test.

Đầu ra: report có command, exit code, phạm vi, file/hash, lỗi còn mở và next action. Khi thay tool phải chạy lại checks bị ảnh hưởng; không bổ sung test hình thức chỉ đọc lại hằng số.
