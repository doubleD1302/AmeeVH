# Font tiếng Việt và kiểm tra trong game

Bản cài có bundle `font.unity3d` và thư viện TextMeshPro; chưa kiểm tra glyph hoặc cách UI chọn font. Font TTF hỗ trợ tiếng Việt chưa đủ chứng minh TMP atlas/fallback trong game có thể hiển thị.

## Corpus kiểm tra

Dùng `templates/VI_GLYPH_TEST.txt`: chữ hoa/thường, dấu kép, Đ/đ, dấu câu, số và dòng mẫu dài. Trích thêm mọi codepoint từ text_vi để so với font/atlas thực, không chỉ xem một câu “Xin chào”. Nếu gặp NFC/NFD từ nguồn ngoài, chuẩn hóa dữ liệu VI trước khi kiểm glyph.

## Quy trình

1. Xác định bundle font thực ứng với phiên bản cập nhật; ghi SHA256 trước khi đọc. Không mặc định lấy bundle cài sẵn khi Persistent_Store có bản khác.
2. Đọc Font/TMP_FontAsset, atlas/material, fallback chain và reference từ UI. Không thay trực tiếp cả `font.unity3d` bằng một TTF.
3. Kiểm font license khi bổ sung font; giữ chứng từ license nếu phân phối. Không đổi font người dùng chọn nếu chưa có lý do từ glyph/layout.
4. Build trên staging đúng phiên bản Unity/target và kiểm reference/readback. Giữ các glyph gốc mà game còn dùng.
5. Kiểm trong game khi được giao bước runtime: menu, settings, dialog, tooltip, mô tả dài, lựa chọn hội thoại, subtitle JPVA/CNVA, số có màu, text nhỏ/đậm/nghiêng, mỗi chế độ phân giải hiện có cần hỗ trợ.
6. Ghi ảnh/video với build hash, màn hình/cảnh, expected/actual và lỗi dấu/tràn khung/tốc độ đọc. Nếu thiếu môi trường/chưa chạy game, giữ not_tested.

TMP có cơ chế fallback font; việc game cụ thể dùng cơ chế nào cần xác minh, không suy từ tài liệu API. Nguồn kỹ thuật: `docs/REFERENCES.md`.
