---
name: translate
description: Dịch sang tiếng Việt và cập nhật trực tiếp file _Merge.txt UI story hoặc UI tĩnh của project SS, đối chiếu CN/JP/EN và dùng glossary/glossary.csv; cập nhật hai báo cáo HTML xung đột và reference sau mỗi lần lưu tiến độ. Dùng khi người dùng yêu cầu dịch một file Merge tương ứng hoặc gọi $translate cho file đó. Không áp dụng cho dịch câu rời, tài liệu khác, file nguồn _EN/_JP/_CN hoặc yêu cầu chỉ tạo Merge.
---

# Translate

Dịch các đơn vị nội dung trong `<base>_Merge.txt` sang tiếng Việt, bổ sung nội dung VI vào chính file đó; chỉ UI story mới thêm tên VI. Giao tiếp bằng tiếng Việt. Chỉ áp dụng cho yêu cầu dịch file Merge của project SS; việc đang mở Merge trong IDE không biến một yêu cầu dịch nội dung khác thành tác vụ của skill này.

## Khi được workflow giao

Nhận file trực tiếp sau terms của bộ đó (hoặc sau merge nếu không có đề xuất),
đọc lại glossary mới nhất; không yêu cầu merger ghi lại Merge vì term vừa cập
nhật. Chỉ một translator ghi hai HTML. Agent chính có thể giao merger chuẩn bị
trước đúng một bộ khác trong khi đang dịch; merger không được sửa file đang dịch,
glossary hoặc báo cáo. Term-controller phải chờ translator kết thúc và agent
chính verify/lưu checkpoint cùng hai báo cáo; không cập nhật CSV giữa lượt dịch.
Nếu phát hiện glossary bị thay đổi ngoài lịch hoặc báo cáo lỗi, báo agent chính
và giữ dữ liệu phục hồi để kiểm tra trước khi dịch tiếp. Các quy tắc dịch/bảo
toàn và cập nhật báo cáo sau mỗi save dưới đây không thay đổi.

## Phạm vi

Ngoại lệ cho claim workflow có `review_scope.mode = glossary`: dùng `review --job <id>` của helper workflow để đọc đúng khối bị ảnh hưởng, glossary và phát hiện hiện hành; chỉ lấy ngữ cảnh liền kề khi cần. Không yêu cầu mô hình đọc lại toàn Merge hoặc toàn nhánh báo cáo. Nếu VI đã đúng thì giữ nguyên byte Merge; nếu cần sửa chỉ sửa VI/tên VI thuộc phạm vi. Cập nhật cả hai HTML cho phần vừa rà, giữ dữ liệu/phát hiện khác; receipt trả `reviewed_blocks` đúng danh sách được giao. Script vẫn kiểm tra cấu trúc/nguồn/hash/coverage toàn file. Các yêu cầu đọc toàn file bên dưới áp dụng cho dịch mới hoặc rà toàn file, không áp dụng máy móc cho lượt đồng bộ giới hạn này. Không viết lại helper hoặc chạy bộ test phát triển trong tác vụ dịch thông thường.

- Xác định file `_Merge.txt` từ yêu cầu hoặc ngữ cảnh IDE. Nếu người dùng yêu cầu dịch bản Merge của một file nguồn đang mở, xác định file cùng tên gốc, cùng thư mục. Nếu có nhiều ứng viên mà không xác định được file tương ứng, hỏi ngắn gọn để chọn đúng file.
- Kiểm tra file có cấu trúc Merge EN/JP/CN đã thống nhất. Không áp dụng chỉ vì một file bất kỳ có chữ Merge trong tên. Nếu Merge chưa tồn tại, báo thiếu file; không tự chạy merge vì thao tác đó có cơ chế kích hoạt riêng.
- Tự phân biệt UI story và UI tĩnh từ cấu trúc header, nội dung và bộ ba nguồn; tên thư mục chỉ hỗ trợ nhận diện. Nếu chưa rõ chức năng trường, tra nguồn/dữ liệu trong project trước khi kết luận. Khi người dùng không giới hạn đoạn, xử lý toàn bộ file Merge đã xác định: các đơn vị story hoặc văn bản UI tĩnh, kể cả mục chỉ có dấu câu. Không tự mở rộng sang file/chương khác.
- Đọc toàn bộ Merge, `glossary/glossary.csv` hiện tại và các mục báo cáo liên quan trước khi dịch. Đọc [quy trình và hợp đồng báo cáo](references/reports.md), dùng helper `--inspect` để xem nhánh hiện có; chưa có báo cáo thì khởi tạo cặp rỗng bằng `--init`. Có thể đọc bộ ba nguồn cùng tên gốc để phân định khối, ID, tên người nói và ngữ cảnh; không sửa chúng.
- Trước khi sửa, nêu file Merge sẽ cập nhật và phạm vi dịch. Chỉ sửa nội dung VI trong Merge, thêm/cập nhật tên VI nếu là UI story, và cập nhật hai HTML báo cáo bên dưới. Không cập nhật glossary, skill khác hoặc Google Sheets trong tác vụ dịch.

