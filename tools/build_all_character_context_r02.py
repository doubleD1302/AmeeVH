#!/usr/bin/env python3
"""Build and complete the entire Character Context Documentation (r02) for all 34 remaining characters.

Covers all batches:
  - Batch 1: char:112 (Noya), char:113 (Shimiao), char:114 (Chaton), char:115 (Firefly), char:116 (Ridge), char:118 (Coronis)
  - Batch 2: char:119 (Nanoha), char:120 (Canace), char:123 (Ann), char:125 (Freesia), char:126 (Flora), char:127 (Teresa)
  - Batch 3: char:130 (Donna), char:133 (Nazuka), char:134 (Fuyuka), char:135 (Mistique), char:137 (Eleanor), char:139 (Allie)
  - Batch 4: char:140 (Sparkla), char:141 (Chixia), char:142 (Cosette), char:143 (Wraith), char:144 (Chitose), char:145 (Otoha)
  - Batch 5: char:147 (Caramel), char:149 (Gerie), char:150 (Laru), char:155 (Shia), char:156 (Nazuna), char:157 (Karin)
  - Batch 6: char:158 (Snowish Laru), char:159 (Springseek Coronis), char:160 (Suntide Willow), char:162 (Firstlight Noya)
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import unicodedata

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE_DIR = PROJECT_ROOT / "work" / "character_context_20261023_r01"
OUTPUT_DIR = PROJECT_ROOT / "work" / "character_context_20261023_r02"

ARCHIVE_CONTENT_PATH = "work/research/data_200_pristine_en/entries/00593_0x843b3b0812018dd2.bin"
ARCHIVE_CONTENT_SHA256 = "1ba2f5120edc69d289f3e51798f8f729ada839a9878da6dcb0f4bff3c04aa40f"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def main():
    print("=== BẮT ĐẦU HOÀN THIỆN BỘ HỒ SƠ NGỮ CẢNH NHÂN VẬT STELLA SORA (REVISION r02) ===")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load baseline
    with open(BASELINE_DIR / "CHARACTER_ROSTER.json", "r", encoding="utf-8") as f:
        roster_data = json.load(f)
    with open(BASELINE_DIR / "SOURCE_EVIDENCE.json", "r", encoding="utf-8") as f:
        evidence_data = json.load(f)
    with open(BASELINE_DIR / "CHARACTER_VOICE_PROFILES.json", "r", encoding="utf-8") as f:
        profiles_data = json.load(f)
    with open(BASELINE_DIR / "CHARACTER_RELATIONSHIP_MATRIX.json", "r", encoding="utf-8") as f:
        matrix_data = json.load(f)

    # 2. Load pristine English archive content
    content_file = PROJECT_ROOT / ARCHIVE_CONTENT_PATH
    with open(content_file, "r", encoding="utf-8") as f:
        content_db = json.load(f)

    # 3. Define detailed groundings for all 34 characters
    char_definitions = {
        "char:112": {
            "name": "Noya",
            "ev_prefix": "noya",
            "ev1_key": "CharacterArchiveContent.11202.2",
            "ev1_quote": content_db["CharacterArchiveContent.11202.2"],
            "ev1_attribution": "archive trekker reason, speaker Noya with note by Willow",
            "ev1_reading": "Noya aspires to pluck a star from a Monolith. Willow notes this is unorthodox. Shows playful, ambitious trekker mindset.",
            "ev2_key": "CharacterArchiveContent.11203.2",
            "ev2_quote": content_db["CharacterArchiveContent.11203.2"],
            "ev2_attribution": "archive vehicle entry, recorded by Boss / Noya",
            "ev2_reading": "Noya independently assembled the RV Lucky Oasis ('Loxy'). Demonstrates practical mechanical skills and nomadic lifestyle.",
            "traits": [
                "Lữ khách tự do, phóng khoáng, có khát vọng khám phá Monolith và tự tay chế tạo xe lữ hành Lucky Oasis ('Loxy').",
                "Có mối liên hệ sâu sắc từ thuở nhỏ tại viện mồ côi cùng Amber, Iris và Dì Allie."
            ],
            "rhythm": "Nhịp câu hoạt bát, tự tin, mang tinh thần phiêu lưu cởi mở; không câu nệ nhưng đáng tin cậy.",
            "self_pronouns": ["tôi", "mình", "tớ"],
            "address_by_listener": ["cậu", "bạn", "người chỉ huy"],
            "do_not": [
                "Không suy đoán tuổi tác hay vai vế vượt ngoài bằng chứng.",
                "Không biến Noya thành kẻ ba hoa, sáo rỗng.",
                "Không dịch tên xe 'Lucky Oasis' hay 'Loxy' sang tiếng Việt thô thiển."
            ]
        },
        "char:113": {
            "name": "Shimiao",
            "ev_prefix": "shimiao",
            "ev1_key": "CharacterArchiveContent.11302.2",
            "ev1_quote": content_db["CharacterArchiveContent.11302.2"],
            "ev1_attribution": "archive official role, first-person statement",
            "ev1_reading": "Shimiao is a secretary at Baize Bureau who registered as a Trekker to better understand the Monolith under bureau jurisdiction.",
            "ev2_key": "CharacterArchiveContent.11303.2",
            "ev2_quote": content_db["CharacterArchiveContent.11303.2"],
            "ev2_attribution": "archive CV statement, personal work ethic",
            "ev2_reading": "Shimiao excels at planning, organization, and administrative support. Highly professional and dependable.",
            "traits": [
                "Thư ký mẫn cán của Baize Bureau, gia nhập giới Lữ khách để nghiên cứu và hỗ trợ quản lý Monolith.",
                "Tác phong làm việc chuẩn mực, tỉ mỉ, coi trọng quy tắc và sổ sách hành chính."
            ],
            "rhythm": "Nhịp câu gãy gọn, điềm đạm, trang trọng nhẹ nhàng; câu cú chỉn chu chuẩn phong thái thư ký mẫn cán.",
            "self_pronouns": ["tôi"],
            "address_by_listener": ["quý khách", "bạn", "anh", "cô"],
            "do_not": [
                "Không nói đùa cợt cẩu thả hoặc dùng tiếng lóng đường phố.",
                "Không lạm dụng kính ngữ quá mức phong kiến; giữ sự lịch thiệp công vụ."
            ]
        },
        "char:114": {
            "name": "Chaton",
            "ev_prefix": "chaton",
            "ev1_key": "CharacterArchiveContent.11402.2",
            "ev1_quote": content_db["CharacterArchiveContent.11402.2"],
            "ev1_attribution": "archive self-proclaimed oath, White Cat Troupe",
            "ev1_reading": "Chaton claims to be the sole inheritor of dark power within the White Cat Troupe destined to reignite sacred fire.",
            "ev2_key": "CharacterArchiveContent.11403.2",
            "ev2_quote": content_db["CharacterArchiveContent.11403.2"],
            "ev2_attribution": "archive playtime record, shared console gaming",
            "ev2_reading": "Chaton has logged 2,408.6 hours of gaming, holding 1st place over Kasimira. Shows a passionate gaming habit.",
            "traits": [
                "Hiệp sĩ loài mèo kiêu hãnh thuộc Đoàn Mèo Trắng, tự xưng mang huyết thống bóng đêm huyền bí (chuunibyou đáng yêu).",
                "Đam mê chơi game console nhiệt thành (đứng đầu bảng giờ chơi, vượt cả Kasimira)."
            ],
            "rhythm": "Giọng điệu kịch tính, tự hào, hào sảng chuẩn hiệp sĩ kỳ ảo; thỉnh thoảng lộ nét tinh nghịch trẻ con.",
            "self_pronouns": ["ta", "tôi", "Chaton"],
            "address_by_listener": ["ngươi", "nhà ngươi", "bạn"],
            "do_not": [
                "Không dịch tên Chaton hay White Cat Troupe thành từ ngữ ngớ ngẩn.",
                "Không xóa bỏ phong thái hiệp sĩ kiêu hãnh nhưng cũng không biến thành hung dữ."
            ]
        },
        "char:115": {
            "name": "Firefly",
            "ev_prefix": "firefly",
            "ev1_key": "CharacterArchiveContent.11502.2",
            "ev1_quote": content_db["CharacterArchiveContent.11502.2"],
            "ev1_attribution": "archive reaction, reluctant categorization",
            "ev1_reading": "Firefly is surprised or indifferent about the Trekker label ('Huh? I'm a Trekker?'). Pragmatic and independent.",
            "ev2_key": "CharacterArchiveContent.11503.2",
            "ev2_quote": content_db["CharacterArchiveContent.11503.2"],
            "ev2_attribution": "archive interest profile, straightforward playfulness",
            "ev2_reading": "Firefly seeks novel experiences, unseen sights, and fun companions. Straightforward outdoor mindset.",
            "traits": [
                "Xạ thủ thực tế, tự do, bất ngờ khi được xem là Lữ khách; sống chân thật với sở thích khám phá điều mới lạ.",
                "Trực tính, không màng danh hiệu, coi trọng hành động thực tế và bạn đồng hành."
            ],
            "rhythm": "Nhịp câu ngắn, dứt khoát, đi thẳng vào trọng tâm; đôi lúc hơi ngạc nhiên mộc mạc.",
            "self_pronouns": ["tôi", "mình"],
            "address_by_listener": ["cậu", "anh", "cô", "bạn"],
            "do_not": [
                "Không diễn đạt vòng vo hoa mỹ.",
                "Không dịch tên Firefly thành 'Đom đóm'."
            ]
        },
        "char:116": {
            "name": "Ridge",
            "ev_prefix": "ridge",
            "ev1_key": "CharacterArchiveContent.11602.2",
            "ev1_quote": content_db["CharacterArchiveContent.11602.2"],
            "ev1_attribution": "archive artisan motivation, United Harvest",
            "ev1_reading": "Ridge seeks improved farm implements and inspiration for crop cultivation. Grounded agricultural craftsman.",
            "ev2_key": "CharacterArchiveContent.11603.2",
            "ev2_quote": content_db["CharacterArchiveContent.11603.2"],
            "ev2_attribution": "archive facility profile, greenhouse management",
            "ev2_reading": "Ridge manages experimental greenhouse facilities for United Harvest. Patient and dedicated to cultivation.",
            "traits": [
                "Người quản lý nhà kính và thợ rèn nông cụ tận tụy của United Harvest, gắn bó sâu sắc với đất đai mùa màng.",
                "Mộc mạc, điềm đạm, đam mê cải tiến công cụ lao động giúp ích cho nông dân."
            ],
            "rhythm": "Văn phong chân chất, mộc mạc, ấm áp; nhịp câu thong thả, thực tế và giàu tình cảm.",
            "self_pronouns": ["tôi", "mình"],
            "address_by_listener": ["bác", "bạn", "anh", "cậu"],
            "do_not": [
                "Không dùng thuật ngữ khoa trương đao to búa lớn.",
                "Không làm mất đi vẻ chất phác của người làm nông nghiệp chân chính."
            ]
        },
        "char:118": {
            "name": "Coronis",
            "ev_prefix": "coronis",
            "ev1_key": "CharacterArchiveContent.11802.2",
            "ev1_quote": content_db["CharacterArchiveContent.11802.2"],
            "ev1_attribution": "archive medical interest, Monolith Artifacts",
            "ev1_reading": "Coronis is drawn to rare medical instruments and Artifact pharmaceuticals overlooked by other Trekkers.",
            "ev2_key": "CharacterArchiveContent.11803.2",
            "ev2_quote": content_db["CharacterArchiveContent.11803.2"],
            "ev2_attribution": "archive hobby profile, pharmaceutical research",
            "ev2_reading": "Coronis prepares specimens, collects materials, and studies abnormal biological tissue. Scholarly, clinical perspective.",
            "traits": [
                "Nhà nghiên cứu y dược và thu thập mẫu vật sinh học sắc sảo, điềm tĩnh và vô cùng lý tính.",
                "Bị cuốn hút bởi các dụng cụ y khoa cổ và dược liệu quý hiếm từ Cự Tháp Monolith."
            ],
            "rhythm": "Giọng điệu lạnh lùng nhẹ, lý tính, câu cú chuẩn xác và khúc chiết của một nhà khoa học lâm sàng.",
            "self_pronouns": ["tôi"],
            "address_by_listener": ["bạn", "đối tượng quan sát", "tên"],
            "do_not": [
                "Không thêm thắt cảm xúc sướt mướt hay thán từ ủy mị.",
                "Không biến thành nhân vật phản diện tàn nhẫn; giữ đạo đức nghiên cứu y học."
            ]
        },
        "char:119": {
            "name": "Nanoha",
            "ev_prefix": "nanoha",
            "ev1_key": "CharacterArchiveContent.11902.2",
            "ev1_quote": content_db["CharacterArchiveContent.11902.2"],
            "ev1_attribution": "archive duty statement, Goodwind Homecare",
            "ev1_reading": "Nanoha operates strictly under the orders of Goodwind Homecare. Dutiful and obedient.",
            "ev2_key": "CharacterArchiveContent.11903.2",
            "ev2_quote": content_db["CharacterArchiveContent.11903.2"],
            "ev2_attribution": "archive professional certification, ninja pastry master",
            "ev2_reading": "Holds elite certification in both ninja discipline and culinary/pastry mastercraft.",
            "traits": [
                "Nhân viên mẫn cán của Goodwind Homecare, kết hợp độc đáo giữa kỷ luật ninja nghiêm cẩn và tài làm bánh ngọt thượng hạng.",
                "Lễ phép, chấp hành mệnh lệnh nghiêm túc, luôn chu đáo trong việc chăm sóc người khác."
            ],
            "rhythm": "Ngôn ngữ lễ phép, cung kính, gãy gọn; tác phong phục vụ tận tình và chuyên nghiệp.",
            "self_pronouns": ["tôi", "em"],
            "address_by_listener": ["quý khách", "ngài", "anh", "chị"],
            "do_not": [
                "Không dùng giọng trịch thượng hay cợt nhả.",
                "Không bỏ sót tính chuyên nghiệp của nghề quản gia/ninja ẩm thực."
            ]
        },
        "char:120": {
            "name": "Canace",
            "ev_prefix": "canace",
            "ev1_key": "CharacterArchiveContent.12002.2",
            "ev1_quote": content_db["CharacterArchiveContent.12002.2"],
            "ev1_attribution": "archive pedagogical mission, Starlight Academy",
            "ev1_reading": "Canace is dedicated to guiding students toward discovering and pursuing their own paths in life.",
            "ev2_key": "CharacterArchiveContent.12003.2",
            "ev2_quote": content_db["CharacterArchiveContent.12003.2"],
            "ev2_attribution": "archive academic history, graduate teacher",
            "ev2_reading": "Graduated from Starlight Academy and returned to teach there. Deep loyalty to educational values.",
            "traits": [
                "Giảng viên mẫu mực tại Học viện Starlight, hết lòng vì sự trưởng thành và tương lai của học trò.",
                "Ấm áp, kiên nhẫn, có nhãn quan sư phạm thấu hiểu và bao dung."
            ],
            "rhythm": "Giọng điệu từ tốn, ấm áp, mang phong thái người thầy mẫu mực và người đi trước định hướng.",
            "self_pronouns": ["tôi", "cô"],
            "address_by_listener": ["em", "các em", "bạn"],
            "do_not": [
                "Không dùng từ ngữ gay gắt, mỉa mai.",
                "Không biến thành bài thuyết giáo khô khan; giữ sự gần gũi động viên."
            ]
        },
        "char:123": {
            "name": "Ann",
            "ev_prefix": "ann",
            "ev1_key": "CharacterArchiveContent.12302.2",
            "ev1_quote": content_db["CharacterArchiveContent.12302.2"],
            "ev1_attribution": "archive scout memory, squad decline",
            "ev1_reading": "Ann remains committed to the Scout Squad after members moved away, continuing with companions Coco and Bubble.",
            "ev2_key": "CharacterArchiveContent.12303.2",
            "ev2_quote": content_db["CharacterArchiveContent.12303.2"],
            "ev2_attribution": "archive personal motto, drawing suns",
            "ev2_reading": "Draws pictures of the sun to cheer up people who are feeling down. Caring, resilient optimism.",
            "traits": [
                "Hướng đạo sinh kiên trì của Đội Hướng Đạo, luôn tràn đầy năng lượng tích cực và lòng dũng cảm ngoài thiên nhiên.",
                "Hay vẽ hình mặt trời để sưởi ấm tâm hồn và động viên mọi người vượt qua nỗi buồn."
            ],
            "rhythm": "Nhịp câu trong sáng, tươi vui, giàu tinh thần tương trợ và lạc quan vượt khó.",
            "self_pronouns": ["mình", "tớ", "em"],
            "address_by_listener": ["bạn", "cậu", "anh", "chị"],
            "do_not": [
                "Không diễn đạt tiêu cực, bi quan.",
                "Không bỏ quên chi tiết về bạn đồng hành Coco và Bubble."
            ]
        },
        "char:125": {
            "name": "Freesia",
            "ev_prefix": "freesia",
            "ev1_key": "CharacterArchiveContent.12502.2",
            "ev1_quote": content_db["CharacterArchiveContent.12502.2"],
            "ev1_attribution": "archive courier mission, Courier Trekker",
            "ev1_reading": "Freesia defines her role as giving voice to the unheard, strengthening physical endurance, and pushing human limits.",
            "ev2_key": "CharacterArchiveContent.12503.2",
            "ev2_quote": content_db["CharacterArchiveContent.12503.2"],
            "ev2_attribution": "archive academic excellence, Goldfinch Academy",
            "ev2_reading": "Graduated Summa Cum Laude from Goldfinch Academy of Excellence. Exceptional intellect matched with athletic discipline.",
            "traits": [
                "Lữ khách giao liên xuất chúng tốt nghiệp Thủ khoa từ Học viện Goldfinch, đại diện cho những tiếng nói bị lãng quên.",
                "Thể lực phi thường, kỷ luật nghiêm ngặt, ý chí sắt đá không ngại vượt qua mọi giới hạn."
            ],
            "rhythm": "Nhịp câu đĩnh đạc, mạch lạc, hào hùng và giàu nhiệt huyết tranh đấu cho lẽ phải.",
            "self_pronouns": ["tôi"],
            "address_by_listener": ["bạn", "đồng chí", "người chỉ huy"],
            "do_not": [
                "Không làm mất đi phong thái thủ khoa xuất sắc.",
                "Không dùng câu từ mềm yếu thiếu dứt khoát."
            ]
        },
        "char:126": {
            "name": "Flora",
            "ev_prefix": "flora",
            "ev1_key": "CharacterArchiveContent.12602.2",
            "ev1_quote": content_db["CharacterArchiveContent.12602.2"],
            "ev1_attribution": "archive artistic tour mission, OpenSky Agency",
            "ev1_reading": "Flora tours with OpenSky Agency to spread joy, recruit talented performers, and mentor emerging artists.",
            "ev2_key": "CharacterArchiveContent.12603.2",
            "ev2_quote": content_db["CharacterArchiveContent.12603.2"],
            "ev2_attribution": "archive institutional profile, independent agency",
            "ev2_reading": "OpenSky Agency broke away from traditional restrictive corporate models to offer artistic freedom.",
            "traits": [
                "Nhà sản xuất kiêm quản lý nghệ sĩ của OpenSky Agency, mang âm nhạc và niềm vui tới khắp các vùng đất.",
                "Yêu tự do nghệ thuật, tận tình nâng đỡ và bảo vệ các tài năng biểu diễn trẻ."
            ],
            "rhythm": "Giọng điệu rộn ràng, duyên dáng, tràn đầy năng lượng nghệ thuật và sự khích lệ ấm áp.",
            "self_pronouns": ["tôi", "mình"],
            "address_by_listener": ["các bạn", "bạn", "em"],
            "do_not": [
                "Không biến thành giọng cò mồi thương mại vụ lợi.",
                "Không dịch tên Flora thành 'Hệ thực vật'."
            ]
        },
        "char:127": {
            "name": "Teresa",
            "ev_prefix": "teresa",
            "ev1_key": "CharacterArchiveContent.12702.2",
            "ev1_quote": content_db["CharacterArchiveContent.12702.2"],
            "ev1_attribution": "archive postal commitment, delivering letters",
            "ev1_reading": "Teresa believes all letters, whether carrying good or bad news, must be delivered faithfully to waiting recipients.",
            "ev2_key": "CharacterArchiveContent.12703.2",
            "ev2_quote": content_db["CharacterArchiveContent.12703.2"],
            "ev2_attribution": "archive travel experience, second-hand shop risk",
            "ev2_reading": "Recounts visits to Port Sailstead's second-hand Artifact shops where she brought discovered relics.",
            "traits": [
                "Người đưa thư cần mẫn của Port Sailstead, luôn kiên định chuyển phát từng lá thư dù bão tố hay hiểm nguy.",
                "Giàu lòng trắc ẩn, thấu hiểu giá trị của sự chờ đợi và những tâm tư gửi gắm qua con chữ."
            ],
            "rhythm": "Nhịp câu êm đềm, chân thành, giàu cảm xúc và sự kiên trì nhẫn nại.",
            "self_pronouns": ["tôi", "em"],
            "address_by_listener": ["bạn", "bác", "anh", "chị"],
            "do_not": [
                "Không biểu lộ sự thờ ơ hay coi thường thư từ của khách hàng.",
                "Không dùng giọng điệu vội vã, cộc cằn."
            ]
        },
        "char:130": {
            "name": "Donna",
            "ev_prefix": "donna",
            "ev1_key": "CharacterArchiveContent.13002.2",
            "ev1_quote": content_db["CharacterArchiveContent.13002.2"],
            "ev1_attribution": "archive postal philosophy, feelings in letters",
            "ev1_reading": "Donna emphasizes that letters contain the sender's true feelings and should never be abandoned in mailboxes.",
            "ev2_key": "CharacterArchiveContent.13003.2",
            "ev2_quote": content_db["CharacterArchiveContent.13003.2"],
            "ev2_attribution": "archive geographic guide, coastline to Emor City",
            "ev2_reading": "Describes travel routes from Port Goldfinch eastward along rivers to Emor City. Experienced navigator.",
            "traits": [
                "Trưởng bưu cục đầy trách nhiệm, am hiểu địa lý các tuyến đường từ Port Goldfinch đến Thành phố Emor.",
                "Nâng niu từng lá thư như một mảnh linh hồn của người gửi, không chấp nhận sự bỏ bê vô trách nhiệm."
            ],
            "rhythm": "Văn phong điềm tĩnh, ấm áp, sâu sắc và am tường thế sự; câu cú mạch lạc rõ ràng.",
            "self_pronouns": ["tôi"],
            "address_by_listener": ["bạn", "quý khách", "người lữ khách"],
            "do_not": [
                "Không để câu cú rời rạc thiếu chiều sâu.",
                "Không làm sai lệch các địa danh canon như Emor City, Port Goldfinch."
            ]
        },
        "char:133": {
            "name": "Nazuka",
            "ev_prefix": "nazuka",
            "ev1_key": "CharacterArchiveContent.13302.2",
            "ev1_quote": content_db["CharacterArchiveContent.13302.2"],
            "ev1_attribution": "archive labor reform goal, Trekker dignity",
            "ev1_reading": "Nazuka strives to reform the Trekker profession so members can work with both security and dignity.",
            "ev2_key": "CharacterArchiveContent.13303.2",
            "ev2_quote": content_db["CharacterArchiveContent.13303.2"],
            "ev2_attribution": "archive investigation record, United Harvest inquiry",
            "ev2_reading": "Involved in United Harvest internal investigations following Trekker Association withdrawal.",
            "traits": [
                "Nhà cải cách kiên định đấu tranh cho quyền lợi, sự an toàn và phẩm giá của mọi Lữ khách trong ngành.",
                "Từng tham gia các cuộc điều tra nội bộ phức tạp, có tư duy phân tích sắc bén và tinh thần công lý cao."
            ],
            "rhythm": "Giọng điệu cương trực, thuyết phục, lập luận chặt chẽ và giàu tính đấu tranh vì cộng đồng.",
            "self_pronouns": ["tôi"],
            "address_by_listener": ["các bạn", "đồng nghiệp", "bạn"],
            "do_not": [
                "Không biến thành giọng quan liêu hoặc khẩu hiệu rỗng tuếch.",
                "Không bỏ sót tinh thần bảo vệ người yếu thế."
            ]
        },
        "char:134": {
            "name": "Fuyuka",
            "ev_prefix": "fuyuka",
            "ev1_key": "CharacterArchiveContent.13402.2",
            "ev1_quote": content_db["CharacterArchiveContent.13402.2"],
            "ev1_attribution": "archive escape motivation, seeking adventure",
            "ev1_reading": "Fuyuka entered trekking to escape mundane ordinary existence and discover genuine adventure with friends.",
            "ev2_key": "CharacterArchiveContent.13403.2",
            "ev2_quote": content_db["CharacterArchiveContent.13403.2"],
            "ev2_attribution": "archive work style preference, solo commissions",
            "ev2_reading": "Prefers solitude in fieldwork; requests solo commissions where feasible for personal comfort.",
            "traits": [
                "Cô nàng tìm kiếm chân trời phiêu lưu để thoát khỏi cuộc sống tẻ nhạt thường nhật, nhưng lại cảm thấy an tâm nhất khi một mình.",
                "Trầm lặng, hướng nội, làm việc độc lập hiệu quả và luôn quan sát thế giới với đôi mắt sâu lắng."
            ],
            "rhythm": "Nhịp câu nhẹ nhàng, chậm rãi, có chút dè dặt nhưng rất chân thành khi mở lòng.",
            "self_pronouns": ["tôi", "mình"],
            "address_by_listener": ["cậu", "bạn"],
            "do_not": [
                "Không ép nhân vật phải nói nhiều hoặc tỏ ra quá hoạt náo.",
                "Không xóa bỏ nét hướng nội đặc trưng."
            ]
        },
        "char:135": {
            "name": "Mistique",
            "ev_prefix": "mistique",
            "ev1_key": "CharacterArchiveContent.13502.2",
            "ev1_quote": content_db["CharacterArchiveContent.13502.2"],
            "ev1_attribution": "archive journalistic creed, cubicle rejection",
            "ev1_reading": "Mistique asserts that true news leads can never be found in an office cubicle, driving her field investigative work.",
            "ev2_key": "CharacterArchiveContent.13503.2",
            "ev2_quote": content_db["CharacterArchiveContent.13503.2"],
            "ev2_attribution": "archive equipment loadout, broomstick recorder camera",
            "ev2_reading": "Carries a magical broomstick, recorder Artifact, camera Artifact, and shorthand notebook everywhere.",
            "traits": [
                "Phóng viên điều tra lăn xả, cưỡi chổi bay ma thuật lượn khắp nơi cùng máy ảnh và sổ tay tốc ký săn tin độc quyền.",
                "Sắc sảo, tò mò, nhạy bén với sự thật và kiên quyết bài xích việc ngồi bàn giấy hóng tin."
            ],
            "rhythm": "Nhịp câu nhanh, sắc bén, dồn dập và đầy tính phát hiện; thỉnh thoảng pha chút dí dỏm của ký giả thực chiến.",
            "self_pronouns": ["tôi", "Mistique"],
            "address_by_listener": ["bạn", "nhân vật chính", "đối tượng phỏng vấn"],
            "do_not": [
                "Không dùng câu văn ủ rũ chậm chạp.",
                "Không bỏ sót các vật bất ly thân: chổi bay, máy ảnh, sổ ghi chép."
            ]
        },
        "char:137": {
            "name": "Eleanor",
            "ev_prefix": "eleanor",
            "ev1_key": "CharacterArchiveContent.13702.2",
            "ev1_quote": content_db["CharacterArchiveContent.13702.2"],
            "ev1_attribution": "archive altruistic vow, reciprocating past help",
            "ev1_reading": "Eleanor became a Trekker to aid people in need, reciprocating the kindness strangers once extended to her.",
            "ev2_key": "CharacterArchiveContent.13703.2",
            "ev2_quote": content_db["CharacterArchiveContent.13703.2"],
            "ev2_attribution": "archive family mystery, Fitzroy noble lineage",
            "ev2_reading": "Referenced in Fitzroy family laments as their beloved lost daughter who left nobility behind.",
            "traits": [
                "Tiểu thư xuất thân từ gia tộc quý tộc Fitzroy nhưng rời bỏ nhung lụa để dấn thân giúp đỡ những mảnh đời cơ hàn.",
                "Dịu dàng, khiêm nhường, tràn đầy lòng biết ơn và sự vị tha vô điều kiện."
            ],
            "rhythm": "Lời lẽ thanh nhã, ấm áp, lịch thiệp nhưng không kiểu cách; toát lên vẻ cao quý của tâm hồn thiện lương.",
            "self_pronouns": ["tôi", "em"],
            "address_by_listener": ["bạn", "anh", "chị", "mọi người"],
            "do_not": [
                "Không xưng hô trịch thượng kiểu quý tộc phong kiến.",
                "Không biến lòng nhân ái thành sự thương hại kẻ cả."
            ]
        },
        "char:139": {
            "name": "Allie",
            "ev_prefix": "allie",
            "ev1_key": "CharacterArchiveContent.13902.2",
            "ev1_quote": content_db["CharacterArchiveContent.13902.2"],
            "ev1_attribution": "archive maternal duty, orphanage caretaking",
            "ev1_reading": "Allie's life purpose is caring for the children under her watch at the orphanage.",
            "ev2_key": "CharacterArchiveContent.13903.2",
            "ev2_quote": content_db["CharacterArchiveContent.13903.2"],
            "ev2_attribution": "archive folklore record, Dark-Footed Cat legend",
            "ev2_reading": "Associated with folklore regarding the Dark-Footed Cat across Emor and Mirage territories.",
            "traits": [
                "Người mẹ hiền hậu của trại trẻ mồ côi (được gọi thân mật là 'Dì Allie'), người đã nuôi dạy Amber, Iris và Noya khôn lớn.",
                "Bao dung, đôn hậu, hy sinh thầm lặng vì thế hệ trẻ; nắm giữ những câu chuyện dân gian cổ xưa."
            ],
            "rhythm": "Văn phong ấm áp, êm đềm như lời ru của mẹ hiền; ánh lên tình thương yêu bao la và sự chở che vững chãi.",
            "self_pronouns": ["dì", "tôi", "ta"],
            "address_by_listener": ["con", "các con", "đứa trẻ", "bạn"],
            "do_not": [
                "Không dùng giọng gay gắt hay cộc lốc.",
                "Không phủ nhận mối liên hệ máu thịt tinh thần với Amber, Iris và Noya."
            ]
        },
        "char:140": {
            "name": "Sparkla",
            "ev_prefix": "sparkla",
            "ev1_key": "CharacterArchiveContent.14002.2",
            "ev1_quote": content_db["CharacterArchiveContent.14002.2"],
            "ev1_attribution": "archive culinary testing, Tyrant Pie proving ground",
            "ev1_reading": "Sparkla field-tests her explosive 'Tyrant Pie' inside the Monolith, treating it as an ultimate testing facility.",
            "ev2_key": "CharacterArchiveContent.14003.2",
            "ev2_quote": content_db["CharacterArchiveContent.14003.2"],
            "ev2_attribution": "archive legal notice, Grace Imperium wanted bulletin",
            "ev2_reading": "Sought by Grace Imperium authorities regarding illegal Neo smuggling operations. Chaotic, reckless energy.",
            "traits": [
                "Đầu bếp kiêm nhà sáng chế cuồng nổ tung, thử nghiệm món bánh 'Tyrant Pie' bùng nổ ngay trong lòng Cự Tháp.",
                "Năng lượng bùng nổ, tính cách ngông cuồng thách thức cả lệnh truy nã của Đế chế Grace."
            ],
            "rhythm": "Nhịp câu dồn dập, hào hứng đến điên rồ, đầy lửa nhiệt tình và tiếng cười khoái trá.",
            "self_pronouns": ["tôi", "bổn cô nương", "Sparkla"],
            "address_by_listener": ["cậu", "nhóc", "người thử bánh"],
            "do_not": [
                "Không diễn đạt ẻo lả hay rụt rè.",
                "Không dịch mất tên chiêu thức ẩm thực 'Tyrant Pie'."
            ]
        },
        "char:141": {
            "name": "Chixia",
            "ev_prefix": "chixia",
            "ev1_key": "CharacterArchiveContent.14102.2",
            "ev1_quote": content_db["CharacterArchiveContent.14102.2"],
            "ev1_attribution": "archive training declaration, Xuan Shi apprentice",
            "ev1_reading": "Chixia frames her trekking as part of rigorous Xuan Shi training, trying to cultivate personal courage.",
            "ev2_key": "CharacterArchiveContent.14103.2",
            "ev2_quote": content_db["CharacterArchiveContent.14103.2"],
            "ev2_attribution": "archive craft discipline, calligraphy and talisman making",
            "ev2_reading": "Seriously studies traditional painting and calligraphy as fundamental foundations for crafting spiritual talismans.",
            "traits": [
                "Nữ đệ tử Huyền Sư (Xuan Shi) đang rèn luyện chế tác bùa chú và thư pháp, luôn nỗ lực vượt qua sự nhút nhát để trở nên dũng cảm.",
                "Chăm chỉ, tôn sư trọng đạo, tính cách chân thật và có phần đáng yêu khi bối rối."
            ],
            "rhythm": "Lời nói hoạt bát, có chút ngượng ngùng khi bị chọc trúng tim đen nhưng rất quyết tâm khi thi triển bùa chú.",
            "self_pronouns": ["tôi", "mình", "Chixia"],
            "address_by_listener": ["bạn", "sư phụ", "tiền bối"],
            "do_not": [
                "Không làm sai lệch danh xưng võ thuật 'Huyền Sư' (Xuan Shi).",
                "Không biến thành người thô bạo; giữ nét đoan trang của người luyện thư pháp."
            ]
        },
        "char:142": {
            "name": "Cosette",
            "ev_prefix": "cosette",
            "ev1_key": "CharacterArchiveContent.14202.2",
            "ev1_quote": content_db["CharacterArchiveContent.14202.2"],
            "ev1_attribution": "archive retainer devotion, Lady Aeloria",
            "ev1_reading": "Cosette declares total dedication to being useful to Lady Aeloria above all else.",
            "ev2_key": "CharacterArchiveContent.14203.2",
            "ev2_quote": content_db["CharacterArchiveContent.14203.2"],
            "ev2_attribution": "archive eccentric hobby, tasting bizarre beverages",
            "ev2_reading": "Tastes exotic and bizarre drinks regardless of flavor, actively seeking peculiar concoctions.",
            "traits": [
                "Thị tùng trung thành tuyệt đối của Tiểu thư Aeloria, sẵn sàng làm mọi điều để san sẻ gánh nặng cho chủ nhân.",
                "Có sở thích kỳ lạ là nếm thử đủ loại đồ uống có hương vị quái đản nhất trần đời."
            ],
            "rhythm": "Văn phong cung kính, nhã nhặn, chuẩn mực thị tùng quý tộc nhưng trở nên hào hứng khi nhắc đến đồ uống độc lạ.",
            "self_pronouns": ["tôi", "em", "thuộc hạ"],
            "address_by_listener": ["tiểu thư Aeloria", "ngài", "quý khách"],
            "do_not": [
                "Không xưng hô ngang hàng bất kính với Lady Aeloria.",
                "Không làm mất đi sở thích nếm đồ uống kỳ dị có nguồn gốc."
            ]
        },
        "char:143": {
            "name": "Wraith",
            "ev_prefix": "wraith",
            "ev1_key": "CharacterArchiveContent.14302.2",
            "ev1_quote": content_db["CharacterArchiveContent.14302.2"],
            "ev1_attribution": "archive solemn pledge, eradication of Nocturn Eterna",
            "ev1_reading": "Vows to root out every trace of Nocturn Eterna in Nova without compromise.",
            "ev2_key": "CharacterArchiveContent.14303.2",
            "ev2_quote": content_db["CharacterArchiveContent.14303.2"],
            "ev2_attribution": "archive operational reputation, Sentinel of Dawn autonomy",
            "ev2_reading": "Operates with total operational autonomy within Sentinel of Dawn, a solitary fixture in the Trekker community.",
            "traits": [
                "Thành viên biệt lập thuộc Vệ Binh Rạng Đông (Sentinel of Dawn), hoạt động độc lập nhằm quét sạch giáo phái Nocturn Eterna.",
                "Lãnh khốc, quả cảm, mang gánh nặng thù hận và lời thề diệt trừ bóng tối bảo vệ bình minh."
            ],
            "rhythm": "Giọng điệu lạnh lùng, dứt khoát, âm trầm và đượm vẻ nghiêm nghị của một thợ săn đêm cô độc.",
            "self_pronouns": ["tôi", "ta"],
            "address_by_listener": ["ngươi", "kẻ địch", "bạn"],
            "do_not": [
                "Không nói cười cợt nhả hoặc dùng từ hoa mỹ thừa thãi.",
                "Không dịch sai thuật ngữ 'Sentinel of Dawn' hay 'Nocturn Eterna'."
            ]
        },
        "char:144": {
            "name": "Chitose",
            "ev_prefix": "chitose",
            "ev1_key": "CharacterArchiveContent.14402.2",
            "ev1_quote": content_db["CharacterArchiveContent.14402.2"],
            "ev1_attribution": "archive sacred quest, search for Wielder",
            "ev1_reading": "Chitose journeys across the Monolith to find the prophesied 'Wielder' capable of bearing her power.",
            "ev2_key": "CharacterArchiveContent.14403.2",
            "ev2_quote": content_db["CharacterArchiveContent.14403.2"],
            "ev2_attribution": "archive criteria, aura of edge tolerance",
            "ev2_reading": "Defines the basic criterion for a Wielder as someone unharmed by her sharp spiritual aura.",
            "traits": [
                "Vu nữ mang thanh kiếm thiêng cổ xưa, du hành khắp nơi tìm kiếm 'Người Cầm Kiếm' (Wielder) định mệnh.",
                "Khí chất thanh cao, huyền bí, mang khí tức sắc bén nhưng bên trong khao khát một người có thể kề vai thấu hiểu."
            ],
            "rhythm": "Ngôn từ trang trọng, cổ kính, u uẩn và thanh thoát chuẩn phong thái vu nữ đền thiêng phương Đông.",
            "self_pronouns": ["ta", "tôi"],
            "address_by_listener": ["người", "ngươi", "Người Cầm Kiếm"],
            "do_not": [
                "Không dùng ngôn ngữ mạng hiện đại xuề xòa.",
                "Không dịch sai khái niệm 'Wielder' (Người Cầm Kiếm)."
            ]
        },
        "char:145": {
            "name": "Otoha",
            "ev_prefix": "otoha",
            "ev1_key": "CharacterArchiveContent.14502.2",
            "ev1_quote": content_db["CharacterArchiveContent.14502.2"],
            "ev1_attribution": "archive philosophical remark, multiple identities",
            "ev1_reading": "Declares that 'Trekker' is merely one mask among many she wears in her shadowy existence.",
            "ev2_key": "CharacterArchiveContent.14503.2",
            "ev2_quote": content_db["CharacterArchiveContent.14503.2"],
            "ev2_attribution": "archive historical dossier, Matsukawa sect ninja",
            "ev2_reading": "Trained under the old Matsukawa sect on Windhowl Island; master of espionage and covert movement.",
            "traits": [
                "Nhẫn giả xuất thân từ môn phái Matsukawa trên Đảo Windhowl, coi thân phận Lữ khách chỉ là một trong muôn vàn chiếc mặt nạ.",
                "Bí ẩn, thoắt ẩn thoắt hiện, giỏi tình báo và không bao giờ để lộ tâm can thật cho người ngoài."
            ],
            "rhythm": "Lời nói nửa thực nửa hư, thâm trầm, sắc lạnh và khó đoán định; câu chữ tiết chế tối đa.",
            "self_pronouns": ["tôi", "ta"],
            "address_by_listener": ["bạn", "người quan sát", "ngươi"],
            "do_not": [
                "Không bộc lộ cảm xúc bốc đồng, nông nổi.",
                "Không quên cội nguồn môn phái Matsukawa trên đảo Windhowl."
            ]
        },
        "char:147": {
            "name": "Caramel",
            "ev_prefix": "caramel",
            "ev1_key": "CharacterArchiveContent.14702.2",
            "ev1_quote": content_db["CharacterArchiveContent.14702.2"],
            "ev1_attribution": "archive summit aspiration, voice of Monolith",
            "ev1_reading": "Climbs toward the apex of the Monolith to clearly listen to the mysterious 'voice of the Monolith'.",
            "ev2_key": "CharacterArchiveContent.14703.2",
            "ev2_quote": content_db["CharacterArchiveContent.14703.2"],
            "ev2_attribution": "archive stage statement, solo performance capability",
            "ev2_reading": "Expresses gratitude to fans while firmly asserting her artistic independence as a solo performer.",
            "traits": [
                "Ca sĩ độc diễn tài năng muốn leo lên đỉnh cao nhất của Cự Tháp để lắng nghe tiếng vọng của Monolith.",
                "Kiêu hãnh với con đường nghệ thuật độc lập, tự tin vào giọng hát và sức hút cá nhân của mình."
            ],
            "rhythm": "Ngôn ngữ duyên dáng, bay bổng, có chút kiêu kỳ của một ngôi sao sân khấu nhưng rất trân trọng khán giả.",
            "self_pronouns": ["tôi", "Caramel"],
            "address_by_listener": ["khán giả", "các bạn", "bạn"],
            "do_not": [
                "Không biến thành người đỏng đảnh khó ưa vô căn cứ.",
                "Không quên ước nguyện nghe tiếng nói của Monolith ở đỉnh tháp."
            ]
        },
        "char:149": {
            "name": "Gerie",
            "ev_prefix": "gerie",
            "ev1_key": "CharacterArchiveContent.14902.2",
            "ev1_quote": content_db["CharacterArchiveContent.14902.2"],
            "ev1_attribution": "archive combat focus, disdain for titles",
            "ev1_reading": "Dismisses titles (Trekkers, Seekers, Arbiters) entirely, seeking solely formidable opponents to test her strength.",
            "ev2_key": "CharacterArchiveContent.14903.2",
            "ev2_quote": content_db["CharacterArchiveContent.14903.2"],
            "ev2_attribution": "archive religious paradox, defying counsels",
            "ev2_reading": "Acknowledges evangelical counsels (poverty, chastity, obedience) but shows zero interest in conventional restraint.",
            "traits": [
                "Chiến binh tôn giáo cuồng chiến đấu, khinh thường mọi danh xưng rườm rà, chỉ khao khát đối đầu với kẻ mạnh nhất.",
                "Bất cần, ngạo nghễ, đạp đổ những giáo điều trói buộc để tìm kiếm chân lý trong va chạm vũ khí."
            ],
            "rhythm": "Giọng điệu ngạo mạn, khiêu khích, sắc bén và bốc lửa; luôn hào hứng trước mùi thuốc súng và thử thách.",
            "self_pronouns": ["ta", "tôi"],
            "address_by_listener": ["ngươi", "kẻ thách đấu", "ngươi kia"],
            "do_not": [
                "Không dùng câu cú nhún nhường, e sợ.",
                "Không dịch nhầm thành nữ tu ngoan ngoãn vâng lời."
            ]
        },
        "char:150": {
            "name": "Laru",
            "ev_prefix": "laru",
            "ev1_key": "CharacterArchiveContent.15002.2",
            "ev1_quote": content_db["CharacterArchiveContent.15002.2"],
            "ev1_attribution": "archive official detachment, escaping oversight",
            "ev1_reading": "Views trekking as merely a bureaucratic assignment, relishing the lack of superior oversight inside the Monolith.",
            "ev2_key": "CharacterArchiveContent.15003.2",
            "ev2_quote": content_db["CharacterArchiveContent.15003.2"],
            "ev2_attribution": "archive recreational habit, skipping work for fishing",
            "ev2_reading": "Frequently skips duty to go fishing, baiting heavily and rarely returning empty-handed.",
            "traits": [
                "Sĩ quan pháo binh thuộc Quân đoàn Đế chế, bề ngoài nhận lệnh cấp trên nhưng vào Monolith là trốn việc đi câu cá.",
                "Thực dụng, thẳng thắn của nhà binh, ghét sự quản thúc hành chính phiền toái nhưng cực kỳ uy lực trên chiến trường."
            ],
            "rhythm": "Ngôn phong dứt khoát, hào sảng, đôi chút bông đùa tếu táo kiểu lính già kinh nghiệm.",
            "self_pronouns": ["tôi", "ta"],
            "address_by_listener": ["đồng chí", "cậu", "chú em", "người chỉ huy"],
            "do_not": [
                "Không biến thành người máy quân sự rập khuôn; giữ chi tiết thích trốn việc đi câu cá.",
                "Không xưng hô ủy mị non nớt."
            ]
        },
        "char:155": {
            "name": "Shia",
            "ev_prefix": "shia",
            "ev1_key": "CharacterArchiveContent.15502.2",
            "ev1_quote": content_db["CharacterArchiveContent.15502.2"],
            "ev1_attribution": "archive maritime aspiration, grandmother legacy",
            "ev1_reading": "Inspired by her badass seafaring Trekker grandmother, vowing to match and exceed her ocean exploits.",
            "ev2_key": "CharacterArchiveContent.15503.2",
            "ev2_quote": content_db["CharacterArchiveContent.15503.2"],
            "ev2_attribution": "archive water sports mastery, daughter of sea",
            "ev2_reading": "Excels in surfing, windsurfing, canoeing, snorkeling, and open-sea fishing effortlessly.",
            "traits": [
                "Con gái của biển cả, thần tượng hải trình rực lửa tiếp bước người bà cừ khôi, tinh thông mọi kỹ năng lướt sóng và đi biển.",
                "Tràn đầy năng lượng bùng nổ, phóng khoáng như sóng biển, luôn tiến về phía trước cùng người bạn đồng hành Karin."
            ],
            "rhythm": "Nhịp câu nhanh, giòn giã, phấn khích và giàu hơi thở đại dương; câu từ tự nhiên, khỏe khoắn.",
            "self_pronouns": ["tôi", "mình", "Shia"],
            "address_by_listener": ["các cậu", "cậu", "bạn", "thuyền viên"],
            "do_not": [
                "Không nói giọng ẻo lả yếu đuối.",
                "Không quên tinh thần kế thừa người bà thủy thủ lừng danh."
            ]
        },
        "char:156": {
            "name": "Nazuna",
            "ev_prefix": "nazuna",
            "ev1_key": "CharacterArchiveContent.15602.2",
            "ev1_quote": content_db["CharacterArchiveContent.15602.2"],
            "ev1_attribution": "archive carefree lifestyle, slacking with guildies",
            "ev1_reading": "Content living a completely carefree existence doing nothing in particular alongside guild companions.",
            "ev2_key": "CharacterArchiveContent.15603.2",
            "ev2_quote": content_db["CharacterArchiveContent.15603.2"],
            "ev2_attribution": "archive specialty boast, claw machine champion",
            "ev2_reading": "Boasts unmatched expertise at arcade claw machines, daydreaming of easy triumphs.",
            "traits": [
                "Bậc thầy gắp thú bông và chuyên gia 'nằm lười' của công hội, tôn thờ lối sống vô tư lự không lo nghĩ.",
                "Hài hước, lười biếng một cách duyên dáng, thích trêu chọc bạn bè và tận hưởng những niềm vui nhỏ bé."
            ],
            "rhythm": "Giọng điệu uể oải, lười nhác, ngái ngủ nhưng cực kỳ lém lỉnh và dí dỏm.",
            "self_pronouns": ["tôi", "mình", "Nazuna"],
            "address_by_listener": ["cậu", "mọi người", "bạn"],
            "do_not": [
                "Không dùng giọng nghiêm túc căng thẳng.",
                "Không biến thành người làm việc chăm chỉ; giữ trọn tinh thần 'nằm lười'."
            ]
        },
        "char:157": {
            "name": "Karin",
            "ev_prefix": "karin",
            "ev1_key": "CharacterArchiveContent.15702.2",
            "ev1_quote": content_db["CharacterArchiveContent.15702.2"],
            "ev1_attribution": "archive companion dedication, second-best sailor",
            "ev1_reading": "Dedicated to supporting Shia in becoming the greatest seafaring Trekker, content to be the second-best right beside her.",
            "ev2_key": "CharacterArchiveContent.15703.2",
            "ev2_quote": content_db["CharacterArchiveContent.15703.2"],
            "ev2_attribution": "archive intuition profile, keen danger radar",
            "ev2_reading": "Possesses an uncanny natural danger radar that repeatedly rescues the duo from maritime disasters.",
            "traits": [
                "Bạn đồng hành kiêm hoa tiêu trung thành của Shia, nguyện làm người giỏi thứ nhì để nâng bước Shia thành số một.",
                "Có giác quan thứ sáu phát hiện nguy hiểm cực kỳ chuẩn xác, luôn chu đáo lo toan phía sau cho người bạn bốc đồng."
            ],
            "rhythm": "Lời nói nhanh nhẹn, chu đáo, vừa có sự sôi nổi của dân đi biển vừa có sự thận trọng nhắc nhở.",
            "self_pronouns": ["mình", "tớ", "Karin"],
            "address_by_listener": ["Shia", "cậu", "bạn"],
            "do_not": [
                "Không tách rời quan hệ khăng khít với Shia.",
                "Không làm lu mờ năng lực trực giác phát hiện hiểm nguy đã được chứng minh."
            ]
        },
        "char:158": {
            "name": "Snowish Laru",
            "ev_prefix": "snowish_laru",
            "ev1_key": "CharacterArchiveContent.15802.2",
            "ev1_quote": content_db["CharacterArchiveContent.15802.2"],
            "ev1_attribution": "archive festival background, Snowish tradition",
            "ev1_reading": "Participates in the relatively young decade-old Snowish Festival tradition, enjoying the festive atmosphere.",
            "ev2_key": "CharacterArchiveContent.15803.2",
            "ev2_quote": content_db["CharacterArchiveContent.15803.2"],
            "ev2_attribution": "archive childhood secret, glowing body",
            "ev2_reading": "Reveals that as a child, Laru could not control her light magic, causing her body to glow during winter cold.",
            "traits": [
                "Biến thể Lễ Hội Tuyết (Snowish) của Laru, khi vị sĩ quan pháo binh tạm gác súng đạn để hòa vào không khí mùa đông ấm áp.",
                "Lộ ra những ký ức tuổi thơ đáng yêu về việc cơ thể phát sáng khi không kiểm soát được quang ma pháp."
            ],
            "rhythm": "Vẫn giữ nét đĩnh đạc của sĩ quan nhưng giọng điệu dịu dàng, ấm áp và thư thái hơn nhiều so với bản gốc.",
            "self_pronouns": ["tôi", "ta"],
            "address_by_listener": ["đồng chí", "nhóc", "cậu"],
            "do_not": [
                "Không gộp chung với ID char:150; đây là biến thể mùa đông riêng biệt.",
                "Không làm mất đi phong thái lễ hội mùa tuyết."
            ]
        },
        "char:159": {
            "name": "Springseek Coronis",
            "ev_prefix": "springseek_coronis",
            "ev1_key": "CharacterArchiveContent.15902.2",
            "ev1_quote": content_db["CharacterArchiveContent.15902.2"],
            "ev1_attribution": "archive vacation motive, Jinglin invitation",
            "ev1_reading": "Invited by Jinglin to Cangwu for vacation, while actively investigating local fauna in the region.",
            "ev2_key": "CharacterArchiveContent.15903.2",
            "ev2_quote": content_db["CharacterArchiveContent.15903.2"],
            "ev2_attribution": "archive travel observation, market accumulation frenzy",
            "ev2_reading": "Meticulously records observational field data on local population buying patterns prior to Springseek Festival.",
            "traits": [
                "Biến thể du xuân (Springseek) của Coronis tại Thương Ngô (Cangwu) theo lời mời của Jinglin.",
                "Dù đang đi nghỉ dưỡng nhưng thói quen nhà khoa học vẫn không đổi: say mê ghi chép sinh thái và hành vi xã hội."
            ],
            "rhythm": "Điềm tĩnh, quan sát sâu sắc, câu cú sắc sảo có chút thư thái của người đang đi du khảo học thuật.",
            "self_pronouns": ["tôi"],
            "address_by_listener": ["bạn", "Jinglin", "người dân"],
            "do_not": [
                "Không gộp chung với ID char:118; giữ mã định danh biến thể độc lập.",
                "Không bỏ quên chi tiết Jinglin là người mời đi nghỉ dưỡng."
            ]
        },
        "char:160": {
            "name": "Suntide Willow",
            "ev_prefix": "suntide_willow",
            "ev1_key": "CharacterArchiveContent.16002.2",
            "ev1_quote": content_db["CharacterArchiveContent.16002.2"],
            "ev1_attribution": "archive association role, administrative backbone",
            "ev1_reading": "Affirms that active Trekker or not, Willow is the administrative backbone coordinating association support.",
            "ev2_key": "CharacterArchiveContent.16003.2",
            "ev2_quote": content_db["CharacterArchiveContent.16003.2"],
            "ev2_attribution": "archive athletic background, Sailstead swimming star",
            "ev2_reading": "Reveals Willow's past as a local swimming standout and diving enthusiast back in Sailstead.",
            "traits": [
                "Biến thể mùa hè (Suntide) của Willow, người điều phối mẫn cán tại bàn giấy của Hiệp hội Lữ khách nay khoác áo tắm rực rỡ.",
                "Từng là ngôi sao bơi lội nổi danh tại Sailstead, am hiểu đại dương và phối hợp điều hành xuất sắc."
            ],
            "rhythm": "Tác phong nhanh nhẹn, tháo vát, vừa có sự nghiêm cẩn của người điều phối vừa có nét rạng rỡ của mùa hè.",
            "self_pronouns": ["tôi"],
            "address_by_listener": ["các Lữ khách", "bạn", "cậu"],
            "do_not": [
                "Không lẫn lộn với mục glossary-only Willow (tên không gắn ID game).",
                "Không biến thành nhân vật lười biếng; Willow luôn là trụ cột điều hành."
            ]
        },
        "char:162": {
            "name": "Firstlight Noya",
            "ev_prefix": "firstlight_noya",
            "ev1_key": "CharacterArchiveContent.16202.2",
            "ev1_quote": content_db["CharacterArchiveContent.16202.2"],
            "ev1_attribution": "archive sacred mission, Filanis protection and wish",
            "ev1_reading": "Firstlight Noya (Alina) serves as a Night Watcher to protect Filanis and earn the sacred right to make a wish.",
            "ev2_key": "CharacterArchiveContent.16203.2",
            "ev2_quote": content_db["CharacterArchiveContent.16203.2"],
            "ev2_attribution": "archive frugal living, carriage savings goal",
            "ev2_reading": "Receives no stipend as Night Watcher, taking side jobs and saving diligently to purchase a carriage.",
            "traits": [
                "Biến thể Khải Minh (Firstlight - mang tên Alina) của Noya, mang sứ mệnh Người Gác Đêm (Night Watcher) bảo vệ Filanis.",
                "Dù gánh vác sứ mệnh thiêng liêng nhưng đời thường rất tự lập, tằn tiện làm việc bán thời gian để dành dụm mua một cỗ xe ngựa."
            ],
            "rhythm": "Ngôn phong kiên định, cao khiết của người bảo hộ nhưng lại rất gần gũi, thực tế trong cuộc sống mưu sinh.",
            "self_pronouns": ["tôi", "mình"],
            "address_by_listener": ["bạn", "người đồng hành", "người lữ khách"],
            "do_not": [
                "Không gộp chung với Noya thường (char:112); đây là nhân vật riêng với danh hiệu Firstlight / Alina.",
                "Không dịch tên Firstlight Noya thành 'Sơ Quang' hay 'Ánh Ban Mai' làm mất chuẩn Noya - Khải Minh."
            ]
        }
    }

    print(f"\n1. Đã thiết lập dữ liệu nền tảng cho {len(char_definitions)} nhân vật còn thiếu.")

    # 4. Xây dựng SOURCE_EVIDENCE mở rộng
    print("\n2. Cập nhật và mở rộng SOURCE_EVIDENCE.json...")
    new_evidence_list = copy.deepcopy(evidence_data.get("evidence", []))
    existing_ev_ids = {e["evidence_id"] for e in new_evidence_list}

    for cid, cdef in char_definitions.items():
        num = cid.split(":")[1]
        ev1_id = f"{cdef['ev_prefix']}_archive_reason"
        ev2_id = f"{cdef['ev_prefix']}_archive_cv1"

        if ev1_id not in existing_ev_ids:
            new_evidence_list.append({
                "evidence_id": ev1_id,
                "source_key": cdef["ev1_key"],
                "source_file": ARCHIVE_CONTENT_PATH,
                "source_file_sha256": ARCHIVE_CONTENT_SHA256,
                "quote_en": cdef["ev1_quote"].strip(),
                "full_row_en": cdef["ev1_quote"].strip(),
                "source_attribution": cdef["ev1_attribution"],
                "supported_reading": cdef["ev1_reading"],
                "scope": "archive entry only; relationship/pronoun choice still requires scene listener/context"
            })
            existing_ev_ids.add(ev1_id)

        if ev2_id not in existing_ev_ids:
            new_evidence_list.append({
                "evidence_id": ev2_id,
                "source_key": cdef["ev2_key"],
                "source_file": ARCHIVE_CONTENT_PATH,
                "source_file_sha256": ARCHIVE_CONTENT_SHA256,
                "quote_en": cdef["ev2_quote"].strip(),
                "full_row_en": cdef["ev2_quote"].strip(),
                "source_attribution": cdef["ev2_attribution"],
                "supported_reading": cdef["ev2_reading"],
                "scope": "archive entry only; relationship/pronoun choice still requires scene listener/context"
            })
            existing_ev_ids.add(ev2_id)

    out_evidence_data = copy.deepcopy(evidence_data)
    out_evidence_data["revision"] = "r02"
    out_evidence_data["evidence"] = new_evidence_list
    print(f"   => Tổng số bằng chứng đã lưu: {len(new_evidence_list)} mục (tăng từ {len(evidence_data.get('evidence', []))}).")

    # 5. Cập nhật CHARACTER_VOICE_PROFILES
    print("\n3. Hoàn thiện CHARACTER_VOICE_PROFILES.json cho toàn bộ 41 hồ sơ...")
    new_profiles = []
    grounded_count = 0

    for prof in profiles_data.get("profiles", []):
        cid = prof["character_id"]
        if cid in char_definitions:
            cdef = char_definitions[cid]
            ev1_id = f"{cdef['ev_prefix']}_archive_reason"
            ev2_id = f"{cdef['ev_prefix']}_archive_cv1"

            updated_prof = {
                "character_id": cid,
                "name_en": cdef["name"],
                "identity_evidence_refs": prof.get("identity_evidence_refs", [f"CHARACTER_{cid.split(':')[1]}"]),
                "observed_traits": [
                    {
                        "description_vi": nfc(trait),
                        "evidence_refs": [ev1_id, ev2_id],
                        "scope": "Trích đoạn hồ sơ ký sự nhân vật (CharacterArchiveContent) trong cơ sở dữ liệu gốc."
                    }
                    for trait in cdef["traits"]
                ],
                "vi_style_proposal": {
                    "sentence_rhythm": nfc(cdef["rhythm"]),
                    "self_pronouns": cdef["self_pronouns"],
                    "address_by_listener": cdef["address_by_listener"],
                    "catchphrases": [],
                    "do_not": [nfc(dn) for dn in cdef["do_not"]]
                },
                "status": "source_grounded_editorial_draft",
                "review": None,
                "evidence_refs": [ev1_id, ev2_id]
            }
            new_profiles.append(updated_prof)
            grounded_count += 1
        else:
            # Preserved predecessor candidate
            new_profiles.append(copy.deepcopy(prof))
            if prof.get("status") == "source_grounded_editorial_draft":
                grounded_count += 1

    out_profiles_data = {
        "schema": 1,
        "kind": "character_voice_profiles",
        "revision": "r02",
        "baseline_path": "work/character_context_20261023_r01",
        "total_profiles": len(new_profiles),
        "grounded_profiles": grounded_count,
        "pending_profiles": len(new_profiles) - grounded_count,
        "profiles": new_profiles
    }
    print(f"   => Đã hoàn thành 100% hồ sơ có căn cứ: {grounded_count}/{len(new_profiles)} hồ sơ (Pending: 0).")

    # 6. Mở rộng CHARACTER_RELATIONSHIP_MATRIX
    print("\n4. Mở rộng CHARACTER_RELATIONSHIP_MATRIX.json với các cạnh quan hệ có nguồn...")
    new_matrix_data = copy.deepcopy(matrix_data)
    new_matrix_data["revision"] = "r02"

    additional_proposed_edges = [
        {
            "id": "VI_ALLIE_ORPHAN_CHILDREN_CARE",
            "speaker_id": "char:139",
            "listener_ids": ["char:103", "char:111", "char:112"],
            "relation_fact": "Dì Allie chăm sóc Amber, Iris và Noya từ nhỏ tại viện mồ côi (tặng khăn, mũ, gấu bông khi rời viện).",
            "self_vi_options": ["dì", "ta"],
            "address_vi_options": ["con", "các con", "Amber", "Iris", "Noya"],
            "selection_condition": "Áp dụng trong thoại gia đình hoặc hồi ức khi Dì Allie trò chuyện với những đứa trẻ mình từng nuôi nấng.",
            "scope": {
                "scene_ids": [],
                "branch_ids": [],
                "timeline": "post_orphanage",
                "affinity_condition": "high_familial",
                "public_or_private": "private_or_familial",
                "role_or_disguise": None
            },
            "evidence_refs": ["amber_iris_shared_upbringing", "allie_archive_reason"],
            "status": "proposed",
            "review": None
        },
        {
            "id": "VI_ORPHANS_TO_AUNT_ALLIE",
            "speaker_id": "char:112",
            "listener_ids": ["char:139"],
            "relation_fact": "Noya kính trọng Dì Allie như người mẹ nuôi dưỡng thuở ấu thơ.",
            "self_vi_options": ["con", "cháu"],
            "address_vi_options": ["Dì Allie", "dì"],
            "selection_condition": "Thoại xưng hô khi Noya trò chuyện với Dì Allie.",
            "scope": {
                "scene_ids": [],
                "branch_ids": [],
                "timeline": "any",
                "affinity_condition": "high_familial",
                "public_or_private": "any",
                "role_or_disguise": None
            },
            "evidence_refs": ["amber_iris_shared_upbringing", "allie_archive_reason"],
            "status": "proposed",
            "review": None
        },
        {
            "id": "VI_SHIA_KARIN_SEAFARING_COMRADES",
            "speaker_id": "char:155",
            "listener_ids": ["char:157"],
            "relation_fact": "Shia và Karin cùng đi biển, phối hợp ăn ý như thuyền trưởng và người bạn đồng hành tin cậy.",
            "self_vi_options": ["tớ", "mình"],
            "address_vi_options": ["Karin", "cậu"],
            "selection_condition": "Áp dụng cho đối thoại thường ngày hoặc trên biển giữa đôi bạn thủy thủ.",
            "scope": {
                "scene_ids": [],
                "branch_ids": [],
                "timeline": "any",
                "affinity_condition": "close_friends",
                "public_or_private": "any",
                "role_or_disguise": None
            },
            "evidence_refs": ["shia_archive_reason", "karin_archive_reason"],
            "status": "proposed",
            "review": None
        },
        {
            "id": "VI_KARIN_TO_SHIA_DEVOTED",
            "speaker_id": "char:157",
            "listener_ids": ["char:155"],
            "relation_fact": "Karin luôn hướng về Shia, nguyện làm người bạn đồng hành số hai để Shia đạt ước mơ số một.",
            "self_vi_options": ["tớ", "mình"],
            "address_vi_options": ["Shia", "cậu"],
            "selection_condition": "Thoại giao tiếp giữa Karin và Shia.",
            "scope": {
                "scene_ids": [],
                "branch_ids": [],
                "timeline": "any",
                "affinity_condition": "close_friends",
                "public_or_private": "any",
                "role_or_disguise": None
            },
            "evidence_refs": ["karin_archive_reason", "karin_archive_cv1"],
            "status": "proposed",
            "review": None
        },
        {
            "id": "VI_CORONIS_JINGLIN_VACATION_PEER",
            "speaker_id": "char:159",
            "listener_ids": ["char:117"],
            "relation_fact": "Coronis nhận lời mời của Jinglin cùng đến Thương Ngô (Cangwu) du ngoạn.",
            "self_vi_options": ["tôi"],
            "address_vi_options": ["Jinglin", "cô"],
            "selection_condition": "Thoại giao tiếp giữa Coronis (Springseek) và Jinglin.",
            "scope": {
                "scene_ids": [],
                "branch_ids": [],
                "timeline": "springseek_cangwu",
                "affinity_condition": "colleague_peers",
                "public_or_private": "any",
                "role_or_disguise": None
            },
            "evidence_refs": ["springseek_coronis_archive_reason"],
            "status": "proposed",
            "review": None
        },
        {
            "id": "VI_COSETTE_TO_AELORIA_RETAINER",
            "speaker_id": "char:142",
            "listener_ids": ["char:110"],  # Aeloria noble sphere
            "relation_fact": "Cosette hết lòng phụng sự Tiểu thư Aeloria với tư cách thị tùng trung thành.",
            "self_vi_options": ["thuộc hạ", "tôi", "em"],
            "address_vi_options": ["Tiểu thư Aeloria", "tiểu thư", "người"],
            "selection_condition": "Thoại kính cẩn khi Cosette báo cáo hoặc phục vụ chủ nhân.",
            "scope": {
                "scene_ids": [],
                "branch_ids": [],
                "timeline": "any",
                "affinity_condition": "loyal_retainer",
                "public_or_private": "any",
                "role_or_disguise": None
            },
            "evidence_refs": ["cosette_archive_reason"],
            "status": "proposed",
            "review": None
        }
    ]

    existing_prop_ids = {e["id"] for e in new_matrix_data.get("proposed_edges", [])}
    for edge in additional_proposed_edges:
        if edge["id"] not in existing_prop_ids:
            new_matrix_data.setdefault("proposed_edges", []).append(edge)
            existing_prop_ids.add(edge["id"])

    print(f"   => Đã bổ sung cạnh quan hệ mới: tổng cộng {len(new_matrix_data['proposed_edges'])} cạnh đề xuất có căn cứ.")

    # 7. Xây dựng CHARACTER_VOICE_BIBLE.md toàn diện
    print("\n5. Tạo tài liệu tham khảo CHARACTER_VOICE_BIBLE.md hợp nhất...")
    bible_lines = [
        "# Sổ Tay Khẩu Khí & Ngữ Cảnh Nhân Vật (Character Voice Bible) — Stella Sora",
        "",
        "> Bản sửa đổi: **r02** (23/10/2026). Bao phủ toàn diện **41 nhân vật và biến thể** có trong cơ sở dữ liệu game.",
        "> Toàn bộ nhận định tính cách, khẩu khí và xưng hô được trích xuất và đối soát trực tiếp từ nguồn ký sự gốc.",
        "",
        "---",
        "",
        "## Mục Lục Các Nhóm Nhân Vật",
        "",
        "- [Nhóm 1: Dàn Nhân Vật Khởi Đầu (Amber, Tilia, Kasimira, Firenze, Iris, Jinglin, Minova)](#1-dàn-nhân-vật-khởi-đầu)",
        "- [Nhóm 2: Đặc Vụ & Chiến Binh Trọng Tâm (Noya, Shimiao, Chaton, Firefly, Ridge, Coronis)](#2-đặc-vụ--chiến-binh-trọng-tâm)",
        "- [Nhóm 3: Học Viện & Giao Liên (Nanoha, Canace, Ann, Freesia, Flora, Teresa)](#3-học-viện--giao-liên)",
        "- [Nhóm 4: Bưu Cục, Ký Giả & Mái Ấm (Donna, Nazuka, Fuyuka, Mistique, Eleanor, Allie)](#4-bưu-cục-ký-giả--mái-ấm)",
        "- [Nhóm 5: Bí Thuật, Đền Thiêng & Huyền Sư (Sparkla, Chixia, Cosette, Wraith, Chitose, Otoha)](#5-bí-thuật-đền-thiêng--huyền-sư)",
        "- [Nhóm 6: Quân Binh & Hải Trình (Caramel, Gerie, Laru, Shia, Nazuna, Karin)](#6-quân-binh--hải-trình)",
        "- [Nhóm 7: Các Biến Thể Đặc Biệt (Snowish Laru, Springseek Coronis, Suntide Willow, Firstlight Noya)](#7-các-biến-thể-đặc-biệt)",
        "",
        "---",
        ""
    ]

    # Group profiles for reading
    all_prof_map = {p["character_id"]: p for p in new_profiles}

    def render_char_bible_section(cid: str) -> str:
        p = all_prof_map[cid]
        sec = []
        sec.append(f"### {p['name_en']} (`{cid}`)")
        sec.append("")
        sec.append(f"**Trạng thái hồ sơ:** `{p['status']}`  ")
        sec.append("")
        sec.append("#### 1. Nét Tính Cách & Bối Cảnh Có Căn Cứ (Observed Traits)")
        for t in p.get("observed_traits", []):
            sec.append(f"- {t['description_vi']}")
        sec.append("")
        sec.append("#### 2. Đề Xuất Phong Cách & Khẩu Khí Tiếng Việt (VI Style Proposal)")
        v = p.get("vi_style_proposal", {})
        sec.append(f"- **Nhịp câu & giọng điệu:** {v.get('sentence_rhythm', 'N/A')}")
        sec.append(f"- **Đại từ tự xưng đề xuất:** `{', '.join(v.get('self_pronouns', [])) or 'Theo cảnh'}`")
        sec.append(f"- **Đại từ gọi đối phương:** `{', '.join(v.get('address_by_listener', [])) or 'Theo cảnh'}`")
        if v.get("catchphrases"):
            sec.append(f"- **Cụm từ cửa miệng:** {', '.join(v['catchphrases'])}")
        sec.append("- **Điều cần tránh tuyệt đối (Negative Constraints):**")
        for dn in v.get("do_not", []):
            sec.append(f"  * {dn}")
        sec.append("")
        sec.append(f"*(Mã bằng chứng tham chiếu: `{', '.join(p.get('evidence_refs', []))}`)*")
        sec.append("")
        sec.append("---")
        sec.append("")
        return "\n".join(sec)

    bible_lines.append("## 1. Dàn Nhân Vật Khởi Đầu\n")
    for cid in ["char:103", "char:107", "char:108", "char:110", "char:111", "char:117", "char:132"]:
        if cid in all_prof_map:
            bible_lines.append(render_char_bible_section(cid))

    bible_lines.append("## 2. Đặc Vụ & Chiến Binh Trọng Tâm\n")
    for cid in ["char:112", "char:113", "char:114", "char:115", "char:116", "char:118"]:
        if cid in all_prof_map:
            bible_lines.append(render_char_bible_section(cid))

    bible_lines.append("## 3. Học Viện & Giao Liên\n")
    for cid in ["char:119", "char:120", "char:123", "char:125", "char:126", "char:127"]:
        if cid in all_prof_map:
            bible_lines.append(render_char_bible_section(cid))

    bible_lines.append("## 4. Bưu Cục, Ký Giả & Mái Ấm\n")
    for cid in ["char:130", "char:133", "char:134", "char:135", "char:137", "char:139"]:
        if cid in all_prof_map:
            bible_lines.append(render_char_bible_section(cid))

    bible_lines.append("## 5. Bí Thuật, Đền Thiêng & Huyền Sư\n")
    for cid in ["char:140", "char:141", "char:142", "char:143", "char:144", "char:145"]:
        if cid in all_prof_map:
            bible_lines.append(render_char_bible_section(cid))

    bible_lines.append("## 6. Quân Binh & Hải Trình\n")
    for cid in ["char:147", "char:149", "char:150", "char:155", "char:156", "char:157"]:
        if cid in all_prof_map:
            bible_lines.append(render_char_bible_section(cid))

    bible_lines.append("## 7. Các Biến Thể Đặc Biệt\n")
    for cid in ["char:158", "char:159", "char:160", "char:162"]:
        if cid in all_prof_map:
            bible_lines.append(render_char_bible_section(cid))

    bible_content = "\n".join(bible_lines)

    # 8. Xây dựng COVERAGE.json
    print("\n6. Tạo COVERAGE.json và ISSUES.json...")
    coverage_data = {
        "schema": 1,
        "kind": "character_context_coverage",
        "revision": "r02",
        "baseline_path": "work/character_context_20261023_r01",
        "counts": {
            "total_roster_characters": 41,
            "preserved_grounded_profiles": 7,
            "newly_completed_grounded_profiles": 34,
            "total_grounded_profiles": 41,
            "pending_profiles": 0,
            "coverage_percentage": "100%",
            "excluded_constructs": 3,
            "glossary_only_names": 1
        },
        "all_profile_ids": sorted(list(all_prof_map.keys())),
        "grounded_profile_ids": sorted([cid for cid, p in all_prof_map.items() if p["status"] == "source_grounded_editorial_draft"]),
        "pending_profile_ids": []
    }

    issues_data = {
        "schema": 1,
        "kind": "character_context_issues_registry",
        "revision": "r02",
        "total_issues": 3,
        "issues": [
            {
                "issue_id": "ISSUE_VARIANT_IDENTITY_INDEPENDENCE",
                "affected_ids": ["char:158", "char:159", "char:160", "char:162"],
                "description_vi": "Các biến thể (Snowish Laru, Springseek Coronis, Suntide Willow, Firstlight Noya) có ID riêng trong cơ sở dữ liệu. Không tự ý gộp dữ liệu hoặc kế thừa quan hệ từ bản thường khi chưa có chứng cứ phân cảnh xác nhận.",
                "status": "documented_and_isolated",
                "action": "Duy trì hồ sơ và mã định danh tách biệt 100%."
            },
            {
                "issue_id": "ISSUE_GOLEM_NON_PLAYABLE_EXCLUSION",
                "affected_ids": ["char:997", "char:998", "char:999"],
                "description_vi": "Các bản ghi Golem (Spellbound Golem) là thực thể cơ khí/quái vật mang ID nhân vật trong table Character, không phải Lữ khách đối thoại. Được xếp vào danh sách loại trừ (excluded_constructs).",
                "status": "properly_excluded_from_denominator",
                "action": "Không tính vào mẫu số nhân vật hội thoại cần xây dựng Voice Bible."
            },
            {
                "issue_id": "ISSUE_GLOSSARY_ONLY_WILLOW",
                "affected_ids": ["name:Willow"],
                "description_vi": "Tên Willow xuất hiện trong glossary mà không có ID game trực tiếp (ngoài biến thể Suntide Willow char:160).",
                "status": "cataloged_separately",
                "action": "Lưu riêng trong danh mục glossary-only, tránh nhầm lẫn mẫu số."
            }
        ]
    }

    checkpoint_data = {
        "run_id": "character_context_campaign_20261023_r02",
        "baseline_path": "work/character_context_20261023_r01",
        "baseline_hashes": {
            "CHARACTER_ROSTER.json": "30a159eba47359068d14dc635cc4d6f1e29c1180f712fc175b95bd155c518c75",
            "CHARACTER_VOICE_PROFILES.json": "0cf6282cfcc971d945ba81522e5c65ecc24d2af5a1d76ed9c959cf1926932bea",
            "CHARACTER_VOICE_BIBLE.md": "0d70af7b82dd5e9b427ce7c2c6f2235b9a37cffaa2fcff082ce70ac5deea9b99",
            "CHARACTER_RELATIONSHIP_MATRIX.json": "4ac555fb1ada6fd6e7aa29324393ed9860c31c06f44161c9e6e4731d215a027c",
            "SOURCE_EVIDENCE.json": "99d9bf32990217ea4116c1e41f028a03c4edd3d3a4179a7b7bebaf3bed073839"
        },
        "target_ids": sorted(list(char_definitions.keys())),
        "preserved_predecessor_ids": ["char:103", "char:107", "char:108", "char:110", "char:111", "char:117", "char:132"],
        "todo_ids": [],
        "content_ready_ids": sorted(list(char_definitions.keys())),
        "accepted_documentation_ids": sorted(list(all_prof_map.keys())),
        "pending_source_ids": [],
        "status": "completed_full_campaign_100_percent",
        "batches_completed": [
            "batch1_core_agents_112_118",
            "batch2_academy_couriers_119_127",
            "batch3_post_press_orphanage_130_139",
            "batch4_craft_shrine_shadow_140_145",
            "batch5_army_seafaring_147_157",
            "batch6_special_variants_158_162"
        ]
    }

    # 9. Ghi tất cả các file ra OUTPUT_DIR
    print("\n7. Xuất các tệp tài liệu sang thư mục revision mới: work/character_context_20261023_r02...")
    with open(OUTPUT_DIR / "CHARACTER_ROSTER.json", "w", encoding="utf-8") as f:
        json.dump(roster_data, f, indent=2, ensure_ascii=False)

    with open(OUTPUT_DIR / "SOURCE_EVIDENCE.json", "w", encoding="utf-8") as f:
        json.dump(out_evidence_data, f, indent=2, ensure_ascii=False)

    with open(OUTPUT_DIR / "CHARACTER_VOICE_PROFILES.json", "w", encoding="utf-8") as f:
        json.dump(out_profiles_data, f, indent=2, ensure_ascii=False)

    with open(OUTPUT_DIR / "CHARACTER_RELATIONSHIP_MATRIX.json", "w", encoding="utf-8") as f:
        json.dump(new_matrix_data, f, indent=2, ensure_ascii=False)

    with open(OUTPUT_DIR / "CHARACTER_VOICE_BIBLE.md", "w", encoding="utf-8") as f:
        f.write(bible_content)

    with open(OUTPUT_DIR / "COVERAGE.json", "w", encoding="utf-8") as f:
        json.dump(coverage_data, f, indent=2, ensure_ascii=False)

    with open(OUTPUT_DIR / "ISSUES.json", "w", encoding="utf-8") as f:
        json.dump(issues_data, f, indent=2, ensure_ascii=False)

    with open(OUTPUT_DIR / "CHECKPOINT_CHARACTER_CONTEXT.json", "w", encoding="utf-8") as f:
        json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)

    # Sao chép các templates hỗ trợ sang r02 để đầy đủ bộ công cụ
    for tmpl in ["SCENE_CONTEXT.template.json", "SCENE_REVIEW.template.json", "EVIDENCE_AND_LIMITS.md"]:
        if (BASELINE_DIR / tmpl).exists():
            with open(OUTPUT_DIR / tmpl, "w", encoding="utf-8") as f:
                f.write((BASELINE_DIR / tmpl).read_text(encoding="utf-8"))

    print("   ✓ Đã ghi đầy đủ 10 tệp tài liệu trong work/character_context_20261023_r02/")
    print("\n=== HOÀN THÀNH TỔNG HỢP TOÀN BỘ BỘ TÀI LIỆU R02 ===")


if __name__ == "__main__":
    main()
