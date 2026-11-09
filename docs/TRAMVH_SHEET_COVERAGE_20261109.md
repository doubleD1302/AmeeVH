# Coverage đối chiếu Sheet của TramVH

Snapshot đọc trực tiếp workbook `13ooFrJLyeP9LsSFrkzp4SWpQY5ePd6ap5muvWCwWOdM` ngày 09/11/2026 bằng cùng parser Worker. Đây là bằng chứng kiểm tra nguồn, chưa phải bằng chứng đã triển khai production.

| Chương | Tổng dòng web | Ghép an toàn | CN có giá trị | JP có giá trị | VI tham khảo |
|---|---:|---:|---:|---:|---:|
| Chương 0 | 121 | 91 | 91 | 91 | 91 |
| Chương 1 | 1.303 | 1.275 | 1.026 | 484 | 6 |
| Chương 2 | 1.503 | 1.081 | 823 | 829 | 0 |
| Chương 3 | 1.897 | 1.870 | 1.555 | 642 | 2 |
| Chương 4 | 2.152 | 2.130 | 1.595 | 846 | 0 |
| Chương 5 | 2.125 | 2.104 | 1.671 | 1.248 | 0 |
| Chương 6 | 3.533 | 3.489 | 2.752 | 1.791 | 0 |
| Chương 7 | 3.005 | 2.981 | 2.253 | 573 | 0 |
| Chương 8 | 3.789 | 3.714 | 2.666 | 486 | 0 |
| Chương 9 | 3.540 | 3.464 | 2.489 | 89 | 0 |
| Cốt truyện sự kiện | 10.861 | 10.728 | 7.916 | 5.077 | 0 |
| Hẹn hò nhân vật | 305 | 305 | 303 | 303 | 1 |
| Kịch bản Ký Ức (CG) | 14.275 | 14.070 | 10.839 | 9.051 | 0 |
| Ngoại truyện | 5.712 | 5.649 | 4.244 | 3.270 | 0 |
| Tin nhắn điện thoại | 8.773 | 8.653 | 8.094 | 4.433 | 0 |
| Ủy thác hội quán | 455 | 452 | 415 | 431 | 0 |
| **Tổng** | **63.349** | **62.056** | **48.732** | **29.644** | **100** |

Ghép an toàn chỉ được tính khi có khóa phù hợp và EN trùng chính xác; dòng có ID trùng, EN khác hoặc không có cặp tương ứng bị bỏ qua. Chương 0 dùng tab Merge `Chuong_STm00` và ghép theo `file_id` + EN duy nhất trong file. Các cột CN/JP trống trên Sheet vẫn được giữ trống trên web. VI trong bảng là tham khảo Sheet; bản VI cộng tác, revision, trạng thái và đề xuất vẫn lấy từ D1.

Glossary đọc được 1.101 dòng hợp lệ. Cột ghi chú/D trong Google Visualization hiện trống dù một số giá trị nguồn/ID vẫn có ở cột H; không coi ghi chú glossary là đã đồng bộ đầy đủ.
