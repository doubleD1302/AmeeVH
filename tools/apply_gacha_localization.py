#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master Gacha Localization Script for Stella Sora:
- Translates GachaStorage (banner categories)
- Translates Gacha (all banner event names)
- Translates GachaType (all rules, odds, pity rules, and duplicate conversion notes)
- Overhauls UIText (all recruitment UI texts, fixing 'chi tiết đáng tiếc', 'tân binh', etc.)
- Repacks dist/data_patched_vi.arcx and dual-syncs to Yostar and Steam.
"""

import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT))
from tools.arcx_adapter import ArcxArchive, repack_archive

DEC_DIR = ROOT / "work" / "research" / "data_200_decrypted"
ENTRIES_DIR = DEC_DIR / "entries"
OUTPUT_ARCX = ROOT / "dist" / "data_patched_vi.arcx"

GACHA_STORAGE_TRANSLATIONS = {
    "GachaStorage.BeginnerCardPool.1": "Khởi Đầu May Mắn (Tân Thủ)",
    "GachaStorage.CharacterCardPool.1": "Chiêu Mộ Du Hành Thường",
    "GachaStorage.CharacterCardRewardPool.1": "Chiêu Mộ Đặc Tuyển Kỷ Niệm",
    "GachaStorage.CharacterUpCardPool.1": "Chiêu Mộ Du Hành Giới Hạn",
    "GachaStorage.DiscCardPool.1": "Khắc Ấn Thường",
    "GachaStorage.DiscUpCardPool.1": "Khắc Ấn Giới Hạn",
}

GACHA_BANNER_TRANSLATIONS = {
    "Gacha.1.1": "Hành Trình Tháp Sao",
    "Gacha.1001.1": "Một Năm Tinh Trình · Duyên Định Trùng Phùng",
    "Gacha.10110.1": "Lý Tính Ánh Bích Ngọc",
    "Gacha.10114.1": "Xạ Thủ Chiều Không Gian Meo",
    "Gacha.10115.1": "Cát Sao Đón Ánh Sáng",
    "Gacha.10119.1": "Kỳ Ngộ Định Mệnh",
    "Gacha.10125.1": "Kỳ Ngộ Định Mệnh",
    "Gacha.10130.1": "Tâm Ý Từng Trang · Giao Đúng Giờ Hẹn",
    "Gacha.10132.1": "Kỳ Ngộ Định Mệnh",
    "Gacha.10133.1": "Gió Thoảng Lung Lay · Hương Tình Thuần Khiết",
    "Gacha.10134.1": "Tuyết Tan Chồi Biếc Đâm Chồi",
    "Gacha.10135.1": "Kỳ Ngộ Định Mệnh",
    "Gacha.10137.1": "Vũ Điệu Nhã Nhặn · Thiên Kim Giá Đáo",
    "Gacha.10139.1": "Đắm Trong Nụ Cười Ấm Áp",
    "Gacha.10140.1": "Lời Giải Hoàn Mỹ Nhất",
    "Gacha.10141.1": "Kỳ Ngộ Định Mệnh",
    "Gacha.10143.1": "Ngọn Thương Bạc Xé Toạc Màn Đêm",
    "Gacha.10144.1": "Trăng Đêm Tuôn Chảy · Ánh Đao Lấp Lánh",
    "Gacha.10145.1": "Dạ Anh Tàn Chốn Nguyệt Trầm",
    "Gacha.10149.1": "Kỳ Ngộ Định Mệnh",
    "Gacha.10155.1": "Sóng Lớn Chạm Trăng Tròn",
    "Gacha.10156.1": "Kỳ Ngộ Định Mệnh",
    "Gacha.10157.1": "Sóng Hoa Đuổi Nắng Tìm Trời",
    "Gacha.10158.1": "Đại Chiến Tặng Quà Đêm Thánh!",
    "Gacha.10159.1": "Từng Lời Tâm Sự · Hơi Ấm Còn Vấn Vương",
    "Gacha.10160.1": "Trước Khi Xuống Nước Nhớ Khởi Động!",
    "Gacha.10162.1": "Tương Ngộ Kiếm Nguyên Sơ",
    "Gacha.11110.1": "Lý Tính Ánh Bích Ngọc",
    "Gacha.11115.1": "Cát Sao Đón Ánh Sáng",
    "Gacha.11119.1": "Kỳ Ngộ Định Mệnh",
    "Gacha.11133.1": "Gió Thoảng Lung Lay · Hương Tình Thuần Khiết",
    "Gacha.11134.1": "Tuyết Tan Chồi Biếc Đâm Chồi",
    "Gacha.11141.1": "Kỳ Ngộ Định Mệnh",
    "Gacha.11144.1": "Trăng Đêm Tuôn Chảy · Ánh Đao Lấp Lánh",
    "Gacha.11155.1": "Sóng Lớn Chạm Trăng Tròn",
    "Gacha.2.1": "Hồi Tưởng Trôi Dạt",
    "Gacha.20110.1": "Hương Trà Chuếnh Choáng · Mộng Điệp Hoa Đằng",
    "Gacha.20114.1": "Trái Tim Cậu Đã Bị Meo Nhắm Trúng",
    "Gacha.20115.1": "Nếu Có Thể Chạm Tới Muôn Vì Tinh Tú",
    "Gacha.20119.1": "Dây Lòng Định Âm",
    "Gacha.20125.1": "Dây Lòng Định Âm",
    "Gacha.20130.1": "Khinh Khí Cầu Hạnh Phúc Chở Ước Mơ",
    "Gacha.20132.1": "Dây Lòng Định Âm",
    "Gacha.20133.1": "Nắng Chiều Nhẹ Rọi · Cùng Vào Giấc Mơ Xanh",
    "Gacha.20134.1": "Trời Đêm Rực Rỡ · Pháo Hoa Bừng Nở",
    "Gacha.20135.1": "Dây Lòng Định Âm",
    "Gacha.20137.1": "Bay Về Thế Giới Hằng Mơ Ước",
    "Gacha.20139.1": "Giấc Mơ Ngây Thơ Nơi Khoảng Trống",
    "Gacha.20140.1": "Ý Tưởng Diệu Kỳ Gửi Gắm Vào Đồ Thủ Công",
    "Gacha.20141.1": "Dây Lòng Định Âm",
    "Gacha.20143.1": "Nắng Ấm Ngày Xuân Giấc Mộng Say",
    "Gacha.20144.1": "Trăng Nổi Soi Bóng Đầm Trong",
    "Gacha.20145.1": "Hương Bách Hợp Thoảng Cùng Làn Khói",
    "Gacha.20149.1": "Dây Lòng Định Âm",
    "Gacha.20155.1": "Biển Trời Một Màu",
    "Gacha.20156.1": "Dây Lòng Định Âm",
    "Gacha.20157.1": "Sóng Biếc Nhuộm Bảy Sắc Cầu Vồng",
    "Gacha.20158.1": "Khúc Ca Của Vương Quốc Khoai Tây Chiên",
    "Gacha.20159.1": "Mới Tỉnh Luyến Lưu · Bóng Hình Tựa Mộng",
    "Gacha.20160.1": "Sóng Nước Lăn Tăn · Đầu Ngón Tay Khẽ Chạm",
    "Gacha.20162.1": "Tâm Ý Ngưng Nơi Đầu Kiếm",
    "Gacha.21110.1": "Hương Trà Chuếnh Choáng · Mộng Điệp Hoa Đằng",
    "Gacha.21115.1": "Nếu Có Thể Chạm Tới Muôn Vì Tinh Tú",
    "Gacha.21119.1": "Dây Lòng Định Âm",
    "Gacha.21133.1": "Nắng Chiều Nhẹ Rọi · Cùng Vào Giấc Mơ Xanh",
    "Gacha.21134.1": "Trời Đêm Rực Rỡ · Pháo Hoa Bừng Nở",
    "Gacha.21141.1": "Dây Lòng Định Âm",
    "Gacha.21144.1": "Trăng Nổi Soi Bóng Đầm Trong",
    "Gacha.21155.1": "Biển Trời Một Màu",
    "Gacha.3.1": "Khởi Đầu May Mắn",
}

UITEXT_GACHA_OVERRIDES = {
    "UIText.Confirm_Recruit_Char.1": "Chiêu mộ Du Hành Giả {0}?",
    "UIText.GachaCover1.1": "Thời gian còn lại",
    "UIText.GachaCover2.1": "Còn lại",
    "UIText.GachaCover3.1": "lượt chiêu mộ chắc chắn nhận Du Hành Giả Tiêu Điểm!",
    "UIText.GachaCover4.1": "lượt chiêu mộ chắc chắn nhận Khắc Ấn Tiêu Điểm!",
    "UIText.GachaCover5.1": "Lượt chiêu mộ còn lại:",
    "UIText.GachaCover6.1": "lượt",
    "UIText.GachaCover7.1": "Chắc chắn nhận ngẫu nhiên trong {0} lượt chiêu mộ",
    "UIText.GachaCover8.1": "Du Hành Giả",
    "UIText.GachaCover_DiscRemainCount.1": "Chắc chắn nhận Khắc Ấn Tiêu Điểm trong <color=#08d3d4>{0}</color> lượt chiêu mộ",
    "UIText.GachaCover_FirstTenTip.1": "Chiêu mộ x10 lần đầu nhận Đĩa Lấp Lánh Vàng <sprite name=item_602_small> <color=#09cdd0>x{0}</color> (gấp {1} lần bình thường)",
    "UIText.GachaCover_GuaranteeGetOverTip.1": "Đã nhận",
    "UIText.GachaCover_GuaranteeGetTip.1": "Nhấn để nhận thưởng",
    "UIText.GachaCover_GuaranteeRemainCount.1": "Còn lại <color=#08d3d4>{0}</color> lượt chiêu mộ để nhận thưởng",
    "UIText.GachaCover_GuaranteeRemainTip.1": "Chỉ 1 lần duy nhất",
    "UIText.GachaCover_Guarantee_Char.1": "Chắc chắn nhận Du Hành Giả 5★ trong <color=#08d3d4>{0}</color> lượt chiêu mộ tiếp theo",
    "UIText.GachaCover_Guarantee_Disc.1": "Chắc chắn nhận Khắc Ấn 5★ trong <color=#08d3d4>{0}</color> lượt chiêu mộ tiếp theo",
    "UIText.GachaCover_OneRewardTip.1": "Mỗi lượt chiêu mộ nhận Đĩa Lấp Lánh Vàng <sprite name=item_602_small> × <color=#09cdd0>{0}</color>",
    "UIText.GachaCover_RemainCount.1": "Chắc chắn nhận Du Hành Giả Tiêu Điểm trong <color=#08d3d4>{0}</color> lượt chiêu mộ tiếp theo",
    "UIText.GachaCover_TimeCountDown.1": "Thời gian còn lại: <color=#08d3d4>{0}</color>",
    "UIText.GachaHistory_Desc.1": "*Trang này hiển thị lịch sử chiêu mộ trong vòng 6 tháng gần nhất.",
    "UIText.GachaHistory_Guarantee.1": "Chi Tiết Bảo Trợ (Pity)",
    "UIText.GachaHistory_History.1": "Lịch Sử Chiêu Mộ",
    "UIText.GachaHistory_Name.1": "Tên",
    "UIText.GachaHistory_Rank.1": "Độ hiếm",
    "UIText.GachaHistory_Tag.1": "Kỳ Chiêu Mộ",
    "UIText.GachaHistory_Time.1": "Thời gian",
    "UIText.GachaHistory_Type.1": "Phân loại",
    "UIText.GachaItemTIpsTitle.1": "Vật phẩm nhận được",
    "UIText.GachaJumpAll.1": "Bỏ qua",
    "UIText.Gacha_Cover_CharUpTitle.1": "Tăng Tỷ Lệ Xuất Hiện Các Du Hành Giả Trên!!",
    "UIText.Gacha_Cover_DiscUpTitle.1": "Tăng Tỷ Lệ Xuất Hiện Các Khắc Ấn Trên!!",
    "UIText.Gacha_Cover_GoToTrial.1": "Dùng thử",
    "UIText.Gacha_Cover_UpItemTitle.1": "{0}",
    "UIText.Gacha_FesGacha.1": "Giới hạn",
    "UIText.Gacha_GachaTimeLimit.1": "Giới hạn chiêu mộ mỗi ngày: {0}/{1}",
    "UIText.Gacha_GachaTimeLimitTips.1": "Không đủ số lượt chiêu mộ còn lại, không thể tiến hành",
    "UIText.Gacha_GiveItemTitle.1": "Quà Tặng Kèm Chiêu Mộ",
    "UIText.Gacha_History_UPMark.1": "RATE UP",
    "UIText.Gacha_NewBieHint.1": "Số lượt còn lại không đủ",
    "UIText.Gacha_NewBieJumpHint.1": "Đến nhiệm vụ",
    "UIText.Gacha_NewBieNoRecordTip.1": "Hiện chưa có kết quả chiêu mộ~",
    "UIText.Gacha_NewBieObtainCancel.1": "Để tôi suy nghĩ lại",
    "UIText.Gacha_NewBieObtainOk.1": "Xác nhận & Nhận kết quả",
    "UIText.Gacha_NewBieObtainTitle.1": "Xác Nhận Kết Quả Chiêu Mộ",
    "UIText.Gacha_NewBieRecord.1": "Kết quả đã lưu",
    "UIText.Gacha_NewBieRecordResult.1": "Kết quả đã lưu ({0})",
    "UIText.Gacha_NewBieRecordResultRemain.1": "Còn lại: <color=#08d3d4>{0}</color>",
    "UIText.Gacha_NewBieReplaceCancel.1": "Đóng",
    "UIText.Gacha_NewBieReplaceOk.1": "Thay thế",
    "UIText.Gacha_NewBieReplaceTitle.1": "Thay Thế Kết Quả Chiêu Mộ",
    "UIText.Gacha_NewBieResultSummonAgain.1": "Chiêu mộ lại",
    "UIText.Gacha_NewBieSaveItem.1": "Kết quả {0}",
    "UIText.Gacha_NewBieSaveItemCurrent.1": "Hiện tại",
    "UIText.Gacha_NewBieSaveRecordCancel.1": "Đóng",
    "UIText.Gacha_NewBieSaveRecordOk.1": "Thay thế",
    "UIText.Gacha_NewBieSaveRecordTip.1": "Có thể lưu kết quả chiêu mộ vào danh sách bên dưới ({0})",
    "UIText.Gacha_NewBieSaveRecordTitle.1": "Kết quả chiêu mộ đã lưu",
    "UIText.Gacha_NewBieSaveResult.1": "Lưu kết quả này",
    "UIText.Gacha_NewBieSaveTip.1": "Lưu kết quả chiêu mộ thành công",
    "UIText.Gacha_NewBieSelect.1": "Đã chọn",
    "UIText.Gacha_NewBieShowCancel.1": "Đóng",
    "UIText.Gacha_NewBieShowOk.1": "Nhận kết quả đã chọn",
    "UIText.Gacha_NewBieShowTitle.1": "Kết quả chiêu mộ đã lưu",
    "UIText.Gacha_NewBieSummonCost.1": "Miễn phí",
    "UIText.Gacha_NewBieSummonLimit.1": "Đã đạt giới hạn lượt chiêu mộ",
    "UIText.Gacha_NewBieSummonNum.1": "Lượt chiêu mộ còn lại: <color=#08d3d4>{0}</color> vòng",
    "UIText.Gacha_NewBieSummonTip.1": "Chiêu Mộ Tân Thủ: Tối đa <color=#08d3d4>{0}</color> vòng chiêu mộ x10 và được chọn <color=#08d3d4>{1}</color> vòng kết quả ưng ý nhất để nhận!",
    "UIText.Gacha_NewBieSummonTitle.1": "Chiêu Mộ x10",
    "UIText.Gacha_Newbie_BtnShowRecord.1": "Xem kết quả chiêu mộ",
    "UIText.Gacha_Newbie_RecordSSRHint.1": "Kết quả hiện tại có <color=#fb8037>Nhân vật độ hiếm cao</color>.\nBạn có chắc chắn không lưu kết quả này và chiêu mộ lại không?",
    "UIText.Gacha_Pool_Rate.1": "Tỷ lệ chiêu mộ",
    "UIText.Gacha_Prob.1": "Chi tiết tỷ lệ",
    "UIText.Gacha_ProbValue.1": "Tỷ lệ",
    "UIText.Gacha_Prob_Time.1": "Thời gian mở:",
    "UIText.Gacha_Record.1": "Lịch sử chiêu mộ",
    "UIText.Gacha_Single.1": "Chiêu mộ 1 lần",
    "UIText.Gacha_Ten.1": "Chiêu mộ 10 lần",
    "UIText.Gacha_sync_ack.1": "Số lượng tài nguyên bất thường, vui lòng chiêu mộ lại",
    "UIText.MainView_Recruit.1": "Chiêu Mộ",
    "UIText.Recruit_Charge.1": "Không đủ <sprite name=item_{0}_small>, bạn có muốn đến trang Nạp không?",
    "UIText.Recruit_ComboDrawTicket.1": "Dùng {0} <sprite name=item_{1}_small> và {2} <sprite name=item_{3}_small> để chiêu mộ?",
    "UIText.Recruit_Exchange.1": "Dùng {0} <sprite name=item_{1}_small> mua {2} <sprite name=item_{3}_small> để chiêu mộ?",
    "UIText.Recruit_ExchangeGem.1": "Hiện có {0} <sprite name=item_{1}_small>.\nDùng {2} <sprite name=item_{3}_small> mua {4} <sprite name=item_{5}_small> để chiêu mộ?",
    "UIText.Recruit_ExchangeGem2.1": "Hiện có {0} <sprite name=item_{1}_small> {2} <sprite name=item_{3}_small>.\nDùng {4} <sprite name=item_{5}_small> mua {6} <sprite name=item_{7}_small> để chiêu mộ?",
    "UIText.Recruit_ExchangeGemZero.1": "Không đủ <sprite name=item_{0}_small>, dùng {1} <sprite name=item_{2}_small> để bù vào?",
    "UIText.Recruit_history.1": "Lịch Sử Chiêu Mộ",
    "UIText.Recruit_history_empty.1": "Chưa có lịch sử chiêu mộ",
    "UIText.Recruit_info.1": "Chi Tiết Kỳ Chiêu Mộ",
    "UIText.Recruit_one.1": "Chiêu Mộ x1",
    "UIText.Recruit_ten.1": "Chiêu Mộ x10",
    "UIText.Trial_Btn_GotoGacha.1": "Đến Chiêu Mộ",
}

def translate_gachatype_value(k: str, v: str) -> str:
    field = k.split('.')[-1]
    
    if field == "1":
        mapping_names = {
            "旅人限时招募": "Chiêu Mộ Du Hành Giới Hạn",
            "旅人常驻招募": "Chiêu Mộ Du Hành Thường",
            "秘纹限时招募": "Khắc Ấn Giới Hạn",
            "秘纹常驻招募": "Khắc Ấn Thường",
            "幸运启封": "Khởi Đầu May Mắn (Tân Thủ)",
            "星途一载·予缘重聚限时招募": "Một Năm Tinh Trình · Duyên Định Trùng Phùng (Giới Hạn)",
            "星途一载·予缘重聚": "Một Năm Tinh Trình · Duyên Định Trùng Phùng",
        }
        for cn, vi in mapping_names.items():
            if cn in v:
                return vi
        return v
        
    if field == "2":
        return "Mô Tả Kỳ Chiêu Mộ"
    if field == "4":
        return "Quy Tắc Xác Suất"
    if field == "6":
        return "Lưu Ý Đặc Biệt"
    if field == "8":
        if "旅人" in v:
            return "TĂNG TỶ LỆ DU HÀNH GIẢ!!"
        elif "秘纹" in v:
            return "TĂNG TỶ LỆ KHẮC ẤN!!"
        return "TĂNG TỶ LỆ!!"
    if field == "9":
        if "旅人" in v:
            return "Chiếm 50% tỷ lệ xuất hiện của Du Hành Giả 5★!"
        elif "秘纹" in v:
            return "Chiếm 75% tỷ lệ xuất hiện của Khắc Ấn 5★!"
        return "Chiếm 50% tỷ lệ xuất hiện của vật phẩm 5★!"
    if field == "10":
        if "旅人" in v:
            return "Chiếm 50% tỷ lệ xuất hiện của Du Hành Giả 4★!"
        elif "秘纹" in v:
            return "Chiếm 50% tỷ lệ xuất hiện của Khắc Ấn 4★!"
        return "Chiếm 50% tỷ lệ xuất hiện của vật phẩm 4★!"
    if field == "11":
        return "Danh Sách Vật Phẩm"
    if field == "12":
        if "旅人" in v:
            return "Du Hành Giả 5★ có thể xuất hiện"
        elif "秘纹" in v:
            return "Khắc Ấn 5★ có thể xuất hiện"
        return "Vật phẩm 5★ có thể xuất hiện"
    if field == "13":
        return "Du Hành Giả & Khắc Ấn 4★ có thể xuất hiện"
    if field == "14":
        return "Khắc Ấn 3★ có thể xuất hiện"
    if field == "15":
        res = v.replace("卡池为", "là ")
        res = res.replace("「旅人限时招募」", "「Chiêu Mộ Du Hành Giới Hạn」")
        res = res.replace("「旅人常驻招募」", "「Chiêu Mộ Du Hành Thường」")
        res = res.replace("「秘纹限时招募」", "「Khắc Ấn Giới Hạn」")
        res = res.replace("「秘纹常驻招募」", "「Khắc Ấn Thường」")
        res = res.replace("「幸运启封」", "「Khởi Đầu May Mắn」")
        res = res.replace("「1周年限定特选招募」", "「Đặc Tuyển Kỷ Niệm 1 Năm」")
        return res
    if field == "16":
        if "旅人" in v:
            return "Còn <color=#fb8037>{0}</color> lượt chiêu mộ chắc chắn nhận 1 trong các Du Hành Giả sau"
        elif "秘纹" in v:
            return "Còn <color=#fb8037>{0}</color> lượt chiêu mộ chắc chắn nhận 1 trong các Khắc Ấn sau"
        return "Còn <color=#fb8037>{0}</color> lượt chiêu mộ chắc chắn nhận 1 trong các mục sau"

    # Narrative text for .3, .5, .7, .17
    res = v
    replacements = [
        # Pool names
        ("「旅人限时招募」", "「Chiêu Mộ Du Hành Giới Hạn」"),
        ("「旅人常驻招募」", "「Chiêu Mộ Du Hành Thường」"),
        ("「秘纹限时招募」", "「Khắc Ấn Giới Hạn」"),
        ("「秘纹常驻招募」", "「Khắc Ấn Thường」"),
        ("「幸运启封」", "「Khởi Đầu May Mắn」"),
        ("「1周年限定特选招募」", "「Đặc Tuyển Kỷ Niệm 1 Năm」"),
        ("旅人限时招募", "Chiêu Mộ Du Hành Giới Hạn"),
        ("旅人常驻招募", "Chiêu Mộ Du Hành Thường"),
        ("秘纹限时招募", "Khắc Ấn Giới Hạn"),
        ("秘纹常驻招募", "Khắc Ấn Thường"),
        ("幸运启封", "Khởi Đầu May Mắn"),
        
        # Tickets
        ("「青空礼券」", "「Vé Thanh Không」"),
        ("「萌芽礼券」", "「Vé Nảy Mầm」"),
        ("「寻梦礼券」", "「Vé Tầm Mộng」"),
        ("「定音礼券」", "「Vé Định Âm」"),
        ("「重逢之缘限定招募礼券」", "「Vé Chiêu Mộ Giới Hạn Duyên Trùng Phùng」"),
        
        # Currency / tokens
        ("「对应5星旅人的心钥」", "「Chìa Khóa Tâm Hồn Du Hành Giả 5★ tương ứng」"),
        ("「对应4星旅人的心钥」", "「Chìa Khóa Tâm Hồn Du Hành Giả 4★ tương ứng」"),
        ("「对应5星秘纹的曲调」", "「Giai Điệu Khắc Ấn 5★ tương ứng」"),
        ("「对应4星秘纹的曲调」", "「Giai Điệu Khắc Ấn 4★ tương ứng」"),
        ("「对应3星秘纹的曲调」", "「Giai Điệu Khắc Ấn 3★ tương ứng」"),
        ("「探险专家凭证」", "「Chứng Nhận Chuyên Gia Thám Hiểm」"),
        ("「旅行执照」", "「Giấy Phép Du Lịch」"),
        ("「心钥」", "「Chìa Khóa Tâm Hồn」"),
        ("「曲调」", "「Giai Điệu」"),

        # Core mechanics
        ("5星限时旅人", "Du Hành Giả 5★ giới hạn"),
        ("5星常驻旅人", "Du Hành Giả 5★ thường"),
        ("5星旅人", "Du Hành Giả 5★"),
        ("4星旅人", "Du Hành Giả 4★"),
        ("5星限时秘纹", "Khắc Ấn 5★ giới hạn"),
        ("5星常驻秘纹", "Khắc Ấn 5★ thường"),
        ("5星秘纹", "Khắc Ấn 5★"),
        ("4星秘纹", "Khắc Ấn 4★"),
        ("3星秘纹", "Khắc Ấn 3★"),
        ("5星角色", "Nhân vật 5★"),
        ("4星角色", "Nhân vật 4★"),
        ("秘纹", "Khắc Ấn"),
        ("旅人", "Du Hành Giả"),
        ("保底", "bảo hiểm bảo trợ (Pity)"),
        ("招募次数", "số lượt chiêu mộ"),
        ("招募", "chiêu mộ"),
        ("卡池周期", "chu kỳ chiêu mộ"),
        ("卡池时间", "thời gian chiêu mộ"),
        ("卡池", "kỳ chiêu mộ"),
        ("基础概率为", "tỷ lệ cơ bản là "),
        ("基础获得概率为", "tỷ lệ nhận cơ bản là "),
        ("综合概率（含保底）为", "tỷ lệ tổng hợp (bao gồm bảo hiểm Pity) là "),
        ("必定能通过保底获得", "chắc chắn nhận thông qua bảo hiểm Pity "),
        ("必然能通过保底获得", "chắc chắn nhận thông qua bảo hiểm Pity "),
        ("最多", "tối đa "),
        ("次招募", " lượt chiêu mộ"),
        ("次", " lượt"),
        ("个", " cái"),
        ("当招募获得", "Khi chiêu mộ nhận "),
        ("的概率为", " có tỷ lệ là "),
        ("本期概率提升的", "tăng tỷ lệ của kỳ này "),
        ("本期招募中", "trong kỳ chiêu mộ này "),
        ("获得重复的", "Khi nhận trùng lặp "),
        ("将转化为", "sẽ chuyển hóa thành "),
        ("当", "Khi "),
        ("溢出时", "bị dư thừa/đầy"),
        ("每个该种", "mỗi "),
        ("特殊说明", "Lưu Ý Đặc Biệt"),
        ("概率说明", "Quy Tắc Xác Suất"),
        ("卡池说明", "Mô Tả Kỳ Chiêu Mộ"),
        ("独立计算，互不影响", "được tính độc lập và không ảnh hưởng lẫn nhau"),
        ("可继续累计到下期", "sẽ được tích lũy tiếp sang kỳ sau"),
        ("清零，不可累计到下个", "sẽ xóa về 0 và không tích lũy sang kỳ tiếp theo"),
        ("本卡池周期结束时", "Khi kết thúc chu kỳ chiêu mộ này"),
    ]

    for cn, vi in replacements:
        res = res.replace(cn, vi)
        
    return res

def main():
    print("=== STARTING FULL GACHA / RECRUITMENT LOCALIZATION ===")
    t0 = time.time()

    # 1. Update GachaStorage
    p_gs = ENTRIES_DIR / "00884_0x07f8babd51f803d6.bin"
    if p_gs.exists():
        d_gs = json.loads(p_gs.read_text(encoding="utf-8"))
        for k, v in GACHA_STORAGE_TRANSLATIONS.items():
            d_gs[k] = v
        p_gs.write_text(json.dumps(d_gs, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Updated GachaStorage: {len(GACHA_STORAGE_TRANSLATIONS)} categories translated.")

    # 2. Update Gacha Banners
    p_gacha = ENTRIES_DIR / "00883_0x7b0a2a29ce7d024e.bin"
    if p_gacha.exists():
        d_gacha = json.loads(p_gacha.read_text(encoding="utf-8"))
        for k, v in GACHA_BANNER_TRANSLATIONS.items():
            d_gacha[k] = v
        p_gacha.write_text(json.dumps(d_gacha, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Updated Gacha: {len(GACHA_BANNER_TRANSLATIONS)} banner names translated.")

    # 3. Update GachaType Rules & Odds
    p_gt = ENTRIES_DIR / "00885_0x244b924d0e05f10c.bin"
    if p_gt.exists():
        d_gt = json.loads(p_gt.read_text(encoding="utf-8"))
        gt_count = 0
        for k, v in d_gt.items():
            new_v = translate_gachatype_value(k, v)
            if new_v != v:
                d_gt[k] = new_v
                gt_count += 1
        p_gt.write_text(json.dumps(d_gt, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Updated GachaType: {gt_count} rule and odds strings translated.")

    # 4. Update UIText
    uitext_files = [
        ENTRIES_DIR / "00789_0x87cc29ac0defc2d9.bin",
        ENTRIES_DIR / "01036_0x363690c09b175230.bin"
    ]
    for p_ui in uitext_files:
        if p_ui.exists():
            d_ui = json.loads(p_ui.read_text(encoding="utf-8"))
            ui_count = 0
            for k, v in UITEXT_GACHA_OVERRIDES.items():
                if k in d_ui and d_ui[k] != v:
                    d_ui[k] = v
                    ui_count += 1
            p_ui.write_text(json.dumps(d_ui, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Updated {p_ui.name}: {ui_count} Gacha UI strings overhauled.")

    # 5. Repack data.arcx with XXTEA encryption
    print("\nRepacking dist/data_patched_vi.arcx with XXTEA encryption...")
    repack_archive(DEC_DIR, OUTPUT_ARCX, encrypt_payload=True)

    arc = ArcxArchive(OUTPUT_ARCX)
    arcx_size = OUTPUT_ARCX.stat().st_size
    with open(OUTPUT_ARCX, "rb") as f:
        arcx_sha256 = hashlib.sha256(f.read()).hexdigest()

    elapsed = time.time() - t0
    print(f"SUCCESS! Created {OUTPUT_ARCX} in {elapsed:.2f}s:")
    print(f"  Size: {arcx_size:,} bytes")
    print(f"  Entries: {len(arc.entries)}")
    print(f"  SHA-256: {arcx_sha256}")

    # 6. Dual-Sync to Live Games
    dests = [
        ROOT / "work" / "research" / "data_patched_vi.arcx",
        Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx"),
        Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Tables\data.arcx")
    ]
    print("\nDeploying to live game environments...")
    for d in dests:
        if d.parent.exists():
            shutil.copy2(OUTPUT_ARCX, d)
            print(f"  -> Synced to: {d} ({d.stat().st_size:,} bytes)")

    print("\n=======================================================")
    print("GACHA LOCALIZATION SUCCESSFULLY APPLIED AND DEPLOYED!")
    print("=======================================================")

if __name__ == "__main__":
    main()
