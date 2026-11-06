# Web sử dụng Google Sheets database

Tài liệu này mô tả cấu trúc dữ liệu đã chốt cho web đọc nội dung Stella Sora,
nhận đề xuất của dịch giả và phối hợp với việc cập nhật từ local.

Schema và quy tắc xử lý dưới đây là quy ước cần tuân theo. Các cơ chế đăng nhập,
ghi đề xuất và chuyển phiên là yêu cầu cho backend tương lai, chưa phải tính năng
đã được triển khai trong workspace này. Phần **Gợi ý tích hợp** chỉ là tham khảo.

## 1. Spreadsheet và trạng thái đồng bộ

- Spreadsheet: [StellaSora_BanDich_GoogleSheets](https://docs.google.com/spreadsheets/d/13ooFrJLyeP9LsSFrkzp4SWpQY5ePd6ap5muvWCwWOdM/edit).
- Spreadsheet ID: `13ooFrJLyeP9LsSFrkzp4SWpQY5ePd6ap5muvWCwWOdM`.
- Trạng thái dưới đây ghi nhận các lần push đã được đọc lại và đối chiếu,
  tính đến ngày 06/11/2026; không phải trạng thái được tự động cập nhật theo Sheet.

| Trang | File Merge | Block | Trạng thái đồng bộ |
|---|---:|---:|---|
| `Chuong_STm00` | 2 | 112 | Hoàn tất, đã đối chiếu |
| `Chuong_STm01` | 12 | 1.507 | Hoàn tất, đã đối chiếu |
| `Chuong_STm02` | 14 | 1.703 | Hoàn tất các Merge hiện có, đã đối chiếu |
| `03_BangText_UI_KyNang` | 1 | 1.324 | Đang đồng bộ dở cả nhóm; file `Achievement` đã hoàn tất, đã đối chiếu |

Ba trang chương trên đã đồng bộ xong các Merge hiện có. Nhóm UI tĩnh mới có
`Achievement` được merge, dịch và đồng bộ; chưa có nghĩa toàn nhóm UI đã xong.
`DB_Proposals` là trang dùng chung để nhận đề xuất, không phải một chương nội dung.

Các lần đồng bộ sau phải cập nhật bảng theo kết quả thực tế:

- **Hoàn tất đồng bộ:** toàn bộ dữ liệu dự kiến đã push và đã đối chiếu thành công.
- **Đang đồng bộ dở:** mới ghi một phần hoặc chưa hoàn tất kiểm tra. Không công bố
  phần dữ liệu đang cập nhật như một phiên hoàn chỉnh cho web.
- **Chưa đồng bộ:** chưa đưa dữ liệu vào các trang theo schema mới. Nội dung có
  trong một tab cũ không có nghĩa là đã đồng bộ theo schema này.

Trạng thái đồng bộ không đồng nghĩa bản dịch đã được hiệu đính hoàn tất. Các nhóm
ngoài bảng trên chưa có xác nhận hoàn tất theo tài liệu này; bổ sung trạng thái cụ
thể khi triển khai, không tự suy ra là đã xong hoặc đang làm dở.

### Quy tắc chia trang theo folder

Đường dẫn trong bảng tính từ thư mục
`StellaSora_TaiNguyen_EN_JP_CN_Text_20261101_r03/`.

| Nhóm nguồn | Đơn vị tương ứng một trang tính |
|---|---|
| `01_CotTruyen/01_Chinh/` | Mỗi folder con, ví dụ `Chuong_STm01` |
| `01_CotTruyen/02_SuKien/` | Mỗi folder con |
| `01_CotTruyen/` ngoài hai nhóm trên | Mỗi folder con, ví dụ `03_NgoaiTruyen` |
| `02_NhanVat/` | Mỗi folder con nhân vật |
| `03_BangText_UI_KyNang/` | Toàn bộ folder chung một trang |
| `04_PhuDeVideo/` | Toàn bộ folder chung một trang |
| `90_CN_Moi_2.0.1/` | Toàn bộ folder chung một trang |

Một trang có thể chứa nhiều file Merge; `file_id` phân biệt các file bên trong.
Không tự chia mỗi file thành một trang khi folder đã được gom theo quy tắc trên.
Chỉ push Merge đã dịch theo yêu cầu đồng bộ; không tự nối các bước tạo Merge,
dịch và push. `05_Lua`, `99_DuLieuGoc`, `99_DuLieuGoc_EN` không thuộc phạm vi
phân chia dữ liệu hiện tại.

Workbook còn các tab từ cấu trúc trước đây. Backend cần danh sách trang nội dung
được cấu hình rõ ràng, hiện gồm ba chương và trang UI trên; không đọc tất cả tab như thể
chúng cùng schema. `DB_Proposals` được xử lý riêng.

## 2. Schema trang nội dung

Các trang nội dung dùng cố định 12 cột, từ A đến L:

```text
file_id, block_order, kind, speaker_en, speaker_jp, speaker_cn,
speaker_vi, text_vi, text_cn, text_jp, text_en, source_refs_json
```

| Cột | Tên | Ý nghĩa |
|---|---|---|
| A | `file_id` | Tên file Merge bỏ hậu tố `_Merge.txt`, ví dụ `STm01_01` |
| B | `block_order` | Số thứ tự block trong file, bắt đầu từ 1 |
| C | `kind` | Loại nội dung lấy từ Merge story; UI tĩnh để trống |
| D | `speaker_en` | Tên hoặc nhãn người nói EN trong Merge |
| E | `speaker_jp` | Tên hoặc nhãn người nói JP trong Merge |
| F | `speaker_cn` | Tên hoặc nhãn người nói CN trong Merge |
| G | `speaker_vi` | Tên hoặc nhãn người nói VI trong Merge |
| H | `text_vi` | Bản dịch VI hiện hành |
| I | `text_cn` | Nội dung CN từ Merge |
| J | `text_jp` | Nội dung JP từ Merge |
| K | `text_en` | Nội dung EN từ Merge |
| L | `source_refs_json` | Tham chiếu nguồn của UI tĩnh dưới dạng chuỗi JSON; story để trống |

`speaker_vi` và `text_vi` luôn đứng cạnh nhau ở G và H. Backend nên ánh xạ ô
theo tên header và kiểm tra đủ schema trước khi dùng, thay vì chỉ đoán vị trí cột.

### Khóa và thứ tự

- Một block được xác định bằng cặp `(file_id, block_order)`.
- `file_id` phải duy nhất giữa các trang nội dung. Nếu trùng tên file ở hai nhóm,
  phải giải quyết tên trước khi đưa lên DB vì bảng đề xuất không chứa tên trang.
- `block_order` là số nguyên dương, sắp xếp theo số trong từng file; không sắp xếp
  như chuỗi khiến `10` đứng trước `2`.
- Số hàng Google Sheets chỉ là vị trí lưu, không phải danh tính block. Không giữ
  một số hàng làm khóa lâu dài vì sắp xếp/chèn hàng có thể thay đổi vị trí.
- Không thay cách đánh thứ tự block trong một phiên đang mở. Cập nhật cấu trúc
  file hoặc thứ tự block phải đi qua quy trình chuyển phiên.

### Story và UI tĩnh

**Story:** giữ `kind` và các nhãn người nói theo file Merge; `source_refs_json`
để trống. Không phải block nào cũng có người nói ở đủ bốn ngôn ngữ. Ví dụ, đầu
block chỉ có một nhãn dẫn chuyện thì giữ nhãn ở `speaker_vi`, ba cột còn lại trống.
Không suy đoán danh tính thay cho `???` hoặc tự điền tên còn thiếu.

Ví dụ story giả định để minh họa bố cục, không phải trích nội dung game:

```json
{
  "file_id": "STm01_01",
  "block_order": 15,
  "kind": "thoại",
  "speaker_en": "???",
  "speaker_jp": "???",
  "speaker_cn": "???",
  "speaker_vi": "???",
  "text_vi": "Chúng ta đi thôi.",
  "text_cn": "我们走吧。",
  "text_jp": "行こう。",
  "text_en": "Let's go.",
  "source_refs_json": ""
}
```

Giá trị `kind` trên chỉ minh họa; không phải enum quy định cho backend. Dữ liệu
thực tế lấy nguyên loại đã lưu trong Merge.

**UI tĩnh:** `kind` và cả bốn cột `speaker_*` để trống. Nội dung vẫn dùng đủ bốn
cột `text_*`; tham chiếu nguồn nằm trong `source_refs_json`.

Ví dụ giả định cho một nhãn giao diện:

```json
{
  "file_id": "ExampleUI",
  "block_order": 1,
  "kind": "",
  "speaker_en": "",
  "speaker_jp": "",
  "speaker_cn": "",
  "speaker_vi": "",
  "text_vi": "Bắt đầu",
  "text_cn": "开始",
  "text_jp": "開始",
  "text_en": "Start",
  "source_refs_json": "{\"EN\":\"example/ui/start\",\"JP\":\"example/ui/start\",\"CN\":\"example/ui/start\"}"
}
```

`source_refs_json` của UI tĩnh dùng đối tượng có ba khóa `EN`, `JP`, `CN`, giữ
nguyên mã nguồn từng ngôn ngữ trong header Merge. Mã chung được lặp ở cả ba khóa;
mã riêng giữ cả dấu `/` bên trong mã, không tách mọi dấu `/`. Các mã trong ví dụ
chỉ minh họa. Không suy ra loại dữ liệu chỉ từ việc không có người nói, vì story
cũng có lời dẫn.

Web và local phải giữ nguyên token điều khiển, placeholder, ID và thẻ định dạng
trong nội dung. Không bỏ block chỉ có dấu câu, lựa chọn hoặc nốt nhạc. Nội dung
nguồn và bản VI không được tự chuẩn hóa theo cách làm thay đổi các ký hiệu đó.

## 3. `DB_Proposals`: một dòng cho mỗi tác giả và block

Trang đề xuất dùng đúng sáu cột, từ A đến F:

```text
file_id, block_order, author_id, author_name, new_text, note
```

| Tên | Ý nghĩa |
|---|---|
| `file_id` | File chứa block được đề xuất sửa |
| `block_order` | Thứ tự block, kiểu số, khớp trang nội dung |
| `author_id` | Định danh ổn định lấy từ đăng nhập đã xác thực |
| `author_name` | Tên hiển thị của tác giả, không dùng làm khóa |
| `new_text` | Bản VI tác giả đề xuất cho block |
| `note` | Chú thích đi kèm đề xuất |

Khóa duy nhất trong phiên hiện hành là `(file_id, block_order, author_id)`.
Một người có tối đa một dòng cho một block, nhưng được gửi lại để sửa đề xuất.

### Quy tắc tạo và ghi đè

1. Backend lấy tác giả từ đăng nhập, không tin `author_id` hoặc tên tác giả do
   trình duyệt tự khai. Tên hiển thị lấy từ thông tin tài khoản đáng tin cậy.
2. Kiểm tra phiên dữ liệu, trạng thái nhận đề xuất và block đích tồn tại.
3. Tìm theo bộ ba khóa. Chưa có thì tạo dòng; đã có thì cập nhật `new_text`,
   `note` và `author_name` trên chính dòng đó. Chú thích mới trống thì thay chú
   thích cũ bằng giá trị trống, không tự giữ lại.
4. Chỉ báo thành công sau khi ghi thành công. Nội dung nhập được lưu như văn
   bản, không biến thành công thức Google Sheets.

Hai tác giả khác nhau luôn có hai dòng riêng. Chỉ đề xuất cùng tác giả, cùng
file, cùng block mới ghi đè lẫn nhau. Việc gửi không tự cập nhật `text_vi` hoặc
file Merge; áp dụng đề xuất là công việc riêng của dev/local AI theo yêu cầu.

### Gửi đồng thời và thứ tự ghi đè

Với cùng khóa, yêu cầu hợp lệ được backend nhận sau sẽ thay yêu cầu trước.
"Nhận sau" là thứ tự backend điều phối xử lý, không phải giờ do trình duyệt gửi,
thứ tự người dùng bấm nút hoặc thời điểm một lệnh ghi Sheet tình cờ hoàn tất.

Backend phải điều phối thứ tự chung khi có nhiều instance và tuần tự hóa toàn
bộ thao tác **tìm khóa → tạo/cập nhật**. Hàng đợi hoặc cơ chế khóa cụ thể do bên
triển khai lựa chọn, nhưng phải giữ được hành vi trên. Chỉ gọi append hoặc update
riêng lẻ không ngăn hai yêu cầu cùng thấy "chưa có" rồi tạo hai dòng.

Không cần thêm số thứ tự xử lý hoặc thời gian vào cột Sheet để thực hiện quy
tắc này. Backend quản lý phần điều phối. Nếu phát hiện dữ liệu đã trùng khóa,
không đoán dòng thắng theo vị trí hàng: schema không có thông tin lịch sử để
khôi phục chắc chắn thứ tự nhận; cần đối soát trước khi tiếp tục ghi khóa đó.

Chỉ tạo dòng cho đề xuất thực tế, không tạo sẵn mọi tổ hợp. Với B block và T
dịch giả, số dòng tối đa trong một phiên là **B × T**, bất kể số lần gửi lại.

## 4. Phiên dữ liệu do backend quản lý

`dataset_version` xác định phiên dữ liệu đang được web sử dụng. Đây là phiên
nội dung dùng chung cho toàn bộ trang dữ liệu, khác phiên đăng nhập của tác giả.

Backend giữ mã phiên và trạng thái mở/khóa nhận đề xuất trong bộ lưu trữ bền
vững, dùng chung giữa các instance. Không chỉ giữ trong RAM, không tự tạo phiên
mới khi khởi động lại và không tái sử dụng mã phiên cũ. Không cần thêm bảng
`DB_Control` hoặc cột phiên vào Sheet cho cơ chế này.

### Khi tải và gửi từ frontend

- Nội dung trả về luôn đi cùng mã phiên của chính nội dung đó. Mọi phần nội dung
  và cache dùng để hiển thị cùng nhau phải thuộc cùng phiên.
- Khi gửi, frontend kèm mã phiên đã đọc cùng khóa block và nội dung đề xuất.
  Đây là thông tin của yêu cầu web, không phải cột mới trong `DB_Proposals`.
- Backend chỉ tạo/ghi đè khi phiên khớp phiên hiện hành và đang mở nhận.
  Thiếu phiên, phiên cũ hoặc đang khóa thì không ghi dữ liệu.
- Khi tab cũ bị từ chối, frontend giữ bản nháp, tải lại nội dung và để dịch giả
  xem lại trước khi gửi. Không chỉ thay mã A thành B rồi gửi bản nháp trên dữ
  liệu cũ như thể người dùng đã đọc phiên mới.
- Ghi đè chỉ áp dụng trong cùng phiên hợp lệ. Một yêu cầu A đến muộn không được
  phép thay đề xuất của B, dù backend nhận yêu cầu A sau.

Backend kiểm tra phiên và ghi đề xuất trong cùng cơ chế phối hợp với khóa chuyển
phiên. Kiểm tra một lần trước khi xếp hàng là chưa đủ: yêu cầu đang chờ không
được ghi lọt sau khi đề xuất A đã bị xóa để mở B.

### Dev chuyển từ phiên A sang B

Dev chủ động điều phối qua backend. Công cụ local hiện chưa tự khóa/mở phiên.

1. **Khóa nhận đề xuất.** Chặn yêu cầu mới và chờ các yêu cầu ghi đang xử lý hoàn
   tất. Các yêu cầu còn chờ phải hoàn tất trước bước xóa hoặc bị từ chối; không
   cho chúng chạy tiếp vào phiên B.
2. **Xử lý đề xuất A cần sử dụng.** Đọc và áp dụng các đề xuất cần thiết trước
   khi xóa. Không tự áp dụng hoặc tự tạo kho lịch sử nếu chưa được yêu cầu.
3. **Push nội dung local.** Chỉ đưa Merge đã dịch lên các trang theo đúng schema.
   Trong lúc cập nhật, web không phục vụ dữ liệu đang ghi dở như phiên hoàn chỉnh.
4. **Kiểm tra kết quả.** Đối chiếu file, số block, khóa, thứ tự cột và giá trị ô.
5. **Xóa đề xuất A.** Xóa nội dung các dòng đề xuất, giữ tiêu đề sáu cột và cấu
   trúc trang `DB_Proposals`. Không xóa các dòng trên trang nội dung.
6. **Chuẩn bị B.** Tạo mã phiên mới, làm mới nội dung/cache và bảo đảm chúng khớp
   kết quả đã kiểm tra. Không gắn cache A với mã B.
7. **Công bố B và mở nhận.** Mọi instance phải thống nhất phiên/trạng thái mới
   trước khi nhận đề xuất trở lại.

Nếu thất bại giữa chừng, giữ trạng thái khóa đến khi khôi phục và kiểm tra xong;
không tự mở lại vì backend vừa khởi động lại. Google Sheets và trạng thái backend
không phải một giao dịch chung, nên không được giả định toàn bộ quy trình tự
rollback khi một bước lỗi. Dev xác định bước đã hoàn tất trước khi tiếp tục.

`DB_Proposals` chỉ chứa đề xuất của một phiên tại một thời điểm. Khi B mở, cùng
tác giả được tạo đề xuất mới cho cùng block vì đề xuất A đã xóa. Việc xóa này
không xóa bản VI hiện hành trên trang nội dung.

## 5. Gợi ý tích hợp web và local

Phần này là gợi ý, không phải danh sách tính năng bắt buộc. Có thể bỏ những thao
tác hoặc màn hình chưa cần. Không ấn định framework, URL API, giao diện quản trị
hoặc công cụ tự động hóa; vẫn giữ các quy tắc toàn vẹn dữ liệu ở các mục trên.

### Phía web

- Cho chọn nhóm/trang, chọn file và đọc block theo `block_order`; hiển thị VI
  cạnh nội dung nguồn để đối chiếu.
- Có thể lấy đề xuất hiện tại của người đang đăng nhập để họ tiếp tục chỉnh
  sửa; lần gửi sau ghi đè chính dòng của họ.
- Có thể thông báo riêng các tình huống phiên cũ, đang cập nhật và ghi thất bại;
  giữ bản nháp khi chưa xác nhận ghi thành công.
- Dev có thể dùng thao tác backend có kiểm soát để khóa nhận, kiểm tra trạng
  thái và mở phiên. Không nhất thiết cần xây một trang quản trị riêng.
- Frontend trao đổi với backend; thông tin xác thực Google và quyền ghi Sheet
  đặt phía backend, không đưa vào mã chạy trên trình duyệt.

### Phía local

Skill [update-sheet](.agents/skills/update-sheet/SKILL.md) được dùng khi yêu cầu
cập nhật sheet database. Skill tìm Merge mới hoặc thay đổi trong phạm vi yêu
cầu, chỉ cập nhật file đã dịch đủ và đọc lại dữ liệu vừa ghi để xác nhận.

Trạng thái local ở `.ss-sync/update-sheet/state.json`: lần đầu nhập hash từ
manifest và đọc/hash để lập mốc metadata. Các lần sau chỉ duyệt tên và stat file;
không đọc nội dung file đã đồng bộ có metadata không đổi. File mới, metadata đổi
hoặc còn pending mới cần đọc/hash; metadata đổi nhưng hash không đổi không gây
push. Có chế độ `--rehash` khi cần phát hiện cả thay đổi giữ nguyên metadata.
Cache này không tự phát hiện chỉnh sửa trực tiếp trên Sheet ở file đang bỏ qua.

Skill không tự chuyển phiên backend hoặc xóa `DB_Proposals`. Khi web đã hoạt
động, dev phải khóa nhận và điều phối chuyển phiên theo mục 4. Manifest có kiểm
tra theo từng file không có nghĩa vừa đối chiếu lại toàn bộ trang.

Exporter hiện có: [export_chapter.py](.ss-sync/Chuong_STm01/export_chapter.py).
Script đọc Merge story hiện tại và xuất JSON ra stdout, chưa tự ghi Sheet hoặc
điều phối phiên. Ví dụ:

```powershell
python .ss-sync/Chuong_STm01/export_chapter.py --chapter Chuong_STm00
python .ss-sync/Chuong_STm01/export_chapter.py --chapter Chuong_STm01
python .ss-sync/Chuong_STm01/export_chapter.py --chapter Chuong_STm02
python .ss-sync/Chuong_STm01/export_chapter.py --chapter Chuong_STm02 --file STm02_01
```

Mặc định là `Chuong_STm01`. Tùy chọn `--chunk START COUNT` xuất một đoạn dữ liệu
theo vị trí bắt đầu từ 0. Exporter này dành cho story; chưa phải công cụ xuất
UI tĩnh theo tham chiếu nguồn.

Manifest hiện hành của từng chương:

- [Chuong_STm00](.ss-sync/Chuong_STm00/partition_manifest.json).
- [Chuong_STm01](.ss-sync/Chuong_STm01/partition_manifest.json).
- [Chuong_STm02](.ss-sync/Chuong_STm02/partition_manifest.json).

Manifest lưu ánh xạ file, hash nguồn, schema, sheet/table ID và kết quả kiểm tra
lần đồng bộ. Đây là hồ sơ local, không thay thế `dataset_version` hiện hành của
backend. Hash nguồn trong manifest không phải cột cần thêm vào Sheet.

Local AI có thể đọc đề xuất theo khóa block để hỗ trợ dev đối chiếu. Việc sửa
Merge, dịch và push vẫn là các bước riêng, chỉ thực hiện theo yêu cầu. Không lấy
bản dịch tạm ghi đè phần VI người dùng đã sửa thủ công.

Không được phép đổi cấu trúc các cột trong database khi chưa có sự đồng ý.

## 6. Ví dụ kiểm tra hành vi

Các ví dụ sau là tiêu chí cho backend tương lai, không phải kết quả kiểm thử
một backend đã triển khai. Giả sử block là `(STm01_01, 15)`:

| Tình huống | Kết quả cần đạt |
|---|---|
| Tác giả X và Y cùng gửi cho block | Hai dòng, mỗi dòng thuộc một tác giả |
| X gửi lại bản sửa trong cùng phiên | Vẫn một dòng của X, nội dung và chú thích được thay mới |
| Hai yêu cầu của X đến gần như đồng thời | Vẫn một dòng; yêu cầu hợp lệ nhận sau thắng |
| Y gửi sau X | Dòng của Y không ghi đè dòng của X |
| Tab A gửi sau khi B đã mở | Bị từ chối, không tạo hoặc cập nhật dòng của B |
| Yêu cầu A đang ghi lúc dev khóa | Hoàn tất trước bước xóa; không được ghi lọt vào B |
| Push thất bại hoặc backend khởi động lại lúc khóa | Giữ khóa; khôi phục và kiểm tra trước khi mở |
| X gửi lại cùng block khi B đã mở | Tạo đề xuất thuộc B sau khi đã tải nội dung B |

Sau mỗi lần push, đối chiếu schema với `AGENTS.md`, manifest tương ứng và dữ
liệu đọc lại từ Sheet; cập nhật trạng thái đồng bộ ở đầu tài liệu. Việc một ô
VI không trống hoặc một trang đã push xong không chứng minh nội dung đã hiệu
đính hoàn tất.
