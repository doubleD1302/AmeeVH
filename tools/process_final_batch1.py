import json
import re
import sys
from pathlib import Path

# Paths
INPUT_PATH = Path("StellaSora_VietHoa/work/batches/final_batch1_combat_skills.json")
OUTPUT_PATH = Path("StellaSora_VietHoa/work/batches/final_batch1_combat_skills_approved.json")

# Character names (TrialCharacter)
TRIAL_CHARACTERS = {
    "Alina": "Alina",
    "Allie": "Allie",
    "Amber": "Amber",
    "Ann": "Ann",
    "Canace": "Canace",
    "Caramel": "Caramel",
    "Chaton": "Chaton",
    "Chitose": "Chitose",
    "Chixia": "Chixia",
    "Coronis": "Coronis",
    "Cosette": "Cosette",
    "Donna": "Donna",
    "Eleanor": "Eleanor",
    "Firefly": "Firefly",
    "Firenze": "Firenze",
    "Firstlight Noya": "Noya - Khải Minh",
    "Flora": "Flora",
    "Freesia": "Freesia",
    "Fuyuka": "Fuyuka",
    "Gerie": "Gerie",
    "Iris": "Iris",
    "Jinglin": "Jinglin",
    "Karin": "Karin",
    "Kasimira": "Kasimira",
    "Laru": "Laru",
    "Minova": "Minova",
    "Mistique": "Mistique",
    "Nanoha": "Nanoha",
    "Nazuka": "Nazuka",
    "Nazuna": "Nazuna",
    "Noya": "Noya",
    "Otoha": "Otoha",
    "Ridge": "Ridge",
    "Shia": "Shia",
    "Shimiao": "Shimiao",
    "Snowish Laru": "Laru Dạ Thánh",
    "Sparkla": "Sparkla",
    "Springseek Coronis": "Coronis Nghênh Xuân",
    "Teresa": "Teresa",
    "Tilia": "Tilia",
    "Willow": "Willow",
    "Wraith": "Wraith"
}

# TrialBuild
TRIAL_BUILDS = {
    "Story Record": "Bản Ghi Cốt Truyện",
    "Ignis Trial Records": "Bản Ghi Dùng Thử Hệ Hỏa",
    "Aqua Trial Records": "Bản Ghi Dùng Thử Hệ Thủy",
    "Ventus Trial Records": "Bản Ghi Dùng Thử Hệ Phong",
    "Terra Trial Records": "Bản Ghi Dùng Thử Hệ Địa",
    "Lux Trial Records": "Bản Ghi Dùng Thử Hệ Quang",
    "Umbra Trial Records": "Bản Ghi Dùng Thử Hệ Ám"
}

# InfinityTowerLevel
INFINITY_TOWER_LEVELS = {
    "[Flames and Beats] Difficulty 21": "[Điệu Nhảy Bốc Lửa] Độ Khó 21",
    "[Flames and Beats] Difficulty 22": "[Điệu Nhảy Bốc Lửa] Độ Khó 22",
    "[Elegance and Flow] Difficulty 21": "[Thanh Nhã Lưu Ca] Độ Khó 21",
    "[Elegance and Flow] Difficulty 22": "[Thanh Nhã Lưu Ca] Độ Khó 22",
    "[Shake the Floor] Difficulty 21": "[Pháo Đài Rung Chuyển] Độ Khó 21",
    "[Shake the Floor] Difficulty 22": "[Pháo Đài Rung Chuyển] Độ Khó 22",
    "[Sinister Ritual] Difficulty 21": "[Nghi Thức U Tối] Độ Khó 21",
    "[Sinister Ritual] Difficulty 22": "[Nghi Thức U Tối] Độ Khó 22",
    "[Thrilling Beat] Difficulty 21": "[Nhịp Điệu Hào Hùng] Độ Khó 21",
    "[Thrilling Beat] Difficulty 22": "[Nhịp Điệu Hào Hùng] Độ Khó 22",
    "[Upbeat Party] Difficulty 21": "[Bữa Tiệc Rực Rỡ] Độ Khó 21",
    "[Upbeat Party] Difficulty 22": "[Bữa Tiệc Rực Rỡ] Độ Khó 22"
}

# InfinityTowerAffix
INFINITY_TOWER_AFFIX_NAMES = {
    "Mark Trance I": "Vũ Điệu Ấn Ký I",
    "Mark Trance Ⅱ": "Vũ Điệu Ấn Ký II",
    "Blade Hunger": "Tàn Nhẫn Ẩm Huyết",
    "Cognitive Glitch": "Nhận Thức Sai Lệch",
    "Battle Enraged Ⅰ": "Càng Đánh Càng Hăng I",
    "Battle Enraged Ⅱ": "Càng Đánh Càng Hăng II",
    "Battle Enraged Ⅲ": "Càng Đánh Càng Hăng III",
    "Technique Tradeoff Ⅰ": "Đổi Bù Kỹ Nghệ I",
    "Offense Tradeoff Ⅰ": "Công Thủ Bù Trừ I",
    "Minion Tradeoff Ⅰ": "Triệu Hồi Bù Trừ I",
    "Pain into Power": "Dấn Thân Thử Lửa",
    "Disrupted Rhythm": "Rối Loạn Nhịp Điệu",
    "Disrupted Rhythm: Greater": "Rối Loạn Nhịp Điệu: Lớn",
    "Sluggish Recharge": "Hồi Năng Trì Trệ",
    "Onslaught Tradeoff": "Cường Công Bù Trừ",
    "Price of Escape": "Cái Giá Thoát Thân",
    "Dodge Slowdown": "Né Tránh Giảm Tốc",
    "Perilous Evade": "Né Tránh Nguy Hiểm",
    "Riddled with Wounds Ⅰ": "Thương Tích Đầy Mình I",
    "Riddled with Wounds Ⅱ": "Thương Tích Đầy Mình II",
    "Victorious Pursuit Ⅰ": "Thừa Thắng Xông Lên I",
    "Victorious Pursuit Ⅱ": "Thừa Thắng Xông Lên II",
    "Auto Attack Mastery Ⅰ": "Tinh Thông Đòn Đánh Thường I",
    "Auto Attack Mastery Ⅱ": "Tinh Thông Đòn Đánh Thường II",
    "Auto Attack Mastery Ⅲ": "Tinh Thông Đòn Đánh Thường III",
    "Skill Mastery I": "Tinh Thông Kỹ Năng I",
    "Skill Mastery Ⅱ": "Tinh Thông Kỹ Năng II",
    "Skill Mastery Ⅲ": "Tinh Thông Kỹ Năng III",
    "Ultimate Mastery Ⅰ": "Tinh Thông Tuyệt Kỹ I",
    "Ultimate Mastery Ⅱ": "Tinh Thông Tuyệt Kỹ II",
    "Ultimate Mastery Ⅲ": "Tinh Thông Tuyệt Kỹ III",
    "Mark Mastery Ⅰ": "Tinh Thông Ấn Ký I",
    "Mark Mastery Ⅱ": "Tinh Thông Ấn Ký II",
    "Mark Mastery Ⅲ": "Tinh Thông Ấn Ký III",
    "HP Boost Ⅰ": "Tăng Cường HP I",
    "HP Boost Ⅱ": "Tăng Cường HP II",
    "HP Boost Ⅲ": "Tăng Cường HP III"
}

