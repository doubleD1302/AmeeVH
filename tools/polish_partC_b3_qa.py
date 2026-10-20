import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
orig_path = ROOT / "work" / "batches" / "batch_10k_b3_partC.json"
trans_path = ROOT / "work" / "batches" / "batch_10k_b3_partC_translated.json"

orig = json.load(open(orig_path, encoding='utf-8'))
trans = json.load(open(trans_path, encoding='utf-8'))

polished = dict(trans)
stats = {
    "new_star_fixed": 0,
    "white_cat_fixed": 0,
    "imperial_guard_fixed": 0,
    "scorpions_fixed": 0,
    "scepters_fixed": 0,
    "hoa_hong_fixed": 0,
    "boss_fixed": 0,
    "stand_down_fixed": 0,
    "pm_nuances_fixed": 0,
    "ruby_fixed": 0,
    "novian_fixed": 0,
    "total_changes": 0
}

# 1. Manual & High precision targeted fixes
manual_fixes = {
    "PM11601.22": "Này Sếp ơi, hôm nay tôi đào được một thứ rất cứng trên cánh đồng này",
    "PM11601.25": "Số Dorra cậu dành dụm được á?",
    "PM11602.3": "Chúng chật ních luôn ấy!",
    "PM11701.2": "Chắc chắn rồi, Quán Trưởng Jinglin!",
    "PM11701.3": "Không thành vấn đề, Quán Trưởng Jinglin!",
    "PM11701.71": "Đột nhiên mấy hôm nay tụi em nhận được rất nhiều nhiệm vụ ủy thác. Em đã tính nộp sớm...",
    "PM11701.72": "Nhiều nhiệm vụ ủy thác ghê...",
    "PM11801.65": "Sao tự nhiên lại hỏi tôi câu này thế?",
    "PM11902.50": "Nghĩ lại thì, thù lao ủy thác của bạn khá cao đấy.",
    "STm08_11.45": "Lùi lại đi, Noya. ==W== Hồi đó họ chỉ là lính đánh thuê theo lệnh, và bây giờ cô ấy không còn thù địch nữa. ==W== Chúng ta là người mới ở đây. Không có ích gì khi gây chiến với người dân địa phương.",
    "STm08_12.97": "Chaton, lùi lại!",
    "STm08_17_a.37": "Lùi lại đi, Taffett. ==W== Tôi biết bạn đang tức giận, nhưng chúng tôi có mệnh lệnh của mình. ==W== Miễn là Mèo Trắng còn phục vụ Đế quốc, chúng tôi sẽ không làm bậy. Chúng ta đã rõ ràng chưa?",
    "STm08_18_a.153": "Hạ vũ khí xuống! Chúng ta là hiệp sĩ, không phải đao phủ!",
    "STm08_16_b.36": "Quyền Trượng Tử Thần được làm bằng thép đặc biệt, đúng vậy... ==W== Khoan đã. ==W== Biết tên là một chuyện, nhưng làm sao bạn biết nó được làm từ <r=·>thép</r> <r=·>đặc biệt</r>?",
    "STm08_16_b.40": "Bình tĩnh nào. ==W== Sau cuộc trò chuyện của chúng tôi, cô ta trườn đi như một con rắn. Chẳng để lại gì ngoài <r=cloak>lớp da</r> kinh tởm của ả.",
    "STm08_17_a.126": "Taffett, từ khi nào mà em lại trở nên đáng <r=contradictory></r>yêu như thế hả? ==W==",
    "STm08_19_b.199": "<r=L-Lưỡi của tôi...>Khụ... Khụ...</r> ==W== <r=K-Không...>A...</r> ==W== Hự, <r=Ả ta chẳng chịu nghe một lời nào cả...>hự</r>...",
    "STm08_13.91": "<Khụ... ==W== Sức bóp của cô...! ==W== Tôi không thở được... <",
    "STm08_15.112": "Tin tình báo đổi lấy tin tình báo. ==W== Đây là một cuộc trao đổi sòng phẳng. ==W== Sếp, chúng ta sắp hết thời gian rồi. Chúng ta có nên đồng ý không?",
    "STm08_16_a.105": "Chiêu bài đó nghe quen thuộc ghê. Sếp... ==W==",
    "STm08_16_b.27": "Để kỷ niệm cuộc hội ngộ của chúng ta ở Huyễn Cảnh, ==W== tôi đã pha món đồ uống này cho bạn. Tôi gọi nó là Sếp.",
    "STm08_16_b.79": "Nhưng... ==W== Tôi thà lấy Quyền Trượng Tử Thần hơn là Phong Ấn bất cứ lúc nào. ==W== Một Tạo Vật độc quyền như thế sẽ tốt hơn nhiều cho chúng ta, bất kể dùng hay bán.",
    "STm08_16_b.111": "Kể từ đó, chúng tôi lần lượt leo lên các Cự Tháp nơi Vùng Hoang Dã, ==RT== thu thập Quyền Trượng Tử Thần.",
    "STm08_16_b.116": "Sếp cần nghỉ ngơi đi. Chúng ta có đủ Quyền Trượng rồi.",
    "STm08_18_b.212": "Ồ? Có phải Cận Vệ Hoàng Gia cũng muốn có phần trong việc buôn bán Quyền Trượng không?",
    "STm08_18_b.216": "Hừm. Việc đầu tiên cần làm. ==W== Để thành lập một công ty bình phong hợp pháp nhằm bán Quyền Trượng, trước tiên chúng ta cần có Phong Ấn Grace.",
    "STm08_18_b.220": "Hừm. Với sự độc quyền về Quyền Trượng và bộ giáp mới của Cận Vệ Hoàng Gia, lũ dân đen đó sẽ không có cửa. Sẽ không còn những đòn đánh lén bẩn thỉu từ đám thảo khấu nữa.",
    "STm08_18_b.236": "Các ngươi dựa dẫm quá nhiều vào những Quyền Trượng đó rồi! Sơ hở sau lưng lộ hết cả ra kìa!",
    "STm08_18_b.246": "Heh... ==W== Bwahahahaha! ==W== Ngươi thực sự nghĩ rằng Angie đang nắm quyền quyết định sao? Rằng cô ta là kẻ điều hành đường dây buôn bán Quyền Trượng của chúng ta ư?",
    "STm08_18_b.258": "Đường dây buôn bán Quyền Trượng... ==W== Ngươi đã điều hành nó suốt thời gian qua sao?",
    "STm08_18_b.261": "Sếp, những chiếc thùng này chứa đầy thuốc súng màu xám đen. Đó là thuốc nổ từ đạn của Quyền Trượng!",
    "STm08_19_b.19": "Ừm. Đó không phải là thứ bạn ước thành hình, mà là một Quyền Trượng Tử Thần hoàn toàn mới với lời nguyện do Joseph sáng chế.",
    "STm08_19_b.60": "Không phải cô ấy. Angie không dính líu gì đến việc buôn bán Quyền Trượng cả. ==RT== Cô ấy đã biến mất trong Cự Thạch hơn một năm trước rồi.",
    "STm08_19_b.289": "Tôi hiểu mà. Vào thời khắc tôi bắt đầu phát tán Quyền Trượng Tử Thần để tự vệ, chẳng đời nào người Novian lại chịu từ bỏ một vũ khí tiện lợi đến nhường này.",
    "STm08_14.96": "Khụ, dù sao đi nữa. Tôi tìm thấy vài manh mối về Cự Thạch mà các bạn đang tìm. ==W== Tôi đã hỏi thăm những mối quen cũ của mình bên Mèo Trắng và Bọ Cạp Sa Mạc, kiếm được tin tức độc quyền không nghe thấy trên đường phố đâu."
}

