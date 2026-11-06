---
name: merge
description: Hợp nhất đủ ba bản text EN, JP, CN hợp lệ của project SS thành _Merge.txt; tự phân biệt UI story và UI tĩnh, ánh xạ tên/token qua glossary và tự gọi update-term cho thuật ngữ mới đủ căn cứ. Chỉ dùng khi người dùng ra lệnh merge hoặc gọi $merge; không tự chạy khi mở file, nhắc đến tên file Merge hoặc yêu cầu Git merge.
---

# Merge

Chỉ thực hiện khi người dùng chủ động ra lệnh bằng từ `merge` hoặc gọi `$merge`. Giao tiếp bằng tiếng Việt. Mục tiêu là tạo tài liệu đối chiếu ba ngôn ngữ, không dịch nội dung Merge sang tiếng Việt. Sau khi thông báo đề xuất thuật ngữ đủ căn cứ, tự gọi skill `update-term` để skill đó dịch target VI và cập nhật glossary, không chờ duyệt lại. Quyền này chỉ áp dụng cho bộ nguồn đã qua kiểm tra đầu vào dưới đây.

## Ngoại lệ khi được workflow giao

Khi agent chính giao claim `merge` theo skill [workflow](../workflow/SKILL.md),
thực hiện ngay một lượt merge đầy đủ: kiểm tra bộ ba, UI/khóa, tra glossary, ánh
xạ và ghi/đọc lại Merge; đồng thời rà term. Không có inspect riêng. Trả receipt
`ui_type`, `term_proposals` đủ căn cứ kèm bằng chứng và `snapshot_path` theo hợp
đồng workflow; nhóm chưa đủ căn cứ báo riêng. Không tự gọi/giao term-controller,
không sửa glossary, không chờ term cập nhật để ghi Merge lần hai. Agent chính giữ
đề xuất và chỉ giao term-controller khi barrier cho phép; translator đọc glossary
mới để áp dụng target/ánh xạ VI. Quy tắc tự gọi update-term và đọc lại CSV bên
dưới vẫn áp dụng cho lệnh merge riêng; trong workflow dùng cách bàn giao này.

Khi chạy chồng translator A với merger B, chỉ ghi Merge B; không đụng Merge A,
glossary hoặc hai HTML. B merge xong thì dừng trả kết quả, không tự nhận C hoặc
đưa đề xuất cho term-controller khi translator A/verify A chưa hoàn tất.
Không bỏ bất kỳ kiểm tra nguồn, UI, ánh xạ hoặc bảo toàn hiệu đính nào.

## Đầu vào và đầu ra

- Từ file/thư mục được chỉ định hoặc file text nguồn đang mở trong IDE, xác định bộ ba cùng thư mục và cùng tên gốc: `<base>_EN.txt`, `<base>_JP.txt`, `<base>_CN.txt`.
- Ghi kết quả vào `<base>_Merge.txt` trong chính thư mục đó. Ví dụ `STm00_01_EN.txt`, `STm00_01_JP.txt`, `STm00_01_CN.txt` tạo `STm00_01_Merge.txt`.
- Nếu người dùng không chỉ định phạm vi, dùng bộ ba của file text nguồn đang mở. Không tự quét và tạo Merge cho cả project. Nếu không xác định được bộ ba duy nhất, hỏi để chốt phạm vi; nếu thiếu file, chặn bộ nguồn theo quy tắc kiểm tra đầu vào, không tự tìm file khác để thay thế.
- Đọc `glossary/glossary.csv` tính từ gốc project SS trong mỗi lần chạy. Dùng thư viện CSV hỗ trợ Unicode và trường được quote; không tách bằng dấu phẩy thủ công. Bảng hiện dùng UTF-8 BOM và các cột `id,EN,target,category,JP,CN`.
- Giữ nguyên ba file nguồn. Glossary chỉ được cập nhật qua skill `update-term` theo quy trình thuật ngữ bên dưới. Chỉ tạo/cập nhật file Merge được yêu cầu; khi có file Merge cũ, đọc trước để không ghi đè bản đã được người dùng biên tập ngoài kết quả sinh tự động. Nếu có chỉnh sửa thủ công cần giữ mà không xác định được cách hợp nhất, chuẩn bị kết quả mới ở file tạm và hỏi về đúng phần xung đột.

