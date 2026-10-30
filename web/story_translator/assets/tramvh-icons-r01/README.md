# TramVH — Soft Sky Icons r01

Bộ asset mới dành cho web https://tramvh.doubled1302.workers.dev/, đối chiếu mã web cục bộ `web/story_translator/` ngày 31/10/2026. Hình SVG được vẽ riêng bằng mã vector, không sao chép artwork hay logo của game. Không sử dụng mô hình tạo ảnh.

## Thành phần

- 49 icon UI, mỗi icon có 3 phiên bản: `svg/light`, `svg/dark`, `svg/mono` (xem số chuẩn trong manifest.json).
- 3 sprite SVG tương ứng. ID có dạng `tram-save`, `tram-glossary`.
- PNG light/dark ở 64 và 128 px; nền trong suốt.
- 6 huy hiệu cộng đồng, mỗi huy hiệu có bản sáng/tối. Đây là asset tùy chọn; chưa gán vào cấp độ hay thành tích thật.
- Biểu tượng TramVH: sách mở + bút dịch + sao dẫn đường; 3 bản SVG nền trong suốt.
- Icon ứng dụng có nền đặc, favicon 16/32/48 và icon PWA 192/512; có vùng đệm cho safe zone maskable.
- `icons.css` là CSS chỉ có class được đặt tiền tố; `manifest.json` liệt kê asset.
- Mở `preview.html` để tìm kiếm, xem sáng/tối, đổi kích thước và xem huy hiệu. Không cần mạng.

## Dùng với cấu trúc web hiện tại

Bộ này đang ở `assets/tramvh-icons-r01/`. Đã tích hợp vào index.html, manifest.json, các view biên dịch/từ điển và điều khiển nhạc. IconView.js cung cấp hàm tramIcon(id) cho HTML động. Việc đồng bộ GitHub và kiểm tra Workers được ghi ở báo cáo tích hợp riêng.

Cách đơn giản, dùng ảnh SVG màu theo theme (không cần JavaScript):

```html
<link rel="stylesheet" href="assets/tramvh-icons-r01/icons.css">
<button type="button" aria-label="Lưu bản dịch">
  <img class="tram-icon tram-icon-light" src="assets/tramvh-icons-r01/svg/light/save.svg" alt="">
  <img class="tram-icon tram-icon-dark" src="assets/tramvh-icons-r01/svg/dark/save.svg" alt="">
</button>
```

CSS dùng đúng thuộc tính theme hiện có: `html[data-theme="dark"]`. Giữ hàm và ID của nút đang dùng; chỉ đổi phần hình bên trong. Nhãn aria-label cần nằm trên nút; icon trang trí có alt rỗng.

Dùng sprite đơn sắc để thừa hưởng màu chữ hiện tại:

```html
<button type="button" aria-label="Mở từ điển thuật ngữ">
  <svg class="tram-icon" aria-hidden="true">
    <use href="assets/tramvh-icons-r01/sprite-mono.svg#tram-glossary"></use>
  </svg>
</button>
```

Sprite ngoài cần chạy trên HTTP cùng origin; khi mở file trực tiếp, dùng SVG qua img như preview. `currentColor` chỉ thừa hưởng từ trang khi SVG inline hoặc qua use; img của bản mono mặc định màu đen, không tự đổi theo màu CSS cha.

Kích thước khuyên dùng: 20 hoặc 24 px trong nút, 32 px trong thẻ, huy hiệu 64–96 px. Giữ vùng chạm nút tối thiểu 44×44 px. Status đã duyệt/chờ/lỗi luôn đi kèm chữ, không truyền đạt chỉ bằng màu. Icon save-next dùng hình lưu + mũi tên; icon next/previous có vạch chặn để phân biệt với play.

## Gợi ý thay thế đúng chức năng

| Thành phần hiện tại | Asset |
|---|---|
| bgmToggleBtn | music / music-off |
| themeToggleBtn | moon / sun |
| openLeaderboardModal | trophy |
| openGlossaryModal | glossary |
| Mở Google Sheets | sheet hoặc external-link |
| tabGameMode / tabListMode | visual-novel / list |
| voiceJpBtn / voiceCnBtn | volume (giữ nhãn JP/CN) |
| navigateLine(-1 / 1) | previous / next |
| saveCurrentLine | save-next |
| Đồng bộ từ điển | sync |
| Kiểm token | tokens + approved/warning |

Không chèn hình vào option của select native; dùng nhãn chữ cho bộ lọc hoặc tạo custom select có hỗ trợ bàn phím trong một thay đổi riêng.

## Phạm vi kiểm chứng

Kết quả tự kiểm và hash được ghi ở QA.json/SHA256SUMS.txt sau khi xuất PNG. Xem ảnh preview-desktop.png, preview-dark.png và preview-mobile.png. Kiểm thử ở viewport di động bằng Chrome máy tính không thay thế kiểm trên điện thoại thật. Không gửi bản dịch thử lên Google Sheets. Trạng thái GitHub/Workers xem báo cáo tích hợp riêng.
