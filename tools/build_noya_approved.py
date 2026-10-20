import json
from pathlib import Path

# Load input
src_path = Path("StellaSora_VietHoa/work/batches/batch_light_group1_noya.json")
items = json.loads(src_path.read_text(encoding="utf-8"))

# Translations map by key
translations = {
    # === SKILL ===
    "Skill.100016202.1": "Bão Tố Lóe Sáng: Rực Rỡ",
    "Skill.100016202.2": "Vung nhanh trường kiếm [Phất Hiểu], gây nhiều đợt sát thương kỹ năng diện rộng tương đương <color=#fb8037>&Param1&</color> Tấn Công; sau đó dùng cự kiếm [Thự Quang] bổ xuống, gây sát thương kỹ năng diện rộng tương đương <color=#fb8037>&Param2&</color> Tấn Công, đồng thời tạo ra 1 [Trụy Tinh] rơi xuống gây sát thương kỹ năng diện rộng tương đương <color=#fb8037>&Param3&</color> Tấn Công.",
    
    "Skill.100016203.1": "Sấm Sét Giáng Đòn: Phá Kích",
    "Skill.100016203.2": "Cầm trường kiếm [Phất Hiểu] xoay tròn tốc độ cao, gây nhiều đợt sát thương kỹ năng diện rộng tương đương <color=#fb8037>&Param1&</color> Tấn Công; sau đó cắm cự kiếm [Thự Quang] xuống đất tạo chấn động liên hoàn, gây nhiều đợt sát thương kỹ năng diện rộng tương đương <color=#fb8037>&Param2&</color> Tấn Công; khi rút cự kiếm lên sẽ kích hoạt vụ nổ, gây sát thương kỹ năng diện rộng tương đương <color=#fb8037>&Param3&</color> Tấn Công.",
    
    "Skill.11620000.13": "Né Tránh",
    "Skill.11620000.2": "Né Tránh",
    
    "Skill.16210000.1": "Bách Luyện Kiếm Thuật",
    "Skill.16210000.13": "Vung cự kiếm và trường kiếm thực hiện chuỗi tấn công liên hoàn không dứt. Khi cách xa mục tiêu, Noya - Khải Minh dùng trường kiếm phát động tấn công xung kích. Đòn đánh thường của Noya - Khải Minh tăng &Param6& gây ra lên mục tiêu mang ##Thiểm Thước#4029#.",
    "Skill.16210000.2": "Vung cự kiếm [Thự Quang] và trường kiếm [Phất Hiểu] thực hiện chuỗi tấn công liên hoàn không dứt.\nĐòn 1: Vung cự kiếm, gây sát thương đòn đánh thường hệ Quang tương đương <color=#fb8037>&Param1&x2</color> HP Tối Đa.\nĐòn 2: Vung cự kiếm, gây sát thương đòn đánh thường hệ Quang tương đương <color=#fb8037>&Param2&x3</color> HP Tối Đa.\nĐòn 3: Vung cự kiếm, gây sát thương đòn đánh thường hệ Quang tương đương <color=#fb8037>&Param3&x2</color> HP Tối Đa.\nĐòn 4: Vung trường kiếm, bắn ra 2 luồng [Lưu Quang], mỗi luồng gây sát thương kỹ năng hệ Quang tương đương <color=#fb8037>&Param4&</color> HP Tối Đa.\nKhi Noya - Khải Minh cách xa mục tiêu, đòn đánh thường sẽ dùng trường kiếm phát động tấn công xung kích, gây sát thương kỹ năng hệ Quang tương đương <color=#fb8037>&Param5&x3</color> HP Tối Đa, hiệu ứng này mỗi 1.5 giây có thể kích hoạt 1 lần.\nKhi đòn đánh thường của Noya - Khải Minh gây sát thương lên mục tiêu mang ##Thiểm Thước#4029#, mỗi 1 tầng ##Thiểm Thước#4029# trên người mục tiêu sẽ tăng &Param6& của đòn đánh lần này thêm <color=#fb8037>&Param7&</color>.",
    
    "Skill.16220000.1": "Né Tránh",
    
    "Skill.16231000.1": "Bão Tố Lóe Sáng: Rực Rỡ",
    "Skill.16231000.13": "Vung nhanh trường kiếm gây nhiều đợt sát thương, sau đó cầm cự kiếm bổ xuống gây sát thương diện rộng, đồng thời tạo ra [Trụy Tinh]. Kỹ Năng Chính có thể kích hoạt ##Ấn Ký Quang#1015#.",
    "Skill.16231000.2": "Vung nhanh trường kiếm [Phất Hiểu], gây sát thương kỹ năng hệ Quang diện rộng tương đương <color=#fb8037>&Param1&x5</color> HP Tối Đa. Sau đó dùng cự kiếm [Thự Quang] bổ xuống, gây sát thương đòn đánh thường hệ Quang diện rộng tương đương <color=#fb8037>&Param2&</color> HP Tối Đa, đồng thời tạo ra 1 [Trụy Tinh] gây sát thương đòn đánh thường hệ Quang diện rộng tương đương <color=#fb8037>&Param3&</color> HP Tối Đa.\nKỹ Năng Chính \"Bão Tố Lóe Sáng: Rực Rỡ\" có thể kích hoạt ##Ấn Ký Quang#1015#, tạo ra ##Quang Diệu#4028#: Gây sát thương ấn ký hệ Quang diện rộng tương đương &Param4& HP Tối Đa, đồng thời gắn thêm 1 tầng ##Thiểm Thước#4029#.",
    
    "Skill.16232000.1": "Sấm Sét Giáng Đòn: Phá Kích",
    "Skill.16232000.13": "Cầm trường kiếm xoay tròn tốc độ cao, sau đó cầm cự kiếm cắm xuống đất tạo chấn động gây sát thương diện rộng. Kỹ Năng Viện Trợ có thể kích hoạt ##Ấn Ký Quang#1015#.",
    "Skill.16232000.2": "Cầm trường kiếm [Phất Hiểu] xoay tròn tốc độ cao, gây sát thương kỹ năng hệ Quang diện rộng tương đương <color=#fb8037>&Param1&x8</color> HP Tối Đa. Sau đó dùng cự kiếm [Thự Quang] cắm xuống đất tạo chấn động liên hoàn, gây sát thương đòn đánh thường hệ Quang diện rộng tương đương <color=#fb8037>&Param2&x6</color> và <color=#fb8037>&Param3&</color> HP Tối Đa.\nKỹ Năng Viện Trợ \"Sấm Sét Giáng Đòn: Phá Kích\" có thể kích hoạt ##Ấn Ký Quang#1015#, tạo ra ##Quang Diệu#4028#: Gây sát thương ấn ký hệ Quang diện rộng tương đương &Param4& HP Tối Đa, đồng thời gắn thêm 1 tầng ##Thiểm Thước#4029#.",
    
    "Skill.16240000.1": "Hoàng Thiểm Cực Tinh: Trảm Đoạn Thiên Không",
    "Skill.16240000.13": "Tuyệt kỹ của Noya - Khải Minh sở hữu 2 dạng thái, lần lượt dùng cự kiếm [Thự Quang] và trường kiếm [Phất Hiểu] để tấn công, gây sát thương trên diện rộng lớn. Khi thi triển Tuyệt kỹ, Noya - Khải Minh nhận [Cực Tinh]: Tăng &Param5&. Tuyệt kỹ có thể kích hoạt ##Ấn Ký Quang#1015#.",
    "Skill.16240000.2": "Tuyệt kỹ của Noya - Khải Minh sở hữu 2 dạng thái, lần lượt dùng cự kiếm [Thự Quang] và trường kiếm [Phất Hiểu] để tấn công, mặc định vào trận với Tuyệt kỹ ở dạng Cự kiếm.\nDạng Cự Kiếm: Bay vút lên không trung vung cự kiếm, gây sát thương đòn đánh thường hệ Quang trên diện rộng lớn tương đương <color=#fb8037>&Param1&x5</color> và <color=#fb8037>&Param2&</color> HP Tối Đa.\nDạng Trường Kiếm: Nhanh chóng lướt thân tấn công tốc độ cao, gây sát thương kỹ năng hệ Quang trên diện rộng lớn tương đương <color=#fb8037>&Param3&x7</color> HP Tối Đa, sau đó tạo ra một lĩnh vực gây sát thương kỹ năng hệ Quang trên diện rộng lớn tương đương <color=#fb8037>&Param4&x7</color> HP Tối Đa.\nKhi thi triển Tuyệt kỹ \"Hoàng Thiểm Cực Tinh: Trảm Đoạn Thiên Không\", Noya - Khải Minh nhận [Cực Tinh]: &Param5& tăng <color=#fb8037>&Param6&</color>, duy trì &Param7& giây.\nTuyệt kỹ \"Hoàng Thiểm Cực Tinh: Trảm Đoạn Thiên Không\" có thể kích hoạt ##Ấn Ký Quang#1015#, tạo ra ##Quang Diệu#4028#: Gây sát thương ấn ký hệ Quang diện rộng tương đương &Param8& HP Tối Đa, đồng thời gắn thêm 1 tầng ##Thiểm Thước#4029#.",
    
    "Skill.8210162.1": "!NONEED!",
    "Skill.8216201.1": "Bão Tố Lóe Sáng: Rực Rỡ",
    "Skill.8216201.13": "Mỗi khi đạn châu phá hủy khối pha lê hoặc tiêu diệt quái vật, sẽ tạo ra 1 tầng [Trụy Tinh] bên cạnh Noya - Khải Minh.\nKhi thi triển kỹ năng sẽ triệu hồi lưỡi kiếm ánh sáng rơi xuống gây sát thương diện rộng, đồng thời tiêu hao toàn bộ [Trụy Tinh], căn cứ theo số tầng tiêu hao để cường hóa đạn châu, giúp cầu năng lượng khi va chạm sẽ gây thêm sát thương diện rộng.",
    "Skill.8216201.2": "Mỗi khi đạn châu phá hủy khối pha lê hoặc tiêu diệt quái vật, sẽ tạo ra 1 tầng [Trụy Tinh] bên cạnh Noya - Khải Minh.\nKhi thi triển kỹ năng sẽ triệu hồi lưỡi kiếm ánh sáng rơi xuống gây sát thương diện rộng, đồng thời tiêu hao toàn bộ [Trụy Tinh], căn cứ theo số tầng tiêu hao để cường hóa đạn châu, giúp cầu năng lượng khi va chạm sẽ gây thêm sát thương diện rộng.",

    # === POTENTIAL (RIDGE) ===
    "Potential.511621.1": "Sau khi thi triển Kỹ Năng Viện Trợ, sẽ tự động thi triển thêm một lần nữa.",
    "Potential.511621.2": "Sau khi thi triển Kỹ Năng Viện Trợ [Bách Hoa Tề Phóng], sẽ tự động thi triển thêm một lần nữa.",
    "Potential.511622.1": "Tăng &Param1& do mưa hạt giống của Kỹ Năng Viện Trợ gây ra, đồng thời rút ngắn khoảng cách giữa các đợt sát thương của mưa hạt giống.",
    "Potential.511622.2": "&Param1& do mưa hạt giống của Kỹ Năng Viện Trợ [Bách Hoa Tề Phóng] gây ra tăng <color=#0abec5>&Param2&</color>, khoảng cách giữa các đợt sát thương rút ngắn <color=#0abec5>30%</color>.",
    "Potential.511623.1": "Kéo dài thời gian duy trì của [Cầu Hạt Giống], tăng &Param1& gây ra, đồng thời có thể gắn thêm ##Ấn Ký Địa: Địa Mạch#2029#.",
    "Potential.511623.2": "Thời gian duy trì của [Cầu Hạt Giống] kéo dài <color=#0abec5>50%</color>, &Param1& gây ra tăng <color=#0abec5>&Param2&</color>, đồng thời có thể gắn thêm ##Ấn Ký Địa: Địa Mạch#2029#.",
    "Potential.511624.1": "Tăng &Param1& và phạm vi phát nổ của [Cầu Hạt Giống], sát thương từ [Cầu Hạt Giống] có thể kích hoạt thêm một [Cầu Hạt Giống] khác.",
    "Potential.511624.2": "&Param1& do [Cầu Hạt Giống] gây ra tăng <color=#0abec5>&Param2&</color>, phạm vi sát thương tăng <color=#0abec5>50%</color>. Sát thương từ [Cầu Hạt Giống] có thể kích hoạt thêm một [Cầu Hạt Giống] khác, hiệu ứng này trên cùng một mục tiêu mỗi giây kích hoạt tối đa 1 lần.",
    "Potential.511625.1": "Khi thi triển Kỹ Năng Viện Trợ, tăng dần sát thương kỹ năng theo thời gian, hiệu ứng này sẽ bị xóa sau khi kỹ năng kết thúc.",
    "Potential.511625.2": "Khi thi triển Kỹ Năng Viện Trợ [Bách Hoa Tề Phóng], sát thương kỹ năng của Lĩnh Xuyên mỗi 0.5 giây tăng <color=#ec6d21>&Param2&</color>, hiệu ứng này sẽ bị xóa sau khi kỹ năng kết thúc.",
    "Potential.511626.1": "Mưa hạt giống của Kỹ Năng Viện Trợ có thể làm giảm &Param1& của mục tiêu.",
    "Potential.511626.2": "Khi mưa hạt giống của Kỹ Năng Viện Trợ [Bách Hoa Tề Phóng] gây sát thương, &Param1& của mục tiêu giảm <color=#ec6d21>&Param2&</color> điểm, duy trì &Param3& giây, có thể cộng dồn &Param4& tầng.",
    "Potential.511627.1": "Tăng &Param1& và phạm vi của mưa hạt giống từ Kỹ Năng Viện Trợ.",
    "Potential.511627.2": "&Param1& do mưa hạt giống của Kỹ Năng Viện Trợ [Bách Hoa Tề Phóng] gây ra tăng <color=#ec6d21>&Param2&</color>, phạm vi sát thương tăng 30%.",
    "Potential.511628.1": "Tăng &Param1& của Lĩnh Xuyên gây ra lên mục tiêu mang [Cầu Hạt Giống].",
    "Potential.511628.2": "&Param1& của Lĩnh Xuyên gây ra lên mục tiêu mang [Cầu Hạt Giống] tăng <color=#ec6d21>&Param2&</color>.",
    "Potential.511629.1": "Mục tiêu bị gắn [Cầu Hạt Giống] sẽ bị giảm &Param1&.",
    "Potential.511629.2": "&Param1& của mục tiêu mang [Cầu Hạt Giống] giảm <color=#ec6d21>&Param2&</color> điểm.",

    # === POTENTIAL (NOYA) ===
    "Potential.516201.1": "Tăng số lần tấn công bằng trường kiếm của Kỹ Năng Chính \"Bão Tố Lóe Sáng: Rực Rỡ\", đồng thời bắn ra nhiều luồng [Lưu Quang] tấn công mục tiêu.",
    "Potential.516201.2": "Số lần tấn công bằng trường kiếm của Kỹ Năng Chính \"Bão Tố Lóe Sáng: Rực Rỡ\" tăng <color=#0abec5>4</color> lần, đồng thời bắn ra <color=#0abec5>9</color> luồng [Lưu Quang], mỗi luồng gây sát thương kỹ năng hệ Quang tương đương <color=#0abec5>&Param1&</color> HP Tối Đa.",
    "Potential.516202.1": "Mỗi khi Noya - Khải Minh bắn ra số luồng [Lưu Quang] nhất định, sẽ nhận Kỹ Năng Chính đặc biệt \"Lưu Ảnh Quang Diệu Trảm\", có thể gây sát thương trên diện rộng lớn. Trong đòn đánh thường, khi dùng trường kiếm phát động tấn công xung kích sẽ bắn ra nhiều luồng [Lưu Quang] tấn công mục tiêu.",
    "Potential.516202.2": "Mỗi khi Noya - Khải Minh tích lũy bắn ra <color=#0abec5>&Param1&</color> luồng [Lưu Quang], sẽ nhận Kỹ Năng Chính đặc biệt \"Lưu Ảnh Quang Diệu Trảm\": Vung trường kiếm tạo ra luồng kiếm quang khổng lồ, gây sát thương kỹ năng hệ Quang tương đương <color=#0abec5>&Param2&x6</color> HP Tối Đa, có thể kích hoạt ##Ấn Ký Quang#1015#.\nTrong đòn đánh thường, khi dùng trường kiếm phát động tấn công xung kích có thể bắn ra <color=#0abec5>3</color> luồng [Lưu Quang], mỗi luồng gây sát thương kỹ năng hệ Quang tương đương <color=#0abec5>&Param3&</color> HP Tối Đa.",
    "Potential.516203.1": "Khi Kỹ Năng Chính \"Bão Tố Lóe Sáng: Rực Rỡ\" tấn công, có thể tạo ra nhiều [Trụy Tinh]. Đòn tấn công xung kích trong đòn đánh thường chuyển thành dùng cự kiếm tấn công và có thể tạo ra [Trụy Tinh]. Khi Noya - Khải Minh kích hoạt ấn ký có thể tạo ra [Trụy Tinh]. Các [Trụy Tinh] nói trên đều có thể gây sát thương diện rộng.",
    "Potential.516203.2": "Khi Kỹ Năng Chính \"Bão Tố Lóe Sáng: Rực Rỡ\" tấn công, có thể tạo thêm <color=#0abec5>2</color> [Trụy Tinh]. Đòn tấn công xung kích trong đòn đánh thường chuyển thành dùng cự kiếm tấn công, gây sát thương đòn đánh thường hệ Quang tương đương <color=#0abec5>&Param1&</color> HP Tối Đa và tạo ra 1 [Trụy Tinh]. Khi Noya - Khải Minh kích hoạt ấn ký, sẽ tạo ra <color=#0abec5>1</color> [Trụy Tinh], hiệu ứng này mỗi 1 giây kích hoạt tối đa 1 lần. Khi các [Trụy Tinh] nói trên tấn công mục tiêu, sẽ gây sát thương đòn đánh thường hệ Quang diện rộng tương đương <color=#0abec5>&Param2&</color> HP Tối Đa.",
    "Potential.516204.1": "Noya - Khải Minh có thể hấp thu các [Trụy Tinh] còn sót lại ở xung quanh; sau khi hấp thu đủ số lượng nhất định, đòn đánh thường kế tiếp có thể phát động \"Đoạn Tội Thiên Tinh Trụy\" gây sát thương trên diện rộng lớn. Tăng phạm vi sát thương và &Param3& của đòn tấn công bằng cự kiếm trong đòn đánh thường, đồng thời có thể kích hoạt ##Ấn Ký Quang#1015#.",
    "Potential.516204.2": "Noya - Khải Minh có thể hấp thu các [Trụy Tinh] còn sót lại ở xung quanh, mỗi khi tích lũy hấp thu <color=#0abec5>&Param1&</color> [Trụy Tinh], ở đòn đánh thường kế tiếp sẽ phát động đòn đánh thường đặc biệt \"Đoạn Tội Thiên Tinh Trụy\": Ngưng tụ năng lượng vung cự kiếm nện mạnh xuống đất, gây sát thương đòn đánh thường hệ Quang trên diện rộng lớn tương đương <color=#0abec5>&Param2&x2</color> HP Tối Đa, có thể kích hoạt ##Ấn Ký Quang#1015#.\nKhi dùng cự kiếm tấn công trong đòn đánh thường, phạm vi sát thương được tăng, &Param3& gây ra tăng <color=#0abec5>&Param4&</color>, đồng thời có thể kích hoạt ##Ấn Ký Quang#1015#.",
    "Potential.516205.1": "[Lưu Quang] do Noya - Khải Minh bắn ra có thể quay ngược trở lại gây sát thương. Tăng &Param2& do đòn tấn công bằng trường kiếm và [Lưu Quang] của Noya - Khải Minh gây ra.",
    "Potential.516205.2": "[Lưu Quang] do Noya - Khải Minh bắn ra có thể quay ngược trở lại tấn công mục tiêu, gây sát thương kỹ năng hệ Quang tương đương <color=#fb8037>&Param1&</color> HP Tối Đa.\n&Param2& do đòn tấn công bằng trường kiếm và [Lưu Quang] của Noya - Khải Minh gây ra tăng <color=#fb8037>&Param3&</color>.",
    "Potential.516206.1": "Khi thi triển Kỹ Năng Chính đặc biệt, Tuyệt kỹ của Noya - Khải Minh sẽ chuyển sang dạng Trường kiếm. Tăng &Param1& do đòn tấn công bằng trường kiếm và [Lưu Quang] của Noya - Khải Minh gây ra lên mục tiêu mang ##Thiểm Thước#4029#.",
    "Potential.516206.2": "Khi thi triển Kỹ Năng Chính \"Lưu Ảnh Quang Diệu Trảm\", Tuyệt kỹ của Noya - Khải Minh chuyển sang dạng Trường kiếm.\n&Param1& do đòn tấn công bằng trường kiếm và [Lưu Quang] của Noya - Khải Minh gây ra lên mục tiêu mang ##Thiểm Thước#4029# tăng <color=#fb8037>&Param2&</color>.",
    "Potential.516207.1": "[Lưu Quang] có thể kích hoạt ##Ấn Ký Quang#1015#, đồng thời có xác suất nhất định tăng phạm vi sát thương. Khi thi triển Kỹ Năng Chính, tăng &Param2& của Noya - Khải Minh và &Param4& của Lữ Khách Cân Bằng hệ Quang.",
    "Potential.516207.2": "[Lưu Quang] có thể kích hoạt ##Ấn Ký Quang#1015#, đồng thời có &Param1&% xác suất tăng phạm vi sát thương.\nKhi thi triển Kỹ Năng Chính, &Param2& của Noya - Khải Minh tăng <color=#fb8037>&Param3&</color>, &Param4& của Lữ Khách Cân Bằng hệ Quang tăng <color=#fb8037>&Param5&</color>, duy trì &Param6& giây, có thể cộng dồn &Param7& tầng.",
    "Potential.516208.1": "Khi thi triển đòn đánh thường đặc biệt \"Đoạn Tội Thiên Tinh Trụy\", sẽ tạo ra một lĩnh vực gây nhiều đợt sát thương. Tăng &Param2& do đòn tấn công bằng cự kiếm và [Trụy Tinh] của Noya - Khải Minh gây ra.",
    "Potential.516208.2": "Khi thi triển đòn đánh thường đặc biệt \"Đoạn Tội Thiên Tinh Trụy\", sẽ tạo ra một lĩnh vực gây sát thương đòn đánh thường hệ Quang tương đương <color=#fb8037>&Param1&x6</color> HP Tối Đa.\n&Param2& do đòn tấn công bằng cự kiếm và [Trụy Tinh] của Noya - Khải Minh gây ra tăng <color=#fb8037>&Param3&</color>.",
    "Potential.516209.1": "Khi [Trụy Tinh] tan biến, sẽ phóng ra tia sét tấn công mục tiêu. Khi thi triển Kỹ Năng Chính, tăng &Param2& của Noya - Khải Minh.",
    "Potential.516209.2": "Khi [Trụy Tinh] tan biến, sẽ phóng ra 1 tia sét tấn công mục tiêu, gây sát thương đòn đánh thường hệ Quang tương đương <color=#fb8037>&Param1&</color> HP Tối Đa.\nKhi thi triển Kỹ Năng Chính, &Param2& của Noya - Khải Minh tăng <color=#fb8037>&Param3&</color>, duy trì &Param4& giây.",
    "Potential.516210.1": "Khi thi triển đòn đánh thường đặc biệt \"Đoạn Tội Thiên Tinh Trụy\", Tuyệt kỹ của Noya - Khải Minh sẽ chuyển sang dạng Cự kiếm. Tăng &Param1& do đòn tấn công bằng cự kiếm và [Trụy Tinh] của Noya - Khải Minh gây ra.",
    "Potential.516210.2": "Khi thi triển đòn đánh thường đặc biệt \"Đoạn Tội Thiên Tinh Trụy\", Tuyệt kỹ của Noya - Khải Minh chuyển sang dạng Cự kiếm.\n&Param1& do đòn tấn công bằng cự kiếm và [Trụy Tinh] của Noya - Khải Minh gây ra tăng <color=#fb8037>&Param2&</color> điểm.",
    "Potential.516211.1": "Tăng &Param1& của Noya - Khải Minh gây ra lên mục tiêu mang ##Thiểm Thước#4029#. Tăng &Param3& của Noya - Khải Minh.",
    "Potential.516211.2": "&Param1& của Noya - Khải Minh gây ra lên mục tiêu mang ##Thiểm Thước#4029# tăng <color=#fb8037>&Param2&</color>.\n&Param3& của Noya - Khải Minh tăng <color=#fb8037>&Param4&</color> điểm.",
    "Potential.516212.1": "Lữ Khách hệ Quang trong đội giúp tăng ##Xuyên Thấu Hệ Quang#2068# của Noya - Khải Minh.",
    "Potential.516212.2": "Mỗi 1 Lữ Khách hệ Quang trong đội sẽ giúp ##Xuyên Thấu Hệ Quang#2068# của Noya - Khải Minh tăng <color=#fb8037>&Param2&</color> điểm.",
    "Potential.516213.1": "Tăng &Param1& của Noya - Khải Minh.",
    "Potential.516213.2": "&Param1& của Noya - Khải Minh tăng <color=#fb8037>&Param2&</color> điểm.",
    "Potential.516221.1": "Sau đòn tấn công bằng cự kiếm trong Kỹ Năng Viện Trợ \"Sấm Sét Giáng Đòn: Phá Kích\", sẽ tạo ra một lĩnh vực gây nhiều đợt sát thương.",
    "Potential.516221.2": "Sau đòn tấn công bằng cự kiếm trong Kỹ Năng Viện Trợ \"Sấm Sét Giáng Đòn: Phá Kích\", sẽ tạo ra một lĩnh vực gây sát thương đòn đánh thường hệ Quang tương đương <color=#0abec5>&Param1&x6</color> HP Tối Đa.",
    "Potential.516222.1": "Khi đòn tấn công bằng cự kiếm trong Kỹ Năng Viện Trợ \"Sấm Sét Giáng Đòn: Phá Kích\" diễn ra, sẽ tạo ra nhiều [Trụy Tinh] tấn công mục tiêu.",
    "Potential.516222.2": "Khi đòn tấn công bằng cự kiếm trong Kỹ Năng Viện Trợ \"Sấm Sét Giáng Đòn: Phá Kích\" diễn ra, sẽ tạo ra <color=#0abec5>11</color> [Trụy Tinh], mỗi [Trụy Tinh] gây sát thương đòn đánh thường hệ Quang tương đương <color=#0abec5>&Param1&</color> HP Tối Đa.",
    "Potential.516223.1": "Khi đòn tấn công bằng trường kiếm trong Kỹ Năng Viện Trợ \"Sấm Sét Giáng Đòn: Phá Kích\" diễn ra, sẽ liên tục bắn ra [Lưu Quang] tấn công mục tiêu.",
    "Potential.516223.2": "Khi đòn tấn công bằng trường kiếm trong Kỹ Năng Viện Trợ \"Sấm Sét Giáng Đòn: Phá Kích\" diễn ra, sẽ liên tục bắn ra [Lưu Quang], mỗi 1 luồng gây sát thương kỹ năng hệ Quang tương đương <color=#0abec5>&Param1&</color> HP Tối Đa.",
    "Potential.516224.1": "Tăng số lần tấn công bằng trường kiếm trong Kỹ Năng Viện Trợ \"Sấm Sét Giáng Đòn: Phá Kích\".",
    "Potential.516224.2": "Số lần tấn công bằng trường kiếm trong Kỹ Năng Viện Trợ \"Sấm Sét Giáng Đòn: Phá Kích\" tăng <color=#0abec5>10</color> lần.",
    "Potential.516225.1": "Tăng phạm vi sát thương của [Trụy Tinh] tạo ra từ Kỹ Năng Viện Trợ \"Sấm Sét Giáng Đòn: Phá Kích\". Khi tạo ra [Trụy Tinh], tăng &Param1& của Noya - Khải Minh.",
    "Potential.516225.2": "Phạm vi sát thương của [Trụy Tinh] tạo ra từ Kỹ Năng Viện Trợ \"Sấm Sét Giáng Đòn: Phá Kích\" được tăng. Mỗi 1 lần tạo ra [Trụy Tinh], &Param1& của Noya - Khải Minh tăng <color=#fb8037>&Param2&</color>, duy trì &Param3& giây, có thể cộng dồn &Param4& tầng.",
    "Potential.516226.1": "Sau đòn tấn công bằng cự kiếm trong Kỹ Năng Viện Trợ \"Sấm Sét Giáng Đòn: Phá Kích\", Tuyệt kỹ của Noya - Khải Minh sẽ chuyển sang dạng Cự kiếm. Khi đòn tấn công bằng trường kiếm của Noya - Khải Minh gây sát thương, sẽ tăng &Param1& của bản thân.",
    "Potential.516226.2": "Sau đòn tấn công bằng cự kiếm trong Kỹ Năng Viện Trợ \"Sấm Sét Giáng Đòn: Phá Kích\", Tuyệt kỹ của Noya - Khải Minh chuyển sang dạng Cự kiếm.\nKhi đòn tấn công bằng trường kiếm của Noya - Khải Minh gây sát thương, &Param1& của bản thân tăng <color=#fb8037>&Param2&</color>, duy trì &Param3& giây, có thể cộng dồn &Param4& tầng.",
    "Potential.516227.1": "Tăng &Param1& do đòn tấn công bằng cự kiếm và [Trụy Tinh] của Noya - Khải Minh gây ra.",
    "Potential.516227.2": "&Param1& do đòn tấn công bằng cự kiếm và [Trụy Tinh] của Noya - Khải Minh gây ra tăng <color=#fb8037>&Param2&</color>.",
    "Potential.516228.1": "Khi bắn ra [Lưu Quang] có xác suất nhất định tăng phạm vi sát thương. Tăng &Param2& do đòn tấn công bằng trường kiếm và [Lưu Quang] của Noya - Khải Minh gây ra.",
    "Potential.516228.2": "Khi bắn ra [Lưu Quang] có &Param1&% xác suất tăng phạm vi sát thương.\n&Param2& do đòn tấn công bằng trường kiếm và [Lưu Quang] của Noya - Khải Minh gây ra tăng <color=#fb8037>&Param3&</color>.",
    "Potential.516229.1": "Sau đòn tấn công bằng trường kiếm trong Kỹ Năng Viện Trợ \"Sấm Sét Giáng Đòn: Phá Kích\", Tuyệt kỹ của Noya - Khải Minh sẽ chuyển sang dạng Trường kiếm. Khi cự kiếm của Noya - Khải Minh gây sát thương, sẽ tăng &Param1& của bản thân.",
    "Potential.516229.2": "Sau đòn tấn công bằng trường kiếm trong Kỹ Năng Viện Trợ \"Sấm Sét Giáng Đòn: Phá Kích\", Tuyệt kỹ của Noya - Khải Minh chuyển sang dạng Trường kiếm.\nKhi cự kiếm của Noya - Khải Minh gây sát thương, &Param1& của bản thân tăng <color=#fb8037>&Param2&</color>, duy trì &Param3& giây, có thể cộng dồn &Param4& tầng.",
    "Potential.516230.1": "Tăng &Param1& do đòn tấn công bằng trường kiếm và [Lưu Quang] của Noya - Khải Minh gây ra.",
    "Potential.516230.2": "&Param1& do đòn tấn công bằng trường kiếm và [Lưu Quang] của Noya - Khải Minh gây ra tăng <color=#fb8037>&Param2&</color>.",
    "Potential.516231.1": "Lữ Khách hệ Quang trong đội giúp tăng &Param1& của toàn bộ Lữ Khách hệ Quang.",
    "Potential.516231.2": "Mỗi 1 Lữ Khách hệ Quang trong đội giúp &Param1& của toàn bộ Lữ Khách hệ Quang tăng <color=#fb8037>&Param2&</color>.",
    "Potential.516232.1": "Khi Lữ Khách Chủ Lực hệ Quang thi triển Kỹ Năng Chính, tăng &Param1& của Noya - Khải Minh.",
    "Potential.516232.2": "Khi Lữ Khách Chủ Lực hệ Quang thi triển Kỹ Năng Chính, &Param1& của Noya - Khải Minh tăng <color=#fb8037>&Param2&</color>, duy trì &Param3& giây.",
    "Potential.516233.1": "Khi bất kỳ Lữ Khách hệ Quang nào trong đội thi triển Kỹ Năng Chính hoặc Kỹ Năng Viện Trợ, tăng &Param1& của Noya - Khải Minh.",
    "Potential.516233.2": "Khi bất kỳ Lữ Khách hệ Quang nào trong đội thi triển Kỹ Năng Chính hoặc Kỹ Năng Viện Trợ, &Param1& của Noya - Khải Minh tăng <color=#fb8037>&Param2&</color>, duy trì &Param3& giây, có thể cộng dồn &Param4& tầng.",
    "Potential.516241.1": "Khi Noya - Khải Minh phát động Tuyệt kỹ dạng Trường kiếm \"Hoàng Thiểm Cực Tinh: Trảm Đoạn Thiên Không\", sẽ bắn ra nhiều luồng [Lưu Quang] tấn công mục tiêu. Tăng &Param2& của Noya - Khải Minh.",
    "Potential.516241.2": "Khi Noya - Khải Minh phát động Tuyệt kỹ dạng Trường kiếm \"Hoàng Thiểm Cực Tinh: Trảm Đoạn Thiên Không\", sẽ bắn ra 7 luồng [Lưu Quang], mỗi 1 luồng gây sát thương kỹ năng hệ Quang tương đương <color=#fb8037>&Param1&</color> HP Tối Đa.\n&Param2& của Noya - Khải Minh tăng <color=#fb8037>&Param3&</color>.",
    "Potential.516242.1": "Sau khi Noya - Khải Minh thi triển Tuyệt kỹ dạng Cự kiếm \"Hoàng Thiểm Cực Tinh: Trảm Đoạn Thiên Không\", sẽ tạo ra một lĩnh vực tấn công mục tiêu. Tăng &Param2& của Noya - Khải Minh.",
    "Potential.516242.2": "Sau khi Noya - Khải Minh thi triển Tuyệt kỹ dạng Cự kiếm \"Hoàng Thiểm Cực Tinh: Trảm Đoạn Thiên Không\", sẽ tạo ra một lĩnh vực gây sát thương đòn đánh thường hệ Quang tương đương <color=#fb8037>&Param1&x6</color> HP Tối Đa.\n&Param2& của Noya - Khải Minh tăng <color=#fb8037>&Param3&</color>.",
    "Potential.516243.1": "Khi Noya - Khải Minh ở trạng thái [Cực Tinh], có thể tăng thêm &Param1& của bản thân, đồng thời mỗi khoảng thời gian nhất định sẽ hồi phục năng lượng.",
    "Potential.516243.2": "Khi Noya - Khải Minh ở trạng thái [Cực Tinh], có thể tăng thêm &Param1& của bản thân thêm <color=#fb8037>&Param2&</color>, đồng thời mỗi &Param3& giây sẽ hồi phục <color=#fb8037>&Param4&</color> điểm năng lượng.",

    # === TALENT (110 ITEMS) ===
    # General talent names & effects:
    # We will map them systematically below.
}

