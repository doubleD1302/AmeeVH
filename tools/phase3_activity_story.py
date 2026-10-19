#!/usr/bin/env python3
"""Module for polishing ActivityStory table (372 items)."""

from pathlib import Path

ACTIVITY_STORY_POLISH = {
    # Springseek Arc
    'ActivityStory.101040201.1': 'Biển Người Hội Ngộ Cố Nhân',
    'ActivityStory.101040201.2': 'Giữa Lễ Hội Nghênh Xuân, bạn bất chợt bắt gặp một bóng hình quen thuộc trên phố Thương Ngô...',
    'ActivityStory.101040202.1': 'Dạo Bước Phố Thị',
    'ActivityStory.101040202.2': 'Dạo quanh các nẻo đường Thương Ngô truy tìm manh mối, đồng thời trải nghiệm phong thổ nhân tình nơi đây.',
    'ActivityStory.101040203.1': 'Liễu Râm Hoa Rạng',
    'ActivityStory.101040203.2': 'Nắm bắt được manh mối then chốt, hai bạn tiếp tục lần theo dấu vết.',
    'ActivityStory.101040204.1': 'Mời Chàng Vào Tròng',
    'ActivityStory.101040204.2': 'Dùng mồi nhử tinh vi, dụ cho "thủ phạm" lộ diện...',
    'ActivityStory.101040205.1': 'Tóm Gọn Một Lưới',
    'ActivityStory.101040205.2': 'Đánh nhanh thắng nhanh, tóm gọn toàn bộ thủ phạm.',
    'ActivityStory.101040206.1': 'Gian Truân Mới Tỏ',
    'ActivityStory.101040206.2': 'Chân tướng đằng sau sự mất tích của những người bạn rốt cuộc cũng được sáng tỏ.',
    'ActivityStory.101040207.1': 'Tầm U Thám Kỳ',
    'ActivityStory.101040207.2': 'Nơi Cự Tháp sâu thẳm, dường như có điều gì đó đang âm thầm đổi thay...',
    'ActivityStory.101040208.1': 'Vén Mây Thấy Nắng',
    'ActivityStory.101040208.2': 'Dị thú này xem ra cũng không hung dữ tàn bạo như tưởng tượng.',
    'ActivityStory.101040209.1': 'Tấm Lòng Lương Y',
    'ActivityStory.101040209.2': 'Đừng chạy mà, tiêm một mũi là khỏe ngay thôi!',
    'ActivityStory.101040210.1': 'Năm Tháng Biền Biệt',
    'ActivityStory.101040210.2': 'Họ chỉ mong cầu một cái Tết đoàn viên yên bình.',

    # Snow Festival & Stove Arc
    'ActivityStory.201010204.1': 'Sắc Đỏ Rực Lửa',
    'ActivityStory.201010204.2': 'Bạn quyết định đến Câu lạc bộ Gió Tro để tìm hiểu ngọn ngành...',
    'ActivityStory.201010205.1': 'Sắc Xám Trùng Hợp',
    'ActivityStory.201010205.2': 'Bạn chọn tiếp tục trao phát quà cho những đứa trẻ...',
    'ActivityStory.201010206.1': 'Điệu Lam Tuyết Rơi',
    'ActivityStory.201010206.2': 'Bạn quyết định đuổi theo bước chân sứ giả ở con phố kế bên...',
    'ActivityStory.201010207.1': 'Tia Sáng Thân Quen',
    'ActivityStory.201010207.2': 'Cuối cùng hai bạn cũng lần theo kịp dấu tích về "tinh linh" bí ẩn.',
    'ActivityStory.201010208.1': 'Lời Nguyện Cô Đơn',
    'ActivityStory.201010208.2': 'Truyền thuyết về tinh linh kia, hóa ra chỉ là một mảnh ký ức nhuốm màu chua xót.',
    'ActivityStory.201010209.1': 'Phép Màu Tình Bạn',
    'ActivityStory.201010209.2': 'Ngày hôm ấy, Laru đã được chứng kiến thứ "phép thuật tình bạn" mà em chưa từng thấy bao giờ...',
    'ActivityStory.201010210.1': 'Thế Giới Bao La',
    'ActivityStory.201010210.2': 'Ngắm nhìn đàn cá dưới làn nước, lần đầu tiên cô đối diện với biển sâu trong lòng mình.',
    'ActivityStory.201010211.1': 'Khai Màn Hoành Tráng',
    'ActivityStory.201010211.2': 'Không khí lễ hội chạm tới cao trào, hôm nay cả Ma Vương và Laru đều nỗ lực phi thường!',
    'ActivityStory.201010212.1': '"Trò Chơi" Nguy Hiểm',
    'ActivityStory.201010212.2': 'Để thỏa ước nguyện của "cô ấy", hai bạn đã liều lĩnh đưa ra một quyết định đầy mạo hiểm...',
    'ActivityStory.201010213.1': 'Dư Âm Lễ Hội',
    'ActivityStory.201010213.2': 'Ảo Giác Bếp Lò bất ngờ ập đến, vì muốn "bảo hộ" Firefly, Laru đã dũng cảm đứng ra chặn đầu...?',
    'ActivityStory.201010214.1': 'Món Quà Dành Cho Bạn',
    'ActivityStory.201010214.2': 'Lễ hội trải qua bao sóng gió rốt cuộc cũng khép lại, giờ là khoảng thời gian riêng tư của đôi ta...',

    # Summer Vacation Arc
    'ActivityStory.201030201.1': 'Đến Lúc Đi Nghỉ Dưỡng Rồi!',
    'ActivityStory.201030201.2': 'Nghỉ ngơi thật tốt thì mới có sức làm việc hiệu quả chứ!',
    'ActivityStory.201030202.1': 'Diện Áo Tắm, Cầm Chổi Lên',
    'ActivityStory.201030202.2': 'Khu nghỉ dưỡng này sao lại đìu hiu vắng vẻ đến thế này...?',
    'ActivityStory.201030203.1': 'Trốn Tìm Bên Bờ Biển',
    'ActivityStory.201030203.2': 'Đã bảo cậu phải chú ý an toàn rồi mà!',
    'ActivityStory.201030204.1': 'Chuyện Lạ Máy Bán Hàng Tự Động',
    'ActivityStory.201030204.2': 'Chuyện kỳ lạ ắt có nguyên do, hóa ra nơi đây đang có "ma quấy phá"?',
    'ActivityStory.201030205.1': 'Sao Lại Là Ngươi Nữa!',
    'ActivityStory.201030205.2': 'Trận chiến nảy lửa cùng những Lữ Khách Tầm Bảo "ngầu" nhất cõi Nova!',
    'ActivityStory.201030206.1': 'Bóng Khổng Lồ Mang Bí Bảo',
    'ActivityStory.201030206.2': 'Rốt cuộc ngươi đang gánh trên vai bí mật nặng nề đến nhường nào?!',
    'ActivityStory.201030207.1': 'Xuất Sư Bất Lợi',
    'ActivityStory.201030207.2': 'Thời tiết trên biển bao giờ cũng biến ảo khôn lường...',
    'ActivityStory.201030208.1': 'Hóa Thành Đôi Tay Người',
    'ActivityStory.201030208.2': 'Nơi sâu thẳm ký ức mờ mịt của cô ấy, chôn giấu bao đớn đau và vết sẹo chưa lành.',
    'ActivityStory.201030209.1': 'Trời Lại Hửng Nắng',
    'ActivityStory.201030209.2': 'Thời tiết rốt cuộc cũng quang đãng... và tâm trạng cũng rạng rỡ theo.',
    'ActivityStory.201030210.1': 'Vị Khách Không Mời Giương Càng Lớn',
    'ActivityStory.201030210.2': 'Mà nghĩ lại... hình như nó chẳng có chút ác ý nào thì phải?',
    'ActivityStory.201030211.1': 'Gió Lộng Biển Xanh, Thong Dong Tự Tại',
    'ActivityStory.201030211.2': 'Mùa hạ hãy còn dài, cứ thong thả mà tận hưởng...',
}

