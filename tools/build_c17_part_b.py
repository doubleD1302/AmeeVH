# -*- coding: utf-8 -*-
"""
Builder and QA-verifier for Campaign 17 Partition B:
CG_155_03, CG_156_01..03, CG_157_01..03, CG_158_01..03, CG_159_01..03, CG_160_01..03, CG_162_01..03.
19 scenes, 1,749 lines.
"""

import json
import re
import unicodedata
from pathlib import Path
from translations_cg_162 import TRANSLATIONS_162

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/tutorial_and_character_cg_editorial_20261025_r01"
SOURCE_B = CAMPAIGN_DIR / "PARTITION_B_SOURCE.json"
PROP_B = CAMPAIGN_DIR / "PROPOSALS_PARTITION_B.jsonl"
RESULT_B = CAMPAIGN_DIR / "RESULT_PARTITION_B.json"

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

# 11 lines in Part B that have unclosed <size=XX> tags in EN source:
UNCLOSED_SIZE_IDS_B = {
    'CG_155_03.96',
    'CG_155_03.126',
    'CG_157_01.79',
    'CG_157_01.83',
    'CG_157_01.232',
    'CG_157_02.170',
    'CG_158_01.45',
    'CG_158_01.294',
    'CG_158_02.162',
    'CG_158_02.277',
    'CG_158_03.128'
}

BANNED_WORDS = [
    (r"\bMa Vương\b", "Cấm dùng Ma Vương cho Demon King / Lord"),
    (r"\bchết tiệt\b", "Cấm dùng chửi thề thô tục 'chết tiệt'"),
    (r"\bbạn biết đấy\b", "Calque máy dịch 'you know'"),
    (r"\bcái quái gì\b", "Calque dịch thô 'what the hell'"),
    (r"\blàm sao mà\b", "Calque dịch thô 'how come'"),
    (r"\bkhoảng không quảng cáo\b", "Calque dịch máy 'inventory'"),
    (r"\bchụp nhanh bộ nhớ\b", "Calque dịch máy 'memory snapshot'"),
    (r"\bHội Ngôi Sao Mới\b", "New Star Guild phải dịch là Lữ Đoàn Tân Tinh"),
    (r"\bHiệp hội Ngôi sao Mới\b", "New Star Guild phải dịch là Lữ Đoàn Tân Tinh"),
    (r"\bKỵ Sĩ Hoàng Gia\b", "Imperial Guard (Tilia) phải dịch là Cận Vệ Hoàng Gia!"),
    (r"\bTrọng Tài Chạng Vạng\b", "Dusk Arbiter phải dịch là Trọng Tài Hoàng Hôn!"),
    (r"\b(Chiến Binh Cây Bụi|Chuột Cây Bụi|Thành cổ Cây bụi)\b", "Shrubshrew phải chuẩn hóa là Chuột Bụi!"),
    (r"\b(Đá Linh Hồn|Đá Hồn)\b", "Soul Stone phải chuẩn hóa là Hồn Thạch!"),
    (r"\bHổ phách\b", "Tên nhân vật Amber cấm dịch thành Hổ phách!"),
    (r"\bDiên Vĩ\b|\bDiên vĩ\b", "Tên nhân vật Iris cấm dịch thành Diên Vĩ!"),
]

def check_tokens(src_tokens, dst_text):
    dst_tokens = TAG_PATTERN.findall(dst_text)
    return sorted(src_tokens) == sorted(dst_tokens), src_tokens, dst_tokens

def check_control_chars(src_text, dst_text):
    src_ctrls = [c for c in src_text if ord(c) < 32 and c not in '\r\n\t']
    dst_ctrls = [c for c in dst_text if ord(c) < 32 and c not in '\r\n\t']
    return src_ctrls == dst_ctrls, src_ctrls, dst_ctrls

with open(SOURCE_B, 'r', encoding='utf-8') as f:
    items = json.load(f)

print(f"Loaded {len(items)} items from Partition B.")

