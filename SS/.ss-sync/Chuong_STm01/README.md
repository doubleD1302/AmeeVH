# Đồng bộ Chương 1 lên Google Sheets

## Schema hiện hành: trang `Chuong_STm01`

Trang này dùng đúng 12 cột đã chốt, bắt đầu bằng `file_id`, `block_order`,
không có `block_id`. Chương 1 là story nên `source_refs_json` luôn trống.
Thứ tự cố định cho các lần xuất và push sau:

```text
file_id, block_order, kind, speaker_en, speaker_jp, speaker_cn,
speaker_vi, text_vi, text_cn, text_jp, text_en, source_refs_json
```

`speaker_vi` và `text_vi` luôn đứng cạnh nhau (cột G và H).

`export_chapter.py` đọc trực tiếp các Merge hiện tại và xuất schema này;
`partition_manifest.json` lưu ánh xạ 12 file, sheet/table ID và kết quả đọc lại
1.507 block, 18.096 ô. Các mục phía dưới mô tả lần xuất bản DB_* trước đó.
Script `prepare.py` phục vụ cấu trúc cũ; không dùng nó để ghi trang mới.

`export_chapter.py` cũng hỗ trợ chương khác bằng tham số `--chapter`, ví dụ:

```powershell
python .ss-sync/Chuong_STm01/export_chapter.py --chapter Chuong_STm00
python .ss-sync/Chuong_STm01/export_chapter.py --chapter Chuong_STm02
```

Mặc định vẫn là `Chuong_STm01`; `--file` chọn một file và `--chunk START COUNT`
xuất một đoạn dữ liệu theo vị trí bắt đầu từ 0. Script chỉ xuất dữ liệu ra stdout,
không tự ghi lên Sheet. Manifest hiện hành nằm trong `.ss-sync/<tên chương>/`.

Nguồn nội dung là 12 file `*_Merge.txt` trong
`StellaSora_TaiNguyen_EN_JP_CN_Text_20261101_r03/01_CotTruyen/01_Chinh/Chuong_STm01`.
Script chỉ đọc Merge, EN, JP, CN và glossary; không sửa các file này.

## Đề xuất chỉnh sửa: `DB_Proposals`

Cấu trúc hiện hành gồm sáu cột theo thứ tự:
`file_id`, `block_order`, `author_id`, `author_name`, `new_text`, `note`.
`block_order` là số, khớp bảng nội dung. Khóa đề xuất là
`(file_id, block_order, author_id)`, mỗi tác giả một đề xuất cho mỗi block.
Không dùng `session_id`, `block_id`, `base_block_revision`,
`proposal_revision` hoặc `updated_at`.

Các trang `DB_Scenes`, `DB_Blocks`, `DB_Control` đã được xóa theo yêu cầu.
`prepare.py` và `manifest.json` chỉ lưu quy trình cũ, không dùng để tái tạo
các trang này hoặc ghi đè cấu trúc hiện hành.

## Dữ liệu và khóa (lịch sử, không còn áp dụng)

- `DB_Scenes`: một dòng mỗi file Merge; đường dẫn tương đối tính từ `D:/SS`.
- `DB_Blocks`: một dòng mỗi block; thứ tự nội dung CN, JP, EN, VI giữ nguyên.
  `speaker_vi/en/jp/cn` lấy từ đầu block, không suy danh tính người nói.
  Đầu block chỉ có một nhãn dùng nhãn đó cho `speaker_vi`, ba cột còn lại để trống.
- `DB_Proposals`: khởi tạo trống; khóa duy nhất dự kiến là
  `(session_id, block_id, author_id)`. `proposal_revision` tăng khi một tác giả sửa
  chính đề xuất của mình. Cột `note` chứa chú thích.
- `DB_Control`: một dòng; `session_state` thuộc `OPEN`, `LOCKED`, `PUBLISHING`.
  Mã phiên áp dụng cho toàn bộ dữ liệu đã đưa vào DB; hiện mới có Chương 1.

`block_id` là UUID được cấp một lần và lưu trong `manifest.json`. Chạy lại cùng
nguồn sẽ dùng lại ID. Khi thứ tự thay đổi, script còn nhận diện được block có
source_hash duy nhất trong cảnh. Không xóa manifest trước các lần đồng bộ sau.
Thay nguồn gây nhập nhằng cần dev đối chiếu manifest trước khi push.

`source_hash` là SHA-256 của JSON UTF-8 được chuẩn hóa bằng `compact()` trong
script, gồm `speaker_raw`, `kind`, `cn`, `jp`, `en`; không bao gồm số thứ tự hay VI.
`revision` khởi tạo bằng 1 và tăng khi VI thay đổi. Manifest chỉ lưu hash VI hiện
hành, không lưu văn bản VI cũ.

`source_refs_json` lưu riêng từng ngôn ngữ. `matched` chỉ có một vị trí khớp chính
xác trong file nguồn của cảnh, có thể sau khi mở rộng token giới tính từ glossary.
`ambiguous` chứa các vị trí ứng viên và chưa chọn một vị trí; `unresolved` chưa
khớp nguồn cảnh; `missing_source` là dấu nguồn thiếu đã có trong Merge. Nội dung
Merge luôn được giữ nguyên dù trạng thái truy nguồn là gì. Một số tên liên hệ lấy
từ preset không xuất hiện trực tiếp trong file nguồn cảnh.

## Chuẩn bị và kiểm tra

```powershell
python -X utf8 .ss-sync/Chuong_STm01/prepare.py --summary
python -X utf8 .ss-sync/Chuong_STm01/prepare.py --verify-sources
```

`payload.json` chứa đúng nội dung hiện hành để connector ghi lên bốn tab DB của
spreadsheet ID `13ooFrJLyeP9LsSFrkzp4SWpQY5ePd6ap5muvWCwWOdM`.
Script kiểm tra 12 file, 1.507 block, bốn dòng nội dung mỗi block, thứ tự liên tục,
roundtrip nguyên byte UTF-8 BOM/CRLF và giới hạn kích thước ô.

Sau khi tất cả dữ liệu đã được đọc lại và so khớp, connector đặt Control thành
`OPEN`, ghi `release_id` và `opened_at`, xóa các trường pending. Sau đó chạy
`--mark-published`. File `verification.json` ghi kết quả kiểm tra của lần push.

Đợt này chỉ khởi tạo dữ liệu và metadata. API/frontend kiểm tra quyền, khóa phiên,
upsert đề xuất và chu trình xử lý phiên chưa được triển khai bằng script này.
Không lưu bản dịch cũ hoặc kho lưu đề xuất cũ.
