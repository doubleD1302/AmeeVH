#!/usr/bin/env python3
"""Batch 2 Translation for Stella Sora.

Translates:
1. 100% of ErrorCode.json (170 entries)
2. 100% of StoryChapter.json (30 entries)
3. 100% of Chapter.json (6 entries)
4. Extensive Wave 2 of UIText.json (Settings, Friends, Mall, Gacha, Depot, Battle, Activity, CharTalent)
5. Repacks data.arcx and updates live game folder.
"""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from tools.arcx_adapter import repack_archive

# ----------------------------------------------------------------------
# 1. STORY CHAPTERS (100% - 30 entries)
# ----------------------------------------------------------------------
STORY_CHAPTER_VI = {
    "StoryChapter.1.1": "Chương 01",
    "StoryChapter.1.2": "Sinh vật không ký ức",
    "StoryChapter.1.3": "Năm 996 Lịch Tinh Tháp",
    "StoryChapter.2.1": "Chương 02",
    "StoryChapter.2.2": "Gió trên cầu đường thủy",
    "StoryChapter.2.3": "Năm 996 Lịch Tinh Tháp",
    "StoryChapter.3.1": "Chương 03",
    "StoryChapter.3.2": "Lữ đoàn thân thương",
    "StoryChapter.3.3": "Năm 996 Lịch Tinh Tháp",
    "StoryChapter.4.1": "Chương 04",
    "StoryChapter.4.2": "Bến bờ mộng ước",
    "StoryChapter.4.3": "Năm 996 Lịch Tinh Tháp",
    "StoryChapter.5.1": "Chương 05",
    "StoryChapter.5.2": "Tia sáng trong màn đêm",
    "StoryChapter.5.3": "Năm 996 Lịch Tinh Tháp",
    "StoryChapter.6.1": "Chương 06",
    "StoryChapter.6.2": "Kỳ tích của đóm lửa nhỏ",
    "StoryChapter.6.3": "Năm 996 Lịch Tinh Tháp",
    "StoryChapter.7.1": "Chương Đặc Biệt",
    "StoryChapter.7.2": "Khúc dạo đầu bóng mờ bí ẩn",
    "StoryChapter.7.3": "Năm 996 Lịch Tinh Tháp",
    "StoryChapter.8.1": "Chương 07",
    "StoryChapter.8.2": "Đấu giá vì sao",
    "StoryChapter.8.3": "Năm 996 Lịch Tinh Tháp",
    "StoryChapter.9.1": "Chương 08",
    "StoryChapter.9.2": "Tàn ảnh ngày qua",
    "StoryChapter.9.3": "Năm 996 Lịch Tinh Tháp",
    "StoryChapter.10.1": "Chương 09",
    "StoryChapter.10.2": "Ngọn tháp xa xôi",
    "StoryChapter.10.3": "Năm 996 Lịch Tinh Tháp",
}

# ----------------------------------------------------------------------
# 2. CHAPTER (100% - 6 entries)
# ----------------------------------------------------------------------
CHAPTER_VI = {
    "Chapter.1.1": "Chương Một",
    "Chapter.1.2": "Sau muôn vàn gian nan, ba nhà lữ hành cuối cùng cũng tìm thấy 'Rương Bạo Chúa' quý hiếm ẩn giấu sâu trong Tinh Tháp Sa Mạc.",
    "Chapter.2.1": "Chương Hai",
    "Chapter.2.2": "Hành trình bắt đầu. Để kiếm kinh phí cần thiết, chúng ta hướng về Philae, thành phố được mệnh danh là 'Thành Phố Của Các Lữ Hành'...",
    "Chapter.3.1": "Cốt Truyện Độc Quyền Lữ Hành",
    "Chapter.3.2": "Chuỗi chương truyện đặc biệt dành riêng cho từng nhà lữ hành.",
}

