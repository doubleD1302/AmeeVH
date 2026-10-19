# Hợp đồng dữ liệu v1

Tất cả JSON/JSONL UTF-8; text VI NFC. Catalog một record mỗi dòng. Không gộp hai ID chỉ vì trùng text; context/variant có thể khác.

| Trường catalog | Ý nghĩa |
|---|---|
| `id` | Định danh ổn định có namespace tài nguyên + khóa gốc |
| `source_text` | Text nguồn chính xác; chỉ chuẩn hóa CRLF body thành LF trong adapter SRT |
| `source_sha256` | SHA256 của UTF-8 source_text, không chứa BOM |
| `source_path` | Đường dẫn tương đối từ game root, không tuyệt đối/traversal/junction |
| `source_file_sha256` | SHA256 toàn byte file gốc, ràng buộc đúng revision |
| `locale`, `category` | `en`, `subtitle` hiện tại; thêm domain khi có bằng chứng |
| `locator` | Adapter + khóa/cue + timestamp hoặc table/field/entry key thực |
| `context` | Người nói, cảnh, trước/sau, biến thể, quan hệ reference; unknown phải ghi rõ |
| `source_issues` | Lỗi nguồn cần reviewer quyết định, không âm thầm sửa |

Proposal có `schema=1`, `kind=translation_proposal`, `batch_id`, hash nguyên file catalog, `translator`, `entries`. Mỗi entry giữ nguyên `id`, `source_sha256`, `source` (bản sao record catalog); chỉ điền `text_vi`, `notes`. `batch` là bộ tạo đề bài, không phải bộ dịch.

Audit kiểm cấu trúc, hash, token, số/dấu, newline, NFC, glossary approved và vài cảnh báo độ dài/CJK/nguồn không đổi. Nó không biết ngữ nghĩa, tính cách, loader, checksum game hay glyph atlas. Regex mặc định không bao phủ mọi formatter; printf có space flag, ICU/plural/conditional và cú pháp tùy biến cần parser riêng khi phát hiện.

Review gắn `catalog_sha256`, `proposal_sha256`, `glossary_sha256`, reviewer khác translator và `independent=true`; từng ID có `status=approved`, `rationale`, `evidence`, `warnings_ack`. Hash glossary dùng JSON canonical (sorted keys, UTF-8, không khoảng trắng), không phải hash byte file. `evidence` là đường dẫn transcript/ghi chú review có thật hoặc mô tả đối chiếu cụ thể; không điền tên file không tồn tại. Các trường khai báo không phải chữ ký số hay bằng chứng chống giả mạo.

`review-template` chỉ tạo pending. Mọi sửa đổi proposal làm review cũ hết hiệu lực. `merge` ghi snapshot **một batch đã review** vào file mới, không hợp nhất/ghi đè catalog toàn game. Chưa có công cụ tự gộp nhiều batch hoặc fuzzy translation memory; điều phối viên phải đối chiếu ID/hash và review khi bổ sung chúng.

`build-srt` nhận catalog + proposal + review, chạy lại guard, yêu cầu đủ mọi cue của từng file được chạm tới, kiểm hash gốc, giữ timing và đọc ngược candidate. Manifest ghi `installed=false`, `runtime=not_tested`.

`diff-sources` tách added/removed/text_changed/context_or_file_changed/unchanged. Ngay cả text giữ nguyên nhưng hash file/context đổi cũng phải rebase trên catalog mới; proposal/review cũ không dùng trực tiếp được.
