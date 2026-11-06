# Hướng dẫn làm việc trong project SS

## Phạm vi và quy trình

- Giao tiếp với người dùng bằng tiếng Việt.
- Đây là project đối chiếu và Việt hóa nội dung Stella Sora từ EN, JP, CN.
- Chỉ sửa những file thuộc phạm vi yêu cầu. Trước khi sửa, nêu ngắn gọn
  file và nội dung sẽ thay đổi.
- Dùng skill merge khi người dùng ra lệnh merge; dùng skill translate
  khi dịch file Merge; dùng update-term khi được yêu cầu cập nhật thuật ngữ.
- Không tự nối các bước merge, cập nhật thuật ngữ và dịch thành một tác vụ
  nếu người dùng chưa yêu cầu các bước đó. Ngoại lệ đã được cho phép: merge
  thông báo thuật ngữ mới đủ căn cứ rồi tự gọi update-term để skill đó dịch
  target VI, lưu glossary và đồng bộ ánh xạ; merge đọc lại glossary sau cập nhật.
  Ngoại lệ này không cho phép tự dịch nội dung Merge hoặc push Google Sheets.
- Khi người dùng yêu cầu chạy/tiếp tục workflow cho phạm vi nguồn cụ thể,
  dùng skill `.agents/skills/workflow/SKILL.md`: agent chính điều phối sub-agent
  `merger` → `term-controller` (nếu có đề xuất) → `translator` → kiểm tra/lưu tiến
  độ. Không có inspect riêng; merger kiểm tra nguồn/UI/glossary trong lượt merge,
  ghi Merge rồi trả đề xuất, không chờ term để quay lại ghi Merge lần hai.
  Đây là ngoại lệ theo yêu cầu workflow, không áp dụng cho lệnh riêng lẻ hoặc
  yêu cầu chỉ tạo/cấu hình workflow. Lưu queue/checkpoint ở `.ss-workflow/state.json`.
  Khi translator A bắt đầu, merger được merge trước đúng một bộ B trên file khác.
  Nếu B xong sớm, giữ đề xuất chờ; chưa giao term-controller hoặc merge C.
  Chỉ sau khi A dịch xong, agent chính kiểm tra/lưu checkpoint và hai báo cáo,
  đồng thời merger B đã dừng, mới xử lý term B. Term-controller ghi glossary độc
  quyền, không chạy cùng merger/translator/verify; translator B đọc glossary mới,
  bắt đầu dịch rồi merger mới nhận C. Chỉ một merger, một translator đồng thời;
  hai HTML chỉ một translator ghi. Giữ hiệu đính, không mở rộng scope hoặc push
  Sheets. Lỗi báo cáo phải khắc phục trước khi xử lý term/dịch tiếp. Chỉ tiếp tục
  run cũ khi xác minh coordinator/worker cũ đã dừng.
- Trong workflow, bàn giao bằng đường dẫn cấu hình vai trò/skill, claim/receipt, phạm vi và lưu ý riêng; worker tự đọc hướng dẫn, không chép lại toàn bộ vào tin giao việc. Khi chỉ glossary thay đổi ở bản đã dịch, dùng `review_scope` của helper để translator và parent rà đúng khối ảnh hưởng cùng ngữ cảnh cần thiết; VI đã đúng thì xác nhận, giữ nguyên Merge. Hai báo cáo chỉ cập nhật phần vừa rà; script vẫn kiểm tra toàn bộ cấu trúc/nguồn/hash/coverage. Dịch mới giữ trách nhiệm reviewer hiện tại. Chỉ sửa/kiểm thử mã helper khi cập nhật workflow hoặc sửa lỗi, không lặp việc đó mỗi tác vụ.
- Không commit hoặc push khi chưa được cho phép.

## Kiểm tra nguồn và loại UI khi merge

- Chỉ merge bộ có đủ ba file EN/JP/CN cùng tên gốc, đọc được và đúng ngôn ngữ
  khai báo nếu có. Thiếu một file hoặc bất kỳ file nào có cảnh báo lỗi ngôn ngữ,
  kể cả `[KHÔNG CÓ KHÓA TRONG NGUỒN ...]` trong một mục, đều chặn cả bộ:
  không tạo/cập nhật Merge, không gọi update-term từ bộ đó; giữ nguyên Merge cũ.
  Tác vụ nhiều bộ tiếp tục các bộ hợp lệ và báo riêng từng bộ bị chặn.
- Phân biệt cảnh báo thiếu/lỗi nguồn với chữ Error/Warning trong nội dung game
  hoặc tên khóa. `[EMPTY_SOURCE]` có chủ ý ở một trường không tự động là lỗi.
