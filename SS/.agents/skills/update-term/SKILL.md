---
name: update-term
description: Cập nhật thuật ngữ trong glossary/glossary.csv của project SS và đồng bộ bản dịch của các ánh xạ phía sau theo bảng thuật ngữ. Dùng khi người dùng ra lệnh cập nhật thuật ngữ, thêm thuật ngữ, đổi cách dịch thuật ngữ hoặc gọi $update-term; cũng dùng khi skill merge chuyển thuật ngữ mới đủ căn cứ từ bộ ba nguồn hợp lệ theo quyền tự cập nhật đã được cho phép.
---

# Update term

Cập nhật `glossary/glossary.csv` tính từ gốc project SS. Giao tiếp bằng tiếng Việt. Đọc file hiện tại mỗi lần chạy; bản trong project là nguồn quyết định, không lấy bản tạm hoặc lịch sử hội thoại ghi đè chỉnh sửa mới của người dùng.

## Khi được workflow giao

Chỉ nhận danh sách từ agent chính sau checkpoint merge hợp lệ và khi không có
merger, translator hoặc verify nào đang hoạt động. Merger chuẩn bị xong bộ kế
tiếp không tự mở quyền cập nhật glossary: phải chờ translator bộ trước kết thúc
và agent chính kiểm tra/lưu checkpoint cùng hai báo cáo. Đọc CSV mới nhất, xử lý
theo quy tắc dưới đây và trả outcome added/existing/unresolved cho từng đề xuất.
Không sửa Merge; sau terms, translator đọc CSV mới và dịch trực tiếp, không yêu
cầu gọi lại merger chỉ vì target VI/ánh xạ VI đổi. Lệnh update-term/merge riêng
vẫn dùng quy trình thông thường, không tự khởi chạy workflow.

## Nhận đề xuất tự động từ merge

- Skill `merge` được phép gọi `update-term` sau khi đã kiểm tra đủ ba file EN/JP/CN hợp lệ và thông báo đề xuất cho người dùng. Không nhận ứng viên tự động từ bộ thiếu file hoặc có cảnh báo lỗi ngôn ngữ; nếu chưa có kết quả kiểm tra đầu vào, yêu cầu bước đó được thực hiện trước.
- Đọc danh sách EN, JP/CN đã xác minh, vị trí nguồn và ngữ cảnh do `merge` cung cấp; kiểm tra lại nguồn liên quan khi cần. **`update-term` là bên dịch/chọn target VI** theo ngữ cảnh, AGENTS.md và glossary hiện tại. Đây là yêu cầu được phép tự dịch và lưu, không cần hỏi duyệt target trước khi thêm term mới đủ căn cứ.
- Chỉ xử lý ứng viên đủ căn cứ về nghĩa/khái niệm. Nếu còn mơ hồ, trả lại ứng viên và lý do chưa cập nhật; không bịa cách dịch hoặc đối ứng JP/CN. Không tự mở rộng sang các term ngoài danh sách được chuyển.
- Khi gọi tự động, term đã tồn tại được dùng theo target hiện hành; không tự đổi bản dịch người dùng đã chốt, không tạo dòng trùng hoặc tự bổ sung/sửa JP/CN của dòng đã có. Quyền sửa các dòng term hiện có theo yêu cầu trực tiếp của người dùng vẫn như quy trình bên dưới.
- Sau lưu, trả cho `merge` kết quả term thêm/bỏ qua/chưa cập nhật và số ánh xạ được đồng bộ, để `merge` đọc lại glossary rồi kiểm tra đầu ra. Không tự sửa các file Merge hoặc nguồn, không gọi skill dịch nội dung và không push Google Sheets.

## Cấu trúc và phạm vi

Giữ đúng sáu cột và thứ tự:

```csv
id,EN,target,category,JP,CN
```