## Kiểm tra đầu vào bắt buộc

Thực hiện trước khi hợp nhất, sinh đầu ra hoặc gọi `update-term`, cho cả UI story và UI tĩnh:

- Phải có đủ ba file `.txt` cùng tên gốc và cùng bộ nguồn: `_EN.txt`, `_JP.txt`, `_CN.txt`. Đọc toàn bộ cả ba file; nếu không đọc/giải mã được, chặn bộ nguồn và báo lỗi. Đối chiếu ngôn ngữ khai báo trong header nếu có với hậu tố tên file; sai ngôn ngữ cũng là lỗi đầu vào. Không suy ngôn ngữ sai chỉ vì tên riêng hoặc một đoạn dùng chữ Latin.
- Kiểm tra thông báo chẩn đoán thiếu/lỗi nguồn ngôn ngữ ở đầu file và trong từng mục. Dấu hiệu đã gặp: `KHÔNG CÓ NGUỒN JP TRONG PHẠM VI ĐÃ KIỂM`, `[KHÔNG CÓ KHÓA TRONG NGUỒN EN]`, cùng các biến thể EN/JP/CN. Đây là cảnh báo của bộ trích xuất; không phải văn bản cần đưa vào Merge.
- Chỉ một file thiếu hoặc chứa cảnh báo lỗi ngôn ngữ cũng **chặn toàn bộ bộ ba**, kể cả khi cảnh báo chỉ nằm trong một mục giữa nhiều mục hợp lệ. Không merge phần còn lại, không dùng hai ngôn ngữ thay ba, không tự dịch bù hay thay cảnh báo bằng `[EMPTY_SOURCE]`.
- Khi bị chặn, báo file/ngôn ngữ, vị trí và cảnh báo cụ thể. Không tạo/cập nhật Merge, không tạo bản Merge dở và không gọi `update-term` từ bộ nguồn đó; giữ nguyên Merge cũ. Được đọc để kiểm tra nhưng không thực hiện bước cập nhật dữ liệu.
- Phân biệt thông báo chẩn đoán với nội dung game: khóa `ErrorCode`, tên có chữ `Warning`, hay câu `WARNING: Suspect...` không tự động là lỗi nguồn. Không chặn chỉ bằng phép tìm chuỗi `Error`/`Warning` bất kỳ. `[EMPTY_SOURCE]` ở một trường rỗng có chủ ý cũng không tự động là lỗi ngôn ngữ.
- Với yêu cầu nhiều bộ nguồn, kiểm tra riêng từng bộ; bỏ qua bộ lỗi và tiếp tục bộ hợp lệ. Không đưa thuật ngữ của bộ bị chặn vào danh sách tự cập nhật chung. Báo riêng trạng thái từng bộ.

## Tự phân biệt UI story và UI tĩnh

- **UI story:** nguồn biểu diễn diễn tiến kịch bản bằng command, như `SetIntro`, `SetTalk`, `SetChoiceBegin`, tin nhắn và các lệnh hiển thị trong cảnh. Tiêu đề, tóm tắt, lựa chọn hoặc lời dẫn không có người nói vẫn thuộc story, không phải UI tĩnh.
- **UI tĩnh:** nguồn là các mục văn bản được tra bằng khóa, như `Achievement.1.1`, nhãn nút, tên, mô tả hoặc trường tên trong Preset; không phải một chuỗi diễn tiến command. File mang tên `Story` nhưng thực chất là bảng khóa văn bản không tự động thuộc UI story.
- Xét cấu trúc nhãn, quan hệ bản ghi và chức năng trường; tên thư mục/file chỉ là bằng chứng hỗ trợ. Không phân loại bằng việc có hay không có người nói, cũng không coi mọi chuỗi trong một bảng là nội dung UI.
- Nếu chức năng trường hoặc loại nguồn chưa rõ, tra JSON/JSONL gốc và phần Lua/UI sử dụng nó trong project. Nếu ba bản có cấu trúc không tương ứng hoặc chưa xác minh được, báo phần vướng; không tự chọn một cấu trúc rồi tuyên bố kết quả đầy đủ.