- Skill merge tự nhận diện UI story/UI tĩnh qua cấu trúc và chức năng trường.
  Story giữ header người nói và loại nội dung; UI tĩnh dùng mã nguồn trong header,
  không có người nói/loại nội dung. Cả hai giữ thứ tự nội dung CN/JP/EN.
  Mỗi mục nguồn là một khối, không gộp chỉ vì trùng chữ; tham chiếu nguồn của
  UI tĩnh không bị dịch hoặc thay bằng giá trị glossary.

## Đồng bộ Google Sheets

- Chỉ push nội dung Merge đã được dịch khi người dùng yêu cầu đồng bộ.
- Khi người dùng yêu cầu cập nhật hoặc đồng bộ sheet database, dùng skill
  `.agents/skills/update-sheet/SKILL.md` để phát hiện file mới/thay đổi, ghi đúng
  phạm vi và xác nhận readback. Không tự gọi sau merge, translate hoặc workflow.
- Các trang dữ liệu dùng cố định 12 cột theo thứ tự:
  `file_id`, `block_order`, `kind`, `speaker_en`, `speaker_jp`, `speaker_cn`,
  `speaker_vi`, `text_vi`, `text_cn`, `text_jp`, `text_en`, `source_refs_json`.
  Giữ `speaker_vi` và `text_vi` đứng cạnh nhau trong mọi lần xuất và push sau.
- Không có cột `block_id`; xác định block bằng cặp `file_id`, `block_order`.
- `DB_Proposals` dùng sáu cột: `file_id`, `block_order`, `author_id`,
  `author_name`, `new_text`, `note`. Khóa đề xuất là
  `(file_id, block_order, author_id)`; `block_order` là số.
  Không dùng `session_id`, `block_id`, `base_block_revision`,
  `proposal_revision`, `updated_at`. Không tái tạo các trang đã bỏ:
  `DB_Scenes`, `DB_Blocks`, `DB_Control` nếu chưa có yêu cầu mới.
- UI story để trống `source_refs_json`. UI tĩnh để trống `kind` và cả bốn cột
  `speaker_*`. Phân biệt hai loại khi xử lý Merge.

## Bối cảnh thế giới

- Thế giới fantasy phép thuật, pha lẫn các thuật ngữ tư bản: Ma vương,
  thần linh, đế quốc, Thánh vật cùng tồn tại với công ty, tổng giám đốc,
  nhân viên, thực tập sinh, hợp đồng, khoản vay, lãi suất và tiền công.
- Giữ sự pha trộn này trong bản dịch. Chức danh và hoạt động kinh doanh
  dùng từ rõ ràng, chính xác; phép thuật, danh xưng và quan hệ quyền lực
  vẫn mang sắc thái fantasy phù hợp với cảnh.
- Một tổng giám đốc có thể nói bằng giọng bề trên “ta/ngươi” nếu cách hành xử
  và vị thế trong cảnh hỗ trợ. Chọn giọng theo nhân vật, thay vì áp một giọng
  công sở hiện đại hoặc cổ trang cho toàn bộ thế giới.

## Nguồn và bản hiệu đính

- Luôn đọc phiên bản hiện tại của file trước khi làm việc.
- Giữ nguyên bản nguồn EN, JP, CN khi merge hoặc dịch.
- Các chỉnh sửa thủ công của người dùng trong phần VI phải được bảo toàn.
  Không dùng bản tạm hoặc bản dịch cũ ghi đè các chỉnh sửa mới.
- Dùng những câu đã được người dùng hiệu đính làm tham chiếu văn phong.
  Không biến một sửa đổi cục bộ thành quy tắc thay thế toàn project.
- Đối chiếu cả ba ngôn ngữ. Khi nội dung mâu thuẫn, dịch theo EN và báo lại;
  không trộn các tình tiết khác nhau thành một bản dịch mới.
- Quy tắc ưu tiên EN áp dụng khi chưa có quyết định hiệu đính của người dùng
  tại vị trí đó. Giữ cách xử lý người dùng đã chốt, kể cả khi khác EN;
  không tự sửa ngược trong lần dịch hoặc đồng bộ sau và không suy rộng
  ngoại lệ sang những đoạn khác.

## Văn phong và xưng hô

- Trước khi dịch, xét ai đang nói với ai, hoàn cảnh, mục đích, tính cách,
  vị thế và quan hệ giữa các bên. Từ đó chọn từ ngữ, nhịp câu và xưng hô.
  Có thể suy đoán từ lời thoại, hành động, chức vụ và diễn biến; phân biệt
  lựa chọn diễn đạt hợp ngữ cảnh với thông tin đã được xác nhận về nhân vật.
