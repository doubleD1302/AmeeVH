---
name: update-sheet
description: Cập nhật Google Sheets database của project SS từ các file _Merge.txt đã dịch mới hoặc thay đổi, dùng metadata và hash để chỉ đọc/push file cần thiết. Dùng khi người dùng yêu cầu cập nhật hoặc đồng bộ sheet database, hay gọi $update-sheet; không tự chạy sau merge, dịch hoặc workflow.
---

# Update Sheet

Đồng bộ Merge hiện hành lên spreadsheet đã cấu hình trong
[README_SHEET_DATABASE.md](../../../README_SHEET_DATABASE.md). Giao tiếp bằng
tiếng Việt. Một yêu cầu cập nhật Sheet cho phép ghi nội dung trong phạm vi đó;
không tự nối merge, dịch hoặc sửa thuật ngữ. Khi người dùng chỉ yêu cầu tạo/cấu
hình skill hoặc hỏi về Sheet, không thực hiện push.

## Phạm vi và dữ liệu

- Nếu yêu cầu chỉ định file/folder, giữ đúng phạm vi. Nếu không, tìm Merge mới
  hoặc thay đổi trong các nhóm được hỗ trợ dưới thư mục tài nguyên hiện hành.
- Dùng schema 12 cột và quy tắc chia trang trong README. Khóa block là
  `(file_id, block_order)`; các file phải có `file_id` duy nhất giữa các nhóm.
- Chỉ push file có VI cho toàn bộ block và ranh giới CN/JP/EN/VI đã đối chiếu.
  Không tự dịch bù. File chưa đủ điều kiện được báo riêng; tiếp tục file hợp lệ.
- UI story để trống `source_refs_json`. UI tĩnh để trống `kind`, bốn cột
  `speaker_*`; `source_refs_json` là chuỗi JSON `{EN, JP, CN}` lấy mã từ header.
- Không sửa Merge, nguồn, glossary, báo cáo dịch hoặc các tab cũ. Không xóa dữ
  liệu remote khi file local biến mất, đổi tên hoặc chuyển nhóm; báo để đối soát.
- Skill hiện chỉ cập nhật nội dung, không quản lý phiên backend và không sửa,
  xóa `DB_Proposals`. Khi web đã hoạt động, dev phải khóa nhận đề xuất trước khi
  push và điều phối chuyển phiên theo README. Không coi khóa local của helper là
  khóa phiên web; không tuyên bố đã chuyển phiên. Nếu biết web đang nhận đề xuất
  mà chưa khóa, dừng ghi để làm rõ trạng thái đó; vẫn được chuẩn bị payload.

## Công cụ

Đọc skill Google Drive và Google Sheets đang có trong môi trường trước khi dùng
connector, cùng các reference chỉnh sửa/đọc live/batch update cần thiết. Ưu tiên
connector trực tiếp; không tự tạo OAuth hoặc đặt credential trong project.

Helper offline: `scripts/sheet_sync.py`, mặc định tự tìm gốc SS từ vị trí skill.
Hợp đồng CLI, chuẩn hóa kết quả connector và cấu trúc dữ liệu được mô tả tại
[references/sync.md](references/sync.md); đọc trước khi thực hiện đồng bộ.
Helper chỉ tạo JSON yêu cầu; agent gửi yêu cầu và đọc lại bằng connector.

## Quy trình

1. Nêu ngắn phạm vi sẽ cập nhật. Đọc metadata workbook để xác định trang, ID,
   grid và trạng thái quyền truy cập. Không dùng ID hàng đã lưu làm vị trí ghi.
2. `begin` lấy token lượt chạy, sau đó `scan --run TOKEN` lưu kết quả quan sát.
   Truyền `--scope` nếu có phạm vi. Chỉ xử lý danh sách `new` và `changed`;
   `metadata_only` không cần push, `unchanged` không cần đọc nội dung.
