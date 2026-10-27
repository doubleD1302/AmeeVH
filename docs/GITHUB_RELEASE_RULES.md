# Quy tắc đặt tiêu đề và mô tả bản phát hành GitHub

Áp dụng khi agent tạo hoặc cập nhật bản phát hành trên GitHub (GitHub Release).
Đây là quy tắc trình bày do người dùng yêu cầu, cần thực hiện cùng quy trình phát hành hiện có của dự án.

## 1. Hai yêu cầu bắt buộc

1. **Tiêu đề chỉ ghi số phiên bản. Không thêm bất kỳ nội dung nào khác.**
2. **Mô tả không vượt quá 100 từ. Viết ngắn gọn, súc tích nhất có thể, tập trung vào những thay đổi đã cập nhật.**

100 từ là giới hạn tối đa, không phải mục tiêu cần viết đủ. Nếu mô tả rõ trong một hoặc hai câu, dùng một hoặc hai câu.

## 2. Phạm vi các trường

| Trường | Quy tắc |
| --- | --- |
| Tiêu đề hiển thị của Release (`title` / `name`) | Chỉ chứa số phiên bản, ví dụ `0.1.2`. |
| Mô tả của Release (`body` / release notes) | Tối đa 100 từ; chỉ tóm tắt thay đổi có ý nghĩa. |
| Tag, tên nhánh, tên file, phiên bản trong ứng dụng | Theo quy ước hiện có của dự án; phân biệt với tiêu đề hiển thị. |

Ví dụ: tag là `v0.1.2` thì tiêu đề hiển thị là `0.1.2`. Không tự đổi tag chỉ để làm giống tiêu đề.

## 3. Cách xác định và viết tiêu đề

- Lấy số phiên bản đã chốt cho bản phát hành từ yêu cầu người dùng hoặc metadata của artifact tương ứng.
- Không tự đặt hoặc tăng phiên bản chỉ để viết tiêu đề.
- Tiêu đề chỉ gồm chữ số và dấu chấm phân cách các thành phần phiên bản.
- Không thêm tiền tố `v`, `Release`, `Update`, tên dự án, tên nền tảng, ngày tháng, emoji hoặc ghi chú.
- Không thêm nội dung thay đổi hoặc trạng thái như `fix`, `hotfix`, `beta`, `candidate`, `stable` vào tiêu đề. Các thông tin phân loại phát hành được quản lý theo quy trình riêng của dự án.
- Không gộp nhiều phiên bản hoặc nhiều tiêu đề vào cùng một trường. Dùng phiên bản chung đã chốt của Release.

### Ví dụ đúng

```text
0.1.2
```

```text
1.0.0
```

### Ví dụ sai

```text
v0.1.2
Stella Sora 0.1.2
Release 0.1.2
0.1.2 - Giao diện mới
0.1.2 Android APK
0.1.2 hotfix
0.1.2 🎉
```

Nếu chưa xác định được phiên bản phát hành, đọc lại metadata và yêu cầu hiện tại trước khi điền tiêu đề. Không đoán số phiên bản từ tên một file cũ.

## 4. Cách viết mô tả

- Viết bằng tiếng Việt, giữ đầy đủ dấu.
- Chỉ nêu những thay đổi thực tế có trong artifact của phiên bản đang phát hành.
- Ưu tiên thay đổi người dùng nhận thấy: tính năng mới, lỗi được sửa, giao diện được cải thiện hoặc hành vi được thay đổi.
- Mở đầu trực tiếp bằng nội dung cập nhật; bỏ lời chào và đoạn giới thiệu.
- Dùng câu ngắn hoặc gạch đầu dòng. Mỗi dòng diễn đạt một ý chính.
- Gộp các thay đổi gần nhau thành một ý thay vì liệt kê mọi chỉnh sửa nhỏ.
- Ưu tiên khoảng 1–4 ý. Có ít thay đổi thì viết ít hơn.
- Không lặp số phiên bản hoặc tiêu đề nếu không giúp người đọc hiểu thay đổi.
- Không dùng từ quảng cáo như “đột phá”, “hoàn hảo”, “tuyệt đối”, “100%” để làm dài mô tả.
- Không kể quá trình làm việc, các phương án đã bỏ hoặc lịch sử những phiên bản cũ.
- Không đưa danh sách file dài, log build, mã băm, bảng kiểm thử hoặc chi tiết triển khai không cần thiết vào mô tả. Lưu chúng trong báo cáo kỹ thuật của dự án.
- Không khẳng định đã kiểm thử, hoạt động thành công trên thiết bị hoặc phát hành công khai nếu chưa có bằng chứng tương ứng.

