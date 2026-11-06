---
name: workflow
description: Điều phối merge → cập nhật thuật ngữ → dịch VI trong project SS bằng merger, term-controller và translator; cho merger chuẩn bị trước đúng một bộ khi translator đang dịch bộ hiện tại, lưu hàng đợi/checkpoint để tiếp tục. Dùng khi người dùng yêu cầu chạy hoặc tiếp tục workflow cho phạm vi nguồn xác định; yêu cầu chỉ cấu hình không cho phép chạy dữ liệu thật.
---

# Workflow

Agent chính điều phối và kiểm chứng; helper quản lý trạng thái/chứng cứ, không gọi
mô hình hoặc dịch. Đọc `AGENTS.md` và [CLI/checkpoint](references/protocol.md) trước
khi chạy. Không có bước inspect riêng, không gọi merger hai lượt cho cùng bộ.

## Phạm vi và khởi động

- Chỉ enqueue folder/bộ nguồn được giao; `--recursive` chỉ khi được giao cả cây.
  Yêu cầu tiếp tục dùng queue đã lưu, không lấy tab IDE hoặc quét toàn project.
- Yêu cầu workflow cho phép nối ba skill và giao ba sub-agent trong phạm vi ấy.
  Không push Sheets, commit hoặc push Git. Lệnh merge/dịch/term riêng vẫn theo skill
  tương ứng; yêu cầu chỉ tạo/cấu hình workflow không tự chạy dữ liệu thật.
- Dùng helper `status`; chưa có thì `init`, không reset hoặc ghi tay state để chữa
  lỗi. Thêm scope bằng `enqueue`, rồi `start`. Mặc định tối đa 10 bộ hoàn tất,
  60 phút, 2 lần thử/bước. Không giao bước mới khi hết giới hạn; để worker đang chạy
  lưu an toàn, ghi checkpoint rồi dừng.
- Chỉ một coordinator. `start --recover` chỉ sau khi xác minh coordinator/worker
  cũ đã dừng. Với state schema 1, dừng run cũ và xác minh không còn claim trước khi
  chạy lệnh `migrate` riêng; `start` hoặc ghi checkpoint không tự chuyển schema.
  Helper giữ bằng chứng cũ trong `legacy_checkpoints`, không coi inspect hoặc
  terms-before-merge là merge hoàn tất; giữ nguyên dữ liệu thật và hiệu đính.

## Mỗi bộ nguồn

1. **merge — merger:** vào việc hợp nhất ngay trong một lượt. Kiểm tra đủ/đúng ba
   nguồn, tự phân loại UI, xác minh khóa/trường, đọc glossary và ánh xạ tên/token
   là phần của lượt merge này. Không bỏ các kiểm tra chỉ vì bỏ inspect. Ghi/đọc
   lại Merge cạnh bộ ba, giữ VI/hiệu đính, trả `ui_type`, `term_proposals` và
   `snapshot_path` theo hợp đồng. Không ghi glossary, không gọi term-controller
   trực tiếp, không đợi cập nhật term để quay lại ghi Merge. Snapshot không cập
   nhật HTML và không xác nhận đã rà xung đột/reference.
2. **terms — term-controller, khi có đề xuất:** parent kiểm chứng và thông báo
   EN/JP/CN, vị trí/ngữ cảnh rồi giao skill [update-term](../update-term/SKILL.md),
   không chờ duyệt lại. Chỉ chạy khi không merger, translator hoặc verify nào
   đang hoạt động. Đọc CSV mới nhất, tự dịch target term mới đủ căn cứ, giữ target
   đã chốt, đồng bộ ánh xạ; trả added/existing/unresolved từng ứng viên. Nhóm chưa
   đủ căn cứ chỉ báo riêng. Không sửa Merge. Không có đề xuất thì bỏ qua bước này.
3. **translate — translator:** tiếp nhận trực tiếp sau terms (hoặc merge nếu
   không có đề xuất), đọc lại glossary mới, Merge và nhánh báo cáo. Theo skill
   [translate](../translate/SKILL.md), dịch/đồng bộ VI và tên VI, giữ nguồn, mã,
   số khối, hiệu đính; cập nhật cả hai HTML sau mỗi lần lưu tiến độ đã kiểm tra.