## Cấu trúc khối UI story

Ghi đúng thứ tự sau, cách nhau một dòng trống giữa các khối:

```text
1. [Tên EN/ Tên JP/ Tên CN] (Loại nội dung bằng tiếng Việt)
Nội dung CN
Nội dung JP
Nội dung EN
```

- Đánh số mọi khối theo dạng `n. [Tên ...] (Loại nội dung)`, bắt đầu từ `1` trong mỗi file và tăng liên tục theo thứ tự xuất hiện sau khi hợp nhất. Tính cả tiêu đề, tóm tắt, UI, lựa chọn, lời dẫn, độc thoại, mục chỉ có dấu câu và mục chỉ có nguồn ở một ngôn ngữ. Không đặt lại số theo cảnh, nhánh hoặc loại nội dung; số khối không phải số command nguồn.
- Tiền tố số nằm ngoài ngoặc vuông, áp dụng cả cho header đặc biệt: `2. [Dẫn chuyện] (Lời dẫn)`, `3. [Người chơi] (Lời thoại)` hoặc `4. [—/ —/ —] (Lựa chọn)`. Khi đọc hoặc cập nhật Merge đã có số, nhận diện tiền tố hiện tại, không thêm số chồng lên số cũ; nếu thêm/bớt khối thì đánh lại liên tục theo thứ tự cuối cùng, giữ nguyên nội dung được bảo toàn.
- Ba tên trong ngoặc vuông là **tên người nói hiển thị** của ba ngôn ngữ, theo thứ tự **EN, JP, CN**. Ba phần nội dung bên dưới theo thứ tự **CN, JP, EN**. Không dùng cột `target` tiếng Việt thay cho một trong ba ngôn ngữ.
- **Ngoại lệ cho ID người nói `0` và `1`:** thay toàn bộ phần `[Tên EN/ Tên JP/ Tên CN]` bằng **`[Dẫn chuyện]`** khi ID là `0`, hoặc **`[Người chơi]`** khi ID là `1`. Chỉ ghi một nhãn tiếng Việt, không lặp thành ba tên và không dùng `[—/ —/ —]`, dù tên nguồn là `[EMPTY_SOURCE]`. Quy tắc này ưu tiên hơn tên mặc định hoặc tên ghi đè. Vẫn giữ `(Loại nội dung bằng tiếng Việt)` và ba phần nội dung CN/JP/EN như các khối khác. Không áp dụng ngoại lệ này cho ID khác như `avg3_100`.
- Phân loại bằng tiếng Việt: `Tên hồi`, `Tiêu đề`, `Tóm tắt`, `Lời thoại`, `Độc thoại`, `Lời dẫn`, `Lựa chọn`, hoặc loại UI tương ứng khi đã xác minh.
- Với nội dung không có người nói như tiêu đề, tóm tắt hay lựa chọn không gắn người nói, dùng `[—/ —/ —]`. Khối có ID người nói `0` hoặc `1` dùng nhãn ngoại lệ ở trên. Không tự đặt tên người nói cho đủ ba ô.
- Tên được xác định là `???`, `??`, `***` phải giữ nguyên theo từng ngôn ngữ. Không đổi tên chưa rõ danh tính thành danh tính thật của nhân vật.
- Nội dung có thể chiếm nhiều dòng; giữ nguyên ngắt dòng, dấu câu và thẻ định dạng nguồn. Không thêm nhãn CN/JP/EN, nhãn lệnh, số command hoặc tham số kỹ thuật vào khối story. Quy tắc này không cấm các nhãn tham chiếu EN/JP/CN trong header UI tĩnh bên dưới.
- Một trường có chữ ở ít nhất một ngôn ngữ vẫn tạo khối. Với trường rỗng có chủ ý ở ngôn ngữ còn lại, ghi `[EMPTY_SOURCE]` tại phần nội dung tương ứng. Thiếu bản ghi không đồng nghĩa với nguồn rỗng: phải kiểm tra và báo phần thiếu.