INFINITY_TOWER_AFFIX_DESCS = {
    "The Main Trekker loses {2}% of current HP every {1}s, but each Crit Hit restores {3}% of Max HP.":
        "Lữ Khách Chủ Lực mỗi {1} giây mất {2}% HP hiện tại, nhưng mỗi đòn Bạo Kích sẽ hồi phục {3}% HP Tối Đa.",
    "Increases the Main Trekker's Skill DMG by {1}%, which then decreases it by {2}% every {3}s":
        "Tăng {1}% Sát Thương Kỹ Năng của Lữ Khách Chủ Lực, sau đó mỗi {3} giây sẽ giảm {2}%.",
    "[Monster] For every {1}s in combat, increases DMG by {2}%.":
        "[Quái Vật] Mỗi {1} giây trong trận chiến, tăng {2}% Sát Thương.",
    "[Squad] Reduces Mark DMG by {1}% and increases Ultimate DMG by {2}%.":
        "[Toàn Đội] Giảm {1}% Sát Thương Ấn Ký và tăng {2}% Sát Thương Tuyệt Kỹ.",
    "[Squad] Reduces Auto ATK DMG by {1}% and increases Skill DMG by {2}%.":
        "[Toàn Đội] Giảm {1}% Sát Thương Đòn Đánh Thường và tăng {2}% Sát Thương Kỹ Năng.",
    "[Squad] Reduces Skill DMG by {1}% and increases Minion DMG by {2}%.":
        "[Toàn Đội] Giảm {1}% Sát Thương Kỹ Năng và tăng {2}% Sát Thương Triệu Hồi Vật.",
    "The Main Trekker takes {1}% more DMG, but gains {2} Energy when hit. Triggers once every {3}s.":
        "Lữ Khách Chủ Lực chịu thêm {1}% Sát Thương, nhưng nhận {2} Năng Lượng khi bị trúng đòn. Kích hoạt một lần mỗi {3} giây.",
    "When the Main Trekker is hit, reduces Skill DMG by {1}% for {2}s. Triggers once every {3}s.":
        "Khi Lữ Khách Chủ Lực bị trúng đòn, giảm {1}% Sát Thương Kỹ Năng trong {2} giây. Kích hoạt một lần mỗi {3} giây.",
    "[Squad] Within {1}s after casting a skill, reduces Charge Efficiency by {2}%.":
        "[Toàn Đội] Trong {1} giây sau khi thi triển kỹ năng, giảm {2}% Hiệu Suất Tích Năng Lượng.",
    "[Squad] Increases Skill DMG by {1}%, but increases DMG taken by {2}%.":
        "[Toàn Đội] Tăng {1}% Sát Thương Kỹ Năng, nhưng tăng {2}% Sát Thương Gánh Chịu.",
    "After the Main Trekker dodges, loses {1} Ultimate Energy.":
        "Sau khi Lữ Khách Chủ Lực né tránh, tiêu hao {1} Năng Lượng Tuyệt Kỹ.",
    "Increases the Main Trekker's Dodge Cooldown by {1}s.":
        "Tăng {1} giây Hồi Chiêu Né Tránh của Lữ Khách Chủ Lực.",
    "After the Main Trekker dodges, increases DMG taken by {1}% for {2}s.":
        "Sau khi Lữ Khách Chủ Lực né tránh, tăng {1}% Sát Thương Gánh Chịu trong {2} giây.",
    "When the Main Trekker is hit, increases DMG taken by {1}% for {2}s. Stacks up to {3} times.":
        "Khi Lữ Khách Chủ Lực bị trúng đòn, tăng {1}% Sát Thương Gánh Chịu trong {2} giây. Tối đa cộng dồn {3} tầng.",
    "[Monster] After hitting the Main Trekker, increases DMG by {1}% for {2}s.":
        "[Quái Vật] Sau khi đánh trúng Lữ Khách Chủ Lực, tăng {1}% Sát Thương trong {2} giây.",
    "[Squad] Increases Auto ATK DMG Power by {1}%.":
        "[Toàn Đội] Tăng {1}% Cường Độ Sát Thương Đòn Đánh Thường.",
    "[Squad] Increases Skill DMG Power by {1}%.":
        "[Toàn Đội] Tăng {1}% Cường Độ Sát Thương Kỹ Năng.",
    "[Squad] Increases Ultimate DMG Power by {1}%.":
        "[Toàn Đội] Tăng {1}% Cường Độ Sát Thương Tuyệt Kỹ.",
    "[Squad] Increases Mark DMG Power by {1}%.":
        "[Toàn Đội] Tăng {1}% Cường Độ Sát Thương Ấn Ký.",
    "Increases the Main Trekker's Max HP by {1}%.":
        "Tăng {1}% HP Tối Đa của Lữ Khách Chủ Lực."
}

# TravelerDuelChallengeAffix
TRAVELER_DUEL_AFFIX_NAMES = {
    "DMG Increase: Lesser": "Tăng Sát Thương: Nhỏ",
    "DMG Increase: Medium": "Tăng Sát Thương: Vừa",
    "DMG Increase: Greater": "Tăng Sát Thương: Lớn",
    "Stagnant Dew: Lesser": "Mật Lộ Ngưng Trệ: Nhỏ",
    "Stagnant Dew: Medium": "Mật Lộ Ngưng Trệ: Vừa",
    "Stagnant Dew: Greater": "Mật Lộ Ngưng Trệ: Lớn",
    "Leech Arcana": "Bí Thuật Hút Máu",
    "Mutual Aid": "Tương Hỗ Hợp Lực",
    "Bait and Ambush": "Vây Điểm Đánh Viện",
    "Shield Reliance": "Bảo Hộ Khiên Chắn",
    "Just Right": "Vừa Đúng Chuẩn Mực",
    "Weakening Arcana": "Bí Thuật Suy Nhược",
    "Weakening Arcana: Greater": "Bí Thuật Suy Nhược: Lớn",
    "Vaporous Drift": "Kỳ Hương Vô Trọng",
    "Delayed Awakening": "Bí Tửu Thức Muộn",
    "Fleeting Bloom": "Đàm Hoa Nhất Hiện",
    "Honeyed Toxin": "Độc Hương Ngọt Ngào",
    "Master of Summons": "Chúa Tể Triệu Linh",
    "Blade Over Curse": "Xả Chú Thủ Nhận",
    "One Last Bet": "Cô Chú Nhất Trịch",
    "Combat Momentum": "Chiến Đấu Tăng Tiến",
    "Combat Momentum: Greater": "Chiến Đấu Tăng Tiến: Lớn",
    "Crit Tuning: Rate": "Điều Chỉnh Bạo Kích: Tỷ Lệ",
    "Crit Tuning: DMG": "Điều Chỉnh Bạo Kích: Sát Thương",
    "Blood to Shield: Lesser": "Hóa Huyết Thành Thuẫn: Nhỏ",
    "Blood to Shield: Medium": "Hóa Huyết Thành Thuẫn: Vừa",
    "Blood to Shield: Greater": "Hóa Huyết Thành Thuẫn: Lớn",
    "Hasty Mix": "Điều Phối Thần Tốc",
    "Grievous Arcana": "Bí Thuật Trọng Thương",
    "Grievous Arcana: Greater": "Bí Thuật Trọng Thương: Lớn",
    "Magic Drain: Lesser": "Hấp Thu Ma Lực: Nhỏ",
    "Magic Drain: Medium": "Hấp Thu Ma Lực: Vừa",
    "Magic Drain: Greater": "Hấp Thu Ma Lực: Lớn",
    "Fuel from Pain": "Nghịch Thương Tăng Uy",
    "Borrowed Time": "Hồi Quang Kỳ Nguyện",
    "Reckless Craving": "Bỏ Khiên Say Hương",
    "Devoted Entourage": "Bí Khế Tôi Trung",
    "Swift Diffusion": "Khuếch Tán Nồng Hương",
    "Perfume Alchemy": "Luyện Chế Bí Hương",
    "Double Trouble": "Song Sinh Quỷ Ảnh",
    "Summon Boost: Aroma Phantom": "Tăng Cường Triệu Linh: Thấm Hương Ảnh Linh",
    "Summon Boost: Incense Phantom": "Tăng Cường Triệu Linh: Huân Hương Ảnh Linh"
}