- Viết như lời thoại tiếng Việt tự nhiên: rõ ý, gọn, có khẩu khí và dễ đọc.
- Trong cảnh thân tình, ưu tiên lời cảm ơn, quan tâm hoặc thừa nhận tình cảm
  giản dị, đúng khẩu khí nhân vật. Không tự nâng thành lời thề, lời mang ơn
  trang trọng hoặc lời giải thích cảm xúc dài dòng khi nguồn không đòi hỏi.
- Có thể đổi trật tự từ, tách hoặc nối câu để diễn đạt thuận tiếng Việt,
  nhưng không làm mất thông tin, thay đổi mức độ chắc chắn hay thêm tình tiết.
- Với thành ngữ hoặc ẩn dụ khó hiểu khi dịch sát, ưu tiên truyền đạt ý nghĩa
  và tác dụng của câu bằng tiếng Việt tự nhiên. Nếu hình ảnh được lặp lại
  để nối ý, tạo hài hoặc xây dựng chủ đề, xét cả đoạn trước khi diễn nghĩa;
  giữ liên kết giữa các lần xuất hiện.
- Ưu tiên câu trực tiếp, có thể lược chủ ngữ, đại từ, từ đệm hoặc phần giải thích
  khi ngữ cảnh đã rõ. Sau khi rút gọn, kiểm tra lại chủ thể, đối tượng, thành ngữ
  và quan hệ nghĩa; giữ rõ ai hành động, ai sở hữu, ai nhận lời nói.
- Tránh dịch từng chữ, câu dài nặng mệnh đề và cách nói giải thích quá mức.
  Ví dụ: ưu tiên “giàu có hơn cả tưởng tượng” thay cho cách diễn đạt dài dòng
  khi hai cách vẫn truyền đạt cùng ý.
- Giữ giọng nhân vật: sắc thái hào hứng, ngập ngừng, điềm tĩnh hoặc châm chọc
  phải được thể hiện theo ngữ cảnh. Các cách nói như “ê”, “chả”, “gan đấy”,
  “đành chịu” có thể dùng khi hợp nhân vật và ý nguồn. Khi chuyển chơi chữ,
  câu đùa hoặc lời khiêu khích, giữ mức độ suồng sã và thô tục phù hợp với
  từng nhân vật và sắc thái nguồn; không tăng độ tục chỉ để gây cười mạnh hơn.
  Giữ các lựa chọn hiệu đính riêng của người dùng tại đúng phạm vi, không
  mặc nhiên biến chúng thành giọng chung của nhân vật hoặc toàn project.
- Giữ đúng sự khác biệt giữa hào hứng đồng ý, miễn cưỡng chấp nhận,
  hỏi cho rõ, nghi ngờ, ra lệnh và đe dọa. Câu gọn vẫn phải giữ đúng thái độ.
- Xưng hô thay đổi theo người đối thoại và tình huống. Phân biệt cách gọi
  trực tiếp, độc thoại và lời nhắc về người vắng mặt: có thể gọi “cô” khi
  đối thoại nhưng dùng “ả ta” khi nhận xét hoặc độc thoại nếu hợp thái độ.
  Trong cùng cuộc trao đổi, giữ nhất quán; chỉ chuyển cách xưng hô khi quan hệ,
  vai trò hoặc thái độ thay đổi có căn cứ từ diễn biến. Áp dụng cả với lựa chọn
  của người chơi.
- Chọn danh xưng theo quan hệ và dụng ý trong cảnh: lãnh đạo nhóm, tâng bốc,
  kính trọng hoặc phụng sự. Các cách gọi như “chị đại”, “cao thủ”, “chúa công”
  có thể phù hợp hơn dịch sát chữ; xét đúng người nói và người được gọi.
  Danh xưng do một nhân vật tự nhận không tự xác nhận tuổi tác, tước vị
  thực tế hoặc quan hệ tình cảm của các bên.
- Lời dẫn ngôi thứ nhất ưu tiên “tôi/chúng tôi”; độc thoại nội tâm có thể dùng
  “mình”. Lời thoại chọn theo người nghe. Phân biệt ba lớp này khi rà nhất quán,
  không thay mọi đại từ của nhân vật chính bằng cùng một từ.
