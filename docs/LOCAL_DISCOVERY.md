# Khảo sát bản cài cục bộ — 19/10/2026

Các dữ kiện dưới đây đọc trực tiếp tại `C:\YostarGames\StellaSora_EN`. Chúng là snapshot, phải kiểm lại sau cập nhật. Báo cáo máy đọc: `reports/inventory_initial_20261019.json`.

| Dữ kiện | Bằng chứng |
|---|---|
| Product | `StellaSora_Data/app.info`: YOSTAR (HONG KONG) LIMITED / StellaSora |
| Client/launcher | `game-launcher-config.json`: tag StellaSora_EN, version 1.13.0 |
| Tài nguyên cập nhật | `Persistent_Store/ss_win.mani`: CLIENT_VER 1.13.0, GAME_VER 1.16.1, RES_VER 2610041900 |
| Tài nguyên cài sẵn | `InstallResource/install_resource_manifest.mani`: GAME_VER 1.13.0, RES_VER 0 |
| Unity | Header `data.unity3d` và `font.unity3d`: UnityFS, 2022.3.62f2 |
| IL2CPP | Có GameAssembly.dll và `il2cpp_data/Metadata/global-metadata.dat` |
| Font/UI libraries | ScriptingAssemblies.json có Unity.TextMeshPro.dll; chưa xác minh từng màn hình dùng font nào |
| Bảng | `Persistent_Store/Tables/data.arcx`, 23.321.879 byte, magic hex `1a424152` |
| Script | `Persistent_Store/Scripts/lua.arcx`, 61.344.344 byte, cùng magic |
| Hotfix | `hotfix.arch` có ZIP signature; cùng thư mục có Hotfix.dll; chưa phân tích loader |
| Thư mục bảo vệ | Có AntiCheatExpert; không sửa/can thiệp trong lộ trình này |
| Patch_Store | Rỗng tại thời điểm kiểm kê |

Magic `.arcx` chưa đủ chứng minh thuật toán nén/mã hóa. Không gọi nó là ZIP, JSON, Lua plaintext hay một format đã hỗ trợ. Không đổi byte rồi đoán offset. Đọc `docs/FORMAT_RESEARCH.md`.

## Phụ đề sẵn sàng trích

Có bốn tên tệp sau trong cả `Persistent_Store/Videos` và `StellaSora_Data/StreamingAssets/InstallResource`:

- `Prologue-Prologue_P4_JPVA_FP_EN.srt`
- `Prologue-Prologue_P4_CNVA_FP_EN.srt`
- `CH04ED-CH04ED_EN.srt`
- `CH06ED-CH06ED_EN.srt`

Hai bản của từng tệp khớp byte ở snapshot này. Catalog khởi đầu chọn **tường minh Persistent_Store**, không coi đó là bằng chứng game ưu tiên đọc thư mục này. Tổng 51 cue, bốn file. JPVA/CNVA vẫn là phụ đề tiếng Anh; timestamp khác nhau nên không gộp ID.

CNVA cue 3 chứa `dffd` cuối câu, có ở cả bản cài sẵn và Persistent_Store. Chưa biết nguyên nhân. Catalog giữ nguyên và gắn source issue; reviewer có thể kết luận là rác nguồn sau khi đối chiếu cảnh/biến thể, ghi lý do cụ thể trước khi bỏ khỏi bản VI.

## Chưa biết

- Tổng số text truyện/UI/cơ chế, cấu trúc bảng và chuỗi được resolve từ ID.
- Mức ưu tiên nguồn, điều kiện hot update, chức năng checksum của từng trường manifest.
- Đường nạp font/TMP, glyph tiếng Việt, fallback, atlas và layout thực tế.
- Có hay không nội dung chỉ tải từ server hoặc ảnh chứa chữ ở mỗi màn hình.
- Khả năng cài patch tài nguyên mà game chấp nhận, độ bền sau update, kết quả gameplay.

Không suy luận các điểm này từ việc trích được SRT hoặc từ báo cáo static PASS.