TRAVELER_DUEL_AFFIX_DESCS = {
    "All enemies' damage dealt increases by <color=#ec6d21>&Param1&</color>.":
        "Cường độ sát thương của tất cả kẻ địch tăng <color=#ec6d21>&Param1&</color>.",
    "Reduces the squad's Charge Efficiency by <color=#ec6d21>&Param1&</color>.":
        "Hiệu suất tích năng lượng toàn đội giảm <color=#ec6d21>&Param1&</color>.",
    "Increases the Main Trekker's DMG taken by <color=#ec6d21>&Param1&</color>. In return, dealing Skill DMG restores <color=#ec6d21>&Param2&</color> HP per hit.":
        "Cường độ sát thương gánh chịu của Lữ Khách Chủ Lực tăng <color=#ec6d21>&Param1&</color>, bù lại mỗi khi gây sát thương kỹ năng sẽ hồi <color=#ec6d21>&Param2&</color> HP.",
    "For every 1s a Support Trekker is on the field, reduces the Main Trekker's DMG Power by <color=#ec6d21>&Param1&</color> and grants a Shield equal to <color=#ec6d21>&Param2&</color> of HP for <color=#ec6d21>&Param3&</color>s, stacking up to <color=#ec6d21>&Param4&</color> times. Support Trekkers gain 1 stack each time they enter combat.":
        "Mỗi 1 giây Lữ Khách Viện Trợ có mặt trên sân, cường độ sát thương của Lữ Khách Chủ Lực giảm <color=#ec6d21>&Param1&</color> và nhận một lá chắn bằng <color=#ec6d21>&Param2&</color> HP trong <color=#ec6d21>&Param3&</color> giây, tối đa cộng dồn <color=#ec6d21>&Param4&</color> tầng. Lữ Khách Viện Trợ nhận ngay 1 tầng mỗi khi vào trận.",
    "For every 1s a Support Trekker is on the field, increases the Main Trekker's DMG Power by <color=#ec6d21>&Param1&</color> and DMG taken by <color=#ec6d21>&Param2&</color> for <color=#ec6d21>&Param3&</color>s, stacking up to <color=#ec6d21>&Param4&</color> times. Support Trekkers gain 1 stack each time they enter combat.":
        "Mỗi 1 giây Lữ Khách Viện Trợ có mặt trên sân, cường độ sát thương của Lữ Khách Chủ Lực tăng <color=#ec6d21>&Param1&</color> và sát thương gánh chịu tăng <color=#ec6d21>&Param2&</color> trong <color=#ec6d21>&Param3&</color> giây, tối đa cộng dồn <color=#ec6d21>&Param4&</color> tầng. Lữ Khách Viện Trợ nhận ngay 1 tầng mỗi khi vào trận.",
    "After the battle begins, increases Shield gained by the Main Trekker by <color=#ec6d21>&Param1&</color>, but reduces the Main Trekker's DMG Power by <color=#ec6d21>&Param2&</color> while no Shield is active.":
        "Sau khi trận chiến bắt đầu, lượng lá chắn Lữ Khách Chủ Lực nhận được tăng <color=#ec6d21>&Param1&</color>, nhưng khi không có lá chắn thì cường độ sát thương giảm <color=#ec6d21>&Param2&</color>.",
    "While the Main Trekker's HP is above <color=#ec6d21>&Param1&</color> or below <color=#ec6d21>&Param2&</color>, decreases the squad's DMG Power by <color=#ec6d21>&Param3&</color>.":
        "Khi HP của Lữ Khách Chủ Lực trên <color=#ec6d21>&Param1&</color> hoặc dưới <color=#ec6d21>&Param2&</color>, cường độ sát thương của toàn đội giảm <color=#ec6d21>&Param3&</color>.",
    "When the Main Trekker is hit, reduces the Main Trekker's Skill DMG Power by <color=#ec6d21>&Param1&</color> for <color=#ec6d21>&Param2&</color>s, stacking up to <color=#ec6d21>&Param3&</color> times.":
        "Khi Lữ Khách Chủ Lực bị trúng đòn, cường độ sát thương kỹ năng của Lữ Khách Chủ Lực giảm <color=#ec6d21>&Param1&</color> trong <color=#ec6d21>&Param2&</color> giây, tối đa cộng dồn <color=#ec6d21>&Param3&</color> tầng.",
    "When the Main Trekker is hit, reduces the squad's Skill DMG Power by <color=#ec6d21>&Param1&</color> for <color=#ec6d21>&Param2&</color>s, stacking up to <color=#ec6d21>&Param3&</color> times.":
        "Khi Lữ Khách Chủ Lực bị trúng đòn, cường độ sát thương kỹ năng của toàn đội giảm <color=#ec6d21>&Param1&</color> trong <color=#ec6d21>&Param2&</color> giây, tối đa cộng dồn <color=#ec6d21>&Param3&</color> tầng.",
    "Dodging drops the Main Trekker's DEF to 0 for <color=#ec6d21>&Param1&</color>s.":
        "Sau khi né tránh, phòng thủ của Lữ Khách Chủ Lực giảm về 0 trong <color=#ec6d21>&Param1&</color> giây.",
    "For the first <color=#ec6d21>&Param1&</color>s of combat, reduces the squad's Charge Efficiency by 100%. Once this period ends, increases by <color=#ec6d21>&Param2&</color> instead.":
        "Trong <color=#ec6d21>&Param1&</color> giây đầu trận chiến, hiệu suất tích năng lượng của toàn đội giảm 100%. Hết thời gian này sẽ chuyển thành tăng <color=#ec6d21>&Param2&</color>.",
    "For the first <color=#ec6d21>&Param1&</color>s of combat, increases the squad's Charge Efficiency by <color=#ec6d21>&Param2&</color>. However, once combat reaches the <color=#ec6d21>&Param3&</color>s mark, decreases by 50%.":
        "Trong <color=#ec6d21>&Param1&</color> giây đầu trận chiến, hiệu suất tích năng lượng của toàn đội tăng <color=#ec6d21>&Param2&</color>. Tuy nhiên khi trận chiến đạt mốc <color=#ec6d21>&Param3&</color> giây, hiệu suất sẽ giảm 50%.",
    "Every <color=#ec6d21>&Param1&</color>s, the Main Trekker gains a Shield equal to <color=#ec6d21>&Param2&</color> of HP, but also suffers a <color=#ec6d21>&Param4&</color> increase to DMG taken for <color=#ec6d21>&Param3&</color>s.":
        "Mỗi <color=#ec6d21>&Param1&</color> giây, Lữ Khách Chủ Lực nhận một lá chắn bằng <color=#ec6d21>&Param2&</color> HP, nhưng sát thương gánh chịu trong <color=#ec6d21>&Param3&</color> giây cũng tăng <color=#ec6d21>&Param4&</color>.",
    "While the Main Trekker's HP is below <color=#ec6d21>&Param1&</color>, increases the squad's DMG Power by <color=#ec6d21>&Param2&</color>.":
        "Khi HP của Lữ Khách Chủ Lực dưới <color=#ec6d21>&Param1&</color>, cường độ sát thương của toàn đội tăng <color=#ec6d21>&Param2&</color>.",
    "Reduces the squad's Ultimate DMG Power by <color=#ec6d21>&Param1&</color> to increase Auto ATK DMG Power by <color=#ec6d21>&Param2&</color>.":
        "Cường độ sát thương tuyệt kỹ toàn đội giảm <color=#ec6d21>&Param1&</color>, bù lại cường độ sát thương đòn đánh thường tăng <color=#ec6d21>&Param2&</color>.",
    "Reduces the squad's Auto ATK DMG Power by <color=#ec6d21>&Param1&</color> to increase Ultimate DMG Power by <color=#ec6d21>&Param2&</color>.":
        "Cường độ sát thương đòn đánh thường toàn đội giảm <color=#ec6d21>&Param1&</color>, bù lại cường độ sát thương tuyệt kỹ tăng <color=#ec6d21>&Param2&</color>.",
    "Reduces the squad's Minion DMG Power by <color=#ec6d21>&Param1&</color> to increase Skill DMG Power by <color=#ec6d21>&Param2&</color>.":
        "Cường độ sát thương triệu hồi vật toàn đội giảm <color=#ec6d21>&Param1&</color>, bù lại cường độ sát thương kỹ năng tăng <color=#ec6d21>&Param2&</color>.",
    "Reduces the squad's Mark DMG Power by <color=#ec6d21>&Param1&</color> to increase Auto ATK DMG Power by <color=#ec6d21>&Param2&</color>.":
        "Cường độ sát thương ấn ký toàn đội giảm <color=#ec6d21>&Param1&</color>, bù lại cường độ sát thương đòn đánh thường tăng <color=#ec6d21>&Param2&</color>.",
    "For every <color=#ec6d21>&Param1&</color>s in combat, increases the DMG Power of Mistique's minions by <color=#ec6d21>&Param2&</color>.":
        "Mỗi chiến đấu <color=#ec6d21>&Param1&</color> giây, cường độ sát thương từ triệu hồi vật của Mistique tăng <color=#ec6d21>&Param2&</color>.",
    "Increases the squad's Crit Rate by <color=#ec6d21>&Param1&</color> and reduces Crit DMG by <color=#ec6d21>&Param2&</color>.":
        "Tỷ lệ bạo kích toàn đội tăng <color=#ec6d21>&Param1&</color>, nhưng sát thương bạo kích giảm <color=#ec6d21>&Param2&</color>.",
    "Increases the squad's Crit DMG by <color=#ec6d21>&Param1&</color>, but reduces Crit Rate by <color=#ec6d21>&Param2&</color>.":
        "Sát thương bạo kích toàn đội tăng <color=#ec6d21>&Param1&</color>, nhưng tỷ lệ bạo kích giảm <color=#ec6d21>&Param2&</color>.",
    "For every <color=#ec6d21>&Param1&</color> HP Mistique loses, reduces her DMG taken by <color=#ec6d21>&Param2&</color>.":
        "Mỗi khi Mistique mất <color=#ec6d21>&Param1&</color> HP, cường độ sát thương bản thân gánh chịu giảm <color=#ec6d21>&Param2&</color>.",
    "For every <color=#ec6d21>&Param1&</color> HP Mistique loses, reduces her and her minions' DMG taken by <color=#ec6d21>&Param2&</color>.":
        "Mỗi khi Mistique mất <color=#ec6d21>&Param1&</color> HP, cường độ sát thương bản thân và triệu hồi vật gánh chịu giảm <color=#ec6d21>&Param2&</color>.",
    "Reduces the Main Trekker's Skill DMG Power by <color=#ec6d21>&Param1&</color> and Skill Cooldown by <color=#ec6d21>&Param2&</color>.":
        "Cường độ sát thương kỹ năng của Lữ Khách Chủ Lực giảm <color=#ec6d21>&Param1&</color>, nhưng hồi chiêu kỹ năng giảm <color=#ec6d21>&Param2&</color>.",
    "When hit, the Main Trekker cannot receive healing for <color=#ec6d21>&Param1&</color>s.":
        "Khi bị trúng đòn, Lữ Khách Chủ Lực không thể nhận hồi máu trong <color=#ec6d21>&Param1&</color> giây.",
    "Each time Mistique takes Skill DMG, reduces her and her minions' DMG taken by <color=#ec6d21>&Param1&</color> for <color=#ec6d21>&Param2&</color>s, stacking up to <color=#ec6d21>&Param3&</color> times. Stacks only once per second.":
        "Mỗi khi Mistique chịu sát thương kỹ năng, cường độ sát thương bản thân và triệu hồi vật gánh chịu giảm <color=#ec6d21>&Param1&</color> trong <color=#ec6d21>&Param2&</color> giây, tối đa cộng dồn <color=#ec6d21>&Param3&</color> tầng. Mỗi giây chỉ cộng dồn tối đa 1 tầng.",
    "Increases the Main Trekker's DMG taken by <color=#ec6d21>&Param1&</color>. When the Main Trekker takes DMG, reduces the remaining cooldown of the squad's Skills and Ultimates by <color=#ec6d21>&Param2&</color>s. This effect triggers only once every <color=#ec6d21>&Param3&</color>s.":
        "Cường độ sát thương gánh chịu của Lữ Khách Chủ Lực tăng <color=#ec6d21>&Param1&</color>. Khi Lữ Khách Chủ Lực chịu sát thương, thời gian hồi chiêu hiện tại của Kỹ Năng và Tuyệt Kỹ toàn đội giảm <color=#ec6d21>&Param2&</color> giây, hiệu ứng này chỉ kích hoạt 1 lần mỗi <color=#ec6d21>&Param3&</color> giây.",
    "After taking fatal DMG, the Main Trekker will not die for <color=#ec6d21>&Param1&</color>s, but reduces the squad's DMG Power by <color=#ec6d21>&Param3&</color> for <color=#ec6d21>&Param2&</color>s. This effect triggers only once per battle.":
        "Sau khi chịu sát thương chí mạng, Lữ Khách Chủ Lực sẽ không tử trận trong <color=#ec6d21>&Param1&</color> giây, nhưng cường độ sát thương của toàn đội giảm <color=#ec6d21>&Param3&</color> trong <color=#ec6d21>&Param2&</color> giây. Hiệu ứng này chỉ kích hoạt 1 lần trong suốt trận chiến.",
    "When casting a skill, the Main Trekker restores <color=#ec6d21>&Param1&</color> HP. After being hit, the Main Trekker's Shield gained is greatly reduced for <color=#ec6d21>&Param2&s</color>.":
        "Khi thi triển kỹ năng, Lữ Khách Chủ Lực hồi <color=#ec6d21>&Param1&</color> HP. Sau khi bị trúng đòn, lượng lá chắn nhận được của Lữ Khách Chủ Lực giảm cực mạnh trong <color=#ec6d21>&Param2&s</color>.",
    "Mistique calls forth additional minions whenever she casts a Minion Summon skill.":
        "Mistique sẽ triệu hồi thêm triệu hồi vật mỗi khi thi triển bất kỳ kỹ năng \"Triệu Hồi Vật\" nào.",
    "Empowers Mistique's minion skills.":
        "Cường hóa các kỹ năng triệu hồi vật của Mistique.",
    "Increases the amount of Perfume Mistique regenerates naturally.":
        "Tăng lượng Nước Hoa mà Mistique tự động hồi phục.",
    "Casting Fragrant Summons for the first time also summons Grouch.":
        "Lần đầu thi triển kỹ năng \"Tích Hương Hoán Linh\", sẽ triệu hồi thêm \"Gã Khó Tính\".",
    "While Reverie Tour is active, Mistique summons Schemer instead.":
        "Khi Mistique đang trong trạng thái \"Tuần Du Kỳ Mộng\", sẽ đổi sang triệu hồi \"Kẻ Tinh Quái\".",
    "While Reverie Tour is active, Mistique summons Meanie instead.":
        "Khi Mistique đang trong trạng thái \"Tuần Du Kỳ Mộng\", sẽ đổi sang triệu hồi \"Kẻ Xấu Bụng\"."
}