## Cấu trúc sau khi dịch

### UI story

Giữ cấu trúc và cách dịch hiện tại:

```text
1. [Tên VI/ Tên EN/ Tên JP/ Tên CN] (Loại nội dung bằng tiếng Việt)
Nội dung CN
Nội dung JP
Nội dung EN
Nội dung VI
```

- Thêm tên VI ở đầu header và bản dịch VI sau nội dung EN. Giữ nguyên thứ tự, tên EN/JP/CN, loại nội dung và toàn bộ ba phần nguồn CN/JP/EN. Không thêm nhãn `CN:`, `JP:`, `EN:`, `VI:` hoặc dấu gạch chéo ngược cuối dòng; dấu xuống dòng trong mẫu là xuống dòng thực tế.
- Giữ nguyên các header đặc biệt `[Dẫn chuyện] (Loại nội dung)` và `[Người chơi] (Loại nội dung)` từ quy tắc ID `0`, `1`. Không mở rộng chúng thành bốn tên. Vẫn thêm nội dung VI sau ba phần nguồn như bình thường.
- Với header không có người nói `[—/ —/ —]`, thêm ô tên VI là `—`, thành `[—/ —/ —/ —]`; không tự đặt tên cho tiêu đề hoặc lựa chọn.

### UI tĩnh

```text
1. [Mã giữ nguyên]
Nội dung CN
Nội dung JP
Nội dung EN
Nội dung VI
```

- Header chỉ chứa mã nguồn gốc; không dịch/ánh xạ mã, không thêm tên VI, người nói hoặc loại nội dung. Nếu header là `[EN: mã_EN/JP: mã_JP/CN: mã_CN]`, giữ nguyên toàn bộ, kể cả thứ tự, dấu câu, khoảng trắng và dấu `/` bên trong mã.
- Chỉ thêm VI sau EN, hoặc cập nhật đúng phần VI đã có khi dịch lại. Mỗi mục nguồn vẫn là một khối riêng dù trùng chữ. Dùng mã và quan hệ bản ghi đã xác minh để tra ngữ cảnh, không ghép lại hoặc đổi mã theo nội dung.
- Dịch theo chức năng UI (tên, nút, mô tả, hướng dẫn…), ưu tiên rõ và gọn nhưng đủ nghĩa; không áp xưng hô thoại hay tự đặt người nói cho chuỗi UI. Vẫn dùng glossary, đối chiếu cả ba nguồn, giữ token/thẻ và ghi hai báo cáo như UI story.

### Bảo toàn chung

- Nội dung của một ngôn ngữ có thể chiếm nhiều dòng. Nhận diện khối từ header và đối chiếu nguồn khi cần; không giả định một khối luôn có bốn hoặc năm dòng, không dùng dòng trống bên trong nội dung để cắt khối tùy tiện.
- Các biến thể giới tính đã có dấu `/` bên trong tên hoặc nội dung không phải ranh giới ngôn ngữ. Dùng dữ liệu glossary/nguồn để phân biệt, không tách mọi dấu `/` thành các cột tên.
- Khi file đã có tên VI/nội dung VI, nhận diện và cập nhật đúng phần VI trong phạm vi yêu cầu; không thêm ô tên hoặc bản dịch trùng. Giữ nguyên những phần ngoài phạm vi và các biên tập người dùng không liên quan. Chạy lại cùng tác vụ phải giữ số khối và cấu trúc hợp lệ.

## Đối chiếu và dịch

