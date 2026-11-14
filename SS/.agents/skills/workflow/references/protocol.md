# CLI và chứng cứ của workflow

Chạy từ gốc SS bằng Python 3.11+. Helper dùng thư viện chuẩn, không scheduler,
không tự spawn agent. Agent chính giữ vòng điều phối và quyền cấp việc.

## Lệnh

```powershell
python .agents/skills/workflow/scripts/workflow_state.py init
python .agents/skills/workflow/scripts/workflow_state.py status
python .agents/skills/workflow/scripts/workflow_state.py migrate
python .agents/skills/workflow/scripts/workflow_state.py enqueue "<folder nguồn>"
python .agents/skills/workflow/scripts/workflow_state.py start --max-items 10 --max-minutes 60 --max-attempts 2
python .agents/skills/workflow/scripts/workflow_state.py claim --run "<run>"
python .agents/skills/workflow/scripts/workflow_state.py review --job "<job>" --context 0
python .agents/skills/workflow/scripts/workflow_state.py complete --run "<run>" --job "<job>" --claim "<claim>" --receipt "<JSON tạm>"
python .agents/skills/workflow/scripts/workflow_state.py fail --run "<run>" --job "<job>" --claim "<claim>" --reason "<lỗi>"
python .agents/skills/workflow/scripts/workflow_state.py stop --run "<run>" --reason "<lý do>"
```

- `--project-root <gốc SS>` đứng trước lệnh; mặc định lấy gốc từ vị trí skill.
- Scope dùng `/`, bắt đầu bằng `StellaSora_TaiNguyen_EN_JP_CN_Text_20261101_r03/`.
  Có thể enqueue nhiều folder. `--recursive` chỉ khi được giao cả cây. Phát hiện
  hợp tên `_EN/_JP/_CN.txt`; thiếu một ngôn ngữ vẫn ghi queue để báo blocked.
- `init` không reset queue. `start` tiếp tục checkpoint, đối chiếu nguồn/glossary/
  Merge. `--recover` chỉ khi coordinator/worker cũ đã dừng; token cũ vô hiệu.
- `claim` trả job, run/claim token và cấu hình agent, hoặc `wait: true`, hoặc
  `stop: true`. Verify là parent, không spawn worker. Không cần lane flag.
- `wait` nghĩa còn việc nhưng đang có worker/barrier: chờ kết quả thật rồi đọc lại
  và complete/fail đúng claim. `stop` nghĩa hết việc hoặc hết giới hạn, đọc
  run.status/reason. Không gọi claim liên tục khi chưa có thay đổi.
- Mỗi claim nhận một job/stage. Có thể có claim translate A và merge B đồng thời.
  Không cấp terms khi bất kỳ merger/translator/verify còn hoạt động. Không cấp
  merge C khi B chưa bắt đầu translate. Giữ một bộ chuẩn bị trước tối đa.
- `fail --blocked` ghi vướng mắc cần quyết định. `fail --reports` dừng cả run;
  trước khi stop/recover phải thu hồi/ngắt hoặc đợi worker còn lại. Lỗi thường tối
  đa max-attempts ở cùng stage, sau đó failed, không tự reset số lần thử.
- `retry --job <id>` chỉ khi run đã dừng, job blocked/failed và nguyên nhân đã xử
  lý; quay merge, giữ game artifacts. `stop --pause` chỉ cho yêu cầu tạm dừng.

## Receipt

Ghi JSON bằng thư viện trong TEMP, không ghép Unicode/newline qua chuỗi shell.
Mỗi receipt cần summary có nghĩa và khớp claim/input hiện hành. Parent kiểm tra
file/diff thật trước complete, không dựa vào tên trường do worker tự khai.

### merge

```json
{
  "summary": "Đã hợp nhất, kiểm tra khối và bảo toàn hiệu đính VI",
  "ui_type": "static",
  "term_proposals": [{
    "EN": "Example Name", "JP": "", "CN": "",
    "context": "Tên vật phẩm được gọi và giải thích trong mục nguồn",
    "source_ref": "<đường dẫn nguồn và mã/command/khối đã xác minh>"
  }],
  "snapshot_path": "<đường dẫn tuyệt đối JSON tạm>"
}
```

ui_type là story/static. term_proposals chỉ chứa ứng viên đủ căn cứ và không
trùng nhau; không có thì `[]`. EN/JP/CN là chuỗi; chưa có bằng chứng JP/CN thì
để `""`, không tự dịch bù. Báo nhóm chưa đủ căn cứ riêng cho parent.

Snapshot theo `translate/references/reports.md`: files/merge_path/merge_sha256/
blocks, đúng một file được giao và đủ mọi khối. Mỗi khối có kind, speaker, source
CN/JP/EN, text_vi đúng phần đang có (hoặc `""`), conflicts/references là `[]`.
Không suy ranh giới ngôn ngữ từ số dòng; tra nguồn/khóa cho nội dung nhiều dòng.
UI story có tên/loại; UI tĩnh để kind/speaker rỗng, giữ nguyên mã. Merge phải được
lưu/đọc lại BOM/CRLF trước receipt. Snapshot chỉ là bằng chứng ghép nguồn, không
gọi helper báo cáo để ghi HTML. Không viết glossary ở stage này.

Một lượt merger bao gồm kiểm tra nguồn, UI, tra glossary, ghép/ghi Merge và rà
term. Không có receipt inspect. Sau checkpoint merge, parent giữ danh sách đề
xuất tới khi barrier cho phép terms; merger không tự giao term sớm hoặc chờ để
ghi Merge lần hai.

