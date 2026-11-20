# Chỉ thị tiếp tục: hai lỗi launcher và chuẩn bị push — 06/11/2026

## Trạng thái dừng theo yêu cầu người dùng

Người dùng yêu cầu lưu chỉ thị để agent sau tiếp tục fix. **Dừng tại đây**: không push, không phát hành, không đồng bộ website, không build thêm, không sửa hoặc cài tài nguyên game trong phiên bàn giao. Đây là chỉ thị dừng hiện tại, không xóa yêu cầu hoàn thành công việc khi người dùng chủ động tiếp tục.

Mục tiêu tiếp theo: sửa lỗi `SIZE_MISMATCH` (26.011.641/26.210.913 byte) và `TRANSACTION_FAILED`/Windows `WinError 5`; chuẩn bị source đạt tiêu chuẩn, push GitHub khi các gate dự án đạt, sau đó chỉ phát hành/sync web nếu thuộc phạm vi được giao. Không hứa có thể tự khắc phục mọi trường hợp Windows từ chối quyền, khóa file hoặc anti-cheat.

**Quyết định còn chờ:** người dùng chỉ trả lời “sao lưu theo hash”. Đã thực hiện backup, nhưng **chưa có chỉ thị rõ ràng cho việc cài `dist/data_patched_vi.arcx` và `dist/lua_patched_vi.arcx` vào client Yostar**, và chưa có lựa chọn trả lời cho câu hỏi tiếp theo. Không coi yêu cầu sao lưu là cho phép ghi đè game. Nếu cần đồng bộ client, trình bày cụ thể ảnh hưởng và rủi ro anti-cheat chưa xác minh, lấy quyết định rõ ràng; đọc `AGENTS.md`, `docs/DEPLOYMENT_AND_SYNC_INVARIANTS.md`, `docs/PATCH_AND_ROLLBACK.md`. Không sửa game hay `dist` chỉ để ép kiểm tra PASS. Không sao chép giữa client; chỉ lấy archive deploy trực tiếp từ `dist` nếu được giao rõ, có preimage, backup readback, journal, atomic replace và rollback guard; không tự kill process hay thay ACL/bảo vệ.

## Git và tài sản đang dở

- Repo: `C:/YostarGames/StellaSora_EN/StellaSora_VietHoa`; HEAD và `origin/main` được kiểm tra lúc bàn giao: `b7f02e677e1a6de384a55b71eee7185afadd3795`. Kiểm tra lại fetch/status trước khi tiếp tục; không reset/clean/stash hay ghi đè công việc khác.
- Source sửa trong working tree: `launcher/core/installer.py`, `launcher/core/network.py`, `launcher/core/self_update.py`, `launcher/core/config.py`, `launcher/version_info.txt` (runtime/PE 1.2.1 dự kiến). Còn thay đổi liên quan ở `tools/publish_release_v120.py`, untracked `tools/verify_release_payloads.py`, `launcher/tests/test_network.py`, `tests/test_release_payloads.py`, cùng tests bị ignore `launcher/tests/test_installer.py`, `test_self_update.py`, `test_rollback.py`, `test_security.py`, `test_config.py`, `__init__.py`.
- `launcher/ui/main_window.py` có rất nhiều thay đổi UI không liên quan thuộc công việc khác. Chỉ thay dòng thông báo tự cập nhật theo patch đã chuẩn bị `work/subagents/push_ready_20261106_r01/ui-only.patch`; **không commit toàn bộ file** nếu không được giao, phải giữ các hunk người dùng. Các file UI/resources và untracked khác cũng giữ nguyên.
- `launcher/tests/test_network.py` và `tests/test_release_payloads.py` đang là intent-to-add; một số tests bị ignore bởi `.gitignore` (`tests/`). Khi tới bước commit phải chủ động track đúng các test và dependencies cần để checkout sạch chạy lại, không đưa file không liên quan. Không stage/reset nội dung người khác mà chưa kiểm index.
- EXE cũ `dist/launcher_fix_20261106_r02/StellaSora-Windows_v1.2.1.exe`, SHA256 `cb58024895d825a37644fb0d77c6fabc42c95d44ee1d45b94a460a2693a439bc`, đã build **trước** sửa legacy `files:null` và UI; không dùng như bản cuối. `work/launcher_release_20261106_r01/staged_release` cũng chứa binary cũ. Source snapshot được cập nhật tại `work/launcher_release_20261106_r01/source`, chưa build lại. Không build lại khi gate mismatch theo quy định.
- Chưa commit/push bản sửa launcher, chưa cập nhật release hay website. Release Windows hiện công khai vẫn v1.2.0. Website đang ghim Windows v1.2.0. Cả Windows và Android đọc `releases/latest`; một release chỉ có EXE sẽ làm hỏng kênh. Trước phát hành cần xác minh đầy đủ manifest/asset Windows, metadata Android, APK/URL, updater, version và link web; không công bố khi QA/gate chưa đạt.

## Bằng chứng lỗi và kiểm thử