3. `prepare` từng ứng viên. Helper có thể dùng hai báo cáo dịch khớp hash hiện
   tại để lấy ranh giới ngôn ngữ. Nếu cần `--structured`, agent đọc đúng file
   thay đổi và đối chiếu nguồn/báo cáo liên quan, tạo bản xuất theo reference.
   Không suy ra đủ VI chỉ từ số dòng hoặc mọi dấu `/`. Không đổi báo cáo để vượt
   kiểm tra. Nếu chưa xác minh được thì giữ file đó, báo lý do.
4. Đọc header, danh sách khóa A:B toàn trang đích và đủ A:L của file được chọn,
   cùng table metadata. Chuẩn hóa thành remote snapshot mới cho mỗi file, vì
   lần ghi trước có thể đã dịch chuyển hàng. Kiểm tra file_id đích không nằm
   trong một trang dữ liệu khác trước khi thêm file mới.
5. `build` sinh plan và lưu trạng thái pending **trước khi gửi ghi**. Với trang
   mới chọn sheet ID chưa được dùng từ metadata; không tạo workbook khác.
   Không tự thay đổi plan JSON; payload lớn chia thành các lượt có kiểm soát,
   giữ pending và không công bố thành công trước khi toàn bộ file đã được kiểm.
6. Gửi `plan.requests` bằng `batch_update_spreadsheet`, đúng spreadsheet ID.
   Nếu không có request thì dữ liệu hiện đã khớp; vẫn cần readback và confirm.
   Không copy banding từ bảng cũ rồi addTable trên cùng dải.
7. Đọc lại khóa A:B, A:L của toàn file vừa ghi và table metadata. `confirm`
   đối chiếu đủ ô, vị trí khóa, phạm vi bảng, kiểu số và hash file local.
   Chỉ khi khớp mới lưu hash đã đồng bộ, manifest và receipt.
8. Xử lý tuần tự từng file. Lỗi connector không được retry mù bằng tọa độ cũ;
   đọc lại remote, dựng plan mới nếu nguyên nhân đã rõ. Nếu chưa rõ thì dừng
   file đó. Lưu phần đã xác nhận; tiếp tục các file độc lập nếu an toàn.
9. `finish` giải phóng token khi không còn request đang chạy. Cập nhật trạng
   thái đồng bộ trong README theo phạm vi thực sự đã xác nhận, phân biệt làm dở
   với hoàn tất; không suy ra đã hiệu đính xong. Báo số file mới/đổi/không đổi,
   bị chặn, đã xác nhận và còn dở. Chỉ trả link Sheet nếu thực sự đã sửa.

## Phát hiện thay đổi và phục hồi

State nằm ở `.ss-sync/update-sheet/state.json`. Lượt đầu nhập baseline từ các
`partition_manifest.json` đã xác nhận rồi đọc/hash một lần để lập mốc metadata.
Các lượt sau chỉ stat mọi tên Merge; chỉ đọc/hash file mới, metadata đổi hoặc
còn pending. Metadata đổi nhưng hash không đổi chỉ cập nhật cache local.

Metadata không bảo đảm phát hiện khi nội dung bị sửa rồi mọi metadata vẫn được
giữ nguyên. Dùng `scan --rehash` khi người dùng yêu cầu kiểm tra đầy đủ hoặc có
dấu hiệu metadata không đáng tin. Không bật lại toàn bộ hash theo thói quen.
Cache local cũng không phát hiện chỉnh sửa trực tiếp trên Sheet của file đang
bị bỏ qua; đồng bộ này lấy Merge local làm nguồn cho file được yêu cầu cập nhật.

File ghi lỗi vẫn pending, kể cả local quay lại hash cũ. Chạy lại phải đọc remote
và đối soát trước khi xác nhận. Không xóa state/manifest để làm mất trạng thái lỗi.
Receipt chỉ lưu bằng chứng hash/metadata, không lưu lịch sử bản dịch VI.

`run.json` ngăn các agent update-sheet chạy chồng. Khi có khóa cũ, xác minh lượt
cũ và các request connector đã dừng rồi mới dùng token cũ để tiếp tục/finish;
không gỡ khóa chỉ vì token đã lâu. `command.lock` chặn hai helper ghi state cùng
lúc; chỉ dọn khóa này sau khi xác minh process cũ đã dừng. Không chạy cùng một
writer khác đang cập nhật các trang nội dung đó.
