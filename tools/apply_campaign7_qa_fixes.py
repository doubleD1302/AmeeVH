#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply QA Fixes for Campaign 7:
Addresses all 56 lines across the 7 scenes identified in QA_REVIEW_REPORT.md.
"""

import json
from pathlib import Path
import unicodedata

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work" / "editorial" / "phone_messages_phase2_20261024_r01"
UNIFIED_FILE = CAMPAIGN_DIR / "UNIFIED_PM_PHASE2_PROPOSALS.jsonl"
PART_A_FILE = CAMPAIGN_DIR / "PROPOSALS_PARTITION_A.jsonl"
PART_B_FILE = CAMPAIGN_DIR / "PROPOSALS_PARTITION_B.jsonl"

FIXES = {
    # 4.1. PM12302 (Ann)
    "PM12302.27": "Làm...",
    "PM12302.28": "sao...",
    "PM12302.29": "chụp hình được ạ?",
    "PM12302.30": "Hửm? Nhóc muốn học cách chụp ảnh hả?",
    "PM12302.31": "Dạ đúng rồi ạ!",
    "PM12302.32": "Nhóc tìm trên màn hình điện thoại cái biểu tượng trông giống như Máy Thu Ảnh xem.",
    "PM12302.33": "Bấm vào đó là có thể bấm máy tanh tách rồi.",
    "PM12302.34": "Xong rồi làm gì nữa ạ?",
    "PM12302.35": "Sau đó thì nhóc phải tự mình mày mò thôi.",
    "PM12302.36": "Cứ thử chụp mọi người với cảnh vật xung quanh trước xem sao nhé.",
    "PM12302.37": "Cháu đi tập chụp đây ạ!",
    "PM12302.38": "Chú nóng lòng muốn xem ảnh nhóc chụp lắm đấy!",

    # 4.2. PM12501 (Freesia)
    "PM12501.141": "Lâu rồi mới lại nghe thấy từ đó. Có chút hoài niệm thật đấy.",
    "PM12501.143": "Có một câu này tôi muốn hỏi cậu, Sếp à.",
    "PM12501.144": "Cậu thấy tôi là một người như thế nào?",

    # 4.3. PM12701 (Teresa)
    "PM12701.211": "Nhưng mà chiếc điện thoại này là tôi được bố cho,",
    "PM12701.212": "máy đời cũ quá nên chẳng có máy ảnh đâu.",
    "PM12701.213": "Thật á~?",
    "PM12701.214": "Thật mà!",

    # 4.4. PM12702 (Teresa)
    "PM12702.12": "Hôm nay cả Donna lẫn Freesia đều về muộn,",
    "PM12702.13": "nên tôi đành ngồi ôm bụng đói ở đây nè.",
    "PM12702.15": "Thế nên tôi mới nghĩ, hay là mình cũng nên học nấu ăn một chút nhỉ...",
    "PM12702.16": "Ừ, ít nhất thì cũng tự xoay xở được lúc khẩn cấp.",
    "PM12702.17": "Trước khi gặp hai người họ thì Teresa giải quyết ba bữa một ngày kiểu gì thế?",
    "PM12702.18": "Để tôi nhớ xem nào...",
    "PM12702.19": "Hồi còn ở nhà thì mẹ chuẩn bị cơm hộp cho tôi.",
    "PM12702.20": "Sau khi ra ngoài sống tự lập thì tôi cứ hái trái cây dại trong rừng ăn qua ngày thôi.",
    "PM12702.22": "Cô sống chẳng khác nào người rừng thứ thiệt luôn đấy!",
    "PM12702.23": "Thế cô chưa từng ăn nhầm thứ gì bậy bạ bao giờ à?",
    "PM12702.24": "Chưa bao giờ luôn! Tôi học được cách nhận biết cây cỏ dại từ sớm lắm rồi nha~",

    # 4.5. & 4.6. PM14701 (Caramel)
    "PM14701.67": "Nhà sản xuất là... kiểu như là... ừm... người mà...",
    "PM14701.114": "Nội dung sinh nhật tạm thời bị khóa",

    # 4.7. PM15901 (Springseek Coronis)
    "PM15901.29": "Nói cho cậu hay, những kẻ hay nói dối sẽ bị ác ma bắt đi làm vật thí nghiệm đấy nhé.",

    # 4.8. PM15902 (Springseek Coronis)
    "PM15902.12": "C-Cậu lại toan tính âm mưu gì nữa đây?",
    "PM15902.13": "Ý cậu toan tính âm mưu là sao chứ?",
    "PM15902.14": "Cậu định dụ tôi qua đó, trói tôi lại rồi làm thí nghiệm mờ ám gì đúng không?",
    "PM15902.15": "Đương nhiên là không rồi. Chúng ta quen biết nhau bao lâu rồi cơ chứ?",
    "PM15902.16": "Trông tôi giống người sẽ làm ra mấy chuyện như thế lắm à?",
    "PM15902.17": "Ờ... Giống chứ?",
    "PM15902.18": "Haizz... Lúc nào cậu cũng hiểu lầm ý tốt của tôi hết. Tổn thương ghê gớm...",
    "PM15902.19": "Quán trọ vừa thêm món mới vào thực đơn, tôi chỉ muốn rủ cậu cùng nếm thử thôi mà, thế thôi đấy.",
    "PM15902.20": "Ra là vậy...",
    "PM15902.21": "Xin lỗi vì tôi đã nghĩ bậy cho cậu nhé.",
    "PM15902.22": "Cho tôi xin lỗi nha!",
    "PM15902.23": "Vậy... Cậu sẽ qua chứ?",
    "PM15902.24": "Ừm! Tôi hứa đấy!",
    "PM15902.25": "Tuyệt quá!",
    "PM15902.27": "Sao tôi vẫn cứ thấy có gì đó sai sai nhỉ?",
    "PM15902.28": "Ý cậu là sao?",
    "PM15902.29": "Nếu chỉ ăn tối thôi thì gặp nhau ở sảnh dưới là được rồi, sao cậu phải đặt hẳn một phòng riêng làm gì?",
    "PM15902.30": "Tại dưới tầng đông người quá.",
    "PM15902.31": "Bọn họ sẽ làm phiền việc tôi quan sát cậu trong lúc ăn mất.",
    "PM15902.32": "Biết ngay mà! Biết ngay là cậu có động cơ ngầm mà!",
    "PM15902.33": "Tôi đùa chút thôi.",
    "PM15902.34": "Ban công của căn phòng đó là vị trí đẹp nhất để ngắm pháo hoa. Tôi muốn cùng ngắm pháo hoa với cậu.",
    "PM15902.35": "Thiệt tình, nói toẹt ra ngay từ đầu có phải hơn không."
}

def update_file(path: Path):
    if not path.exists():
        return
    updated_lines = []
    applied = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            iid = item.get("id")
            if iid in FIXES:
                item["vi_editorial"] = unicodedata.normalize("NFC", FIXES[iid])
                applied += 1
            updated_lines.append(item)
    with open(path, "w", encoding="utf-8") as f:
        for it in updated_lines:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(f"Updated {path.name}: applied {applied} fixes across {len(updated_lines)} lines.")

def main():
    print(f"Total fixes to apply: {len(FIXES)}")
    update_file(UNIFIED_FILE)
    update_file(PART_A_FILE)
    update_file(PART_B_FILE)

if __name__ == "__main__":
    main()