for k, val in manual_fixes.items():
    if k in polished:
        polished[k] = val
        stats["total_changes"] += 1

# 2. Global pattern replacements
for k, t in list(polished.items()):
    orig_t = t
    
    # New Star Guild
    t = re.sub(r'(?:Hiệp hội|Hội|Bang hội)\s*Ngôi\s*sao\s*Mới', 'Lữ Đoàn Tân Tinh', t, flags=re.IGNORECASE)
    t = re.sub(r'\bHiệp hội Ngôi sao mới\b', 'Lữ Đoàn Tân Tinh', t, flags=re.IGNORECASE)
    
    # White Cat Troupe
    # If it's "Đội Mèo Trắng" / "Đoàn Mèo Trắng" / "Nhóm Mèo Trắng" / "Bầy Mèo Trắng"
    t = re.sub(r'(?:Đội|Đoàn|Nhóm|Bầy)\s*Mèo\s*Trắng', 'Gánh Xiếc Mèo Trắng', t)
    t = re.sub(r'\bNhững chú Mèo Trắng\b', 'Mèo Trắng', t, flags=re.IGNORECASE)
    
    # Imperial Guard
    t = re.sub(r'Vệ\s*binh\s*Hoàng\s*gia', 'Cận Vệ Hoàng Gia', t, flags=re.IGNORECASE)
    t = re.sub(r'Đội\s*cận\s*vệ\s*Hoàng\s*gia', 'Cận Vệ Hoàng Gia', t, flags=re.IGNORECASE)
    
    # Desert Scorpions
    t = re.sub(r'\bDesert Scorpions\b', 'Bọ Cạp Sa Mạc', t)
    t = re.sub(r'\bBọ cạp sa mạc\b', 'Bọ Cạp Sa Mạc', t)
    
    # Scepters of Death
    t = re.sub(r'\bScepters of Death\b', 'Quyền Trượng Tử Thần', t)
    t = re.sub(r'\bScepter of Death\b', 'Quyền Trượng Tử Thần', t)
    t = re.sub(r'Vương\s*trượng\s*Tử\s*thần', 'Quyền Trượng Tử Thần', t, flags=re.IGNORECASE)
    t = re.sub(r'Quyền\s*trượng\s*của\s*cái\s*chết', 'Quyền Trượng Tử Thần', t, flags=re.IGNORECASE)
    
    # Novians redundancy
    t = re.sub(r'người Dân người Novian', 'người Novian', t, flags=re.IGNORECASE)
    t = re.sub(r'Dân người Novian', 'người Novian', t, flags=re.IGNORECASE)
    
    # Boss addressing in dialogues
    # Replace "ông chủ" with "Sếp"
    t = re.sub(r'\bÔng chủ\b', 'Sếp', t)
    t = re.sub(r'\bông chủ\b', 'Sếp', t)
    
    # "hoa hồng" in commissions
    if "commission" in orig[k].lower():
        t = re.sub(r'\bhoa\s*hồng\b', 'nhiệm vụ ủy thác', t, flags=re.IGNORECASE)
        t = re.sub(r'phí\s*nhiệm vụ ủy thác', 'thù lao ủy thác', t, flags=re.IGNORECASE)

    if t != orig_t:
        polished[k] = t
        stats["total_changes"] += 1

print(f"Polishing complete. Total modified strings: {stats['total_changes']}")

# Save back to batch_10k_b3_partC_translated.json
with open(trans_path, 'w', encoding='utf-8') as f:
    json.dump(polished, f, ensure_ascii=False, indent=2)

print(f"Saved updated file to {trans_path}")
