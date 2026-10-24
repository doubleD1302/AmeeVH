import json, re, sys

sys.path.append("StellaSora_VietHoa/work/editorial/final_cg_npc_and_disc_editorial_20261025_r01")
from translations_cg_disc4066 import TRANSLATIONS_CG_DISC4066

SRC_PATH = "StellaSora_VietHoa/work/editorial/final_cg_npc_and_disc_editorial_20261025_r01/PARTITION_B_SOURCE.json"
OUT_PATH = "StellaSora_VietHoa/work/editorial/final_cg_npc_and_disc_editorial_20261025_r01/PROPOSALS_PARTITION_B.jsonl"

with open(SRC_PATH, "r", encoding="utf-8") as f:
    source_items = json.load(f)

# Specific curated overrides for Partition B
OVERRIDES = {
    # CG_disc4004
    "CG_disc4004.5": "Giấc Mộng Tử Đằng",
    "CG_disc4004.6": "Phần thưởng xứng đáng cho những nhọc nhằn là một giấc ngủ say cùng những giấc mơ êm đềm.",
    "CG_disc4004.108": "Ruby và Sapphire",
    "CG_disc4004.109": "<size=45>Oái?! B-Boss?!",

    # CG_disc4005
    "CG_disc4005.5": "Đóa Hoa Nắng Mai",
    "CG_disc4005.6": "Một thoáng ngập ngừng, một khởi đầu rạng rỡ.",

    # CG_disc4006
    "CG_disc4006.5": "Xích Đu Phù Thủy",
    "CG_disc4006.6": "Nơi hoa viên tĩnh mịch chở che bao điều bí mật, nàng phù thủy lặng lẽ buông mình đáp xuống.",
    "CG_disc4006.69": "Nhìn cái gì mà nhìn? Tưởng lừa được đám Hội Giám Sát Hàng Hóa chúng ta sao?",
    "CG_disc4006.71": "Hội Giám Sát Hàng Hóa...==W== Các người chẳng qua cũng chỉ là một nhóm tự phát thôi mà? Có tư cách gì mà—",
    "CG_disc4006.180": "Là Vệ Binh Hoàng Gia! Chúng tới bắt chúng ta đấy!",
    "CG_disc4006.181": "Đội Cận Vệ!?...==W== Phù thủy đáng nguyền rủa! Chúng cũng sẽ tóm cả cô thôi!",
    "CG_disc4006.233": "<size=50>Oaaaaaaa—!!</size>",

    # CG_disc4007
    "CG_disc4007.5": "Hỗn Loạn Lúc Nửa Đêm",
    "CG_disc4007.6": "Khi mọi sự đã an bài, Tộc Ashwind sẽ đón nhận những thử thách mới phía trước ra sao?",
    "CG_disc4007.147": "<size=50>Có người tới kìa!",
    "CG_disc4007.236": "<size=80>Đi mau! Ngay bây giờ!",
    "CG_disc4007.241": "<size=60>Agh—bị phục kích rồi, rút lui, rút lui mau!",

    # CG_disc4008
    "CG_disc4008.5": "Sắc Xanh Tung Cánh",
    "CG_disc4008.6": "Con người ta luôn mơ mộng giữa tiết xuân sang. Dưới rèm mi khép hờ, là giấc mơ về vòm trời xanh biếc bao la...",
    "CG_disc4008.120": "... A!",
    "CG_disc4008.130": "Là một Du Hành Giả! Anh ấy đã cứu cháu khỏi tay lũ quái vật nên cháu mới viết một bức thư cảm ơn.==W== Nhưng cháu không biết tên lẫn địa chỉ của anh ấy...==W== Cô vẫn có thể gửi giúp cháu được chứ?",
    "CG_disc4008.320": "Vì thế chúng tôi nhận mọi ủy thác có thể, tính toán chi li từng lộ trình, chắt chiu từng đồng chi phí rồi mới lên đường.",

    # CG_disc4015
    "CG_disc4015.5": "Khúc Ca Của Hươu",
    "CG_disc4015.6": "Một cuộc kỳ ngộ, một niềm vui bất ngờ; căn nhà gỗ giữa rừng sâu này chỉ thuộc về riêng hai ta, ngân vang tiếng nai gọi bầy tha thiết.",
    "CG_disc4015.86": "Đúng vậy. Theo ủy thác từ Hiệp hội Du Hành Giả.",
    "CG_disc4015.97": "Một mình tôi không cáng đáng nổi nên hôm qua tôi đã đăng ủy thác lên Hiệp hội Du Hành Giả.",
    "CG_disc4015.214": "Không cần đâu, thưa bác. Bác đã có phần thưởng cho ủy thác rồi mà, đúng không?",
    "CG_disc4015.235": "Em cũng đang cảm ơn tôi sao?==W== Hì hì. Ủy thác lần này mang lại nhiều phần thưởng hơn tôi tưởng đấy.",

    # CG_disc4016
    "CG_disc4016.5": "Ký Sự Mùa Xuân",
    "CG_disc4016.6": "Khi sắc xuân đã hòa vào nếp sống thường nhật, cô bắt đầu thầm mong gặp được một người cùng bước vào mùa xuân của đời mình.",

    # CG_disc4017
    "CG_disc4017.6": "Trước khi kịp nhận ra, cô đã đứng trên một sân khấu rộng lớn hơn. Muôn người bắt đầu chiêm ngưỡng ánh hào quang của cô, nhưng niềm tin nơi cô dành cho bạn thì chưa từng lay chuyển.",
    "CG_disc4017.158": "... Fuyuka?",

    # CG_disc4026
    "CG_disc4026.5": "Nghịch Lưu Trảm Kiếm",
    "CG_disc4026.6": "Bạn cùng Chitose ghé suối nước nóng Tanikaze có hạn, nơi khiến cô bồi hồi nhớ về cố hương…",

    # CG_disc4027
    "CG_disc4027.5": "Nét Bút Huyền Bí",
    "CG_disc4027.6": "Bất kể nét chữ ra sao, mỗi một nét thảo đều là cách cô phác họa thế giới này.",

    # CG_disc4028
    "CG_disc4028.5": "Hoa Viên Ánh Dương",
    "CG_disc4028.6": "Nếu hết thảy đều lãng quên, liệu nó có từng thực sự tồn tại?",

    # CG_disc4029
    "CG_disc4029.5": "Kho Báu Của Mèo",
    "CG_disc4029.6": "Hỡi món quà may mắn bị mê hoặc bởi Tà Nhãn của Chaton vĩ đại! Hãy quy phục trước sức mạnh hắc ám của ta!",
    "CG_disc4029.73": "==Off==<size=70><color=#8e65ad>Tà Nhãn, giải phóng—!</color>",
    "CG_disc4029.166": "Hừm! Chắc chắn được! Tuyệt đối sẽ được mà!==W== Dù có không được đi chăng nữa, Chaton vĩ đại này cũng sẽ ép cậu phải làm cho bằng được!",

    # CG_disc4036
    "CG_disc4036.5": "Lữ Khách Lạc Lối",
    "CG_disc4036.6": "Một câu hỏi trăn trở suốt bao năm của Kẻ Tầm Đạo đang đợi câu trả lời từ bạn.",
    "CG_disc4036.262": "Phì... Ha ha ha ha~",

    # CG_disc4037
    "CG_disc4037.5": "Máy Gắp Thú Bông",
    "CG_disc4037.6": "Chuyến phiêu lưu kỳ vĩ gói gọn trong một căn phòng, huyền thoại bé nhỏ về những món đồ chơi.",
    "CG_disc4037.176": "Thế là hết, chịu thua rồi. Mình chẳng thể làm gì hơn được nữa.",
    "CG_disc4037.199": "Cách này chắc chắn sẽ hiệu quả,==W== bởi Kaede lúc nào cũng đi tuần tra khắp Nhà Du Hành Giả cả.",
    "CG_disc4037.241": "Thật sao? Vậy có lẽ cuối cùng cô ấy cũng chịu ra ngoài nhận ủy thác rồi...",

    # CG_disc4038
    "CG_disc4038.5": "Gợn Sóng Hoài Niệm",
    "CG_disc4038.6": "Trong trái tim cô ấy, mỗi món quà từ bạn đều là độc nhất vô nhị.",

    # CG_disc4044
    "CG_disc4044.5": "Rạng Đông Mùa Xuân",
    "CG_disc4044.6": "Hãy chọn một món quà lưu niệm, rồi chúng ta cùng nhau dệt thêm nhiều kỷ niệm đẹp nhé.",
    "CG_disc4044.271": "Sao lại không chứ?==W== Đã bảo rồi mà... điều tôi muốn chính là kỷ niệm này.",

    # CG_disc4045
    "CG_disc4045.5": "Cánh Hoa Ảo Mộng",
    "CG_disc4045.6": "Khi gió lặng hoa tàn, trần thế bàng hoàng nhận ra biển hoa rực rỡ thuở nào chỉ là một giấc chiêm bao được dệt nên.",
    "CG_disc4045.70": "Giờ tôi phải làm sao đây?==W== Phải hai ngày nữa Lữ Đoàn Tân Tinh mới hoàn thành ủy thác trở về. Nếu tên trộm đột nhập vào lúc này, tôi hoàn toàn không thể tự vệ được...",
    "CG_disc4045.404": "C-Cảm ơn cậu rất nhiều!==W== Tôi sẽ không bao giờ quên ơn của cậu đâu!",

    # CG_disc4048
    "CG_disc4048.5": "Bất Ngờ Đêm Tuyết",
    "CG_disc4048.6": "Khi chuông nửa đêm điểm nhịp và hội hè dần lắng xuống, cô ấy cũng xứng đáng có được món quà cho riêng mình sau một ngày dài.",

    # CG_disc4051
    "CG_disc4051.5": "Bến Đỗ Vì Sao",
    "CG_disc4051.6": "Nơi những vì sao lấp lánh, ước nguyện của trẻ thơ sẽ tìm thấy mái ấm cho mình.",
    "CG_disc4051.184": "Thực ra, đôi khi các thành viên Lữ Đoàn Tân Tinh cũng cùng nhau chạm vào Hộp Ước Nguyện...==W== Nhưng họ phải cùng mường tượng về một thứ y hệt nhau và hợp nhất tri thức lại. Nếu không thì tỉ lệ thành công sẽ tụt dốc thảm hại...",

    # CG_disc4054
    "CG_disc4054.5": "Thiên Đường Nhỏ",
    "CG_disc4054.6": "Đó là kỷ vật của riêng hai chúng ta, đong đầy những tình cảm sâu đậm nhất tôi dành cho bạn.",
    "CG_disc4054.157": "Mimi và Lily",

    # CG_disc4055
    "CG_disc4055.5": "Ánh Sáng Thoáng Qua",
    "CG_disc4055.6": "Hãy lắng nghe tiếng lòng mình giữa chốn sâu thẳm tĩnh mịch này.",
    "CG_disc4055.64": "Chào buổi sáng, Willow. Tôi cứ ngỡ lại thấy cậu đang vùi đầu dưới đống giấy tờ nữa chứ.",
    "CG_disc4055.119": "Willow? Đầu óc cậu lại chuyển về chế độ làm việc rồi đấy à?",
    "CG_disc4055.122": "A, xin lỗi. Không ngờ cậu lại nhận ra. Chế độ nghỉ phép, Willow ơi là Willow. Phải nhập vai cho đúng chứ.",
    "CG_disc4055.136": "Willow? Sao trông mặt nghiêm trọng thế? Có chuyện gì vậy?",
    "CG_disc4055.138": "K-Không có gì. ==PLAYER_NAME==, không chơi Cờ Bãi Biển nữa. Nếu cậu bị thương ngoài đó, tôi biết lấy mặt mũi nào đối diện với Lữ Đoàn Tân Tinh đây.",
    "CG_disc4055.146": "Willow?! Được rồi, không chơi nữa là được chứ gì. Đừng kéo tay tôi mạnh thế!",
    "CG_disc4055.256": "_NOT_IN_LOG_<br><br><br><br><margin-left=15em><align=left><size=100><i><voffset=0.3em>Chẳng là </voffset><size=200><color=#b0e0f6>gì đâu==A0.03==",
    "CG_disc4055.257": "_NOT_IN_LOG_<br><br><br><br><margin-left=15.05em><align=left><size=100><i><voffset=0.3em>Chẳng là </voffset><size=200><color=#b0e0f6>gì đâu==A0.03==",
    "CG_disc4055.258": "_NOT_IN_LOG_<br><br><br><br><margin-left=15.1em><align=left><size=100><i><voffset=0.3em>Chẳng là </voffset><size=200><color=#b0e0f6>gì đâu==A0.03==",
    "CG_disc4055.259": "_NOT_IN_LOG_<br><br><br><br><margin-left=15.15em><align=left><size=100><i><voffset=0.3em>Chẳng là </voffset><size=200><color=#b0e0f6>gì đâu==A0.03==",
    "CG_disc4055.260": "_NOT_IN_LOG_<br><br><br><br><margin-left=15.2em><align=left><size=100><i><voffset=0.3em>Chẳng là </voffset><size=200><color=#b0e0f6>gì đâu==A0.03==",
    "CG_disc4055.261": "_NOT_IN_LOG_<br><br><br><br><margin-left=15.25em><align=left><size=100><i><voffset=0.3em>Chẳng là </voffset><size=200><color=#b0e0f6>gì đâu==A0.03==",
    "CG_disc4055.262": "_NOT_IN_LOG_<br><br><br><br><margin-left=15.3em><align=left><size=100><i><voffset=0.3em>Chẳng là </voffset><size=200><color=#b0e0f6>gì đâu==A0.03==",
    "CG_disc4055.326": "Willow! Cậu lặn dưới đó lâu quá đấy. Tôi bắt đầu lo rồi...",

    # CG_disc4057
    "CG_disc4057.5": "Cùng Tôi Vượt Sóng",
    "CG_disc4057.6": "Mình sẽ không phụ lòng tốt của Shia đâu! Nhất định mình phải cưỡi ngọn sóng này!",
    "CG_disc4057.234": "Thôi tiêu rồi! Mải tập trung quá nên mình trôi dạt ra tít ngoài biển mất rồi! Phải làm sao đây? Đến bờ còn chẳng thấy đâu nữa...",

    # CG_disc4059
    "CG_disc4059.5": "Bay Đi, Chú Chim Trong Lồng",
    "CG_disc4059.6": "Tôi trong bức họa và tôi trong gương soi—đâu mới thực sự là bản ngã của tôi?",

    # CG_disc4061
    "CG_disc4061.5": "Chuyện Kể Trước Giờ Ngủ",
    "CG_disc4061.6": "Một trang sách trắng tinh khôi, lại mở ra muôn vàn khả năng bất tận.",
    "CG_disc4061.265": "<size=50>Aaaaa!</size>==W==",
    "CG_disc4061.307": "<size=50>Hyaaaaa!!</size>"
}

