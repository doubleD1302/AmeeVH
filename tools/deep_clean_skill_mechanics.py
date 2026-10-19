#!/usr/bin/env python3
"""Deep clean all clunky skill mechanics across all skill and card tables."""

import json
import re
from pathlib import Path

def polish_mechanics_text(text: str) -> str:
    if not isinstance(text, str):
        return text
    
    t = text

    # 1. Tên đĩa nhạc chuẩn hóa
    t = t.replace("Truyện Cổ Tích Đầu Giường", "Chuyện Kể Đêm Khuya")

    # 2. Chuẩn hóa điểm -> tầng / cộng dồn
    t = re.sub(r'cấp (\d+) điểm "([^"]+)"', r'cấp \1 tầng "\2"', t)
    t = re.sub(r'nhận được (\d+) điểm "([^"]+)"', r'nhận \1 tầng "\2"', t)
    t = re.sub(r'nhận (\d+) điểm "([^"]+)"', r'nhận \1 tầng "\2"', t)
    t = re.sub(r'có (\d+) điểm "([^"]+)"', r'có \1 tầng "\2"', t)
    t = re.sub(r'mọi điểm "([^"]+)"', r'mỗi tầng "\1"', t)
    t = re.sub(r'tối đa (\d+) điểm', r'tối đa cộng dồn \1 tầng', t)
    t = re.sub(r'tối đa (\d+) lần cộng dồn', r'tối đa cộng dồn \1 tầng', t)

    # 3. Chuẩn hóa Lữ Khách với -> Lữ Khách sở hữu
    t = re.sub(r'([Kk]hi (?:một )?Lữ Khách[^"]*) với "([^"]+)"', r'\1 sở hữu "\2"', t)
    t = re.sub(r'([Vv]ới "Quang Chi Dực")', r'sở hữu "Quang Chi Dực"', t)

    # 4. Sửa non-Auto Attack DMG & chance
    t = t.replace("gây sát thương Tấn Công không tự động", "gây sát thương ngoài Đòn Đánh Thường")
    t = re.sub(r'sẽ có cơ hội (\{[^\}]+\}|\d+%) gây ra', r'có \1 xác suất gây ra', t)
    t = re.sub(r'có cơ hội (\{[^\}]+\}|\d+%) gây ra', r'có \1 xác suất gây ra', t)

    # 5. Sửa mẫu: tăng sát thương mà hệ X nhận được bởi Y trong Z giây
    t = re.sub(
        r'tăng sát thương mà hệ (\w+) nhận được bởi (<color=[^>]+>\{[^\}]+\}</color>|\{[^\}]+\}) trong (\{[^\}]+\}) giây',
        r'khiến mục tiêu nhận thêm \2 Sát Thương hệ \1 trong \3 giây',
        t
    )

    # 6. Sửa mẫu giảm sát thương phải gánh chịu
    t = re.sub(
        r'Giảm sát thương mà Lữ Khách chủ lực hệ (\w+) phải gánh chịu từ các mục tiêu bị "([^"]+)" bởi (<color=[^>]+>\{[^\}]+\}</color>|\{[^\}]+\})',
        r'Đồng thời giảm \3 sát thương Lữ Khách chủ lực hệ \1 phải chịu từ mục tiêu dính "\2"',
        t
    )
    t = re.sub(
        r'Giảm sát thương mà Lữ Khách chủ lực hệ (\w+) phải gánh chịu đi (<color=[^>]+>\{[^\}]+\}</color>|\{[^\}]+\})',
        r'Giảm \2 sát thương Lữ Khách chủ lực hệ \1 phải chịu',
        t
    )

    # 7. Sửa mẫu Kính Sợ (Reverence) trong MainSkill
    t = re.sub(
        r'tăng Sát Thương hệ Ám Tùy tùng sát thương nhận bởi (<color=[^>]+>\{[^\}]+\}</color>|\{[^\}]+\}) trong (\{[^\}]+\}) giây',
        r'khiến mục tiêu nhận thêm \1 Sát Thương Tùy Tùng hệ Ám trong \2 giây',
        t
    )

    # 8. Sửa mẫu Tinh Vọng (MainSkill 405901..06)
    t = re.sub(
        r'Khi một Lữ Khách có (\d+) tầng "Tinh Vọng" trở lên gây sát thương, gây sát thương sau cho mục tiêu: tăng Sát Thương Kỹ Năng hệ Phong gánh chịu thêm (<color=[^>]+>\{[^\}]+\}</color>) trong (\{[^\}]+\}) giây\.',
        r'Khi một Lữ Khách có từ \1 tầng "Tinh Vọng" trở lên gây sát thương, sẽ khiến mục tiêu nhận thêm \2 Sát Thương Kỹ Năng hệ Phong trong \3 giây.',
        t
    )
    t = re.sub(
        r'Khi một Lữ Khách có 10 tầng "Tinh Vọng" gây sát thương, đồng thời gây ra những điều sau đây cho mục tiêu: tăng Sát Thương Đòn Đánh Thường hệ Phong gánh chịu thêm (<color=[^>]+>\{[^\}]+\}</color>) trong (\{[^\}]+\}) giây\.',
        r'Khi một Lữ Khách có 10 tầng "Tinh Vọng" gây sát thương, sẽ đồng thời khiến mục tiêu nhận thêm \1 Sát Thương Đòn Đánh Thường hệ Phong trong \2 giây.',
        t
    )

    # 9. Sửa mẫu gánh chịu của mục tiêu thêm X trong Y giây
    t = re.sub(
        r'tăng Sát Thương hệ (\w+) gánh chịu của mục tiêu thêm (<color=[^>]+>\{[^\}]+\}</color>|\{[^\}]+\}) trong (\{[^\}]+\}) giây',
        r'khiến mục tiêu nhận thêm \2 Sát Thương hệ \1 trong \3 giây',
        t
    )
    t = re.sub(
        r'tăng Sát Thương Kỹ Năng gánh chịu của mục tiêu thêm (<color=[^>]+>\{[^\}]+\}</color>|\{[^\}]+\}) trong (\{[^\}]+\}) giây',
        r'khiến mục tiêu nhận thêm \1 Sát Thương Kỹ Năng trong \2 giây',
        t
    )

    # 10. Sửa mẫu tăng Sát thương mà mục tiêu phải gánh chịu thêm
    t = re.sub(
        r'tăng sát thương mà mục tiêu phải gánh chịu thêm (<color=[^>]+>\{[^\}]+\}</color>|\{[^\}]+\}%?) trong (\{[^\}]+\}) giây trong trận này, không thể cộng dồn',
        r'khiến mục tiêu nhận thêm \1 sát thương trong \2 giây ở trận hiện tại, không cộng dồn',
        t
    )
    t = re.sub(
        r'tăng sát thương mà mục tiêu phải gánh chịu thêm (<color=[^>]+>\{[^\}]+\}</color>|\{[^\}]+\}%?) trong (\{[^\}]+\}) giây trong trận này',
        r'khiến mục tiêu nhận thêm \1 sát thương trong \2 giây ở trận hiện tại',
        t
    )
    t = re.sub(
        r'tăng Sát Thương hệ (\w+) mà mục tiêu phải gánh chịu thêm (<color=[^>]+>&Param1&</color>) trong (&Param2&) giây',
        r'khiến mục tiêu nhận thêm \2 Sát Thương hệ \1 trong \3 giây',
        t
    )

    # 11. Các câu tóm tắt tiềm năng (Potential)
    t = re.sub(
        r'sẽ tăng sát thương kỹ năng mà các mục tiêu ở gần phải gánh chịu',
        r'khiến các mục tiêu xung quanh phải chịu thêm Sát Thương Kỹ Năng',
        t
    )
    t = re.sub(
        r'tăng Sát thương hệ Quang mà mục tiêu phải gánh chịu',
        r'khiến mục tiêu nhận thêm Sát Thương hệ Quang',
        t
    )
    t = re.sub(
        r'sẽ tăng Sát thương hệ Thủy mà mục tiêu phải gánh chịu',
        r'khiến mục tiêu nhận thêm Sát Thương hệ Thủy',
        t
    )
    t = re.sub(
        r'sẽ tăng Sát Thương Kỹ Năng mà mục tiêu phải gánh chịu',
        r'khiến mục tiêu nhận thêm Sát Thương Kỹ Năng',
        t
    )
    t = re.sub(
        r'tăng Sát thương hệ Quang mà chúng phải gánh chịu',
        r'khiến chúng nhận thêm Sát Thương hệ Quang',
        t
    )
    t = re.sub(
        r'tăng Sát thương hệ Hỏa mà mục tiêu phải gánh chịu',
        r'khiến mục tiêu nhận thêm Sát Thương hệ Hỏa',
        t
    )
    t = re.sub(
        r'tăng sát thương mà các mục tiêu gần đó phải gánh chịu',
        r'khiến các mục tiêu gần đó phải nhận thêm sát thương',
        t
    )
    t = t.replace("gây sát thương Aqua Sát Thương Kỹ Năng và tăng Sát thương gánh chịu của tất cả các Nguyên tố của mục tiêu",
                  "gây Sát Thương Kỹ Năng hệ Thủy và khiến mục tiêu nhận thêm Sát Thương từ mọi Nguyên Tố")
    t = t.replace("Mục tiêu bình thường sẽ bị ##Fear#4501# gây ra trong 2 giây.",
                  "Mục tiêu thông thường sẽ chịu hiệu ứng ##Fear#4501# trong 2 giây.")

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

    total_polished = 0
    for st in skill_tables:
        fpath = entries_dir / st
        if not fpath.exists(): continue
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        file_changed = 0
        for k, text in data.items():
            if not isinstance(text, str): continue
            new_text = polish_mechanics_text(text)
            if new_text != text:
                data[k] = new_text
                file_changed += 1

        if file_changed > 0:
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✓ {st}: Trau chuốt thành công {file_changed} chuỗi cơ chế kỹ năng")
            total_polished += file_changed

    print(f"\n===> TỔNG CỘNG: Đã nâng cấp {total_polished} chuỗi cơ chế kỹ năng chuẩn ngữ pháp mượt mà!")

if __name__ == '__main__':
    main()
