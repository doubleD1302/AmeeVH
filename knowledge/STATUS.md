# Trạng thái tri thức chatbot

File này do `build_knowledge.py` tự sinh, đừng sửa tay. Chatbot chỉ có tri thức về phần **đã Việt hóa**; phần còn lại cần nói rõ là chưa có dữ liệu.

- Tài liệu (docs): **1000**, khối: **111723**, chunk: **9366** (chưa tính thuật ngữ)
- Thuật ngữ nạp vào: **726** mục

## Độ phủ luồng Merge (bản dịch đã review)

Chỉ tính các file Merge trong dự án Việt hóa SS; phần bản Việt hóa đang chạy trong game (gói arcx) xem các mục bên dưới.

| Nhóm | Đơn vị nguồn | Đã dịch | Dịch dở | Merge chưa dịch | Chưa merge | Phủ |
|---|--:|--:|--:|--:|--:|--:|
| `01_CotTruyen` — Cốt truyện, sự kiện, ngoại truyện | 412 | 28 | 0 | 1 | 383 | 6.8% |
| `02_NhanVat` — Hồ sơ, giọng và dữ liệu nhân vật | 693 | 0 | 0 | 0 | 693 | 0.0% |
| `03_BangText_UI_KyNang` — Vật phẩm, kỹ năng, nhiệm vụ, giao diện | 239 | 1 | 0 | 0 | 238 | 0.4% |
| `04_PhuDeVideo` — Phụ đề video | 9 | 0 | 0 | 0 | 9 | 0.0% |
| `90_CN_Moi_2.0.1` — Nhóm khóa bổ sung 2.0.1 | 8 | 0 | 0 | 0 | 8 | 0.0% |

## Độ phủ luồng Merge theo nhóm (chỉ nhóm đã có Merge)

| Nhóm | Đơn vị nguồn | Đã dịch | Dịch dở | Merge chưa dịch | Chưa merge | Phủ |
|---|--:|--:|--:|--:|--:|--:|
| `01_CotTruyen` / `Chuong_STm00` | 2 | 2 | 0 | 0 | 0 | 100.0% |
| `01_CotTruyen` / `Chuong_STm01` | 12 | 12 | 0 | 0 | 0 | 100.0% |
| `01_CotTruyen` / `Chuong_STm02` | 14 | 14 | 0 | 0 | 0 | 100.0% |
| `01_CotTruyen` / `Chuong_STm03` | 15 | 0 | 0 | 1 | 14 | 0.0% |
| `03_BangText_UI_KyNang` / `03_BangText_UI_KyNang` | 239 | 1 | 0 | 0 | 238 | 0.4% |

## Bản Việt hóa đang chạy trong game (gói arcx)

Nguồn: `lua_patched_vi.arcx` (2867 mục), `data_patched_vi.arcx` (1048 mục) trong `dist/` của dự án patch AmeeVH — văn bản tiếng Việt thực tế người chơi thấy. Cảnh/bảng đã có trong Merge (đã review) thì dùng Merge, không lặp lại ở đây.

- Cảnh AVG: **629** nạp / 657 cảnh trong gói (28 cảnh dùng bản Merge)
- Bảng text: **244** bảng, 40639 chuỗi tiếng Việt

## Bản Việt hóa trong patch (dự án AmeeVH)

Nguồn: 2 bản tổng hợp `delivery/*/Van_ban_EN_VI.jsonl` cộng 3 file `hotfix_*` (602 dòng ghi đè/bổ sung). Trường `status` trong dữ liệu gốc ghi "Bản nháp" (chưa thấy ghi nhận review độc lập); dòng giữ nguyên EN không được nạp.

| Phiên bản | Loại nội dung | Tài liệu | Dòng nguồn | Có VI | Giữ EN | Chưa có VI |
|---|---|--:|--:|--:|--:|--:|
| 2.1.0 | Bảng khác | 95 | 201 | 201 | 0 | 0 |
| 2.1.0 | Danh bạ | 1 | 4 | 2 | 2 | 0 |
| 2.1.0 | Tên người nói | 1 | 18 | 4 | 14 | 0 |

## Merge đã có nhưng chưa dịch xong (chưa nạp)

- `01_CotTruyen/01_Chinh/Chuong_STm03/STm03_04/STm03_04_Merge.txt`

## Cảnh báo

- hotfix: 61 dòng không có trong delivery nên không nạp

_Cập nhật lần cuối: 2026-11-15T01:29:35+00:00_
