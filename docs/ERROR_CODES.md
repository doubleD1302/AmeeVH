# Mã lỗi của launcher (PC và Android)

Mọi lỗi người chơi nhìn thấy đều được quy về **một mã `E-…` ổn định**, kèm tiêu đề dễ hiểu, giải thích và các bước xử lý. Hai nền tảng dùng chung một bộ mã: cùng mã nghĩa là cùng một tình huống.

> Tệp này được sinh tự động từ `launcher/core/error_catalog.py` (PC) và `android/.../ErrorCatalog.java` (Android). Đừng sửa tay; sửa danh mục rồi sinh lại.

## Người chơi làm gì khi gặp lỗi

1. Đọc tiêu đề và phần **Cách xử lý** trong hộp thoại.
2. Nếu vẫn lỗi, bấm **Sao chép mã lỗi** rồi dán cho người hỗ trợ. Nút này chép toàn bộ báo cáo chẩn đoán.
3. Khi nút Cài bị xám (PC) hoặc chưa cài được (Android), bấm **"Vì sao chưa cài được? [mã]"** dưới nút để xem đúng lý do.

## Báo cáo sao chép gồm gì

- **Dòng đầu:** `MÃ LỖI E-… (#ID)`, nền tảng, phiên bản launcher, thời gian, thao tác đang làm, bước cuối.
- **Giải thích + cách xử lý** đã hiển thị cho người chơi và **thông báo gốc** của hệ thống.
- **Đo kết nối mạng** (khi là lỗi mạng): DNS và cổng 443 tới GitHub so với một điểm đối chứng, cho biết "mất Internet", "DNS hỏng" hay "chỉ GitHub bị chặn".
- **PC:** Windows, quyền Quản trị, proxy, ổ đĩa trống, game (đường dẫn, phiên bản, biên bản cài), trạng thái GitHub từng nguồn, tuỳ chọn, 30 dòng nhật ký, chuỗi lỗi và vết lỗi rút gọn.
- **Android:** phiên bản Android và máy, loại mạng (Wi-Fi/4G/VPN, DNS riêng tư), game, gói, biên bản, nhật ký thao tác, dung lượng trống, chuỗi lỗi.

**Quyền riêng tư:** đường dẫn tài khoản Windows được thay bằng `%USERPROFILE%`, phần query của URL bị bỏ, không có token hay mã ghép đôi; Android không ghi địa chỉ/cổng ADB, định danh thiết bị hay mã ghép đôi.

## Danh mục mã lỗi

`PC` / `AND` cho biết nền tảng nào dùng mã đó. Mức: **lỗi** = thao tác thất bại; **cảnh báo/thông tin** = tình huống cần người dùng làm bước tiếp theo, không phải hỏng game.

### Mạng và GitHub