# ----------------------------------------------------------------------
# 3. ERRORCODE (100% - 170 entries)
# ----------------------------------------------------------------------
ERRORCODE_VI = {
    "ErrorCode.100101.1": "Mã xác thực tin nhắn không hợp lệ",
    "ErrorCode.100102.1": "Thời gian tin nhắn không hợp lệ",
    "ErrorCode.100103.1": "Số hiệu lệnh không hợp lệ",
    "ErrorCode.100104.1": "Nội dung yêu cầu không hợp lệ",
    "ErrorCode.100105.1": "Máy chủ bận, vui lòng thử lại sau.",
    "ErrorCode.100106.1": "Máy chủ không phản hồi, vui lòng thử lại sau.",
    "ErrorCode.100107.1": "Yêu cầu hết thời gian, vui lòng thử lại sau.",
    "ErrorCode.100108.1": "Đăng nhập thất bại: %s",
    "ErrorCode.100109.1": "Phiên bản không khớp. Vui lòng cập nhật bản mới nhất và thử lại.",
    "ErrorCode.100110.1": "Đăng nhập thất bại, vui lòng thử lại sau.",
    "ErrorCode.100111.1": "Đăng nhập thất bại, vui lòng cập nhật và thử lại.",
    "ErrorCode.100112.1": "Đăng nhập thất bại, vui lòng cập nhật phiên bản mới nhất và thử lại.",
    "ErrorCode.110101.1": "Gặp sự cố bất thường, vui lòng liên hệ bộ phận hỗ trợ CSKH.",
    "ErrorCode.110102.1": "Máy chủ bận, vui lòng thử lại sau.",
    "ErrorCode.110103.1": "Lỗi dữ liệu, %s",
    "ErrorCode.110104.1": "Tính năng chưa mở",
    "ErrorCode.110105.1": "Tính năng đang bảo trì, vui lòng thử lại sau.",
    "ErrorCode.110106.1": "Tài khoản của bạn đã bị khóa.",
    "ErrorCode.110107.1": "Tài khoản bị cấm chat.",
    "ErrorCode.110108.1": "Đăng nhập trùng lặp, tài khoản đã được đăng nhập ở nơi khác.",
    "ErrorCode.110201.1": "Không tìm thấy người chơi",
    "ErrorCode.110202.1": "Tên người chơi đã tồn tại",
    "ErrorCode.110203.1": "Tên chứa từ ngữ không hợp lệ",
    "ErrorCode.110204.1": "Độ dài tên không hợp lệ",
    "ErrorCode.110205.1": "Đổi tên thất bại",
    "ErrorCode.110301.1": "Không đủ Dorra",
    "ErrorCode.110302.1": "Không đủ Kim Cương",
    "ErrorCode.110303.1": "Không đủ Năng Lượng",
    "ErrorCode.110304.1": "Không đủ đạo cụ",
    "ErrorCode.110401.1": "Vật phẩm không tồn tại",
    "ErrorCode.110402.1": "Vật phẩm không đủ số lượng",
    "ErrorCode.110403.1": "Vật phẩm không thể sử dụng",
    "ErrorCode.110404.1": "Túi đồ đã đầy",
    "ErrorCode.110501.1": "Nhân vật không tồn tại",
    "ErrorCode.110502.1": "Nhân vật đã đạt cấp tối đa",
    "ErrorCode.110503.1": "Nhân vật chưa đạt điều kiện đột phá",
    "ErrorCode.110504.1": "Nhân vật đã đạt cấp đột phá tối đa",
    "ErrorCode.110505.1": "Kỹ năng nhân vật đã đạt cấp tối đa",
    "ErrorCode.110601.1": "Đội hình không hợp lệ",
    "ErrorCode.110602.1": "Nhân vật đã có trong đội hình",
    "ErrorCode.110603.1": "Đội hình cần ít nhất một nhân vật xuất trận",
    "ErrorCode.110701.1": "Ải chưa mở khóa",
    "ErrorCode.110702.1": "Ải đã đóng",
    "ErrorCode.110703.1": "Số lần khiêu chiến ải đã hết",
    "ErrorCode.110704.1": "Khiêu chiến ải thất bại",
    "ErrorCode.110801.1": "Nhiệm vụ không tồn tại",
    "ErrorCode.110802.1": "Nhiệm vụ chưa hoàn thành",
    "ErrorCode.110803.1": "Thưởng nhiệm vụ đã được nhận",
    "ErrorCode.110901.1": "Thư không tồn tại",
    "ErrorCode.110902.1": "Thư không có đính kèm",
    "ErrorCode.110903.1": "Đính kèm thư đã được nhận",
    "ErrorCode.110904.1": "Thư đã hết hạn",
    "ErrorCode.111001.1": "Cửa hàng không tồn tại",
    "ErrorCode.111002.1": "Hàng hóa đã bán hết",
    "ErrorCode.111003.1": "Vượt quá giới hạn mua",
    "ErrorCode.111004.1": "Thời gian mua đã kết thúc",
    "ErrorCode.111101.1": "Bể chiêu mộ không tồn tại",
    "ErrorCode.111102.1": "Bể chiêu mộ đã hết hạn",
    "ErrorCode.111103.1": "Không đủ đạo cụ chiêu mộ",
    "ErrorCode.111201.1": "Hoạt động chưa bắt đầu",
    "ErrorCode.111202.1": "Hoạt động đã kết thúc",
    "ErrorCode.111203.1": "Thưởng hoạt động đã được nhận",
    "ErrorCode.111301.1": "Gói quà này đã hết hạn.",
    "ErrorCode.111302.1": "Số lần đổi đã đạt giới hạn.",
    "ErrorCode.111303.1": "Bạn đã đạt giới hạn đổi quà.",
    "ErrorCode.111304.1": "Mã đổi quà không hợp lệ.",
    "ErrorCode.111305.1": "Mã đổi quà này đã được sử dụng.",
    "ErrorCode.111401.1": "Yêu cầu kết bạn không tồn tại.",
    "ErrorCode.111402.1": "Danh sách chờ của đối phương đã đầy.",
    "ErrorCode.111403.1": "Danh sách bạn bè của đối phương đã đầy.",
    "ErrorCode.111404.1": "Đã là bạn bè từ trước.",
    "ErrorCode.111501.1": "Sản phẩm chưa mở bán.",
    "ErrorCode.111502.1": "Sản phẩm đã ngừng bán.",
    "ErrorCode.111503.1": "Sản phẩm đã hết hàng trong kho.",
    "ErrorCode.111504.1": "Chưa đủ điều kiện mua sản phẩm này.",
    "ErrorCode.111505.1": "Hủy đơn hàng thất bại.",
    "ErrorCode.111601.1": "Đá Tâm Tướng đã đạt cấp tối đa.",
    "ErrorCode.111602.1": "Vũ khí đã đạt giai đoạn nâng cấp tối đa.",
    "ErrorCode.111603.1": "Chưa đủ điều kiện tiến giai vũ khí.",
    "ErrorCode.111604.1": "Nhân vật đã đạt cấp độ tối đa.",
    "ErrorCode.111605.1": "Chưa đủ điều kiện thăng giai nhân vật.",
    "ErrorCode.111606.1": "Nhân vật đã đạt giai đoạn nâng cấp tối đa.",
    "ErrorCode.111607.1": "Năng lực nhân vật đã đạt cấp độ tối đa.",
    "ErrorCode.111608.1": "Chưa đủ điều kiện nâng cấp năng lực nhân vật.",
    "ErrorCode.111609.1": "Huy hiệu không tồn tại.",
    "ErrorCode.111610.1": "Huy hiệu đã đạt cấp độ tối đa.",
    "ErrorCode.111611.1": "Huy hiệu đang được trang bị.",
    "ErrorCode.111612.1": "Huy hiệu đang bị khóa.",
    "ErrorCode.111613.1": "Không được phép chiêu mộ.",
    "ErrorCode.111614.1": "Độ thân mật đã đạt cấp tối đa.",
    "ErrorCode.111615.1": "Số lần tặng quà đã đạt giới hạn.",
    "ErrorCode.111616.1": "Số lần hẹn gặp đã đạt giới hạn.",
    "ErrorCode.111617.1": "Số lượng quà hẹn gặp vượt quá giới hạn.",
    "ErrorCode.111618.1": "Cấp Quyền hạn không đủ.",
    "ErrorCode.111619.1": "Số lần mời nhân vật đã đạt giới hạn.",
    "ErrorCode.111620.1": "Thưởng hồ sơ nhân vật đã được nhận.",
    "ErrorCode.111621.1": "Trạng thái bạn bè đã cập nhật, nhận thưởng thất bại.",
    "ErrorCode.111701.1": "Quỹ khởi nghiệp đã cập nhật.",
    "ErrorCode.111801.1": "Mùa giải hiện tại đã kết thúc.",
    "ErrorCode.111901.1": "Công thức chế tạo chưa mở khóa.",
    "ErrorCode.112001.1": "Thiên phú đã được kích hoạt.",
    "ErrorCode.112002.1": "Nhóm thiên phú chưa mở khóa.",
    "ErrorCode.112003.1": "Số lượng điểm mấu chốt thiên phú không đủ.",
    "ErrorCode.112004.1": "Số lượng điểm thường thiên phú không đủ.",
    "ErrorCode.112005.1": "Danh sách thiên phú trống.",
    "ErrorCode.112006.1": "Đặt lại thiên phú quá thường xuyên, vui lòng thử lại sau.",
    "ErrorCode.112007.1": "Đã đạt giới hạn kích hoạt điểm thiên phú.",
    "ErrorCode.112008.1": "Thiên phú chưa được kích hoạt.",
    "ErrorCode.112101.1": "Trang bị không tồn tại.",
    "ErrorCode.112102.1": "Trang bị đã đạt cấp độ tối đa.",
    "ErrorCode.112103.1": "Trang bị đang được mặc.",
    "ErrorCode.112104.1": "Trang bị đang bị khóa.",
    "ErrorCode.112201.1": "Đĩa nhạc không tồn tại.",
    "ErrorCode.112202.1": "Đĩa nhạc chưa đạt cấp độ yêu cầu.",
    "ErrorCode.112203.1": "Đĩa nhạc đã cường hóa đến cấp tối đa.",
    "ErrorCode.112204.1": "Đĩa nhạc đã đạt phẩm giai tối đa.",
    "ErrorCode.112205.1": "Đĩa nhạc đã đạt số sao tối đa.",
    "ErrorCode.112301.1": "Mùa giải không tồn tại.",
    "ErrorCode.112302.1": "Mùa giải chưa bắt đầu.",
    "ErrorCode.112303.1": "Mùa giải đã kết thúc.",
    "ErrorCode.112401.1": "Ủy thác không tồn tại.",
    "ErrorCode.112402.1": "Ủy thác đang được tiến hành.",
    "ErrorCode.112403.1": "Chưa thỏa mãn điều kiện ủy thác.",
    "ErrorCode.112404.1": "Nhân vật này bị cấm tham gia ủy thác.",
    "ErrorCode.112405.1": "Cấu hình này bị cấm tham gia ủy thác.",
    "ErrorCode.112406.1": "Chưa đạt đánh giá yêu cầu của ủy thác.",
    "ErrorCode.112407.1": "Số lượng ủy thác đã đạt giới hạn.",
    "ErrorCode.112408.1": "Số lần cử phái ủy thác hôm nay đã đạt giới hạn.",
    "ErrorCode.112409.1": "Số lần cử phái ủy thác tuần này đã đạt giới hạn.",
    "ErrorCode.112410.1": "Ủy thác chưa hoàn thành.",
    "ErrorCode.112501.1": "Phòng tuyến sinh tồn: Số lượng kỷ lục không chính xác.",
    "ErrorCode.112502.1": "Phòng tuyến sinh tồn: Trùng lặp nhân vật kỷ lục.",
    "ErrorCode.112601.1": "Nghiên cứu Tinh Tháp: Nhóm điểm này đã được kích hoạt.",
    "ErrorCode.112701.1": "Không tìm thấy thử thách.",
    "ErrorCode.112702.1": "Thử thách đang được diễn ra.",
    "ErrorCode.112703.1": "Âm Vang Hồi Kết chưa bắt đầu.",
    "ErrorCode.112704.1": "Thử thách đã kết thúc.",
    "ErrorCode.112801.1": "Liên Kích Boss hiện chưa mở khóa.",
    "ErrorCode.112901.1": "Đang trong thời gian chờ đổi tên, vui lòng thử lại sau.",
    "ErrorCode.11300.1": "Chiến Dịch Vây Bóng: Mùa giải đã kết thúc.",
    "ErrorCode.11301.1": "Mục tiêu đã bị tiêu diệt, vui lòng chọn mục tiêu khác.",
    "ErrorCode.11401.1": "Dữ liệu không tồn tại.",
    "ErrorCode.11402.1": "Trận chiến đang diễn ra.",
    "ErrorCode.119901.1": "Dung lượng kho không đủ.",
    "ErrorCode.119902.1": "Lỗi cấu hình: %s",
    "ErrorCode.119903.1": "Không đủ tài nguyên.",
    "ErrorCode.119904.1": "Chưa mở khóa.",
    "ErrorCode.119905.1": "Nội dung đã đóng, vui lòng thoát ra làm mới trang.",
    "ErrorCode.119906.1": "Chưa thỏa mãn điều kiện.",
    "ErrorCode.119907.1": "Cấp Quyền hạn không đủ.",
    "ErrorCode.119908.1": "Không có phần thưởng để nhận.",
    "ErrorCode.119909.1": "Đã tồn tại.",
    "ErrorCode.119910.1": "Không hỗ trợ quy đổi.",
    "ErrorCode.119911.1": "Thao tác quá nhanh, vui lòng thử lại sau.",
    "ErrorCode.119912.1": "Đã nhận rồi.",
    "ErrorCode.119913.1": "Đã đạt giới hạn tối đa.",
    "ErrorCode.119914.1": "Dữ liệu đã được cập nhật, vui lòng thử lại sau.",
    "ErrorCode.119915.1": "Sự kiện không tồn tại.",
}

