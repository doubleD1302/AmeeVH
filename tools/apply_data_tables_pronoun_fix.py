# -*- coding: utf-8 -*-
"""
Script to apply gender-neutral pronoun fixes to data tables in work/research/data_200_decrypted/entries.
Replaces gendered "anh/chị" towards the player with neutral/respectful anime terms (Sếp, Đội trưởng, ngài, cậu, tôi).
"""

import json
from pathlib import Path
import re
import sys
import time

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))
from arcx_adapter import repack_archive

ENTRIES_DIR = ROOT / "work" / "research" / "data_200_decrypted" / "entries"
DEC_DIR = ROOT / "work" / "research" / "data_200_decrypted"
OUTPUT_ARCX = ROOT / "dist" / "data_patched_vi.arcx"

# Exact key replacements
EXACT_TABLE_REPLACEMENTS = {
    # ActivityStory
    "ActivityStory.101080208.2": "Bạo chúa, tôi đã dành cho ngài chỗ ngồi tốt nhất trong nhà.",

    # Agent
    "Agent.300102.3": "Tôi nghe nói bạn khá giỏi trong việc theo đuổi điểm cao trong các trò chơi nhịp điệu... Tại sao không chỉ cho học sinh của tôi cách thực hiện? Tôi sẽ đổi giúp cậu những hộp đạn này. Một thỏa thuận khá tốt, phải không?",

    # CharacterSkin
    "CharacterSkin.11103.2": "Dưới ánh nắng đông trong lành, hình bóng cậu nâng niu ly nước ấm phả ra làn khói trắng; một người luôn tự nhận mình bình phàm giản đơn, nhưng lại chính là toàn bộ ý nghĩa của ngày hôm nay.",
    "CharacterSkin.11104.2": "Cái đó... Em sẽ cố hết sức giữ thăng bằng cho chiếc phao bơi này, nhưng khi trèo lên Sếp nhớ cẩn thận một chút nhé. ——Đ-Đương nhiên rồi, nếu Sếp lỡ sảy chân rơi xuống nước, em nhất định sẽ kéo Sếp lại thật chặt!",
    "CharacterSkin.15503.2": "Trong làn nước biển dạt dào, phảng phất hương vị của rạn san hô, và cả hương thơm quen thuộc của Đội trưởng nữa. Khẽ nhắm mắt lại, ngỡ như đang được tất thảy sự dịu dàng này ôm trọn vào lòng vỗ về.",

    # CharGetLines
    "CharGetLines.10301.1": "Em là Amber.\n...Iris có viết sẵn cho em một bản tự giới thiệu, lát nữa em sẽ gửi qua tin nhắn cho Sếp nhé.",
    "CharGetLines.10306.1": "Nương theo làn gió biển ấm nồng, chớp lấy một thoáng lặng giữa ngày hội rộn rã, em khẽ hướng ánh nhìn bình yên về phía Sếp.",
    "CharGetLines.11302.1": "Lại gặp nhau rồi, Đội trưởng! Có một ủy thác khẩn cấp cần đến sự trợ giúp của Đội trưởng, nội dung chi tiết em sẽ báo cáo cụ thể trên đường đi.",
    "CharGetLines.11401.1": "Hừ hừ hừ... Dưới sự dẫn dắt của số phận bóng tối, rốt cuộc chúng ta cũng đã tao ngộ! Kể từ hôm nay trở đi, sức mạnh diệt thế của đại nhân Chaton sẽ phụng sự cho ngài!",
    "CharGetLines.11402.1": "Ngạc nhiên chưa! Kẻ thừa kế bóng tối vĩ đại nhất đã đích thân đến tái ngộ cùng ngài đây!",
    "CharGetLines.11503.1": "Đội trưởng ơi, em không còn là con nít nữa đâu, em cũng có thể bảo vệ Đội trưởng mà.",
    "CharGetLines.11601.1": "Em... em là Ridge, quản lý nhà kính bên Nông Nghiệp Liên Hợp. Lần đầu gặp mặt... mong Sếp chỉ giáo thêm cho em ạ...",
    "CharGetLines.11602.1": "Lần này... em có đem chút quà cho Sếp nè! Toàn là rau củ tươi ngon do chính tay em chăm sóc đó, vừa mới hái ngoài vườn luôn á.",
    "CharGetLines.11701.1": "Chào Đội trưởng! Em là Jinglin, chưởng quầy của nhà hàng Hoài Cảnh Thực Phủ (Huaijing Bistro)! Sau này mong Đội trưởng chiếu cố việc làm ăn của quán em nhé!",
    "CharGetLines.11702.1": "Em sẽ bảo nhà bếp nấu riêng cho Đội trưởng một phần ăn đặc biệt nhé. Hì hì, không phiền hà gì đâu, Đội trưởng là khách quen quý giá của nhà em mà!",
    "CharGetLines.12301.1": "Sếp ơii~ Cuối cùng Ann cũng được gặp Sếp rồi! Hi hi, Sếp có thể dẫn Ann đi phiêu lưu cùng được không nào~",
    "CharGetLines.12302.1": "Oa~ Sếp lại tìm thấy Ann rồi nè~ Lần tới phải đổi lại thành lượt Ann đi tìm Sếp đấy nhé~",

    # DatingCharacterEvent
    "DatingCharacterEvent.107302.3": '"Xin lỗi nhé, chờ em gọi điện một lát... Hừ, đúng là phí hoài thời gian quý báu—hôm nay rõ ràng là ngày nghỉ của mình mà!"\n\nCác kỵ sĩ trực ban nhanh chóng có mặt tại hiện trường, giúp hai người có thể tiếp tục ngày nghỉ thảnh thơi. Bạn nhận thấy nụ cười của Tilia dường như rạng rỡ hơn trước một chút.',
    "DatingCharacterEvent.123301.3": '"Đây nhất định là món quà thần núi ban tặng riêng cho Ann đấy. Để tôi chỉ cho em cách dùng nhé."\nNhìn ánh mắt mong chờ của Ann, bạn đưa ra một lời giải thích thật ấm áp, khiến cô bé mừng rỡ reo vui.',
    "DatingCharacterEvent.132303.2": '"Xem này!" Cô bé rút ra cuốn "Nhập Môn Giám Định Di Vật". "Đọc cuốn này đi rồi cậu sẽ chẳng bao giờ bị mấy tay gian thương lọc lừa nữa đâu."\nCô bé trao sách cho bạn với nụ cười ngượng nghịu: "Mong là nó giúp ích cho hành trình của cậu."',
    "DatingCharacterEvent.137301.2": '“Xem ra Tiền bối có tiêu chuẩn khá khắt khe về bánh ngọt nhỉ.”\n"À thì, hiếm khi được đi chơi cùng em nên tôi muốn chọn quán nào được đánh giá cao một chút. Tôi không muốn đồ ăn làm em thất vọng."\n"Em đâu có kén ăn dữ dằn như tiền bối n... Ưm."\nChưa kịp nói dứt câu, một miếng bánh ngọt mềm mại đã được khéo léo đút thẳng vào miệng bạn.',
    "DatingCharacterEvent.140302.3": 'Sparkla khẽ vươn vai một cái thật sảng khoái.\nThoáng cái mà cả hai đã ở lỳ trong thư viện suốt cả ngày trời. Sparkla đầy tiếc nuối xếp lại những cuốn sách chưa đọc xong lên giá.\n"Ma Vương..."\n"Em..."\nCả hai đồng thanh cất lời cùng một lúc, rồi nhìn nhau mỉm cười đầy thấu hiểu.\n"Cậu vừa định rủ lần sau tụi mình lại ghé qua đây tiếp, đúng không nào?"',
    "DatingCharacterEvent.143302.2": 'Bạn tưởng mình đã đi vào ngõ cụt ở bức tường đá, nhưng Wraith đã bật một công tắc ẩn và tảng đá bị nghiền nát mở ra.\n\nTrước khi bạn kịp phản ứng, một nhà tắm tự nhiên hiện ra.\n\n"Tôi đã bỏ rất nhiều công sức để sửa chữa nơi này."\n\n"Nhưng nhìn thấy vẻ mặt đó của cậu à? Hoàn toàn xứng đáng."\n\n"Hãy nhảy vào. Đừng lo, nước rất trong lành."\n\nCô ấy biến mất sau tấm bình phong để tắm rửa. Không muốn tỏ ra thô lỗ, bạn quyết định thử cách tắm ngoài trời này. Tuy nhiên...',
    "DatingCharacterEvent.147302.3": 'Nàng lục tìm trong túi—ôi bất ngờ chưa, cô nàng lại cháy túi mất rồi. Bạn đành phì cười bất lực rồi rút tiền thanh toán hộ nàng.\n"Em nhất định sẽ đền đáp bằng một buổi biểu diễn miễn phí, producer đại nhân!"\nCô nàng tỏ ra vô cùng quyết tâm dùng tài năng âm nhạc để báo đáp món nợ ân tình này.',
    "DatingCharacterEvent.156303.2": '"Sự kiện bốc thăm lần này tặng gấu bông ước nguyện từ Tinh Tháp đấy, cực kỳ quý hiếm lại còn giới hạn số lượng, tôi nhất định phải rinh bằng được một con!"\nMiệng thì nói đầy tự tin, nhưng khi nhân viên cầm thùng phiếu bước đến, Nazuna lại lộ rõ vẻ chần chừ, đôi mắt long lanh đáng thương nhìn sang bạn.\n"Ý em là muốn tôi bốc thăm hộ à?"',
    "DatingCharacterEvent.156303.3": '"Được rồi, được rồi. Nhưng nếu tôi không hiểu thì đừng trách tôi..."\n\n"Yay! Tôi tin tưởng vào vận may tuyệt vời của Sếp mà!"\nMay mắn thay, bạn đã không làm Nazuna thất vọng. Nhìn cô bé vui sướng nhấc thú nhồi bông lên, bạn cũng không khỏi mỉm cười.',

    # Item
    "Item.10304.3": "Nương theo làn gió biển ấm nồng, chớp lấy một thoáng lặng giữa ngày hội rộn rã, em khẽ hướng ánh nhìn về phía Sếp. Khoảnh khắc ấy thật bình yên biết bao.",
    "Item.11103.1": "Mảnh Ghép 1/365 Của Cậu",
    "Item.11103.2": "Chứng chỉ mở khóa trang phục độc quyền của Iris: 'Mảnh Ghép 1/365 Của Cậu'!",
    "Item.11103.3": "Dưới ánh nắng đông nhàn nhạt, cậu cầm trên tay tách trà ấm, từng hơi thở khẽ phả thành làn sương mỏng manh. Người luôn tự nhận mình bình thường như cậu, lại chính là người thắp sáng ngày hôm nay trở nên thật đặc biệt.",
    "Item.11104.3": "Ừm... Em sẽ cố hết sức giữ chiếc phao này thăng bằng, nhưng Sếp nhớ cẩn thận khi bước lên nhé. —V-Và dĩ nhiên, lỡ Sếp có trượt chân rơi xuống nước, em nhất định sẽ kéo Sếp lên ngay!",
    "Item.224054.3": "Một thiên đường nhỏ chỉ của riêng chúng ta, cùng cô ấy chạy trong ánh đèn mờ ảo. Đừng sợ vấp ngã—Tôi sẽ nắm chặt tay em, cho đến khi chúng ta cùng nhau đi đến cuối cùng.",
}

