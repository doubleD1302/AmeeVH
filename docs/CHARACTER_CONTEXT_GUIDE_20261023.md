# Bộ ngữ cảnh nhân vật và dịch theo cảnh — Stella Sora

Ngày lập: 23/10/2026 (Asia/Saigon). Phạm vi: tài liệu, cấu hình đề xuất và mẫu ngữ cảnh offline. Không dịch đè batch, không repack, không cài game.

## Mở bộ tài liệu

- [Ma trận quan hệ có hướng](../work/character_context_20261023_r01/CHARACTER_RELATIONSHIP_MATRIX.json).
- [Roster và nguồn tên](../work/character_context_20261023_r01/CHARACTER_ROSTER.json).
- [Hồ sơ khẩu khí dạng JSON](../work/character_context_20261023_r01/CHARACTER_VOICE_PROFILES.json).
- [Voice Bible cho người đọc](../work/character_context_20261023_r01/CHARACTER_VOICE_BIBLE.md).
- [Mẫu context cảnh](../work/character_context_20261023_r01/SCENE_CONTEXT.template.json) và [mẫu review](../work/character_context_20261023_r01/SCENE_REVIEW.template.json).
- [Prompt dịch theo cảnh](../prompts/TRANSLATE_SCENE_CONTEXT_20261023.txt).
- [Bằng chứng và kết quả kiểm tra](../work/character_context_20261023_r01/EVIDENCE_AND_LIMITS.md).

## Phân biệt dữ kiện và lựa chọn biên tập

Tên đã approved trong glossary chứng minh cách viết tên của dự án. Ghi chú lore trong glossary, cache bản dịch hoặc lời của agent trước không tự chứng minh quan hệ canon. Phải lưu nguồn EN thật, hash file, locator hàng/field hoặc đường constant/prototype, trích đoạn và phạm vi kết luận. Nếu chưa chứng minh được snapshot gốc, ghi rõ nguồn ứng viên; không gọi là pristine.

Quan hệ như bạn thuở nhỏ, chủ–thị vệ, tuổi tác, thân phận, giới của người chơi và biệt danh thân mật cần bằng chứng riêng. Một câu thể hiện lo lắng chỉ chứng minh lo lắng trong cảnh đó. Không từ một câu suy ra tính cách vĩnh viễn. Xưng “tớ–cậu” là lựa chọn VI có thể đề xuất, không phải dữ kiện nguyên văn EN.

Trạng thái: `source_observed` = đã đọc đúng trích đoạn; `proposed` = lựa chọn biên tập chưa khóa; `approved` = quyết định có người review độc lập và phạm vi; `pending_context` = thiếu chứng cứ; `conflict` = nguồn/quy tắc xung đột; `obsolete` = snapshot đã đổi. Chỉ quy tắc approved đúng scope được dùng như quy tắc bắt buộc. Không được nâng toàn bộ profile thành approved chỉ vì tài liệu đã qua review.

## Ma trận có hướng và có phạm vi

Lưu quan hệ dạng danh sách cạnh thưa. A→B và B→A là hai quyết định khác nhau; thiếu cạnh nghĩa là chưa biết, không phải “tôi–bạn”. Không cần tạo N×N dòng trống hoặc tự điền tất cả cặp bằng suy đoán.

Mỗi cạnh có người nói, người nghe (một hoặc nhiều), căn cứ quan hệ, lựa chọn xưng/gọi, điều kiện chọn, cảnh/nhánh/thời điểm/độ thân mật và review. Không gán đại từ theo một danh sách lựa chọn ngẫu nhiên. Nếu có hai rule cùng ưu tiên và đều hợp cảnh nhưng mâu thuẫn, mở issue rồi resolve; không âm thầm chọn bản mới nhất.

Ưu tiên nghĩa và bằng chứng cảnh → override đã duyệt đúng cảnh/nhánh → cặp có hướng đã duyệt đúng phạm vi → giọng nhân vật đã duyệt. Glossary khóa cách dịch thuật ngữ, không thay được bằng chứng người nghe. Nếu glossary chuẩn và master glossary xung đột, ghi issue để người quản lý giải quyết, không tự chọn theo văn phong thích hơn.

Cảm xúc thay đổi có thể đổi nhịp câu hoặc độ trực diện; không tự biến “cậu” thành “mày”. Đổi xưng hô phải có tín hiệu và ghi mốc thay đổi. Cảnh cải trang, công khai/riêng tư, độc thoại, trích dẫn và hồi tưởng phải được phân biệt.

## Xác định cảnh, người nói và người nghe