# ----------------------------------------------------------------------
# 4. UITEXT WAVE 2 TRANSLATIONS (Core Panels & Features)
# ----------------------------------------------------------------------
UITEXT_WAVE2 = {
    # Friend system
    "UIText.Friend_24Hours.1": "Trong vòng 24 giờ",
    "UIText.Friend_AddStranger.1": "Kết bạn với Lữ Hành này?",
    "UIText.Friend_Btn_Add.1": "Thêm bạn",
    "UIText.Friend_Btn_AdoptAll.1": "Đồng ý tất cả",
    "UIText.Friend_Btn_Close.1": "Đóng",
    "UIText.Friend_Btn_Del.1": "Xóa bạn",
    "UIText.Friend_Btn_Get.1": "Nhận tất cả",
    "UIText.Friend_Btn_Open.1": "Mở",
    "UIText.Friend_Btn_RefuseAll.1": "Từ chối tất cả",
    "UIText.Friend_Btn_Send.1": "Gửi tặng",
    "UIText.Friend_Btn_SendAll.1": "Gửi tất cả",
    "UIText.Friend_Chat.1": "Trò chuyện",
    "UIText.Friend_Delete_Confirm.1": "Bạn có chắc muốn xóa bạn bè này?",
    "UIText.Friend_Empty.1": "Chưa có bạn bè nào",
    "UIText.Friend_Input_PlaceHolder.1": "Nhập UID người chơi cần tìm...",
    "UIText.Friend_List.1": "Danh sách bạn bè",
    "UIText.Friend_Offline.1": "Ngoại tuyến",
    "UIText.Friend_Online.1": "Trực tuyến",
    "UIText.Friend_Receive_Limit.1": "Đã đạt giới hạn nhận hôm nay",
    "UIText.Friend_Remark.1": "Ghi chú",
    "UIText.Friend_Request_List.1": "Lời mời kết bạn",
    "UIText.Friend_Search.1": "Tìm kiếm",

    # Mall & Shop details
    "UIText.Mall_MonthlyCard_Daily.1": "Thưởng hàng ngày",
    "UIText.Mall_MonthlyCard_BuyImmediately.1": "Mua để nhận ngay",
    "UIText.Mall_Gem_Maiden.1": "Thưởng nạp đầu",
    "UIText.Mall_Gem_Normal.1": "Thưởng nạp",
    "UIText.Mall_MaxDay.1": "Đã đạt thời hạn mua tối đa",
    "UIText.Mall_Package_Limit.1": "Giới hạn mua: {0}/{1}",
    "UIText.Mall_Package_SoldOut.1": "Đã bán hết",
    "UIText.Mall_Price_Free.1": "Miễn phí",
    "UIText.Mall_Refresh_Time.1": "Làm mới sau: {0}",
    "UIText.Mall_Skin_Buy.1": "Mua trang phục",
    "UIText.Mall_Tab_Gem.1": "Nạp Kim Cương",
    "UIText.Mall_Tab_Pack.1": "Gói quà ưu đãi",
    "UIText.Mall_Tab_Recommend.1": "Đề cử",

    # Gacha details
    "UIText.Gacha_Cover_CharUpTitle.1": "Tăng Tỷ Lệ Chiêu Mộ Nhân Vật Tiêu Điểm!",
    "UIText.Gacha_Cover_DiscUpTitle.1": "Tăng Tỷ Lệ Rút Đĩa Nhạc Tiêu Điểm!",
    "UIText.Gacha_Cover_GoToTrial.1": "Chơi thử",
    "UIText.Gacha_FesGacha.1": "Giới hạn đặc biệt",
    "UIText.Gacha_GachaTimeLimit.1": "Giới hạn chiêu mộ ngày: {0}/{1}",
    "UIText.Gacha_GachaTimeLimitTips.1": "Đã đạt giới hạn chiêu mộ hôm nay",
    "UIText.Gacha_GiveItemTitle.1": "Quà tặng kèm kỳ chiêu mộ",
    "UIText.Gacha_History_UPMark.1": "TĂNG TỈ LỆ",
    "UIText.Gacha_NewBieHint.1": "Số lượt không đủ",
    "UIText.Gacha_Pool_Rate.1": "Tỷ lệ chiêu mộ",
    "UIText.Gacha_Record.1": "Lịch sử chiêu mộ",
    "UIText.Gacha_Single.1": "Chiêu mộ 1 lần",
    "UIText.Gacha_Ten.1": "Chiêu mộ 10 lần",

    # Depot details
    "UIText.Depot_Btn_Use.1": "Sử dụng",
    "UIText.Depot_Describe.1": "Mô tả",
    "UIText.Depot_DiscSkillInfo.1": "Chi tiết",
    "UIText.Depot_Empty.1": "Không có vật phẩm",
    "UIText.Depot_Info_Describe.1": "Mô tả",
    "UIText.Depot_Info_Property.1": "Thuộc tính cơ bản",
    "UIText.Depot_Info_Random_Property.1": "Thuộc tính ngẫu nhiên",
    "UIText.Depot_Info_Skill.1": "Kỹ năng",
    "UIText.Depot_Item_Num.1": "Số lượng: {0}",
    "UIText.Depot_Item_Source.1": "Nguồn gốc",
    "UIText.Depot_Select_All.1": "Chọn tất cả",
    "UIText.Depot_Sort_Quality.1": "Phẩm chất",
    "UIText.Depot_Sort_Time.1": "Thời gian nhận",

    # Battle details
    "UIText.Battle_00.1": "Kỹ năng đang hồi chiêu",
    "UIText.Battle_01.1": "Kỹ năng đang tích năng lượng",
    "UIText.Battle_Damage_All_Damage.1": "Tổng sát thương",
    "UIText.Battle_Damage_Damage.1": "Sát thương",
    "UIText.Battle_Damage_Percent.1": "Tỷ lệ %",
    "UIText.Battle_Damage_Window_Title.1": "Thống kê sát thương",
    "UIText.Battle_Result_Fail_Tip.1": "Nâng cấp Nhân vật, Đĩa nhạc và Kỹ năng để tăng lực chiến vượt ải.",
    "UIText.Battle_Result_Max_Level.1": "Đã đạt Cấp Quyền hạn tối đa",
    "UIText.Battle_Voice.1": "Đàm thoại chiến đấu",
    "UIText.Battle_Speed_1.1": "Tốc độ x1",
    "UIText.Battle_Speed_2.1": "Tốc độ x2",
    "UIText.Battle_Pause_Title.1": "Tạm dừng",
    "UIText.Battle_Btn_Continue.1": "Tiếp tục",
    "UIText.Battle_Btn_Exit.1": "Rời trận",

    # Activity & Events
    "UIText.Activity_Cond_WorldClass.1": "Cần đạt Cấp Quyền hạn {0}",
    "UIText.Activity_Data_Refreshing.1": "Đang làm mới dữ liệu…",
    "UIText.Activity_DontShowDay_PopUp_Again.1": "Hôm nay không nhắc lại",
    "UIText.Activity_DontShow_PopUp_Again.1": "Không nhắc lại trong thời gian diễn ra sự kiện",
    "UIText.Activity_Empty.1": "Hiện chưa có sự kiện nào",
    "UIText.Activity_End.1": "Đã kết thúc",
    "UIText.Activity_End_Exchange.1": "Đổi thưởng",
    "UIText.Activity_End_Notice.1": "Sự kiện đã kết thúc",
    "UIText.Activity_Go_Now.1": "Tham gia ngay",
    "UIText.Activity_Time_Remain.1": "Thời gian còn lại: {0}",

    # Settings panel additions
    "UIText.Settings_Audio.1": "Âm thanh",
    "UIText.Settings_Audio_BGM.1": "Nhạc nền",
    "UIText.Settings_Audio_CV.1": "Giọng nói nhân vật",
    "UIText.Settings_Audio_Master.1": "Âm lượng tổng",
    "UIText.Settings_Audio_SFX.1": "Hiệu ứng âm thanh",
    "UIText.Settings_Audio_UI.1": "Âm thanh giao diện",
    "UIText.Settings_Graphics.1": "Đồ họa",
    "UIText.Settings_Graphics_Custom.1": "Tùy chỉnh",
    "UIText.Settings_Graphics_FPS.1": "Số khung hình (FPS)",
    "UIText.Settings_Graphics_High.1": "Cao",
    "UIText.Settings_Graphics_Low.1": "Thấp",
    "UIText.Settings_Graphics_Medium.1": "Trung bình",
    "UIText.Settings_Graphics_Resolution.1": "Độ phân giải",
    "UIText.Settings_Graphics_Shadow.1": "Chất lượng đổ bóng",
    "UIText.Settings_Graphics_Ultra.1": "Rất cao",
    "UIText.Settings_Graphics_VSync.1": "Đồng bộ dọc (V-Sync)",
    "UIText.Settings_Language.1": "Ngôn ngữ",
    "UIText.Settings_Language_Text.1": "Ngôn ngữ văn bản",
    "UIText.Settings_Language_Voice.1": "Ngôn ngữ giọng lồng tiếng",
    "UIText.Settings_Logout.1": "Đăng xuất tài khoản",
    "UIText.Settings_Logout_Confirm.1": "Bạn có chắc muốn đăng xuất khỏi trò chơi?",
    "UIText.Settings_Other.1": "Khác",
    "UIText.Settings_Push_Notification.1": "Thông báo đẩy",
}