# MainSkill
MAIN_SKILL_NAMES = {
    "My Guiding Star": "Khởi Minh Tinh Dẫn Lối",
    "Eternal Brilliance": "Tỏa Sáng Vĩnh Hằng"
}

MAIN_SKILL_DESCS = {
    "Increases the squad's HP by <color=#ec6d21>{1}</color>.\x0bAfter the Main Trekker triggers ##Lux Mark#1015# for the first time, gains 1 stack of Starwish.\x0bWhen a Trekker with Starwish deals Skill DMG to a target, increases the target's Lux Skill DMG Taken by <color=#ec6d21>{2}</color> for {3}s.\x0bWhen the Lux Main Trekker triggers the Mark to generate ##Lucent#4028#, increases own Crit Rate by <color=#ec6d21>{4}</color> for {5}s.":
        "HP toàn đội tăng <color=#ec6d21>{1}</color>.\x0bSau khi Lữ Khách Chủ Lực lần đầu kích hoạt ##Lux Mark#1015#, nhận 1 tầng \"Tinh Nguyện\".\x0bKhi Lữ Khách mang \"Tinh Nguyện\" gây Sát Thương Kỹ Năng lên mục tiêu, khiến Sát Thương Kỹ Năng hệ Quang mục tiêu gánh chịu tăng <color=#ec6d21>{2}</color> trong {3} giây.\x0bKhi Lữ Khách Chủ Lực hệ Quang kích hoạt ấn ký tạo ra ##Lucent#4028#, Tỷ Lệ Bạo Kích của bản thân tăng <color=#ec6d21>{4}</color> trong {5} giây.",
    "When the Lux Main Trekker deals Auto Attack or Skill DMG {1} times in total, gains 1 stack of Eternity: increases Lux Skill DMG by <color=#ec6d21>{2}</color> for {3}s, up to 10 stacks.\x0bWhile the Main Trekker has Eternity, increases the squad's Lux DMG dealt by <color=#ec6d21>{4}</color>.":
        "Khi Lữ Khách Chủ Lực hệ Quang tích lũy gây Sát Thương Đòn Đánh Thường hoặc Kỹ Năng {1} lần, nhận 1 tầng \"Vĩnh Hằng\": Sát Thương Kỹ Năng hệ Quang tăng <color=#ec6d21>{2}</color> trong {3} giây, có thể cộng dồn 10 tầng.\x0bKhi Lữ Khách Chủ Lực sở hữu \"Vĩnh Hằng\", Sát Thương hệ Quang do toàn đội gây ra tăng <color=#ec6d21>{4}</color>."
}