## Merge UI tĩnh

Một khối UI tĩnh không có người nói hoặc loại nội dung. Ghi mã tham chiếu nguồn nguyên gốc trong header và nội dung theo CN, JP, EN:

```text
1. [Achievement.1.1]
魔王之路 I
魔王の道Ⅰ
Becoming a Real Boss Ⅰ
```

Nếu mã của cùng một mục khác nhau giữa ba bản, ghi đúng thứ tự nhãn **EN, JP, CN**:

```text
1. [EN: mã_EN/JP: mã_JP/CN: mã_CN]
Nội dung CN
Nội dung JP
Nội dung EN
```

- Các mã ở đây là tham chiếu cho `source_refs_json`, nhưng header Merge **không phải chuỗi JSON**. Nếu cả ba mã giống hệt nhau, chỉ ghi mã chung; nếu khác dù chỉ một bản, ghi đủ ba nhãn. Không thêm `(Loại nội dung)`, `[—/ —/ —]`, tên người nói hoặc nhãn nội dung vào khối UI tĩnh.
- Lấy mã từ nhãn mục nguồn đã xác minh. Không tự đổi mã sang tên có vẻ dễ hiểu, không dịch/mở rộng token hoặc tra glossary để thay mã ở header. Giữ nguyên cả dấu `/` nằm trong mã; khi đọc header nhiều ngôn ngữ, nhận ranh giới bằng `/JP:` và `/CN:`, không tách mọi dấu `/`.
- **Mỗi mục nguồn là một khối riêng**. Không gộp các khóa khác nhau dù nội dung CN/JP/EN giống hệt nhau. Header nhiều nhãn biểu diễn mã của cùng một mục ở ba ngôn ngữ, không phải danh sách gộp các mục trùng chữ.
- Parse theo nhãn mục, giữ nội dung nhiều dòng. Ghép bằng khóa đầy đủ hoặc quan hệ bảng + ID bản ghi + vai trò trường đã xác minh. Với khóa chỉ số như `/0/name`, phải đối chiếu ID bản ghi trong dữ liệu gốc trước khi ghép nếu thứ tự ba bản khác nhau; header vẫn giữ mã thật của từng bản. Không ghép theo số dòng, chỉ số vị trí chưa kiểm chứng hoặc chỉ vì câu chữ giống nghĩa.
- Giữ thứ tự xuất hiện trong nguồn EN. Nếu nguồn JP/CN có mục chưa đối chiếu, kiểm tra để bảo toàn và xác định vị trí logic; không âm thầm bỏ mục. Thiếu bản ghi không phải nguồn rỗng có chủ ý và phải được giải quyết/báo rõ trước khi nhận đầu ra là đầy đủ.
- Chỉ lấy trường tạo chữ người chơi đọc, ví dụ tên, mô tả, nhãn nút. Loại ID kỹ thuật, mã tài nguyên, màu, tọa độ và tham số điều khiển dựa trên chức năng thực tế. Ví dụ Preset có thể chứa `/id`, `/name`, `/name_bg_color`: không đưa mọi trường vào Merge chỉ vì chúng đều là chuỗi.
- Giữ mục chỉ có dấu câu hoặc token hiển thị, giữ thẻ/placeholder/ngắt dòng. Trường có nội dung ở ít nhất một ngôn ngữ vẫn được giữ nếu phần rỗng ở bản khác đã được xác minh là có chủ ý; dùng `[EMPTY_SOURCE]` ở phần đó. Chỉ bỏ mục rỗng ở cả ba bản; tuyệt đối không áp dụng ngoại lệ này cho cảnh báo lỗi nguồn ở bước kiểm tra đầu vào.
- Đánh số liên tục từ `1` theo thứ tự cuối cùng, một dòng trống giữa các khối. Dùng chung quy trình ánh xạ nội dung, rà thuật ngữ và kiểm tra/lưu bên dưới.

