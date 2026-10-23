# Hợp đồng hoàn thiện hồ sơ nhân vật

## Phạm vi và baseline

Tại thời điểm soạn skill 23/10/2026, baseline `work/character_context_20261023_r01/` có 41 hồ sơ nhân vật/biến thể: 7 source_grounded_editorial_draft, 34 pending_character_evidence. Bảng roster còn 3 Golem và một tên chỉ có trong glossary ở danh sách riêng. Đây là snapshot để định hướng, không phải số đếm cố định. Giữ các biến thể như Firstlight Noya riêng; không tự kế thừa Noya khi chưa xác minh quan hệ và khác biệt.

Nguồn EN đã dùng ở baseline nằm trong `work/research/data_200_pristine_en/entries/`: bảng Character, CharacterArchiveBaseInfo và CharacterArchiveContent. Chỉ số entry thay đổi giữa snapshot; nhận diện theo khóa/schema/locale rồi kiểm manifest/hash, không giả 00525 là Character trong mọi phiên bản. Có bảng CN cùng snapshot; không trộn vào EN chỉ vì cùng tên table. Xem SOURCE_EVIDENCE của baseline để biết nguồn/hash chính xác; không sao chép hash cũ sang nguồn mới.

`config/glossary.json` khóa cách viết tên/thuật ngữ theo status thực tế, không xác nhận lore trong notes. Đối chiếu master glossary khi cần, ghi conflict trước khi thay quyết định. Không đem quy tắc CZN vào Stella Sora. Source issue, alias chưa lộ danh tính, người chơi chưa rõ giới và lời người thứ ba cần giữ riêng.

## Nội dung một hồ sơ

Giữ field/ID hiện hữu và mở rộng có chủ đích, nêu rõ schema revision nếu thay đổi. Hồ sơ phải có:

1. Danh tính, game ID/variant, nguồn tên và liên kết nguồn; tách tên khóa với tên hiển thị.
2. Những nét có bằng chứng: trích đoạn chính xác, key/field/prototype/cue thật, file hash và người phát ngôn. Một lời khen/chê của người khác cần attribution, không biến thành giọng tự nói.
3. Đề xuất giọng VI cụ thể: nhịp, từ vựng, mức trực tiếp, mức trang trọng, phản ứng ở các tình huống có nguồn. Có giới hạn và phản ví dụ nếu nguồn cho thấy giọng thay đổi. Không đặt quota catchphrase.
4. Xưng/gọi với Main và đồng đội có căn cứ; nơi chưa biết ghi pending_context, điều cần tìm và cách diễn đạt tạm thời bảo toàn nghĩa. Không bắt mỗi hồ sơ có quan hệ với mọi nhân vật.
5. Những lựa chọn cần tránh riêng cho nhân vật và căn cứ; không lặp toàn bộ quy tắc chung trong từng mục.
6. Ví dụ dùng được khi đủ nguồn, hoặc phần thiếu được mô tả cụ thể. Quote nguồn không sửa Unicode/tag; text VI NFC. Phân biệt dịch minh họa với proposal game được duyệt.
7. Trạng thái nội dung và review gắn đúng hash; không dùng một status “done” thay mọi gate.

Nếu nguồn thật chỉ đủ ít nét, viết hồ sơ gọn đúng phạm vi và công khai phần chưa biết; không cần sáng tác lore để kéo dài. Nếu thiếu cả căn cứ giọng nói, mục chưa hoàn thiện dù đã có tên/ID.

## Registry bằng chứng và ma trận

Giữ schema evidence của baseline khi có thể: `evidence_id`, `source_key`, `source_file`, `source_file_sha256`, `quote_en`, `full_row_en`, `source_attribution`, `supported_reading`, `scope`. Nếu adapter/nguồn không phải bảng JSON, thêm locator đúng loại và giải thích cách đọc lại. Mọi evidence_ref phải resolve; quote phải khớp nguồn đã khóa, không chỉ khớp cache.

Tách `source_observed_edges`, `proposed_edges` và `approved_edges`. Mỗi cạnh đề xuất nêu speaker/listener IDs, self/address options cùng điều kiện chọn, timeline/scene/branch/public-private/affinity nếu liên quan, evidence_refs và review. Không tạo chiều ngược từ suy đoán. Nhắc tên không chứng minh đang nói với người đó; người nói kế tiếp không tự là người nghe.

