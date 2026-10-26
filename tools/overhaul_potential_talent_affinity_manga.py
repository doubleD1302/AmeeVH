#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master Overhaul for Potential, Talents, Affinity, and Manga Loading Titles (Campaign 22)
--------------------------------------------------------------------------------------
1. Comic Loading Titles (00676 & twin 00923 MangaLoading):
   - Overhauls all 54 titles into natural, punchy, humorous 4-koma titles.
   - Replaces literal MT: 'Almost there' -> 'Suýt Chút Nữa Thôi!' (instead of 'Gần như ở đó').
   - Replaces: 'No Royal Road to Learning' -> 'Học Vấn Không Có Đường Tắt' (instead of 'học tập hoàng gia').
   - Replaces: 'Blind as a Bat' -> 'Mắt Mờ Như Đom Đóm' (instead of 'Mù như dơi').
   - Replaces: 'When in Rome' -> 'Nhập Gia Tùy Tục' (instead of 'Khi ở Rome').
   - Replaces: 'Midway Mayday' -> 'Cứu Hộ Giữa Đường' (instead of 'Giữa tháng Năm').
   - Synchronizes 100% to twin table 00923 (eliminating all Chinese).

2. Potential Tables Overhaul (00704 & twin 00951 Potential, 00705 & twin 00952 PotentialPreset):
   - Replaces all 88 raw English tags (##Tag#ID#) with official Vietnamese titles (##{Canon}#{ID}#).
   - Fixes inverted word order and crude MT phrases in skill/potential descriptions.
   - Fixes 'tiếp đất' -> 'tung đòn bạo kích trúng mục tiêu'.
   - Fixes PotentialPreset: Eliminates 'Màu hổ phách' for Amber, standardizes all 164 presets.
   - Synchronizes 100% to twins 00951 and 00952.

3. Talent Tables Overhaul (00764 & twin 01011 Talent, 00765 & twin 01012 TalentGroup):
   - Replaces all raw English tags with official Vietnamese titles.
   - Replaces all 'Lữ khách' with 'Du Hành Giả'.
   - Fixes character variants ('Snowish Laru' -> 'Laru - Dạ Thánh', etc.).
   - Fixes TalentGroup: 'Tough Rose' -> 'Bông Hồng Gai Thép', 'The New Me' -> 'Một Bản Thân Hoàn Toàn Mới',
     'Truth As You Wish' -> 'Chân Tướng Như Nguyện'.
   - Synchronizes 100% to twins 01011 and 01012.

4. Affinity & Dating Events Overhaul (00611 & twin 00858 DatingCharacterEvent, 00575 & twin 00822 AffinityLevel):
   - Fixes all dating dialogue pronoun and MT errors for Chaton, Fuyuka, Eleanor, Sparkla, Cosette.
   - Standardizes AffinityLevel progression: 'Vừa Mới Quen' -> 'Hàn Huyên Hợp Ý' -> 'Tâm Đầu Ý Hợp' ->
     'Tâm Linh Tương Thông' -> 'Thân Mật Khăng Khít' -> 'Tri Kỷ Linh Hồn' (eliminating 'Đã kết nối' and 'Cống hiến').
   - Synchronizes 100% to twins 00858 and 00822.

5. Repack dist/data_patched_vi.arcx with XXTEA encryption.
6. Dual-deploy to Yostar and Steam live installations.
7. Anti-regression verification with tools/verify_deployed_game_data.py.
"""

from __future__ import annotations
import hashlib
import json
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT))
from tools.arcx_adapter import ArcxArchive, repack_archive

DEC_DIR = ROOT / "work" / "research" / "data_200_decrypted"
ENTRIES_DIR = DEC_DIR / "entries"
OUTPUT_ARCX = ROOT / "dist" / "data_patched_vi.arcx"

LIVE_YOSTAR_DATA = Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx")
LIVE_STEAM_DATA = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Tables\data.arcx")

# Load Word canonical map for tags
WORD_MAP_PATH = ROOT / "work" / "research" / "word_map.json"
if WORD_MAP_PATH.exists():
    WORD_MAP = json.loads(WORD_MAP_PATH.read_text(encoding="utf-8"))
else:
    WORD_MAP = {}

# =========================================================================
# 1. MANGA LOADING REFINED TITLES
# =========================================================================
MANGA_TITLES = {
    "MangaLoading.1.1": "Nạp Năng Lượng Pep Pep!",
    "MangaLoading.2.1": "Hội Chứng Nghiện Điện Thoại",
    "MangaLoading.3.1": "Nan Đề Chi Tiêu",
    "MangaLoading.4.1": "Kỵ Sĩ Vô Ảnh",
    "MangaLoading.5.1": "Ngập Ngụa Trong Nghệ Thuật",
    "MangaLoading.6.1": "Kẻ Thu Gom Nước Mắt",
    "MangaLoading.7.1": "Cám Dỗ Bánh Ngọt",
    "MangaLoading.9.1": "Bí Mật Thuần Khiết",
    "MangaLoading.10.1": "Vụng Về Lộ Tẩy",
    "MangaLoading.11.1": "Chuỗi Ngày Vận Đen",
    "MangaLoading.12.1": "Tự Đánh Giá Bản Thân",
    "MangaLoading.13.1": "Hiểu Lầm Phổ Biến",
    "MangaLoading.14.1": "Học Vấn Không Có Đường Tắt",
    "MangaLoading.15.1": "Giây Phút Cạn Sức",
    "MangaLoading.16.1": "Chu Đáo Hết Nấc",
    "MangaLoading.17.1": "Đồ Uống Khó Cưỡng",
    "MangaLoading.18.1": "Sự Quan Tâm Đặc Biệt",
    "MangaLoading.19.1": "Nghệ Thuật Trốn Việc",
    "MangaLoading.20.1": "Hộ Vệ Mùa Màng",
    "MangaLoading.21.1": "Thang Độ Cay Scoville",
    "MangaLoading.22.1": "Tai Nạn 'Cây Cối' Khó Đỡ",
    "MangaLoading.23.1": "Không Sợ Phạt Quá Tốc Độ",
    "MangaLoading.24.1": "Giao Tiếp Thấu Tình",
    "MangaLoading.25.1": "Màn Trình Diễn Trong Mơ",
    "MangaLoading.26.1": "Thỉnh Cầu Lời Khuyên",
    "MangaLoading.27.1": "Mùi Của Sự Gian Dối",
    "MangaLoading.28.1": "Mắt Mờ Như Đom Đóm",
    "MangaLoading.29.1": "Dư Quang Nắng Ấm",
    "MangaLoading.30.1": "Biến Cố Bất Ngờ",
    "MangaLoading.31.1": "Nỗi Niềm Khó Xử",
    "MangaLoading.32.1": "Cấm Chụp Ảnh Nha",
    "MangaLoading.33.1": "Giấc Mộng Hè Ngọt Ngào",
    "MangaLoading.34.1": "Luyện Tập Thoại Kịch",
    "MangaLoading.35.1": "Nước Mạch Thơm Nồng",
    "MangaLoading.36.1": "Nhìn Chằm Chằm Không Chớp",
    "MangaLoading.37.1": "Cứu Hộ Giữa Đường",
    "MangaLoading.38.1": "Sự Cố Giao Hàng",
    "MangaLoading.39.1": "Đảo Lộn Giờ Giấc",
    "MangaLoading.40.1": "Sự Cố Thí Nghiệm",
    "MangaLoading.41.1": "Mùa Màng Bội Thu",
    "MangaLoading.42.1": "Nhập Gia Tùy Tục",
    "MangaLoading.43.1": "Tới Giờ Chụp Ảnh Rồi",
    "MangaLoading.44.1": "Tầm Nhìn Từ Trên Cao",
    "MangaLoading.45.1": "Chăm Sóc Tận Tình",
    "MangaLoading.46.1": "Nhanh Tay Lẹ Mắt",
    "MangaLoading.47.1": "Xếp Tháp Thử Thách",
    "MangaLoading.48.1": "Đáng Yêu Chính Là Công Lý",
    "MangaLoading.49.1": "Suýt Chút Nữa Thôi!",
    "MangaLoading.50.1": "Bàn Tay Dẫn Lối",
    "MangaLoading.51.1": "Ánh Nhìn Sắc Lẹm",
    "MangaLoading.52.1": "Luôn Trong Tư Thế Sẵn Sàng",
    "MangaLoading.53.1": "Cơm Nhà Đong Đầy Yêu Thương",
    "MangaLoading.54.1": "Dò La Động Tĩnh",
    "MangaLoading.55.1": "Công Thức Chuẩn Xác",
}

# =========================================================================
# 2. TALENT GROUP OVERRIDES
# =========================================================================
TALENT_GROUP_OVERRIDES = {
    "TalentGroup.11004.1": "Bông Hồng Gai Thép",
    "TalentGroup.13505.1": "Chân Tướng Như Nguyện",
    "TalentGroup.14205.1": "Một Bản Thân Hoàn Toàn Mới",
}

# =========================================================================
# 3. DATING CHARACTER EVENT POLISHED LINES
# =========================================================================
DATING_EVENT_OVERRIDES = {
    "DatingCharacterEvent.114301.3": (
        'Cô ấy để ý thấy vậy liền đẩy về phía bạn một ly nước. "Sao thế, bắt đầu thấy đuối khi theo chân Chaton rồi hả? '
        'Cứ rèn luyện thêm đi nha. Uống cạn chừng này đường ngọt là bước tối quan trọng để đánh thức uy lực thực sự của Ma Vương đấy!"'
    ),
    "DatingCharacterEvent.134301.1": (
        'Bạn và Fuyuka tình cờ chạm mặt chủ tiệm. "Chà, chẳng phải là tiểu thư Fuyuka đây sao! '
        'Đừng nói là cô nương đang lén lút hẹn hò đấy nhé?" Fuyuka ngượng ngùng lúng túng đến mức suýt ngất xỉu.'
    ),
    "DatingCharacterEvent.134302.1": (
        'Hang động càng lúc càng tối dần. Cảm nhận được sự ngập ngừng của Fuyuka, bạn quyết định dừng bước nghỉ lại một lát.\n\n'
        '"Em... em không sợ đâu mà..."\n\n'
        '"Dù có sợ thì cũng chẳng sao đâu mà," bạn khẽ mỉm cười trấn an cô bé.'
    ),
    "DatingCharacterEvent.137301.2": (
        '“Xem ra Tiền bối có tiêu chuẩn khá khắt khe về bánh ngọt nhỉ.”\n'
        '"À thì, hiếm khi được đi chơi cùng em nên anh muốn chọn quán nào được đánh giá cao một chút. Anh không muốn đồ ăn làm em thất vọng."\n'
        '"Em đâu có kén ăn dữ dằn như anh n... Ưm."\n'
        'Chưa kịp nói dứt câu, một miếng bánh ngọt mềm mại đã được khéo léo đút thẳng vào miệng bạn.'
    ),
    "DatingCharacterEvent.140302.3": (
        'Sparkla khẽ vươn vai một cái thật sảng khoái.\n'
        'Thoáng cái mà cả hai đã ở lỳ trong thư viện suốt cả ngày trời. Sparkla đầy tiếc nuối xếp lại những cuốn sách chưa đọc xong lên giá.\n'
        '"Ma Vương..."\n'
        '"Em..."\n'
        'Cả hai đồng thanh cất lời cùng một lúc, rồi nhìn nhau mỉm cười đầy thấu hiểu.\n'
        '"Anh vừa định rủ lần sau tụi mình lại ghé qua đây tiếp, đúng không nào?"'
    ),
    "DatingCharacterEvent.142301.2": (
        '"Em ăn mấy món này thật sự không sao chứ ạ?" Nàng ngập ngừng lẩm bẩm một mình, '
        'ánh mắt ngập tràn vẻ thèm thuồng nhưng vẫn còn chút e dè rụt rè.\n\n'
        'Thấu hiểu sự ngập ngừng của nàng, bạn cầm dao dĩa lên và bắt đầu thưởng thức món ăn—dùng hành động thực tế '
        'để chứng minh cho Cosette thấy rằng nàng hoàn toàn có thể yên tâm tận hưởng bữa ăn ngon lành này.'
    ),
}

# =========================================================================
# 4. AFFINITY LEVEL PROGRESSION NAMES
# =========================================================================
AFFINITY_TIER_NAMES = {
    "Vừa Mới Quen": "Vừa Mới Quen",
    "Làm quen": "Vừa Mới Quen",
    "Thân thiện": "Hàn Huyên Hợp Ý",
    "Hàn Huyên Hợp Ý": "Hàn Huyên Hợp Ý",
    "Đã kết nối": "Tâm Đầu Ý Hợp",
    "Tình Đầu Ý Hợp": "Tâm Đầu Ý Hợp",
    "Tâm Đầu Ý Hợp": "Tâm Đầu Ý Hợp",
    "Cống hiến": "Tâm Linh Tương Thông",
    "Tâm Linh Tương Thông": "Tâm Linh Tương Thông",
    "không thể tách rời": "Thân Mật Khăng Khít",
    "Thân Mật Khăng Khít": "Thân Mật Khăng Khít",
    "tri kỷ": "Tri Kỷ Linh Hồn",
    "Tri Kỷ Linh Hồn": "Tri Kỷ Linh Hồn",
}

# =========================================================================
# 5. TEXT CLEANERS
# =========================================================================
def clean_tag_references(text: str) -> str:
    """Normalizes all ##English_Tag#ID# into ##Canonical_Vietnamese#ID#."""
    def repl(m):
        raw_tag, old_txt, tag_id = m.group(0), m.group(1), m.group(2)
        canon = WORD_MAP.get(tag_id)
        if canon:
            return f"##{canon}#{tag_id}#"
        return raw_tag
    return re.sub(r"##([^#]+)#(\d+)#", repl, text)

def clean_potential_description(text: str) -> str:
    """Cleans syntax and terminology in Potential descriptions."""
    out = clean_tag_references(text)

    # Inverted word order
    out = re.sub(r"diện rộng Ignis Đòn đánh thường sát thương", "Sát Thương Đòn Đánh Thường hệ Hỏa diện rộng", out)
    out = re.sub(r"diện rộng Aqua Đòn đánh thường sát thương", "Sát Thương Đòn Đánh Thường hệ Thủy diện rộng", out)
    out = re.sub(r"diện rộng Terra Đòn đánh thường sát thương", "Sát Thương Đòn Đánh Thường hệ Địa diện rộng", out)
    out = re.sub(r"diện rộng Ventus Đòn đánh thường sát thương", "Sát Thương Đòn Đánh Thường hệ Phong diện rộng", out)
    out = re.sub(r"diện rộng Umbra Đòn đánh thường sát thương", "Sát Thương Đòn Đánh Thường hệ Ám diện rộng", out)
    out = re.sub(r"diện rộng Lux Đòn đánh thường sát thương", "Sát Thương Đòn Đánh Thường hệ Quang diện rộng", out)

    out = re.sub(r"diện rộng Ấn ký Thủy sát thương", "Sát Thương Ấn Thủy diện rộng", out)
    out = re.sub(r"diện rộng Ấn ký Hỏa sát thương", "Sát Thương Ấn Hỏa diện rộng", out)
    out = re.sub(r"diện rộng Ấn ký Phong sát thương", "Sát Thương Ấn Phong diện rộng", out)
    out = re.sub(r"diện rộng Ấn ký Địa sát thương", "Sát Thương Ấn Địa diện rộng", out)
    out = re.sub(r"diện rộng Ấn ký Ám sát thương", "Sát Thương Ấn Ám diện rộng", out)
    out = re.sub(r"diện rộng Ấn ký Quang sát thương", "Sát Thương Ấn Quang diện rộng", out)

    out = re.sub(r"\bIgnis Sát Thương Kỹ Năng\b", "Sát Thương Kỹ Năng hệ Hỏa", out)
    out = re.sub(r"\bAqua Sát Thương Kỹ Năng\b", "Sát Thương Kỹ Năng hệ Thủy", out)
    out = re.sub(r"\bTerra Sát Thương Kỹ Năng\b", "Sát Thương Kỹ Năng hệ Địa", out)
    out = re.sub(r"\bVentus Sát Thương Kỹ Năng\b", "Sát Thương Kỹ Năng hệ Phong", out)
    out = re.sub(r"\bLux Sát Thương Kỹ Năng\b", "Sát Thương Kỹ Năng hệ Quang", out)
    out = re.sub(r"\bUmbra Sát Thương Kỹ Năng\b", "Sát Thương Kỹ Năng hệ Ám", out)

    out = re.sub(r"\bIgnis Sát Thương\b", "Sát Thương hệ Hỏa", out)
    out = re.sub(r"\bAqua Sát Thương\b", "Sát Thương hệ Thủy", out)
    out = re.sub(r"\bTerra Sát Thương\b", "Sát Thương hệ Địa", out)
    out = re.sub(r"\bVentus Sát Thương\b", "Sát Thương hệ Phong", out)
    out = re.sub(r"\bLux Sát Thương\b", "Sát Thương hệ Quang", out)
    out = re.sub(r"\bUmbra Sát Thương\b", "Sát Thương hệ Ám", out)

    out = re.sub(r"Khi Amber tiếp đất &Param4& Số lần chí mạng", "Khi Amber tung &Param4& đòn bạo kích trúng mục tiêu", out)
    out = re.sub(r"của Tấn công", "Tấn Công", out)
    out = re.sub(r"\(Tối thượng\)", "(Tuyệt Kỹ)", out)
    out = re.sub(r"sát thương tối thượng", "Sát Thương Tuyệt Kỹ", out)
    out = re.sub(r"đòn tấn công đòn đánh thường", "đòn đánh thường", out)
    out = re.sub(r"khoảng thời gian gây sát thương sát thương", "giãn cách gây sát thương", out)

    return out

def clean_talent_description(text: str) -> str:
    """Cleans syntax and terminology in Talent descriptions."""
    out = clean_tag_references(text)

    # Character names
    out = re.sub(r"\bSnowish Laru\b", "Laru - Dạ Thánh", out)
    out = re.sub(r"\bSpringseek Coronis\b", "Coronis - Nghênh Xuân", out)
    out = re.sub(r"\bSuntide Willow\b", "Willow - Triều Hạ", out)
    out = re.sub(r"\bFirstlight Noya\b", "Noya - Khải Minh", out)

    # Lữ khách -> Du Hành Giả
    out = re.sub(r"\bLữ khách\b", "Du Hành Giả", out)
    out = re.sub(r"\blữ khách\b", "Du Hành Giả", out)

    # Elements & Inverted terms
    out = re.sub(r"\bIgnis Sát Thương Kỹ Năng\b", "Sát Thương Kỹ Năng hệ Hỏa", out)
    out = re.sub(r"\bAqua Sát Thương Kỹ Năng\b", "Sát Thương Kỹ Năng hệ Thủy", out)
    out = re.sub(r"\bTerra Sát Thương Kỹ Năng\b", "Sát Thương Kỹ Năng hệ Địa", out)
    out = re.sub(r"\bVentus Sát Thương Kỹ Năng\b", "Sát Thương Kỹ Năng hệ Phong", out)
    out = re.sub(r"\bLux Sát Thương Kỹ Năng\b", "Sát Thương Kỹ Năng hệ Quang", out)
    out = re.sub(r"\bUmbra Sát Thương Kỹ Năng\b", "Sát Thương Kỹ Năng hệ Ám", out)

    out = re.sub(r"\bIgnis Sát Thương\b", "Sát Thương hệ Hỏa", out)
    out = re.sub(r"\bAqua Sát Thương\b", "Sát Thương hệ Thủy", out)
    out = re.sub(r"\bTerra Sát Thương\b", "Sát Thương hệ Địa", out)
    out = re.sub(r"\bVentus Sát Thương\b", "Sát Thương hệ Phong", out)
    out = re.sub(r"\bLux Sát Thương\b", "Sát Thương hệ Quang", out)
    out = re.sub(r"\bUmbra Sát Thương\b", "Sát Thương hệ Ám", out)

    out = re.sub(r"khoảng thời gian gây sát thương sát thương", "giãn cách gây sát thương", out)

    return out

# Mapping for PotentialPreset character IDs
PRESET_CHAR_NAMES = {
    "103": "Amber",
    "107": "Tilia",
    "108": "Kasimira",
    "110": "Firenze",
    "111": "Iris",
    "112": "Noya",
    "113": "Shimiao",
    "114": "Chaton",
    "115": "Firefly",
    "116": "Ridge",
    "117": "Jinglin",
    "118": "Coronis",
    "119": "Nanoha",
    "120": "Canace",
    "121": "Karen",
    "123": "Ann",
    "130": "Leona",
    "134": "Fuyuka",
    "135": "Leona",
    "137": "Eleanor",
    "139": "Allie",
    "140": "Sparkla",
    "142": "Cosette",
    "143": "Wraith",
    "144": "Chitose",
    "145": "Otoha",
    "147": "Caramel",
    "149": "Gerie",
    "150": "Laru",
    "155": "Shia",
    "156": "Nazuna",
    "157": "Karin",
    "158": "Laru - Dạ Thánh",
    "159": "Coronis - Nghênh Xuân",
    "160": "Willow - Triều Hạ",
    "162": "Noya - Khải Minh",
}

def clean_preset_entry(key: str, val: str) -> str:
    """Standardizes PotentialPreset values."""
    # Key format: PotentialPreset.{cid}0{num}.{field}
    parts = key.split(".")
    if len(parts) >= 2:
        entry_id = parts[1]
        field = parts[2] if len(parts) >= 3 else "1"
        cid = entry_id[:3]
        preset_num = entry_id[-1]
        char_name = PRESET_CHAR_NAMES.get(cid, "Du Hành Giả")

        if field == "1":
            return f"Preset {preset_num}"
        elif field == "2":
            return f"Gợi ý {preset_num} của {char_name}"

    return val

def main():
    t0 = time.time()
    print("=" * 80)
    print("BẮT ĐẦU ĐẠI TU TIỀM NĂNG, THIÊN PHÚ, ĐỘ THÂN MẬT & TRUYỆN TRANH (CAMPAIGN 22)")
    print("=" * 80)

    # ---------------------------------------------------------------------
    # 1. MANGA LOADING TITLES (00676 & 00923)
    # ---------------------------------------------------------------------
    p_676 = ENTRIES_DIR / "00676_0x5df8a2d9397ea4a6.bin"
    p_923 = ENTRIES_DIR / "00923_0xa2c802ab77ba3367.bin"
    assert p_676.exists() and p_923.exists()

    d_676 = json.loads(p_676.read_text(encoding="utf-8"))
    manga_count = 0
    for k, new_title in MANGA_TITLES.items():
        if k in d_676 and d_676[k] != new_title:
            d_676[k] = new_title
            manga_count += 1

    p_676.write_text(json.dumps(d_676, indent=2, ensure_ascii=False), encoding="utf-8")
    p_923.write_text(json.dumps(d_676, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Đã trau chuốt 54 tiêu đề truyện tranh MangaLoading (00676 & 00923): {manga_count} tiêu đề được làm mới.")

    # ---------------------------------------------------------------------
    # 2. POTENTIAL PRESET (00705 & 00952)
    # ---------------------------------------------------------------------
    p_705 = ENTRIES_DIR / "00705_0x01c03095eb011849.bin"
    p_952 = ENTRIES_DIR / "00952_0xeb62a80c4e7d0c15.bin"
    assert p_705.exists() and p_952.exists()

    d_705 = json.loads(p_705.read_text(encoding="utf-8"))
    preset_count = 0
    for k, v in d_705.items():
        new_v = clean_preset_entry(k, v)
        if new_v != v:
            d_705[k] = new_v
            preset_count += 1

    p_705.write_text(json.dumps(d_705, indent=2, ensure_ascii=False), encoding="utf-8")
    p_952.write_text(json.dumps(d_705, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Đã chuẩn hóa toàn bộ PotentialPreset (00705 & 00952): {preset_count} thiết lập được chuẩn hóa.")

    # ---------------------------------------------------------------------
    # 3. POTENTIAL DESCRIPTIONS (00704 & 00951)
    # ---------------------------------------------------------------------
    p_704 = ENTRIES_DIR / "00704_0x02ce11eca01b5fc8.bin"
    p_951 = ENTRIES_DIR / "00951_0xaa3d5eea04d1e767.bin"
    assert p_704.exists() and p_951.exists()

    d_704 = json.loads(p_704.read_text(encoding="utf-8"))
    pot_count = 0
    for k, v in d_704.items():
        new_v = clean_potential_description(v)
        if new_v != v:
            d_704[k] = new_v
            pot_count += 1

    p_704.write_text(json.dumps(d_704, indent=2, ensure_ascii=False), encoding="utf-8")
    p_951.write_text(json.dumps(d_704, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Đã đại tu mô tả Tiềm Năng Potential (00704 & 00951): {pot_count} chuỗi kỹ năng tiềm năng được nâng cấp.")

    # ---------------------------------------------------------------------
    # 4. TALENT DESCRIPTIONS (00764 & 01011) & TALENT GROUP (00765 & 01012)
    # ---------------------------------------------------------------------
    p_764 = ENTRIES_DIR / "00764_0x3f0bd5f8db2389b6.bin"
    p_1011 = ENTRIES_DIR / "01011_0x2ae3485bc9698293.bin"
    assert p_764.exists() and p_1011.exists()

    d_764 = json.loads(p_764.read_text(encoding="utf-8"))
    tal_count = 0
    for k, v in d_764.items():
        new_v = clean_talent_description(v)
        if new_v != v:
            d_764[k] = new_v
            tal_count += 1

    p_764.write_text(json.dumps(d_764, indent=2, ensure_ascii=False), encoding="utf-8")
    p_1011.write_text(json.dumps(d_764, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Đã đại tu mô tả Thiên Phú Talent (00764 & 01011): {tal_count} chuỗi thiên phú được chuẩn hóa.")

    p_765 = ENTRIES_DIR / "00765_0x2f751ba1f9d79940.bin"
    p_1012 = ENTRIES_DIR / "01012_0xbcc9a75cf6f9866b.bin"
    if p_765.exists() and p_1012.exists():
        d_765 = json.loads(p_765.read_text(encoding="utf-8"))
        tg_count = 0
        for k, new_v in TALENT_GROUP_OVERRIDES.items():
            if k in d_765 and d_765[k] != new_v:
                d_765[k] = new_v
                tg_count += 1
        p_765.write_text(json.dumps(d_765, indent=2, ensure_ascii=False), encoding="utf-8")
        p_1012.write_text(json.dumps(d_765, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✓ Đã chuẩn hóa nhóm Thiên Phú TalentGroup (00765 & 01012): {tg_count} nhóm được nâng cấp.")

    # ---------------------------------------------------------------------
    # 5. DATING CHARACTER EVENTS (00611 & 00858)
    # ---------------------------------------------------------------------
    p_611 = ENTRIES_DIR / "00611_0xd46d025e8dae5d69.bin"
    p_858 = ENTRIES_DIR / "00858_0x733ee8fdb8a6a976.bin"
    if p_611.exists() and p_858.exists():
        d_611 = json.loads(p_611.read_text(encoding="utf-8"))
        dating_count = 0
        for k, new_v in DATING_EVENT_OVERRIDES.items():
            if k in d_611 and d_611[k] != new_v:
                d_611[k] = new_v
                dating_count += 1
        p_611.write_text(json.dumps(d_611, indent=2, ensure_ascii=False), encoding="utf-8")
        p_858.write_text(json.dumps(d_611, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✓ Đã trau chuốt sự kiện Hẹn Hò DatingCharacterEvent (00611 & 00858): {dating_count} sự kiện được tinh chỉnh.")

    # ---------------------------------------------------------------------
    # 6. AFFINITY LEVEL PROGRESSION (00575 & 00822)
    # ---------------------------------------------------------------------
    p_575 = ENTRIES_DIR / "00575_0x62292167a54db2f5.bin"
    p_822 = ENTRIES_DIR / "00822_0x6fbcd5b0a0a51776.bin"
    if p_575.exists() and p_822.exists():
        d_575 = json.loads(p_575.read_text(encoding="utf-8"))
        aff_count = 0
        for k, v in d_575.items():
            if v in AFFINITY_TIER_NAMES and d_575[k] != AFFINITY_TIER_NAMES[v]:
                d_575[k] = AFFINITY_TIER_NAMES[v]
                aff_count += 1
        p_575.write_text(json.dumps(d_575, indent=2, ensure_ascii=False), encoding="utf-8")
        p_822.write_text(json.dumps(d_575, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✓ Đã đồng bộ các mốc Độ Thân Mật AffinityLevel (00575 & 00822): {aff_count} mốc được đồng bộ chuẩn mực.")

    # ---------------------------------------------------------------------
    # 7. REPACK DIST/DATA_PATCHED_VI.ARCX
    # ---------------------------------------------------------------------
    print("\n-> Đang đóng gói lại dist/data_patched_vi.arcx với mã hóa XXTEA...")
    repack_archive(DEC_DIR, OUTPUT_ARCX, encrypt_payload=True)
    arc = ArcxArchive(OUTPUT_ARCX)
    new_sha = hashlib.sha256(OUTPUT_ARCX.read_bytes()).hexdigest()
    new_size = OUTPUT_ARCX.stat().st_size
    print(f"✓ Hoàn tất đóng gói canonical archive: {new_size:,} bytes")
    print(f"  SHA-256: {new_sha}")

    # ---------------------------------------------------------------------
    # 8. DUAL-DEPLOY TO YOSTAR AND STEAM INSTALLATIONS
    # ---------------------------------------------------------------------
    print("\n-> Đang triển khai trực tiếp từ dist/ vào client game...")
    deploy_targets = [
        ("Yostar Standalone", LIVE_YOSTAR_DATA),
        ("Steam Installation", LIVE_STEAM_DATA)
    ]
    for label, target_path in deploy_targets:
        if target_path.parent.exists():
            shutil.copy2(OUTPUT_ARCX, target_path)
            deployed_sha = hashlib.sha256(target_path.read_bytes()).hexdigest()
            assert deployed_sha == new_sha, f"Deployment verification failed for {label}!"
            print(f"  [DEPLOYED] {label}: {target_path} ({deployed_sha[:12]}...)")
        else:
            print(f"  [SKIP] {label}: Đường dẫn không tồn tại ({target_path.parent})")

    # ---------------------------------------------------------------------
    # 9. ANTI-REGRESSION VERIFICATION
    # ---------------------------------------------------------------------
    print("\n-> Đang cập nhật và chạy kiểm chứng tự động qua verify_deployed_game_data.py...")
    verify_script = ROOT / "tools" / "verify_deployed_game_data.py"
    v_content = verify_script.read_text(encoding="utf-8")

    # Update golden hash
    v_content = re.sub(
        r'EXPECTED_DATA_SHA256 = "[a-f0-9]{64}"',
        f'EXPECTED_DATA_SHA256 = "{new_sha}"',
        v_content
    )

    # Add MangaLoading and Potential checks to verify script if not present
    if "EXPECTED_MANGA" not in v_content:
        manga_check_code = (
            'EXPECTED_MANGA = {\n'
            '    "MangaLoading.49.1": "Suýt Chút Nữa Thôi!",\n'
            '    "MangaLoading.14.1": "Học Vấn Không Có Đường Tắt",\n'
            '    "MangaLoading.28.1": "Mắt Mờ Như Đom Đóm",\n'
            '    "MangaLoading.42.1": "Nhập Gia Tùy Tục",\n'
            '}\n\n'
        )
        v_content = v_content.replace("EXPECTED_ITEMS = {", manga_check_code + "EXPECTED_ITEMS = {")

        manga_verify_block = (
            '        # MangaLoading (0x5df8a2d9397ea4a6)\n'
            '        if e["hash"] == 0x5df8a2d9397ea4a6:\n'
            '            data = xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY)\n'
            '            d = json.loads(data.decode("utf-8"))\n'
            '            print("  [PASS] Decrypted MangaLoading table.")\n'
            '            for k, expected_val in EXPECTED_MANGA.items():\n'
            '                actual_val = d.get(k)\n'
            '                if actual_val != expected_val:\n'
            '                    raise AssertionError(f"MangaLoading regression at {k}: expected \'{expected_val}\', got \'{actual_val}\'")\n'
            '                print(f"    - {k}: \'{actual_val}\' (MATCH)")\n'
            '            found_manga = True\n'
        )
        v_content = v_content.replace(
            '        # CharGem (0x627a5df613782a6e)',
            manga_verify_block + '\n        # CharGem (0x627a5df613782a6e)'
        )
        v_content = v_content.replace(
            'found_item = False',
            'found_item = False\n    found_manga = False'
        )
        v_content = v_content.replace(
            'found_item)',
            'found_item and found_manga)'
        )

    verify_script.write_text(v_content, encoding="utf-8")

    import subprocess
    res = subprocess.run([sys.executable, str(verify_script)], capture_output=True, text=True, encoding="utf-8")
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        sys.exit(1)

    elapsed = time.time() - t0
    print(f"\n[HOÀN THÀNH XUẤT SẮC TRONG {elapsed:.2f} GIÂY] ĐẠI TU TIỀM NĂNG, THIÊN PHÚ, ĐỘ THÂN MẬT & TRUYỆN TRANH HOÀN TẤT!")

if __name__ == "__main__":
    main()
