# Hợp đồng corpus mẫu

## Record JSONL

Mỗi dòng là một object của một đơn vị nguồn trọn. Giữ schema có nghĩa ổn định; thêm field có chủ đích nếu cần. Tối thiểu:

- `scene_id`: ID duy nhất; `source`: path project-relative, key/locator, file_sha256, text_sha256 UTF-8, locale và scope như archive_document_not_avg_scene.
- `source_text`: nguyên văn đầy đủ đơn vị được khai báo. `text_vi`: bản dịch toàn bộ, không cắt câu khó.
- `participants`: name, id nullable, attribution, listener_status; `speaker_listener_notes` mô tả chỗ chắc/chưa rõ. Người được nhắc không tự là người nghe.
- `editorial_notes`: decision/rationale cụ thể; `tones`: mô tả sắc thái có nguồn; `translator`: tác giả thật.
- `status`: pending_review hoặc accepted_for_calibration sau quyết định thật; `content_sha256`: hash nội dung; `review`: null trước review, sau đó chứa reviewer, report path/hash và decision gắn scene/content.

Không tự normalize lại source_text; chỉ VI NFC. Giữ tag/ruby/placeholder như ==PLAYER_NAME==, số, thứ tự lượt và newline theo policy nguồn. Với archive mẫu hiện tại, giữ cấu trúc dòng như nguồn; không đồng nghĩa mọi adapter game đều cho phép cùng schema.

## Hash để promote mà không đổi nội dung

`content_sha256 = SHA256(UTF8(JSON canonical của record loại bỏ đúng ba field status, review, content_sha256)))`.

JSON canonical: ensure_ascii=False, sort_keys=True, separators=(',',':'); arrays giữ thứ tự. Mọi field mới về context/author/nguồn/text/rationale đều được hash. Chỉ metadata review/status được thêm khi promote; chỉnh chữ dù nhỏ làm content hash đổi và phải review lại. File SHA-256 của candidate cũng được reviewer ghi; không dùng hash toàn file sau promote để giả là file reviewer đã đọc.

## Đọc nguồn và review

Exact source/hash và token checks là kỹ thuật; reviewer phải xem nghĩa, register, tính tự nhiên, xưng hô, điểm nhìn và mức bản địa hóa cả cảnh. Lý do riêng theo scene, không dùng “đúng nghĩa” cho tất cả. Một ý kiến tổng hợp không thay quyết định từng sample. Nếu reviewer viết lại sample, cần người khác review phần đó.

Source bị gắn wrong speaker hoặc đầy dấu prefix do quét bytecode thì pending_context, không xóa prefix bằng regex cho trông sạch. Nhãn source archive owner chỉ là ownership; chat/chữ ký phải dùng tác giả thực. Alias bí ẩn/nhánh/giới người chơi chưa rõ giữ unknown. Không tự dùng một cặp đại từ của mẫu làm canon toàn game.

## Sổ quyết định

Mỗi record có decision_id, kind, scope, decision, rationale, authority/source refs, status và supersedes nullable. Tách policy do người dùng chọn với quyết định dịch đã qua review. Khi quyết định gắn mẫu, lưu scene_id/content hash và review reference. Không chép toàn bộ corpus vào log hoặc tự nâng policy thành translation approved.

## Tiếp tục và dùng mẫu

Corpus ở work/editorial/revision mới, giữ predecessor path/hash. Checkpoint ghi target/done/pending/needs_changes theo scene ID, nguồn đã tìm, writer/reviewer và lệnh tiếp tục. Sau nguồn/policy/context đổi, xét tác động và re-review phần ảnh hưởng. Các mẫu synthetic để minh họa/kiểm skill phải tách riêng, không đưa vào GOLDEN_SCENES như thoại thật.

Người dịch đọc mẫu gần domain/tình huống nhất và dùng kỹ thuật, không copy câu đùa qua cảnh khác. Nếu corpus mới có năm archive entries, công khai rằng chưa có toàn cảnh AVG/romance/combat runtime tương ứng; thiếu nguồn đại diện là gap, không phải lý do bịa cảnh hoặc gán mức tình cảm mới.

## Mẫu để bắt đầu

Sao chép [GOLDEN_SCENE.template.json](../assets/GOLDEN_SCENE.template.json), điền dữ liệu thật, bỏ template_only và ghi một object trên mỗi dòng JSONL. Null trong template là chỗ phải điền hoặc giải thích unknown, không phải record được duyệt. Helper chỉ tính hash; người viết vẫn phải kiểm đủ schema, nguồn và review. Mẫu synthetic phải nằm riêng ngoài corpus game.
