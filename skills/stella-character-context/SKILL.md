---
name: stella-character-context
description: Hoàn thiện hoặc tiếp tục hồ sơ khẩu khí, quan hệ và xưng hô nhân vật Stella Sora từ nguồn game có dẫn chứng, theo từng đợt có checkpoint và review độc lập. Dùng cho bộ tài liệu nhân vật của StellaSora_VietHoa; không dùng để tự dịch lại hay cài tài nguyên game.
---

# Hoàn thiện ngữ cảnh nhân vật Stella Sora

Mục tiêu là hoàn thiện nội dung còn thiếu trong roster được giao, gồm Voice Bible, hồ sơ JSON, quan hệ có hướng và hướng dẫn xưng hô theo cảnh. Tạo skill/prompt không có nghĩa đã chạy công việc này. Khi người dùng giao hoàn thiện, tiếp tục qua các batch đến hết danh sách đủ nguồn; không dừng sau một pilot hoặc chỉ báo kế hoạch.

## Chọn dự án và điểm tiếp tục

Dùng project root người dùng giao. Nếu workspace là thư mục cài game, project thường là `StellaSora_VietHoa/`; không tự tạo dự án mới. Đọc AGENTS → START_HERE → STATUS/CHECKPOINT → `docs/CHARACTER_CONTEXT_GUIDE_20261023.md`, STYLE_GUIDE_VI, DATA_CONTRACT. Các tài liệu này nằm trong dự án, không trong thư mục skill cài cá nhân.

Tìm baseline theo trường `character_context_documents` và checkpoint riêng của đợt nếu có; kiểm file/hash thực, không lấy thư mục tên mới nhất hoặc nhãn “100%” làm bằng chứng. Fallback đã biết: `work/character_context_20261023_r01/`. Roster, profiles, matrix, SOURCE_EVIDENCE và review bàn giao cũ phải được đối chiếu trước khi chia việc.

Có helper stdlib để lập inventory, không sinh nội dung hoặc phê duyệt:

```powershell
python scripts/inventory_remaining.py --project-root 'C:/YostarGames/StellaSora_EN/StellaSora_VietHoa' --out 'work/character_context_full_run/INVENTORY_r01.json'
```

Lệnh trên chạy từ thư mục skill. Từ nơi khác, dùng đường dẫn tuyệt đối tới script của skill đang đọc. `--out` tương đối project root, phải là file mới trong work/reports. Có thể dùng `--baseline-dir` với một revision cụ thể đã xác minh. Helper ghi nhận source drift; nếu preflight không ready, rebase nguồn trước khi chấp nhận nội dung mới. Danh sách preserved của helper chỉ là phân loại hồ sơ có căn cứ, không chứng minh review còn hiệu lực.

## Nghiên cứu và hoàn thiện

Đọc [references/completion-contract.md](references/completion-contract.md) khi bắt đầu khảo sát/batch và trước tổng hợp. Nó định nghĩa nội dung tối thiểu, checkpoint, cách tính coverage và điều kiện hoàn tất.

- Lấy danh sách còn thiếu từ hồ sơ thực, không cố định 34. Giữ ID biến thể riêng. Đối soát glossary-only/NPC/unknown-kind trong danh sách riêng, không bỏ âm thầm hoặc tự tính là playable. Hồ sơ tiền nhiệm có căn cứ được giữ; chỉ xét lại khi nguồn, context hoặc findings liên quan thay đổi.
- Tra bảng EN thật, hồ sơ, thư, chat/voice có người phát ngôn xác định và cảnh AVG khi adapter liên kết speaker/text có căn cứ. EN hiện có là nguồn chính; JPVA/CNVA chỉ là nhãn lồng tiếng nếu chưa có phụ đề JP/CN tương ứng. Không dùng cache VI làm nguồn EN; tên thư mục pristine không tự chứng minh nguồn nguyên bản.
- Mỗi kết luận có source path, hash file, key/locator thật, quote chính xác, attribution và phạm vi. Phân biệt nhân vật tự nói, người khác nhận xét và suy luận biên tập. Không coi thứ tự constant pool là thứ tự thoại, không chạy Lua/DLL trích xuất. Nếu thiếu liên kết speaker, tiếp tục nguồn archive đủ căn cứ thay vì bịa người nói.
- Viết hồ sơ VI cụ thể: nhịp câu, mức trực tiếp/kính ngữ, sắc thái theo tình huống, cách nói với Main/người nghe đã biết, điều nên tránh và khoảng trống. Không điền khuôn “tự nhiên, thân thiện” cho mọi nhân vật. Số ví dụ phải đủ hỗ trợ kết luận; không nhồi trích đoạn vô nghĩa để đạt quota. Ví dụ VI tự soạn ghi rõ minh họa, không giả làm thoại game.
- Ma trận là cạnh có hướng, có cảnh/nhánh/thời điểm và căn cứ. Quan hệ quan sát được và đại từ VI đề xuất là hai lớp khác nhau. Thiếu cạnh là unknown; không điền N×N bằng tôi–bạn. Không suy tuổi/giới/quan hệ từ ngoại hình, không rải bé cưng/đại nhân/ta–con. Chỉ rule approved đúng scope mới là khóa bắt buộc; chấp nhận tài liệu không tự phê duyệt mọi rule.

## Batch, review và tiếp tục

Ưu tiên một nhóm nhỏ theo cụm nguồn/nhân vật để dễ review, thường 3–5 hồ sơ; linh hoạt với lượng nguồn. Lập task packet/hash/allowlist trước phân công theo `docs/SUBAGENT_POLICY.md` và `agents/README.md`. Khi có subagent, dùng catalog/author và reviewer độc lập phù hợp; chỉ agent chính tổng hợp canonical JSON/Markdown và sửa STATUS/CHECKPOINT. Reviewer không sửa bản đang review; nếu tự viết lại thì cần người khác review phần đó. Không có subagent thì tiếp tục nội dung và kiểm tĩnh, giữ review pending cho người/phiên khác.

Mỗi batch: nguồn → evidence → hồ sơ/edges đề xuất → kiểm tĩnh → đóng băng hash → review từng hồ sơ/claim/edge → sửa finding → review lại phần ảnh hưởng → tổng hợp revision mới → checkpoint → batch tiếp theo. Không sinh approval hàng loạt, không tự đổi role để review bản mình viết. Mục vướng context được tách riêng, các mục khác vẫn tiếp tục.

Tạo output revision mới trong dự án; giữ baseline/ZIP/review cũ bất biến. Với resume, kiểm task/writer đã dừng, hash và predecessor; không đè file dang dở của tác giả khác. Sau hai lỗi giống nhau không có dữ kiện mới, ghi blocker cụ thể và chuyển phần độc lập; không lặp chờ vô hạn. Không tự đặt lịch hay mở chat khác để làm tiếp khi phiên kết thúc.

## Bàn giao và ranh giới

Bàn giao bộ hồ sơ hợp nhất, Voice Bible, matrix, evidence registry, coverage theo ID, unresolved issues, review/hash và checkpoint có lệnh tiếp tục. Chỉ báo hoàn tất khi tất cả target IDs đạt nội dung và review ở đúng phạm vi; nếu còn thiếu nguồn, ghi kết quả hữu ích kèm số pending và bằng chứng đã tìm, không bịa để đạt 100%.

Đây là công việc tài liệu offline. Không thay bản dịch game, glossary khóa, launcher, bundle, archive cài, executable/DLL, Anti-Cheat hoặc phát hành từ skill này. Không tuyên bố đã tự tích hợp sidecar vào pipeline hoặc đã kiểm runtime.