def polish_activity_story_item(item):
    k = item['key']
    en = item['en']
    vi = item['vi_current']

    if k in ACTIVITY_STORY_POLISH:
        return ACTIVITY_STORY_POLISH[k]

    # Global cleanups
    vi = vi.replace('Lữ khách', 'Lữ Khách')
    vi = vi.replace('Cự tháp', 'Cự Tháp')
    vi = vi.replace('vùng hoang dã', 'Vùng Hoang Dã')
    vi = vi.replace('Springseek Festival', 'Lễ Hội Nghênh Xuân')
    vi = vi.replace('Lễ hội Springseek', 'Lễ Hội Nghênh Xuân')
    vi = vi.replace('Cangwu', 'Thương Ngô')
    vi = vi.replace('Lợi nhuận khó khăn', 'Gian Truân Mới Tỏ')
    vi = vi.replace('Mùa hè tháng ba', 'Hành Khúc Mùa Hè')
    vi = vi.replace('Khu bảo tồn mùa hè', 'Miền Trú Ẩn Mùa Hè')
    vi = vi.replace('Giai điệu thánh địa mùa hè', 'Giai Điệu Miền Trú Ẩn Mùa Hè')

    return vi

if __name__ == '__main__':
    from pathlib import Path
    import json
    p = Path(__file__).resolve().parent.parent / 'work' / 'polish' / 'phase3_dataset.json'
    with open(p, 'r', encoding='utf-8') as f:
        items = json.load(f)['ActivityStory']

    polished = [polish_activity_story_item(it) for it in items]
    print(f"Polished {len(polished)} / {len(items)} ActivityStory items.")
    assert len(polished) == len(items)

    for i in range(15):
        print(f"  [{items[i]['key']}] EN: '{items[i]['en']}' -> VI: '{polished[i]}'")
