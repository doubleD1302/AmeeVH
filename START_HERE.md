# Bắt đầu Việt hóa Stella Sora

Bộ dự án này dành cho agent tiếp tục làm việc ngay từ dữ liệu cục bộ, không cần tạo lại khung quy trình.

## Đã có gì

| Thành phần | Vị trí | Công dụng |
|---|---|---|
| Chỉ thị chung | `AGENTS.md` | Phạm vi, cách tiếp tục, bằng chứng và giới hạn |
| Prompt dán cho agent | `prompts/START_AGENT.txt` | Bắt đầu dịch và nghiên cứu định dạng |
| Prompt review/tiếp tục | `prompts/REVIEW_AGENT.txt`, `prompts/RESUME_AGENT.txt` | Review độc lập, phục hồi sau gián đoạn |
| Vai trò | `agents/` | Điều phối, nghiên cứu format, dịch, QA, font/runtime |
| Công cụ | `tools/localize.py`, `tools/run.ps1` | Kiểm kê, trích SRT, chia đợt, audit, merge, staging, diff |
| Dữ liệu nguồn thật | `work/source/subtitles_persistent_20261019.jsonl` | 51 cue từ 4 tệp EN; giữ timestamp và biến thể giọng |
| Batch bắt đầu | `work/batches/SRT001_JPVA.json` | Proposal trống của phụ đề Prologue JPVA |
| Nguyên tắc tiếng Việt | `docs/STYLE_GUIDE_VI.md`, `config/glossary.json` | Văn phong, thuật ngữ và nội dung kỹ thuật |
| Lộ trình | `docs/ROADMAP.md` | Từ discovery đến bản thử và bảo trì |
| Trạng thái | `STATUS.json`, `CHECKPOINT.json` | Các gate và điểm tiếp tục hiện tại |
| Kiểm chứng | `reports/` | Inventory, kết quả tool và kiểm tra bảo toàn dữ liệu |

Báo cáo bàn giao: [BAO_CAO_CHUAN_BI_20261019.md](reports/BAO_CAO_CHUAN_BI_20261019.md). Kiểm tra cuối đạt 26/26 tests, 9/9 bước CLI synthetic và no-op byte-identical trên 8 bản SRT thực. Đây là tự kiểm công cụ, chưa phải review bản dịch hay QA gameplay.

## Dùng ngay

Mở workspace tại `C:\YostarGames\StellaSora_EN` hoặc thư mục dự án con, rồi gửi nguyên văn `prompts/START_AGENT.txt` cho agent. Nếu agent không tự đọc `AGENTS.md`, yêu cầu nó đọc file này trước. Đây là tài liệu và CLI, không phải dịch vụ tự chạy khi máy bật.

Lệnh dưới đây chạy trong PowerShell tại thư mục dự án:

```powershell
Set-Location 'C:\YostarGames\StellaSora_EN\StellaSora_VietHoa'
python tools/localize.py doctor
python -m unittest discover -s tests -v
```

Python 3.10 trở lên; phần lõi không cần cài pip, API key hoặc dịch vụ dịch. Agent dùng năng lực dịch của chính nó để điền proposal. Không có script tự gọi API trả phí.

Ví dụ sau khi agent đã dịch `SRT001_JPVA.json`:

```powershell
python tools/localize.py audit --catalog work/source/subtitles_persistent_20261019.jsonl --proposal work/batches/SRT001_JPVA.json --out reports/SRT001_audit_r01.json
python tools/localize.py review-template --catalog work/source/subtitles_persistent_20261019.jsonl --proposal work/batches/SRT001_JPVA.json --out work/reviews/SRT001_review_r01.json
```

Reviewer điền quyết định thật, sau đó mới chạy merge/build theo `docs/TOOLS.md`. Chạy audit ngay trên proposal trống sẽ **thất bại có chủ đích**; đó là kiểm tra ngăn xuất bản dịch rỗng.

## Phần còn phải làm

- Dịch và review 51 cue; chưa có câu nào được dịch/approved trong bộ khởi tạo.
- Viết adapter `.arcx` cho bảng/script, xác minh catalog text của toàn game. Tổng số chuỗi toàn game còn chưa biết.
- Xác minh loader, font có dấu và ảnh chứa chữ; thử runtime khi có candidate đủ điều kiện.

Không cần cài UnityPy để chạy phần đã có. Công cụ nghiên cứu Unity chỉ được thêm vào môi trường riêng sau khi kiểm tra tương thích; tài liệu tham khảo tại `docs/REFERENCES.md`.
