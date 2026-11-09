# Chuyển phiên dữ liệu TramVH

TramVH dùng D1 làm dữ liệu cộng tác. `dataset_state` giữ một phiên toàn cục và một trong ba trạng thái `open`, `locked`, `publishing`. Mỗi yêu cầu ghi mang `base_dataset_version`; yêu cầu từ phiên cũ bị từ chối, còn bản nháp trên máy người dịch được giữ lại.

## Bản đang chạy

Phiên đầu sau migration là `legacy-1`. Manifest tương ứng nằm ở `web/story_translator/data/dataset-manifest.json`; nó ghi SHA-256 của `chapters.json` và từng chương. Dữ liệu web hiện có 16 chương, 63.349 câu EN/VI. Giao diện chọn nhóm → chương/trang → cảnh/file → câu và dành chỗ đối chiếu EN/JP/CN khi soạn đề xuất. Chưa có JP/CN trong các JSON chương, nên hai ô đó hiện báo thiếu nguồn; không coi việc kiểm tra EN/VI là kiểm tra đủ ba ngôn ngữ.

Migration `web/story_translator/worker/migrations/0002_dataset_identity.sql` chỉ chạy một lần trên D1 schema v1, trước khi triển khai Worker v2. Sao lưu D1 trước khi chạy. Cloudflare hỗ trợ `wrangler d1 export ... --remote --output ...` và `wrangler d1 execute ... --remote --file ...`; luôn chỉ định `--remote` rõ ràng. Không chạy migration này trên DB đã là v2 vì `ALTER TABLE` sẽ báo cột trùng.

## Mỗi lần thay dữ liệu chương

1. Kiểm tra nguồn Merge, ID câu, thứ tự và số câu. Đối chiếu EN/JP/CN ở nguồn riêng nếu đợt đó có đủ và đã ghép ID; web hiện chưa có JP/CN. Kiểm token/tag trước khi công bố.
2. Chạy `node tools/build_tramvh_dataset_manifest.mjs --write <version>` rồi `node tools/build_tramvh_dataset_manifest.mjs --check <version>`. Chọn tên phiên mới, khác tên đang chạy. Công cụ dừng nếu chương/câu thiếu, ID trùng hoặc tổng câu sai.
3. Từ TramVH, bật quyền duyệt rồi mở **Quản lý phiên dữ liệu**. Chuyển `open → locked`. Khi khóa, người dịch không gửi được đề xuất mới; các bản nháp vẫn ở máy.
4. Duyệt hoặc từ chối toàn bộ đề xuất đang chờ. Chỉ chuyển `locked → publishing` khi số đề xuất chờ là 0.
5. Triển khai Worker và tài nguyên web. Kiểm trang, API `/api/collab/status`, `/api/chapter_data?id=...` và manifest trên URL thật. Chạy smoke test desktop/mobile trước khi mở cho mọi người.
6. Trong màn quản lý phiên, chọn **Kích hoạt phiên mới**. Backend tính lại hash từng tệp đã triển khai và so với manifest; tệp thiếu hoặc sai byte làm kích hoạt thất bại. Kích hoạt để phiên ở `locked`.
7. Kiểm phiên mới và mở `locked → open`. Khi mở, backend đối chiếu manifest đang triển khai. Kiểm lại API công khai và thử gửi/duyệt một câu theo quy trình bình thường.

Nếu chưa triển khai dữ liệu mới, có thể mở lại từ `locked`. Nếu đã sang `publishing` mà cần hủy, triển khai lại đúng bộ dữ liệu cũ trước, rồi chọn **Hủy xuất bản**. Backend chỉ cho hủy khi manifest cũ đã hiện trên web. Sau đó mới mở lại. Giữ bản triển khai cũ và bản sao lưu D1 cho việc phục hồi; không xóa đề xuất/lịch sử để ép chuyển phiên.

Định danh người dùng được giữ bằng cookie HttpOnly theo trình duyệt. Tên hiển thị lấy từ D1, không lấy từ payload của đề xuất. Mỗi người có tối đa một đề xuất cho một câu trong mỗi phiên; đề xuất còn chờ có thể sửa. Đây chưa phải tài khoản đa thiết bị: mất cookie đồng nghĩa nhận ID mới.

Google Sheets chỉ là nguồn trao đổi/xuất nhập sau khi ánh xạ dữ liệu. Bản dịch câu trên web chỉ ghi qua Worker/D1; luồng lưu câu trực tiếp vào GAS đã đóng. Thuật ngữ và bảng xếp hạng vẫn đi qua proxy backend hiện có.

Lệnh kiểm tra mã: `node --test tests/test_tramvh_collaboration_backend_20261101.mjs` và `node tools/build_tramvh_dataset_manifest.mjs --check legacy-1` cho snapshot hiện tại.

Tài liệu CLI D1: https://developers.cloudflare.com/workers/wrangler/commands/d1/
