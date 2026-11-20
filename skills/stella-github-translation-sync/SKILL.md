---
name: stella-github-translation-sync
description: Đồng bộ lên GitHub các thay đổi bản dịch Stella Sora đã hoàn tất, bao gồm kiểm tra phạm vi, commit, push, xác minh từ xa và xử lý riêng GitHub Release khi được giao.
---

# Đồng bộ bản dịch Stella Sora lên GitHub

Dùng skill này sau mỗi đợt cập nhật bản dịch Stella Sora hoặc khi người dùng yêu cầu đẩy bản dịch lên GitHub. Chủ sở hữu đã yêu cầu đồng bộ sau mỗi lần cập nhật bản dịch mới: trong phạm vi đó, chuẩn bị, commit và push các thay đổi phù hợp mà không hỏi lại từng bước, miễn là xác định được đúng repository, nhánh đích và nội dung được phép công bố. Yêu cầu hiện tại của người dùng, phân quyền thực tế và quy định dự án luôn được ưu tiên. Nếu người dùng chỉ yêu cầu nghiên cứu/offline, yêu cầu không push, hoặc chưa cho phép công bố dữ liệu cụ thể, giữ nguyên phạm vi đó.

Skill hướng dẫn agent/collaborator; bản thân nó không tạo Git hook, lịch chạy hay tự theo dõi file. Khi được gọi trong phiên cập nhật, thực hiện workflow trước khi kết thúc phiên nếu có nội dung thực sự sẵn sàng.

## Đầu vào và ranh giới

1. Xác định thư mục gốc bằng `git rev-parse --show-toplevel`; đọc `AGENTS.md`, yêu cầu phiên, trạng thái/checkpoint và quy tắc phân phối hiện hành nếu có. Không coi đường dẫn máy khác hay số phiên bản cũ là sự thật hiện tại.
2. Tìm đúng repo/remote/nhánh bằng `git remote -v`, `git branch -vv`, `git status --short --branch`. Repo ghi nhận tại thời điểm soạn là `https://github.com/doubleD1302/AmeeVH.git`; xác minh lại, không tự thay remote hoặc lộ credential. Repo/nhánh không rõ hoặc khác yêu cầu thì dừng phần push và báo chính xác thông tin cần xác định.
3. Xác định rõ output mới, nguồn/phiên bản game, review và QA tương ứng; phân biệt proposal, bản được duyệt, artifact đã build và bản đã kiểm runtime. Không nâng trạng thái pending thành approved. Không tuyên bố đã cập nhật game hoặc phát hành chỉ vì dữ liệu offline đã được push.
4. Chỉ đưa lên GitHub nội dung người dùng được phép chia sẻ và thuộc lần cập nhật: bản dịch/dữ liệu nguồn do dự án chọn, registry/metadata, ghi chú hoặc code cần thiết. Bảo toàn token/tag, ID, hash và provenance khi áp dụng; không push khóa, token, credential, dữ liệu cá nhân, file game gốc hoặc artifact có quyền chia sẻ chưa rõ. Không hiển thị bí mật trong log. Tôn trọng `.gitignore`; không `git add -f` để vượt qua nó chỉ vì thiếu file.
5. `work/`, `dist/`, `*.arcx` đang bị ignore trong dự án lúc viết skill. Nếu bản dịch mới chỉ nằm trong những nơi này, không báo Git push đã đưa bản vá lên GitHub. Xác định nơi lưu dữ liệu dịch được dự án cho phép theo dõi hoặc kênh phân phối được giao. Chuẩn bị phương án cụ thể; nếu không xác định được quyền chia sẻ/đích thì giữ offline và báo blocker. Không tự đưa dump game vào repository.

## Workflow bắt buộc

Đọc [references/git-workflow.md](references/git-workflow.md) để thực hiện thao tác Git, nhất là khi worktree bẩn, nhánh chậm hơn upstream, đã có staged changes, hoặc xảy ra xung đột.

- Kiểm tra danh sách và nội dung thay đổi theo từng đường dẫn, kiểm tra nguồn/QA và chạy test hoặc audit phù hợp với định dạng thật. Xem cả file mới và file bị ignore; báo rõ gate chưa chạy. Không tự tạo review giả hoặc dùng kiểm cấu trúc thay semantic/runtime.
- Chọn duy nhất các file thuộc batch đã được phép chia sẻ. Giữ nguyên thay đổi/staging của người khác. Nếu không thể tách an toàn trong worktree hiện tại, dùng worktree riêng và chuyển đúng thay đổi; không reset, stash toàn bộ, sửa conflict hoặc xóa file của người khác một cách âm thầm.
- Fetch nhánh đích, xác minh upstream và chênh lệch trước khi tạo commit dựa trên HEAD thích hợp. Không force push, ghi đè lịch sử, gộp thay đổi ngoài phạm vi, hoặc âm thầm sửa protected branch. Bảo vệ thay đổi sẵn có khi đồng bộ; dừng và báo blocker nếu không thể làm an toàn.
- Review staged diff và danh sách file; commit mô tả cụ thể đợt dịch, push đúng remote/nhánh được xác định. Khi branch protection đòi pull request, dùng nhánh mới và PR nếu việc đó thuộc yêu cầu; không vượt protection. Khi có lỗi auth/quyền, non-fast-forward hoặc xung đột, không lặp vô hạn: kiểm tra nguyên nhân, thử cách an toàn có căn cứ, rồi báo blocker nếu không giải quyết được.
- Sau push, fetch/read lại nhánh đích, xác minh commit đã có trên remote, và kiểm tra file/bản dịch thực sự hiện diện ở commit đó. Báo link repository/commit khi xác định được, hash, nhánh, phạm vi, kiểm tra và các giới hạn còn lại. Nếu không có thay đổi phù hợp, nói rõ không có commit/push; không tạo commit rỗng.

## Release và cập nhật đến người chơi

Git push chỉ cập nhật Git; không tự tạo Release, upload file, đổi manifest, build hoặc triển khai game nếu phạm vi yêu cầu chưa bao gồm các việc đó. Khi người dùng yêu cầu phát hành/cập nhật cho người chơi, đọc [references/release-workflow.md](references/release-workflow.md) và quy tắc release hiện hành. Nếu chỉ có registry/proposal offline, kết quả là bản dịch offline, chưa có bản cài cập nhật. Không biến lời yêu cầu tạo skill thành yêu cầu thực hiện push hoặc phát hành ngay.