| Mã | Tiêu đề | Mức | PC | AND |
|---|---|---|:-:|:-:|
| `E-CONFIG-CHANNEL` | Nguồn GitHub trong Cài đặt chưa hợp lệ | lỗi | ✓ | ✓ |
| `E-CONFIG-SAVE` | Không lưu được cấu hình launcher | lỗi | ✓ |  |
| `E-DATA-JSON` | Dữ liệu tải về không đọc được | lỗi | ✓ | ✓ |
| `E-DATA-SCHEMA` | Dữ liệu GitHub trả về sai định dạng | lỗi | ✓ | ✓ |
| `E-DATA-UNVERIFIED` | Tệp phát hành chưa có mã xác minh | lỗi | ✓ | ✓ |
| `E-HTTP-404` | Không tìm thấy tệp trên GitHub | lỗi | ✓ | ✓ |
| `E-HTTP-4XX` | GitHub từ chối yêu cầu | lỗi | ✓ | ✓ |
| `E-HTTP-5XX` | GitHub đang gặp sự cố | lỗi | ✓ | ✓ |
| `E-HTTP-RATE` | GitHub đang giới hạn lượt truy cập | lỗi | ✓ | ✓ |
| `E-NET` | Không kết nối được máy chủ | lỗi | ✓ | ✓ |
| `E-NET-BLOCKED` | Windows hoặc phần mềm bảo mật chặn launcher dùng mạng | lỗi | ✓ |  |
| `E-NET-CAPTIVE` | Mạng đang chặn hoặc chuyển hướng đăng nhập (Captive Portal) | lỗi | ✓ | ✓ |
| `E-NET-DNS` | Không tìm ra địa chỉ GitHub (lỗi DNS) | lỗi | ✓ | ✓ |
| `E-NET-OFFLINE` | Máy chưa có đường ra Internet | lỗi | ✓ | ✓ |
| `E-NET-PROXY` | Proxy từ chối hoặc chặn yêu cầu | lỗi | ✓ |  |
| `E-NET-REFUSED` | Máy chủ từ chối kết nối | lỗi | ✓ | ✓ |
| `E-NET-RESET` | Kết nối bị ngắt giữa chừng | lỗi | ✓ | ✓ |
| `E-NET-TIMEOUT` | GitHub phản hồi quá chậm | lỗi | ✓ | ✓ |
| `E-NET-TLS` | Không thiết lập được kết nối an toàn (HTTPS) | lỗi | ✓ | ✓ |
| `E-NET-TLS-CERT` | Chứng chỉ bảo mật không được tin cậy | lỗi | ✓ | ✓ |
| `E-NET-VPN-DNS` | VPN hoặc DNS riêng tư đang chặn GitHub | lỗi |  | ✓ |
| `E-RELEASE` | Chưa có bản phát hành dùng được | lỗi | ✓ |  |
| `E-SYNC-PENDING` | Launcher đang đọc thông tin từ GitHub | thông tin | ✓ | ✓ |

### Gói bản dịch và tải về

| Mã | Tiêu đề | Mức | PC | AND |
|---|---|---|:-:|:-:|
| `E-DL-FAILED` | Tải tệp không thành công | lỗi | ✓ |  |
| `E-DL-OVERSIZE` | Tệp trên máy chủ lớn hơn kích thước công bố | lỗi |  | ✓ |
| `E-DL-PARAM` | Thông tin tải không hợp lệ | lỗi |  | ✓ |
| `E-DL-RANGE` | Máy chủ trả dữ liệu tải tiếp không đúng | lỗi | ✓ | ✓ |
| `E-DL-RESPONSE` | Máy chủ trả về dữ liệu tải không hợp lệ | lỗi | ✓ | ✓ |
| `E-DL-TIMEOUT` | Tải quá lâu so với thời hạn | lỗi | ✓ | ✓ |
| `E-DL-VERIFY` | Tệp tải về bị sai hoặc hỏng | lỗi | ✓ | ✓ |
| `E-DOWNGRADE` | Gói bản dịch cũ hơn bản đang cài | lỗi | ✓ |  |
| `E-MANIFEST-INVALID` | Bảng kê bản dịch bị lỗi | lỗi | ✓ | ✓ |
| `E-MANIFEST-MISSING` | Bản phát hành chưa có bảng kê bản dịch | lỗi | ✓ |  |
| `E-MANIFEST-PLATFORM` | Gói bản dịch không dành cho Windows | lỗi | ✓ |  |
| `E-MANIFEST-VERSION` | Không so sánh được phiên bản bản dịch | lỗi | ✓ |  |
| `E-NO-PACKAGE` | Bản phát hành chưa có gói Android | lỗi |  | ✓ |
| `E-PKG-MISMATCH` | Phiên bản game chưa khớp gói Việt hoá | cảnh báo | ✓ | ✓ |
| `E-SECURITY` | Launcher từ chối vì không an toàn | lỗi | ✓ | ✓ |
| `E-TIMEOUT` | Thao tác quá thời hạn | lỗi |  | ✓ |

### Local ADB (Android)

