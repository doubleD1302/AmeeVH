---
name: stella-golden-scenes-vi
description: Xây dựng, review và cập nhật corpus cảnh dịch mẫu Stella Sora có nguồn thật, bản VI và lý do biên tập để hiệu chỉnh giọng light novel cùng hài Việt tiết chế. Dùng cho GOLDEN_SCENES_VI và sổ quyết định; không tự dịch lại toàn game hoặc tạo thoại giả làm nguồn.
---

# Corpus cảnh dịch mẫu Stella Sora

Tạo mẫu chuẩn có thể đối chiếu, đủ ngữ cảnh và dùng lại để hướng dẫn AI dịch. Người dùng chọn light novel isekai/harem nhưng hạn chế bản địa hóa quá mức; mẫu phải giữ bối cảnh, nghĩa và giọng nguồn, tránh meme/slang địa phương và không thêm tình cảm để giống harem.

Đọc [references/corpus-contract.md](references/corpus-contract.md) trước viết/review. Trong dự án đọc AGENTS, START_HERE, STATUS/CHECKPOINT, các tài liệu LIGHTNOVEL_STYLE_BIBLE_VI, VI_SENTENCE_EDITING_GUIDE, NARRATION_AND_CONTINUITY và EDITORIAL_QA_RUBRIC trong docs. Không cần skill khác để làm việc; dùng glossary/context của project khi có và kiểm file/hash thực.

## Xây dựng hoặc mở rộng corpus

Chốt số/phạm vi mẫu người dùng giao; nếu chưa có corpus, bắt đầu nhóm nhỏ đa dạng, thường 5–8 đơn vị nguồn phù hợp, không làm giả độ đa dạng khi nguồn thiếu. Chọn cảnh/đoạn trọn có người nói và chức năng rõ: đối đáp, kể/nội tâm, căng thẳng/cảm xúc hoặc tương tác thân mật nếu nguồn thật có. Báo coverage gap để mở rộng, không gọi vài chat là đã phủ toàn cốt truyện.

Đọc nguồn EN chính xác và lưu full source với path/key/hash/locale. Archive entry trọn ghi archive_document, không gọi toàn cảnh AVG. Đoạn trích ghi excerpt và không dùng làm chuẩn “cảnh đầy đủ”. Chỉ nhận AVG khi đã có mapping trình tự/speaker thật; không đoán từ constant order, không chạy Lua/DLL trích xuất.

Tạo bản VI và rationale riêng theo cảnh: nhịp câu, đại từ có scope, điểm nhấn của câu đùa, mức kính ngữ và điều không thêm. Lược chủ ngữ có chủ ý nhưng không làm mơ hồ chủ thể. Nguồn đời thường không bị ép cổ trang hóa; cảnh buồn không bị chèn đùa. Các phương án hay nhưng đổi nghĩa/văn hóa phải loại hoặc ghi needs_changes.

Tạo revision mới của GOLDEN_SCENES_VI.jsonl và EDITORIAL_DECISION_LOG.jsonl trong work/editorial; không đè corpus/review đã giao. Nếu schema bổ sung field ngữ cảnh, field đó phải nằm trong content hash. Lưu coverage và checkpoint theo scene IDs, không bỏ mục khó khỏi mẫu số để gọi hoàn tất.

## Review thực và promote

Tác giả hoàn thành → kiểm exact source/tokens/NFC → khóa candidate/hash → reviewer độc lập đọc toàn bộ từng nguồn/đích/context → accepted_for_calibration, needs_changes hoặc pending_context theo scene. Dùng task packet, một writer và role của dự án; không có reviewer thì để pending_review, tiếp tục soạn mẫu khác.

Sau sửa phải review lại hash đổi. Chỉ agent chính promote những scene được quyết định thật, gắn review path/hash và giữ content_sha256 trùng với bản reviewer đã đọc. Không tạo approval bằng vòng lặp dựa vào status có sẵn hoặc tự đổi danh tính. Script ghi lại quyết định đã có không thay việc đọc/review.

Helper `scripts/corpus_hash.py` chỉ tính content hash theo hợp đồng, không xác minh nghĩa/nguồn hay phê duyệt. Dùng từ thư mục skill hoặc đường dẫn tuyệt đối:

```powershell
python scripts/corpus_hash.py 'C:/path/to/GOLDEN_SCENES_VI.candidate.jsonl'
```

Bàn giao JSONL, sổ quyết định, source/policy hashes, review theo scene, coverage/gaps, checkpoint và bản dễ đọc khi hữu ích. Accepted_for_calibration là review biên tập độc lập, không tự chứng minh người dùng đã chốt gu, translation game đã đổi, layout hoặc runtime đạt. Không chạy install/repack/publish từ skill này.
