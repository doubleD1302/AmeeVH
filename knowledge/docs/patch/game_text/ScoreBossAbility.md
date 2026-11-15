---
doc_id: patch/game_text/ScoreBossAbility
category: game_text
group: tables
file_id: ScoreBossAbility
origin: patch_game
source: patch:arcx/game_text/ScoreBossAbility
source_sha256: 8899c25b923cd7b69e5689f5c521f43306bb22a4251fbc344965ca78673a9ef2
blocks: 27
status: translated
---

# ScoreBossAbility (bảng văn bản trong game)

## Nội dung

ScoreBossAbility.100000: không có
ScoreBossAbility.100001: Tinh Mạch Cuồng Bạo | Thủ Lĩnh bắt đầu với 1 điểm Berserk và tăng 1 điểm sau mỗi 10 giây (tối đa 5 tầng). Mỗi điểm cộng dồn sẽ tăng DMG của trùm lên &Param1&.
Gây 10 đòn lên trùm trong vòng 2 giây sẽ loại bỏ tất cả điểm cộng dồn Berserk. Du Hành Giả chính sau đó nhận được 10 điểm Amplify (tối đa 10 tầng). Mỗi đòn đánh tiêu tốn 1 điểm Khuếch đại để tăng DMG của đòn đánh đó lên &Param2&.
ScoreBossAbility.100002: Bệnh tàn lụi | Trùm nhận được Nhẫn lửa, tăng DMG gây ra của chúng thêm &Param1& và liên tục gây sát thương cho đội của bạn trong vòng.
Kích hoạt 3 Dấu ấn Nguyên tố lên trùm trong vòng 5 giây sẽ tăng cường đội hình, tăng DMG tự động tấn công thêm &Param2& trong 10 giây và vô hiệu hóa Nhẫn lửa của trùm trong 10 giây.
ScoreBossAbility.100003: Chiến đấu nhiệt thành | Thủ Lĩnh tăng 1 điểm Battle Frenzy cứ sau 5 giây, tăng thiệt hại mà nó gây ra thêm &Param1& (tối đa 5 tầng).
Khi Main Du Hành Giả kích hoạt Dấu ấn, loại bỏ 1 điểm Battle Frenzy khỏi trùm. Loại bỏ thành công một cộng dồn Battle Frenzy sẽ khôi phục 20 Năng lượng cho đội và tăng Thiệt hại tối thượng của trùm do &Param2&, tồn tại trong 10 giây và đặt lại khi được kích hoạt lại.
ScoreBossAbility.100004: Chiếc nhẫn bóng tối nuốt chửng | Khi trùm sở hữu Dark Ring, DMG của nó tăng thêm &Param1& và nó gây thêm DMG AoE cứ sau 5 giây.
Gây 20 đòn đánh vào trùm trong vòng 3 giây sẽ vô hiệu hóa Nhẫn bóng tối của trùm trong 15 giây. Thủ Lĩnh cũng nhận thêm &Param2& thêm DMG kỹ năng do Du Hành Giả hỗ trợ xử lý trong thời gian này.
ScoreBossAbility.100005: Sự thay đổi thực tế | Thủ Lĩnh chuyển đổi giữa Dạng ảo ảnh và Dạng thực tế cứ sau 15 giây.
Ở ​​Dạng Thực tế, trùm nhận thêm &Param1& thêm DMG của Minion. Việc kích hoạt một dấu sẽ tăng thời lượng của biểu mẫu hiện tại thêm &Param2& s. Nó chỉ có thể kích hoạt một lần mỗi giây.
Ở Dạng Ảo ảnh, trùm nhận &Param3& tăng DMG Kỹ năng. Gây thiệt hại cho Minion mỗi lần sẽ tăng thời gian tồn tại của hình thức hiện tại thêm &Param4& giây. Nó chỉ có thể kích hoạt một lần mỗi giây.
ScoreBossAbility.100006: Gọi xuống sấm sét | Khi trùm có Thunderbolt, DMG của nó tăng thêm &Param4& và gây thêm DMG trong một khu vực nhỏ 4 lần mỗi 3 giây.
Xử lý DMG kỹ năng hỗ trợ &Param2& lần cho trùm trong &Param1& s vô hiệu hóa Thunderbolt trong 15 giây và tăng DMG kỹ năng mà trùm lấy từ Hỗ Trợ Du Hành Giả thêm &Param3& trong suốt thời gian.
ScoreBossAbility.100007: Động lực | Thủ Lĩnh nhận được &Param1& Tăng DMG. Đối với mỗi người chơi Minion trên sân, trùm gây &Param2& ít thiệt hại hơn và bị ảnh hưởng bởi &Param3& VUL. Hiệu ứng này cộng dồn tối đa 3 lần và tồn tại trong &Param4& giây sau khi Minion biến mất.
ScoreBossAbility.100008: Tập trung | Thủ Lĩnh nhận được một điểm Tập trung sau khi nhận DMG trong &Param1& lần, tăng DMG gây ra của nó lên &Param2&.
Kích hoạt Dấu hiệu &Param4& lần trong &Param3& s sẽ xóa tất cả các ngăn xếp Tiêu điểm. Trong &Param5& giây tiếp theo, thủ lĩnh nhận thêm &Param6& thêm DMG từ Kỹ năng hỗ trợ. Hiệu ứng này kích hoạt tối đa một lần mỗi &Param7& giây. Kích hoạt lại sẽ đặt lại thời lượng.
ScoreBossAbility.100009: Thế đứng của Nam tước | Thủ Lĩnh luân phiên giữa các dạng Chiến binh và Honeypot, chuyển đổi mọi &Param1& s và xóa tất cả các debuff của nó (Điểm Kiên Cường Break không được tính vào bộ đếm thời gian).
Ở dạng Chiến binh, Bá tước Duloos nhận &Param2& giảm DMG tối thượng và &Param3& tăng DMG tấn công tự động.
Ở dạng Honeypot, Nam Tước Duloo nhận &Param4& giảm Mark DMG và &Param5& tăng DMG kỹ năng.
ScoreBossAbility.100010: Nhẫn thủy sinh | Khi trùm sở hữu Nhẫn nước, DMG của nó tăng thêm &Param1& và nó gây thiệt hại diện rộng mỗi 5 giây.
Xử lý &Param2& trường hợp DMG cho trùm trong vòng 5 giây sẽ vô hiệu hóa Vòng nước trong &Param3& giây. Khi Vòng Nước bị vô hiệu hóa:
Gây &Param4& các trường hợp Hỗ trợ DMG cho trùm trong vòng 5 giây sẽ tăng DMG Tự động Tấn công mà trùm phải nhận thêm &Param5&.
Xử lý &Param6& các trường hợp DMG của Main Du Hành Giả DMG trong vòng 5 giây sẽ tăng DMG kỹ năng mà thủ lĩnh nhận được từ các Du Hành Giả hỗ trợ thêm &Param7&.
ScoreBossAbility.100011: Sự cộng hưởng của sức mạnh | Đối với mỗi kỹ năng &Param1& được thi triển bởi Du Hành Giả chính, tất cả DMG kỹ năng của Du Hành Giả hỗ trợ sẽ được tăng cường thêm &Param2& cho &Param3& s.
Với mỗi &Param4& lần Người hỗ trợ gây sát thương, DMG kỹ năng của Du Hành Giả chính được tăng cường bởi &Param5& trong &Param6& s.
Kích hoạt lại sẽ làm mới thời lượng; hiệu ứng không xếp chồng lên nhau.
ScoreBossAbility.100012: Combo nghỉ giải lao | Với mỗi &Param7& Skill Skill DMG gây ra cho trùm, Tuyệt Kỹ Sát Thương Gánh Chịu của trùm được tăng thêm &Param1& cho &Param3& s, cộng dồn lên tới &Param2& lần.
Đối với mỗi trường hợp &Param8& của Mark DMG được chia cho trùm, Skill Sát Thương Gánh Chịu của trùm được tăng cường thêm &Param4& cho &Param6& s, cộng dồn lên tới &Param5& lần.
ScoreBossAbility.100013: Gọi xuống sấm sét | Khi trùm có Thunderbolt, DMG của nó tăng thêm &Param4& và gây thêm DMG trong một khu vực nhỏ 4 lần mỗi 3 giây.
Gây Mark DMG &Param2& lần cho trùm trong &Param1& s sẽ vô hiệu hóa Thunderbolt trong 15 giây và tăng cường DMG kỹ năng mà trùm phải nhận &Param3& trong suốt thời gian.
ScoreBossAbility.100014: Tinh luyện khéo léo | Với mỗi &Param1& mà Du Hành Giả hỗ trợ còn lại trên chiến trường, áp dụng 1 điểm Xây dựng cho chính họ và Du Hành Giả chính.
Mỗi ngăn xếp Tích lũy cung cấp &Param2& cường độ DMG kỹ năng và &Param5& Cường độ DMG tự động tấn công, cộng dồn tối đa &Param3& lần. Mỗi ngăn xếp tồn tại trong &Param4& giây và mọi ngăn xếp đạt được sẽ đặt lại thời lượng này.
Hai Du Hành Giả hỗ trợ, mỗi người có thể áp dụng Xây dựng cho Du Hành Giả chính; giới hạn ngăn xếp và hiệu ứng được tính toán riêng biệt và có thể tồn tại đồng thời.
ScoreBossAbility.100015: Bá tước bệ hạ | Số lượng Duloos bắt đầu với 1 điểm Kháng cự và nhận thêm một điểm kháng cự sau mỗi 5 giây. Mỗi điểm Kháng cự làm giảm thiệt hại mà anh ta đã lấy đi &Param1&, cộng dồn tối đa &Param2& lần.
Khi Du Hành Giả chính kích hoạt Dấu ấn, 1 điểm Kháng cự sẽ bị loại bỏ khỏi Bá tước Duloos và tất cả Du Hành Giả hỗ trợ trên chiến trường đều nhận được 1 điểm Khuếch đại. Mỗi điểm cộng dồn sẽ tăng Thiệt hại thêm &Param3&, cộng dồn tối đa &Param4& lần, kéo dài 20 giây.
ScoreBossAbility.100016: Cơn sốt cuồng nhiệt | Mỗi &Param1& tiêu diệt lính Puff Gió, tiêu diệt được [Cảm hứng], cấp cho toàn đội &Param2& Sức mạnh sát thương kỹ năng cho &Param3& s.
Bất cứ khi nào Du Hành Giả chính sử dụng một kỹ năng, thời gian còn lại của [Cảm hứng] sẽ được kéo dài thêm &Param4& giây (tối đa là &Param5& giây).
ScoreBossAbility.100017: Chữa cháy bằng lửa | Kẻ địch sở hữu Nhẫn Lửa, liên tục gây thiệt hại cho Main Du Hành Giả trong vòng. Mỗi khi Main Du Hành Giả kích hoạt &Param1& Dấu ấn nguyên tố lên kẻ địch trùm, đội sẽ nhận được Cường hóa: DMG kỹ năng được tăng cường thêm &Param2& trong &Param3& giây. Trong thời gian này, Vòng lửa của kẻ địch bị vô hiệu hóa và không thể kích hoạt lại.
ScoreBossAbility.100018: Mệt mỏi khi đánh | Kẻ địch trùm sở hữu &Param1& DMG RES khi chống lại đòn tấn công tự động/Kỹ năng/Đánh dấu DMG.
Mỗi khi Main Du Hành Giả gây &Param2& các trường hợp Tự động tấn công/Kỹ năng/Đánh dấu DMG cho kẻ địch trùm, RES của nó đối với loại DMG cụ thể đó sẽ giảm đi &Param3& cho đến khi giảm xuống 0. Sau đó, mỗi lần kích hoạt tiếp theo sẽ tăng DMG lấy từ loại DMG cụ thể đó thêm &Param4&, tối đa là &Param5&.
ScoreBossAbility.100019: Nêm xuyên giáp | Sau khi Main Du Hành Giả gây ATK DMG tự động cho trùm, trùm nhận &Param1& tăng DMG tối thượng cho &Param2& s (cộng dồn tối đa &Param3& lần) và có thể kích hoạt tối đa 0,5 giây một lần.
Tăng Xuyên Phòng Thủ của đội lên &Param4&. Có Du Hành Giả hỗ trợ trên chiến trường sẽ tăng Xuyên Phòng Thủ của đội thêm &Param5&.
ScoreBossAbility.100020: thiết kế riêng | Với mỗi &Param1& một Du Hành Giả hỗ trợ còn lại trên chiến trường, áp dụng 1 điểm tích lũy cho bản thân và Du Hành Giả chính.
Mỗi ngăn xếp Tích lũy cung cấp &Param2& cường độ DMG kỹ năng và &Param5& Cường độ DMG tự động tấn công, cộng dồn tối đa &Param3& lần. Mỗi ngăn xếp tồn tại trong &Param4& giây và mọi ngăn xếp đạt được sẽ đặt lại thời lượng này.
Hai Du Hành Giả hỗ trợ, mỗi người có thể áp dụng Xây dựng cho Du Hành Giả chính; giới hạn ngăn xếp và hiệu ứng được tính toán riêng biệt và có thể tồn tại đồng thời.
ScoreBossAbility.100021: Lớp mỏng | Với mỗi &Param3& lần, Du Hành Giả kích hoạt một Dấu ấn, gây ra Armor Break cho mục tiêu của trùm. Mỗi điểm cộng dồn Armor Break tăng cường DMG tấn công tự động do &Param4& và Thiệt hại kỹ năng bị lấy bởi &Param5&, cộng dồn tối đa &Param6& lần.
ScoreBossAbility.100022: Cuộc truy đuổi phá vỏ | Khi một Du Hành Giả hỗ trợ gây sát thương tối thượng cho mục tiêu trùm, DMG tối thượng đã thực hiện của mục tiêu trùm sẽ tăng thêm &Param1& trong &Param3& giây, cộng dồn tối đa &Param4& lần.
Khi một Du Hành Giả hỗ trợ gây sát thương tấn công tự động cho mục tiêu trùm, Skill Sát Thương Gánh Chịu của mục tiêu trùm sẽ tăng thêm &Param2& trong &Param5& s, cộng dồn tối đa &Param6& lần.
ScoreBossAbility.100023: Dư chấn tan vỡ | Khi Main Du Hành Giả sử dụng chiêu cuối, tăng DMG kỹ năng mà mục tiêu trùm phải nhận thêm &Param1& trong &Param3& giây.
Khi Du Hành Giả chính sử dụng chiêu cuối, Mark Sát Thương Gánh Chịu của mục tiêu trùm được tăng thêm &Param2& cho &Param4& s.
ScoreBossAbility.100024: Hiệp ước máu | Tăng HP tối đa của Du Hành Giả chính thêm &Param1& và Sát Thương Gánh Chịu bởi &Param2&.
Khi một đơn vị đồng minh gây Mark DMG &Param4& lần cho mục tiêu trùm trong &Param3& s, tăng DMG kỹ năng và ATK tự động DMG mà mục tiêu trùm phải nhận thêm &Param5& và &Param6& tương ứng cho &Param7& s.
ScoreBossAbility.100025: Rạn Nứt Ầm Ầm | HP tối đa của Du Hành Giả chủ lực tăng &Param4&, sát thương phải chịu tăng &Param5&.
Khi Du Hành Giả chủ lực gây sát thương lên mục tiêu Thủ Lĩnh và kích hoạt Tiêu Ký, sát thương kỹ năng mà Thủ Lĩnh phải chịu tăng thêm &Param1& trong &Param2& giây, tối đa cộng dồn &Param3& tầng.
ScoreBossAbility.100026: Tàn Hoa Lộ Nhụy | Mỗi khi mục tiêu Thủ Lĩnh chịu Sát Thương Tuyệt Kỹ, sát thương Tiêu Ký phải chịu tăng thêm &Param1& trong &Param2& giây, tối đa cộng dồn &Param3& tầng.
Mỗi khi mục tiêu Thủ Lĩnh chịu Sát Thương Kỹ Năng, sát thương kỹ năng phải chịu tăng thêm &Param4& trong &Param5& giây, tối đa cộng dồn &Param6& tầng.