### Ví dụ mô tả hợp lệ

```markdown
- Làm mới giao diện Android theo phong cách anime healing.
- Thêm icon pastel, nút bo tròn và font dễ đọc.
- Thu gọn bố cục, sửa chữ nhạt và thông báo lặp.
```

Ví dụ trên minh hoạ cách viết. Khi phát hành thật, thay bằng những thay đổi đã xác minh của phiên bản đó.

## 5. Cách đếm giới hạn 100 từ

Để kiểm tra nhất quán, đếm các đơn vị được phân tách bằng khoảng trắng hoặc xuống dòng trong toàn bộ mô tả.

- Tính cả nội dung trong tiêu đề phụ, gạch đầu dòng, liên kết hoặc ghi chú nếu có trong phần mô tả.
- Dấu `-` đứng riêng trong Markdown cũng được tính khi dùng cách đếm này. Đây là cách đếm bảo thủ để không vượt giới hạn.
- Không ghép từ bằng dấu gạch dưới hoặc dấu nối để lách giới hạn.
- Nếu quá 100 từ, bỏ ý phụ và viết lại câu ngắn hơn. Không cắt ngang câu hoặc làm sai nghĩa để giảm số từ.

Kiểm tra nhanh bằng Python:

```python
import re

def validate_release_text(title: str, body: str) -> tuple[str, str]:
    title = title.strip()
    body = body.strip()

    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", title):
        raise ValueError("Tiêu đề chỉ được chứa số phiên bản, ví dụ 0.1.2.")

    word_count = len(body.split())
    if word_count == 0:
        raise ValueError("Mô tả cần nêu nội dung cập nhật.")
    if word_count > 100:
        raise ValueError(f"Mô tả có {word_count} từ, vượt giới hạn 100 từ.")

    return title, body
```

Kiểm tra định dạng và số từ không thay thế việc đọc lại nội dung để xác nhận các thay đổi là đúng.

## 6. Trình tự agent thực hiện

1. Xác định đúng artifact, phiên bản và những thay đổi của lần phát hành này.
2. Điền tiêu đề chỉ bằng số phiên bản đã chốt.
3. Chọn các thay đổi quan trọng nhất, viết mô tả ngắn nhất vẫn đủ rõ.
4. Kiểm tra tiêu đề, đếm số từ và đọc lại nội dung.
5. Dùng nguyên văn tiêu đề và mô tả đã kiểm tra khi thực hiện bước phát hành được giao.
6. Sau khi tạo hoặc cập nhật Release, đọc lại nội dung thực tế trên GitHub để bảo đảm đúng tiêu đề và giới hạn mô tả.

## 7. Checklist khi phát hành

- [ ] Đúng phiên bản của artifact đang phát hành.
- [ ] Tiêu đề chỉ chứa số phiên bản.
- [ ] Không có tiền tố, tên dự án, nền tảng, ngày tháng, emoji hoặc chú thích trong tiêu đề.
- [ ] Mô tả có nội dung và không vượt quá 100 từ.
- [ ] Mô tả chỉ nêu những thay đổi thực tế của phiên bản này.
- [ ] Câu chữ ngắn, rõ, không lặp hoặc quảng cáo.
- [ ] Không có khẳng định kiểm thử/thành công chưa được chứng minh.
- [ ] Sau khi ghi: nội dung thực tế trên GitHub đã được đọc lại.

**Nguyên tắc chốt: Tiêu đề = số phiên bản. Mô tả = những gì đã cập nhật, ngắn gọn nhất có thể và tối đa 100 từ.**