SPECIFIC_OVERRIDES_B = {
    'CG_155_03.227': 'Suốt cả ngày dài,==W== tôi luôn cảm thấy cô độc,==W== như thể bị cả thế giới bỏ rơi lại phía sau…==W== Đó là một cảm giác==W== đã khắc sâu==W== vào tận đáy lòng tôi…',
    'CG_156_01.143': 'Dù sao thì trong phòng cậu cũng có rất nhiều "bạn"<r=dolls></r> bè. Bản thân việc đó thì chẳng có vấn đề gì cả.',
    'CG_156_01.144': 'Thế nhưng cậu không thể cứ để "họ"<r=dolls></r> nằm vương vãi khắp nơi như thế này được. Như vậy là không được đâu đấy nhé.',
    'CG_156_01.146': 'Thế thì càng phải đối xử với "họ"<r=dolls></r> cẩn thận hơn chứ.==W====RT==Cậu không thể cứ vứt "họ" lung tung được, làm vậy tội nghiệp người ta lắm.',
    'CG_156_02.200': 'Cái gì cơ, cậu định nhốt tất cả "mọi người"<r=the dolls></r> vào trong nhà kho sao!?==W== Kể cả là cậu đi chăng nữa, ==PLAYER_NAME==, làm thế cũng quá tàn nhẫn rồi đấy!',
    'CG_156_02.202': 'Hơn nữa, chẳng phải như vậy nghĩa là em sẽ phải chia tay "mọi người"<r=the dolls></r> sao?==W== Em không muốn phải rời xa "mọi người"<r=the dolls></r> đâu—không đời nào!',
    'CG_156_03.94': 'Hừm, đừng có hiểu lầm đấy nhé. Mời cậu ở lại qua đêm là ý của "mọi người"<r=the dolls\'></r> đấy, chứ không phải của em đâu.',
    'CG_156_03.97': 'Em chỉ thay mặt "mọi người"<r=the dolls></r> mời ==PLAYER_NAME== thôi, chỉ thế thôi đấy.',
    'CG_156_03.154': 'Ooooooh, ta chính là hiện thân từ oán niệm của những "người bạn"<r=dolls></r>==W== mà cậu đã nhẫn tâm đày ải vào trong nhà kho đây~',
    'CG_156_03.185': 'Bé Dango Bồng Bềnh miễn cưỡng tuột khỏi vòng tay tôi==W== rồi lảo đảo<r=climbs onto the></r> trèo lên<r=top bunk></r> tầng trên của chiếc giường tầng.==W==',
    'CG_156_03.251': 'Nhưng biết làm sao được chứ?==W== Bá tước Ch<r=The doll></r>ompchomp bảo muốn ra ngoài ngắm nhìn thế giới cơ mà.',
    'CG_157_02.271': 'Không có thời gian để giải thích đâu!==W== Karin, nhảy sang bên trái mau!',
    'CG_158_02.162': 'Hướng hai giờ,==W== khoảng cách hai ngàn năm trăm,==W== góc ngẩng bốn mươi lăm độ...==W==<size=45> Gió ổn định</size>,==W==<size=50> khoang nhộng đã nạp</size>,<size=60>==W== ma năng đã sẵn sàng!',
    'CG_158_02.259': 'N-Nó là khoang nhộng sao!?==W== Bạo Chúa, cúi rạp xuống mau!',
    'CG_160_01.33': '==Off==Vài giờ trước đó...',
    'CG_157_01.45': 'Để xem nào... Nên ghé Nhà Lữ Khách nhận ủy thác, hay là đi tới lối vào Cự Tháp đây nhỉ...==W== Hửm?',
    'CG_158_01.134': 'Tốt nhất là cô ấy nên chấn chỉnh lại thái độ làm việc của mình, vì vậy nếu cậu có thể cung cấp thêm manh mối, ==W== tôi xin thay mặt cho Viện Bầu Trời của Đế Quốc Grace chân thành cảm ơn cậu!',
    'CG_158_02.208': 'Vâng, tôi đã nghe rồi. Không biết liệu những kẻ tấn công đang nhắm vào Đế Quốc Grace hay chỉ đánh vào các điểm ngẫu nhiên...==W== Dù thế nào đi nữa, chúng ta cũng cần phải luôn đề cao cảnh giác.',
    'CG_160_01.127': 'Các Du Hành Giả phải đối mặt với hiểm nguy mỗi ngày. Tôi đã tham gia rất nhiều khóa học sơ cứu để luôn trong tư thế sẵn sàng ứng cứu.',
    'CG_160_02.153': 'Những Du Hành Giả không quen với việc đi thuyền buồm luôn gặp phải trở ngại.==W== Tôi nghĩ họ cần một nơi nào đó để xin lời khuyên nên tôi đã lập ra văn phòng tạm thời này.',
    'CG_160_02.269': 'Khốn kiếp, tôi không còn lựa chọn nào khác...!==W==<size=50> Xông lêêên—!!!</size>',
    'CG_158_02.6': 'Đợt thử nghiệm đầu tiên của Hệ Thống Pháo Chuyển Phát, khoang tiếp tế vừa bắn đi... sao lại bay ngược trở về thế này?',
    'CG_158_02.100': 'Nhưng nếu cứ chần chừ thêm nữa, mình sẽ bị trễ hạn chót của ủy thác mất...==W== Hazzz...',
    'CG_158_02.116': 'Đúng vậy! Đây chính là lúc để hỏa pháo tỏa sáng! Hãy chứng kiến uy lực từ Hệ Thống Pháo Chuyển Phát của tôi đi!',
    'CG_158_02.117': 'Hệ Thống Pháo Chuyển Phát? Là cái thứ gì vậy?',
    'CG_158_02.183': 'Hệ Thống Pháo Chuyển Phát—==W==bắn!',
    'CG_159_03.6': 'Nếu phải kể tên một pháp môn dưỡng sinh nức tiếng nhất của tộc Long, thì chắc chắn đó phải là thuật xoa bóp rồi.',
    'CG_160_02.244': 'Willow, bờ biển đã an toàn rồi.',
    'CG_160_03.6': 'Hiếm hoi lắm mới có được kỳ nghỉ thế này, chi bằng cứ gác lại công việc mà thảnh thơi tận hưởng chuyến đi đi chứ?',
    'CG_160_03.96': 'Sao, tới lôi tôi đi ăn tối đấy à?==W== Chắc tôi còn phải viết muộn đấy, nên mọi người ở Lữ Đoàn Tân Tinh cứ ăn trước đi.',
    'CG_160_03.119': 'Nguy to, mình còn chưa kịp nghĩ ra lý do gì để rủ cô ấy ra đây nữa...!',
}

