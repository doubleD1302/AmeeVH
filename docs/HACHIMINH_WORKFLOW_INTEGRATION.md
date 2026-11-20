# Đồng bộ quy trình Stella Sora với HachiMinh

Nguồn: `origin/main` commit `4b13a8d8563227f762e65360732590d7d024ef5b`, thư mục `SS/`, đưa vào checkout từ cây Git ngày 09/11/2026. Đọc `SS/AGENTS.md` và skill liên quan khi làm việc trong `SS/`. Các skill local khác tiếp tục dùng cho đúng phạm vi của chúng.

## Quy trình

- `SS/.agents/skills/merge`: tạo tài liệu đối chiếu từ bộ EN/JP/CN hợp lệ. Chỉ chạy theo phạm vi yêu cầu, bảo toàn bản đã hiệu đính.
- `update-term`: dùng CSV của SS làm nguồn term; chỉ thêm term đủ căn cứ. Sau mỗi lần thay đổi chạy `python tools/sync_ss_glossary.py --write`, sau đó `python tools/sync_ss_glossary.py` từ gốc dự án. Lệnh thứ hai phải thoát 0 trước khi các công cụ local dùng JSON. Script chỉ cập nhật term có EN trùng, giữ nguyên mục local khác. Term SS mới trong JSON có status `proposed`: đây là trạng thái tương thích, không tuyên bố review độc lập.
- `translate`: thêm VI vào Merge, đối chiếu nguồn, ghi hai báo cáo conflict/reference. Khi nguồn mâu thuẫn dùng EN theo SS và ghi rõ; kiểm tra ID, version và nguồn trước khi đối chiếu; không coi JPVA/CNVA là text JP/CN. EN trống theo ngoại lệ của SS phải ghi nguồn và không tự suy ra có thể build cho client EN.
- `workflow`: điều phối merge → term → translate → parent verify, checkpoint và quyền ghi theo SS. Nếu đi tiếp vào proposal/build dự án, review ngữ nghĩa độc lập theo AGENTS vẫn cần hoàn tất trên đúng hash. Kết quả verify của workflow không tự là approval cho archive.
- `update-sheet`: chỉ đồng bộ khi được yêu cầu, đúng phạm vi và có readback; không chạy chỉ vì workflow hoặc skill được cập nhật. Sheet là kênh cộng tác, không chứng minh review hoặc bản cài.

## Ranh giới dữ liệu

`SS/glossary/glossary.csv` quyết định target của term khớp EN. Các dòng ánh xạ tên/token không tự thành term; ghép theo ID và ngữ cảnh trong skill SS. `config/glossary.json` và `config/master_glossary.json` là projection tương thích; nội dung local không trùng được giữ, cùng status cũ. Nhãn status không chứng minh review bản dịch. CSV có thể đổi độc lập: luôn chạy lệnh kiểm tra drift trước khi dùng JSON.

`docs/MASTER_GLOSSARY.md`, phần notes và danh sách `forbidden`/`forbidden_calques` cũ có thể nêu target trái CSV. Chúng là dữ liệu lịch sử khi trùng term SS, không được dùng làm căn cứ ghi đè CSV. Các script cũ thay hàng loạt theo `forbidden` chưa được điều chỉnh theo glossary mới; không chạy chúng trên bản dịch thật cho đến khi rà từng quy tắc và xác minh scope.

Merge là tài liệu đối chiếu, có thể đã mở rộng ID/token hiển thị; không là dữ liệu build trực tiếp. Muốn đưa vào game phải map về nguồn gốc với ID, version, hash, token, đủ semantic review và các gate build/readback/runtime. Không thay nguồn, proposal, archive, game, Sheet, Git remote hay release chỉ vì cài quy trình.

## Kiểm tra

`python tools/sync_ss_glossary.py` trả exit 1 khi projection lệch CSV, không ghi dữ liệu; `--write` tạo lại hai projection. Việc đồng bộ target không thay bản dịch cũ, không xét ngữ nghĩa của các term hay xác nhận dữ liệu Sheet/game. Kiểm tra test helper SS trên project giả; không chạy workflow thật chỉ để xác nhận cấu hình.

Trên máy này Python mặc định là 3.10, thiếu `tomllib` mà workflow helper dùng. Dùng `py -3.14` thay `python` cho các lệnh `workflow_state.py` và `test_workflow_state.py` trong protocol SS. Các lệnh sync glossary ở trên chạy được với Python 3.10.