# Regex replacements for general polish
LEXICAL_REPLACEMENTS = [
    (r"\bAshwind Clan\b", "Tộc Ashwind"),
    (r"\bNew Star Guild\b", "Lữ Đoàn Tân Tinh"),
    (r"\bHội Ngôi Sao Mới\b", "Lữ Đoàn Tân Tinh"),
    (r"\bHiệp hội Ngôi sao Mới\b", "Lữ Đoàn Tân Tinh"),
    (r"\bhội ngôi sao mới\b", "Lữ Đoàn Tân Tinh"),
    (r"\bTrekker Association\b", "Hiệp hội Du Hành Giả"),
    (r"\bHiệp hội Trekker\b", "Hiệp hội Du Hành Giả"),
    (r"\bTrekkers\' House\b", "Nhà Du Hành Giả"),
    (r"\bNhà của những người đi bộ\b", "Nhà Du Hành Giả"),
    (r"\bTrekkers\b", "Du Hành Giả"),
    (r"\bTrekker\b", "Du Hành Giả"),
    (r"\bnhững người đi bộ\b", "các Du Hành Giả"),
    (r"\bngười đi bộ\b", "Du Hành Giả"),
    (r"\bHổ phách\b", "Amber"),
    (r"\bhổ phách\b", "Amber"),
    (r"\bDiên vĩ\b", "Iris"),
    (r"\bdiên vĩ\b", "Iris"),
    (r"\bchết tiệt\b", "khốn khiếp"),
    (r"\bMonolith\b", "Cự Thạch"),
    (r"\bWishing Box\b", "Hộp Ước Nguyện"),
    (r"\bHộp Điều Ước\b", "Hộp Ước Nguyện"),
    (r"\bHộp điều ước\b", "Hộp Ước Nguyện"),
    (r"\bStella Coins\b", "Đồng Stella"),
    (r"\bStar Bells\b", "Chuông Tinh Tú"),
    (r"\bStar Bell\b", "Chuông Tinh Tú"),
    (r"\bStellaroid\b", "Tinh Linh Thể"),
    (r"\bArtifact\b", "Cổ Vật"),
    (r"\bBạo quân\b", "Bạo Chúa"),
    (r"\bBạo Quân\b", "Bạo Chúa"),
]

