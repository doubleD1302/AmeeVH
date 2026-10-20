# -*- coding: utf-8 -*-
"""
Refine and de-formalize database tables in data.arcx:
- CharacterArchiveVoice: replace formal / stiff Sino-Vietnamese titles with natural, gaming-friendly labels
- AffinityUpReward: replace bureaucratic titles ('Trích Yếu Lý Lịch') with natural labels ('Hồ Sơ Cá Nhân')
- CharGetLines: smooth out archaic / poetry calques into natural anime speech
- AffinityLevel: ensure friendly, warm friendship tiers
"""

import json
from pathlib import Path
import re

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
ENTRIES_DIR = ROOT / "work" / "research" / "data_200_decrypted" / "entries"

# 1. Voice Titles mapping
VOICE_TITLE_REPLACEMENTS = {
    "Tuyên Ngôn Tuyệt Kỹ": "Khi Tung Chiêu",
    "Nhân Vật Gục Ngã": "Khi Bị Hạ Gục",
    "Khai Mở Tiềm Năng": "Mở Khóa Tiềm Năng",
    "Bồi Dưỡng Lữ Khách": "Nâng Cấp Lữ Khách",
    "Phát Triển Lữ Khách": "Nâng Bậc Lữ Khách",
    "Trọng Đột Biến Lữ Khách": "Tái Lập Đột Biến",
    "Lữ Khách Trưởng Thành Vượt Bậc": "Đột Phá Lữ Khách",
    "Cự Tháp: Bắt Đầu Thăng Tiến": "Tháp Sao: Khi Xuất Trận",
    "Cự Tháp: Bắt Đầu Thăng Tiến (Loại Mới)": "Tháp Sao: Xuất Trận (Kiểu Mới)",
    "Cự Tháp: Bắt Đầu Thăng Tiến (Độ Khó Mới)": "Tháp Sao: Xuất Trận (Độ Khó Mới)",
    "Cự Tháp: Biến Cố": "Tháp Sao: Biến Cố Bất Ngờ",
    "Cự Tháp: Phòng Nghỉ An Toàn": "Tháp Sao: Trạm Nghỉ Chân",
    "Cự Tháp: Trận Đánh Kết Thúc": "Tháp Sao: Kết Thúc Trận Đánh",
    "Cửa Hàng Cự Tháp": "Cửa Hàng Tháp Sao",
    "Nghe Đĩa Cổ Ngữ Thường": "Nghe Đĩa Nhạc Thường",
    "Nghe Đĩa Cổ Ngữ Đặc Biệt": "Nghe Đĩa Nhạc Đặc Biệt",
    "Tái Ngộ": "Gặp Lại",
    "Lần Đầu Gặp Gỡ": "Lần Đầu Gặp",
    "Tương Tác Nhấp Liên Tục": "Khi Chạm Liên Tục",
    "Tương Tác Treo Máy Lâu": "Khi Chờ Lâu",
    "Chạm Vào Khoảng Trống": "Chạm Màn Hình",
    "Nghi Hoặc": "Thắc Mắc",
    "Vào Trận": "Khi Vào Trận",
    "Thắng Trận": "Khi Thắng Trận",
    "Thất Bại": "Khi Thất Bại"
}

def update_character_archive_voice():
    p = ENTRIES_DIR / "00594_0xd8b61831cfe58bf2.bin"
    if not p.exists(): return 0
    data = json.loads(p.read_text(encoding="utf-8"))
    changed = 0
    for k, v in data.items():
        new_v = v
        for old, repl in VOICE_TITLE_REPLACEMENTS.items():
            if old in new_v:
                new_v = new_v.replace(old, repl)
        if new_v != v:
            data[k] = new_v
            changed += 1
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated {changed} voice titles in CharacterArchiveVoice.")
    return changed

def update_affinity_tables():
    # AffinityUpReward
    p_reward = ENTRIES_DIR / "00577_0xc0b538ebf3963e61.bin"
    changed = 0
    if p_reward.exists():
        data = json.loads(p_reward.read_text(encoding="utf-8"))
        for k, v in data.items():
            new_v = v.replace("Trích Yếu Lý Lịch", "Hồ Sơ Cá Nhân")
            new_v = new_v.replace("Truyện Ký Lữ Khách", "Ký Sự Lữ Khách")
            if new_v != v:
                data[k] = new_v
                changed += 1
        p_reward.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Updated {changed} rewards in AffinityUpReward.")

    # AffinityLevel
    p_level = ENTRIES_DIR / "00575_0x62292167a54db2f5.bin"
    if p_level.exists():
        data = json.loads(p_level.read_text(encoding="utf-8"))
        lvl_changed = 0
        for k, v in data.items():
            new_v = v.replace("Bèo Nước Gặp Nhau", "Vừa Mới Quen")
            new_v = new_v.replace("Bèo nước gặp nhau", "Vừa mới quen")
            if new_v != v:
                data[k] = new_v
                lvl_changed += 1
        p_level.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Updated {lvl_changed} levels in AffinityLevel.")

def update_chargetlines_natural():
    p = ENTRIES_DIR / "00603_0x8dcf06b298f46b28.bin"
    if not p.exists(): return
    data = json.loads(p.read_text(encoding="utf-8"))
    
    # Specific natural lines
    manual_fixes = {
        "CharGetLines.10305.1": "Lụa là dệt tựa ánh lửa, sắc vàng lấp lánh như mây bay. Trông tớ ngầu và oai phong ghê chưa nè!\nGaooo—!",
        "CharGetLines.10306.1": "Đón làn gió biển ấm áp, tranh thủ lúc lễ hội đang rộn ràng để nhìn về phía cậu... Cảm giác thật bình yên làm sao.",
        "CharGetLines.10701.1": "Báo cáo! Tớ là Tilia, kỵ sĩ cận vệ đại diện cho công lý! Hãy gia nhập cùng tớ để cùng giương cao ngọn cờ chính nghĩa nào!",
        "CharGetLines.10703.1": "Ủa... tiếng phi cơ nghe là lạ thế nào ấy... Oa oa oa, cái quái gì thế này—?!",
        "CharGetLines.10705.1": "Thắt chặt đai lưng, biến hình siêu ngầu, ý chí chiến đấu bùng cháy tựa ánh mặt trời! Khoác lên chiến giáp chính nghĩa, hóa thân kỵ sĩ bảo vệ từng góc phố— Đây chính là công lý của tớ!",
        "CharGetLines.10706.1": "Cô nàng màu nắng đã sẵn sàng tiếp sức cho cậu rồi đây~! Hãy nở nụ cười thật tươi và chuẩn bị phong độ đỉnh nhất để đón nhận thử thách tiếp theo nào!"
    }
    
    changed = 0
    for k, v in manual_fixes.items():
        if k in data and data[k] != v:
            data[k] = v
            changed += 1
            
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated {changed} lines in CharGetLines with natural anime tone.")

def main():
    print("=== DE-FORMALIZING DATA.ARCX TABLES ===")
    update_character_archive_voice()
    update_affinity_tables()
    update_chargetlines_natural()
    print("=== FINISHED REFINING DATA TABLES ===")

if __name__ == "__main__":
    main()
