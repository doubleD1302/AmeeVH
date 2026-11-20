# Bàn giao tiếp tục release thử công khai 1.2.1 — 07/11/2026

## Chỉ thị dừng
Người dùng yêu cầu **stop**, sau đó yêu cầu lưu chỉ thị. Phiên bàn giao chỉ ghi lại trạng thái và dừng; không push, tạo tag/release, upload, build thêm, chạy tiếp giả lập hay thay dữ liệu game. Chỉ tiếp tục khi người dùng giao tiếp tục.

Mục tiêu người dùng trước khi dừng: có release **test công khai ai cũng tải được**, không thay kênh release chính thức; giao diện bảng thông báo nâng cấp cho Windows/Android dành cho 1.2.1. Người dùng đã cho phép build thử cô lập dù gate dữ liệu game không đạt, giữ nguyên dữ liệu game; điều đó không biến gate thành PASS hoặc cho phép ghi đè game. Không tự suy bản test là bản 1.2.1 chính thức.

## Trạng thái Git và phạm vi
- Repo gốc: `C:\YostarGames\StellaSora_EN\StellaSora_VietHoa`; có nhiều thay đổi gốc của người dùng, giữ nguyên; kiểm status trước khi làm.
- Checkout riêng: `C:\YostarGames\launcher_fix_review_20261106_r03`; nhánh cục bộ `draft/launcher-121-notice-20261107`, sạch tại thời điểm bàn giao, HEAD `5715a5c3a8b3d48a2de165c0a8c51ef4d4e1169c` (`Improve launcher update notice layouts`), parent `d3203b75fdc4cc99ce3a4dfc0b67791e90f8e6ac`.
- `origin/main` được đọc lại `d3203b75fdc4cc99ce3a4dfc0b67791e90f8e6ac`; chưa thấy remote tag `v1.2.1*` khi kiểm. Commit UI 5715a5c chưa push. Không reset/clean/stash hoặc ghi đè các thay đổi gốc.
- Chưa tạo draft/pre-release, chưa upload và chưa công bố. GitHub latest quan sát trước dừng là `v1.2.0`. Kiểm lại live trước khi tiếp tục.
- Không nhầm `C:\YostarGames\launcher_fix_review_20261106_r03` với checkout gốc; `docs/SUBAGENT_POLICY.md`, `agents/README.md`, `docs/GITHUB_RELEASE_RULES.md`, `docs/DEPLOYMENT_AND_SYNC_INVARIANTS.md` và handoff `work/subagents/startup_notice_121_20261107_r01/HANDOFF.md` cần đọc lại.

## Bản thử đã build — chỉ candidate
Root báo cáo: `C:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\subagents\public_beta_121_20261107_r01`.

**Windows:** `pc/source/dist/launcher_ui_candidate_r09/StellaSora_Launcher.exe`, 123097168 byte, SHA256 `cd91f0929dfff8a7286d1226e8f67a0766c4f0714118507b1e20278866f18a5b`. Source do agent trích từ git archive đúng 5715a5c; PE 1.2.1.0. `pc_result.json`: 54/54 source tests; so sánh 37 module và 1479 tài nguyên bên trong; smoke/offscreen 12 giây. Không chứng minh GUI tương tác, cài game, gameplay hoặc release. Gate `pc/gate.log` FAIL; đích Yostar `data.arcx` hash `bc57df547138628e0b598a701591103d2ee5b716f44b5b1515bbcadc320c8bd0`, dist `3605edbb969e83e3ad104f1d1ebef35693223cf8a619aea4130ce212311aca3c`. Không chép archive để ép PASS.

**Android:** `android/StellaSora-Android_v1.2.1-beta.apk`, 16708339 byte, SHA256 `0625014e1b1d3d6a20242c1ae38d51da65b14b057b08d0c30d90d67eda579e42`. Agent báo build thành công, package chính, versionName `1.2.1-beta`, versionCode 13, chữ ký cert khớp production `21a38b89d9a315aee7028d25324fe4fd30ff40c97d4708310ae43ba670d74cd2`; tự xác minh lại artifact bằng apksigner/aapt2. `android/source/android/app/build.gradle` khác commit 5715 ở versionName và cách trỏ keystore phục vụ build cô lập; không đưa đường dẫn key/cấu hình nhạy cảm vào git hay report công khai. Source provenance của tag phải được xử lý rõ và độc lập review trước công bố.

