# TramVH Worker

Cloudflare Worker `tramvh` (`worker/index.mjs`): API cộng tác trên D1 `tramvh-collaboration`, proxy thuật ngữ/bảng xếp hạng sang Google Apps Script, và phục vụ tài nguyên tĩnh qua binding `ASSETS`. Thư mục `worker/` được loại khỏi tài nguyên công khai bởi `.assetsignore`.

## Các phần dựng lại ngày 2026-11-17

Bản deploy trước đó (worktree `work/tramvh_git_sync_20261109_r01`) bị xóa cùng các thay đổi chưa commit. Ba phần dưới đây được viết lại theo hợp đồng mà giao diện live đang gọi (`js/admin-portal.js`, `js/models/CollaborationModel.js`) và theo schema D1 thật. Chúng **không** phải mã gốc; hành vi chi tiết được xác nhận bằng test, không bằng đối chiếu với bản cũ.

### Chương
`CHAPTERS` (collaboration.mjs) là danh sách cho phép cố định. Đã thêm `Chuong_10_MainStory`. Khi thêm chương mới, thêm vào đây và vào `data/chapters.json` + manifest.

### Moderator theo từng người
- Bảng `moderator_codes` + cột `users.moderator_code_hash` (xem `schema.sql`, `migrations/0005_moderators.sql`; migration này **đã áp dụng trên live**, không chạy lại).
- Admin (`X-Reviewer-Key`): `GET /api/admin/moderators`; `POST /api/admin/moderators` với `action: create | revoke | unlink`.
- Dịch giả: `POST /api/collab/moderator` với `action: activate | deactivate`. Mã gắn với tên dịch giả đầu tiên kích hoạt; thiết bị khác phải đặt đúng tên. Đổi tên khác tên đã gắn thì Moderator tự tắt. Không cho kích hoạt khi còn tên mặc định "Dịch giả". Sai quá 10 lần sẽ bị khóa 5 phút theo IP.
- `GET /api/collab/me` và `POST /api/collab/profile` trả `user: {id, display_name, is_moderator}`; không bao giờ trả `moderator_code_hash`.
- `submit`: Moderator được duyệt ngay (`moderator_saved`, `provenance: moderator`, `approved_by: "<tên> (Moderator)"`), vẫn ghi lịch sử và đề xuất `accepted`. Client gửi `expect_moderator: true` mà server không còn xác nhận thì nhận `403 moderator_invalid`.
- Mã mới: 4 nhóm × 5 ký tự (`A-Z2-9`, bỏ ký tự dễ nhầm), băm SHA-256 của mã đã chuẩn hóa (chữ hoa, bỏ ký tự không phải chữ/số). Khi kích hoạt, Worker cũng chấp nhận SHA-256 của mã như gõ và của mã chữ hoa. `code_cipher` là AES-GCM (`v1.<iv>.<ciphertext>`), khóa dẫn xuất từ `REVIEWER_KEY` đầu tiên.
- **Lưu ý:** mã tạo trước đây trong D1 dùng cách băm và mã hóa không còn nguồn. Thiết bị đã kích hoạt vẫn hoạt động (so khớp bằng giá trị băm đã lưu), nhưng nhập lại mã cũ trên máy mới có thể thất bại và mã cũ không hiện lại trong danh sách. Khi đó tạo mã mới ở Admin Portal. `tools/verify_tramvh_moderator_hash.mjs` kiểm tra cách băm với một mã thật (chạy trên máy bạn).

### Duyệt hàng loạt
`POST /api/admin/bulk_approve` `{chapter_id, scene_id, reason, dry_run}`.
- Chỉ xét câu `pending` (không gồm `machine_pending`, `needs_review`) khớp nguồn hiện tại.
- Bỏ qua và đếm: `chua_co_ban_dich`, `con_nguyen_tieng_anh`, `co_de_xuat_cho`, `loi_ma_dinh_dang`. `not_in_database`: câu chưa có hàng trong D1.
- Không `dry_run: false` tường minh thì chỉ là chạy thử. Mỗi yêu cầu duyệt tối đa 200 câu, mỗi câu một mục lịch sử (`event_type: approved`, lý do `Duyệt hàng loạt: ...`), có điều kiện revision/source_hash/trạng thái nên không ghi đè câu vừa đổi. Không chạy khi phiên `publishing`.

## Kiểm thử
Từ gốc repo: `node --test "tests/*.mjs"` (cần Node có `node:sqlite`).

## Deploy
```
cd web/story_translator
npx wrangler deploy --dry-run --config wrangler.json
npx wrangler deploy --keep-vars --config wrangler.json --message "<mô tả>"
```
- Không deploy từ thư mục chỉ có giao diện: deploy thay cả Worker và sẽ làm mất backend.
- Trước khi deploy ghi lại phiên bản hiện tại (`npx wrangler deployments list`) để có đích `wrangler rollback`.
- Sau khi deploy kiểm tra: `/api/collab/status`, `/api/chapters` (đủ chương), các route `/api/admin/*` trả 401/403 (không phải 404), trang `/admin`; Cloudflare từng phục vụ HTML cũ từ cache.
- Phiên bản live trước lần dựng lại này: `86b8b5a9-7d10-4e05-9469-c18c0fdc7691`; phiên bản sau: `5ce4ea51-f90c-4ce2-b341-f6122cd47fdd`.