### terms

```json
{
  "summary": "Đã lưu term và đồng bộ ánh xạ theo update-term",
  "outcomes": [
    {"EN": "Example Name", "status": "added", "target": "Tên ví dụ"}
  ]
}
```

Mỗi đề xuất đúng một outcome: added/existing có target khớp CSV đã lưu, hoặc
unresolved kèm reason. Parent đối chiếu CSV: giữ target/ID đã chốt, chèn sau term
cuối, chỉ JP/CN có bằng chứng, đồng bộ ánh xạ. Terms chỉ sửa glossary, không sửa
Merge. Translator kế tiếp đọc CSV mới, không quay lại merger chỉ vì CSV đổi.

### translate và verify

Nếu claim có `review_scope.mode = glossary`, chỉ rà `review_scope.blocks` cùng `changes` (định nghĩa trước/sau, gồm thêm hoặc xóa). Lệnh đọc `review` trả `payload` chứa đúng các khối và hai mảng phát hiện hiện hành, `reviewed_blocks`, `changes`. Mặc định không có ngữ cảnh; `--context 1` trả riêng `context_blocks` khi cần, không mở rộng quyền sửa. Không đọc toàn Merge/HTML bằng mô hình hoặc tạo script trích xuất mới mỗi lượt.

Nếu VI đã đúng, không ghi lại Merge. Giữ phát hiện còn phù hợp và cập nhật hai HTML bằng payload của phần vừa rà. Khi VI đổi, đọc lại khối vừa lưu và lập payload/hash mới theo skill translate, không chỉ đổi hash để bỏ kiểm tra. Receipt translate thêm `reviewed_blocks: [<số khối được giao>]`, không thiếu, trùng hoặc thêm số. Helper xác minh toàn file bằng mã và từ chối thay đổi header/body ngoài phạm vi; parent verify phần vừa rà. Baseline chốt sau verify.

Schema 2 bổ sung định nghĩa glossary ở checkpoint và `review_scope`, không reset queue. State cũ có fingerprint còn khớp được bổ sung baseline ở lần chạy kế tiếp; thiếu baseline mà glossary đã đổi thì blocked cần đối chiếu, không tự xác nhận đồng bộ. Thay đổi nguồn/mã/ánh xạ nguồn vẫn theo nhánh kiểm tra hiện có.

```json
{"summary": "Đã đọc lại bản lưu, đối chiếu đầy đủ VI và hai báo cáo"}
```

Translator dùng helper riêng để cập nhật hai HTML sau mỗi save. Workflow helper
kiểm tra cùng phiên bản Merge, đủ inventory/coverage, header/nguồn/VI/fingerprint,
không vị trí unresolved, VI không trống. Verify không được sửa Merge. Parent
chịu trách nhiệm chất lượng nghĩa, tên/token/thuật ngữ và hiệu đính; helper không
thay việc đó. Sau complete translate vẫn phải complete verify trước khi terms
của bộ sau được cấp. Trong khi verify A, merger B có thể đang làm trên file khác;
terms B phải chờ cả verify A và merge B hoàn tất.

## State và phục hồi

Schema 2 có các stage merge/terms/translate/verify. Chuyển schema 1 bằng lệnh
`migrate` riêng sau khi parent đã dừng coordinator/worker cũ, stop run và xác minh
không còn claim. `start` hoặc ghi checkpoint không tự chuyển schema; schema 2 đã
có thì `migrate` là no-op. Helper giữ bằng chứng cũ trong `legacy_checkpoints`;
inspect cũ không còn là stage nhận việc, inspect hoặc terms-before-merge không
được coi là merge hoàn tất. Chỉ giữ checkpoint có đủ bằng chứng cho pipeline
mới, không đánh done từ dữ liệu cũ thiếu bằng chứng. Nguồn/VI/glossary/HTML không
bị sửa bởi việc chuyển schema.

`.ss-workflow/state.json` giữ queue, đường dẫn tương đối, token, hash, checkpoint,
đề xuất chờ, lỗi/lịch sử; không chứa bản sao toàn nội dung game/báo cáo.
state.backup.json là state trước lần lưu gần nhất, `.pending` có thể còn khi ghi
lỗi. state.lock dùng khóa OS tự nhả khi tiến trình chết; file còn không có nghĩa
còn khóa. State hỏng phải dừng và đối chiếu backup/pending/file thật, không tự
reset hoặc lấy backup cũ làm chứng cứ job hiện tại đã done.

Ghi state qua khóa ngắn, kiểm tra phiên bản, file tạm/thay thế, đọc lại; UTF-8
BOM/CRLF. Trạng thái job pending/running/done/blocked/failed; run running/completed/
finished_with_issues/limited/stopped/paused/needs_attention. Done vẫn được kiểm
lại khi tiếp tục, không là cờ bỏ qua vĩnh viễn. Nguồn lỗi được sửa có thể trở về
merge; lỗi quyết định/hết số lần thử cần retry sau khi đã giải quyết nguyên nhân.

Helper kiểm marker lỗi nguồn đã biết, ngôn ngữ khai báo và glossary liên quan
bằng ID/từ nguồn. Worker vẫn xác minh chức năng trường, quan hệ khóa, cảnh báo
khác và ngữ nghĩa, không bỏ validation chỉ vì helper cấp claim.