Agent Android **đã bị ngắt theo lệnh stop** trong lúc test trên giả lập riêng: đang thử cài APK v1.2.0 rồi cài đè beta code 13, sau đó tính thử đường lên code 14. **Không có kết quả hoàn tất/không coi cài đè hay nâng cấp là PASS**. Giả lập `beta_qa_121` port 5570 đã được tắt; `adb devices` rỗng tại bàn giao. Không tự suy APK chạy trên máy thật, Package Installer, thông báo, cập nhật hoặc game. Kiểm lại artifacts và tiến trình trước bàn giao tiếp theo.

## Rủi ro/kênh
- `verify_result.json` chỉ là review sơ bộ; cần RELEASE_VERIFIER độc lập kiểm **đúng hai artifact cuối**, SHA, phiên bản/signature, modules/assets, test liên quan và rõ giới hạn. Tuyệt đối không nhận kết quả preliminary là QA cuối.
- Cả hai launcher đang gọi `releases/latest`; APK còn từ chối prerelease. GitHub pre-release công khai không thành latest: có thể tải bằng link trực tiếp nhưng **không tự cập nhật qua beta**, và bản thử mặc định vẫn đọc manifest/payload **stable v1.2.0**. Bảng cập nhật mới có thể không tự hiện khi latest vẫn 1.2.0; test riêng bằng fixture/kênh staging. Giải thích cho người dùng và kiểm `/releases/latest` không đổi nếu sau này được giao publish.
- Payload game/chữ Trung `流水与暗影` và nguyên nhân đổi tài khoản/banner chưa được sửa hay xác minh; không viết release note khẳng định đã fix các lỗi đó. Kết quả điều tra: `work/subagents/account_switch_display_20261107_r01/REPORT.md`.
- EXE cũ v1.2.0 có thể dùng helper cũ nếu copy helper mới thất bại; thử nghiệm helper mới trước đây không chứng minh fallback cũ an toàn. Test beta tải thủ công không chứng minh đường tự update cũ.
- Android beta giữ code 13 nhằm không chiếm code 14 của official 1.2.1; không đảm bảo bản cài thủ công qua Package Installer, nâng cấp và tương thích trước khi test thực tế. Không để beta cản phiên bản chính thức; không sửa package/authority/Store.APP một cách không kiểm tra.
- GitHub Release rules: title chỉ số phiên bản, ví dụ `1.2.1`, mô tả tiếng Việt tối đa 100 từ, nêu đúng beta, tải thủ công và phạm vi xác minh; tag beta phải riêng với tag 1.2.1 chính thức. Public pre-release là công khai, không phải private.
- Đã kiểm quyền GitHub repo `doubleD1302/AmeeVH` có push lúc trước dừng; không lưu hoặc in token/credentials.

## Tiếp tục khi người dùng chủ động yêu cầu
1. Xác minh không còn agent/fixture cũ ghi, git status/fetch/remote HEAD/latest/tags, hash hai candidate và dữ liệu nguồn. Giữ nguyên công việc người dùng.
2. Hoàn thành test Android cô lập, kiểm cert/metadata, cài đè v1.2.0 → beta và thử lộ trình beta → bản test code 14; ghi chính xác cách thử và giới hạn của Package Installer/thiết bị thật. Chỉ test trên AVD mới/cô lập; không đụng tài khoản hay game.
3. Đóng băng nguồn/binary, xử lý provenance tag và chênh lệch Android versionName không đưa đường dẫn key vào repository; tạo gói checksum/biên bản. Kiểm cả PC EXE UI mới, APK, các trạng thái notice, các sửa cũ, kênh payload. Chạy gate bắt buộc và ghi FAIL nếu vẫn khác.
4. Giao RELEASE_VERIFIER độc lập review artifact/gate. Xử lý blockers; tách candidate/beta và nghiệm thu chính thức. Không tuyên bố gameplay/đổi tài khoản đã kiểm khi chưa.
5. Nếu người dùng tiếp tục yêu cầu release test và các gate áp dụng cho beta được xử lý: lưu source trên beta branch hoặc tag riêng theo provenance, tạo **draft** trước, upload đúng EXE/APK/checksum, xác minh byte/hashes, sau đó publish `prerelease=true`, readback tag/flag, link tải nặc danh/hash và đảm bảo latest stable không đổi. Không đẩy beta vào `main`, không thay asset v1.2.0, không công bố 1.2.1 official hoặc đồng bộ website khi chưa được giao.
6. Báo URL và cách tải thủ công, giới hạn dữ liệu/khả năng cập nhật/rủi ro; không nói lỗi ảnh đã fix.
