# Bàn giao bộ chuẩn bị Việt hóa — 19/10/2026

## Kết quả

Đã tạo bộ dự án `StellaSora_VietHoa` trong thư mục cài game, có root `AGENTS.md` để điều hướng. Agent có thể đọc `START_HERE.md` và dùng ngay `prompts/START_AGENT.txt` để bắt đầu dịch pilot và nghiên cứu định dạng tài nguyên.

Gồm: chỉ thị chung, sáu vai trò agent, ba prompt giao việc/tiếp tục/review, tài liệu khảo sát và lộ trình, quy chuẩn VI, hợp đồng dữ liệu, hướng dẫn tool, kế hoạch format/font/runtime/rollback, glossary đề xuất, mẫu issue/ma trận runtime/corpus glyph, CLI Python + wrapper PowerShell, tests, STATUS và CHECKPOINT.

## Dữ liệu thật đã chuẩn bị

| Batch | Nguồn EN | Cue | Đã dịch/approved |
|---|---|---:|---:|
| SRT001_JPVA | Prologue P4 JPVA | 14 | 0 |
| SRT002_CNVA | Prologue P4 CNVA | 14 | 0 |
| SRT003_CH04ED | CH04ED | 10 | 0 |
| SRT004_CH06ED | CH06ED | 13 | 0 |
| Tổng | 4 file | 51 | 0 |

Catalog: `work/source/subtitles_persistent_20261019.jsonl`.

SHA256: `8fa06cc0a649918eae0aa7de7e79aab4a71fd5f7f502ee136a3a877c8cb62440`.

Nguồn được chọn tường minh từ Persistent_Store; chưa xác minh ưu tiên loader. Hai bản của mỗi SRT ở Persistent_Store và InstallResource khớp hash. CNVA cue 3 có `dffd` ở cả hai nguồn; catalog giữ nguyên và gắn issue để review.

## Công cụ đã chạy

Lệnh xác minh tổng:

```powershell
python tools/verify_setup.py --baseline reports/inventory_initial_20261019.json --out reports/preparation_verification_20261019.json
```

- 26/26 unit/integration tests đạt. Bao gồm token, số/dấu, Unicode NFC, tag/printf order, nguồn đổi, review hết hiệu lực, glossary đổi, tự review, warning chưa giải quyết, path traversal, output tồn tại, partial SRT và staging/readback.
- 9/9 bước CLI synthetic trả đúng mã: extract → batch → chặn proposal rỗng → audit → pending review template → chặn merge khi chưa review → merge fixture → build/readback fixture → diff nguồn.
- 8/8 SRT thực (4 bản cài sẵn + 4 bản persistent) no-op roundtrip khớp byte, gồm BOM/newline/timestamp.
- 4 batch bao phủ đúng 51 ID, không trùng/thiếu; toàn bộ JSON đã parse được, liên kết Markdown nội bộ đã kiểm.
- Trước/sau: 16.207 file có metadata được đối chiếu; 23 file trọng tâm có SHA256 được đối chiếu. Không phát hiện added/removed/changed trong phạm vi inventory. Đây không phải hash toàn bộ byte của mọi file game.

Evidence máy đọc: `preparation_verification_20261019.json`, inventory đầu và `preparation_verification_20261019_inventory.json`. Report có lệnh, mã thoát, log tests và hash nguồn/batch. Các source/approval trong test là synthetic và chỉ tồn tại trong thư mục tạm được dọn sau kiểm tra; không có review giả cho text thật.

## Giới hạn đúng của bàn giao

- Đây là **tự kiểm cùng phiên**, không có reviewer/subagent QA độc lập trong lượt chuẩn bị.
- Bảng/script `.arcx` chưa được giải mã/đóng gói; tổng số text toàn game chưa biết. Có magic/header và nhiệm vụ nghiên cứu cụ thể, không có stub báo thành công.
- Font/Unity asset adapter, loader precedence và installer live chưa triển khai/xác minh.
- Chưa dịch/duyệt câu game nào; chưa có candidate game thực, chưa cài patch, chưa kiểm runtime/gameplay hoặc phát hành.
- Phiên bản đọc được: client/launcher 1.13.0; game resource 1.16.1 / RES_VER 2610041900; Unity header 2022.3.62f2. Không coi chúng là một số phiên bản duy nhất.

## Bước tiếp theo

Gửi `prompts/START_AGENT.txt` cho agent trong workspace hiện tại. Agent xác nhận hash nguồn, dịch SRT001_JPVA, chạy audit và giao reviewer độc lập. Khi một batch chờ review, tiếp tục batch khác hoặc nghiên cứu `.arcx` theo tài liệu. Chỉ tạo staging khi có review thật; bước cài/runtime là giai đoạn riêng sau khi đã có cơ sở kỹ thuật.
