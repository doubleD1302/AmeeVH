import json
import re
from pathlib import Path
import sys

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.append(str(ROOT / "tools"))
from token_validator import extract_tokens

INPUT_FILE = ROOT / "work" / "batches" / "audit_batch2_ui_sys_ach.json"
OUTPUT_FILE = ROOT / "work" / "batches" / "audit_batch2_ui_sys_ach_polished.json"
MOD_FILE = ROOT / "work" / "batches" / "audit_batch2_modifications.json"

# Exact translations for untranslated / broken entries
EXACT_KEY_MAP = {
    # 17 Token-fixed entries
    "UIText.ActivityLevels_Lock_Day_Color_Common.1": "Mở khóa sau <color=#{0}>{1} ngày</color>",
    "UIText.ActivityLevels_Lock_Hour_Color_Common.1": "Mở khóa sau <color=#{0}>{1} giờ</color>",
    "UIText.ActivityLevels_Lock_Min_Color_Common.1": "Mở khóa sau <color=#{0}>{1} phút</color>",
    "UIText.ActivityLevels_Lock_Sec_Color_Common.1": "Mở khóa sau <color=#{0}>{1} giây</color>",
    "UIText.Gacha_Prob_Time.1": "Thời gian Sự Kiện:<color=#00000000>.</color>",
    "UIText.JP_CV.1": "CV Tiếng Nhật:<color=#00000000>.</color>",
    "UIText.ZN_CV.1": "CV Tiếng Trung:<color=#00000000>.</color>",
    "UIText.Soldier_Battle_GiveUp.1": "Chọn <color=#CE996E>Từ Bỏ</color> sẽ hủy bỏ toàn bộ tiến trình điều tra hiện tại.",
    "UIText.Soldier_Battle_Result.1": "Bạn có chắc chắn muốn <color=#CE996E>Từ Bỏ Điều Tra</color> không?",
    "UIText.Soldier_FinishTips.1": "Chọn <color=#CE996E>Từ Bỏ</color> sẽ hủy bỏ toàn bộ tiến trình điều tra hiện tại.",
    "UIText.Soldier_Resolveadispute_SucessTip.1": "Đổ xúc xắc đạt từ <color=#e0608f>{0}</color> trở lên để vượt qua kiểm tra",
    "UIText.StarTower_Event_Book_Source.1": "Yêu Cầu:<color=#00000000>.</color>",
    "UIText.StarTower_Sweep_Option_2.1": "Cường hóa (<color={0}>{1}</color> <sprite name=\"item_11_small\">)",
    "UIText.TowerDef_LevelPreTime.1": "Đợt tiếp theo bắt đầu sau <color=#08d3d4>{0}",

    # Commission (hoa hồng) complete elimination
    "UIText.Agent_Accpect.1": "Nhận Nhiệm Vụ Ủy Thác",
    "UIText.Agent_Again_Accept_Fail.1": "Nhiệm vụ ủy thác khẩn cấp không thể tự động nhận liên tiếp. Vui lòng nhận thủ công!",
    "UIText.Agent_Again_Fail.1": "Nhiệm vụ ủy thác vừa hoàn thành không thể phái đi lần nữa",
    "UIText.Agent_Build.1": "Lịch Sử Ủy Thác",
    "UIText.Agent_Delegate_Now.1": "Đang làm ủy thác: {0}",
    "UIText.Agent_GiveUp_Confirm.1": "Nếu triệu hồi về, bạn sẽ không nhận được phần thưởng của Nhiệm Vụ Ủy Thác này. Bạn có chắc chắn muốn triệu hồi?",
    "UIText.Agent_Max_Accepted.1": "Đã đạt giới hạn số lượng Nhiệm Vụ Ủy Thác",
    "UIText.Agent_Reward_Title.1": "Phần Thưởng Ủy Thác",
    "UIText.Agent_Tab_Unlock.1": "Hiện không có nhiệm vụ ủy thác nào để nhận",
    "UIText.City_1_1_Search_03.1": "Ngoài vài lời đồn thổi bên lề, chẳng thu thập được thông tin hay ủy thác nào hữu ích cả.",
    "UIText.Guide_24_2.1": "Phái Lữ Khách đi làm nhiệm vụ ủy thác để rinh về thật nhiều phần thưởng nhé!",
    "UIText.Guide_24_3.1": "Mỗi nhiệm vụ ủy thác sẽ có yêu cầu đội hình khác nhau — nhớ kiểm tra kỹ trước khi xuất phát nhé!",
    "UIText.Guide_24_4.1": "Nào, cùng phái đội thám hiểm đi làm nhiệm vụ ủy thác đầu tiên thôi!",
    "UIText.Guide_24_5.1": "Xác nhận thời gian phái cử là nhiệm vụ ủy thác sẽ bắt đầu ngay!",
    "UIText.Special_Agent_Notice.1": "Ủy Thác Khẩn Cấp không tính vào Giới Hạn Ủy Thác",
    "DictionaryDiagram.90010102.2": "Bên cạnh nhiệm vụ thường nhật, mỗi ngày còn xuất hiện ngẫu nhiên một số nhiệm vụ ủy thác đặc biệt.",

    # Ultimate (Tuyệt Kỹ / Tuyệt Đỉnh)
    "UIText.Action_Fire4.1": "Tuyệt Kỹ",
    "UIText.Char_Skill_Type_4.1": "Tuyệt Kỹ",
    "UIText.Enums_Effect_58.1": "Sát Thương Tuyệt Kỹ",
    "UIText.JointDrill_Difficulty_Name_4.1": "Tuyệt Đỉnh",
    "UIText.Talent_Skill_Ultimate.1": "Tuyệt Kỹ",

    # JointDrill Difficulty & Modes
    "UIText.JointDrill_Difficulty_Name_1.1": "Thường",
    "UIText.JointDrill_Difficulty_Name_2.1": "Khó",
    "UIText.JointDrill_Difficulty_Name_3.1": "Cực Khó",
    "UIText.JointDrill_Difficulty_Name_5.1": "Siêu Việt",
    "UIText.JointDrill_Difficulty_Name_6.1": "Hỗn Loạn",
    "UIText.JointDrill_BossSkill_Title.1": "Cơ Chế Thủ Lĩnh",
    "UIText.JointDrill_Boss_Info.1": "Cơ Chế Thủ Lĩnh",
    "UIText.JointDrill_Boss_Die.1": "Đã Vượt",
    "UIText.JointDrill_Level_Lock.1": "Vượt độ khó trước để mở khóa.",
    "UIText.JointDrill_Lock_Tip.1": "Vượt độ khó trước để mở khóa.",
    "UIText.JointDrill_Btn_Start_Challenge_Fast.1": "Càn Quét",
    "UIText.JointDrill_Build_Damage_Text.1": "Sát Thương Gây Ra",
    "UIText.JointDrill_Build_NotMeetingCond.1": "Đội hình chưa đủ điều kiện để vào ải",
    "UIText.JointDrill_Build_Select_Tip.1": "Cùng một Lữ Khách không thể xuất trận hai lần trong Âm Vang Hồi Kết.",
    "UIText.JointDrill_Give_Up_Tip.1": "Dừng khiêu chiến Âm Vang Hồi Kết lần này?",
    "UIText.JointDrill_Give_Up_Tip_2.1": "※Lệnh Quyết Đấu sẽ không được hoàn trả.",
    "UIText.JointDrill_Reward_Window_Title.1": "Phần Thưởng Âm Vang Hồi Kết",
    "UIText.JointDrill_Tickets_NotEnough.1": "Không đủ Lệnh Quyết Đấu",
    "UIText.JointDrill_Tickets_Refresh_Time.1": "Lệnh Quyết Đấu được hồi phục sau: {0}",
    "UIText.JointDrill_Fast_Battle_Tip_Text.1": "Dùng Lệnh Quyết Đấu để Càn Quét và nhận phần thưởng ngay lập tức.",
    "UIText.JointDrill_Fast_Battle_Title.1": "Càn Quét Nhanh",
    "UIText.JointDrill_SelectBuild_Tip.1": "Chưa chọn Bản Ghi, không thể khiêu chiến.",

    # Records Management & Dismantle
    "UIText.BUILD_01.1": "Bản Ghi đang khóa không thể phân giải!",
    "UIText.BUILD_04.1": "Đã đạt giới hạn số lượng Bản Ghi.\nKhông thể lưu thêm dữ liệu Cự Tháp.\nĐến giao diện Quản Lý Bản Ghi ngay?",
    "UIText.BUILD_08.1": "Đã phân giải Bản Ghi! Bạn nhận được:",
    "UIText.BUILD_12.1": "Đã phân giải Bản Ghi!",
    "UIText.Build_LockDelete.1": "Bản Ghi đang khóa không thể phân giải!",
    "UIText.Build_Btn_Skip.1": "Hủy Lưu Bản Ghi",
    "UIText.Agent_Build_Same_Cant_Delete.1": "Một số Bản Ghi đang thực hiện ủy thác, không thể phân giải!",
    "UIText.Agent_Non_Build.1": "Không có Bản Ghi nào thỏa mãn yêu cầu",
    "UIText.BdConvert_CheckTips.1": "Chứa các Bản Ghi có giá trị cao. Bạn có chắc chắn muốn nộp không?",
    "UIText.BdConvert_SubmitNoneTips.1": "Hãy chọn ít nhất 1 bộ Bản Ghi để nộp",
    "UIText.Build_Attribute_DescTip.1": "Đánh giá xếp hạng Bản Ghi sẽ gia tăng thêm thuộc tính thưởng trong trận chiến.",
    "UIText.Build_Attribute_Level.1": "Xếp Hạng Bản Ghi {0}",
    "UIText.EnemyInfo_Window_StoryTitle.1": "Hồ Sơ",
    "UIText.Friend_Tog_Info.1": "Hồ Sơ",
    "UIText.GachaHistory_Desc.1": "*Có thể xem lịch sử chiêu mộ trong vòng 6 tháng gần nhất tại trang này.",
    "UIText.InfinityTower_Recommend_Tips.1": "Cấp độ Lữ Khách hoặc điểm Bản Ghi của bạn <color=#ff0000>thấp hơn</color> mức đề xuất, khiêu chiến sẽ <color=#ff0000>vô cùng gian nan</color>! Bạn vẫn muốn tiếp tục chứ?",
    "UIText.Guide_5_2.1": "Các <color=#EA5946>Tiềm Năng</color> và <color=#EA5946>Kỹ Năng Bí Văn</color> được kích hoạt sẽ quyết định <color=#EA5946>Đánh Giá Bản Ghi</color>. Đánh giá càng cao, Bản Ghi càng mạnh mẽ.",
    "UIText.Guide_5_3.1": "<color=#EA5946>Bản Ghi</color> được <color=#EA5946>ràng buộc</color> cố định với các Lữ Khách trong chuyến thám hiểm này và không thể thay đổi khi mang đi tác chiến.",

    # Achievement Names & Descriptions
    "Achievement.658.1": "Kẻ Thám Hiểm Thâm Tầng I",
    "Achievement.658.2": "Vượt qua Vực Sâu Hiểm Nguy thành công 1 lần.",
    "Achievement.659.1": "Kẻ Thám Hiểm Thâm Tầng II",
    "Achievement.659.2": "Vượt qua Vực Sâu Hiểm Nguy thành công 5 lần.",
    "Achievement.660.1": "Kẻ Thám Hiểm Thâm Tầng III",
    "Achievement.660.2": "Vượt qua Vực Sâu Hiểm Nguy thành công 10 lần.",
    "Achievement.661.1": "Kẻ Thám Hiểm Thâm Tầng IV",
    "Achievement.661.2": "Vượt qua Vực Sâu Hiểm Nguy thành công 20 lần.",
    "Achievement.662.1": "Kẻ Thám Hiểm Thâm Tầng V",
    "Achievement.662.2": "Vượt qua Vực Sâu Hiểm Nguy thành công 50 lần.",
    "Achievement.87.1": "Xuất Loại Bạt Tụy",
    "Achievement.87.2": "Lần đầu tiên đạt Đĩa Nhạc phẩm chất [Xanh Lá]",
    "Achievement.88.1": "Trác Nhĩ Bất Phàm",
    "Achievement.88.2": "Lần đầu tiên đạt Đĩa Nhạc phẩm chất [Xanh Lam]",
    "Achievement.89.1": "Bách Luyện Thành Thép",
    "Achievement.89.2": "Lần đầu tiên đạt Đĩa Nhạc phẩm chất [Cam]",
    "Achievement.90.1": "Đăng Phong Tạo Cực",
    "Achievement.90.2": "Lần đầu tiên đạt Đĩa Nhạc phẩm chất [Cầu Vồng]",
    "Achievement.91.1": "Người Hướng Dẫn Hàng Đầu Ⅰ",
    "Achievement.91.2": "Đạt 10 Đĩa Nhạc phẩm chất [Cầu Vồng]",
    "Achievement.92.1": "Người Hướng Dẫn Hàng Đầu Ⅱ",
    "Achievement.92.2": "Đạt 20 Đĩa Nhạc phẩm chất [Cầu Vồng]",
    "Achievement.93.1": "Người Hướng Dẫn Hàng Đầu Ⅲ",
    "Achievement.93.2": "Đạt 30 Đĩa Nhạc phẩm chất [Cầu Vồng]",
    "Achievement.94.1": "Người Hướng Dẫn Hàng Đầu Ⅳ",
    "Achievement.94.2": "Đạt 50 Đĩa Nhạc phẩm chất [Cầu Vồng]",
    "Achievement.24.1": "Cứu Tinh Cánh Hoa",
    "Achievement.25.1": "Vung Tiền Như Nước Ⅰ",
    "Achievement.35.1": "Trùng Phùng Bình An Ⅰ",
    "Achievement.499.1": "Nghề Này Chẳng Hợp Với Ma Vương",
    "Achievement.500.1": "Bát Cơm Vững Chắc",
    "Achievement.56.1": "Vén Mây Thấy Trăng",
    "Achievement.571.1": "Kinh Nghiệm Chống Nắng",
    "Achievement.580.1": "Sợi Tóc Không Rụng",
    "Achievement.594.1": "Diệt Từ Trứng Nước",
    "Achievement.598.1": "Nhà Bếp Địa Ngục",
    "Achievement.610.1": "Máy Hút Thú Cưng",
    "Achievement.611.1": "Tam Trọng Né Tránh",
    "Achievement.614.1": "Ngang Tàng Tung Hoành",
    "Achievement.657.1": "Tạm Biệt Nhé, Ma Vương Đại Nhân",

    # Word Table Polish & Untranslated
    "Word.2024.1": "Quang Minh",
    "Word.2068.1": "Xuyên Kháng Quang",
    "Word.2068.2": "Sát thương gây ra bỏ qua một phần Kháng Thuộc Tính của mục tiêu, tối đa 250 điểm.",
    "Word.2069.1": "Xuyên Kháng Ám",
    "Word.2069.2": "Sát thương gây ra bỏ qua một phần Kháng Thuộc Tính của mục tiêu, tối đa 250 điểm.",
    "Word.2070.1": "Xuyên Kháng Thủy",
    "Word.2070.2": "Sát thương gây ra bỏ qua một phần Kháng Thuộc Tính của mục tiêu, tối đa 250 điểm.",
    "Word.2071.1": "Xuyên Kháng Hỏa",
    "Word.2071.2": "Sát thương gây ra bỏ qua một phần Kháng Thuộc Tính của mục tiêu, tối đa 250 điểm.",
    "Word.2072.1": "Xuyên Kháng Địa",
    "Word.2072.2": "Sát thương gây ra bỏ qua một phần Kháng Thuộc Tính của mục tiêu, tối đa 250 điểm.",
    "Word.2073.1": "Xuyên Kháng Phong",
    "Word.2073.2": "Sát thương gây ra bỏ qua một phần Kháng Thuộc Tính của mục tiêu, tối đa 250 điểm.",
    "Word.4044.1": "Kiếm Hồn",
    "Word.4044.2": "Noya Thức Tỉnh nhận được trạng thái này khi thi triển Kỹ Năng Chính. Khi Kiếm Hồn tích lũy đạt 100 tầng, tiêu hao toàn bộ tầng Kiếm Hồn để kích hoạt Đòn Kết Liễu: gây <color=#fb8037>&Param1& Tấn Công x2</color> thành Sát Thương Kỹ Năng hệ Quang diện rộng cho các mục tiêu lân cận.",
    "Word.67.1": "Phòng Thủ",
    "Word.67.2": "Giảm sát thương phải gánh chịu. Phòng Thủ có giới hạn tối đa là 2,000 điểm và không thể bị giảm quá 500 điểm.",

    # DictionaryDiagram 61 Untranslated Entries
    "DictionaryDiagram.30011901.1": "Điều Chỉnh Bản Ghi: Tiềm Năng",
    "DictionaryDiagram.30011901.2": "Khi Bản Ghi đạt đánh giá phẩm chất yêu cầu, bạn sẽ mở khóa tính năng Điều Chỉnh Tiềm Năng và Điều Chỉnh Nốt Nhạc.\x0bĐiều Chỉnh Tiềm Năng cho phép chuyển cấp độ từ Tiềm Năng này sang Tiềm Năng khác.\x0bXác nhận điều chỉnh sẽ tiêu hao nguyên liệu chỉ định, và Bản Ghi đó sẽ không thể điều chỉnh thêm lần nào nữa.",
    "DictionaryDiagram.30012001.1": "Điều Chỉnh Bản Ghi: Nốt Nhạc",
    "DictionaryDiagram.30012001.2": "Khi Bản Ghi đạt đánh giá phẩm chất yêu cầu, bạn sẽ mở khóa tính năng Điều Chỉnh Tiềm Năng và Điều Chỉnh Nốt Nhạc.\x0bĐiều Chỉnh Nốt Nhạc cho phép chuyển cấp độ từ Nốt Nhạc này sang Nốt Nhạc khác.\x0bXác nhận điều chỉnh sẽ tiêu hao nguyên liệu chỉ định, và Bản Ghi đó sẽ không thể điều chỉnh thêm lần nào nữa.",
    "DictionaryDiagram.40050102.1": "Tổ Hợp Bài",
    "DictionaryDiagram.40050104.1": "Khế Ước",
    "DictionaryDiagram.40050104.2": "Bạn phải lựa chọn và ký kết khế ước trong suốt trận đấu.\x0bHoàn thành khế ước sẽ nhận được thêm thưởng, nhưng nếu vi phạm khế ước 3 lần trận đấu sẽ lập tức kết thúc.",
    "DictionaryDiagram.40090117.1": "Quyền Năng Ma Vương",
    "DictionaryDiagram.40090117.2": "Trước khi xuất phát, bạn cần chọn loại Ma Vương muốn hóa thân trong chuyến điều tra này.\nMỗi loại Ma Vương sở hữu các Quyền Năng Ma Vương riêng biệt và có sự khác biệt giữa các chỉ số Trực Giác, Phân Tích và Hỗn Loạn.\nMở khóa thêm nhiều nút trên Cây Sách Lược để mở ra nhiều loại Ma Vương mới.",
    "DictionaryDiagram.40090118.1": "Tăng Ích Công Kích",
    "DictionaryDiagram.40090118.2": "Mở khóa các nút trên Cây Sách Lược còn giúp khai mở thêm hiệu ứng vị trí cho các ô Công Kích. Thành viên đặt tại các ô này sẽ nhận được hiệu ứng tăng ích tương ứng.",
    "DictionaryDiagram.40090119.1": "Tư Thế Chủ Đạo",
    "DictionaryDiagram.40090119.2": "Rất nhiều gương mặt thân quen mà bạn từng đồng hành cũng góp mặt trong đội điều tra!\nCác Lữ Khách đã chiêu mộ dưới trướng sẽ được quy đổi thành chỉ số cơ bản cộng thêm dựa theo tiến độ bồi dưỡng hiện tại, bao gồm Cấp Lữ Khách và Cấp Thiên Phú.",
    "DictionaryDiagram.40100101.1": "Khởi Động Hành Trình",
    "DictionaryDiagram.40100101.2": "Sparkla lái Bánh Nướng Siêu Cấp lao về phía trước không ngừng. Nhấn và kéo sang trái hoặc phải để điều khiển hướng lái.",
    "DictionaryDiagram.40100102.1": "Quy Tắc Tốc Độ",
    "DictionaryDiagram.40100102.2": "Sparkla xuất phát với một lượng Tốc Độ nhất định. Thu nhặt Pháo Thỏ Hoa hoặc lái qua Ký Hiệu Tăng Tốc để tăng thêm Tốc Độ.",
    "DictionaryDiagram.40100103.1": "Chướng Ngại & Quái Vật",
    "DictionaryDiagram.40100103.2": "Lái qua Ký Hiệu Giảm Tốc sẽ bị tụt Tốc Độ.\nQuái vật mai phục trên đường đua sở hữu Tốc Độ riêng. Khi Sparkla va chạm với chúng, cả hai bên đều mất một lượng Tốc Độ tương ứng.\nCả việc húc trúng quái vật và đánh văng chúng đều mang lại điểm số.",
    "DictionaryDiagram.40100104.1": "Quyết Đấu Tinh Linh",
    "DictionaryDiagram.40100104.2": "Sau khi vượt qua quãng đường nhất định, Tinh Linh Bạo Ngược sẽ chắn ngang đường. Sparkla sẽ dồn toàn bộ Tốc Độ tích lũy được để đối đầu trực diện. Chỉ khi húc văng Tinh Linh Bạo Ngược bạn mới giành chiến thắng.",
    "DictionaryDiagram.40100105.1": "Điều Kiện Thất Bại",
    "DictionaryDiagram.40100105.2": "Nếu Tốc Độ của Sparkla tụt về 0 trước khi chạm trán Tinh Linh Bạo Ngược, hành trình sẽ thất bại.",
    "DictionaryDiagram.40100106.1": "Tăng Tốc Toàn Lực",
    "DictionaryDiagram.40100106.2": "Đường đua xuất hiện thêm Ký Hiệu Tăng Tốc và Giảm Tốc có khả năng nhân hoặc chia Tốc Độ. Chướng ngại vật sẽ chắn ngang đường di chuyển ngang.",
    "DictionaryDiagram.40100107.1": "Quái Vật Cường Hóa",
    "DictionaryDiagram.40100107.2": "Hãy sẵn sàng đối mặt với quái vật trâu bò hơn. Nhặt Mũi Khoan Phá Giáp NGO để bào mòn Tốc Độ của quái nhanh gấp đôi!",
    "DictionaryDiagram.40100108.1": "Trang Bị NGO & Viện Binh",
    "DictionaryDiagram.40100108.2": "Húc vào Amber đang mắc kẹt trên đường đua để giải cứu và nhận hỏa lực yểm trợ từ cô ấy.\nLưỡi Cưa Tròn NGO giúp Sparkla chém trúng nhiều quái vật cùng lúc.\nCông Thức Bánh Nướng cho phép thổi bay quái vật ngay lập tức, nhưng chỉ dùng được một lần mỗi khi nhặt.",
    "DictionaryDiagram.40100109.1": "Viện Binh Mới",
    "DictionaryDiagram.40100109.2": "Noya và Iris cũng sẽ xuất hiện dọc đường đua chờ được giải cứu. Mỗi người sẽ mang đến sự hỗ trợ đắc lực riêng sau khi được cứu thoát!",
    "DictionaryDiagram.40100110.1": "Trông Cậy Cả Vào Cậu Đó, Bánh Thỏ!",
    "DictionaryDiagram.40100110.2": "Thiết Bị Trấn Áp Toàn Năng có thể nhặt được trên đường đua. Nhấn nút để Bánh Thỏ phóng ra quả bom uy lực quét sạch quái vật phía trước.\nVũ khí này không thể giữ quá lâu, một lúc sau khi nhặt Bánh Thỏ sẽ tự động khai hỏa!",
    "DictionaryDiagram.40100111.1": "Ký Hiệu Đảo Ngược",
    "DictionaryDiagram.40100111.2": "Ký Hiệu Đảo Ngược thần bí xuất hiện. Lái qua nó sẽ hoán đổi các chữ số của Tốc Độ hiện tại.\nHãy cân nhắc thật kỹ trước khi đặt cược vận may nhé!",
    "DictionaryDiagram.70010101.1": "Tháp Ma Vương",
    "DictionaryDiagram.70010101.2": "Đây là không gian riêng tư dành cho bạn và các Lữ Khách. Tại đây, bạn có thể tương tác gần gũi với đồng đội và tự do sắp xếp muôn vàn đồ nội thất yêu thích.",
    "DictionaryDiagram.70010102.1": "Thao Tác Cơ Bản",
    "DictionaryDiagram.70010102.2": "Vuốt sang trái hoặc phải trên màn hình (hoặc nhấn giữ chuột kéo ngang) để xoay góc nhìn camera.",
    "DictionaryDiagram.70010201.1": "Bày Trí Nội Thất",
    "DictionaryDiagram.70010201.2": "Chọn món đồ nội thất yêu thích cho không gian hiện tại rồi đặt vào vị trí. Xin lưu ý một số nội thất chỉ có thể đặt trong nhà hoặc ngoài trời.",
    "DictionaryDiagram.70010202.1": "Điều Chỉnh Nội Thất",
    "DictionaryDiagram.70010202.2": "Trước khi đặt nội thất, bạn có thể xoay hoặc di chuyển vị trí. Khi đã vừa ý, nhấn Xác Nhận để đặt xuống.\nNội thất đã đặt vẫn có thể di chuyển lại hoặc cất vào kho bất cứ lúc nào.",
    "DictionaryDiagram.70010203.1": "Bộ Nội Thất",
    "DictionaryDiagram.70010203.2": "Bạn có thể nhanh chóng hoàn thiện bố cục căn phòng bằng cách áp dụng bộ nội thất mẫu có sẵn.\nSau khi áp dụng bộ mẫu, bạn vẫn có thể tinh chỉnh thêm. Bố cục tự trang trí cũng có thể lưu thành mẫu riêng để tiện sử dụng sau này.",
    "DictionaryDiagram.70010301.1": "Quà Tặng Thường Nhật",
    "DictionaryDiagram.70010301.2": "Tương tác với Tượng Sherlock đã bày trí mỗi ngày 1 lần để nhận ngẫu nhiên món quà nhỏ thú vị.\nNgoài Tượng Sherlock, còn có nhiều món đồ nội thất sở hữu công năng đặc biệt khác đang chờ bạn khám phá!",
    "DictionaryDiagram.70010401.1": "Điều Khiển Di Chuyển",
    "DictionaryDiagram.70010401.2": "Trong Chế Độ Ma Vương, bạn có thể trực tiếp điều khiển Ma Vương di chuyển tự do khắp căn phòng.",
    "DictionaryDiagram.70010402.1": "Tương Tác Với Lữ Khách",
    "DictionaryDiagram.70010402.2": "Điều khiển Ma Vương tiến lại gần Lữ Khách và nhấn nút tương tác để trò chuyện cùng cô ấy.",
    "DictionaryDiagram.70010403.1": "Phần Thưởng Tương Tác",
    "DictionaryDiagram.70010403.2": "Lần tương tác đầu tiên mỗi ngày với mỗi Lữ Khách sẽ tăng Độ Thân Mật và nhận được món quà đáp lễ từ cô ấy. Mỗi ngày có thể nhận tối đa 5 phần thưởng tương tác.",
    "DictionaryDiagram.70010501.1": "Nội Thất Tương Tác Độc Quyền",
    "DictionaryDiagram.70010501.2": "Bạn có thể đặt nội thất tương tác độc quyền của Lữ Khách vào không gian phòng.\nKhi Lữ Khách tiến lại gần món đồ này, sẽ có cơ hội kích hoạt hoạt ảnh tương tác độc quyền vô cùng đáng yêu.",
    "DictionaryDiagram.70010601.1": "Chuyển Đổi Chế Độ",
    "DictionaryDiagram.70010601.2": "Nhấn nút để chuyển đổi linh hoạt giữa Chế Độ Ma Vương và Chế Độ Tháp.\nỞ Chế Độ Ma Vương, bạn có thể điều khiển Ma Vương tương tác với Lữ Khách và nội thất.\nỞ Chế Độ Tháp, bạn có thể quan sát toàn cảnh căn phòng từ góc nhìn trên cao.",
    "DictionaryDiagram.70010602.1": "Thu Phóng Tầm Nhìn",
    "DictionaryDiagram.70010602.2": "Ở Chế Độ Tháp, dùng hai ngón tay chụm mở trên màn hình hoặc cuộn con lăn chuột để phóng to thu nhỏ tầm nhìn.",
    "DictionaryDiagram.70010603.1": "Nhấc Bổng Lữ Khách",
    "DictionaryDiagram.70010603.2": "Ở Chế Độ Tháp, nhấn giữ để nhấc bổng một Lữ Khách lên, rồi thả cô ấy vào bất kỳ vị trí hợp lệ nào trong phòng.\nCách này sẽ giúp kích hoạt hoạt ảnh tương tác dễ dàng hơn đấy!",
    "DictionaryDiagram.70010701.1": "Thang Máy",
    "DictionaryDiagram.70010701.2": "Chạm vào nút thang máy hoặc sử dụng thang máy trong bối cảnh để di chuyển qua lại giữa các tầng khác nhau của Tháp Ma Vương.",

    # General UI & AutoDecision Polish
    "UIText.ActionBar_Check.1": "Xem",
    "UIText.Activity_PopUp_Goto.1": "Xem",
    "UIText.Activity_AvgReview.1": "Hồi Tưởng Sự Kiện",
    "UIText.Activity_CopyMemo.1": "Kỷ Niệm Tấu Lại",
    "UIText.Activity_Fate_Card_20104.1": "Bài Sao Túc Mệnh",
    "UIText.Activity_StoryNameTips_20104.1": "Phần Ⅰ",
    "UIText.Activity_StoryName_20104.1": "Ngoại Truyện Cốt Truyện Chính",
    "UIText.Activity_Advertise_Bonus_201018.1": "Đặc Biệt\nTheo Đuổi Ước Mơ",
    "UIText.Activity_Advertise_ChargeReset_201018.1": "Làm Mới\nThưởng Nạp Đầu",
    "UIText.Activity_Advertise_PackageDiscount_201018.1": "Ưu Đãi Cực Hời",
    "UIText.Activity_Advertise_Package_201018.1": "Gói Quà Nổi Bật",
    "UIText.Activity_Advertise_Skin_201018.1": "Trang Phục Mới",
    "UIText.Attribute_Size_High.1": "Cao",
    "UIText.AutoDecision_DefualtPresetName.1": "Kế Hoạch Chưa Đặt Tên",
    "UIText.AutoDecision_Disable.1": "Tắt Tự Động Thám Hiểm",
    "UIText.AutoDecision_Enable.1": "Bật Tự Động Thám Hiểm",
    "UIText.AutoDecision_Event.1": "Lựa Chọn Nhánh Sự Kiện",
    "UIText.AutoDecision_EventCoin.1": "Xu Stella",
    "UIText.AutoDecision_EventConserve.1": "An Toàn",
    "UIText.AutoDecision_EventRadical.1": "Mạo Hiểm",
    "UIText.AutoDecision_EventRandomNote.1": "Nốt Nhạc Ngẫu Nhiên",
    "UIText.AutoDecision_EventSort.1": "Ưu tiên chọn nhánh sự kiện theo thứ tự sau:",
    "UIText.AutoDecision_EventStandard.1": "Cân Bằng",
    "UIText.AutoDecision_EventTendency.1": "Khuynh Hướng Chung",
    "UIText.AutoDecision_InputLocked.1": "Hệ thống tự động đang chạy. Vui lòng tạm dừng trước khi thao tác!",
    "UIText.AutoDecision_InsufficientToken.1": "Đã cạn Vé Thám Hiểm, không thể khởi động chế độ tự động. Vui lòng nạp thêm Vé!",
    "UIText.AutoDecision_MainCharPotential.1": "Tiềm Năng Lữ Khách Chủ Lực",
    "UIText.AutoDecision_Ongoing.1": "Đang tự động thám hiểm...",
    "UIText.AutoDecision_PlanActivatedTip.1": "Chế độ tự động đang chạy theo kế hoạch: {0}.",
    "UIText.AutoDecision_PlanDefaultName.1": "Kế Hoạch Thám Hiểm",
    "UIText.AutoDecision_Potential.1": "Thiết Lập Tiềm Năng",
    "UIText.AutoDecision_PotentialBookUnlock.1": "Tiềm Năng chưa mở khóa trong Bách Khoa",
    "UIText.AutoDecision_PotentialCoinReroll.1": "Làm mới Tiềm Năng khi Xu Stella vượt mức chỉ định",
}

