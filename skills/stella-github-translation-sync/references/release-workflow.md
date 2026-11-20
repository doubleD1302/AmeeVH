# Khi được giao phát hành cho người chơi

Phân biệt ba việc: push mã/dữ liệu Git; tạo/cập nhật GitHub Release và upload asset; build/cài bản vá. Chỉ thực hiện các việc thuộc phạm vi được giao. Đọc `AGENTS.md`, `docs/GITHUB_RELEASE_RULES.md`, `docs/DEPLOYMENT_AND_SYNC_INVARIANTS.md` và quy trình phiên bản hiện hành; yêu cầu hiện tại của người dùng được ưu tiên. Không tự đoán phiên bản, tag, artifact hoặc nền tảng từ một release cũ.

Trước khi phát hành, xác minh bản dịch đã qua review phù hợp; bản build được tạo từ đúng snapshot/nguồn và có provenance, hash, kiểm thử, readback, font/layout và runtime tương ứng với tuyên bố. Những gate chưa đạt phải được nêu đúng; không phát hành bản build chưa có bằng chứng theo quy trình được giao. Tạo danh sách asset được phép phát hành, size/SHA256, metadata/manifest và kế hoạch khôi phục; kiểm tra asset thuộc đúng phiên bản. Không công khai source game, credential hoặc nội dung chưa rõ quyền chia sẻ.

Các script `tools/publish_release_v120.py` và `tools/verify_published_github_release.py` từng được viết cho tag/version cụ thể và có thể sửa release hoặc upload/xóa/thay asset. Đọc toàn bộ script và xác minh version, đích, side effect trước khi dùng; không chạy nguyên trạng cho một phiên bản khác. Nếu phù hợp, `tools/verify_release_payloads.py` có preflight chỉ đọc: kiểm tra argument và input thực tế trước khi chạy. Không cho rằng tên script hay lần kiểm cũ bảo đảm asset hiện tại hợp lệ.

Đối với GitHub Release theo quy định hiện hành: tiêu đề chỉ là số phiên bản đã chốt (không có `v`); mô tả tiếng Việt tối đa 100 từ, chỉ nêu thay đổi có thật. Tag, title và tên asset là các trường khác nhau. Xác định draft/prerelease/stable theo yêu cầu; không tự đổi release đã công khai, xóa hay ghi đè asset hoặc thay tag khi chưa có chỉ dẫn phù hợp. Nếu cập nhật một release đang tồn tại, kiểm trạng thái và tác động đến launcher/update trước khi thay đổi.

Sau thao tác được giao, đọc lại release/tag/commit/title/body, trạng thái và danh sách asset thực tế trên GitHub; xác minh asset qua checksum đáng tin cậy hoặc tải về và băm so với file đã kiểm, đồng thời kiểm manifest/URL đúng byte. Nếu chỉ kiểm tên/size, ghi đúng giới hạn đó. Kiểm tra luồng cập nhật launcher, game, font và gameplay chỉ khi được giao và có bằng chứng; không báo đã kiểm nếu chưa làm. Ghi link release, version, commit, asset/hash, kiểm tra và mọi gate còn thiếu.

## Thông báo trong launcher

Mỗi lần phát hành hoặc cập nhật bản dịch cho người chơi phải thêm mục vào `launcher/notifications.json` (đầu danh sách, ID kế tiếp, `type: release`), nâng `version`/`updated_at`, chạy `python tools/verify_seamless_update_readiness.py` (Gate 7), commit và push `main`. Chi tiết: `skills/stella-launcher-auto-update-assurance/SKILL.md` mục 5. Chỉ đăng sau khi asset release đã khớp manifest.
