# Công cụ thử nghiệm tải tài nguyên từ launcher

> Đây là ghi chép của bản thử đầu tiên. Xem [công cụ V2](RESOURCE_DOWNLOADER_V2.md) để dùng luồng cập nhật trong game và tải bundle ảnh. Các giới hạn launcher bên dưới chỉ áp dụng chế độ `--launcher-only`.

`tools/stella_resource_fetch.py` truy vấn API và manifest launcher PC chính thức cho EN, CN hoặc JP, sau đó tải từng tệp được chọn. Không cần mở game hoặc cài launcher. Cần Python 3 và Internet; không cần thư viện ngoài.

**Giới hạn hiện tại:** manifest launcher bản 2.0.0 chỉ liệt kê các tệp SRT trong nhóm cần tìm, không chứa `data.arcx` hoặc `lua.arcx`. Hai archive này thuộc luồng cập nhật trong game chưa xác định được URL/manifest. Vì vậy công cụ chưa thể lấy nội dung truyện và bảng mới sau mỗi bản cập nhật. Không xóa các bản cài vì cho rằng công cụ này thay thế được chúng. Launcher version cũng không nhất thiết là resource version mới nhất.

Đối chiếu ngày 05/11/2026: `ss_win.mani` của cả ba bản cài EN/CN/JP ghi `CLIENT_VER:2.0.0` và `GAME_VER:2.0.1`. Do đó thư mục đầu ra `2.0.0` thể hiện phiên bản gói launcher, **không phải** dữ liệu cập nhật 2.0.1. Không dùng bộ tải thử này để thay thế nguồn 2.0.1.

Kiểm tra danh sách mà không tải:

```powershell
python tools/stella_resource_fetch.py EN --list
python tools/stella_resource_fetch.py CN --list
python tools/stella_resource_fetch.py JP --list
```

Chỉ khi muốn tải những tệp hiện tìm thấy, cho phép kết quả thiếu archive:

```powershell
python tools/stella_resource_fetch.py EN --allow-partial --output 'C:\YostarGames\StellaResourceDownloads'
```

Đổi `EN` thành `CN` hoặc `JP`. Thư mục đầu ra được chia theo khu vực và phiên bản launcher; chọn một thư mục mới nếu đã tải trước đó. Cần chuyển công cụ và dự án ra khỏi thư mục game trước khi gỡ bản EN. Tệp `receipt.json` ghi nguồn, kích thước và SHA-256 được tính sau tải. Kích thước được đối chiếu với manifest; CRC64 của launcher được ghi lại nhưng **chưa được kiểm chứng**, SHA-256 chỉ dùng nhận diện bản tải, không xác thực nguồn độc lập.

Nếu manifest không có đủ hai archive, mặc định công cụ dừng và không tải. `--allow-partial` không có nghĩa là đã có đủ nội dung để Việt hóa. Không ghi đè thư mục game, archive hiện có hoặc các bản dịch.