- Khi dịch “we”, xác định nhóm được nói đến có bao gồm người nghe hay không.
  Chọn “chúng tớ”, “chúng mình”, “chúng tôi” theo quan hệ và phạm vi của nhóm;
  ví dụ Iris nói “Khi chúng tớ tìm thấy cậu” làm rõ nhóm đã đi cứu Sylar.
- Trong các chương hiện tại, dùng những lựa chọn sau làm tham chiếu:
  - Sylar dùng “mình/cậu” với nhóm bạn; có thể xưng “tôi” với người lạ,
    nhân viên phục vụ, khi đối chất hoặc trong cảnh ký ức trang nghiêm.
  - Trong cuộc chia tay đầu STm01_01, ??? xưng “tôi”, gọi Ma vương là “ngài”;
    Sylar xưng “tôi”, có thể gọi “bạn” hoặc lược đại từ. Giọng kính trọng,
    gần gũi và tiếc nuối. “Thưa Ma vương” phù hợp hơn cách dịch cứng
    “Ma vương của tôi”; chưa tự xác lập quan hệ thần thuộc hoặc tình cảm.
  - Noya hoạt bát, bộc trực; Iris thực tế, lo tiền bạc và sắp xếp việc chung;
    Amber thường ít lời. Giữ nhịp riêng của từng người và quan hệ “tớ/cậu”,
    “mình/cậu” trong bản hiệu đính, tránh đồng loạt đổi mọi người sang một cặp.
  - Bastelina có thể xưng “em”, gọi “quý khách” để thể hiện vai phục vụ
    niềm nở, nhún nhường. Khi đại diện công ty đối chất, “tôi/cô” có thể phù hợp.
    Cách xưng “em” trong dịch vụ không tự xác nhận tuổi của nhân vật.
  - Feagin dùng “ta/ngươi/các ngươi” khi trịch thượng, sai khiến và thị uy;
    giữ giọng kẻ có tiền, có quyền, kể cả khi nói về lương, hợp đồng và kiện cáo.
    Khi đại diện công ty, giữ rõ chủ thể tập thể của khoản vay hoặc tài sản;
    có thể dùng “bên ta”, “công ty” hay tên tổ chức tùy câu.
  - Chitose xưng “em”, gọi nhân vật chính là “chúa công”; dùng “ngài”
    trong câu khi cần đại từ thay thế, không tự đổi thành “Người”. Đây là
    cách Chitose tự nhận quan hệ phụng sự, không xác nhận tước vị hoặc tuổi tác.
    Cụm “my lady/lord” (thường được mở rộng từ `==SEX11==`), JP `主殿`,
    CN `主公` trong quan hệ này được dịch là “chúa công”, kể cả khi
    nhân vật khác trích lại hoặc nhắc rõ cách gọi của Chitose.
    Không thay mọi “lady/lord” bằng “chúa công”, không đổi ánh xạ
    giới tính chung trong glossary; xét người nói, người được gọi và ngữ cảnh.
- Các tham chiếu trên cần được xét lại khi ngữ cảnh mới cung cấp thông tin khác;
  không áp dụng máy móc cho mọi nhân vật cùng giới tính hoặc chức danh.
- Lời tóm tắt hướng tới người chơi dùng “bạn”.
- Không suy ra tuổi tác, địa vị hoặc quan hệ thân mật chỉ từ giới tính.

## Giới tính, tên và thuật ngữ

- Dùng “phép thuật” làm cách gọi chung, có thể rút gọn thành “phép” khi tự nhiên;
  dùng “ma lực” để chỉ năng lượng thi triển phép. Không luân phiên “ma thuật”
  và “phép thuật” chỉ để tránh lặp; chỉ dùng “ma thuật” cho một khái niệm riêng
  khi nguồn hoặc bối cảnh thực sự có sự phân biệt.
- Trong bản VI, ưu tiên cách gọi trung tính tự nhiên như “bạn ấy”,
  “người này” hoặc lược đại từ khi vẫn giữ đúng nghĩa và đối tượng.
  Không bắt buộc viết “cô ấy/anh ấy” nếu một cách nói trung tính đã phù hợp.
- Nếu khác biệt giới tính làm thay đổi ý nghĩa hoặc danh xưng và không thể
  trung tính hóa, giữ đủ các trường hợp bằng dấu `/`.
- Quy tắc trung tính hóa chỉ áp dụng cho bản VI; không sửa các biến thể
  đã lưu trong nguồn EN, JP, CN.
- Giữ tên riêng theo glossary. Không thay tên đang hiển thị là ???, ?? hoặc ***
  bằng danh tính thật dù có thể đoán ra người nói.
- Đọc glossary/glossary.csv mỗi lần xử lý tên và thuật ngữ; dùng cột target
  làm cách dịch chuẩn.