| Mã | Tiêu đề | Mức | PC | AND |
|---|---|---|:-:|:-:|
| `E-ADB` | Lỗi Local ADB | lỗi |  | ✓ |
| `E-ADB-AUTH` | Điện thoại chưa chấp nhận khoá Local ADB | lỗi |  | ✓ |
| `E-ADB-CONN-REFUSED` | Gỡ lỗi không dây đang tắt hoặc cổng đã đổi | lỗi |  | ✓ |
| `E-ADB-DISCONNECTED` | Kết nối Local ADB bị ngắt giữa chừng | lỗi |  | ✓ |
| `E-ADB-INPUT` | Thông tin kết nối Local ADB không hợp lệ | cảnh báo |  | ✓ |
| `E-ADB-KEY` | Khoá Local ADB gặp vấn đề | lỗi |  | ✓ |
| `E-ADB-NO-WIFI` | Cần bật Wi-Fi để dùng Gỡ lỗi không dây | cảnh báo |  | ✓ |
| `E-ADB-NOT-CONNECTED` | Chưa kết nối Local ADB | cảnh báo |  | ✓ |
| `E-ADB-PAIR` | Ghép đôi chưa thành công | lỗi |  | ✓ |
| `E-ADB-PERM` | Hệ điều hành đang chặn quyền Local ADB (ColorOS / HyperOS / MIUI) | lỗi |  | ✓ |
| `E-ADB-START` | Không khởi động được Local ADB | lỗi |  | ✓ |
| `E-ADB-TIMEOUT` | Local ADB không phản hồi | lỗi |  | ✓ |
| `E-DEVOPT` | Chưa bật Tuỳ chọn nhà phát triển | cảnh báo |  | ✓ |
| `E-NOTIF-PERMISSION` | Chưa cấp quyền hiện Thông báo | cảnh báo |  | ✓ |
| `E-OEM-BG-RESTRICT` | Hệ thống tiết kiệm pin đang hạn chế ứng dụng nền | lỗi |  | ✓ |

### Game và thư mục

| Mã | Tiêu đề | Mức | PC | AND |
|---|---|---|:-:|:-:|
| `E-BIND-MISMATCH` | Nhật ký/bản sao lưu thuộc thiết bị hoặc thư mục khác | lỗi |  | ✓ |
| `E-BUSY` | Launcher đang bận | cảnh báo | ✓ | ✓ |
| `E-GAME-NO-DATA` | Game chưa có thư mục dữ liệu (chưa tải tài nguyên) | cảnh báo |  | ✓ |
| `E-GAME-NOT-FOUND` | Không tự tìm thấy game | cảnh báo | ✓ |  |
| `E-GAME-ROOT-CHANGED` | Thư mục dữ liệu game đã thay đổi | lỗi |  | ✓ |
| `E-GAME-RUNNING` | Game đang chạy | cảnh báo | ✓ | ✓ |
| `E-GAME-STATE` | Không kiểm tra được trạng thái game | lỗi |  | ✓ |
| `E-GAME-VERSION` | Chưa đọc được phiên bản game | lỗi |  | ✓ |
| `E-GAME-WRONG-EDITION` | Đang cài bản Stella Sora khu vực khác (không phải Global EN) | cảnh báo |  | ✓ |
| `E-LAUNCH-FAILED` | Không mở được game | lỗi | ✓ |  |
| `E-NO-EXE` | Thư mục này không có StellaSora.exe | cảnh báo | ✓ |  |
| `E-NO-GAME` | Chưa tìm thấy game Stella Sora | cảnh báo |  | ✓ |
| `E-NO-GAME-FOLDER` | Chưa chọn thư mục game | cảnh báo | ✓ |  |
| `E-ROOT-MISMATCH` | Nhật ký thuộc về thư mục game khác | lỗi | ✓ |  |
| `E-VER-CHANGED` | Game đã cập nhật sau lần cài trước | cảnh báo |  | ✓ |
| `E-VERIFY` | Không đối chiếu được tệp trên máy | lỗi |  | ✓ |
| `E-VERIFY-WRITE` | Ghi xong nhưng đọc lại không khớp | lỗi | ✓ | ✓ |

### Cài đặt, tệp và khôi phục