TAG_PATTERN = re.compile(r'<[^>]+>|==[a-zA-Z0-9_.-]+==|\{[0-9]+\}|_NOT_IN_LOG_')

proposals = []
for item in source_items:
    item_id = item["id"]
    en = item["en"]
    raw_vi = item["current_vi"]

    if item_id in TRANSLATIONS_CG_DISC4066:
        final_text = TRANSLATIONS_CG_DISC4066[item_id]
    elif item_id in OVERRIDES:
        final_text = OVERRIDES[item_id]
    else:
        text = raw_vi
        for pat, repl in LEXICAL_REPLACEMENTS:
            text = re.sub(pat, repl, text)
        final_text = text

    # Verify tokens
    src_tokens = TAG_PATTERN.findall(en)
    tgt_tokens = TAG_PATTERN.findall(final_text)

    if src_tokens != tgt_tokens:
        print(f"Token notice [{item_id}]:\n  EN: {src_tokens}\n  VI: {tgt_tokens}")

    proposals.append({
        "id": item_id,
        "scene_id": item["scene_id"],
        "en": en,
        "current_vi": raw_vi,
        "proposed_vi": final_text
    })

with open(OUT_PATH, "w", encoding="utf-8") as f:
    for p in proposals:
        f.write(json.dumps(p, ensure_ascii=False) + "\n")

print(f"Successfully generated {len(proposals)} Partition B proposals to {OUT_PATH}")
