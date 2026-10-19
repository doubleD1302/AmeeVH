#!/usr/bin/env python3
"""Module for polishing DatingCharacterEvent table (670 items)."""

from pathlib import Path

DCHAR_CUSTOM = {
    # Amber Cat scene
    'DatingCharacterEvent.103301.1': 'Bất chợt, bạn và Amber cùng nghe thấy tiếng mèo kêu meo meo.\n\nAmber lập tức di chuyển, thoăn thoắt lướt đi trong bóng tối rồi nhanh chóng lần theo âm thanh tìm thấy một chú mèo con.',
    'DatingCharacterEvent.103301.2': 'Bạn vô cùng kinh ngạc trước "thể chất hút mèo" kỳ diệu của cô ấy, vừa thở hổn hển vừa bảo rằng mình thật sự chẳng thể nào theo kịp tốc độ của nàng.',
    'DatingCharacterEvent.103301.3': 'Amber ôm chú mèo con trong lòng, gương mặt thoáng nét lưu luyến không nỡ buông—cô ấy biết Lữ đoàn Blank hiện tại e rằng chưa đủ điều kiện để nhận nuôi bé.\n\nVì thế, hai bạn quyết định cứ thế tận hưởng trọn vẹn khoảng thời gian bình yên bên chú mèo nhỏ.',
    'DatingCharacterEvent.103301.5': 'Kỳ Ngộ Mèo Con',
    'DatingCharacterEvent.103301.6': 'Đến Cảng để mở khóa',
    'DatingCharacterEvent.103301.7': 'Bạn và Amber tình cờ gặp chú mèo con bị mùi cá hấp dẫn ở Cảng.\nTuy chưa đủ điều kiện nhận nuôi, nhưng hai bạn đã cùng chú mèo nhỏ trải qua những giây phút vô cùng vui vẻ.',

    # Amber Cafeteria scene
    'DatingCharacterEvent.103303.1': 'Bạn và Amber bước vào nhà ăn sinh viên, sau một hồi tìm kiếm rốt cuộc cũng thấy một quầy không cần quẹt thẻ học viên. Hai bạn chỉ tay vào món ăn mình thích, nhưng khi thấy bác nhà ăn bắt đầu vung chiếc muôi lớn lên, trong lòng bạn bỗng dâng lên dự cảm chẳng lành.',
    'DatingCharacterEvent.103303.2': 'Ban đầu, bác múc lên một muôi đầy tới năm viên thịt, bạn và Amber khẽ thốt lên mừng rỡ. Thế rồi cổ tay bác lắc nhẹ một cái, một viên thịt văng ra ngoài. Lại thêm một cú rung nữa, lại thêm một viên rơi lại vào nồi. Đến khi thức ăn được trút vào khay, trong muôi thậm chí vẫn còn sót lại một viên thịt nữa.',
    'DatingCharacterEvent.103303.3': 'Bạn và Amber buồn bã nhìn khay đồ ăn chỉ còn vỏn vẹn hai viên thịt giữa một biển rau xanh. Mỗi người chỉ được một viên, thế còn lại thì sao? Hai người nhìn nhau cười trừ, bất lực ngắm nhìn đống rau xanh bạt ngàn. Haiz—lát nữa phải dắt Amber đi ăn thêm thứ khác thôi.',
    'DatingCharacterEvent.103303.5': 'Kỳ Ngộ Căng Tin',
    'DatingCharacterEvent.103303.6': 'Đến Học Viện để mở khóa',
    'DatingCharacterEvent.103303.7': 'Cùng Amber nếm trải "kỹ thuật múc thức ăn" kinh điển lưu truyền trong giới học viên, trái tim hai bạn cũng lên bổng xuống trầm theo từng nhịp lắc muôi. Sao ngay cả ăn cơm căng tin cũng chẳng thể nào "mắt thấy là tay được" thế này?',

    # Tilia poster fine print scene
    'DatingCharacterEvent.107301.1': 'Nhân viên cửa hàng nhiệt tình chỉ vào áp phích quảng cáo sự kiện.\n\nĐầy bất ngờ, Tilia lại ghé sát mắt soi kỹ từng dòng điều khoản in chữ nhỏ bên dưới.',
    'DatingCharacterEvent.107301.2': '"Ừm, ít nhất thì xét từ góc độ sự kiện, chưa thấy có chỗ nào vi phạm quy định cả."\n\nCô ấy thở phào một tiếng, rồi quay trở lại chỗ ngồi.',
    'DatingCharacterEvent.107301.3': '"A ha, hình như tôi bị bệnh nghề nghiệp quá rồi." Cô ấy gãi gãi đầu ngượng nghịu.\n\nNhưng bạn lại cảm thấy, cô gái lúc này quả thực đang tỏa ra vầng hào quang rạng rỡ của một "sứ giả chính nghĩa".',
    'DatingCharacterEvent.107301.5': 'Thói Quen Của Tilia',

    # Flora spell improv scene
    'DatingCharacterEvent.126303.3': '"Tước vũ khí!"\n"Lấy mạng ngươi!"\nSau tiếng hô đồng thanh, bạn ngã vật ra đất hệt như một Ma Vương vừa bị vị anh hùng cứu thế đánh bại.\nNghe thấy tiếng tách màn trập, bạn bật dậy đập tay ăn mừng cùng Flora vì hai người lại một lần nữa bắt đúng tần sóng của nhau, ngẫu hứng diễn nên một màn kịch xuất sắc.\nĐến lúc này hai bạn mới nhận ra tiếng chụp hình xuất phát từ đám học viên đang đứng xem kịch bên cạnh. Dưới tràng pháo tay giòn giã của mọi người, hai bạn đành đỏ mặt cùng cúi đầu chào rồi co giò chạy biến.',

    # Cafeteria broken artifact
    'DatingCharacterEvent.127303.2': 'Đột nhiên trong nhà ăn vang lên tiếng còi báo động chói tai. Lần theo âm thanh, hai bạn nhận ra Thần Khí cấp phát đồ ăn đã gặp sự cố hỏng hóc, điều này đồng nghĩa với việc những học viên đang xếp hàng phía sau có nguy cơ phải nhịn đói.',

    # Fuyuka scene
    'DatingCharacterEvent.134302.2': 'Dù có bạn ở bên an ủi, trên gương mặt Fuyuka vẫn thoáng chút muộn phiền.\n\n"Chẳng lẽ ngay cả Sư phụ... cũng có điều phải sợ hãi sao?"\n\n"Đương nhiên là có chứ," bạn mỉm cười nói. "Nhưng sợ hãi không đồng nghĩa với hèn nhát. Em vì lo lắng phía trước có nguy hiểm nên mới ngập ngừng chùn bước, đúng không? Thận trọng luôn là một đức tính tốt mà."',

    # Eleanor cake scene
    'DatingCharacterEvent.137301.3': '"Hương vị thế nào ạ, Tiền bối~?"\nEleanor lại xúc thêm một miếng bánh nữa, đưa chiếc thìa nhỏ đến bên khóe môi bạn, nụ cười rạng rỡ như hoa nở.\n"Nào, ngoan, há miệng ra nào, a~"\nTiểu thư đài các dường như đã hoàn toàn mê mẩn trò đút đồ ăn cho bạn mất rồi.',

    # Arcade amateurs
    'DatingCharacterEvent.140301.5': 'Tân Thủ Khu Trò Chơi',

    # Parfait server scene
    'DatingCharacterEvent.147303.2': '"Tiệc mừng công thì đương nhiên phải ăn parfait rồi!"\nNói thì nói vậy, nhưng số tiền trong túi cả hai gom lại cũng chỉ đủ mua thêm một phần, thế là hai bạn quyết định cùng chia sẻ một ly parfait.\nThế nhưng, khi nhân viên bồi bàn bưng ly parfait ra bàn, cả hai đều sững sờ kinh ngạc: Lượng kem hoa quả khổng lồ này, e rằng hai người ăn cả ngày cũng không hết!',

    # Nazuna claw machine scenes
    'DatingCharacterEvent.156301.2': 'Nazuna quả không hổ danh là cao thủ gắp thú kỳ cựu. Bỏ đồng xu vào, gắp gấu bông ra, mọi thao tác đều mượt mà uyển chuyển như mây trôi nước chảy.\nGiờ đây, cô nàng đang hào hứng chống cằm dõi theo bạn chật vật so tài cùng chiếc máy gắp.',
    'DatingCharacterEvent.156301.5': 'Đại Sư Gắp Gấu Bông',
    'DatingCharacterEvent.156301.7': 'Khi cùng Nazuna thi thố gắp gấu bông ở chợ, Nazuna sau khi hoàn thành phần thi đã tinh quái giở trò can thiệp khiến bạn thua trận thê thảm.\nTuy vậy, cô nàng vẫn hào phóng tặng lại toàn bộ số thú bông gắp được cho bạn. Xem ra bạn đã nhận được sự công nhận từ "Đại Sư Gắp Thú" rồi đấy.',
    'DatingCharacterEvent.156303.2': '"Sự kiện bốc thăm lần này tặng gấu bông ước nguyện từ Tinh Tháp đấy, cực kỳ quý hiếm lại còn giới hạn số lượng, tôi nhất định phải rinh bằng được một con!"\nMiệng thì nói đầy tự tin, nhưng khi nhân viên cầm thùng phiếu bước đến, Nazuna lại lộ rõ vẻ chần chừ, đôi mắt long lanh đáng thương nhìn sang bạn.\n"Ý em là muốn anh bốc thăm hộ à?"',
}