4. **verify — parent:** đọc lại bản lưu, đối chiếu nguồn/glossary/snapshot; kiểm
   tra số khối, UI, tên, token, VI, hiệu đính, BOM/CRLF và cả hai báo cáo. Gọi
   `complete` cho helper kiểm chứng phiên bản/coverage/nội dung. Chỉ khi thành
   công mới đánh dấu done và mở quyền xử lý term của bộ kế tiếp.

Tham chiếu skill [merge](../merge/SKILL.md) cho mọi kiểm tra/nội dung merge.
Lời worker nói “xong” không thay bằng chứng file thật hoặc kiểm tra ngữ nghĩa.
Không gọi lại merger chỉ vì term-controller vừa thêm target VI; translator đọc
CSV mới để áp dụng target/ánh xạ VI. Nếu lỗi thật cần sửa, dùng retry/repair có
kiểm soát và bảo toàn phần hiện tại, không tạo lượt merge thứ hai mặc định.

## Chồng lấp đúng một bộ

- Khi A đã xong terms và bắt đầu translate, gọi `claim` tiếp để giao merger B.
  Chỉ được một merger và một translator đồng thời, ghi hai Merge khác nhau.
- Nếu B merge xong trước A, parent lưu checkpoint merge B và giữ đề xuất B trong
  queue. Merger dừng chờ; chưa giao term-controller, chưa merge C. Translator A
  tiếp tục với glossary ổn định.
- A dịch xong phải được parent kiểm tra và lưu verify/checkpoint/báo cáo thành
  công. Chờ merger B kết thúc nếu cần; sau đó mới giao terms B. Term-controller
  là writer glossary duy nhất, chạy độc quyền, không song song merger/translator/
  verify. Sau terms B, bắt đầu translator B rồi mới giao merger C.
- Nếu B không có term mới, vẫn chờ A verify xong mới dịch B và merge C. Giới hạn
  một bộ chuẩn bị trước áp dụng cả trường hợp bỏ qua terms.
- Hai HTML chỉ một translator ghi. Merger không đọc/ghi báo cáo đang được dịch;
  parent verify đọc chúng sau translator đã kết thúc. Agent chính chỉ ghi state.
- Lặp `claim` tới khi helper trả `wait: true` hoặc `stop: true`; mỗi job/claim
  phải gắn đúng worker và receipt. Khi `wait`, đợi worker hiện hành có kết quả,
  checkpoint rồi claim tiếp; không coi là hết việc, không busy-poll hoặc lách
  barrier bằng tự giao stage. `stop` mới kết thúc vòng nhận việc.

## Cấu hình vai trò

Bàn giao chỉ gồm đường dẫn cấu hình vai trò/skill, claim/receipt, phạm vi và lưu ý riêng. Worker tự đọc hướng dẫn trong file; không chép lại developer_instructions hoặc nội dung skill vào tin giao việc. Lưu JSON claim đầy đủ vào TEMP, chỉ đưa tóm tắt và đường dẫn vào context điều phối.

Đọc cấu hình `.codex/agents/{role}.toml` hiện tại do claim trả về:

| Vai trò | Model | Effort | Quyền ghi |
|---|---|---|---|
| merger | gpt-6.1-sol | medium | Merge được giao |
| term-controller | gpt-6-luna | medium | glossary theo update-term |
| translator | gpt-6.1-sol | high | VI/tên VI trong Merge, hai HTML |

Dùng custom role nếu runtime hỗ trợ. Nếu chỉ có `spawn_agent`, truyền đúng model,
effort và yêu cầu worker đọc developer_instructions tại đường dẫn TOML cùng scope/skill/claim; dùng
`fork_turns: none` khi đặt override. Không âm thầm thay model hoặc dùng model
parent. Parent thực hiện verify, không spawn role thứ tư.