# SecondarySkill
SECONDARY_SKILL_NAMES = {
    "Shining Starwish": "Tinh Nguyện Lấp Lánh",
    "Forging Tomorrow": "Khai Thác Ngày Mai",
    "Garden of Eternity": "Vĩnh Hằng Chi Đình",
    "Light of Humanity": "Ánh Sáng Lòng Người"
}

SECONDARY_SKILL_DESCS = {
    "After a Versatile Trekker inflicts ##Lux Mark#1015# on a target for the first time, the Main Trekker gains 1 stack of Starwish.\x0bWhen a Trekker with Starwish deals Auto Attack DMG to a target, increases the target's Lux Auto Attack DMG Taken by <color=#ec6d21>{1}</color> for {2}s.\x0bStarwish gains an additional effect: each stack increases own Lux Skill DMG and Lux Auto Attack DMG by <color=#ec6d21>{3}</color>.":
        "Sau khi Lữ Khách Cân Bằng lần đầu gắn ##Lux Mark#1015# lên mục tiêu, Lữ Khách Chủ Lực nhận 1 tầng \"Tinh Nguyện\".\x0bKhi Lữ Khách mang \"Tinh Nguyện\" gây Sát Thương Đòn Đánh Thường lên mục tiêu, khiến Sát Thương Đòn Đánh Thường hệ Quang mục tiêu gánh chịu tăng <color=#ec6d21>{1}</color> trong {2} giây.\x0b\"Tinh Nguyện\" nhận thêm hiệu ứng: Mỗi tầng giúp Sát Thương Kỹ Năng hệ Quang và Sát Thương Đòn Đánh Thường hệ Quang của bản thân tăng <color=#ec6d21>{3}</color>.",
    "After a Support Trekker inflicts ##Lux Mark#1015# on a target for the first time, the Main Trekker gains 1 stack of Starwish.\x0bWhen any Lux Trekker casts a skill, increases the Lux Main Trekker's Crit DMG by <color=#ec6d21>{1}</color> for {2}s.\x0bStarwish gains an additional effect: Each stack increases the Skill Crit DMG dealt by the Lux Main Trekker by <color=#ec6d21>{3}</color>.":
        "Sau khi Lữ Khách Hỗ Trợ lần đầu gắn ##Lux Mark#1015# lên mục tiêu, Lữ Khách Chủ Lực nhận 1 tầng \"Tinh Nguyện\".\x0bKhi bất kỳ Lữ Khách hệ Quang nào thi triển kỹ năng, Sát Thương Bạo Kích của Lữ Khách Chủ Lực hệ Quang tăng <color=#ec6d21>{1}</color> trong {2} giây.\x0b\"Tinh Nguyện\" nhận thêm hiệu ứng: Mỗi tầng giúp Sát Thương Bạo Kích Kỹ Năng do Lữ Khách Chủ Lực hệ Quang gây ra tăng <color=#ec6d21>{3}</color>.",
    "For every {1}s a Lux Versatile Trekker is on the battlefield, grants the Main Trekker 1 stack of Eternity.\x0bEternity gains an additional effect: each stack increases own Lux Auto Attack DMG by <color=#ec6d21>{2}</color>.":
        "Mỗi {1} giây Lữ Khách Cân Bằng hệ Quang có mặt trên sân, gắn cho Lữ Khách Chủ Lực 1 tầng \"Vĩnh Hằng\".\x0b\"Vĩnh Hằng\" nhận thêm hiệu ứng: Mỗi tầng giúp Sát Thương Đòn Đánh Thường hệ Quang của bản thân tăng <color=#ec6d21>{2}</color>.",
    "When a Lux Support Trekker casts a skill, grants the Main Trekker 1 stack of Eternity.\x0bEternity can stack up to 20 times. When Eternity is at max stacks, increases own Lux DMG dealt by <color=#ec6d21>{1}</color>.":
        "Khi Lữ Khách Hỗ Trợ hệ Quang thi triển kỹ năng, gắn cho Lữ Khách Chủ Lực 1 tầng \"Vĩnh Hằng\".\x0b\"Vĩnh Hằng\" có thể cộng dồn tối đa 20 tầng. Khi \"Vĩnh Hằng\" đạt tầng tối đa, Sát Thương hệ Quang do bản thân gây ra tăng <color=#ec6d21>{1}</color>."
}