def polish_dating_character_item(item):
    k = item['key']
    en = item['en']
    vi = item['vi_current']

    if k in DCHAR_CUSTOM:
        return DCHAR_CUSTOM[k]

    # Global terminology & tone cleanups
    vi = vi.replace('Lữ khách', 'Lữ Khách')
    vi = vi.replace('Cự tháp', 'Cự Tháp')
    vi = vi.replace('vùng hoang dã', 'Vùng Hoang Dã')
    vi = vi.replace('Tân Tinh', 'Blank')
    vi = vi.replace('quán cà phê', 'nhà ăn')
    vi = vi.replace('máy chủ', 'nhân viên phục vụ')
    vi = vi.replace('bản in đẹp', 'điều khoản in chữ nhỏ')
    vi = vi.replace('nhà vô địch của công lý', 'sứ giả chính nghĩa')
    vi = vi.replace('Imperial Guard', 'Cận Vệ Hoàng Gia')
    vi = vi.replace('Chúa tể của móng vuốt giải thưởng', 'Đại Sư Gắp Thú')
    vi = vi.replace('Bạn có muốn tôi vẽ cho bạn không?', 'Ý em là muốn anh bốc thăm hộ à?')
    vi = vi.replace('Trò chơi điện tử nghiệp dư', 'Tân Thủ Khu Trò Chơi')

    return vi

if __name__ == '__main__':
    p = Path(__file__).resolve().parent.parent / 'work' / 'polish' / 'phase3_dataset.json'
    import json
    with open(p, 'r', encoding='utf-8') as f:
        items = json.load(f)['DatingCharacterEvent']

    polished = [polish_dating_character_item(it) for it in items]
    print(f"Polished {len(polished)} / {len(items)} DatingCharacterEvent items.")
    assert len(polished) == len(items)

    for i in range(10):
        print(f"  [{items[i]['key']}] EN: '{items[i]['en'][:60]}' -> VI: '{polished[i][:60]}'")
