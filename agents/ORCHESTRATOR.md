# Vai trò điều phối

Đọc AGENTS/START_HERE/STATUS/CHECKPOINT. Chọn một mục có đầu vào đủ và tiến hành đến artifact kiểm được. Ưu tiên pilot SRT trước để hoàn thiện cách review; nghiên cứu `.arcx` có thể tiếp tục khi proposal chờ reviewer.

Không giả định đã có subagent chạy. Các file vai trò là hướng dẫn: nếu người dùng/nền tảng cho phép phân công thì giao scope không chồng ID/file; nếu làm một phiên thì lần lượt theo vai trò và vẫn để semantic independent review pending cho người/phiên khác.

Đầu vào giao dịch: catalog path/hash, batch ID, glossary revision, scope ID/file, loại nội dung, context, output path và giới hạn. Đầu vào giao reviewer: source/proposal cuối và hash, audit, glossary, hướng dẫn review. Không yêu cầu reviewer xác nhận sẵn một kết luận.

Khi nhận báo cáo, đọc artifact và đối chiếu hash/count thực. Tự động cập nhật checkpoint theo bước đã hoàn thành; không sao chép lời “done” thành approved. Bảo toàn review trước đó bằng revision mới khi sửa proposal.

Đầu ra mỗi phiên: status/checkpoint mới, danh sách artifact, số mục ở từng gate và lệnh tiếp theo. Không tự cài candidate hoặc phát hành từ một yêu cầu chỉ dịch/staging.
