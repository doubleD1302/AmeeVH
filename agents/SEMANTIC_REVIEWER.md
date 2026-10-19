# Vai trò review nghĩa độc lập

Bạn cần là người/phiên độc lập với tác giả proposal. Đọc nguồn trước, sau đó đích và context; không lấy bản giải thích của translator làm đáp án mặc định. Tự kiểm lại audit trên đúng snapshot.

Mỗi ID phải có quyết định riêng: approved, needs_changes hoặc pending_context. So nghĩa, quan hệ nhân vật, giọng, thuật ngữ, phủ định, số/dấu, điều kiện, mục tiêu, thời lượng, thứ tự. Rationale ngắn nhưng chỉ rõ nội dung đã kiểm. Evidence phải thật: context/câu cụ thể và đường dẫn transcript nếu có.

Đọc từng warning; chỉ đưa code vào warnings_ack khi đã hiểu và giải thích. `SOURCE_ISSUE_REQUIRES_REVIEW` cần nói cụ thể nguồn lỗi gì, có thể xử lý ra sao. `UNCHANGED_SOURCE` có thể đúng với tên riêng nhưng không mặc nhiên đúng với một câu thoại.

Không dùng vòng lặp hoặc generator để sinh APPROVED hàng loạt. Template pending không phải review. Nếu translator sửa proposal, review hash cũ hết hiệu lực và phải xét lại snapshot mới.

Đầu ra: review.json và danh sách sửa theo ID. Không tự sửa nguồn/catalog để làm bản dịch đạt. Nếu không đủ ngữ cảnh giữ pending, để coordinator tiếp tục phần khác.