# Systematic mapping for Talent and SecondarySkill
for item in items:
    k = item["key"]
    zh = item.get("zh", "")
    en = item.get("en", "")
    table = item.get("table", "")
    
    if k in translations:
        continue
        
    if table == "SecondarySkill":
        if k.endswith(".1"):
            translations[k] = "Tế Vũ Nhuận Vật"
        elif k.endswith(".2"):
            translations[k] = "[Phù Tuyết] nhận thêm hiệu ứng: Mỗi tầng tăng sát thương kỹ năng của bản thân thêm <color=#ec6d21>{1}</color>."
            
    elif table == "Talent":
        if k.endswith(".1"):
            if zh == "生命强化":
                translations[k] = "Cường Hóa HP"
            elif zh == "光系伤害提升":
                translations[k] = "Tăng Sát Thương Hệ Quang"
            elif zh == "技能伤害提升":
                translations[k] = "Tăng Sát Thương Kỹ Năng"
            elif zh == "普攻伤害提升":
                translations[k] = "Tăng Sát Thương Đòn Đánh Thường"
            elif zh == "暴击伤害提升":
                translations[k] = "Tăng Sát Thương Bạo Kích"
            elif zh == "埋葬的过往":
                translations[k] = "Quá Khứ Chôn Vùi"
            elif zh == "守夜人之责":
                translations[k] = "Trách Nhiệm Kẻ Canh Đêm"
            elif zh == "跨越命运的觉悟":
                translations[k] = "Quyết Tâm Vượt Qua Vận Mệnh"
            elif zh == "极星闪耀于黑夜":
                translations[k] = "Cực Tinh Tỏa Sáng Giữa Màn Đêm"
            elif zh == "与你相逢在黎明":
                translations[k] = "Tương Phùng Cùng Người Nơi Bình Minh"
            else:
                print(f"Unknown Talent .1: {k} | {zh}")
        elif k.endswith(".2"):
            if k == "Talent.1620116.2":
                translations[k] = "Trong trạng thái [Cực Tinh], sát thương bạo kích của Noya - Khải Minh tăng <color=#0abec5>&Param1&</color>; khi Noya - Khải Minh gây bất kỳ sát thương nào sẽ nhận được [Cực Tinh], hiệu ứng này mỗi 5 phút có thể kích hoạt 1 lần."
            elif k == "Talent.1620232.2":
                translations[k] = "Giới hạn HP của Noya - Khải Minh tăng <color=#0abec5>&Param1&</color>, bội số sát thương do \"Lưu Ảnh Quang Diệu Trảm\" và \"Đoạn Tội Thiên Tinh Trụy\" gây ra lên mục tiêu mang ##Thiểm Thước#4029# tăng <color=#0abec5>&Param2&</color>."
            elif k == "Talent.1620348.2":
                translations[k] = "Sát thương hệ Quang do Noya - Khải Minh gây ra lên kẻ địch cấp Tinh Anh trở lên tăng <color=#0abec5>&Param1&</color>."
            elif k == "Talent.1620464.2":
                translations[k] = "Sau khi kích hoạt ##Ấn Ký Quang#1015#, sát thương đòn đánh thường do Noya - Khải Minh gây ra tăng <color=#0abec5>&Param1&</color>, duy trì &Param2& giây."
            elif k == "Talent.1620580.2":
                translations[k] = "Khi HP của Noya - Khải Minh cao hơn 20%, bội số sát thương do trường kiếm [Phất Hiểu] gây ra tăng <color=#0abec5>&Param1&</color>, bội số sát thương do cự kiếm [Thự Quang] gây ra tăng <color=#0abec5>&Param2&</color>."
            elif "基础生命提升" in zh:
                translations[k] = "HP cơ bản tăng <color=#0abec5>&Param1&</color>."
            elif "光系伤害提升" in zh:
                translations[k] = "Sát thương hệ Quang tăng <color=#0abec5>&Param1&</color>."
            elif "技能伤害提升" in zh:
                translations[k] = "Sát thương kỹ năng tăng <color=#0abec5>&Param1&</color>."
            elif "普攻伤害提升" in zh:
                translations[k] = "Sát thương đòn đánh thường tăng <color=#0abec5>&Param1&</color>."
            elif "暴击伤害提升" in zh:
                translations[k] = "Sát thương bạo kích tăng <color=#0abec5>&Param1&</color>."
            else:
                print(f"Unknown Talent .2: {k} | {zh}")

out_items = []
missing = 0
for item in items:
    k = item["key"]
    if k not in translations:
        print(f"MISSING: {k}")
        missing += 1
    new_vi = translations.get(k, item.get("current_vi", ""))
    out_obj = {
        "table": item["table"],
        "key": item["key"],
        "en": item["en"],
        "zh": item["zh"],
        "current_vi": item.get("current_vi", ""),
        "vi": new_vi
    }
    out_items.append(out_obj)

print(f"Processed {len(out_items)} items. Missing: {missing}")

out_path = Path("StellaSora_VietHoa/work/batches/batch_light_group1_noya_approved.json")
out_path.write_text(json.dumps(out_items, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {len(out_items)} items to {out_path}")
