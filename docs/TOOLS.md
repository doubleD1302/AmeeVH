# Hướng dẫn công cụ chạy thật

Chạy các lệnh từ `StellaSora_VietHoa`. Có thể thay `python tools/localize.py` bằng `.\tools\run.ps1` nếu PowerShell cho phép script. Không cần đổi ExecutionPolicy.

Output của CLI chỉ được đặt dưới `work/`, `reports/`, `staging/`, tương đối từ project root; output đã tồn tại sẽ bị từ chối. Tăng run/revision (`r02`, `r03`) để giữ lịch sử. Input của các lệnh được tính từ working directory hiện tại.

## Khảo sát và nguồn

```powershell
python tools/localize.py doctor
python tools/localize.py inventory --out reports/inventory_r02.json
python tools/localize.py extract-srt --out work/source/subtitles_r02.jsonl
python tools/localize.py diff-sources --old work/source/subtitles_persistent_20261019.jsonl --new work/source/subtitles_r02.jsonl --out reports/source_diff_r02.json
```

`inventory` duyệt metadata các file dưới StellaSora_Data/Persistent_Store/Patch_Store và file root, bỏ junction/symlink. Chỉ hash nhóm tài nguyên liên quan đã chọn, không hash mọi video/audio. Các file chưa có SHA256 chỉ có bằng chứng size/mtime, không phải đối chiếu byte.

`extract-srt` mặc định chọn `Persistent_Store/Videos` tường minh. Chọn bản cài sẵn bằng `--source-dir StellaSora_Data/StreamingAssets/InstallResource`; ID sẽ có namespace khác. Chỉ hỗ trợ UTF-8 có/không BOM, SRT dạng số + timestamp + text, LF/CRLF. Dữ liệu không hiểu được phải lỗi, không bỏ dòng.

## Tạo và dịch batch

Batch SRT001–004 đã được tạo trong `work/batches`. Ví dụ tạo lại một revision mới:

```powershell
python tools/localize.py batch --catalog work/source/subtitles_persistent_20261019.jsonl --batch-id SRT001-r02 --source-file Persistent_Store/Videos/Prologue-Prologue_P4_JPVA_FP_EN.srt --limit 200 --out work/batches/SRT001_JPVA_r02.json
```

Điền `translator`, `text_vi`, `notes`; không thay `source`. Với catalog lớn có thể dùng `--offset 0 --limit 40`; không dùng offset để chia cắt một file SRT rồi đòi build cả file. Giữ cảnh liền mạch, ghi tiến độ theo ID.

## Audit, review, ghi snapshot

```powershell
python tools/localize.py audit --catalog work/source/subtitles_persistent_20261019.jsonl --proposal work/batches/SRT001_JPVA.json --out reports/SRT001_audit_r01.json
python tools/localize.py review-template --catalog work/source/subtitles_persistent_20261019.jsonl --proposal work/batches/SRT001_JPVA.json --out work/reviews/SRT001_review_r01.json
```

Nếu audit exit 2: đọc `errors` và `rows`, sửa đúng nguyên nhân rồi chạy output revision mới. Warning chưa được reviewer giải thích/ack sẽ chặn build. Template review chỉ tạo được sau audit đạt.

Reviewer làm theo `prompts/REVIEW_AGENT.txt`. Sau khi có review thật:

```powershell
python tools/localize.py merge --catalog work/source/subtitles_persistent_20261019.jsonl --proposal work/batches/SRT001_JPVA.json --review work/reviews/SRT001_review_r01.json --out work/merged/SRT001_r01.json
python tools/localize.py build-srt --catalog work/source/subtitles_persistent_20261019.jsonl --proposal work/batches/SRT001_JPVA.json --review work/reviews/SRT001_review_r01.json --out staging/SRT001_r01
```

Candidate nằm dưới `staging/SRT001_r01/files/` với đường dẫn game được giữ để kiểm tra. `manifest.json` đi kèm có hash gốc/hash candidate và phạm vi kiểm tra. Lệnh này không cài, không sửa checksum live và không xác minh nguồn nào game thực sự đọc.

## Kiểm thử

```powershell
python -m unittest discover -s tests -v
python tools/verify_setup.py --baseline reports/inventory_initial_20261019.json --out reports/preparation_verification_r02.json
```

Tests dùng dữ liệu **synthetic**, gồm thành công và trường hợp phải từ chối. Quyết định approved trong fixture chỉ dùng thử gate; tuyệt đối không lấy nó làm reviewer cho dữ liệu game.

`verify_setup.py` kiểm thêm toàn chuỗi CLI trên fixture tạm, catalog/batch coverage, no-op của 8 bản SRT và so inventory với baseline. Script này dành cho bộ khởi tạo trước khi nguồn/batch được thay theo chủ đích; khi đổi catalog hoặc thêm revision batch cần cập nhật scope kiểm, không coi khác biệt có chủ đích là lỗi game. Report ghi rõ self-check, không phải QA độc lập.

Mã thoát: 0 = thao tác kỹ thuật được yêu cầu đạt; 2 = lỗi input/guard/audit. `doctor` chỉ báo khả năng tool và môi trường, không phải kết luận runtime.