## Nhận diện nội dung hiển thị trong UI story

Đọc toàn bộ ba file và parse theo nhãn mục, không ghép theo số dòng. Giữ thứ tự diễn tiến command và thứ tự mục bên trong command. Không dùng TrueText/wiki làm danh sách đầy đủ vì có thể thiếu nhánh và chứa UI của wiki.

Với cấu trúc kịch bản đã xác minh trong SS:

| Nội dung | EN và JP | CN |
| --- | --- | --- |
| Tên hồi | `SetIntro/param/1` | `SetIntro/param/1` |
| Tiêu đề | `SetIntro/param/2` | `SetIntro/param/2` |
| Tóm tắt | `SetIntro/param/3` | `SetIntro/param/3` |
| Lời thoại, độc thoại, lời dẫn | `SetTalk/param/7` | `SetTalk/param/2` |
| Lựa chọn thứ i | `SetChoiceBegin/param/12/i` | `SetChoiceBegin/param/3/i` |
| ID người nói | `SetTalk/param/1` | `SetTalk/param/1` |

- Ghép bằng **tên kịch bản + số command + loại lệnh + vai trò nội dung + chỉ số lựa chọn**. Không ghép nguyên nhãn tham số giữa CN và EN/JP, không ghép các câu chỉ vì trông giống nghĩa.
- Giữ mọi nhánh lựa chọn và mọi lời thoại trong nhánh, gồm cả lời dẫn, độc thoại và mục chỉ có `...`, `!`, `?` hoặc dấu khác. Không gộp các mục trùng chữ ở command khác nhau. Chỉ bỏ mục có nội dung rỗng ở cả ba bản.
- ID người nói `0` dùng cho lời dẫn, ID `1` dùng cho người chơi; header tương ứng là `[Dẫn chuyện]` và `[Người chơi]`. Phân biệt độc thoại/lời nhân vật chính bằng ngữ cảnh và dữ liệu nguồn đã xác minh; không đoán chỉ từ việc có hay không có voice.
- Với ID khác `0` và `1`, nếu nguồn có trường tên hiển thị ghi đè tên mặc định, dùng tên ghi đè sau khi xác minh chức năng trường đó. Không tự coi một tham số chưa biết là tên.
- Bảng trên là các trường đã biết, không phải lý do để bỏ qua lệnh UI mới. Với lệnh/trường khác có dấu hiệu chứa nội dung người chơi đọc, tra dữ liệu hoặc định nghĩa lệnh trong project (ví dụ nhóm `05_Lua/Game/UI/Avg/`) để xác định trường và ngôn ngữ. Nếu chưa xác định chắc chắn, báo rõ và giải quyết trước khi tuyên bố kết quả đầy đủ.
- Bỏ tài nguyên ảnh/âm thanh, voice ID, hiệu ứng, tọa độ, thời lượng, easing, animation, màu, ID nhánh và các tham số điều khiển. Ví dụ `SetBg`, `CtrlBg`, `SetBGM`, `SetAudio`, `SetFx`, `SetMainRoleTalk` không tạo khối chỉ vì có giá trị chuỗi. Có thể dùng dữ liệu của chúng làm ngữ cảnh nhưng không đưa lệnh hệ thống vào đầu ra.

## Ánh xạ tên và token

Áp dụng cho nội dung của cả hai loại UI; các quy tắc người nói chỉ áp dụng cho UI story. Mã tham chiếu ở header UI tĩnh không phải token từ vựng cần ánh xạ.

