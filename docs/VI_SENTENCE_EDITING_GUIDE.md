# Quy chuẩn biên tập câu tiếng Việt

Áp dụng cho lời kể/thoại VI của Stella Sora với giọng light novel hiện đại, bản địa hóa tiết chế. Giữ nghĩa trước, sau đó chỉnh nhịp và độ tự nhiên. Không làm câu “văn chương” bằng cách thêm sự kiện, tính từ hoặc tâm trạng.

## Chủ thể và trật tự câu

- Xác định ai nói, ai được nhắc và ai nhận hành động trước khi lược chủ ngữ. Cho phép lược trong câu đáp/chuỗi hành động có chủ thể rõ. Nhắc lại tên/đại từ nếu vừa đổi người làm hoặc dễ nhầm.
- Không coi I/you/she/he phải xuất hiện đủ từng lần trong VI. Cũng không xóa đồng loạt đại từ; lời thú nhận, nhấn trách nhiệm, đối lập tôi/cậu cần giữ trọng tâm.
- Sắp xếp câu theo tiếng Việt tự nhiên; quan hệ thời gian/điều kiện không đổi. Giữ chủ ý trì hoãn thông tin hoặc cú đáp ở cuối nếu đó là dụng ý nguồn.
- Mệnh đề dài có thể chia/tái cấu trúc trong text được phép sửa. Không tách/gộp ID, cue hoặc dòng được adapter bảo vệ khi chưa có policy phù hợp.

## Nghĩa và mức độ

Giữ phân biệt biết/nghĩ/ngờ, chắc chắn/có lẽ, muốn/phải/có thể, đã/đang/sắp khi liên quan. Không dịch “as if” thành một sự thật. Không tự thêm “khẽ”, “bỗng”, “chợt”, “run rẩy”, “tim đập mạnh” nếu nguồn không hỗ trợ. Đại từ, từ tình thái và kính ngữ đều có thể đổi quan hệ; chọn theo cảnh và ghi lựa chọn khó.

Không cấm mọi “bị/được”. Dùng khi có nghĩa chịu tác động, được hưởng hoặc khi câu cần điểm nhìn đó. Tránh bị động/danh từ hóa bám ngữ pháp nguồn làm câu nặng; sửa mà vẫn giữ tác nhân, người chịu tác động và thái độ. Không dùng một regex xóa “việc”, “sự”, “bị”, “được” trên toàn game.

## Từ vựng và khẩu ngữ

Ưu tiên “giúp”, “tìm”, “chờ”, “làm” khi phù hợp thay chuỗi từ hành chính. Từ Hán–Việt dùng khi tên gọi, văn cảnh hoặc người nói cần; không cưỡng ép thuần Việt tới mức sai thuật ngữ. Giữ cách viết tên theo glossary approved. Tiếng Việt phổ thông làm nền; tránh tự gán phương ngữ/teencode hoặc danh xưng anh/chị theo ngoại hình.

Thoại có thể có câu ngắn, câu cụt và hạt tình thái đúng hoàn cảnh. “Nè/nhé/ạ/đấy” là lựa chọn mang sắc thái, không phải gia vị thêm vào mọi dòng. Không làm mọi nhân vật lặp một câu cửa miệng.

## Dấu câu và nhịp

Chọn dấu phẩy/dấu chấm theo nhịp VI, nhưng giữ lực hỏi/cảm thán/đứt lời của nguồn. Không tăng số dấu !/? để tăng “chất anime”. Dùng dấu ba chấm cho ngập ngừng/bỏ lửng có căn cứ; dấu gạch hoặc kiểu ngoặc theo quy chuẩn UI/proposal của tài nguyên. Chat, thư và lời kể có cách trình bày khác nhau; không ép tất cả thành hội thoại ngoặc kép.

Không chuyển escape literal `\\n` thành newline thật hoặc ngược lại nếu adapter yêu cầu giữ. Giữ nguyên token, ruby, rich text, tên sprite, placeholder và dấu/đơn vị trong công thức. VI Unicode NFC; source_text giữ nguyên để đối chiếu hash.

## Ví dụ tự tạo để học thao tác, không phải thoại game

Nguồn: “She looked at me, as if she wanted to say something.”
Đề xuất: “Cô nhìn tôi, như muốn nói gì đó.”
Lược chủ ngữ lặp, giữ ý phỏng đoán. “Cô nhìn tôi, lòng đầy điều không thể nói” là diễn giải thêm nội tâm, cần nguồn riêng để dùng.

Nguồn: “I thought you had left.”
Đề xuất trong cảnh đã chốt tôi–cậu: “Tôi tưởng cậu đi rồi.”
“Tôi biết cậu đã đi” làm sai mức biết; “Tưởng đi rồi chứ” chỉ dùng khi người được nhắc vẫn rõ.

## Lượt đọc lại

Đọc cả cảnh thành tiếng hoặc đọc liền để phát hiện câu cứng, chủ thể mơ hồ và đại từ lặp. Đối chiếu lại nguồn sau khi câu đã mượt để bắt ý bị thêm/bớt. Một câu trôi chảy vẫn có thể sai nghĩa; reviewer cần giải thích lựa chọn cụ thể theo [rubric](EDITORIAL_QA_RUBRIC.md).