- Đọc cả CN, JP, EN của từng đơn vị và ngữ cảnh liền kề, kể cả các nhánh khác nhau. Dịch tự nhiên, đúng ý và giọng nhân vật; giữ quan hệ xưng hô nhất quán theo tình huống, không tự thêm thông tin hoặc bỏ câu.
- **Khi ba bản xung đột về nội dung, lấy EN làm căn cứ cho bản dịch VI, tiếp tục dịch rồi báo cáo xung đột cho người dùng.** Không lấy biểu quyết hai bản thắng một bản, không trộn tình tiết CN/JP vào EN để tạo nghĩa mới, không dừng để hỏi chỉ vì có xung đột đã được quy tắc này giải quyết.
- Xung đột đáng báo cáo là khác biệt làm đổi tình tiết, danh tính/đối tượng, hành động, phủ định, số lượng, quan hệ hoặc ý nghĩa câu. Diễn đạt khác nhau nhưng đồng nghĩa, khác thứ tự từ và dấu câu thông thường không phải xung đột nội dung.
- Khi ba bản không mâu thuẫn, dùng JP/CN làm rõ sắc thái, chủ ngữ lược bỏ, hàm ý và cách xưng hô; không để điều đó làm đổi ý của EN. Khi không đủ ngữ cảnh, ưu tiên cách dịch không tự suy diễn.
- `[EMPTY_SOURCE]` là nguồn rỗng, không phải câu cần dịch. Nếu EN rỗng nhưng CN/JP có nội dung thống nhất, dịch từ nội dung hiện có và báo rõ ngoại lệ nguồn. Nếu EN rỗng và các nguồn còn lại mâu thuẫn đến mức không thể chốt nghĩa, hoàn thành phần độc lập rồi hỏi về đúng đơn vị còn vướng; không bịa bản EN. Mục nguồn chỉ có dấu câu vẫn cần nội dung VI tương ứng.
- Bảo toàn thẻ định dạng, token điều khiển như `==W==`, `==RT==`, placeholder `%s`, `%d` và tên biến theo bản EN trong phần VI. Giữ cặp thẻ mở/đóng đúng, đặt quanh phần dịch tương ứng; không dịch cú pháp. Nếu khác biệt token giữa ba nguồn ảnh hưởng ý nghĩa hoặc cách hiển thị, lấy EN làm chuẩn và ghi nhận trong báo cáo.

## Chơi chữ và reference

**Rất khuyến khích chủ động phát hiện chơi chữ và reference trong bất kỳ bản EN, JP hoặc CN nào khi đối chiếu để dịch. Nếu phát hiện, báo lại cho người dùng**, kể cả khi chỉ một ngôn ngữ có chi tiết đó hoặc bản VI không thể giữ được hiệu ứng tương đương.

- Chú ý từ đồng âm/đa nghĩa, cách đọc chữ Hán hoặc kana, lối nói lái và biến tấu thành ngữ, câu đùa dựa trên tên, trích dẫn/ám chỉ tác phẩm, văn hóa đại chúng, meme hoặc sự kiện. Không gán mọi cách nói thông thường thành reference.
- Với mỗi trường hợp, ghi nhận **vị trí khối và người nói/mã UI tĩnh, ngôn ngữ phát hiện, đoạn gốc liên quan, cơ chế chơi chữ hoặc đối tượng được ám chỉ, cách xử lý trong VI**. Nêu rõ nếu hiệu ứng đã được giữ, chuyển cách diễn đạt hoặc bị mất khi dịch. Đối chiếu các bản còn lại khi chúng dùng câu đùa/reference khác hoặc bỏ chi tiết ấy.
- Phân biệt điều đã xác minh và suy đoán. Nếu chỉ nghi là reference, ghi rõ là nghi vấn và lý do; không khẳng định nguồn gốc hoặc chủ ý tác giả khi chưa có căn cứ. Khi cần xác định tác phẩm/câu trích cụ thể mà chưa chắc, kiểm chứng bằng nguồn đáng tin cậy, ưu tiên nguồn gốc/chính thức và dẫn nguồn đã dùng trong báo cáo.
- Cố gắng giữ nghĩa và hiệu ứng trong bản VI bằng cách diễn đạt tự nhiên, phù hợp ngữ cảnh và glossary. Không tự thêm một câu đùa mới hoặc sửa tình tiết chỉ để tái tạo chơi chữ. Khi phải lựa chọn, giữ nghĩa và giọng nhân vật, rồi giải thích phần hiệu ứng không chuyển được trong báo cáo.
- Quy tắc ưu tiên EN khi xung đột vẫn giữ nguyên. Reference/chơi chữ chỉ có ở JP/CN vẫn cần báo, nhưng không tự đưa thêm vào VI nếu làm đổi nghĩa hoặc thông tin của EN. Nếu các bản không mâu thuẫn, có thể dùng chi tiết này để hiểu sắc thái và chọn cách dịch phù hợp.
- Lưu reference theo từng khối trong báo cáo HTML; có thể nhắc các khối liên quan trong phần giải thích nhưng không gộp mất vị trí. Không chèn chú giải/reference vào Merge và không dừng tác vụ chỉ vì không giữ được trọn vẹn chơi chữ. Không phát hiện trong phạm vi đã rà không có nghĩa nguồn chắc chắn không có reference.