- Với ID người nói khác `0` và `1`, tra ID của từng ngôn ngữ trong các dòng ánh xạ của glossary, lấy đúng cột `EN`, `JP`, `CN`. Ví dụ `avg1_111` tương ứng `Iris`, `アヤメ`, `鸢尾`. Dùng ID người nói của chính bản ngôn ngữ đó nếu ba nguồn khác nhau; không mặc định ID EN áp dụng cho mọi bản.
- Với ID khác `0` và `1`, các tên nguồn `[EMPTY_SOURCE]` có nghĩa là không có tên trong bảng, không phải tên cần in. Dùng `—` ở ô tên tương ứng và kiểm tra ngữ cảnh nếu có tên runtime.
- Thay các ID/token tạo chữ hiển thị bằng giá trị ngôn ngữ tương ứng đã được xác minh. Không thay chuỗi con trong từ, không đổi tên riêng sang bản Việt chỉ vì có thuật ngữ trong cột `target`.
- Với token giới tính, tra các khóa `SEX/<token>/0`, `SEX/<token>/1` trong glossary, lấy **cùng cột ngôn ngữ với nội dung đang xử lý**, ghép các biến thể bằng `/` theo thứ tự chỉ số nguồn tăng dần. Không tự chọn giới tính và không sắp xếp lại theo ví dụ tiếng Việt.
- Ví dụ `==SEX5==` trong câu EN phải thành `hers/his` theo glossary hiện hành; nội dung JP/CN dùng các giá trị JP/CN của chính token đó. Cùng mã token ở ba ngôn ngữ có thể được dùng với nghĩa khác nhau, không suy ra JP/CN từ EN. Khi nguồn có cả hai biến thể giống nhau, vẫn giữ cả hai theo yêu cầu liệt kê trường hợp.
- Nếu tên người nói cũng chứa token nhiều biến thể, mở rộng từng ô tên theo đúng ngôn ngữ, dùng `/` giữa các trường hợp, rồi giữ thứ tự ba ô tên EN/JP/CN.
- Token điều khiển/định dạng như `==W==`, `==RT==`, `<color=...>`, `<size=...>` không phải ID từ vựng cần tra tên. Giữ nguyên trong nội dung, cùng thẻ đóng và placeholder `%s`, `%d`; không lược bỏ cả câu vì có token.
- Nếu ID/token hiển thị không có trong glossary, tìm nguồn ánh xạ tương ứng trong project để xác minh (như `Preset/AvgCharacter`, `Preset/AvgUIText`, `Preset/AvgContacts`). Việc xác minh ID thiếu không cho phép tự tạo thuật ngữ hoặc tự sửa các dòng ánh xạ ngoài phạm vi; quyền gọi `update-term` bên dưới chỉ dành cho thuật ngữ mới đủ căn cứ. Nếu vẫn chưa giải được, giữ bản nháp tạm và báo đúng ID/token thiếu để giải quyết; không giả tên, bỏ mục hay báo hoàn tất một bản còn ID chưa ánh xạ.

## Rà thuật ngữ và tự gọi update-term

Trong lúc merge, đọc nội dung hiển thị của **cả EN, JP và CN** để tìm từ/cụm từ lạ có khả năng là thuật ngữ của thế giới game, như khái niệm đặc thù, vật phẩm, địa danh, tổ chức, chức danh hoặc cách gọi được dùng nhất quán. Dấu hiệu như viết hoa bất thường, được giải thích trong thoại hoặc lặp lại cùng một khái niệm giúp nhận diện; không coi mọi từ thông thường là thuật ngữ chỉ vì chưa có trong glossary.

