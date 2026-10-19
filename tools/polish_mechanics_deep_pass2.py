#!/usr/bin/env python3
"""Deep clean pass 2: fix all 'bởi <color' passive structures into natural Vietnamese."""

import json
import re
from pathlib import Path

def polish_pass2(t: str) -> str:
    if not isinstance(t, str):
        return t

    # 1. MainSkill 401601..06 (Drifting Snow)
    t = re.sub(
        r'Khi Lữ Khách chủ lực hệ Phong gây Sát Thương Đòn Đánh Thường, 1/2/3 tầng "Phù Tuyết" gây ra những điều sau đây cho mục tiêu: tăng Sát Thương Đòn Đánh Thường hệ Phong thêm (<color=[^>]+>\{[^\}]+\}</color> / <color=[^>]+>\{[^\}]+\}</color> / <color=[^>]+>\{[^\}]+\}</color>) trong (\d+) giây\.',
        r'Khi Lữ Khách chủ lực hệ Phong gây Sát Thương Đòn Đánh Thường, 1/2/3 tầng "Phù Tuyết" sẽ khiến mục tiêu nhận thêm \1 Sát Thương Đòn Đánh Thường hệ Phong trong \2 giây.',
        t
    )
    t = re.sub(
        r'Khi Lữ Khách chủ lực hệ Phong gây Sát Thương Kỹ Năng, 1/2/3 tầng "Phù Tuyết" gây ra những điều sau đây cho mục tiêu: tăng Sát Thương Kỹ Năng hệ Phong nhận được bởi (<color=[^>]+>\{[^\}]+\}</color> / <color=[^>]+>\{[^\}]+\}</color> / <color=[^>]+>\{[^\}]+\}</color>) trong (\d+) giây\.',
        r'Khi Lữ Khách chủ lực hệ Phong gây Sát Thương Kỹ Năng, 1/2/3 tầng "Phù Tuyết" sẽ khiến mục tiêu nhận thêm \1 Sát Thương Kỹ Năng hệ Phong trong \2 giây.',
        t
    )

    # 2. MainSkill 402901..06 (Dark Evil Eye)
    t = t.replace('cấp 1 điểm Dark Evil Eye', 'nhận 1 tầng "Hắc Tà Nhãn"')
    t = re.sub(
        r'1/2/3 tầng của Dark Evil Eye tăng Sát Thương Kỹ Năng hệ Hỏa mà mục tiêu đã lấy bởi (<color=[^>]+>\{[^\}]+\}</color> / <color=[^>]+>\{[^\}]+\}</color> / <color=[^>]+>\{[^\}]+\}</color>) trong (\d+) giây\.',
        r'1/2/3 tầng "Hắc Tà Nhãn" sẽ khiến mục tiêu nhận thêm \1 Sát Thương Kỹ Năng hệ Hỏa trong \2 giây.',
        t
    )

    # 3. MainSkill 404501..06 (Dark Sakura)
    t = t.replace('gây ra 1 điểm Dark Sakura lên mục tiêu', 'gắn 1 tầng "Hắc Anh" lên mục tiêu')
    t = re.sub(
        r'Dark Sakura: Khi đạt mức cộng dồn tối đa, tăng Sát Thương Kỹ Năng hệ Ám được thực hiện bởi (<color=[^>]+>\{[^\}]+\}</color>)\.',
        r'Hắc Anh: Khi đạt tối đa số tầng cộng dồn, tăng thêm \1 Sát Thương Kỹ Năng hệ Ám gây ra.',
        t
    )

    # 4. MainSkill 405401..06 (Terra Vanguard)
    t = t.replace('hệ Địa Vanguard Lữ Khách', 'Lữ Khách tiên phong hệ Địa')
    t = t.replace('Lữ Khách hệ Địa Vanguard', 'Lữ Khách tiên phong hệ Địa')
    t = t.replace('1 điểm Nạp', '1 tầng Nạp')
    t = t.replace('2 điểm Nạp', '2 tầng Nạp')
    t = re.sub(
        r'tăng hệ Địa Sát Thương Kỹ Năng Taken bởi (<color=[^>]+>\{[^\}]+\}</color>) trong (\{[^\}]+\}) giây\.',
        r'khiến mục tiêu nhận thêm \1 Sát Thương Kỹ Năng hệ Địa trong \2 giây.',
        t
    )

    # 5. SecondarySkill 4030101..05
    t = re.sub(
        r'Tăng Sát Thương Kỹ Năng của Lữ Khách hệ Quang gây ra cho các mục tiêu bị Sốc bởi (<color=[^>]+>\{[^\}]+\}</color>)\.',
        r'Tăng thêm \1 Sát Thương Kỹ Năng của Lữ Khách hệ Quang gây ra cho các mục tiêu bị Sốc.',
        t
    )

    # 6. SecondarySkill 4048101..05 & 4048201..05 (Ode / Thánh ca)
    t = re.sub(
        r'Tăng Sát Thương Kỹ Năng hệ Hỏa được thực hiện bởi (<color=[^>]+>\{[^\}]+\}</color>)\.',
        r'Tăng thêm \1 Sát Thương Kỹ Năng hệ Hỏa gây ra.',
        t
    )
    t = re.sub(
        r'Lữ Khách hệ Hỏa trong đội gây ra Sát Thương Tuyệt Kỹ cho các mục tiêu bị Ode gây ra bởi (<color=[^>]+>\{[^\}]+\}</color>)\.',
        r'Lữ Khách hệ Hỏa trong đội tăng thêm \1 Sát Thương Tuyệt Kỹ gây ra cho các mục tiêu dính Ode.',
        t
    )

    # 7. Potential 511003 (Firenze Shadow Clone)
    t = re.sub(
        r'tăng số lượng ##Shadow Clones#4002# được triệu hồi bởi (<color=[^>]+>&Param1&</color>)\.',
        r'tăng thêm \1 số lượng ##Shadow Clones#4002# được triệu hồi.',
        t
    )

    # 8. Potential 511026
    t = re.sub(
        r'Tăng Sát thương hệ Ám của cây gậy lên các mục tiêu bị ##Dark Burn#2028# gây ra bởi (<color=[^>]+>&Param1&</color>)\.',
        r'Tăng thêm \1 Sát Thương hệ Ám của quyền trượng lên các mục tiêu dính ##Dark Burn#2028#.',
        t
    )

    # 9. Potential 511403
    t = re.sub(
        r'Tăng &Param1& của Chaton lên các mục tiêu gây ra Ấn ký Hắc ám bởi (<color=[^>]+>&Param2&</color>)\.',
        r'Tăng thêm \1 &Param1& của Chaton lên các mục tiêu dính Ấn Ký Hắc Ám.',
        t
    )

    # 10. Potential 511629
    t = re.sub(
        r'Giảm &Param1& của mục tiêu bị Seed Orb gây ra bởi (<color=[^>]+>&Param2&</color>)\.',
        r'Giảm thêm \1 &Param1& của các mục tiêu dính Seed Orb.',
        t
    )

    # 11. Potential 512624
    t = re.sub(
        r'có 20% cơ hội tăng sát thương gây ra bởi (<color=[^>]+>&Param1&</color>)',
        r'có 20% xác suất tăng thêm \1 sát thương gây ra',
        t
    )

    # 12. Potential 512632
    t = re.sub(
        r'HP của Lữ Khách Chủ Lực sẽ được phục hồi bởi (<color=[^>]+>&Param1&</color>)\.',
        r'Lữ Khách chủ lực sẽ được hồi phục \1 HP.',
        t
    )

    # 13. Potential 513023
    t = re.sub(
        r'và Sát Thương Kỹ Năng gây ra bởi (<color=[^>]+>&Param2&</color>)\.',
        r'và tăng thêm \1 Sát Thương Kỹ Năng gây ra.',
        t
    )

    # 14. Potential 514443
    t = re.sub(
        r'Tăng Sát Thương Tuyệt Kỹ của Chitose lên các mục tiêu gây ra (##Chill#1027# / ##Frozen#1002#) bởi (<color=[^>]+>&Param2&</color>)\.',
        r'Tăng thêm \2 Sát Thương Tuyệt Kỹ của Chitose lên các mục tiêu dính \1.',
        t
    )

    # 15. Potential 514509
    t = re.sub(
        r'Tăng &Param1& gây ra bởi Dạ Đàm \(Kỹ Năng Chính\) đối với các mục tiêu bị ##Dark Shackles#2020# gây ra bởi (<color=[^>]+>&Param2&</color>)\.',
        r'Tăng thêm \1 &Param1& do Dạ Đàm (Kỹ Năng Chính) gây ra cho các mục tiêu dính ##Dark Shackles#2020#.',
        t
    )

    # 16. Potential 514524
    t = re.sub(
        r'Tăng &Param2& gây ra bởi Weeping Sky lên các mục tiêu bị (##Umbra Mark#1019# hoặc ##Dark Shackles#2020#) gây ra bởi (<color=[^>]+>&Param3&</color>)\.',
        r'Tăng thêm \2 &Param2& do Weeping Sky gây ra cho các mục tiêu dính \1.',
        t
    )

    # 17. Potential 514542
    t = re.sub(
        r'Tăng &Param1& do Không Hoa \(Tuyệt Kỹ\) gây ra cho các mục tiêu bị ##Dark Shackles#2020# gây ra bởi (<color=[^>]+>&Param2&</color>)\.',
        r'Tăng thêm \1 &Param1& do Không Hoa (Tuyệt Kỹ) gây ra cho các mục tiêu dính ##Dark Shackles#2020#.',
        t
    )

    # 18. Potential 514732 & 514741
    t = re.sub(
        r'Tăng &Param1& của Ma Âm Vỗ Cánh \(Kỹ Năng Viện Trợ\) đối với các mục tiêu bị ##Dark Burn#2028# gây ra bởi (<color=[^>]+>&Param2&</color>)\.',
        r'Tăng thêm \1 &Param1& của Ma Âm Vỗ Cánh (Kỹ Năng Viện Trợ) lên các mục tiêu dính ##Dark Burn#2028#.',
        t
    )
    t = re.sub(
        r'Tăng &Param1& của Thiên Thần Sa Ngã Nhịp Điệu \(Tuyệt Kỹ\) lên các mục tiêu bị ##Dark Burn#2028# gây ra bởi (<color=[^>]+>&Param2&</color>)\.',
        r'Tăng thêm \1 &Param1& của Thiên Thần Sa Ngã Nhịp Điệu (Tuyệt Kỹ) lên các mục tiêu dính ##Dark Burn#2028#.',
        t
    )

    # 19. Potential 515701
    t = re.sub(
        r'Tăng &Param2& của Karin đối với các mục tiêu bị ##Dark Burn#2028# gây ra bởi (<color=[^>]+>&Param3&</color>)\.',
        r'Tăng thêm \1 &Param2& của Karin lên các mục tiêu dính ##Dark Burn#2028#.',
        t
    )

    # 20. Potential 515822
    t = re.sub(
        r'sẽ tăng Sát Thương Kỹ Năng của mục tiêu được thực hiện bởi (<color=[^>]+>&Param2&</color>) cho (<color=[^>]+>&Param3&</color>) s, lên đến (<color=[^>]+>&Param4&</color>) tầng\.',
        r'khiến mục tiêu nhận thêm \1 Sát Thương Kỹ Năng trong \2 giây, tối đa cộng dồn \3 tầng.',
        t
    )

    # 21. Talent cases
    t = re.sub(
        r'Tăng Sát thương Kỹ năng của Kasimira đối với các mục tiêu bị ##Ignis Mark: Sacred Flame#2013# gây ra bởi (<color=[^>]+>&Param1&</color>)\.',
        r'Tăng thêm \1 Sát Thương Kỹ Năng của Kasimira lên các mục tiêu dính ##Ignis Mark: Sacred Flame#2013#.',
        t
    )
    t = re.sub(
        r'Tăng Sát thương Kỹ năng của Iris đối với các mục tiêu gây ra ##Aqua Mark: Torrent#2008# bởi (<color=[^>]+>&Param1&</color>)\.',
        r'Tăng thêm \1 Sát Thương Kỹ Năng của Iris lên các mục tiêu dính ##Aqua Mark: Torrent#2008#.',
        t
    )
    t = re.sub(
        r'Tăng Sát Thương hệ Địa của Ridge gây ra cho các mục tiêu bị ##Terra Mark: Earth Vein#2029# gây ra bởi (<color=[^>]+>&Param1&</color>)\.',
        r'Tăng thêm \1 Sát Thương hệ Địa của Ridge gây ra cho các mục tiêu dính ##Terra Mark: Earth Vein#2029#.',
        t
    )
    t = re.sub(
        r'Tăng Sát thương hệ Hỏa của tất cả các đơn vị đồng minh gây ra cho các mục tiêu bị ##Ignis Mark#1016# gây ra bởi (<color=[^>]+>&Param1&</color>)\.',
        r'Tăng thêm \1 Sát Thương hệ Hỏa của toàn bộ đồng minh gây ra cho các mục tiêu dính ##Ignis Mark#1016#.',
        t
    )

    return t

def main():
    root = Path(__file__).parent.parent
    entries_dir = root / 'work' / 'research' / 'data_decrypted' / 'entries'

    skill_tables = [
        '00591_0x57e760255c1d3b2d.bin',
        '00635_0x31a8814a91313129.bin',
        '00624_0x02ce11eca01b5fc8.bin',
        '00680_0x3f0bd5f8db2389b6.bin',
        '00560_0x788d8a3db60dd08a.bin'
    ]

    total_changed = 0
    for st in skill_tables:
        f = entries_dir / st
        if not f.exists(): continue
        d = json.load(open(f, encoding='utf-8'))
        changed = 0
        for k, v in d.items():
            if not isinstance(v, str): continue
            new_v = polish_pass2(v)
            if new_v != v:
                d[k] = new_v
                changed += 1
        if changed > 0:
            with open(f, 'w', encoding='utf-8') as fp:
                json.dump(d, fp, ensure_ascii=False, indent=2)
            print(f"✓ {st}: Sửa thành công {changed} chuỗi 'bởi <color>'")
            total_changed += changed

    print(f"\n===> TỔNG CỘNG ĐÃ SỬA: {total_changed} chuỗi 'bởi <color>'")

if __name__ == '__main__':
    main()