# Regex replacements for pervasive calques and mechanical phrasing
REPLACEMENTS = [
    # Severe Calques
    (r"\bchấp nhận hoa hồng\b", "nhận nhiệm vụ ủy thác"),
    (r"\bhoa hồng khẩn cấp\b", "nhiệm vụ ủy thác khẩn cấp"),
    (r"\btiền hoa hồng\b", "thù lao ủy thác"),
    (r"\bhoa hồng\b", "nhiệm vụ ủy thác"),
    (r"\bbánh mì nướng\b", "tiêu đời"),
    (r"\btuyệt chiêu\b", "tuyệt kỹ"),
    (r"\bTuyệt chiêu\b", "Tuyệt Kỹ"),
    (r"\bkỷ lục phẩm chất\b", "đĩa nhạc phẩm chất"),
    (r"\bnhận được kỷ lục\b", "nhận được đĩa nhạc"),
    (r"\bkỷ lục mới\b", "đĩa nhạc mới"),
    (r"\bnhấn vào bất cứ đâu để đóng\b", "chạm vào khoảng trống để đóng"),
    (r"\bbấm vào bất cứ đâu để đóng\b", "chạm vào khoảng trống để đóng"),
    (r"\bnhấn vào bất cứ đâu để tiếp tục\b", "chạm vào màn hình để tiếp tục"),
    (r"\bvui lòng kiểm tra kết nối mạng của bạn\b", "vui lòng kiểm tra lại kết nối mạng"),
    (r"\bthư của bạn\b", "Hòm Thư"),
    (r"\bchiêu mộ lữ khách trùng lặp sẽ nhận được\b", "khi chiêu mộ được lữ khách trùng lặp sẽ nhận thêm"),
    (r"\bđiều ước đã được thực hiện\b", "ước nguyện đã trở thành hiện thực!"),
    (r"\bFirstlight Noya\b", "Noya - Khải Minh"),
    (r"\bNoya Sơ Quang\b", "Noya - Khải Minh"),
    (r"\bSơ Quang\b", "Khải Minh"),
    (r"\bsân khấu\b", "ải"),
    (r"\bSân khấu\b", "Ải"),
    (r"\bông chủ\b", "Thủ Lĩnh"),
    (r"\bÔng chủ\b", "Thủ Lĩnh"),
    (r"\bnghị định đối đầu\b", "Lệnh Quyết Đấu"),
    (r"\bNghị định đối đầu\b", "Lệnh Quyết Đấu"),
    (r"\bnghị định quyết đấu\b", "Lệnh Quyết Đấu"),
    (r"\bNghị định quyết đấu\b", "Lệnh Quyết Đấu"),
    (r"\bNghị định thách thức\b", "Lệnh Quyết Đấu"),
    (r"\bQuyết định hạ gục\b", "Lệnh Quyết Đấu"),
    (r"\bnhớ lại\?", "thu hồi?"),
    (r"\bbản sao\b", "bản trùng lặp"),
]