# Skill
SKILL_NAMES = {
    "Banishing Barrage": "Phá Ma Chi Tản",
    "Precision Strike": "Phẫu Thuật Chuẩn Xác",
    "Elegant Parade": "Thục Ảnh Man Vũ",
    "Reign of Night": "Quyền Khuynh Triêu Dạ",
    "Rising Tides": "Chuyển Vân Thôi Ba",
    "Chilling Drizzle": "Hàn Vũ Quyết",
    "Sniper Operation": "Tác Chiến Bắn Tỉa",
    "Area Explosion": "Bộc Phá Diện Rộng",
    "Bean Cyclone": "Mạch Đậu Hồi Toàn",
    "Floral Storm": "Bách Hoa Tề Phóng",
    "Static Discharge": "Minh Lôi Vân Thiểm",
    "Thunder Strike": "Oanh Lôi Triệt Điện",
    "Bone Chain": "Cốt Lao Cấm Cố",
    "Skeleton Sculpture": "Hài Cốt Điêu Khắc",
    "Flowers Dance": "Hoa Phong Vũ",
    "Flowers Bloom": "Hoa Vị Điêu",
    "Hat Toss": "Mở Màn Sân Khấu",
    "Flutter Flare": "Bạn Vũ Diễm Điệp",
    "Pumpka Pummel": "Quỷ Ảnh Trùng Trùng",
    "Summoning Circle": "Quái Kỳ Môn Phi",
    "Sentry Deployment": "Tiêu Vệ Triển Khai",
    "Armed Assault": "Vũ Trang Cường Kích",
    "Sweeping Rush": "Tảo Đường Đột Tiến",
    "Sweeping Slashes": "Thanh Tảo Liên Nhận",
    "Purifying Flames": "Xích Diễm Trừ Yêu",
    "Awakening: Crimson Dragon": "Phù Khởi: Xích Long",
    "Eruption Punch": "Tật Bộ Xung Quyền",
    "Nightbloom": "Dạ Đàm",
    "Shattered Edge": "Phá Nhận",
    "Bait and Catch": "Nguyện Giả Thượng Câu",
    "Raging Sea": "Nộ Hải Phiên Đằng",
    "Output Drive": "Tăng Sản Động Viên",
    "Efficient Operation": "Tác Nghiệp Tối Ưu",
    "Lightchase Flurry": "Trục Quang Loạn Nhận",
    "Whirling Rush": "Toàn Phong Đột Tiến",
    "Orb Barrage": "Liên Châu Pháp Cầu",
    "Starlight Fall": "Tinh Quang Trụy Lạc",
    "Sandwall Bulwark": "Hoàng Sa Cố Lũy",
    "Sandstep Thrust": "Đạp Sa Đột Thứ",
    "Rapid Reload": "Nạp Đạn Thần Tốc",
    "Sandpiercer Bolt": "Xuyên Sa Tiễn",
    "Lethal Calibration": "Hiệu Chuẩn Chí Mạng",
    "Pinpoint Hunt": "Định Điểm Liệp Sát",
    "Sandsweep Moonbreaker": "Lược Sa Đoạn Nguyệt",
    "Sandy Burial": "Thiên Mạc Sa Táng",
    "Rapier Waltz": "Tế Kiếm Viên Vũ",
    "Elegant Hunt": "Tao Nhã Vi Liệp",
    "!PENDING!": "!PENDING!"
}

