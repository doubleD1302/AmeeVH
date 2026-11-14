# Stella Sora — tài nguyên EN–JP–CN

Đây là bộ tổng hợp chung trong một folder. Mở DANH_MUC_EN_JP_CN.csv để tìm. Mỗi folder nội dung chứa ba file EN, JP, CN; nếu không có nguồn tương ứng thì file ghi rõ trạng thái.

- 01_CotTruyen: cảnh truyện, sự kiện và nội dung liên quan.
- 02_NhanVat: hồ sơ, giọng và dữ liệu nhân vật.
- 03_BangText_UI_KyNang: bảng UI, kỹ năng, vật phẩm và preset.
- 04_PhuDeVideo: phụ đề để đọc.
- 05_Lua: 379 file Lua có chuỗi ứng viên, phân theo đường dẫn gốc; mỗi folder có ba file. Nhãn chỉ rõ 24 vị trí được truy vết tĩnh tới UI và các mục chưa xác nhận; còn lẫn log, mã kỹ thuật, test/editor.
- 90_CN_Moi_2.0.1: nhóm khóa bổ sung; nay có nguồn EN 2.0.1 đã khôi phục.
- 99_DuLieuGoc và 99_DuLieuGoc_EN: dữ liệu thô, hằng Lua, bảng, cảnh, giọng, preset và SRT.

Ba phụ đề EN CH04ED và Prologue JPVA/CNVA đã sửa: r02 lấy nhầm bản VI từ Persistent_Store; bộ này lấy EN từ InstallResource có hash ghi trong MANIFEST.json. Các timestamp giữ theo nguồn. Chưa xác minh ưu tiên tải thực tế.

Nguồn EN/JP/CN là client 2.0.1; ghép theo ID, không giả định nội dung cùng vị trí luôn tương đương. [KHÔNG CÓ KHÓA...] là thông báo, không phải text game. Còn chữ trong ảnh/video, dữ liệu server và các payload nhị phân chưa phân tích; không thể khẳng định toàn bộ chữ hiển thị đã được trích. Runtime chưa kiểm.