## Glossary, tên và biến thể

- Đọc CSV bằng thư viện CSV có hỗ trợ UTF-8 BOM, trường quote và xuống dòng; các cột là `id,EN,target,category,JP,CN`. Dùng dữ liệu hiện tại, không dựa vào bảng thuật ngữ nhớ từ lượt trước.
- Các dòng `category=term` quy định cách dịch chuẩn ở `target`. Áp dụng cho toàn bộ nội dung VI và phần mô tả trong tên VI. Ưu tiên cụm đầy đủ hơn thuật ngữ thành phần; xét số nhiều/sở hữu theo nghĩa, không thay chuỗi con làm sai từ khác hoặc tên riêng.
- Với UI story có tên người nói, ưu tiên dòng ánh xạ chính xác theo ID của đơn vị nguồn và lấy `target`. Nếu Merge không chứa ID, đối chiếu ba tên và nguồn để chọn đúng dòng; không lấy ngẫu nhiên dòng đầu khi một tên có nhiều ánh xạ khác nhau.
- Dùng `target` đã được quy định cho tên riêng; nếu chưa có bản đích, giữ tên riêng EN, dịch phần vai trò/mô tả theo glossary và ngữ cảnh. Giữ hậu tố phân biệt A/B/C, tên che giấu `???`, `??`, `***`; không tiết lộ danh tính thật thay cho tên đang hiển thị.
- Nếu bản dịch ánh xạ cũ chưa khớp thuật ngữ `term` hiện hành, áp dụng thuật ngữ hiện hành trong phần VI của Merge, giữ tên riêng và phần còn lại. Không tự sửa glossary trong bước này.
- Với các biến thể giới tính đã mở rộng bằng `/`, dịch đủ các trường hợp và giữ thứ tự biến thể từ bản EN. Tra dòng `SEX/<token>/<chỉ số>` và `target` tương ứng khi xác minh được token; không tự chọn một giới tính hoặc coi mọi dấu `/` là biến thể.
- Cùng mã token ở CN/JP/EN có thể mang nghĩa khác nhau. Phần VI phải bám nghĩa EN; nếu các `target` của token không phù hợp với nghĩa EN trong câu cụ thể, dịch theo EN và báo chênh lệch, không ép giá trị khác nghĩa vào câu. Bảo toàn các phần nguồn.
- Nếu thiếu thuật ngữ, dịch nhất quán theo ngữ cảnh hoặc giữ nguyên tên riêng; ghi nhận thuật ngữ mới cần chốt nếu ảnh hưởng đáng kể. Nếu glossary có bản dịch mâu thuẫn không thể chọn theo ID/ngữ cảnh, hỏi đúng phần cần quyết định; không sửa glossary hay tự kích hoạt update-term.

## Hai báo cáo HTML tích lũy

