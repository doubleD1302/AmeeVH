#!/usr/bin/env python3
"""Polisher for Item table (00577_0xe60634348b826f41.bin)."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from phase2a_token_manager import extract_tokens, shield_tokens, unshield_tokens, validate_token_preservation

ITEM_SPECIFIC_OVERRIDES = {
    # Key exact replacements
    "Item.1.2": "Đơn vị tiền tệ cơ bản, dùng cho nhiều tính năng trong game.",
    "Item.1.3": "Được phát hành bởi Tài Chính Biển Sâu, đơn vị tiền tệ này lưu hành khắp Đại Lục Nova... nhưng chỉ trong các đô thị.\x0bNếu đơn độc nơi Vùng Hoang Dã, mọi Dorra mang theo chẳng khác nào mớ giấy lộn.",
    "Item.1000.3": "Chìa khóa tâm hồn rực rỡ, tràn ngập sức mạnh cảm xúc.\x0bKhai mở những thiên phú còn say ngủ nơi sâu thẳm tâm hồn...",
    "Item.1001.3": "Chìa khóa tâm hồn rực rỡ, tràn ngập sức mạnh cảm xúc.\x0bThắp sáng những thiên phú tiềm ẩn nơi sâu thẳm tâm hồn...",
    "Item.103.3": "Lắng tai nghe kỹ, tựa như có thể nghe thấy tiếng mèo kêu khe khẽ vẳng lại bên tai.",
    "Item.1030.3": "Lắng tai nghe kỹ, tựa như có thể nghe thấy tiếng mèo kêu khe khẽ vẳng lại bên tai.",
    "Item.11.2": "Tiền tệ dùng để mua sắm bên trong Cự Tháp.",
    "Item.11.3": "Đồng xu lấp lánh ánh sao, lưu hành độc quyền bên trong Cự Tháp.\x0bHãy tiêu xài khi còn có thể, bởi bạn chẳng thể mang nó ra ngoài đâu.",
    "Item.20.2": "Thể lực dùng để tham gia các chế độ chơi.",
    "Item.20997.3": "Nguyên liệu cơ bản ngẫu nhiên dùng để thăng giai Lữ Khách.",
    "Item.28.2": "Chứng nhận dùng để mở khóa Đấu Trường Thử Luyện.",
    "Item.29.1": "Vé Thang Trời Cự Tháp",
    "Item.29.2": "Vé dùng để kích hoạt Chuyến Tốc Hành Cự Tháp.",
    "Item.29.3": "Nắm giữ \"Chìa Khóa Thang Trời Cự Tháp\", bạn có thể phóng thẳng lên đỉnh tháp đoạt lấy \"Đĩa Nhạc\" tối thượng... nhưng đời nào có chuyện dễ dàng như thế.\x0bMọi gian nan thử thách vẫn còn nguyên đó, món đồ này chỉ giúp bạn đỡ phần nào công sức nhọc nhằn mà thôi.",
    "Item.30.1": "Vé Thang Trời Cự Tháp",
    "Item.30.2": "Vé dùng để kích hoạt Chuyến Tốc Hành Cự Tháp.",
    "Item.30.3": "Nắm giữ \"Chìa Khóa Thang Trời Cự Tháp\", bạn có thể phóng thẳng lên đỉnh tháp đoạt lấy \"Đĩa Nhạc\" tối thượng... nhưng đời nào có chuyện dễ dàng như thế.\x0bMọi gian nan thử thách vẫn còn nguyên đó, món đồ này chỉ giúp bạn đỡ phần nào công sức nhọc nhằn mà thôi.",
    "Item.32003.2": "Nguyên liệu cao cấp dùng để nâng cấp kỹ năng Lữ Khách.",
    "Item.32013.2": "Nguyên liệu cao cấp dùng để nâng cấp kỹ năng Lữ Khách.",
    "Item.32023.2": "Nguyên liệu cao cấp dùng để nâng cấp kỹ năng Lữ Khách.",
    "Item.33001.3": "Mỗi khi thám hiểm Cự Tháp, Trứng Cầu Nguyện sẽ xuất hiện cùng Hộp Cầu Nguyện, dùng để ước nguyện các Cổ Vật thông thường.\x0bBên cạnh việc bán Cổ Vật cho cư dân thành phố kiếm tiền, các Lữ Khách đôi khi cũng giữ lại vài món đồ hữu ích cho riêng mình.",
    "Item.34000.2": "Mở khóa ký ức tương tác với Lữ Khách này; có thể cài đặt làm màn hình chính.",
    "Item.502.2": "Vé dùng để chiêu mộ trong Kỳ Chiêu Mộ Lữ Khách Giới Hạn.",
    "Item.503.2": "Vé dùng để chiêu mộ trong Kỳ Chiêu Mộ Lữ Khách Thường Trực.",
    "Item.510.2": "Vé độc quyền dùng để chiêu mộ trong sự kiện \"Đêm Thánh Tặng Quà\"!",
    "Item.511.2": "Vé độc quyền dùng để Chiêu Mộ ×10 trong sự kiện \"Đêm Thánh Tặng Quà\"!",
    "Item.512.2": "Tín vật dùng để chiêu mộ trong sự kiện \"Anh Đào Tàn, Nguyệt Tối Tịch\".",
    "Item.513.2": "Vé độc quyền dùng để chiêu mộ trong sự kiện \"Khởi Động Trước Khi Nhập Cuộc\"!",
    "Item.602.2": "Vé dùng để chiêu mộ trong Kỳ Chiêu Mộ Đĩa Nhạc Giới Hạn.",
    "Item.603.2": "Vé dùng để chiêu mộ trong Kỳ Chiêu Mộ Đĩa Nhạc Thường Trực.",
    "Item.73101.2": "Tiền tệ nhận được khi tham gia sự kiện: Mạo Hiểm Táo Bạo! Tàu Ma Vực Sâu. Dùng để đổi vật phẩm tại Cửa Hàng Sự Kiện.",
    "Item.73112.3": "Loại đạn đặc biệt chứa năng lượng bóng tối, cực kỳ quý giá và chỉ bắn được từ súng bắn tỉa của Chaton. Hãy trân trọng từng phát bắn.",
    "Item.116016.1": "Cự Tháp Nơi Xa",
    "Item.116016.2": "Mở khóa Danh hiệu: Cự Tháp Nơi Xa.",
    "Item.198025.1": "Bản Ghi Đội Hệ Phong",
    "Item.198025.2": "Nhận ngay Bản Ghi Cự Tháp hệ Phong cho tân thủ!",
    "Item.198026.1": "Bản Ghi Đội Hệ Hỏa",
    "Item.198026.2": "Nhận ngay Bản Ghi Cự Tháp hệ Hỏa dành riêng cho tân thủ!",
    "Item.199007.1": "Thưởng theo cấp:\nTúi Chọn Đĩa Nhạc (Trợ Cấp)",
    "Item.199007.2": "Thưởng theo cấp:\nTúi Chọn Đĩa Nhạc (Trợ Cấp)",
    "Item.199007.3": "Túi Chọn Đĩa Nhạc (Trợ Cấp)",
    "Item.213012.3": "Lấy mặt đất làm sân khấu, mượn trời sao làm phông nền,\nVũ trụ hãy lắng nghe—đây là khoảnh khắc chúng ta tỏa sáng!",
    "Item.214043.3": "Dưới tầng đất chôn vùi bao âm mưu toan tính,\nBao ánh mắt dò xét đan xen.\nCó mầm sống đang vùng vẫy vươn lên khỏi lòng đất.",
    "Item.110.3": "Đứng nơi đỉnh cao vạn người dõi mắt, nàng ngắm nhìn vạn vật bên dưới tựa bậc đế vương.\x0bThế nhưng trên tay, ngón tay nàng lại dịu dàng vuốt ve chiếc ghế cũ kỹ thân thương nhất.",
    "Item.1100.3": "Đứng nơi đỉnh cao vạn người dõi mắt, nàng ngắm nhìn vạn vật bên dưới tựa bậc đế vương.\x0bThế nhưng trên tay, ngón tay nàng lại dịu dàng vuốt ve chiếc ghế cũ kỹ thân thương nhất.",
}

ITEM_REGEX_RULES = [
    (re.compile(r'\bngười đi bộ\b', re.I), 'Lữ Khách'),
    (re.compile(r'\bngười đi phượt\b', re.I), 'Lữ Khách'),
    (re.compile(r'\bngười phượt\b', re.I), 'Lữ Khách'),
    (re.compile(r'\btảng đá nguyên khối\b', re.I), 'Cự Tháp'),
    (re.compile(r'\bđá nguyên khối\b', re.I), 'Cự Tháp'),
    (re.compile(r'\bnguyên khối\b', re.I), 'Cự Tháp'),
    (re.compile(r'\bĐĩa than\b', re.I), 'Đĩa Nhạc'),
    (re.compile(r'\bđĩa than\b', re.I), 'đĩa nhạc'),
    (re.compile(r'\bCẩm nang Lữ khách\b'), 'Cẩm Nang Lữ Khách'),
    (re.compile(r'\bDeepsea Finance\b'), 'Tài Chính Biển Sâu'),
    (re.compile(r'\bMột loại tiền tệ cơ bản có thể được sử dụng trong nhiều tính năng khác nhau\b'), 'Đơn vị tiền tệ cơ bản, dùng cho nhiều tính năng trong game'),
    (re.compile(r'\bcó thể được sử dụng để\b'), 'dùng để'),
    (re.compile(r'\bcó thể được sử dụng trong\b'), 'dùng cho'),
    (re.compile(r'\bđược sử dụng để\b'), 'dùng để'),
    (re.compile(r'\bđược sử dụng cho\b'), 'dùng cho'),
    (re.compile(r'\bđược sử dụng trong\b'), 'dùng cho'),
    (re.compile(r'\bchỉ có thể được bắn từ\b'), 'chỉ có thể bắn từ'),
    (re.compile(r'\bcó thể được đặt làm\b'), 'có thể cài đặt làm'),
    (re.compile(r'\bcó thể được mở\b'), 'có thể mở'),
    (re.compile(r'\bElite Startup Grant\b'), 'Trợ Cấp Khởi Đầu Tinh Anh'),
    (re.compile(r'\bRoyal Startup Grant\b'), 'Trợ Cấp Khởi Đầu Hoàng Gia'),
]

def polish_item_entry(key: str, vi_text: str, en_orig: str) -> str:
    if key in ITEM_SPECIFIC_OVERRIDES:
        return ITEM_SPECIFIC_OVERRIDES[key]

    sh, toks = shield_tokens(vi_text)

    for pattern, repl in ITEM_REGEX_RULES:
        sh = pattern.sub(repl, sh)

    sh = re.sub(r'[ \t]{2,}', ' ', sh)
    res = unshield_tokens(sh, toks)

    # Condition: restore \n if original had \n but vi_text had lost it
    if '\n' in en_orig and '\n' not in res:
        res = re.sub(r':\s*', ':\n', res, count=1)

    return res

def polish_item_table(items):
    polished = []
    changes = 0
    token_errors = 0
    for it in items:
        k = it['key']
        en = it['en']
        orig_vi = it['vi_current']
        new_vi = polish_item_entry(k, orig_vi, en)

        valid, ot, vt = validate_token_preservation(en, new_vi)
        if not valid:
            token_errors += 1
            print(f"Token error in Item [{k}]:")
            print("  EN toks:", ot)
            print("  VI toks:", vt)
            # fallback to orig_vi if invalid
            new_vi = orig_vi

        if new_vi != orig_vi:
            changes += 1

        polished.append({
            'key': k,
            'en': en,
            'vi': new_vi
        })
    print(f"Item table: {changes} items polished, {token_errors} token errors.")
    return polished
