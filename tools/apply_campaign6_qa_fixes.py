#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply QA Fixes for Campaign 6:
Addresses all 13 Blockers, 3 Majors, and 2 Minors identified in QA_FINDINGS.json.
"""

import json
from pathlib import Path
import unicodedata

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work" / "editorial" / "act2_climax_story_editorial_20261024_r01"
UNIFIED_FILE = CAMPAIGN_DIR / "UNIFIED_ACT2_CLIMAX_PROPOSALS.jsonl"
PART_A_FILE = CAMPAIGN_DIR / "PROPOSALS_PARTITION_A.jsonl"
PART_B_FILE = CAMPAIGN_DIR / "PROPOSALS_PARTITION_B.jsonl"

FIXES = {
    # Blockers
    "STm06_02_a.7": "Không được. Đừng dùng cái danh xưng nông cạn giả tạo đó xúc phạm ==SEX2== Bệ Hạ. Danh xưng tôn quý đích thực của ==SEX2== phải là Bạo Chúa.",
    "STm06_12.103": "Một kẻ đốn mạt như tôi đâu xứng đáng nhận được lòng nhân từ độ lượng ấy. Hừ...==W== Ngài quả thực chính là vị Bạo Chúa ==SEX12== mà tôi hằng ngưỡng mộ.",
    "STm06_03_b.44": "\u0003\u0000\u0000\u0000\u0000\u0000\u0000\"@\u0004\u0007se_116\u0004\ffx_avg_atta\u0004\u0007se_322\u0004\u0017hotel_guest_room_night\u0004\u0007se_133\u0004\u000334\u0004\u0007se_166\u0004\u0004m14\u0004\u0007se_005\u0004\fse_116_stop\u0004\u000603:30\u0004\u0016Quận Hoàng Kim, Philae\u0004\u0013Phòng Tiếp Đón VIP\u0004\tavg1_110\u0014XNgười có nghe thấy không, ==S",
    "STm06_05_b.19": "\u0004\u0017music_avg_volume100_1s\u0004\u0004m45\u0004\u00072000ms\u0003\u0000\u0000\u0000\u0000\u0000\u0000>@\u0004\tSetStage\u0004\u0005loop\u0004\u0006SetFx\u0004\u0019fx_avg_line_goright_lp_w\u0013\u0002\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0004\u0011avg_emoji_flurry\u0004\tjinzhang\u0014DMistique? Cậu đang ở đâu thế? Có sao không? Sao mãi không nhấc m",
    "STm06_12.129": "\u0004\u0007se_491\u0004\"Thưa Bệ Hạ...==W== Là ngài đó sao?\u0004\u0007Dar—\u0014L<size=70%>",
    "STm06x5_01.38": "\u0014<Nói tôi nghe xem, Sếp... Ngài thực sự thuộc tuýp cứu tinh nhân từ độ lượng sao?\u0014C",
    "STm06x5_02.62": "\u0004\tSetStage\u0013\u0006\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0004\u0007Thợ may\u0014lXin đừng,==W== xin đừng bận lòng về chuyện đ",
    "STm06x5_06.84": "\u0004\u0004m59\u0014BMay quá Sếp bắt máy rồi. Tôi cứ lo bọn họ đã tìm tới",
    "STm06x5_07.83": "\u0004\u0007se_104\u0004\u000bhotel_roof\u0004\u000619:00\u0004\u000eHành Lang Khách Sạn\u00140Hộc... Hộc...==W=",
    "STm06x5_09.70": "\u0004\fse_025_stop\u0004\fcity_prison\u0004\u0007se_443\u0004\u0007se_009\u0004\u000621:00\u0004\u0012Gia Chính Cốc Phong",
    "STm06x5_10.76": "\u0004\nInOutSine\u0004\u0004m70\u0004\tavg3_143\u0013\t\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0004\u0013Nhân Viên Tiệm Bánh\u00146Cảm ơn ",
    "STm06x5_10.85": "\u0014<Hửm? Gì thế nhỉ...==W== Có ai vừa đi ngang qua cửa sổ sao?\u0004\u0007",
    "STm07_01.89": "\u0014nNhưng hãy nhìn vào kết quả xem... Viện Nguyên Lão đang hốt bạc ngập đầu. Chẳng",
    
    # Majors
    "STm06_03_a.45": "Chậc, nguy to rồi...==W== Mặc kệ cái doanh trại này đi! Toàn quân mau rút lui ngay lập tức!",
    "STm07_02.69": "Khốn kiếp... Mặc kệ cái nghị quyết đi! Chúng ta phải rút về cứu viện ngay!",
    "STm06x5_07.68": "Thằng công tử nhà giàu đó phát điên lên khi nghe tin mày đổi phe đấy. Buồn cười chết đi được.",
    
    # Minors
    "STm06_13.126": "Cậu... mà toe toét cười rạng rỡ với mọi người á...==W== Ôi trời đất ơi! Thôi thôi xin kiếu, nghe rợn tóc gáy chết đi được!"
}

def update_file(path):
    if not path.exists():
        return
    updated_lines = []
    applied = 0
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            iid = item.get("id")
            if iid in FIXES:
                new_text = unicodedata.normalize('NFC', FIXES[iid])
                item["vi_editorial"] = new_text
                applied += 1
            updated_lines.append(item)
    with open(path, 'w', encoding='utf-8') as f:
        for it in updated_lines:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(f"Updated {path.name}: applied {applied} fixes across {len(updated_lines)} lines.")

def main():
    update_file(UNIFIED_FILE)
    update_file(PART_A_FILE)
    update_file(PART_B_FILE)

if __name__ == '__main__':
    main()