- Các dòng `category=term` định nghĩa thuật ngữ chuẩn. `target` là cách dịch hoặc cách giữ nguyên đã được chọn.
- Các dòng phía sau là ánh xạ nhân vật, biến thể giới tính và chữ giao diện. Chỉ cập nhật `target` của các dòng này khi cần đồng bộ thuật ngữ.
- ID của dòng thuật ngữ có thể trống. ID của ánh xạ phải được giữ nguyên, kể cả `0`, `1` và các đường dẫn như `SEX/==SEX5==/0`.
- Tên riêng giữ nguyên, trừ khi người dùng quy định cách dịch cho chính tên đó. Phần mô tả đi kèm tên vẫn phải tuân theo thuật ngữ.
- Không sửa file nguồn EN/JP/CN, thêm cột hay chuyển sang XLSX nếu không được yêu cầu.

## Cập nhật thuật ngữ

1. Đọc yêu cầu và bảng hiện tại. Trước khi sửa, nói ngắn gọn thuật ngữ nào sẽ đổi và sẽ đồng bộ các ánh xạ liên quan trong `glossary/glossary.csv`.
2. Dùng `EN` làm khóa đối chiếu thuật ngữ; bỏ qua khoảng trắng thừa ở hai đầu khi tìm. Kiểm tra khác biệt hoa/thường để tránh tạo dòng trùng ngoài ý muốn, nhưng không tự gộp những mục có nghĩa hoặc cách viết chủ ý khác nhau.
3. Với yêu cầu cập nhật trực tiếp của người dùng, nếu thuật ngữ đã tồn tại, cập nhật dòng đó tại vị trí hiện tại; với đề xuất tự động từ `merge`, giữ dòng hiện hành và báo đã có. Nếu có nhiều dòng trùng với bản dịch mâu thuẫn mà yêu cầu không giải quyết được, hỏi ngắn gọn về phần mâu thuẫn trước khi sửa phần phụ thuộc; không tự chọn một bản để tiếp tục đồng bộ.
4. Nếu là thuật ngữ mới, chèn **ngay sau dòng `term` cuối cùng**, trước các ánh xạ phía sau. Thêm nhiều thuật ngữ theo thứ tự người dùng đưa ra hoặc thứ tự đề xuất đã thông báo từ `merge`. Nếu chưa có `term`, chèn ngay sau dòng tiêu đề. Không sắp xếp lại các dòng khác.
5. Với dòng mới, đặt `category=term`, `id` trống trừ khi người dùng cung cấp ID. Ghi cách dịch được yêu cầu vào `target`. Nếu người dùng yêu cầu tự dịch hoặc `merge` chuyển ứng viên theo quyền tự cập nhật ở trên, tự dịch target VI theo ngữ cảnh; giữ tên riêng. Nếu là yêu cầu trực tiếp chưa có cách dịch và không được yêu cầu tự chọn, hỏi về cách dịch cần chốt.
6. Giữ nguyên EN/JP/CN của dòng đã có, trừ khi người dùng yêu cầu sửa chúng. Với dòng mới, chỉ điền JP/CN khi có dữ liệu đối chiếu chắc chắn; nếu không thì để trống. Không tự suy ra các ngôn ngữ là cùng một nghĩa chỉ vì chung ID token.

## Đồng bộ các ánh xạ phía sau

Sau mỗi lần cập nhật, rà **toàn bộ ánh xạ sau khối thuật ngữ** theo toàn bộ bảng `term` hiện hành. Dùng EN và ngữ cảnh JP/CN để nhận diện nghĩa; dùng `target` của thuật ngữ làm chuẩn cho bản dịch Việt. Bảo toàn cách xử lý cụ thể người dùng đã chốt cho một ánh xạ; không sửa ngược quyết định đó bằng thay thế thuật ngữ máy móc.