| Mã | Tiêu đề | Mức | PC | AND |
|---|---|---|:-:|:-:|
| `E-BACKUP` | Bản sao lưu bị thiếu hoặc hỏng | lỗi | ✓ | ✓ |
| `E-FILE-CHANGED` | Tệp game bị thay đổi trong lúc launcher làm việc | lỗi | ✓ | ✓ |
| `E-FILE-DENIED` | Windows không cho launcher ghi vào thư mục game | lỗi | ✓ |  |
| `E-FILE-IN-USE` | Tệp đang được chương trình khác sử dụng | lỗi | ✓ |  |
| `E-FILE-MISMATCH` | Tệp game không còn khớp bản Việt hoá đã cài | cảnh báo | ✓ | ✓ |
| `E-FILE-MISSING` | Không tìm thấy một tệp cần thiết | lỗi | ✓ |  |
| `E-INSTALL-ROLLED-BACK` | Cài đặt không thành công, đã hoàn tác | lỗi | ✓ |  |
| `E-JOURNAL` | Nhật ký thao tác bị hỏng | lỗi | ✓ | ✓ |
| `E-NO-RECEIPT` | Chưa cài Việt hoá bằng launcher này | thông tin | ✓ | ✓ |
| `E-NO-RECOVERY` | Không có thao tác nào cần phục hồi | thông tin |  | ✓ |
| `E-RECEIPT-MISMATCH` | Biên bản cài đặt không khớp thư mục game | cảnh báo | ✓ |  |
| `E-RECOVERY-REQUIRED` | Có thao tác trước đó bị ngắt giữa chừng | lỗi | ✓ | ✓ |
| `E-STORAGE` | Ổ đĩa không đủ dung lượng | lỗi | ✓ | ✓ |
| `E-STORAGE-ACCESS` | Ứng dụng chưa truy cập được vùng lưu trữ của nó | lỗi |  | ✓ |

### Cập nhật launcher / APK

| Mã | Tiêu đề | Mức | PC | AND |
|---|---|---|:-:|:-:|
| `E-APK-INSTALL-PERMISSION` | Chưa cấp quyền cài đặt APK từ ứng dụng | cảnh báo |  | ✓ |
| `E-APK-INVALID` | Thông tin bản cập nhật ứng dụng không hợp lệ | lỗi |  | ✓ |
| `E-APK-NONE` | Chưa có bản ứng dụng mới hơn | thông tin |  | ✓ |
| `E-APK-SIGNATURE` | Chữ ký APK không khớp | lỗi |  | ✓ |
| `E-APK-VERIFY` | APK tải về bị sai hoặc hỏng | lỗi |  | ✓ |
| `E-UPDATE-INVALID` | Gói tự cập nhật không hợp lệ | lỗi | ✓ |  |
| `E-UPDATE-RECOVERY` | Lần cập nhật launcher trước chưa hoàn tất | lỗi | ✓ |  |
| `E-UPDATE-RELAUNCH` | Launcher mới không khởi động được | lỗi | ✓ |  |
| `E-UPDATE-TIMEOUT` | Launcher cũ chưa đóng nên chưa cập nhật được | lỗi | ✓ |  |
| `E-UPDATE-UNSUPPORTED` | Chỉ tự cập nhật được bản launcher đã đóng gói | cảnh báo | ✓ |  |

### Dữ liệu nhà phát hành (PC)

| Mã | Tiêu đề | Mức | PC | AND |
|---|---|---|:-:|:-:|
| `E-OFFICIAL-CRYPTO` | Windows thiếu thành phần giải mã | lỗi | ✓ |  |
| `E-OFFICIAL-FORMAT` | Launcher chưa hiểu dữ liệu của nhà phát hành | lỗi | ✓ |  |
| `E-OFFICIAL-INCONSISTENT` | Máy chủ nhà phát hành đang cập nhật | lỗi | ✓ |  |
| `E-OFFICIAL-NET` | Không tải được dữ liệu gốc từ máy chủ nhà phát hành | lỗi | ✓ |  |
| `E-OFFICIAL-NOTFOUND` | Nhà phát hành không còn tệp tài nguyên này | lỗi | ✓ |  |
| `E-OFFICIAL-REGION` | Khu vực game chưa được hỗ trợ | lỗi | ✓ |  |

### Khác