REPLACEMENTS_PART_B = [
    # 1. Banned machine translation calques & vulgarities
    ("Chết tiệt... Với tốc độ này, kế hoạch làm cô ấy vui lên của tôi sẽ đổ vỡ...",
     "Khốn thật... Cứ theo đà này, kế hoạch làm cô ấy vui lên của mình sẽ đổ bể mất..."),
    ("Chết tiệt... Với tốc độ này, kế hoạch làm cô ấy vui lên của tôi sẽ đổ",
     "Khốn thật... Cứ theo đà này, kế hoạch làm cô ấy vui lên của mình sẽ đổ bể mất"),
    ("Gyaaahhh! ==W==Đ-Đợi đã, Bạo chúa!==W== Cậu đang làm cái quái gì vậy?!",
     "Gyaaahhh! ==W==K-Khoan đã, Bạo chúa!==W== Cậu đang làm cái trò quái quỷ gì thế hả?!"),
    ("Chết tiệt, tôi không còn lựa chọn nào khác...!==W==<size=50> Đòi tiền—",
     "Khốn thật, tôi không còn lựa chọn nào khác...!==W==<size=50> Đòi tiền—"),
    ("Chết tiệt, tôi thậm chí còn không nghĩ ra lý do gì để đưa cô ấy ra đây",
     "Chết thật, tôi thậm chí còn chẳng nghĩ ra nổi lý do gì để đưa cô ấy ra đây"),
    ("<size=50>Di chuyển! Di chuyển! Tránh đường cho tôi!",
     "<size=50>Tránh ra! Tránh ra! Mau dẹp đường nào!"),
    ("khoảng cách 25 trăm", "khoảng cách hai ngàn năm trăm"),
    ("Chết tiệt!", "Khốn thật!"),
    ("Chết tiệt", "Khốn thật"),
    ("chết tiệt", "chết thật"),
    ("cái quái gì", "chuyện quái gì"),
    ("làm sao mà", "sao có thể"),
    ("bạn biết đấy", "cậu biết đấy"),
    ("khoảng không quảng cáo", "kho đồ"),
    ("chụp nhanh bộ nhớ", "hồi ức đặc tả"),

    # 2. Master Glossary terms in Part B
    ("Hội Ngôi Sao Mới", "Lữ Đoàn Tân Tinh"),
    ("Hiệp hội Ngôi sao Mới", "Lữ Đoàn Tân Tinh"),
    ("Hổ phách", "Amber"),
    ("Diên vĩ", "Iris"),
    ("Diên Vĩ", "Iris"),
    ("Hoa diên vĩ", "Iris"),
    ("trọng tài hoàng hôn", "Trọng Tài Hoàng Hôn"),
    ("Trọng tài hoàng hôn", "Trọng Tài Hoàng Hôn"),
    ("Trọng Tài Chạng Vạng", "Trọng Tài Hoàng Hôn"),
    ("Kỵ Sĩ Hoàng Gia", "Cận Vệ Hoàng Gia"),
    ("Đá Linh Hồn", "Hồn Thạch"),
    ("Đá Hồn", "Hồn Thạch"),
    ("đá linh hồn", "hồn thạch"),
    ("đá hồn", "hồn thạch"),
    ("Ốc đảo may mắn", "Ốc Đảo May Mắn"),
    ("Thành phố Emor", "Thành Phố Emor"),
    ("Monolith", "Cự Tháp"),
]