1. Chốt phiên bản nguồn, locale và variant. EN trong bản cài là nguồn hiện có; JPVA/CNVA là nhãn giọng, không mặc nhiên là phụ đề JP/CN.
2. Đọc toàn cảnh và các nhánh; đặt ID ổn định cho dòng, giữ cue/field/constant path thật. Số thứ tự trong cache regex không phải locator chắc chắn.
3. Xác định speaker từ cấu trúc script/bảng hoặc transcript đã kiểm. Không lấy nhân vật trên màn hình làm người nói mặc định; giữ alias chưa lộ danh tính để tránh spoiler.
4. Xác định addressee từ gọi tên, logic thực thi và đáp lời có căn cứ. Người nói kế tiếp hoặc tất cả người có mặt không tự là người nghe. Lưu phân biệt cá nhân, nhóm, độc thoại, khán giả và unknown. Nhắc tên người thứ ba không có nghĩa đang nói với họ.
5. Với Lua bytecode, constant pool có thể gộp/dùng lại tên, lệnh và text. Thứ tự constant không chứng minh trình tự thoại hay liên kết speaker→text. Nếu chưa có trace/disassembly/adapter bảo toàn quan hệ, không gán speaker chắc chắn và không tự chạy Lua/DLL trích xuất.
6. Chia theo ranh giới cảnh và nhánh, không cắt máy móc mỗi 10–20 câu. Nếu cảnh dài, dùng đoạn 20–40 câu theo AGENTS với phần context chồng lấn chỉ đọc; mỗi ID chỉ một writer. Giữ mốc trước/sau và issue xuyên cảnh.

## Dịch khi thiếu thông tin

Ưu tiên cấu trúc VI có thể lược đại từ hoặc gọi tên nếu đúng nghĩa, tự nhiên và không thêm ý. Không bắt mọi câu phải có đủ chủ ngữ–đại từ. Không lược chủ thể nếu làm mơ hồ ai bảo vệ/ra lệnh/nhận hành động. Nếu lựa chọn phụ thuộc vai vế chưa rõ, đánh dấu pending_context và tiếp tục những dòng đủ thông tin. Không đưa chữ UNKNOWN hoặc placeholder giải thích vào text game.

Không tự xưng chị/em/ta/thuộc hạ; không gọi đại nhân/tiểu thư/bé cưng vì ngoại hình hoặc nhãn “anime”. Không lạm dụng “ạ”, “nè”, dấu ba chấm hay tiếng cười để tạo cá tính. Giữ khẩu khí qua nhịp, mức trực tiếp, từ vựng và tình huống có trong nguồn. Có thể dùng bị động tự nhiên khi cần; tránh máy móc xóa “bị/được” làm đảo nghĩa.

## Hợp đồng với pipeline hiện có

JSON mới là sidecar ngữ cảnh và tài liệu đề xuất; chưa có adapter tự nạp vào pipeline dịch. Không gọi localize.py với schema sidecar này, không khẳng định tool đã cưỡng chế xưng hô. Với proposal hiện có, giữ nguyên schema/ID/source/hash; chỉ sửa text_vi và notes theo DATA_CONTRACT. Với bảng/Lua, dùng adapter và gate đúng loại dữ liệu, không mượn PASS của SRT.

Giữ mọi token/tag, rich text, số, ngắt dòng được bảo vệ, ruby `<r=...>`, escape và tên khóa. Không dùng regex xóa ký tự “rác” đầu câu từ cache; đọc lại string bằng parser trước. Chuẩn hóa VI NFC; không chuẩn hóa lại byte nguồn để che khác biệt hash. Không chạy thay thế đại từ toàn cục trên bản dịch hiện có.

## Review và tiếp tục

Translator tạo proposal revision mới, ghi các rule đã dùng và issue. Đóng băng hash proposal/context/matrix/voice/glossary rồi giao reviewer độc lập. Reviewer đọc từng nguồn, đích và cảnh, ghi nhận xét cụ thể từng ID: nghĩa, người nghe, xưng hô, giọng, độ tự nhiên, token và vấn đề chưa biết. Reviewer tự viết lại câu sẽ trở thành tác giả phần đó; cần người khác review trước khi chấp nhận.

Kiểm schema/hash/NFC không chứng minh giọng nhân vật hoặc quan hệ đúng. Những bản dịch đã có không mất hay tự nhận approval do tài liệu này. Nguồn hoặc ngữ cảnh đổi phải rebase, tạo revision và review lại phần ảnh hưởng. Lưu checkpoint riêng của đợt; không ghi “toàn game đã đúng xưng hô”. Runtime, font/layout và gameplay là các gate riêng.

## Ví dụ minh họa không phải thoại game

Đây là ví dụ tự tạo để giải thích lựa chọn đại từ; không phải lời thoại hay bằng chứng quan hệ Stella Sora.

Nguồn giả định: “Don't worry, I'll protect you!”

- Nếu một cảnh giả định đã xác nhận cặp ngang hàng dùng tớ–cậu: “Đừng lo, tớ sẽ bảo vệ cậu!”
- Nếu một cảnh giả định khác đã xác nhận người nói xưng tôi và gọi người nghe là cô: “Đừng lo, tôi sẽ bảo vệ cô!”

Hai câu giữ cùng người thực hiện và người được bảo vệ; lựa chọn phụ thuộc context. Nếu cảnh game chưa đủ thông tin, giữ pending_context hoặc đề xuất cách diễn đạt bảo toàn nghĩa để reviewer xét. Không lấy một câu ví dụ làm đáp án mặc định.

## Tiêu chí dùng được

Có source/hash và locator thật; speaker/listener không bị đoán thành fact; chỉ rule approved đúng scope mới bắt buộc; profile không bịa tuổi/quan hệ/catchphrase; ID/token không thay đổi; review gắn snapshot; cấu hình được nạp có chủ đích khi dịch. Bộ này chuẩn bị cách làm và dữ kiện đã đọc, không phải bằng chứng bản dịch hoặc game đã thay đổi.
