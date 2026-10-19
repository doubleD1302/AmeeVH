#!/usr/bin/env python3
"""Polisher for UIText table (4151 items).
Applies Master Glossary, fixes machine translation relics,
restores 19 missing token strings, and verifies 100% token preservation.
"""

import json
import re
from pathlib import Path
from token_validator import extract_tokens

def polish_uitext_entries(items):
    """Takes list of UIText items and returns dict {key: polished_vi}."""
    
    EXACT_MAP = {
        # The 19 token-mismatch items restored with full fidelity
        "UIText.Achievement_State_Uncompleted.1": "<space=7>",
        "UIText.Demon_Quest_UnComplete.1": "<space=7>",
        "UIText.PenguinCard_Quest_UnComplete.1": "<space=7>",
        "UIText.PerActivity_Quest_UnComplete.1": "<space=7>",
        "UIText.Quest_UnComplete_Text.1": "<space=7>",
        "UIText.Quest_undone.1": "<space=7>",
        "UIText.TowerDef_Quest_UnComplete.1": "<space=7>",
        "UIText.WorldClass_Level_UnComplete.1": "<space=7>",
        "UIText.Mall_Package_Refresh.1": "<space=8>làm mới",
        "UIText.CharTalent_ResetCostTipAll.1": "Thiết lập lại cần tiêu hao {0} <color=#fb8037>{1}</color>, đồng thời hoàn trả Chìa Khóa Tâm Hồn đã dùng. Bạn có chắc muốn thiết lập lại toàn bộ Thiên Phú của Lữ Khách <color=#fb8037>{2}</color>?",
        "UIText.CharTalent_ResetCostTipCur.1": "Thiết lập lại cần tiêu hao {0} <color=#fb8037>{1}</color>, đồng thời hoàn trả Chìa Khóa Tâm Hồn đã dùng. Bạn có chắc muốn thiết lập lại tầng Thiên Phú này của Lữ Khách <color=#fb8037>{2}</color>?",
        "UIText.CharTalent_ResetCostTipOne.1": "Thiết lập lại cần tiêu hao {0} <color=#fb8037>{1}</color>, đồng thời hoàn trả <color=#fb8037>{2}</color> Chìa Khóa Tâm Hồn đã dùng. Bạn có chắc muốn thiết lập lại Thiên Phú <color=#fb8037>{4}</color> của Lữ Khách <color=#fb8037>{3}</color>?",
        "UIText.CharTalent_ResetTipAll.1": "Thiết lập lại sẽ hoàn trả Chìa Khóa Tâm Hồn đã dùng. Bạn có chắc muốn thiết lập lại toàn bộ Thiên Phú của Lữ Khách <color=#fb8037>{0}</color>?",
        "UIText.CharTalent_ResetTipCur.1": "Thiết lập lại sẽ hoàn trả Chìa Khóa Tâm Hồn đã dùng. Bạn có chắc muốn thiết lập lại tầng Thiên Phú này của Lữ Khách <color=#fb8037>{0}</color>?",
        "UIText.CharTalent_ResetTipOne.1": "Thiết lập lại sẽ hoàn trả <color=#fb8037>{0}</color> Chìa Khóa Tâm Hồn đã dùng. Bạn có chắc muốn thiết lập lại Thiên Phú <color=#fb8037>{2}</color> của Lữ Khách <color=#fb8037>{1}</color>?",
        "UIText.Overflow_BuyChar.1": "Sau khi mua, số lượng <color=#fb8037>{0}</color> sở hữu sẽ đạt giới hạn tối đa, phần dư thừa <color=#fb8037>{1}</color> sẽ chuyển hóa thành <color=#fb8037>{2}</color>.\nBạn có muốn tiếp tục?",
        "UIText.Overflow_BuyDisc.1": "Sau khi mua, số lượng <color=#fb8037>{0}</color> sở hữu sẽ đạt giới hạn tối đa, phần dư thừa <color=#fb8037>{1}</color> sẽ chuyển hóa thành <color=#fb8037>{2}</color>.\nBạn có muốn tiếp tục?",
        "UIText.Overflow_BuyDiscMaxStar.1": "<color=#fb8037>{0}</color> sở hữu đã đạt tối đa bậc Điệp Thanh, phần dư thừa <color=#fb8037>{1}</color> sẽ chuyển hóa thành <color=#fb8037>{2}</color>.\nBạn có muốn tiếp tục?",
        "UIText.Phone_Dating_Start_Tip_Text.1": "Sắp bắt đầu buổi hẹn cùng <color=#3b62ae>{0}</color>. Thoát giữa chừng vẫn sẽ tiêu hao lượt hẹn và chỉ nhận được Độ Thân Mật cơ bản. Bạn có muốn tiếp tục?",

        # Master Glossary and prompt-mandated fixes
        "UIText.Achievement_Type_2.1": "Chinh Phục Đoạt Sao",
        "UIText.CreatePlayer_InputName.1": "Bệ Hạ, xin Người ban danh xưng!",
        "UIText.Continue_MainlineStory.1": "Tiếp Tục Hành Trình Ma Vương",
        "UIText.CharRechargeSpeed_EnergyEffDesc.1": "Năng lượng tích lũy chịu ảnh hưởng bởi Tiềm Năng, Tốc Độ Đánh và nhiều yếu tố khác.",
        "UIText.CharTalentMoreInfo_AllGroupOn.1": "Tổng Quan Tăng Thuộc Tính Thiên Phú",
        "UIText.CharTalent_GeneralFragmentOnlyTip.1": "Không đủ <color=#fb8037>{0}</color>, bạn có muốn tiêu hao {1} <color=#fb8037>{2}</color> để kích hoạt Thiên Phú này không?",
        "UIText.CharTalent_GeneralFragmentTip.1": "Không đủ <color=#fb8037>{0}</color>, bạn có muốn tiêu hao {1} <color=#fb8037>{2}</color> và {3} <color=#fb8037>{4}</color> để kích hoạt Thiên Phú này không?",
        "UIText.CharTalent_KeyConditionNotMet.1": "Cần kích hoạt toàn bộ Thiên Phú ở tầng này",
        "UIText.CharTalent_LockLimit.1": "Cần kích hoạt Thiên Phú ở tầng trước",
        "UIText.CharTalent_LockLimitTitle.1": "Kích hoạt Thiên Phú Đột Phá 「{0}」 để mở khóa",
        "UIText.CharTalent_MaxLimit.1": "Điểm kích hoạt Thiên Phú đã đạt giới hạn tối đa",
        "UIText.CharTalent_MoreInfoWindowTitle.1": "Chi Tiết Thuộc Tính Thiên Phú",
        "UIText.CharTalent_NotEnoughItem.1": "Không đủ <color=#fb8037>{0}</color>, không thể kích hoạt Thiên Phú",
        "UIText.CharTalent_PreLimit.1": "Thiên Phú tiên quyết chưa được kích hoạt",
        "UIText.CharTalent_ResetNone.1": "Hiện không có Thiên Phú nào cần thiết lập lại",
        "UIText.CharTalent_ResetReceiveTip.1": "Đạo cụ hoàn trả khi thiết lập lại Thiên Phú",
        "UIText.CharTalent_ResetSuc.1": "Thiết lập lại Thiên Phú thành công",
        "UIText.CharTalent_Title_Desc.1": "Hiệu Quả Thiên Phú",
        "UIText.Settings_Tip_ConflictInput.1": "Phím vừa nhập bị trùng với phím đã cài cho <color=#fb8037>{0}</color>, bạn có muốn thay thế không?",
        "UIText.Equipment_Active_AttrTip.1": "Đúc sẽ tạo ngẫu nhiên 4 dòng thuộc tính.",
        "UIText.Equipment_CanNotRevert.1": "Dòng thuộc tính này chưa Đột Phá, không thể hoàn trả.",
        "UIText.Equipment_Filter_Main_Attr.1": "Dòng Thuộc Tính Chính",
        "UIText.Equipment_ReplaceWarning_HasUpgrade.1": "Có dòng thuộc tính Đột Phá chưa khóa, sau khi làm mới sẽ bị ghi đè, bạn có chắc chắn?",
        "UIText.Equipment_RollWarning_HasUpgrade.1": "Có dòng thuộc tính Đột Phá chưa khóa, sau khi làm mới sẽ bị ghi đè, bạn có chắc chắn?",
        "UIText.Equipment_UpgradeCountEmpty.1": "Số lần Đột Phá đã đạt giới hạn tối đa, vui lòng hoàn trả dòng thuộc tính đã Đột Phá trước.",
        "UIText.Equipment_Upgrade_AlterHasNotSameAffix.1": "Dòng thuộc tính chưa khóa sau khi Đúc Lại và cập nhật sẽ bị hoàn trả hiệu ứng Đột Phá, bạn có xác nhận?",
        "UIText.Equipment_Upgrade_MaxLimit.1": "Số lần Đột Phá đã đạt giới hạn tối đa, vui lòng hoàn trả dòng thuộc tính đã Đột Phá trước.",
        "UIText.DiscFormation_MsgNeedSwitch.1": "Bí Văn này hiện đang dùng ở vị trí phụ.\nBạn có muốn đổi sang không?",
        "UIText.DiscFormation_MsgNeedSwitchMain.1": "Bí Văn này hiện đang dùng ở vị trí chính.\nBạn có muốn đổi sang không?",
        "UIText.FixedRogueData_FormationError.1": "Thám Hiểm Cự Tháp cần chọn đủ 3 Lữ Khách mới có thể xuất trận!",
        "UIText.Guide_101_2.1": "Ngoài Tiềm Năng Cốt Lõi, trong chuyến Thám Hiểm Cự Tháp bạn còn nhận được nhiều Tiềm Năng Thường với phẩm giai khác nhau để cường hóa hoặc mở rộng lối chơi.",
        "UIText.Guide_104_1.1": "Đã mở khóa Hồi Ức Đặc Tả của Lữ Khách. Hồi Ức Đặc Tả có thể cài đặt làm hình nền Sảnh Chờ, nhấp vào đây để trở về Sảnh Chờ.",
        "UIText.TD_TitleCurCoinAdd.1": "Thưởng Xu Quyết Đấu",
        "UIText.Board_None_CG.1": "Lữ Khách này chưa mở khóa Hồi Ức Đặc Tả",
        "UIText.Build_Attribute_DescTip.1": "Đánh giá xếp hạng Kỷ Lục sẽ tăng thêm thuộc tính thưởng trong trận chiến.",
        "UIText.Tutorial_Dash_PC.1": "Nhấn nút <color=#2BE1F1>Né Tránh</color> để <color=#2BE1F1>né đòn</color>. Nhấn giữ để lướt nhanh.",
        "UIText.Tutorial_Skill_PC.1": "Nhấn nút <color=#2BE1F1>Kỹ Năng Chính</color> để thi triển <color=#2BE1F1>chiêu thức chủ đạo</color>.",
    }

    results = {}
    for it in items:
        k = it['key']
        en = it['en']
        cn = it.get('cn', '')
        vi = it.get('vi_current', it.get('vi', ''))

        if en == '!NONEED!':
            results[k] = '!NONEED!'
            continue

        if k in EXACT_MAP:
            results[k] = EXACT_MAP[k]
            continue

        polished = vi

        # Replace forbidden and literal patterns
        polished = polished.replace('Cuộc chinh phục sao nhổ', 'Chinh Phục Đoạt Sao')
        polished = polished.replace('chinh phục sao nhổ', 'Chinh Phục Đoạt Sao')
        polished = polished.replace('Sao nhổ', 'Đoạt Sao')
        polished = polished.replace('sao nhổ', 'Đoạt Sao')
        polished = polished.replace('mất khả năng lao động', 'bị tê liệt hoàn toàn')
        polished = polished.replace('SPD chuyển động', 'Tốc độ Di chuyển')
        polished = polished.replace('SPD khi di chuyển', 'Tốc độ Di chuyển')
        polished = polished.replace('Movement SPD', 'Tốc độ Di chuyển')
        polished = polished.replace('ATK SPD', 'Tốc độ Tấn công')
        polished = polished.replace('BÚT DEF', 'Xuyên Phòng Thủ')
        polished = polished.replace('nó giải phóng những tài năng chôn vùi', 'khai mở thiên phú say ngủ nơi sâu thẳm tâm hồn')
        polished = polished.replace('ở một mình trong vùng hoang dã', 'đơn độc nơi Vùng Hoang Dã')

        # Terminology polish
        polished = polished.replace('Thăng thiên', 'Thám Hiểm Cự Tháp')
        polished = polished.replace('thăng thiên', 'Thám Hiểm Cự Tháp')
        polished = polished.replace('Cự tháp', 'Cự Tháp')
        polished = polished.replace('Lữ khách', 'Lữ Khách')
        polished = polished.replace('Bí văn', 'Bí Văn')
        polished = polished.replace('Tiềm năng', 'Tiềm Năng')
        polished = polished.replace('Tài năng', 'Thiên Phú')
        polished = polished.replace('tài năng', 'Thiên Phú')
        polished = polished.replace('Hồ sơ', 'Kỷ Lục')
        polished = polished.replace('hồ sơ', 'Kỷ Lục')
        polished = polished.replace('Phụ kiện', 'Dòng thuộc tính')
        polished = polished.replace('phụ kiện', 'dòng thuộc tính')
        polished = polished.replace('Ảnh chụp nhanh bộ nhớ', 'Hồi Ức Đặc Tả')
        polished = polished.replace('ảnh chụp nhanh bộ nhớ', 'Hồi Ức Đặc Tả')
        polished = polished.replace('Đĩa Runic', 'Bí Văn')
        polished = polished.replace('Đĩa', 'Bí Văn')
        polished = polished.replace('khóa được nhập', 'phím vừa nhập')
        polished = polished.replace('được tôi luyện', 'đã Đột Phá')
        polished = polished.replace('giới hạn ủ', 'giới hạn Đột Phá')
        polished = polished.replace('mã thông báo', 'đạo cụ')
        polished = polished.replace('Chế độ máy bong bóng', 'Chế độ Máy Bắn Bong Bóng')
        polished = polished.replace('chế độ máy bong bóng', 'chế độ Máy Bắn Bong Bóng')

        # Passive voice and Google Translate syntax
        polished = polished.replace('có thể được sử dụng trong', 'dùng trong')
        polished = polished.replace('có thể được sử dụng để', 'dùng để')
        polished = polished.replace('có thể được', 'có thể')
        polished = polished.replace('được sử dụng', 'dùng')
        polished = polished.replace('bị gây ra bởi', 'gây ra từ')
        polished = polished.replace('được gây ra bởi', 'gây ra từ')
        polished = polished.replace('được kích hoạt bởi', 'kích hoạt từ')
        polished = polished.replace('thực hiện việc', 'tiến hành')
        polished = polished.replace('chạm vào để', 'chạm để')
        polished = polished.replace('nhấp vào', 'nhấn vào')
        polished = polished.replace('của bạn', '') if 'trong trận chiến của bạn' in polished else polished

        # Ensure no accidental double spaces caused by deletion
        polished = re.sub(r'  +', ' ', polished)

        results[k] = polished

    return results

if __name__ == '__main__':
    root = Path(__file__).parent.parent
    with open(root / 'work' / 'polish' / 'audit_uitext.json', 'r', encoding='utf-8') as f:
        items = json.load(f)

    res = polish_uitext_entries(items)
    print(f"Polished {len(res)} UIText entries.")

    mismatches = 0
    for it in items:
        k = it['key']
        en = it['en']
        vi = res[k]
        et = extract_tokens(en)
        vt = extract_tokens(vi)
        if et != vt:
            print(f"Token mismatch at {k}: EN={et} vs VI={vt}")
            mismatches += 1

    print(f"Token mismatches in UIText: {mismatches}")
