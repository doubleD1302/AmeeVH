# Báo cáo HTML của translate

Hai file tích lũy: `reports/translation-conflicts.html` và
`reports/translation-references.html`, tính từ gốc SS. Mỗi HTML tự chứa dữ liệu
JSON nhúng; không có JSON ngoài làm kho dữ liệu. Dùng helper để đọc/cập nhật,
không thay chuỗi thủ công trong HTML. Helper chỉ tổ chức kết quả, không dịch
hoặc phát hiện xung đột/reference bằng từ khóa. Python chỉ dùng thư viện chuẩn.

## Lệnh

Đọc nhánh báo cáo liên quan trước khi dịch:

```powershell
python .agents/skills/translate/scripts/update_reports.py --inspect "StellaSora_TaiNguyen_EN_JP_CN_Text_20261101_r03/01_CotTruyen/01_Chinh/Chuong_STm02/STm02_05/STm02_05_Merge.txt"
```

Sau mỗi lần lưu tiến độ Merge đã kiểm tra, đọc lại Merge, tính SHA-256 nguyên
byte và chuẩn bị JSON ở thư mục tạm. Kiểm tra rồi cập nhật cả hai HTML:

```powershell
python .agents/skills/translate/scripts/update_reports.py --input "<JSON tạm>" --dry-run
python .agents/skills/translate/scripts/update_reports.py --input "<JSON tạm>"
```

`--dry-run` không ghi file. `--project-root <đường dẫn>` chỉ định gốc SS khi cần;
mặc định xác định từ vị trí skill. `--init` tạo hai báo cáo rỗng nếu cả hai chưa
có, hoặc kiểm tra và giữ nguyên cặp đã có; không xóa lịch sử. Kiểm thử:

```powershell
python .agents/skills/translate/scripts/test_update_reports.py
```

## Hợp đồng JSON đầu vào

Ví dụ minh họa, không phải dữ liệu game thật:

```json
{
  "files": [{
    "merge_path": "StellaSora_TaiNguyen_EN_JP_CN_Text_20261101_r03/01_CotTruyen/01_Chinh/Chuong_STm02/STm02_05/STm02_05_Merge.txt",
    "merge_sha256": "<SHA-256 file Merge sau khi lưu, gồm BOM và CRLF>",
    "blocks": [{
      "block_order": 1,
      "kind": "Lời thoại",
      "speaker": "Sylar",
      "source_refs": {},
      "source": {"CN": "她到了。", "JP": "彼女が来た。", "EN": "He arrived."},
      "text_vi": "Anh ấy đến rồi.",
      "conflicts": [{
        "title": "Khác người được nhắc đến",
        "languages": ["EN", "JP", "CN"],
        "detail": "EN dùng he; JP/CN dùng đại từ nữ.",
        "handling": "VI theo đại từ EN trong ngữ cảnh này.",
        "basis": "EN; chưa có quyết định hiệu đính khác của người dùng."
      }],
      "references": []
    }]
  }]
}
```

- `merge_path`: đường dẫn từ gốc SS, dùng `/`, bắt đầu bằng tên thư mục tài
  nguyên, kết thúc `_Merge.txt`. Không chỉ dùng basename để định vị.
- `merge_sha256`: hash toàn bộ byte Merge **sau khi lưu**; file đã đổi sẽ bị từ
  chối. Không đổi hash để bỏ qua việc đọc/rà lại bản mới.
- `blocks`: **mọi khối vừa rà**, kể cả không có phát hiện. Với khối đó vẫn gửi
  đầy đủ các trường và hai mảng `conflicts: []`, `references: []`. Không gửi
  khối chưa rà hoặc ngoài phạm vi.
- `source`: đúng ba khóa EN/JP/CN, nội dung chính xác đang lưu trong Merge,
  gồm thẻ, placeholder và xuống dòng thực tế. Không lấy câu thô khác từ nguồn
  khi Merge đã mở rộng token. Ghi JSON bằng thư viện để escape đúng.
- `text_vi`: đúng bản VI đã lưu; có thể là `""` nếu đã đối chiếu nhưng chưa thể
  dịch. Helper kiểm tra khối thực tế chưa có VI, cho phép báo nguồn đang vướng;
  ghi phạm vi đã rà không có nghĩa xác nhận đã dịch xong.
- `kind`: loại trong header story; `speaker`: tên/nhãn hiển thị, giữ tên che giấu,
  có thể rỗng nếu story không có người nói. Với UI tĩnh, **cả hai bắt buộc `""`**;
  không lấy mã nguồn làm người nói hoặc tự đặt loại nội dung.
- Helper nhận diện header story `[Tên...] (Loại)` và UI tĩnh `[Mã]`. `ui_type`
  (`story`/`static`) và `source_code` có thể bỏ qua trong đầu vào; nếu cung cấp
  phải khớp cấu trúc/mã nguyên gốc. UI tĩnh được lưu và hiển thị bằng mã header.
  Báo cáo story đã có vẫn đọc/cập nhật được, không cần xóa hoặc tạo lại.
- `source_refs`: tùy chọn, mặc định `{}`; các khóa EN/JP/CN có giá trị là mã
  nguồn đã xác minh. Không tự đặt ID. Nên cung cấp nếu có command đáng tin để
  nhận diện mục khi câu nguồn hoặc số khối đổi. Helper không thay việc xác minh
  mã với dữ liệu gốc của người dịch.
