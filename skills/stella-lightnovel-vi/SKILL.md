---
name: stella-lightnovel-vi
description: Dịch hoặc biên tập truyện và đối thoại Stella Sora sang tiếng Việt theo giọng light novel isekai/harem hiện đại, câu Việt tự nhiên và hài tiết chế. Dùng khi người dùng giao cảnh hoặc batch; giữ nghĩa, giọng nhân vật và bối cảnh nguồn, hạn chế bản địa hóa quá mức.
---

# Biên tập light novel Việt — Stella Sora

Phong cách người dùng chọn: tương tác có duyên, nội tâm dí dỏm khi nguồn hỗ trợ, cảm xúc có nhịp và câu Việt tự nhiên. Hài Việt ở cách diễn đạt/nhịp đối đáp; tránh meme, slang đậm đời Việt, thay văn hóa hoặc đùa thêm. “Isekai/harem” là định hướng thể hiện, không cho phép viết thêm romance, ghen tuông hay thay lore.

## Đọc và chốt scope

Xác định project root từ người dùng/workspace; với bản cài dùng `StellaSora_VietHoa/`. Đọc AGENTS, START_HERE, STATUS/CHECKPOINT và policy/role phù hợp. Chỉ xử lý scene/batch/field được giao. Việc tạo/cài skill không tự giao dịch lại toàn game.

Đọc trong dự án: `docs/LIGHTNOVEL_STYLE_BIBLE_VI.md`, `VI_SENTENCE_EDITING_GUIDE.md`, `HUMOR_LOCALIZATION_VI.md`. Đọc `NARRATION_AND_CONTINUITY.md` khi có lời kể/nội tâm/nhánh, `EDITORIAL_QA_RUBRIC.md` trước review. [references/editorial-workflow.md](references/editorial-workflow.md) là hướng dẫn thao tác và các nguyên tắc cốt lõi nếu project thiếu bản tài liệu đầy đủ; không cần đọc lại mọi tài liệu cho từng dòng đã cùng snapshot.

Tra glossary approved, Voice Bible và ma trận đang được chấp nhận theo file/hash. Nếu STATUS/CHECKPOINT trỏ khác revision, đối soát artifact và review thật, ghi khác biệt; không tự chọn r01 cũ hay tin “100%”. Mẫu trong `GOLDEN_SCENES_VI.jsonl` chỉ dùng như calibration khi review/hash còn hợp lệ; không có mẫu phù hợp vẫn có thể soạn proposal và ghi phần calibration còn thiếu.

## Dịch/biên tập theo cảnh

Đọc toàn cảnh với nhánh và trước/sau. Xác định speaker/listener, điểm nhìn, mức biết và mục đích câu. EN thực là nguồn hiện có; nhãn JPVA/CNVA không tự là text Nhật/Trung. Constant pool không chứng minh trình tự thoại; không tự chạy Lua/DLL trích xuất.

Giữ nghĩa, trọng tâm, tính chắc chắn, thứ tự thông tin cần cho cú đáp. Chỉnh cú pháp tiếng Việt, lược lặp khi người đọc vẫn biết chủ thể. Không thêm khẽ/bỗng/tim đập mạnh, kết luận tâm lý, thảm họa hoặc quan hệ chỉ để câu có chất truyện. Giữ chữ ký/giọng người khác trong archive; không gán cho chủ hồ sơ.

Hài: nhận ra câu dẫn–cú đáp–phản ứng trong nguồn, chọn khẩu ngữ phổ thông vừa lực; không biến mọi câu thành punchline. Giữ tên, đồ ăn, đơn vị và thế giới nguồn; không thay bằng tham chiếu Việt. Cảnh nghiêm túc giữ sức nặng. Tình cảm theo đúng mức nguồn, không tự rải bé cưng/em yêu/đại nhân. Có thể đề xuất phương án trung tính hơn nếu chơi chữ không chuyển được; ghi đánh đổi cho reviewer.

UI/cơ chế ưu tiên rõ và chính xác; không áp giọng truyện vào hướng dẫn chiến đấu. Giữ ID/source/hash, token/tag/ruby, số/dấu, cue/timing và ngắt dòng bảo vệ. Chỉ sửa trường cho phép trong proposal; VI NFC. Không gọi schema corpus mẫu vào localize.py nếu adapter không hỗ trợ.

## Review và bàn giao

Tạo revision mới, ghi quyết định có scope vào log thay vì thay đại từ toàn cục. Làm kiểm tĩnh đúng adapter, đóng băng file/hash và giao LOCALIZATION_QA_REVIEWER/SEMANTIC_REVIEWER độc lập theo policy dự án. Reviewer đọc cả cảnh, chỉ ra nghĩa, giọng, tiếng Việt và mức tiết chế từng ID; tác giả sửa rồi reviewer xét lại phần đổi. Không có reviewer thì tiếp tục phần khả thi và để pending_review, không tự duyệt.

Bàn giao proposal, source/context/policy/glossary hashes, decision log, audit/review, issue và checkpoint. Không để một câu thiếu context chặn các câu độc lập. Đạt biên tập không chứng minh font/layout/runtime. Skill không tự cài tài nguyên, sửa glossary khóa, launcher, DLL/Anti-Cheat hoặc phát hành.