Claim bị phản bác hoặc thiếu căn cứ trong attachment cũ vẫn giữ ở assessment/issue lịch sử. Không tái nhập “Jinglin nhà khoa học”, “Minova trưởng lão”, “Tilia thị vệ riêng Amber” hoặc “Kasimira gọi ai cũng bé cưng” thành fact nếu không có nguồn mới hỗ trợ.

## Checkpoint và coverage

Agent chính tạo revision output mới, ví dụ `work/character_context_full_YYYYMMDD_rNN/`, kèm predecessor path/hash. Checkpoint đợt có thể là `CHECKPOINT_CHARACTER_CONTEXT.json` trong revision đó; đây là sổ do agent cập nhật, không phải daemon.

Tối thiểu ghi:
- `run_id`, `baseline_path`, `baseline_hashes`, source locale/version/hash.
- `target_ids`, `preserved_predecessor_ids`, `todo_ids`, `in_progress_ids`, `content_ready_ids`, `review_pending_ids`, `accepted_documentation_ids`, `pending_source_ids`, `conflict_ids`.
- Phân công file/ID một writer, batch IDs và artifact paths/hashes.
- Issues theo ID với nguồn đã thử đọc, truy vấn/thư mục đã kiểm, thiếu dữ kiện nào và next action cụ thể.
- Lệnh kiểm/kết quả, reviewer ID thực và review paths/hash.

`target_ids` phải phủ mọi hồ sơ còn thiếu đã xác định. Các bucket tiến độ của target phải không trùng và hợp bằng target; preserved_predecessor là tập ngoài target. Khi thêm/bớt target do rebase, ghi delta và lý do. Không xóa ID khó để tăng coverage. Unknown-kind/NPC/glossary-only nằm riêng để quyết định phạm vi, không lẫn mẫu số nhân vật được giao.

Tách tỷ lệ nội dung có căn cứ, đã review, pending_source và pending_review. Bảy hồ sơ tiền nhiệm có review tài liệu ở snapshot cũ: giữ bằng chứng đó, không tự coi review còn hợp lệ nếu nguồn/profile đổi. Thay đổi pending→source_grounded chỉ sau khi có nội dung và evidence thật; accepted_documentation cần review độc lập, không đồng nghĩa mọi cặp pronoun approved.

## Reviewer và kiểm tĩnh

Reviewer đọc từng hồ sơ, các claim mới và từng cạnh mới/đổi trên snapshot đóng băng; ghi accepted_for_documentation, needs_changes hoặc pending_context theo artifact/ID, cùng rationale cụ thể và nguồn. Không biến 34 hồ sơ thành approved bằng một vòng lặp. Với ví dụ dịch, kiểm nghĩa/đại từ/token và không sửa trực tiếp vào input; tác giả sửa revision rồi reviewer xem lại.

Kiểm tĩnh: JSON parse, ID duy nhất/coverage, ref resolve, hash file, exact quotes/full rows, NFC cho VI, liên kết Markdown và nhất quán giữa Bible/profiles/matrix. Nó không chứng minh tính cách đúng hay thay thế review. Helper inventory chỉ phân loại việc còn lại; không kiểm nội dung toàn bộ, không tạo evidence và không cưỡng chế reviewer.

## Hoàn tất và trường hợp thiếu nguồn

Kết quả đích: bộ JSON/Markdown hợp nhất cho mọi target đủ nguồn, matrix/evidence cập nhật, review độc lập, coverage theo ID và hướng dẫn tiếp tục dùng khi dịch cảnh. Agent chính cập nhật trường riêng của tài liệu trong STATUS/CHECKPOINT và liên kết điều hướng sau khi kiểm artifact; giữ nguyên trạng thái luồng khác. Gói ZIP mới tùy nhu cầu, không thay gói đã bàn giao trước đó.

Không dừng ở danh sách tên hay một batch mẫu khi còn target làm được. Nếu thiếu nguồn/reviewer thật, hoàn tất phần khả thi và bàn giao đúng phần pending; không gọi toàn bộ đã xong. Không tự kéo dài bằng retry vô hạn, tìm web không giới hạn hoặc tạo quan hệ giả. Chỉ tìm nguồn ngoài khi cần và phù hợp phạm vi; ghi URL/locale/version nếu thực sự dùng. Không dùng kết luận từ bài wiki không có nguồn để thay script/record game.