SKILL_DESCS = {
    "Loads <color=#fb8037>3</color> Incendiary Shells, each pellet dealing <color=#fb8037>&Param1&</color> of ATK as Auto Attack DMG when fired.":
        "Nạp <color=#fb8037>3</color> viên đạn ghém rực lửa, khi bắn mỗi mảnh đạn gây Sát Thương Đòn Đánh Thường bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Air-drops a bomb, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG.":
        "Thả bom từ trên không, gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Slashes forward repeatedly, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG multiple times.":
        "Liên tục chém về phía trước, gây nhiều đợt Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Summons <color=#fb8037>2</color> Shadow Clones that last <color=#fb8037>6</color>s around the target. Shadow Clones continuously attack the target.":
        "Triệu hồi <color=#fb8037>2</color> \"Phân Thân Ám Ảnh\" duy trì <color=#fb8037>6</color> giây xung quanh mục tiêu, \"Phân Thân Ám Ảnh\" sẽ liên tục tấn công mục tiêu.",
    "Swings the sword to send out multiple waves, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG.":
        "Vung kiếm phóng ra nhiều đợt sóng nước, gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Condenses and fires a water blade, dealing <color=#fb8037>&Param1&</color> of ATK as Skill DMG to the target.":
        "Ngưng tụ thủy kiếm bắn ra, gây cho mục tiêu Sát Thương Kỹ Năng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Fires Dark Ray, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG.":
        "Bắn ra \"Tia Sáng Hắc Ám\", gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Throws <color=#fb8037>2</color> Bouncing Bombs at the target. Each deals <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG upon landing and can bounce up to <color=#fb8037>3</color> times.":
        "Ném <color=#fb8037>2</color> quả \"Bom Nảy\" về phía mục tiêu, khi chạm đất gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công, tối đa nảy <color=#fb8037>3</color> lần.",
    "Hurls seeds, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG.":
        "Tung hạt giống ra ngoài, gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Rains down seeds, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG over time.":
        "Giáng xuống cơn mưa hạt giống, liên tục gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Generates a lightning field, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG over time.":
        "Tạo ra lĩnh vực sấm sét, liên tục gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Calls down lightning, dealing <color=#fb8037>&Param1&</color> of ATK as Skill DMG to the target.":
        "Giáng xuống sấm sét, gây cho mục tiêu Sát Thương Kỹ Năng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Swings the blade in a horizontal slash, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG.":
        "Vung đao chém ngang, gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Fires multiple Shadow Scythes, each dealing <color=#fb8037>&Param1&</color> of ATK as Skill DMG to the target.":
        "Bắn ra nhiều đạo \"Liêm Ảnh\", mỗi đạo gây cho mục tiêu Sát Thương Kỹ Năng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Throws sunflower shurikens that strike the target and return, dealing <color=#fb8037>&Param1&</color> of ATK as Skill DMG when it hits the target.":
        "Phóng ra \"Phi Tiêu Hướng Dương\" bay khứ hồi, khi đánh trúng mục tiêu gây Sát Thương Kỹ Năng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Generates an exploding sunflower that fires <color=#fb8037>12</color> shurikens, each dealing <color=#fb8037>&Param1&</color> of ATK as Skill DMG.":
        "Tạo \"Hoa Hướng Dương Bộc Phát\" bắn ra <color=#fb8037>12</color> phi tiêu, mỗi phi tiêu gây Sát Thương Kỹ Năng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Throws a magic hat, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG over time.":
        "Ném mũ ma thuật, liên tục gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Generates <color=#fb8037>3</color> Soulflare Butterflies, each dealing <color=#fb8037>&Param1&</color> of ATK as Skill DMG to the target.":
        "Tạo ra <color=#fb8037>3</color> con \"Diễm Điệp\", mỗi con gây cho mục tiêu Sát Thương Kỹ Năng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Takes a photo ahead, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG. Meanwhile, summons <color=#fb8037>2</color> Pumpka Phantoms that last <color=#fb8037>10</color>s, up to <color=#fb8037>6</color> at the same time. Pumpka Phantoms automatically track and attack the target, dealing <color=#fb8037>&Param2&</color> of ATK as Skill DMG.":
        "Chụp ảnh về phía trước, gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công, đồng thời triệu hồi <color=#fb8037>2</color> \"Bí Ngô Ảnh Linh\" duy trì <color=#fb8037>10</color> giây, tối đa tồn tại cùng lúc <color=#fb8037>6</color> con. \"Bí Ngô Ảnh Linh\" tự động bám đuổi và tấn công mục tiêu, gây Sát Thương Kỹ Năng bằng <color=#fb8037>&Param2&</color> Tấn Công.",
    "Draws a magic circle that summons <color=#fb8037>1</color> Lanterna Phantom every <color=#fb8037>1</color>s. Lanterna Phantoms automatically track the target and self-destruct, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG.":
        "Vẽ pháp trận, mỗi <color=#fb8037>1</color> giây triệu hồi <color=#fb8037>1</color> \"Đèn Lồng Ảnh Linh\", \"Đèn Lồng Ảnh Linh\" tự động bám đuổi mục tiêu rồi tự bạo, gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Spins rapidly, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG.":
        "Xoay tròn thần tốc, gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Leaps and slams down <color=#fb8037>3</color> times, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG. The final strike generates <color=#fb8037>1</color> Sentry on the spot that lasts <color=#fb8037>3</color>s. The Sentry fires bullets at the target, dealing <color=#fb8037>&Param2&</color> of ATK as Skill DMG.":
        "Nhảy lên đập mạnh <color=#fb8037>3</color> lần, gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công, đòn đánh cuối cùng sẽ tạo tại chỗ <color=#fb8037>1</color> \"Trụ Canh\" duy trì <color=#fb8037>3</color> giây. \"Trụ Canh\" sẽ bắn đạn vào mục tiêu, gây Sát Thương Kỹ Năng bằng <color=#fb8037>&Param2&</color> Tấn Công.",
    "Dashes to the target and slashes repeatedly, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG multiple times, and gains <color=#fb8037>1</color> Sweep Mark.":
        "Lướt tới vị trí mục tiêu chém liên hoàn, gây nhiều đợt Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công, đồng thời nhận <color=#fb8037>1</color> \"Dấu Ấn Quét Dọn\".",
    "Wields the long blade to perform Cycling Slashes, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG multiple times, and gains <color=#fb8037>1</color> Sweep Mark.":
        "Vung trường đao chém xoay tròn tuần hoàn, gây nhiều đợt Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công, đồng thời nhận <color=#fb8037>1</color> \"Dấu Ấn Quét Dọn\".",
    "Breathes fire forward, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG over time.":
        "Phun lửa về phía trước, liên tục gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Summons <color=#fb8037>1</color> Crimson Dragon that lasts <color=#fb8037>5</color>s. The Crimson Dragon continuously attacks the target, and upon death, charges at the target and self-destructs, dealing <color=#fb8037>&Param2&</color> of ATK as AoE Skill DMG.":
        "Triệu hồi <color=#fb8037>1</color> \"Xích Long\" duy trì <color=#fb8037>5</color> giây. \"Xích Long\" sẽ liên tục tấn công mục tiêu, khi tử trận sẽ lao vào mục tiêu tự bạo gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param2&</color> Tấn Công.",
    "Moves quickly and then shoots, dealing <color=#fb8037>&Param1&</color> of ATK as Skill DMG when it hits the target, and sets off a fan-shaped blast to the rear that deals <color=#fb8037>&Param2&</color> of ATK as AoE Skill DMG.":
        "Di chuyển thần tốc rồi khai hỏa, khi bắn trúng mục tiêu gây Sát Thương Kỹ Năng bằng <color=#fb8037>&Param1&</color> Tấn Công, đồng thời kích nổ hình quạt phía sau gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param2&</color> Tấn Công.",
    "Generates <color=#fb8037>1</color> forward-moving Weeping Skies, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG over time.":
        "Tạo ra <color=#fb8037>1</color> dải \"Toái Vũ\" tiến về phía trước, liên tục gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Launches a fishcake, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG. Then lures Boss Shark in to devour it, dealing <color=#fb8037>&Param2&</color> of ATK as AoE Skill DMG.":
        "Bắn bánh quy cá gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công, sau đó dụ \"Cá Mập Đại Ca\" tới nuốt chửng, gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param2&</color> Tấn Công.",
    "Swings the chain, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG multiple times, and lures in Boss Shark to deal <color=#fb8037>&Param2&</color> of ATK as AoE Skill DMG. Finally, rides Boss Shark to slam the ground, dealing <color=#fb8037>&Param3&</color> of ATK as AoE Skill DMG.":
        "Vung xích sắt gây nhiều đợt Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công, đồng thời kéo \"Cá Mập Đại Ca\" tới gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param2&</color> Tấn Công, cuối cùng cưỡi \"Cá Mập Đại Ca\" đập mạnh xuống đất gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param3&</color> Tấn Công.",
    "Increases own ATK by <color=#fb8037>&Param1&</color> for <color=#fb8037>&Param2&</color>s.":
        "Tăng <color=#fb8037>&Param1&</color> Tấn Công của bản thân trong <color=#fb8037>&Param2&</color> giây.",
    "Fires three-round bursts, each shot dealing <color=#fb8037>&Param1&</color> of ATK as Skill DMG. Lasts <color=#fb8037>3</color>s.":
        "Bắn loạt 3 viên, mỗi phát gây Sát Thương Kỹ Năng bằng <color=#fb8037>&Param1&</color> Tấn Công, kéo dài <color=#fb8037>3</color> giây.",
    "Charges forward with a flurry of blade strikes, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG multiple times.":
        "Lao về phía trước chém liên hoàn, gây nhiều đợt Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Whirls and dashes forward, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG.":
        "Xoay người lao về phía trước, gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Fires <color=#fb8037>3</color> magic orbs, each dealing <color=#fb8037>&Param1&</color> of ATK as Skill DMG.":
        "Bắn <color=#fb8037>3</color> pháp cầu, mỗi pháp cầu gây Sát Thương Kỹ Năng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Calls down stars, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG.":
        "Triệu hồi các vì sao giáng xuống, gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Increases own DEF by <color=#fb8037>&Param1&</color> for <color=#fb8037>&Param2&</color>s.":
        "Tăng <color=#fb8037>&Param1&</color> Phòng Thủ của bản thân trong <color=#fb8037>&Param2&</color> giây.",
    "Steps forward with a thrust, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG.":
        "Lướt tới trước đâm thương xuyên phá, gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Increases own ATK SPD by <color=#fb8037>&Param1&</color> for <color=#fb8037>&Param2&</color>s.":
        "Tăng <color=#fb8037>&Param1&</color> Tốc Độ Tấn Công của bản thân trong <color=#fb8037>&Param2&</color> giây.",
    "Fires a crossbow bolt, dealing <color=#fb8037>&Param1&</color> of ATK as Skill DMG.":
        "Bắn tên nỏ, gây Sát Thương Kỹ Năng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "After casting the skill, increases the DMG of the next sniper shot by <color=#fb8037>&Param1&</color>.":
        "Sau khi thi triển kỹ năng, tăng <color=#fb8037>&Param1&</color> sát thương của phát bắn tỉa tiếp theo.",
    "Enters the field for <color=#fb8037>6</color>s and continuously snipes the target, each shot dealing <color=#fb8037>&Param1&</color> of ATK as Skill DMG.":
        "Xuất trận <color=#fb8037>6</color> giây, liên tục bắn tỉa mục tiêu, mỗi phát gây Sát Thương Kỹ Năng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Locks onto the farthest enemy target and charges, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG to targets along the way. Upon arrival, turns around and unleashes a charged draw slash, dealing <color=#fb8037>&Param2&</color> of ATK as AoE Skill DMG.":
        "Khóa định mục tiêu địch xa nhất rồi xung phong, gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công cho các mục tiêu trên đường đi, sau khi tới nơi quay người tụ lực tung nhát chém bạt đao, gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param2&</color> Tấn Công.",
    "Condenses <color=#fb8037>3</color> massive sand pillars that crash down from the sky, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG.":
        "Ngưng tụ <color=#fb8037>3</color> cột cát khổng lồ giáng xuống từ bầu trời, gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Dashes and performs a spinning rapier technique, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG.":
        "Lao tới và thi triển kiếm thuật xoay tròn, gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "Summons <color=#fb8037>3</color> hounds that track and pounce on the target, dealing <color=#fb8037>&Param1&</color> of ATK as AoE Skill DMG.":
        "Triệu hồi <color=#fb8037>3</color> con chó săn truy đuổi và vồ lấy mục tiêu, gây Sát Thương Kỹ Năng diện rộng bằng <color=#fb8037>&Param1&</color> Tấn Công.",
    "!PENDING!":
        "!PENDING!",
    "Each time an item is picked up, generates 1 Sweep Mark, stacking up to 3 times.\nWhen casting the skill, Allie wields the long blade to perform Cycling Slashes, continuously firing Frost Blades to deal AoE DMG\nWhen casting the skill, if she already has 3 Sweep Marks, additionally generates a long blade phantom after Cycling Slashes ends to deal DMG.":
        "Mỗi lần nhặt đạo cụ, sẽ bắn Hàn Băng Chi Nhận lên phía trên đồng thời tạo ra 1 \"Dấu Ấn Quét Dọn\", tối đa cộng dồn 3 tầng.\nKhi thi triển kỹ năng, Allie vung trường đao chém xoay tròn tuần hoàn, liên tục phóng Hàn Băng Chi Nhận gây sát thương diện rộng.\nKhi thi triển kỹ năng, nếu đã có 3 \"Dấu Ấn Quét Dọn\", sau khi kết thúc chém xoay tròn tuần hoàn sẽ tạo thêm tàn ảnh trường đao để gây sát thương."
}