def polish_entry(table: str, key: str, en: str, cur_vi: str) -> str:
    # 1. Exact match override
    if key in EXACT_KEY_MAP:
        return EXACT_KEY_MAP[key]

    # 2. General regex replacements
    res = cur_vi
    for pat, rep in REPLACEMENTS:
        res = re.sub(pat, rep, res)

    # 3. Specific table heuristics
    if table == "Achievement":
        if "Lần đầu tiên nhận được Kỷ Lục phẩm chất" in res:
            res = res.replace("Kỷ Lục", "Đĩa Nhạc")
        elif "Nhận 10 lần Kỷ Lục phẩm chất" in res:
            res = res.replace("Kỷ Lục", "Đĩa Nhạc")

    elif table == "UIText":
        if res == "Tuyệt chiêu":
            res = "Tuyệt Kỹ"
        elif res == "Hoa hồng":
            res = "Nhiệm Vụ Ủy Thác"
        elif res == "Chấp nhận hoa hồng":
            res = "Nhận Nhiệm Vụ Ủy Thác"
        elif "Sự kiện đã hết hạn. Phần thưởng đã được gửi tới thư của bạn" in res:
            res = "Sự kiện đã kết thúc. Phần thưởng đã được gửi vào Hòm Thư của bạn!"
        elif "Điều ước đã được thực hiện" in res:
            res = "Ước nguyện đã thành hiện thực!"

    return res

