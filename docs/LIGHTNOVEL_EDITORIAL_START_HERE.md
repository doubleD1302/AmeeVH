# Bộ light novel VI — cách sử dụng

Định hướng người dùng: giọng light novel isekai/harem hiện đại, câu Việt tự nhiên, hài Việt tiết chế và hạn chế bản địa hóa quá mức. Giữ nghĩa, quan hệ và bối cảnh nguồn; không tự thêm romance hoặc meme.

## Sáu tài liệu chính

1. [LIGHTNOVEL_STYLE_BIBLE_VI.md](LIGHTNOVEL_STYLE_BIBLE_VI.md): giọng đích, nhịp và cách viết theo domain.
2. [VI_SENTENCE_EDITING_GUIDE.md](VI_SENTENCE_EDITING_GUIDE.md): chủ thể, cú pháp, dấu câu và khẩu ngữ.
3. [GOLDEN_SCENES_VI.jsonl](../work/editorial/lightnovel_editorial_20261023_r01/GOLDEN_SCENES_VI.jsonl): các mẫu đã review độc lập trong phạm vi calibration; xem metadata từng sample.
4. [NARRATION_AND_CONTINUITY.md](NARRATION_AND_CONTINUITY.md): điểm nhìn, mức biết và nhánh truyện.
5. [EDITORIAL_QA_RUBRIC.md](EDITORIAL_QA_RUBRIC.md): tiêu chí reviewer đọc cả cảnh và ra quyết định.
6. [EDITORIAL_DECISION_LOG.jsonl](../work/editorial/lightnovel_editorial_20261023_r01/EDITORIAL_DECISION_LOG.jsonl): policy và quyết định có scope.

Bổ sung: [HUMOR_LOCALIZATION_VI.md](HUMOR_LOCALIZATION_VI.md) hướng dẫn hài tiết chế; [corpus dễ đọc](../work/editorial/lightnovel_editorial_20261023_r01/GOLDEN_SCENES_VI_READABLE.md) và [coverage/gaps](../work/editorial/lightnovel_editorial_20261023_r01/CORPUS_COVERAGE.json).

## Hai skill

- [stella-lightnovel-vi](../skills/stella-lightnovel-vi/SKILL.md): dịch/biên tập scene hoặc batch đã được giao. Dùng [prompt dịch](../prompts/TRANSLATE_LIGHTNOVEL_VI_20261023.txt).
- [stella-golden-scenes-vi](../skills/stella-golden-scenes-vi/SKILL.md): xây/mở rộng corpus mẫu và review. Dùng [prompt tạo mẫu](../prompts/BUILD_GOLDEN_SCENES_VI_20261023.txt).

Ví dụ gọi sau khi đã giao cảnh:

```text
Dùng $stella-lightnovel-vi để biên tập cảnh được giao theo bộ tài liệu LIGHTNOVEL_EDITORIAL_START_HERE.md. Giữ hài nhẹ và hạn chế bản địa hóa quá mức.
```

Ví dụ mở rộng bộ mẫu:

```text
Dùng $stella-golden-scenes-vi để bổ sung những loại cảnh còn thiếu coverage, giữ nguồn đầy đủ và review độc lập từng mẫu. Tạo revision mới, không ghi đè corpus đã duyệt.
```

Nếu môi trường chưa nhận skill, đọc trực tiếp SKILL.md trong dự án rồi thực hiện prompt. Skill tự chọn khi phù hợp không đồng nghĩa tự chạy tác vụ nền. Tài liệu/corpus là sidecar biên tập, chưa có adapter tự thay bản dịch đang cài.

## Phạm vi bộ mẫu ban đầu

Các mẫu lấy từ archive EN cục bộ, mỗi mẫu có full row, key/hash, attribution, bản VI và rationale. Chúng không được gọi là toàn cảnh AVG. Các loại chưa có đại diện được ghi gap, không tạo thoại giả để đủ thể loại. Ví dụ synthetic dùng kiểm skill nằm riêng, không đưa vào corpus game.

Review độc lập chấp nhận chất lượng calibration trong phạm vi đã xem; người dùng có thể chỉnh gu tiếp trên các mẫu này. Đổi nguồn, context hoặc nội dung làm review liên quan cần xét lại. Cài hai skill không thay thế quyền giao dịch/cài game trong từng nhiệm vụ.
