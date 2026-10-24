import json, re

SRC_PATH = "StellaSora_VietHoa/work/editorial/final_cg_npc_and_disc_editorial_20261025_r01/PARTITION_A_SOURCE.json"
OUT_PATH = "StellaSora_VietHoa/work/editorial/final_cg_npc_and_disc_editorial_20261025_r01/PROPOSALS_PARTITION_A.jsonl"

with open(SRC_PATH, "r", encoding="utf-8") as f:
    source_items = json.load(f)

# Specific curated overrides for Partition A
OVERRIDES = {
    # CG_npc133_01
    "CG_npc133_01.4": "Hồi 1",
    "CG_npc133_01.5": "Cô Thu Ngân Cô Đơn",
    "CG_npc133_01.6": "Không còn gì tẻ nhạt hơn việc phải thui thủi một mình trông coi tiệm bách hóa tiện lợi. Giá mà có ai đó đến phụ một tay giúp Portia bán hàng thì tốt biết mấy.",
    "CG_npc133_01.57": "(À, là các Du Hành Giả.)",
    "CG_npc133_01.71": "Kính chào quý khách... Mời quý khách cứ tự nhiên xem hàng ạ...",
    "CG_npc133_01.113": "(Có vẻ họ chẳng mấy dư dả Đồng Stella... Tiết kiệm thật đấy.)",
    "CG_npc133_01.117": "Nếu lần này không tìm được Cổ Vật, chúng ta sẽ chẳng thể hoàn thành ủy thác! Thế là cả đoàn coi như tiêu tùng!",
    "CG_npc133_01.118": "Nếu đoàn mà bị giải tán, chúng ta sẽ phải ra đường ở. Mà ra đường ở thì trang bị sẽ bị nẫng mất. Một khi trang bị mất sạch...",
    "CG_npc133_01.159": "Này nhé, nếu cậu chịu cất vài bước ra bắt chuyện với khách thay vì đứng ngẩn người ra đó thì doanh thu đã khá hơn rồi. Ít nhất cũng phải phụ tôi tính tiền chứ.",
    "CG_npc133_01.168": "<size=50>Tôi vẫn phải trông cái cửa hàng này một mình đấy à?!",

    # CG_npc133_02
    "CG_npc133_02.4": "Hồi 2",
    "CG_npc133_02.5": "Tái Tuyển Dụng",
    "CG_npc133_02.6": "Tuyển lại nhân viên cũ mang lại vô số lợi thế: họ đã thấu hiểu văn hóa công ty, quen thuộc với mọi quy định, và quan trọng nhất là—hoàn toàn không tốn công đào tạo.",
    "CG_npc133_02.55": "Kính chào quý khách, mời quý khách cứ tự nhiên xem hàng...==W== Ơ?",
    "CG_npc133_02.84": "Hồi đầu tiên gặp Lữ Đoàn Tân Tinh,==W== tôi bị lạc trong Cự Thạch rồi vô tình xơi mất phần cơm hộp thịt cốt lết...==W== để rồi cuối cùng bị bắt ở lại làm chân chạy vặt cho cửa hàng.",
    "CG_npc133_02.93": "May mà có Lữ Đoàn đến chuộc tôi ra trước khi tôi mất hẳn bản thân... Dù nghĩ lại thì có vẻ giống như Portia chỉ muốn thả cho tôi đi thì đúng hơn.",
    "CG_npc133_02.191": "Á! Noya! Amber! Iris! Cứu—==W==",
    "CG_npc133_02.207": "Suỵt! Du Hành Giả đang tới kìa.",
    "CG_npc133_02.235": "Đoàn của tôi lúc nào cũng quét sạch chiến trường... Tôi cứ ngỡ ai ai cũng làm thế chứ.",
    "CG_npc133_02.254": "<size=50>TÔI. ĐÃ. BẢO. RỒI!==W== Tôi nghỉ việc đấy!!!",
    "CG_npc133_02.279": "Nửa giá...==W== Ôi, đúng là thanh âm êm tai nhất trần đời!==W== Lại còn đúng loại Chuông Tinh Tú chúng ta đang cần nữa chứ?==W== Không thể bỏ lỡ cơ hội này được!",

    # CG_npc172_01
    "CG_npc172_01.4": "Hồi 1",
    "CG_npc172_01.5": "Thiên Thần Áo Trắng",
    "CG_npc172_01.6": "Rảo bước giữa những tòa tháp sao, một thiếu nữ thuần khiết không mang đôi cánh—nhưng lại được muôn người tôn xưng là \"thiên thần\".",
    "CG_npc172_01.88": "==PLAYER_NAME==!",
    "CG_npc172_01.117": "Nguy rồi, một mình mình không đấu lại chúng đâu...==W== Phải chuồn thôi!",
    "CG_npc172_01.168": "Cảm ơn cậu nhé, tôi thấy đỡ hơn nhiều rồi. Tôi là ==PLAYER_NAME== đến từ Lữ Đoàn Tân Tinh. Cậu cũng có thể gọi tôi là Boss.",
    "CG_npc172_01.183": "Ái chà! Khốn khiếp... Lại là con Tinh Linh Thể khi nãy sao?",
    "CG_npc172_01.215": "<size=50>Aaaa—",

    # CG_npc172_02
    "CG_npc172_02.4": "Hồi 2",
    "CG_npc172_02.5": "Chế Độ Ăn Uống Lành Mạnh",
    "CG_npc172_02.6": "Phàm ăn tục uống là ngọn nguồn của mọi tai ương. Cứ kiên trì giữ chế độ ăn uống lành mạnh, cậu sẽ tránh được khối rắc rối đấy.",
    "CG_npc172_02.88": "Noya và Amber",
    "CG_npc172_02.105": "Lần trước tôi đã gây cho cô ấy phiền phức lớn. Vẫn chưa có dịp nói lời cảm ơn đàng hoàng nữa.",
    "CG_npc172_02.163": "Không, chuyện là... Tôi từng ăn một hộp cơm thịt cốt lết ở đó rồi bị bắt làm chân thu ngân suốt một dạo...==W== May mà nhờ có Lữ Đoàn Tân Tinh đến giải cứu.",

    # CG_npc173_01
    "CG_npc173_01.4": "Hồi 1",
    "CG_npc173_01.5": "Sự Cám Dỗ Của Ác Ma",
    "CG_npc173_01.6": "Ác ma ấy bước ra từ Phòng Trắng, chìa ra miếng mồi nhử hòng lôi kéo cậu chìm vào vực thẳm.",
    "CG_npc173_01.149": "Khò khò...==W==<size=30> Khò khò...</size>",
    "CG_npc173_01.166": "Tôi chỉ cùng đồng đội trong đoàn đi tìm Hộp Ước Nguyện thôi mà.==W== Khoan đã—sao tôi lại nhìn thấy cậu được?",
    "CG_npc173_01.185": "Nhưng mà...==W== chẳng phải tôi nên trở về Phòng Trắng sao? Sao tôi vẫn còn ở đây?",

    # CG_npc173_02
    "CG_npc173_02.4": "Hồi 2",
    "CG_npc173_02.5": "Duyên Do Định Mệnh",
    "CG_npc173_02.6": "Tìm thấy người thương giữa biển người mênh mông... Phải chăng là sự an bài của số phận, hay đơn thuần chỉ là kết quả của sự kiên nhẫn đợi chờ?",
    "CG_npc173_02.77": "<size=50>Oái?! Ai ở đó thế?!",
    "CG_npc173_02.146": "<size=50>Chỉ trong chớp mắt thôi sao?!",
    "CG_npc173_02.208": "Vấn đề đâu phải ở chỗ đó...==W== Mọi người trong đoàn sẽ phát hoảng lên nếu tôi tự dưng bốc hơi mất dạng đấy!",
    "CG_npc173_02.223": "<size=50>Tuyệt đối không!",

    # CG_npc174_01
    "CG_npc174_01.4": "Hồi 1",
    "CG_npc174_01.5": "Thử Thách Của Ác Ma",
    "CG_npc174_01.6": "Ác ma ấy bước ra từ phòng trắng, sẵn sàng đưa ra một bài thử thách đặc biệt dành cho bạn.",

    # CG_npc174_02
    "CG_npc174_02.4": "Hồi 2",
    "CG_npc174_02.5": "Hành Trình Giữa Những Trang Sách",
    "CG_npc174_02.6": "Từng con chữ và nét vẽ trong những trang sách của cô ấy không đơn thuần chỉ là trò tiêu khiển. Lưu giữ giữa những trang giấy ấy là nỗi khát khao được cùng Bạo Chúa rong ruổi trên chuyến hành trình viễn xứ.",
    "CG_npc174_02.148": "<size=30>Bernina... Lát nữa chúng ta sẽ tính sổ sau...",
    "CG_npc174_02.171": "Biên niên sử Nova... Các Du Hành Giả thường nhận được khi đặt chân đến vùng đất mới. Trong đó ghi chép về các Hoang Đô địa phương, tình trạng Cự Thạch, đôi khi còn có cả bảng tin ủy thác... Đúng là cuốn đó không?",
    "CG_npc174_02.237": "Cơ hội được chu du thế này quả thực là một đặc ân hiếm có. Tôi nhất định phải chuẩn bị thật chu đáo để trân trọng từng phút từng giây."
}

