# Hợp đồng helper và connector

Helper dùng Python standard library, không gọi mạng. Các lệnh chạy từ gốc SS:

```powershell
python -B .agents/skills/update-sheet/scripts/sheet_sync.py begin
python -B .agents/skills/update-sheet/scripts/sheet_sync.py scan --run TOKEN
python -B .agents/skills/update-sheet/scripts/sheet_sync.py scan --run TOKEN --scope "StellaSora_TaiNguyen_EN_JP_CN_Text_20261101_r03/01_CotTruyen/01_Chinh/Chuong_STm02"
python -B .agents/skills/update-sheet/scripts/sheet_sync.py prepare --run TOKEN --path MERGE_PATH --output PAYLOAD.json
python -B .agents/skills/update-sheet/scripts/sheet_sync.py build --run TOKEN --payload PAYLOAD.json --remote BEFORE.json --output PLAN.json
python -B .agents/skills/update-sheet/scripts/sheet_sync.py confirm --run TOKEN --plan PLAN.json --remote AFTER.json
python -B .agents/skills/update-sheet/scripts/sheet_sync.py finish --run TOKEN
```

`TOKEN` lấy từ `begin`. `MERGE_PATH` tính từ gốc project, dùng `/`. Tạo các file
JSON trung gian bằng thư viện JSON trong thư mục tạm, không dựng shell command
bằng nội dung lời thoại. `--project-root` là tùy chọn chung, đứng trước tên lệnh.
Khi đọc thử không muốn ghi state: `scan --dry-run`; `--rehash` đọc lại nội dung
mọi Merge trong phạm vi. Không gọi `begin` khi chỉ đọc thử. `scan --dry-run`
không có `--output` mới hoàn toàn không tạo artifact.

## State và baseline

State tách `published_sha256` khỏi `observed_sha256`, `observed_stat` và `pending`.
Stat gồm size, mtime_ns, ctime_ns, device và inode. Chỉ skip nội dung khi stat
khớp, hash quan sát bằng hash đã xác nhận và không pending.

Khởi tạo nhập file của manifest có `verification.matched: true` hoặc hash file
được lưu tại `verification.verified_files`. Thiếu baseline không được coi bản
local hiện tại là đã push. Pending được lưu trước lệnh connector để không mất
công việc khi HTTP timeout hoặc process bị ngắt.

`confirm` ghi receipt hash/metadata, rồi cập nhật manifest và state bằng thay
file nguyên tử. Hai file local không phải một giao dịch chung: nếu bị ngắt,
giữ pending và dùng readback mới để confirm lại. Không commit state chỉ dựa vào
receipt cũ vì remote hoặc local có thể đã đổi sau đó.

Manifest mới ghi `verification.scope: per_file`, `matched: false` và hash các
file đã có bằng chứng tại `verified_files`. Đây không phải thất bại readback:
chỉ có nghĩa không vừa kiểm tra lại toàn trang. `data_rows` là số block remote;
`verified_cells` chỉ tính ô của file vừa đọc lại, không bao gồm header. Giữ các
hash đã xác nhận trước đó nhưng không tuyên bố đã rà lại tất cả file lần này.

## Payload có cấu trúc khi không dùng được báo cáo dịch

`prepare` mặc định chỉ tự xuất từ hai HTML của translate khi chúng khớp hash
Merge, đủ coverage, có nội dung từng block khớp nhau và VI không trống. Báo cáo
thiếu/cũ không đồng nghĩa file chưa dịch; agent có thể xác minh và cung cấp:

```json
{
  "merge_sha256": "SHA256_NGUYEN_BYTE_GOM_BOM_CRLF",
  "blocks": [{
    "block_order": 1,
    "header": "1. [VI/ EN/ JP/ CN] (Lời thoại)",
    "source": {"CN": "中文", "JP": "日本語", "EN": "English"},
    "text_vi": "Tiếng Việt"
  }]
}
```

Gửi bằng `prepare ... --structured EXPORT.json`. Đủ mọi block theo đúng thứ tự,
`header` lấy nguyên văn không gồm CRLF cuối dòng. Nội dung JSON dùng xuống dòng
LF; helper kiểm tra ghép CN + LF + JP + LF + EN + LF + VI khớp nguyên phần thân.
Không thay đổi nguồn để làm khớp. Việc khớp phép ghép không tự chứng minh đã xác
định đúng ranh giới ngôn ngữ: agent phải đối chiếu trước khi tạo JSON.

Header story thường có bốn tên theo VI/EN/JP/CN hoặc một nhãn đặc biệt. Khi tên
có dấu `/ ` gây nhập nhằng, thêm `speakers: [VI, EN, JP, CN]` sau đối chiếu; helper
kiểm tra ghép lại đúng header. Ba tên nguồn chưa có VI không được tự nhận là bốn
tên. UI tĩnh không có `speakers`; giữ mã ở header. JSON tham chiếu được tạo theo
`{"EN":"mã EN","JP":"mã JP","CN":"mã CN"}`. Mã chung được lặp ở cả ba khóa;
mã khác nhau tách bằng nhãn `/JP:` và `/CN:`, không tách mọi dấu `/` trong mã.