- `reports/translation-conflicts.html`: xung đột EN/JP/CN ảnh hưởng nghĩa, ngoại lệ nguồn rỗng và khác biệt token ảnh hưởng nghĩa/hiển thị. Không ghi khác biệt diễn đạt đồng nghĩa.
- `reports/translation-references.html`: chơi chữ/reference ở bất kỳ nguồn nào, đối chiếu các bản còn lại, cách xử lý trong VI; phân biệt đã xác minh với nghi vấn và ghi bằng chứng/đường dẫn khi có.
- Người dịch chịu trách nhiệm phát hiện, giải thích và lựa chọn cách xử lý. Helper `scripts/update_reports.py` chỉ tiếp nhận kết quả có cấu trúc theo [references/reports.md](references/reports.md), kiểm tra phiên bản và dựng HTML; không thay việc đọc/đối chiếu ba nguồn.
- Sau **mỗi lần lưu tiến độ Merge đã kiểm tra**, đọc lại file vừa lưu, tính SHA-256 toàn bộ byte, lập JSON tạm với đúng nguồn/VI và **mọi khối vừa rà**, gồm cả hai mảng rỗng khi không có phát hiện. Chạy `--dry-run` rồi `--input` để cập nhật **cả hai báo cáo ngay**, trước khi dịch tiếp file hoặc phạm vi khác; không đợi xong cả danh sách. JSON tạm chỉ phục vụ truyền kết quả/phục hồi, hai HTML nhúng JSON là dữ liệu báo cáo lâu dài.
- Định vị bằng đường dẫn tương đối đầy đủ theo nguyên cây thư mục tài nguyên, số khối, header và nguồn/mã đã xác minh; không dùng riêng basename/số khối. Mỗi khối có một mục trong mỗi báo cáo và có thể chứa nhiều phát hiện. Dịch lại cập nhật mục hiện hành, chỉ thay phạm vi vừa rà, giữ nhánh khác. Không còn phát hiện thì đánh dấu “không còn ở bản hiện tại”, giữ phân tích/ngữ cảnh cũ. Chưa xác định chắc vị trí mới sau đổi nguồn/đánh số thì giữ mục cũ “cần đối chiếu”, không gán bừa.
- Với bộ nguồn EN/JP/CN cố định, dịch lại toàn file thì làm mới nội dung hiện hành của toàn nhánh file trong báo cáo; dịch một phần chỉ ghi đè các khối vừa rà. Cập nhật VI và giải thích tại đúng mục, không nối thêm một bản báo cáo cho mỗi lần dịch. Phát hiện cũ không còn phù hợp vẫn giữ nhãn lịch sử theo quy tắc trên.
- Helper phải chấp nhận đúng hash Merge vừa lưu và đối chiếu chính xác nguồn/VI từng khối. Nếu bị từ chối vì dữ liệu cũ, đọc/rà lại bản mới và lập đầu vào mới; không chỉ thay hash để bỏ qua kiểm tra. Bảo toàn hiệu đính người dùng.
- Chuẩn bị, kiểm tra cả hai HTML trước khi thay thế; lưu UTF-8 BOM/CRLF và đọc lại. Nếu lỗi báo cáo, giữ Merge đã lưu, đầu vào và bản phục hồi; khắc phục cặp báo cáo trước khi dịch thêm. Không xóa báo cáo hỏng để bắt đầu lại hoặc báo hoàn tất khi thiếu một báo cáo.
- HTML tự chứa CSS, JavaScript và JSON; cây thư mục thu/mở, tìm kiếm, lọc trạng thái/mức xác minh, liên kết Merge, phạm vi và thời điểm rà. Trích nguồn giữ nguyên thẻ/token, escape khi nhúng và dựng bằng textContent để không thực thi nội dung. Trang chỉ để đọc, không tự dịch hoặc theo dõi file nền.
- Chỉ ghi nhận từ các lần dịch tiếp theo, không rà ngược Merge cũ. Chưa có dữ liệu phải ghi “chưa có dữ liệu rà”; file/khối không có phát hiện vẫn ghi nhận phạm vi đã rà, không tuyên bố toàn project không có vấn đề.

## Kiểm tra, lưu và báo cáo

- Lưu bản dữ liệu trước sửa để đối chiếu. Có thể dùng script tạm hỗ trợ kiểm tra cấu trúc và ghi file, nhưng việc dịch/đối chiếu nghĩa phải được thực hiện trên nội dung đầy đủ, không chỉ thay từ bằng từ điển.
- Kiểm tra số khối và thứ tự không đổi; mọi đơn vị trong phạm vi đều có VI, kể cả dấu câu; không thiếu nhánh hoặc tự gộp hai câu giống nhau ở hai vị trí khác nhau.
- Đối chiếu trước/sau để bảo đảm ba phần nguồn không đổi; với UI story giữ ba tên gốc, loại nội dung và header đặc biệt; với UI tĩnh giữ nguyên toàn bộ mã/header, không thêm người nói hay loại nội dung. Kiểm tra token, placeholder, cặp thẻ; thuật ngữ và tên VI nhất quán với glossary; không còn sót lời thoại EN thông thường trong phần VI ngoài tên/thuật ngữ được giữ nguyên.
- Ghi lại chính file `_Merge.txt`, giữ UTF-8 BOM, xuống dòng CRLF và một dòng trống giữa các khối. Chuẩn bị xong và kiểm tra trước khi thay thế; đọc lại file đã lưu để xác nhận. Nếu file đang bị khóa, giữ bản đã chuẩn bị và yêu cầu đóng đúng file; không đóng ứng dụng hoặc bỏ thay đổi chưa lưu thay người dùng.
- Sau khi lưu Merge, cập nhật và kiểm tra cả hai HTML theo quy trình trên. Câu trả lời cuối chỉ tóm tắt file/số khối đã dịch, kết quả kiểm tra, điểm cần chú ý hoặc thuật ngữ cần chốt và liên kết hai báo cáo; chi tiết xung đột/reference nằm trong HTML.
- Không chèn ghi chú, nhãn kiểm tra hoặc báo cáo vào Merge. Chỉ báo hoàn tất khi không còn đơn vị bắt buộc chưa xử lý và cả hai báo cáo đã lưu, đọc lại thành công. Nếu còn nguồn vướng hoặc lỗi báo cáo, nêu rõ phạm vi dở và dữ liệu đang được giữ để phục hồi.