- Xét cả thuật ngữ đứng riêng, số nhiều, sở hữu và cụm ghép. Ví dụ, cập nhật `Trekker` phải rà cả `Trekkers in Queue`, `Trekker Association Clerk` và `Pink-haired Trekker`.
- Phát hiện cả bản dịch cũ không còn giống chữ EN. Không chỉ thay chữ EN trong `target`; nếu ánh xạ vẫn dùng cách dịch cũ, sửa phần tương ứng sang thuật ngữ mới.
- Khi các thuật ngữ lồng nhau, ưu tiên cụm đầy đủ, cụ thể hơn. Ví dụ `Soul Stone` phải được xét trước `Stone`; không thay từng từ làm hỏng thuật ngữ ghép.
- Không thay theo chuỗi con tùy tiện. `Grace` không tự động khớp `Graceful Lady`. Một từ tiếng Anh cũng có thể là tên riêng, như `Firefly`; giữ tên khi ngữ cảnh xác định đó là nhân vật và bảng thuật ngữ không có chỉ dẫn đổi tên ấy.
- Với một tên riêng kèm vai trò, cập nhật phần vai trò nhưng bảo toàn tên và hậu tố phân biệt A/B/C. Điều chỉnh trật tự từ cho tự nhiên mà vẫn dùng đúng thuật ngữ đã chốt.
- Không sửa `id`, `EN`, `category`, `JP`, `CN` của ánh xạ. Bảo toàn token, thẻ, `%s`, `%d`, dấu xuống dòng có chủ ý và nội dung không liên quan. Không điền bản dịch cho `[EMPTY_SOURCE]`.
- Nếu một nghĩa chưa rõ, đọc nguồn liên quan trong project để phân biệt trước. Chỉ hỏi khi thiếu thông tin thực sự quyết định cách áp dụng; không thay đồng loạt bằng phỏng đoán.

## Lưu và kiểm tra

- Đọc/ghi bằng thư viện xử lý CSV, không tách dòng bằng dấu phẩy thủ công. Lưu **UTF-8 BOM, dấu phẩy phân cách, xuống dòng CRLF**, quote đúng các trường chứa dấu phẩy, dấu nháy hoặc xuống dòng.
- Trên PowerShell, không pipe script chứa chữ VI/JP/CN qua stdin của Python;
  dùng file script UTF-8 hoặc chuỗi escape Unicode. Đọc lại từng ô mới để phát
  hiện mất chữ thành dấu `?` trước khi bàn giao cho bước dịch.
- Nếu file không còn là UTF-8 hoặc bị Excel đổi dấu phân cách, xác định định dạng thực tế trước. Không đọc với chế độ bỏ lỗi rồi lưu mất chữ. Nếu đã mất ký tự, khôi phục từ nguồn/bản xác thực và giữ các chỉnh sửa của người dùng; không đoán những phần không thể khôi phục chắc chắn.
- Chuẩn bị kết quả và kiểm tra trước khi thay thế file. Nếu ứng dụng đang khóa file, giữ bản đã chuẩn bị, yêu cầu người dùng đóng file rồi thử lưu lại. Không đóng ứng dụng hay loại bỏ thay đổi chưa lưu của người dùng.
- Đọc lại file đã lưu và kiểm tra: đúng sáu cột, Unicode còn nguyên; số dòng tăng đúng số thuật ngữ mới; thuật ngữ mới nằm sau `term` cuối; thứ tự và ID các ánh xạ không đổi; chỉ các ô được yêu cầu hoặc cần đồng bộ mới thay đổi; placeholder/token còn nguyên.
- Rà lại các ánh xạ có chứa thuật ngữ, gồm dạng biến đổi và cụm ghép, để xác nhận không sót cách dịch cũ hoặc thay nhầm nghĩa. Chạy lại cùng yêu cầu không được tạo thêm thuật ngữ trùng.
- Báo ngắn gọn số thuật ngữ thêm/sửa và số ánh xạ đã đồng bộ, kèm liên kết `glossary/glossary.csv`. Chỉ báo hoàn tất sau khi đã lưu và kiểm tra thành công.