def main():
    items = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    polished = []
    modifications = []
    token_mismatches = 0

    for it in items:
        tbl = it["table"]
        k = it["key"]
        en = it["en"]
        cur_vi = it["current_vi"]

        new_vi = polish_entry(tbl, k, en, cur_vi)
        it["polished_vi"] = new_vi
        polished.append(it)

        # Token verification: check that required tokens in original current_vi / en are preserved
        en_tokens = extract_tokens(en)
        cur_tokens = extract_tokens(cur_vi)
        new_tokens = extract_tokens(new_vi)

        # For entries where we intentionally fixed broken tokens (in EXACT_KEY_MAP),
        # verify new_tokens matches en_tokens
        if k in EXACT_KEY_MAP:
            if en_tokens and new_tokens != en_tokens:
                print(f"[TOKEN WARNING] Fixed key {k}: expected {en_tokens}, got {new_tokens}")
                token_mismatches += 1
        else:
            # Otherwise new_tokens must match cur_tokens
            if cur_tokens != new_tokens:
                print(f"[TOKEN WARNING] Key {k}: cur_tokens {cur_tokens} != new_tokens {new_tokens}")
                token_mismatches += 1

        if new_vi != cur_vi:
            modifications.append({
                "table": tbl,
                "key": k,
                "before": cur_vi,
                "after": new_vi,
                "category": "Giao Diện & Thành Tựu",
                "reason": "Chuẩn hóa thuật ngữ UI, khử triệt để calque hoa hồng/bánh mì nướng/tuyệt chiêu, hoàn thiện 100% bách khoa thế giới và thành tựu chuẩn RPG",
                "agent": "UI Text & System Specialist Subagent"
            })

    OUTPUT_FILE.write_text(json.dumps(polished, indent=2, ensure_ascii=False), encoding="utf-8")
    MOD_FILE.write_text(json.dumps(modifications, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Pillar 2 Polish complete: {len(polished)} items processed, {len(modifications)} modifications made.")
    print(f"Token verification: {token_mismatches} mismatches encountered.")
    print(f"Saved modifications to {MOD_FILE.name}")

if __name__ == "__main__":
    main()