Nếu file thiếu VI, source/header nhập nhằng hoặc có thông báo chẩn đoán nguồn
chưa được giải quyết, không tạo bản xuất giả để bỏ kiểm tra. Báo file bị chặn.

## Chuẩn hóa remote snapshot

Lấy dữ liệu mới bằng connector, không dùng payload local làm readback. Snapshot
cho `build` và `confirm` cùng một định dạng:

```json
{
  "spreadsheet_id": "13ooFrJLyeP9LsSFrkzp4SWpQY5ePd6ap5muvWCwWOdM",
  "exists": true,
  "title": "Chuong_STm02",
  "sheet_id": 2101040007,
  "row_count": 1187,
  "column_count": 12,
  "headers": ["file_id", "block_order", "kind", "speaker_en", "speaker_jp", "speaker_cn", "speaker_vi", "text_vi", "text_cn", "text_jp", "text_en", "source_refs_json"],
  "keys": [["STm02_01", 1], ["STm02_01", 2]],
  "rows": [],
  "table": {
    "table_id": "1037465531",
    "sheet_id": 2101040007,
    "headers": ["file_id", "block_order", "kind", "speaker_en", "speaker_jp", "speaker_cn", "speaker_vi", "text_vi", "text_cn", "text_jp", "text_en", "source_refs_json"],
    "start_row": 0,
    "start_column": 0,
    "end_row": 3,
    "end_column": 12,
    "block_order_type": "DOUBLE"
  }
}
```

Ví dụ chỉ minh họa định dạng; không dùng số liệu ví dụ thay kết quả đọc thật.
`keys` phải chứa **toàn bộ** cặp A:B của mọi file trong trang, theo thứ tự hàng,
không gồm tiêu đề. Chỉ bỏ hàng trống ở cuối; hàng trống giữa dữ liệu là lỗi.
`rows` chứa **đủ 12 ô của mọi block thuộc đúng file đang xử lý**, không chứa file
kế bên. File mới trong trang có sẵn dùng `rows: []`, nhưng keys vẫn phải đầy đủ.
Chuẩn hóa ô rỗng thành `""`; số nguyên hợp lệ thành integer; không trim nội dung.
Đọc userEnteredValue; không âm thầm đổi công thức thành kết quả tính toán rồi
ghi lại. Nếu gặp công thức hoặc kiểu ô không thuộc schema, đối soát trước.

Lấy row_count/column_count từ gridProperties; range, headers và kiểu cột B từ
native table metadata, không đoán từ tên tab. Nếu metadata connector không trả
tables, dùng batchUpdate readback/probe theo reference của Google Sheets skill.
Chỉ `table: null` khi đã xác minh thực sự chưa có table. Bảng có banding riêng
hoặc nhiều native table gây chồng lấn cần đối soát, không xóa banding tùy tiện.

Trang chưa tồn tại dùng:

```json
{
  "spreadsheet_id": "13ooFrJLyeP9LsSFrkzp4SWpQY5ePd6ap5muvWCwWOdM",
  "exists": false,
  "title": "TEN_TRANG_TU_PAYLOAD",
  "sheet_id": 123456789,
  "keys": [],
  "rows": []
}
```

Chọn sheet_id chưa dùng sau khi đọc metadata. Sau khi tạo, snapshot `AFTER`
phải chứa ID và native table thật từ kết quả connector, không dùng ID dự đoán.

## Gửi request và kiểm tra

`build` lưu pending rồi sinh `requests` và `expected_keys`. Agent gửi đúng mảng
requests bằng `batch_update_spreadsheet` tới spreadsheet đã cấu hình; không gửi
các trường `payload`, `run` hoặc `expected_keys` như request Google.

Helper chỉ sửa vùng của file: cập nhật cùng số hàng, thêm/xóa phần chênh lệch
khi số block đổi; file mới append vào cuối dữ liệu. Range native table được sửa
cho đủ mọi hàng. File có hàng không liên tục bị chặn. Phần còn lại giữ nguyên.
Sheet có sửa trực tiếp đồng thời không có compare-and-swap: phải điều phối để
không có writer khác đổi các trang đích giữa snapshot và ghi.

Đọc lại keys toàn trang, rows của file, headers và table metadata. `confirm`
kiểm tra đủ ô của file, vị trí khóa, kiểu B, phạm vi table và Merge vẫn đúng
phiên bản payload; không chỉ kiểm tra vài dòng đầu. Nếu rows đã khớp sau lần
ghi trước bị timeout, build có thể không cần request; vẫn confirm bằng dữ liệu
live để kết thúc pending.

Payload lớn: chia updateCells thành các lô theo hàng, giữ nguyên thứ tự yêu cầu
thêm/xóa trước ghi. Không chạy lại thao tác thêm/xóa sau timeout khi chưa đọc
remote mới. Nếu phải chia một batch, khoảng giữa các lô có thể chưa đầy đủ;
chưa confirm hoặc mở phiên web cho đến khi hoàn tất toàn file. Không tự retry
vô hạn hoặc thay request để ghi cả trang nhằm tránh đối soát.