- Với UI tĩnh, `source_refs` có thể bỏ qua hoặc `{}` để helper lấy từ header:
  mã chung ánh xạ cả EN/JP/CN; header `[EN: mã_EN/JP: mã_JP/CN: mã_CN]` giữ
  đủ ba mã. Nếu gửi `source_refs`, phải đúng đủ ba ngôn ngữ và khớp header.
  Không tách mọi dấu `/`; các dấu `/` nằm trong mã được giữ nguyên.
  Ví dụ khối UI tĩnh đã dịch (hai mảng phát hiện dùng cùng hợp đồng story):

  ```json
  {
    "block_order": 1,
    "kind": "",
    "speaker": "",
    "source": {"CN": "魔王之路 I", "JP": "魔王の道Ⅰ", "EN": "Becoming a Real Boss Ⅰ"},
    "text_vi": "Trở thành Boss thực thụ Ⅰ",
    "conflicts": [],
    "references": []
  }
  ```

- Mỗi conflict bắt buộc có `title`, `languages`, `detail`, `handling`, `basis`.
  Nêu cụ thể khác biệt và căn cứ, kể cả khi theo hiệu đính người dùng thay EN.
- Mỗi phát hiện có thể mang `id` ổn định trong khối để nhận diện khi đổi tiêu đề;
  nếu không có, helper dùng tiêu đề và tập ngôn ngữ. Không gửi hai phát hiện cùng
  định danh. Chỉ gửi phát hiện còn phù hợp; helper giữ từng phát hiện bị bỏ bằng
  trạng thái `absent` và ngữ cảnh cũ, kể cả khi khối vẫn còn phát hiện khác.
  `status` và `previous_context` do helper quản lý, không truyền từ đầu vào.
- Mỗi reference có `title`, `languages`, `detail`, `handling`, `confidence`
  (`verified` hoặc `suspected`), `evidence` là mảng không rỗng. Mỗi bằng chứng
  có `label`, URL tùy chọn. Nguồn nằm trong câu thì URL rỗng, label giải thích
  cơ chế; nghi vấn thì ghi lý do nghi, không nâng thành đã xác minh. Ví dụ:

  ```json
  {
    "title": "Hai nghĩa của blast",
    "languages": ["EN"],
    "detail": "Câu chúc vui xuất hiện đúng lúc nhân vật ném bom.",
    "handling": "Giữ liên hệ giữa vui vẻ và vụ nổ, không thêm lời tục vượt nguồn.",
    "confidence": "verified",
    "evidence": [{"label": "Have a blast! cùng hành động ném bom trong cảnh.", "url": ""}]
  }
  ```

## Cập nhật và trạng thái

Helper kiểm tra cặp HTML/checkpoint, hash Merge, nguồn/VI từng khối gồm nội dung
nhiều dòng, rồi cập nhật từng file theo nguyên cây thư mục nguồn. Mỗi khối có
một mục cho mỗi báo cáo, chứa nhiều phát hiện; dịch lại cập nhật mục cũ.

Các nhánh/file/khối ngoài phạm vi được giữ nguyên. Trong file vừa cập nhật,
mục cũ chỉ đổi số khối khi trích đoạn/header khớp duy nhất hoặc có mã nguồn
đáng tin trong đầu vào. Mục mơ hồ được giữ riêng dưới “Vị trí cũ”, không gán bừa.
Thay đổi ngoài phạm vi khiến khối đó mất xác nhận phạm vi rà hiện hành.

- `active`: còn phát hiện.
- `clear`: đã rà, chưa có phát hiện; vẫn lưu một mục cho khối này.
- `absent`: không còn phù hợp trong lần rà hiện tại; giữ chi tiết cũ để đọc.
- `needs_review`: nguồn, VI hoặc vị trí cần đối chiếu; không phải trạng thái
  người dùng đã/chưa duyệt. HTML không có chức năng sửa hoặc duyệt.

Chỉ ghi từ những lần dịch mới; không tự rà ngược. HTML phản ánh lần rà đã lưu
gần nhất, không theo dõi file nền hoặc kích hoạt dịch khi mở trình duyệt.

## Lỗi và phục hồi

Không dịch thêm nếu báo cáo chưa lưu xong. Giữ Merge đã lưu, JSON đầu vào tạm
và mọi đường dẫn phục hồi được helper báo; không rollback Merge vì lỗi báo cáo.

- Snapshot không khớp: đọc Merge mới, bảo toàn hiệu đính, rà lại và lập JSON mới.
- Báo cáo hỏng/thiếu một file/checkpoint lệch: không xóa để khởi tạo lại. Kiểm
  tra bản `.pending` hoặc bản xác thực, chỉ khôi phục cặp cùng checkpoint sau
  khi xác minh dữ liệu và phiên bản Merge.
- Helper dùng khóa tạm để tránh hai lượt ghi đè nhau. Chờ lượt đang chạy;
  không tự xóa khóa của tiến trình còn hoạt động.
- Lỗi ghi: helper cố khôi phục cặp cũ và giữ cặp đề xuất phục hồi. Nếu không
  khôi phục được, báo chính xác phần dở/đường dẫn; không tuyên bố đã cập nhật đủ.

Chỉ hai HTML là dữ liệu báo cáo lâu dài. Khóa và `.pending` chỉ phục vụ ghi an
toàn/phục hồi, không phải báo cáo hoặc kho dữ liệu thứ ba.
