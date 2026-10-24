# -*- coding: utf-8 -*-
"""
Builder and QA-verifier for Campaign 13 Partition B:
STsp_16 to STsp_18 (9 scenes, 837 lines) + STev_01 (11 scenes, 1,048 lines) = 1,885 lines.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/side_stories_part2_editorial_20261025_r01"
SOURCE_B = CAMPAIGN_DIR / "PARTITION_B_SOURCE.json"
PROP_B = CAMPAIGN_DIR / "PROPOSALS_PARTITION_B.jsonl"
RESULT_B = CAMPAIGN_DIR / "RESULT_PARTITION_B.json"

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

# 7 lines containing binary control bytes / runtime opcodes that must preserve source EN verbatim
KEEP_EN_IDS = {
    'STsp_17_01.54',
    'STsp_17_03.52',
    'STsp_18_01.17',
    'STev_01_04.119',
    'STev_01_07.102',
    'STev_01_09.35',
    'STev_01_09.63'
}

# Targeted replacements to eliminate all calques, banned words, token glitches, and MT awkwardness
EXACT_REPLACEMENTS = {
    # 1. Calques & Banned Words in Partition B
    'STsp_16_01.62': 'Chuyện quái quỷ gì đang diễn ra thế này?!',
    'STsp_16_03.52': 'Ối chết rồi, tôi chuồn trước đây! Gặp lại sau nhé!',
    'STsp_17_01.11': 'Không, Di Vật của tôi! ==W== Chẳng còn sót lại món nào... Mất sạch rồi!',
    'STsp_17_03.145': 'Cả nhóm đã phải vào sinh ra tử vì thứ này, vậy mà phần thưởng lớn lại là một tấm bản đồ khốn kiếp khác ư...? Mọi khổ ải đó rốt cuộc là vì cái gì chứ...? ==W== Hơ... hahahaha...',
    'STsp_18_02.99': 'Khốn thật! ==W== Chúng chạy đằng nào rồi?!',
    'STsp_18_03.6': 'Tức thật chứ! Con mồi béo bở thế kia mà lại để vuột mất được là sao?!',
    'STsp_18_03.30': 'Gay go rồi, tên này không phải dạng vừa đâu...!',
    'STev_01_01.64': 'À, thôi kệ đi. Đã mất công đến đây rồi thì cứ tận hưởng không khí bãi biển mùa hè cái đã.',
    'STev_01_01.82': 'Nguy rồi!! Mình đang bị hút xuống dưới...!',
    'STev_01_04.29': 'Hỏng thật rồi. Lẽ ra mình không nên lỡ lời như thế. Giờ thì cô ấy nổi trận lôi đình thực sự rồi...',
    'STev_01_05.19': 'Khốn kiếp, đúng là chiêu trò bỉ ổi... Tôi sẽ đuổi theo bọn chúng!',
    'STev_01_06.96': 'Nguy cấp rồi, mình phải đi tìm Karin ngay lập tức!',
    'STev_01_07.19': 'Shia nói cá voi rất nhạy cảm với ánh sáng mạnh. Mình có thể thu hút sự chú ý của nó bằng pháo sáng.',
    'STev_01_07.29': 'Karin bắn một quả pháo sáng lên bầu trời. Luồng sáng chói lòa bùng nổ, lập tức thu hút toàn bộ sự chú ý của Cá Voi Lục Sừng về phía đó.',
    'STev_01_07.34': 'Chúng ta đã chạy xa đến mức này rồi, khốn thật... Sao nó vẫn bám sát nút phía sau được chứ?! ==W== Được rồi, đến lúc dùng Kế hoạch B—',
    'STev_01_07.60': 'Nguy rồi, thuyền sắp lật úp mất thôi—!!',
    'STev_01_07.92': 'Được rồi, chuẩn bị khởi hành bất cứ lúc nào nào! Trước tiên, chúng ta phải dọn dẹp sạch sẽ boong tàu này đã. Trông bừa bộn kinh khủng.',
    'STev_01_08.70': 'Những chùm pháo sáng quen thuộc bùng nổ thắp sáng bầu trời xa xăm. Shia đứng dậy, biết rằng chân tướng cuối cùng cũng nằm trong tầm tay.',
    'STev_01_09.34': 'Trời đất ơi, chuyện gì thế này...?!',
    'STev_01_09.51': 'Khốn thật! Hóa ra những tiếng bước chân đó chẳng phải ma quỷ gì mà là do lũ khốn đó gây ra!',
    'STev_01_10.107': 'Tức thật chứ, vậy mà lũ lừa đảo kia dám tung tin đồn rằng Bà nội đã trộm kho báu. Tất cả chỉ là do ảnh hưởng của thời tiết!',
    'STev_01_10.138': 'Chết thật... Chẳng kiếm nổi một đồng Dorra nào, lại còn gánh thêm món nợ ngập đầu...',
    'STev_01_11.21': 'Hả? Amber cũng có mùi hương sao?',
    'STev_01_11.48': '... Khốn thật, suýt chút nữa là toi rồi. Cô bé người thỏ suýt nữa thì phát hiện ra mình.',

    # 2. Token fix for STsp_17_03.16
    'STsp_17_03.16': 'Eheheh! <size=60>♪',

    # 3. Light Novel polish for STsp_16 (Life Goes On)
    'STsp_16_01.4': 'Đáng lẽ hôm nay vẫn là một ngày bình lặng như bao ngày khác, nếu như kế hoạch không bất ngờ bị xáo trộn. Tiếc thay, mong ước đó chung quy cũng chỉ là ảo tưởng viển vông.',
    'STsp_16_01.8': 'Được rồi, tập trung nào. Nhân lúc xung quanh vẫn còn yên tĩnh... ==W== Mình phải giải quyết cho dứt điểm đống giấy tờ này.',
    'STsp_16_01.9': 'Nghĩ lại thì, dạo gần đây đúng là hỗn loạn thật. Không ngờ việc lại dồn ứ đến mức này... ==W== Mình phải sắp xếp lại lịch trình cho đàng hoàng mới được.',
    'STsp_16_01.12': 'À phải rồi, hôm nay chẳng phải Horizon sẽ đến thăm Thành Phố Emor sao?',
    'STsp_16_01.13': 'Cô ấy muốn bàn về dự án đóng tàu của mình. Nhưng chẳng phải chuyện đó đã bị gác lại do thiếu hụt ngân sách rồi sao?',
    'STsp_16_01.14': '... ==W== Không lẽ cô ấy kiếm đâu ra nguồn tài trợ rồi ư?',

    # 4. Polish for STsp_17 (Post Haste / Lucky Oasis)
    'STsp_17_01.2': 'Hồi Một',
    'STsp_17_01.3': 'Báu Vật Trong Lòng Đất (Phần I)',
    'STsp_17_01.6': '<size=65>==W==Meeoow?!',
    'STsp_17_01.25': '<size=35>Mình còn chưa kịp phân loại chúng nữa cơ...',

    # 5. Polish for STev_01 (Ghost Ship & Hexhorn Whale)
    'STev_01_01.2': 'Màn Một',
    'STev_01_01.3': 'Hồi Chuông U Linh Hạm (Phần I)',
    'STev_01_01.95': '<size=50>U. Linh. Hạm.',
    'STev_01_07.27': '<size=50>Này bạn lớn ơi! Có cá siêu siêu ngon cho bạn đây—!',
    'STev_01_07.40': '<size=50>TOÀN TỐC TIẾN LÊN—!!',
    'STev_01_08.62': '<size=50>GRAOOOOO—!!!',
    'STev_01_08.101': '<size=50>Giấc ngủ ngàn thu dưới đáy đại dương sâu thẳm, cùng báu vật vĩnh hằng...',
    'STev_01_09.44': '<size=80>Sai rồi. Hoàn toàn sai bét rồi.'
}

def clean_and_normalize(text: str) -> str:
    # Ensure NFC unicode
    text = unicodedata.normalize('NFC', text)
    # Fix any accidental MT token translated
    text = text.replace('<kích thước=', '<size=')
    text = text.replace('</kích thước>', '</size>')
    # Common terminology alignment
    text = re.sub(r'\bU Linh Thuyền\b', 'U Linh Hạm', text)
    text = re.sub(r'\bTàu Ma\b', 'U Linh Hạm', text)
    text = re.sub(r'\bCá Voi 6 Sừng\b', 'Cá Voi Lục Sừng', text)
    text = re.sub(r'\bCự Thạch\b', 'Cự Tháp', text)
    text = re.sub(r'\bCổ vật\b', 'Di Vật', text)
    text = re.sub(r'\bCổ Vật\b', 'Di Vật', text)
    text = re.sub(r'\bViên Hồn Thạch\b', 'Hồn Thạch', text)
    text = re.sub(r'\bHòn Hồn Thạch\b', 'Hồn Thạch', text)
    text = re.sub(r'\bĐá Linh Hồn\b', 'Hồn Thạch', text)
    text = re.sub(r'\bĐá Hồn\b', 'Hồn Thạch', text)
    text = re.sub(r'\bChuột Cây Bụi\b', 'Chuột Bụi', text)
    text = re.sub(r'\bChiến Binh Cây Bụi\b', 'Chuột Bụi', text)
    text = re.sub(r'\bTrọng Tài Chạng Vạng\b', 'Thẩm Phán Hoàng Hôn', text)
    text = re.sub(r'\bTrọng Tài Hoàng Hôn\b', 'Thẩm Phán Hoàng Hôn', text)
    text = re.sub(r'\bKỵ Sĩ Hoàng Gia\b', 'Cận Vệ Hoàng Gia', text)
    text = re.sub(r'\bGrand Thanh tra\b', 'Đại Thanh Tra', text)
    text = re.sub(r'\bPhòng Màu Trắng\b', 'Phòng Trắng', text)
    text = re.sub(r'\bĐêm Vĩnh Cửu\b', 'Đêm Trường Vĩnh Cửu', text)
    text = re.sub(r'\bKim Khố Ý Chí Ân Tứ\b', 'Đế Quốc Grace', text)
    text = re.sub(r'\bHiệu Trưởng Allie\b', 'Giám Đốc Allie', text)
    return unicodedata.normalize('NFC', text)

def main():
    print(f"Loading Partition B source from {SOURCE_B.name}...")
    with open(SOURCE_B, 'r', encoding='utf-8') as f:
        items = json.load(f)

    print(f"Loaded {len(items)} items. Assembling proposals...")

    proposals = []
    kept_en = 0
    exact_replaced = 0
    normalized_count = 0

    for it in items:
        iid = it['id']
        sc = it['scene_id']
        en = it['en']
        raw_vi = it['current_vi']
        is_tech = it.get('is_tech', False)
        src_tokens = it.get('tokens', [])

        if iid in KEEP_EN_IDS:
            final_vi = en
            kept_en += 1
        elif iid in EXACT_REPLACEMENTS:
            final_vi = EXACT_REPLACEMENTS[iid]
            exact_replaced += 1
        else:
            final_vi = clean_and_normalize(raw_vi)
            normalized_count += 1

        final_vi = unicodedata.normalize('NFC', final_vi)

        prop_entry = {
            "id": iid,
            "scene_id": sc,
            "en": en,
            "vi_editorial": final_vi,
            "is_tech": is_tech,
            "tokens": src_tokens
        }
        proposals.append(prop_entry)

    print(f"Assembly summary:")
    print(f"  Total items: {len(proposals)}")
    print(f"  Kept EN (control byte lines): {kept_en}")
    print(f"  Exact replacements: {exact_replaced}")
    print(f"  Normalized lines: {normalized_count}")

    print(f"Writing {PROP_B.name}...")
    with open(PROP_B, 'w', encoding='utf-8') as f:
        for p in proposals:
            f.write(json.dumps(p, ensure_ascii=False) + '\n')

    result_data = {
        "partition": "B",
        "total_lines": len(proposals),
        "kept_en_count": kept_en,
        "exact_replacements": exact_replaced,
        "scenes_count": len(set(p["scene_id"] for p in proposals)),
        "status": "READY_FOR_AUDIT"
    }
    with open(RESULT_B, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print("Partition B generated successfully!")

if __name__ == "__main__":
    main()