# Regex replacements for general polish
LEXICAL_REPLACEMENTS = [
    (r"\bmàn một\b", "Hồi 1"),
    (r"\bnhững người đi bộ\b", "các Du Hành Giả"),
    (r"\bngười đi bộ\b", "Du Hành Giả"),
    (r"\bHội Ngôi Sao Mới\b", "Lữ Đoàn Tân Tinh"),
    (r"\bHiệp hội Ngôi sao Mới\b", "Lữ Đoàn Tân Tinh"),
    (r"\bhội ngôi sao mới\b", "Lữ Đoàn Tân Tinh"),
    (r"\bHổ phách\b", "Amber"),
    (r"\bhổ phách\b", "Amber"),
    (r"\bDiên vĩ\b", "Iris"),
    (r"\bdiên vĩ\b", "Iris"),
    (r"\bchết tiệt\b", "khốn khiếp"),
    (r"\bMonolith\b", "Cự Thạch"),
    (r"\bStella Coins\b", "Đồng Stella"),
    (r"\bStar Bells\b", "Chuông Tinh Tú"),
    (r"\bStellaroid\b", "Tinh Linh Thể"),
    (r"\bArtifact\b", "Cổ Vật"),
    (r"\bWishing Box\b", "Hộp Ước Nguyện"),
    (r"\bBạo quân\b", "Bạo Chúa"),
    (r"\bBạo Quân\b", "Bạo Chúa"),
]

TAG_PATTERN = re.compile(r'<[^>]+>|==[a-zA-Z0-9_.-]+==|\{[0-9]+\}|_NOT_IN_LOG_')

proposals = []
for item in source_items:
    item_id = item["id"]
    en = item["en"]
    raw_vi = item["current_vi"]

    if item_id in OVERRIDES:
        final_text = OVERRIDES[item_id]
    else:
        text = raw_vi
        for pat, repl in LEXICAL_REPLACEMENTS:
            text = re.sub(pat, repl, text)
        final_text = text

    # Verify tokens
    src_tokens = TAG_PATTERN.findall(en)
    tgt_tokens = TAG_PATTERN.findall(final_text)

    # Allow unclosed size tags if present in EN
    if src_tokens != tgt_tokens:
        # Check if difference is only unclosed size tag or spacing
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

print(f"Successfully generated {len(proposals)} Partition A proposals to {OUT_PATH}")