| Mã | Tiêu đề | Mức | PC | AND |
|---|---|---|:-:|:-:|
| `E-CANCELLED` | Thao tác đã được huỷ | thông tin | ✓ | ✓ |
| `E-INTERNAL` | Launcher gặp lỗi nội bộ | lỗi | ✓ | ✓ |
| `E-LOCAL-PAYLOAD` | Gói bản dịch cục bộ không dùng được | lỗi | ✓ |  |
| `E-MEMORY` | Máy không đủ bộ nhớ RAM | lỗi | ✓ | ✓ |
| `E-ZIP-CORRUPT` | Gói nén AssetBundles bị lỗi khi giải nén | lỗi |  | ✓ |
| `E-SHORTCUT` | Không tạo được lối tắt | cảnh báo | ✓ |  |
| `E-UI-BLOCKED` | Yêu cầu bị chặn | lỗi |  | ✓ |
| `E-UNKNOWN` | Lỗi chưa xác định | lỗi | ✓ | ✓ |

### Launcher v2.0 (PC)

| Mã | Tiêu đề | Mức | PC | AND |
|---|---|---|---|:-:|
| `E-BG-SYNC` | Không đồng bộ được hình nền chính thức, đang dùng ảnh dự phòng | thông tin | ✓ |  |
| `E-CFA-BLOCKED` | Controlled Folder Access / Diệt virus chặn ghi tệp | lỗi | ✓ |  |
| `E-GPU-RENDER` | Lỗi khởi tạo đồ họa phần cứng (đã bật chế độ tương thích) | cảnh báo | ✓ |  |
| `E-MIGRATION` | Di trú dữ liệu từ phiên bản cũ gặp cảnh báo | cảnh báo | ✓ |  |
| `E-NET-CAPTIVE` | Mạng đang chặn hoặc chuyển hướng đăng nhập (Captive Portal) | lỗi | ✓ |  |
| `E-PARALLEL-DL` | Tải song song gặp sự cố | lỗi | ✓ |  |
| `E-STARTUP-DLL` | Không nạp được thư viện hệ thống / Qt khi khởi động | lỗi | ✓ |  |

## Mã HTTP

Mã `E-HTTP-<số>` giữ nguyên số trạng thái HTTP thật (ví dụ `E-HTTP-503`) và dùng chung giải thích theo nhóm: `403/429` giới hạn lượt truy cập, `404` không tìm thấy, `5xx` GitHub gặp sự cố, các `4xx` khác bị từ chối.

## Thêm hoặc đổi một mã

- **PC:** thêm `_add(...)` trong `launcher/core/error_catalog.py`; nếu là `InstallerError` mới, thêm mã nội bộ vào `INTERNAL_MAP`. Test `test_every_raised_code_is_mapped_to_a_catalog_entry` sẽ báo nếu thiếu.
- **Android:** thêm `add(...)` và, nếu cần nhận diện theo nội dung thông báo, thêm một dòng vào `RULES` trong `ErrorCatalog.java`. `ErrorCatalogCheck` quét mọi thông báo trong mã nguồn và báo nếu có thông báo chưa có mã riêng.
- Giữ **mã ổn định**: người dùng đã gửi mã cũ cho bạn; chỉ đổi tiêu đề/giải thích, đừng đổi tên mã.

## Kiểm thử

```powershell
# PC (từ thư mục StellaSora_VietHoa)
$env:QT_QPA_PLATFORM = "offscreen"; python -m unittest discover -s launcher/tests -t .

# Android: danh mục + quét toàn bộ thông báo trong mã nguồn (chạy trên JVM, không cần thiết bị)
$json = "<đường dẫn tới org.json json-*.jar>"
javac -encoding UTF-8 --release 17 -cp $json -d out android/app/src/main/java/com/stellasora/viethoa/localadb/ErrorCatalog.java android/tests/ErrorCatalogCheck.java
java -Dfile.encoding=UTF-8 -cp "out;$json" com.stellasora.viethoa.localadb.ErrorCatalogCheck android/app/src/main/java/com/stellasora/viethoa/localadb
```

Chưa kiểm thử trên thiết bị Android thật (cần người dùng thử: ngắt mạng, bật chế độ máy bay, đổi DNS riêng tư, v.v.).