## Đồng bộ sau thay đổi glossary

- Với file đã dịch/verify, helper so định nghĩa đã lưu với glossary mới và tìm khối sử dụng mục thêm/sửa/xóa qua nguồn EN/JP/CN, tên và token. Claim chứa `review_scope.blocks` và `changes`. Dùng lệnh `review` trong protocol lấy các khối và phát hiện hiện hành; chỉ thêm ngữ cảnh liền kề khi cần, không đọc lại toàn file bằng mô hình.
- Translator chỉ rà các khối đó. Nếu VI đã đúng, giữ nguyên byte Merge và xác nhận; nếu cần sửa chỉ sửa VI/tên VI thuộc phạm vi. Receipt ghi đủ `reviewed_blocks`. Parent vẫn reviewer nhưng chỉ đọc phần đồng bộ và ngữ cảnh liên quan trong lượt này; dịch mới giữ quy trình rà toàn file.
- Cập nhật hai HTML cho phần vừa rà, giữ dữ liệu/phát hiện ngoài phạm vi. Helper vẫn kiểm tra cấu trúc, nguồn, hash và coverage toàn file bằng mã, từ chối sửa khối ngoài phạm vi. Định nghĩa chỉ xuất hiện trong dữ liệu kỹ thuật không tạo lượt rà bằng mô hình.
- Checkpoint cũ chỉ lấy baseline hiện tại khi fingerprint liên quan còn khớp. Nếu glossary đã khác và không có định nghĩa cũ, báo cần đối chiếu, không đoán phạm vi. Nguồn, ánh xạ nguồn hoặc hiệu đính ngoài phạm vi thay đổi vẫn theo quy trình kiểm tra đầy đủ hiện có.

## Lỗi, tiếp tục và dừng

- Thiếu/sai/lỗi một nguồn chặn cả bộ, giữ Merge cũ, không giao term. Tiếp tục bộ
  hợp lệ khác và báo file/ngôn ngữ/cảnh báo của bộ bị chặn.
- Nguồn đổi thì quay merge có kiểm soát. Glossary liên quan đổi hoặc Merge sửa
  thủ công phải đọc lại/đối chiếu hiện tại; không lấy bản tạm ghi đè hiệu đính.
  Không ép merge lại chỉ do target VI thay đổi. Term không liên quan không làm
  mọi job phải dịch lại; parent vẫn xét ngữ nghĩa ngoài phép dò chuỗi của helper.
- `fail` trong giới hạn; `--blocked` khi cần quyết định/bảo toàn chưa giải được.
  Chỉ `retry` sau giải quyết nguyên nhân, không reset để vượt giới hạn thử.
- Lỗi báo cáo dừng run ở needs_attention. Giữ VI/dữ liệu phục hồi; không giao
  terms hoặc dịch tiếp trước khi sửa báo cáo. Bộ đã merge trước vẫn ở checkpoint
  chờ; không tuyên bố done, không đổi hash snapshot cũ để lách kiểm tra.
- Trước `stop`, ngắt/đợi tất cả worker lưu an toàn; helper không ngắt mô hình.
  `--pause` chỉ khi người dùng yêu cầu. Gần hết ngữ cảnh/budget thì checkpoint và
  dừng có lý do, không hứa chạy nền sau phản hồi cuối.
- Kết thúc tóm tắt done/blocked/failed/pending, phần đang chờ và cách tiếp tục,
  liên kết hai báo cáo khi đã dịch và [state](../../../.ss-workflow/state.json).
  Không chèn báo cáo/điều phối vào Merge.

## Kiểm thử helper

Chỉ sửa mã và chạy bộ test khi cập nhật workflow/helper hoặc sửa lỗi. Mỗi lượt workflow thông thường chỉ gọi helper có sẵn và kiểm tra dữ liệu tác vụ; không viết script thay thế hoặc chạy lại bộ test phát triển.

`python .agents/skills/workflow/scripts/test_workflow_state.py`

Chỉ dùng project giả trong TEMP; không gọi model hoặc sửa dữ liệu game.