- Đối chiếu ứng viên với các dòng **`category=term`** và các cột EN/JP/CN trong glossary hiện tại. Xét cụm đầy đủ, số nhiều/sở hữu và khác biệt hoa/thường theo ngữ cảnh để tránh báo lại thuật ngữ đã có.
- Một thuật ngữ đã có dòng `term` không trở thành thuật ngữ mới chỉ vì ô JP/CN của dòng đó còn trống. Ngược lại, việc một từ xuất hiện trong tên ánh xạ hoặc trong câu của dòng khác không chứng minh nó đã có định nghĩa `term`.
- Đối chiếu cùng đơn vị nội dung và ngữ cảnh để tìm cách gọi tương ứng ở ba ngôn ngữ. Không ép ba từ thành một thuật ngữ chỉ vì đứng cùng vị trí; nếu chưa chắc tương ứng thì ghi rõ mức chưa chắc. Nếu một bản lược bỏ hoặc không có cách gọi tương ứng, báo là không thấy thay vì tự dịch hoặc bịa dữ liệu.
- Gộp những lần xuất hiện của cùng một ứng viên thành một mục báo cáo, kèm một hoặc vài vị trí tiêu biểu. Không báo lại tên nhân vật đã được ánh xạ đầy đủ chỉ vì tên ấy không có dòng `term`, trừ khi ngữ cảnh cho thấy còn có nghĩa thuật ngữ riêng cần chốt.
- Chia ứng viên thành nhóm **đủ căn cứ về nghĩa/khái niệm để cập nhật** và nhóm **chưa đủ căn cứ**. Cụm mô tả thông thường chứa thuật ngữ đã có không tự trở thành term mới; tên nhân vật đã ánh xạ cũng không cần một term riêng nếu không có nghĩa thuật ngữ độc lập.
- Trước khi cập nhật, thông báo đề xuất trong commentary bằng bảng **EN, JP, CN, lý do, vị trí/ngữ cảnh**. Với story, dùng file + số khối hoặc command; với UI tĩnh, dùng file + số khối + mã nguồn. Không chèn bảng này vào Merge và không kết thúc lượt để chờ duyệt.
- Với nhóm đủ căn cứ từ bộ nguồn hợp lệ, **tự gọi skill [update-term](../update-term/SKILL.md)** ngay sau thông báo. Truyền cách gọi EN, JP/CN đã xác minh hoặc thông tin chưa tìm thấy, ngữ cảnh và vị trí bằng chứng. `merge` không tự dịch target VI; **`update-term` chịu trách nhiệm dịch/chọn target VI, thêm term và đồng bộ các ánh xạ liên quan**. Đây là quyền tự động đã được cho phép, không hỏi lại chỉ vì chưa có target VI.
- Không yêu cầu đổi bản dịch đã được người dùng chốt hoặc sửa định nghĩa term đã có chỉ vì tìm ra một phương án khác. Để `update-term` đọc glossary hiện tại, tránh trùng term, chèn term mới sau dòng term cuối, chỉ điền JP/CN có bằng chứng và bảo toàn các quyết định hiệu đính.
- Nhóm chưa đủ căn cứ được báo riêng, không đưa vào yêu cầu tự lưu và không bịa nghĩa hoặc cặp ngôn ngữ. Nếu `update-term` gặp mâu thuẫn glossary chưa giải quyết được, không ép cập nhật; báo rõ phần chưa cập nhật. Không để nghi vấn thuật ngữ đơn thuần ngăn lưu một Merge đã ánh xạ đầy đủ.
- Sau khi `update-term` lưu và kiểm tra thành công, **đọc lại glossary** để hoàn tất/kiểm tra ánh xạ tên và token trong Merge theo các cột nguồn EN/JP/CN. Không đưa target VI vào nội dung CN/JP/EN, không thêm nội dung VI, không gọi `translate`, `translate-update` hoặc push Google Sheets.
- Nếu không có term mới đủ căn cứ thì không gọi `update-term`. Báo kết quả cuối: term đã thêm, số ánh xạ đã đồng bộ theo kết quả `update-term`, ứng viên còn nghi vấn và lỗi thực tế nếu có. Chạy lại không được thêm term trùng. Nếu không có ứng viên mới, nói ngắn gọn như vậy.

