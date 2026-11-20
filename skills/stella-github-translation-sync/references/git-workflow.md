# Quy trình Git cho cộng tác viên

## Kiểm tra trước khi thay đổi

Tại repo thực tế, dùng PowerShell hoặc shell phù hợp:

```powershell
git rev-parse --show-toplevel
git status --short --branch
git remote -v
git branch -vv
git diff --name-status
git diff --cached --name-status
git ls-files --others --exclude-standard
```

Xem diff của từng đường dẫn trong phạm vi, bao gồm staged và unstaged; `git status` một mình không đủ chứng minh nội dung. Với file mới, đọc trực tiếp và kiểm tra dung lượng, định dạng, provenance và quyền chia sẻ. Dùng `git check-ignore -v -- <đường-dẫn>` khi file bị thiếu; tìm các file được dự án chủ động track (`git ls-files`) và tài liệu phân phối thực tế. Không ép add file ignore; không thay `.gitignore` chỉ để vượt rào mà chưa hiểu tác động.

Ghi lại chính xác remote và nhánh upstream. Nếu remote không có upstream, nhánh đích không rõ, credential/quyền thiếu, hoặc scope dữ liệu chưa được phép chia sẻ: hoàn tất các kiểm tra và chuẩn bị cục bộ có thể làm, sau đó nêu blocker. Không đoán URL/nhánh hoặc in token. Remote ghi trong SKILL chỉ là manh mối phải kiểm tra lại.

## Đồng bộ và cô lập

Fetch đúng remote/nhánh đã xác định; ví dụ với `origin` và `main` chỉ sau khi đã xác nhận chúng là đích:

```powershell
git fetch origin main
git rev-list --left-right --count HEAD...origin/main
git log --oneline --decorate -8 HEAD
git log --oneline --decorate -8 origin/main
```

Khi sạch và nhánh có upstream phù hợp, đồng bộ fast-forward khi khả thi, không áp `pull` lên worktree có thay đổi chưa rõ. Nếu worktree bẩn, có staged changes của người khác, HEAD behind/diverged, hoặc đang ở nhánh không phù hợp, ưu tiên worktree/nhánh tạm riêng dựa trên remote đã fetch; đem sang chính xác các file/hunk được giao, bảo toàn nội dung và quyền sở hữu. So diff, tránh copy đè thay đổi đồng thời. Đối với file cùng bị sửa ở upstream và batch: so ba phía, hòa giải có căn cứ và kiểm thử; nếu mơ hồ, dừng tại conflict và mô tả thay đổi cần quyết định. Đừng reset, clean, stash mọi thứ, checkout đè file, cherry-pick mù hoặc force push để vượt trở ngại.

Không tự stage toàn bộ bằng `git add .` / `git add -A` trong worktree có thay đổi ngoài scope. Nếu index đã có thay đổi của người khác, không commit index đó; dùng worktree riêng hoặc phương án cô lập khác đã kiểm tra. Không include file theo tên riêng mà bỏ qua nội dung/hunk ngoài phạm vi.

## Kiểm tra, commit, push

- Chạy kiểm tra phù hợp dữ liệu thực tế: mapping đúng source/version, ID không mất hoặc trùng, token/tag/placeholder/control và Unicode; semantic review/localization QA theo project gate. Ghi lệnh, kết quả và phần chưa test. Nếu snapshot chưa có review bắt buộc, không coi là bản đã duyệt; chỉ chia sẻ draft nếu người dùng cho phép rõ.
- Stage theo đường dẫn cụ thể bằng `git add -- <đường-dẫn>`. Xem `git diff --cached --stat`, `git diff --cached --check`, `git diff --cached` và `git status --short`. Xác nhận staged diff chỉ chứa batch được giao, không lẫn binary/game/credentials; sửa trong phạm vi được phép.
- `git commit -m "..."` với thông điệp phản ánh thay đổi thực; ghi hash `git rev-parse HEAD`. Với lệnh push, chỉ dùng remote và nhánh đã xác minh, ví dụ `git push origin HEAD:main` khi trực tiếp push main thực sự phù hợp. Nếu nhánh bảo vệ hoặc quy trình repo cần PR, push nhánh thích hợp và mở PR khi đã được giao; không cố vượt quyền.
- Sau push `git fetch <remote> <nhánh>` và kiểm `git merge-base --is-ancestor <commit> <remote>/<nhánh>`. Xác minh path/nội dung tại commit (`git show <commit>:<path>` hoặc hash blob) và remote branch thực tế. Commit có mặt trên GitHub không chứng minh bản cài đã được cập nhật hay runtime pass.
- Ghi repo, nhánh, commit, đường dẫn được đẩy, kết quả QA và các file chưa được chia sẻ. Có sai lệch, push thất bại, nhánh từ xa thay đổi hoặc không thể xác thực từ xa thì báo cụ thể, không nói đã thành công.