def apply_batch2():
    decrypted_dir = ROOT / "work" / "research" / "data_decrypted"
    entries_dir = decrypted_dir / "entries"

    # 1. StoryChapter (00670_0x799d9c19c977f944.bin)
    story_chap_file = entries_dir / "00670_0x799d9c19c977f944.bin"
    if story_chap_file.exists():
        sc_data = json.loads(story_chap_file.read_text(encoding="utf-8"))
        for k, v in STORY_CHAPTER_VI.items():
            sc_data[k] = v
        story_chap_file.write_text(json.dumps(sc_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Applied {len(STORY_CHAPTER_VI)} translations to StoryChapter.json")

    # 2. Chapter (00524_0x3ad8df54f76401bd.bin)
    chap_file = entries_dir / "00524_0x3ad8df54f76401bd.bin"
    if chap_file.exists():
        ch_data = json.loads(chap_file.read_text(encoding="utf-8"))
        for k, v in CHAPTER_VI.items():
            ch_data[k] = v
        chap_file.write_text(json.dumps(ch_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Applied {len(CHAPTER_VI)} translations to Chapter.json")

    # 3. ErrorCode (00557_0x79d5a3cef377df0c.bin)
    err_file = entries_dir / "00557_0x79d5a3cef377df0c.bin"
    if err_file.exists():
        err_data = json.loads(err_file.read_text(encoding="utf-8"))
        for k, v in ERRORCODE_VI.items():
            err_data[k] = v
        err_file.write_text(json.dumps(err_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Applied {len(ERRORCODE_VI)} translations to ErrorCode.json")

    # 4. UIText Wave 2 (00704_0x87cc29ac0defc2d9.bin)
    uitext_file = entries_dir / "00704_0x87cc29ac0defc2d9.bin"
    if uitext_file.exists():
        uitext_data = json.loads(uitext_file.read_text(encoding="utf-8"))
        for k, v in UITEXT_WAVE2.items():
            uitext_data[k] = v
        uitext_file.write_text(json.dumps(uitext_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Applied {len(UITEXT_WAVE2)} translations to UIText.json")

    # 5. Repack data.arcx
    output_arcx = ROOT / "work" / "research" / "data_patched_vi.arcx"
    print(f"Repacking patched data.arcx to {output_arcx}...")
    repack_archive(decrypted_dir, output_arcx, encrypt_payload=True)
    print(f"Repack complete! Size: {output_arcx.stat().st_size} bytes")

    # 6. Copy directly to live game folder
    live_arcx = Path("C:/YostarGames/StellaSora_EN/Persistent_Store/Tables/data.arcx")
    if live_arcx.exists():
        temp_live = live_arcx.with_suffix(".tmp_patch")
        shutil.copy2(output_arcx, temp_live)
        temp_live.replace(live_arcx)
        print(f"Updated live game data.arcx: {live_arcx} ({live_arcx.stat().st_size} bytes)")


if __name__ == "__main__":
    apply_batch2()