- Thuật ngữ có thể cần biến đổi trật tự trong câu, nhưng phải giữ đúng
  khái niệm và cách gọi đã chốt.
- Nhận diện tên riêng và phần tên được dùng để gọi tắt hoặc ám chỉ trong tiêu đề.
  Ví dụ “Oasis” trong tiêu đề STm01_03 gợi tên xe Lucky Oasis; ưu tiên giữ liên hệ
  với tên đang dùng trong bản dịch. Từ tiếng Anh thông thường vẫn dịch theo nghĩa
  và ngữ cảnh; việc giữ một tên riêng không tạo quy tắc giữ mọi từ tiếng Anh.
- Khi merge, chỉ thêm thuật ngữ qua quy trình tự gọi update-term đã cho phép
  sau kiểm tra nguồn và thông báo đề xuất; ứng viên chưa đủ căn cứ chỉ báo riêng.
  Khi dịch nội dung Merge, không tự thêm thuật ngữ vào glossary.
- Không đề xuất một term riêng cho mọi cụm mô tả chứa term đã có.
  Ví dụ “humanoid Artifact” có thể dịch là “Thánh vật hình người”.
  Vẫn báo ứng viên khi cả cụm là một tên riêng hoặc khái niệm độc lập.

## Bảo toàn dữ liệu và kiểm tra

- Không làm mất nhánh, lời dẫn, độc thoại, lựa chọn, nốt nhạc hoặc mục
  chỉ chứa dấu câu.
- Giữ nguyên thẻ định dạng, token điều khiển, placeholder và ID cần bảo toàn.
  Không dịch cú pháp thẻ hoặc tên biến.
- Phần VI dùng ngoặc kép thẳng `"` (U+0022) như bản EN hiện tại,
  không tự đổi sang ngoặc kép cong. Không thay đổi dấu nháy thuộc cú pháp
  thẻ hoặc token khi chuẩn hóa ngoặc kép trong nội dung.
- Lưu file Merge và glossary bằng UTF-8 BOM, xuống dòng CRLF.
  Glossary dùng dấu phẩy phân cách và quote đúng chuẩn CSV.
- Sau khi sửa, đọc lại file và kiểm tra phạm vi thay đổi, số khối,
  thứ tự ngôn ngữ, tên người nói, thuật ngữ và token.
- Báo ngắn gọn kết quả cùng những khác biệt nguồn ảnh hưởng tới nghĩa.
  Rất khuyến khích phát hiện và giải thích chơi chữ/reference ở cả EN/JP/CN;
  phân biệt điều đã xác minh với suy đoán.
- Với skill translate, ghi chi tiết vào `reports/translation-conflicts.html` và
  `reports/translation-references.html` sau mỗi lần lưu tiến độ Merge đã kiểm tra,
  trước khi dịch tiếp. Đọc các mục liên quan trước khi dịch; định vị theo cây
  thư mục tài nguyên → file Merge → số khối và nguồn/mã đã xác minh.
  Dịch lại cập nhật đúng mục, giữ nhánh ngoài phạm vi; phát hiện không còn phù hợp
  giữ trạng thái “không còn ở bản hiện tại”, vị trí chưa rõ giữ “cần đối chiếu”.
  File/khối không có phát hiện vẫn ghi nhận phạm vi; chỉ bắt đầu từ các lần dịch
  tiếp theo, không rà ngược hoặc suy ra toàn project không có vấn đề.
- Hai HTML tự chứa dữ liệu, chỉ để đọc; dùng helper của skill để kiểm tra đúng
  phiên bản Merge, chuẩn bị/lưu/đọc lại cả hai báo cáo. Nếu lỗi, giữ bản dịch đã
  lưu và dữ liệu phục hồi, khắc phục trước khi dịch thêm; không báo hoàn tất thiếu
  báo cáo. Không chỉnh glossary hoặc push Sheets qua quy trình này.
- Skill translate xử lý cả Merge UI story và UI tĩnh. UI story giữ cấu trúc
  tên/loại như hiện tại; UI tĩnh giữ nguyên header mã, không thêm người nói/loại,
  chỉ thêm hoặc cập nhật VI sau CN/JP/EN. Cả hai dùng chung glossary, đối chiếu
  nguồn và quy trình báo cáo xung đột/reference.
- Câu trả lời của translate chỉ tóm tắt kết quả, điểm cần chú ý và liên kết hai
  báo cáo. Các tác vụ khác báo trong câu trả lời. Không chèn báo cáo/chú giải
  vào file Merge.
