# Tải tài nguyên Stella Sora V2

Công cụ tải tài nguyên PC nguyên gốc từ máy chủ chính thức từng khu vực, không cần cài/mở game hay launcher. Đầu ra là archive/bundle để trích xuất, chưa tự dịch hoặc xuất ảnh PNG.

## Chạy bản độc lập

Thư mục: `C:\YostarGames\StellaResourceTool`. Cần Python 3.10+; bản đóng gói có dependency AES trong `.deps`. Chạy lệnh tại thư mục này:

```powershell
# Xem phiên bản, số tệp, dung lượng; chưa tải payload
python stella_resource_fetch.py ALL --plan

# Tải toàn bộ phần chữ và bundle ảnh của ba khu vực
python stella_resource_fetch.py ALL

# Chỉ một khu vực, hoặc chỉ phần chữ
python stella_resource_fetch.py CN
python stella_resource_fetch.py ALL --profile text

# Tải mẫu: hai archive, một SRT, tối đa hai bundle banner/gacha/UI nhỏ
python stella_resource_fetch.py ALL --sample
```

`--sample` chỉ là kiểm chứng mẫu. Profile mặc định `localization` lấy mọi `.unity3d` trong manifest đúng khu vực, cả bundle chung và bundle ngôn ngữ, để bao phủ texture/banner và phụ thuộc. Dung lượng có thể gần bản cài: gói cài đầu tiên có khoảng 19,4 GiB bundle/khu vực. Xem `--plan` cho dung lượng hiện tại và chi phí base/delta. `text` chỉ lấy hai archive và phụ đề. Banner website/dịch vụ ngoài manifest tài nguyên PC không thuộc phạm vi này.

## Cập nhật và kiểm chứng

Đọc `/meta/win.html` của đúng khu vực, giải mã metadata, kiểm MD5 các manifest, chọn manifest sau bản vá cuối. Giữ riêng phiên bản client, game và resource. Client 2.0.0 có thể đi cùng game 2.0.1.

Từng tài nguyên là tệp đầy đủ hoặc chuỗi base + BSDIFF40 delta. Base, delta, các kết quả trung gian và kết quả cuối đều phải khớp hash/kích thước nguồn. Phát hiện cấu trúc chưa hỗ trợ, thiếu dependency hoặc metadata thay đổi khi lập kế hoạch thì dừng. Không tự lùi về gói cài cũ để báo cập nhật thành công.

`--launcher-only` chỉ lấy gói cài ban đầu và luôn ghi `latest_verified=false`. Tùy chọn cũ `--allow-partial` là bí danh của chế độ đó.

## Đầu ra và tiếp tục

Mặc định `C:\YostarGames\StellaResourceDownloads`; đổi bằng `--output 'D:\StellaResources'`. Snapshot chia theo khu vực, phiên bản game/resource, profile và hash manifest.

- `plan.json`: URL, checksum, dependency, manifest nguồn và dung lượng.
- `receipt.json`: trạng thái và SHA-256 từng tệp đã kiểm chứng. `complete_for_manifest` chỉ xác nhận phạm vi plan, có thể là mẫu; `incomplete` là tải dở.
- `files/`: Tables, Scripts, Videos và AssetBundles để trích xuất.
- `inputs/`: base/delta/trung gian phục vụ tái tạo và tiếp tục.

Chạy lại cùng lệnh để tiếp tục. Tệp `.part` dùng HTTP Range; nếu máy chủ trả 200 thì tải lại từ đầu. Tệp hoàn chỉnh được kiểm checksum trước khi tái sử dụng; khác checksum thì dừng để bảo toàn dữ liệu. Snapshot mới không trộn vào snapshot cũ. Dependency bản vá làm tăng dung lượng ngoài tệp cuối; công cụ báo cả hai.

Công cụ không ghi vào bản cài game. Trước khi gỡ EN, giữ riêng dự án Việt hóa vì dự án hiện nằm trong thư mục game.

## Nguồn kỹ thuật

Đường dẫn Windows được đối chiếu từ metadata client theo chế độ chỉ đọc. Cấu trúc AES-CBC/protobuf được tham khảo từ [Nebula](https://github.com/RoundNailoong/Nebula-nb); URL và checksum thực tế phải được kiểm chứng trên CDN chính thức. Không chạy mã/DLL trích xuất từ game.