def translate_item(it):
    table = it.get("table", "")
    key = it.get("key", "")
    en = it.get("en", "")
    zh = it.get("zh", "")
    before = it.get("current_vi", en)
    
    approved_vi = None
    reason = "Trau chuốt văn phong anime RPG/Hán-Việt kiếm hiệp, bảo toàn token kỹ thuật &ParamX& và định dạng tag"

    if table == "TrialCharacter":
        if en in TRIAL_CHARACTERS:
            approved_vi = TRIAL_CHARACTERS[en]
            reason = f"Tên Lữ Khách chuẩn theo Master Glossary: {approved_vi}"
    elif table == "TrialBuild":
        if en in TRIAL_BUILDS:
            approved_vi = TRIAL_BUILDS[en]
            reason = f"Bản ghi dùng thử nhân vật theo thuộc tính nguyên tố: {approved_vi}"
    elif table == "InfinityTowerLevel":
        if en in INFINITY_TOWER_LEVELS:
            approved_vi = INFINITY_TOWER_LEVELS[en]
            reason = f"Tên tầng Tháp Vô Tận chuẩn hóa theo hệ thống Achievement: {approved_vi}"
    elif table == "InfinityTowerAffix":
        if key.endswith(".1"):
            if en in INFINITY_TOWER_AFFIX_NAMES:
                approved_vi = INFINITY_TOWER_AFFIX_NAMES[en]
                reason = f"Từ tố Tháp Vô Tận chuẩn kiếm hiệp/anime RPG: {approved_vi}"
        else:
            if en in INFINITY_TOWER_AFFIX_DESCS:
                approved_vi = INFINITY_TOWER_AFFIX_DESCS[en]
                reason = "Mô tả cơ chế từ tố Tháp Vô Tận, bảo toàn 100% token chỉ số {X}"
    elif table == "TravelerDuelChallengeAffix":
        if key.endswith(".1"):
            if en in TRAVELER_DUEL_AFFIX_NAMES:
                approved_vi = TRAVELER_DUEL_AFFIX_NAMES[en]
                reason = f"Từ tố Thách Đấu Lữ Khách chuẩn hóa: {approved_vi}"
        else:
            if en in TRAVELER_DUEL_AFFIX_DESCS:
                approved_vi = TRAVELER_DUEL_AFFIX_DESCS[en]
                reason = "Mô tả cơ chế từ tố Thách Đấu Lữ Khách, bảo toàn tag <color> và &ParamX&"
    elif table == "MainSkill":
        if key.endswith(".1"):
            if en in MAIN_SKILL_NAMES:
                approved_vi = MAIN_SKILL_NAMES[en]
                reason = f"Tên Kỹ Năng Chính phong cách anime RPG: {approved_vi}"
        else:
            if en in MAIN_SKILL_DESCS:
                approved_vi = MAIN_SKILL_DESCS[en]
                reason = "Mô tả Kỹ Năng Chính, bảo toàn token ##Tag#ID##, tag màu và chỉ số {X}"
    elif table == "SecondarySkill":
        if key.endswith(".1"):
            if en in SECONDARY_SKILL_NAMES:
                approved_vi = SECONDARY_SKILL_NAMES[en]
                reason = f"Tên Kỹ Năng Phụ phong cách anime RPG: {approved_vi}"
        else:
            if en in SECONDARY_SKILL_DESCS:
                approved_vi = SECONDARY_SKILL_DESCS[en]
                reason = "Mô tả Kỹ Năng Phụ, bảo toàn token ##Tag#ID##, tag màu và chỉ số {X}"
    elif table == "Skill":
        if key.endswith(".1"):
            if en in SKILL_NAMES:
                approved_vi = SKILL_NAMES[en]
                reason = f"Tên kỹ năng chiến đấu anime kỳ ảo: {approved_vi}"
        else:
            if en in SKILL_DESCS:
                approved_vi = SKILL_DESCS[en]
                reason = "Mô tả chiêu thức chiến đấu, bảo toàn token màu sắc, &ParamX& và định dạng xuống dòng"

    if approved_vi is None:
        raise ValueError(f"Unmapped item: table={table}, key={key}, en={repr(en)}, zh={repr(zh)}")
        
    return {
        "table": table,
        "key": key,
        "en": en,
        "zh": zh,
        "before": before,
        "approved_vi": approved_vi,
        "reason": reason
    }

def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"Loaded {len(data)} items from {INPUT_PATH}")
    
    approved_items = []
    unmapped = []
    for it in data:
        try:
            trans = translate_item(it)
            approved_items.append(trans)
        except Exception as e:
            unmapped.append((it, str(e)))
            
    if unmapped:
        print(f"ERROR: {len(unmapped)} items could not be mapped!")
        for it, err in unmapped[:10]:
            print(" -", it.get("key"), err)
        sys.exit(1)
        
    print(f"Successfully processed all {len(approved_items)} items.")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(approved_items, f, ensure_ascii=False, indent=2)
    print(f"Saved approved items to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