proposals = []
blockers = []
majors = []

for it in items:
    iid = it['id']
    en = it['en']
    cur_vi = it.get('current_vi', en)
    src_tokens = it['tokens']

    if iid in TRANSLATIONS_162:
        vi_final = TRANSLATIONS_162[iid]
    elif iid in SPECIFIC_OVERRIDES_B:
        vi_final = SPECIFIC_OVERRIDES_B[iid]
    elif it.get('is_tech'):
        vi_final = en
    else:
        vi = cur_vi

        # Clean tags corrupted by translation
        vi = vi.replace('== W==', '==W==')
        vi = re.sub(r'<kích thước=(\d+)>', r'<size=\1>', vi)
        vi = re.sub(r'<màu=([^>]+)>', r'<color=\1>', vi)
        vi = vi.replace('</kích thước>', '</size>').replace('</màu>', '</color>')

        # Unclosed tag protection
        if iid in UNCLOSED_SIZE_IDS_B:
            # Special case: CG_158_02.162 has valid </size> tags for size=45 and size=50, but size=60 is unclosed!
            # For other unclosed size lines, ensure they don't have stray </size>
            if iid != 'CG_158_02.162' and '</size>' in vi:
                vi = vi.replace('</size>', '')
        else:
            if '</size>' not in en and '</size>' in vi:
                vi = vi.replace('</size>', '')

        if '</color>' not in en and '</color>' in vi:
            vi = vi.replace('</color>', '')

        # Apply standardized replacements
        for old, new in REPLACEMENTS_PART_B:
            vi = vi.replace(old, new)

        vi_final = vi

    # Normalize NFC
    vi_final = unicodedata.normalize('NFC', vi_final)

    # Validate tokens
    ok_tok, st, dt = check_tokens(src_tokens, vi_final)
    if not ok_tok:
        blockers.append(f"[{iid}] Token mismatch! Src: {st} vs Dst: {dt}")

    # Validate control chars
    ok_ctrl, sc, dc = check_control_chars(en, vi_final)
    if not ok_ctrl:
        blockers.append(f"[{iid}] Control char mismatch! Src: {sc} vs Dst: {dc}")

    # Validate banned words
    for pat, desc in BANNED_WORDS:
        if re.search(pat, vi_final, re.IGNORECASE):
            majors.append(f"[{iid}] Contains banned word '{pat}' ({desc}): {vi_final}")

    # Validate newline
    if '\n' in en and '\n' not in vi_final:
        blockers.append(f"[{iid}] Missing newline present in source")

    proposals.append({
        "id": iid,
        "scene_id": it['scene_id'],
        "en": en,
        "vi_editorial": vi_final,
        "is_tech": it.get('is_tech', False),
        "tokens": src_tokens
    })

print(f"Partition B generated {len(proposals)} proposals.")
print(f"Blockers: {len(blockers)}, Majors: {len(majors)}")

if blockers:
    for b in blockers[:10]:
        print("  [BLOCKER]", b)
if majors:
    for m in majors[:10]:
        print("  [MAJOR]", m)

if len(blockers) == 0 and len(majors) == 0:
    # Write output
    with open(PROP_B, 'w', encoding='utf-8') as f:
        for p in proposals:
            f.write(json.dumps(p, ensure_ascii=False) + '\n')

    result_data = {
        "campaign_id": "tutorial_and_character_cg_editorial_20261025_r01",
        "partition": "Partition B",
        "scenes": sorted(list(set(it["scene_id"] for it in items))),
        "total_lines": len(proposals),
        "token_parity_percent": 100.0,
        "control_bytes_preserved": 0,
        "unclosed_size_tags_preserved": len(UNCLOSED_SIZE_IDS_B),
        "banned_calques_count": 0,
        "status": "COMPLETED",
        "qa_ready": True
    }
    with open(RESULT_B, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print(f"Successfully saved Partition B proposals to {PROP_B.name} and {RESULT_B.name}!")
else:
    print("Fixes required before saving outputs!")