## Kiểm tra và lưu

Trước khi thực hiện, thông báo bộ ba đầu vào và đường dẫn đầu ra. Có thể dùng script tạm để parse, ghép, đối chiếu và ghi file; không cần tạo công cụ hoặc báo cáo phụ trong thư mục kịch bản.

Kiểm tra trên dữ liệu ghép và đọc lại file sau khi lưu:

- Mỗi mục hiển thị đã nhận diện xuất hiện đúng một lần; tổng khối khớp tổng mục logic, không phải tổng trường của cả ba file. Không cố định số lượng của một chương mẫu cho chương khác.
- Header có số khối liên tục từ `1` đến tổng số khối của chính file, không thiếu, trùng hoặc lặp tiền tố. Số khối trong báo cáo phải khớp số được ghi trong file.
- Không thiếu nhánh, không loại dấu câu đơn lẻ, không mất mục vì tham số EN/JP khác CN. Không có mục lệnh hệ thống được dùng làm nội dung.
- Kiểm tra kiểu UI đã xác minh: story dùng `[Dẫn chuyện]` cho ID `0`, `[Người chơi]` cho ID `1`, tên EN/JP/CN cho các ID khác và có loại nội dung; UI tĩnh chỉ có mã chung hoặc ba mã gắn nhãn EN/JP/CN, không có người nói/loại nội dung. Không thay header story thành mã hoặc ngược lại.
- Cả hai loại có thứ tự nội dung CN/JP/EN, không gộp mục trùng chữ, không mất nội dung nhiều dòng. Các biến thể giới tính đã được thay bằng dấu `/`, không sót token từ vựng chưa giải; header UI tĩnh vẫn giữ mã nguyên gốc.
- Bản gốc chỉ thay đổi trong đầu ra ở những vị trí ánh xạ đã định nghĩa. Giữ nguyên câu chữ, dấu câu, thẻ, token định dạng và placeholder còn lại; không tự dịch, diễn giải hoặc cắt ngắn.
- Ghi UTF-8 BOM, xuống dòng CRLF, một dòng trống giữa các khối. Không ghi đè file nguồn hoặc bản Merge có thay đổi thủ công chưa được xử lý. Chỉ `update-term` được sửa glossary theo quy trình đã cho phép; sau đó phải đọc lại bản mới.

Kết thúc bằng liên kết `<base>_Merge.txt`, loại UI, số khối, kết quả cập nhật thuật ngữ và ứng viên chưa đủ căn cứ. Với tác vụ nhiều bộ, báo cả bộ bị chặn cùng ngôn ngữ/vị trí/cảnh báo. Chỉ báo hoàn tất cho đầu ra đã được lưu và kiểm tra; không coi bộ bị chặn là đã merge.

Các tình huống cần đối chiếu khi kiểm tra quy trình:

- Bộ hợp lệ đi qua kiểm tra; thiếu từng file EN/JP/CN hoặc có cảnh báo thiếu nguồn/khóa ở bất kỳ mục nào đều chặn cả bộ, giữ nguyên Merge/glossary. Câu thoại có `Warning/Error` và `[EMPTY_SOURCE]` có chủ ý không bị chặn nhầm.
- Story giữ header cũ và mọi nhánh; UI tĩnh kiểm tra mã chung, mã khác nhau giữa ba bản, mã chứa `/`, mục trùng chữ giữ riêng và các trường kỹ thuật bị loại.
- Giữ nội dung nhiều dòng, dấu câu, placeholder và thẻ khi ánh xạ. Đối chiếu trước/sau để không mất hiệu đính VI ở Merge đã có.
- Term đủ căn cứ được thông báo rồi chuyển `update-term` tự dịch/lưu; term mơ hồ chỉ báo. Đọc lại glossary sau lưu; chạy lại không thêm trùng và không sửa ngược target đã chốt.