# Regex replacements across all data tables
TABLE_REGEX_RULES = [
    (r'\bmong anh/chị chỉ giáo\b', 'mong Sếp chỉ giáo'),
    (r'\bcho anh/chị nè\b', 'cho Sếp nè'),
    (r'\bcho anh/chị\b', 'cho Sếp'),
    (r'\banh/chị\b', 'Sếp'),
]

def apply_pronoun_fixes():
    print("=== APPLYING GENDER-NEUTRAL PRONOUN FIXES TO DATA TABLES ===")
    total_files_modified = 0
    total_keys_modified = 0

    for fpath in ENTRIES_DIR.glob("*.bin"):
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
        except Exception:
            continue

        file_modified = False
        for k, v in list(data.items()):
            if not isinstance(v, str):
                continue
            orig_v = v

            # 1. Exact map
            if k in EXACT_TABLE_REPLACEMENTS:
                v = EXACT_TABLE_REPLACEMENTS[k]

            # 2. Regex rules
            for pattern, repl in TABLE_REGEX_RULES:
                v = re.sub(pattern, repl, v)

            if v != orig_v:
                data[k] = v
                file_modified = True
                total_keys_modified += 1

        if file_modified:
            fpath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            total_files_modified += 1

    print(f"Data tables updated: {total_files_modified} files, {total_keys_modified} keys patched.")

def repack_data():
    print(f"\nRepacking data archive to {OUTPUT_ARCX}...")
    t0 = time.time()
    repack_archive(DEC_DIR, OUTPUT_ARCX, encrypt_payload=False)
    print(f"Repack completed in {time.time()-t0:.2f}s. Output size: {OUTPUT_ARCX.stat().st_size:,} bytes")

def main():
    apply_pronoun_fixes()
    repack_data()

if __name__ == "__main__":
    main()