- Release công khai v1.2.0: tải thực `data_patched_vi.arcx` đủ 26.011.641 byte SHA256 `3605edbb969e83e3ad104f1d1ebef35693223cf8a619aea4130ce212311aca3c`; manifest công khai khai đúng kích thước/hash. Ảnh 1 khớp metadata cũ, nhưng không có log chính máy ảnh nên nguồn manifest cũ trên máy đó chưa xác định. Bản sửa network ràng buộc metadata và payload, tải lại có giới hạn/range/hash; QA phát hiện manifest legacy `files:null` regression đã được sửa.
- Ảnh 2 cho thấy Windows từ chối replace, không xác định được nguyên nhân cụ thể từ ảnh. Fixture Windows tái hiện WinError 5 khi đích readonly hoặc handle không chia sẻ quyền xóa. Bản sửa retry có giới hạn, kiểm preimage/hash trước từng lần; lỗi kéo dài cần hướng dẫn kiểm tra tiến trình, quyền thay/xóa, thuộc tính. Không tự đổi ACL hoặc thuộc tính.
- Updater mới bỏ ép taskkill và xử lý phục hồi có guard. QA đã thử chuyển tiếp bằng source updater trích từ EXE v1.2.0 trên bản sao EXE và app-data cô lập: helper mới thay đúng bản sao, backup khớp. Không điều khiển GUI EXE cũ, chưa thử máy thật. EXE cũ có fallback helper cũ nếu copy helper mới thất bại: không tuyên bố đường cập nhật an toàn trong mọi trường hợp.
- `python -m unittest launcher.tests.test_self_update launcher.tests.test_installer launcher.tests.test_rollback launcher.tests.test_security launcher.tests.test_network launcher.tests.test_config tests.test_release_payloads`: **50/50** pass; QA độc lập `work/subagents/push_ready_20261106_r01/qa/RESULT_R02.json`. Source snapshot cô lập chạy 44 launcher tests và 6 preflight tests. GUI mới, cài lên máy ảnh và gameplay: chưa kiểm. Source hashes của QA trong RESULT.
- `python tools/verify_release_payloads.py --dist work/launcher_release_20261106_r01/staged_release`: 189 mục, 9 checksum pass trên snapshot trước sửa source cuối; không chứng minh binary mới hoặc release công khai.

## Backup, mismatch và provenance

Backup chỉ đọc, đã kiểm SHA256 nguồn trước/sau và bản sao; chưa ghi game:
`work/push_ready_20261106_r01/yostar_backup/BACKUP_MANIFEST.json` (SHA256 `456039abd43b5175dc7d2c4c179693533dcdab9c3bab0362f3e39c4eec795538`), kèm `README.md`. Backup data `bc57df547138628e0b598a701591103d2ee5b716f44b5b1515bbcadc320c8bd0`, lua `26499e674c460edb776a0071b440d8ffa3a50f3fa471ae73ceac1d8cbda7ab8b`, receipt `666bfa64fae62b333103b9a997846db6653ec7fcdf1fcb63a596dcd86710708c`. Xác minh lại mọi hash khi tiếp tục; không rollback lên bản đã thay đổi sau backup.

`dist` data `3605edbb969e83e3ad104f1d1ebef35693223cf8a619aea4130ce212311aca3c`, lua `3be9d079315349a6e85a2e0e9b0ed6127ed1956a029fd8823a3f6270ff3e32f3`; Steam khớp hai hash này khi kiểm. Yostar đang khớp receipt cài 01/11 từ manifest release cũ, không phải lỗi byte ngẫu nhiên. Báo cáo snapshot `work/subagents/push_ready_20261106_r01/data/RESULT.json`: 481 chuỗi bảng khác, 610 tham số cảnh khác gồm 562 thoại chính, 31 khóa chỉ dist; không tự kết luận phiên bản nào tốt hơn ở mọi mục. Yostar resource `2610291554`, Steam `2610161720`, cùng game 2.0.1; gameplay không xác minh.

Gate `python tools/verify_deployed_game_data.py` exit 1 vì data Yostar khác golden, kiểm tra dừng ngay trước lua; lua cũng khác theo kiểm hash độc lập. Rule `AGENTS.md` và `docs/DEPLOYMENT_AND_SYNC_INVARIANTS.md` yêu cầu mọi hash/mẫu khớp sau build/deploy trước nghiệm thu. Không nới hoặc giả kết quả gate.

## Tiếp tục khi người dùng giao

1. Đọc handoff này, AGENTS/policy, kiểm Git status/fetch và hash source, backup, dist, receipt, cả hai client và trạng thái game; các bằng chứng là snapshot có thể cũ. Không tự thay file nếu chưa có phạm vi cài Yostar rõ ràng.
2. Sau quyết định rõ, dùng giao dịch có kiểm preimage, backup, journal, readback, rollback guard theo quy định; nếu dữ liệu đổi hoặc gate vẫn lỗi, dừng và giữ nguyên backup. Không lấy dữ liệu từ Steam hoặc can thiệp anti-cheat.
3. Chạy lại gate, tests và QA độc lập. Nếu được build, build source snapshot cuối và kiểm GUI/embedded code/test; ghi riêng runtime/gameplay/máy thật chưa kiểm.
4. Nếu người dùng vẫn yêu cầu push và gate đạt: chuẩn bị commit đúng phạm vi bao gồm tests/dependencies, stage riêng patch UI, giữ mọi thay đổi khác; xác minh commit và remote. Không suy luận push đồng nghĩa phát hành. Nếu phát hành sau này, kiểm kênh latest/Windows/Android, website, metadata/hash public và quy tắc release.
