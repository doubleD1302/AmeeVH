# -*- coding: utf-8 -*-
"""
De-formalization & Natural Youthful Anime Style Polish Module for Stella Sora (v2).
Removes stiff Sino-Vietnamese, courtly archaic terms, and mechanical calques.
Replaces them with lively, natural, friendly Vietnamese appropriate for young anime heroes.
"""

import re

FORMAL_TO_NATURAL_PAIRS = [
    # 1. Stiff pronouns & addressings
    (r'\bCác hạ\b', 'cậu'),
    (r'\bcác hạ\b', 'cậu'),
    (r'\bTại hạ\b', 'tôi'),
    (r'\btại hạ\b', 'tôi'),
    (r'\bBản tọa\b', 'ta'),
    (r'\bbản tọa\b', 'ta'),
    (r'\bHuynh đài\b', 'anh bạn'),
    (r'\bhuynh đài\b', 'anh bạn'),
    (r'\bHiền đệ\b', 'cậu em'),
    (r'\bhiền đệ\b', 'cậu em'),
    (r'\bThị vệ\b', 'cận vệ'),
    (r'\bthị vệ\b', 'cận vệ'),
    (r'\bThương hội\b', 'Hội buôn'),
    (r'\bthương hội\b', 'hội buôn'),
    (r'\bThương Hội\b', 'Hội Buôn'),
    (r'\bĐa tạ\b', 'Cảm ơn nhé'),
    (r'\bđa tạ\b', 'cảm ơn nhé'),

    # 2. Pompous / Archaic courtly phrases
    (r'\bBèo nước gặp nhau\b', 'Vừa mới quen'),
    (r'\bbèo nước gặp nhau\b', 'vừa mới quen'),
    (r'\bOai phong lẫm liệt, khí chất ngút ngàn\b', 'Ngầu đét, phong độ ngời ngời'),
    (r'\boai phong lẫm liệt, khí chất ngút ngàn\b', 'ngầu đét, phong độ ngời ngời'),
    (r'\bOai phong lẫm liệt\b', 'Cực kỳ ngầu'),
    (r'\boai phong lẫm liệt\b', 'cực kỳ ngầu'),
    (r'\bkhí chất ngút ngàn\b', 'phong độ ngút ngàn'),
    (r'\bKhí chất\b', 'Phong thái'),
    (r'\bkhí chất\b', 'phong thái'),
    (r'\ban yên\b', 'bình yên'),
    (r'\bAn yên\b', 'Bình yên'),
    (r'\bthống khổ\b', 'khổ sở'),
    (r'\bThống khổ\b', 'Khổ sở'),
    (r'\bminh ước\b', 'giao kèo'),
    (r'\bMinh ước\b', 'Giao kèo'),
    (r'\bMinh Ước\b', 'Giao Kèo'),
    (r'\bcảm kích khôn nguôi\b', 'thật sự biết ơn cậu rất nhiều'),
    (r'\bCảm kích khôn nguôi\b', 'Thật sự biết ơn cậu rất nhiều'),
    (r'\bkhôn nguôi\b', 'da diết'),
    (r'\bhồi báo\b', 'đền đáp'),
    (r'\bHồi báo\b', 'Đền đáp'),
    (r'\bcứu rỗi\b', 'giải thoát'),
    (r'\bCứu rỗi\b', 'Giải thoát'),

    # 3. Handle 'Bệ hạ' contextually
    (r'Tôi không phải là "Bệ hạ"', 'Tôi có phải Bệ hạ đâu chứ'),
    (r'tôi không phải là "Bệ hạ"', 'tôi có phải Bệ hạ đâu chứ'),
    (r'Tôi không phải là Bệ hạ', 'Tôi có phải Bệ hạ đâu'),
    (r'tôi không phải là Bệ hạ', 'tôi có phải Bệ hạ đâu'),
    (r'thưa bệ hạ\b', 'thưa Bạo Chúa'),
    (r'thưa Bệ hạ\b', 'thưa Bạo Chúa'),
    (r'cho Bệ hạ\b', 'cho Ngài'),
    (r'cho bệ hạ\b', 'cho Ngài'),
    (r'với Bệ hạ\b', 'với Ngài'),
    (r'với bệ hạ\b', 'với Ngài'),

    # 4. Mechanical translation calques
    (r'\bBạn đang nói về cái gì vậy\?', 'Cậu đang nói cái gì thế?'),
    (r'\bbạn đang nói về cái gì vậy\?', 'cậu đang nói cái gì thế?'),
    (r'\bCái gì trên thế giới\?!\b', 'Cái quái gì thế này?!'),
    (r'\bcái gì trên thế giới\?!\b', 'cái quái gì thế này?!'),
    (r'\bCái gì trên thế giới\?', 'Cái quái gì thế này?'),
    (r'\bcái gì trên thế giới\?', 'cái quái gì thế này?'),
    (r'\bvới bạn\b', 'với cậu'),
    (r'\bcủa bạn\b', 'của cậu'),
    (r'\bcho bạn\b', 'cho cậu'),
    (r'\bgặp bạn\b', 'gặp cậu'),
    (r'\bthấy bạn\b', 'thấy cậu'),
    (r'\bgiúp bạn\b', 'giúp cậu'),
    (r'\bchờ bạn\b', 'chờ cậu'),
    (r'\bđợi bạn\b', 'đợi cậu'),
    (r'\bnhìn bạn\b', 'nhìn cậu'),
    (r'\bhỏi bạn\b', 'hỏi cậu'),
    (r'\bbảo bạn\b', 'bảo cậu'),
    (r'\bnhắc bạn\b', 'nhắc cậu'),
    (r'\bvề bạn\b', 'về cậu'),
    (r'\bôm bạn\b', 'ôm cậu'),
    (r'\bgần bạn\b', 'gần cậu'),
    (r'\bbên bạn\b', 'bên cậu'),
    (r'\bkhen bạn\b', 'khen cậu'),
    (r'\bthích bạn\b', 'thích cậu'),
    (r'\byêu bạn\b', 'yêu cậu'),
    (r'\bghét bạn\b', 'ghét cậu'),
    (r'\btin bạn\b', 'tin cậu'),
    (r'\bhiểu bạn\b', 'hiểu cậu'),
    (r'\btheo bạn\b', 'theo cậu'),
    (r'\bnghe bạn\b', 'nghe cậu'),

    # Subject 'bạn' when followed by common verbs (unless 'bạn bè')
    (r'\bBạn có\b', 'Cậu có'),
    (r'\bbạn có\b', 'cậu có'),
    (r'\bBạn đang\b', 'Cậu đang'),
    (r'\bbạn đang\b', 'cậu đang'),
    (r'\bBạn muốn\b', 'Cậu muốn'),
    (r'\bbạn muốn\b', 'cậu muốn'),
    (r'\bBạn sẽ\b', 'Cậu sẽ'),
    (r'\bbạn sẽ\b', 'cậu sẽ'),
    (r'\bBạn đã\b', 'Cậu đã'),
    (r'\bbạn đã\b', 'cậu đã'),
    (r'\bBạn phải\b', 'Cậu phải'),
    (r'\bbạn phải\b', 'cậu phải'),
    (r'\bBạn nên\b', 'Cậu nên'),
    (r'\bbạn nên\b', 'cậu nên'),
    (r'\bBạn đừng\b', 'Cậu đừng'),
    (r'\bbạn đừng\b', 'cậu đừng'),
    (r'\bBạn hãy\b', 'Cậu hãy'),
    (r'\bbạn hãy\b', 'cậu hãy'),
    (r'\bNếu bạn\b', 'Nếu cậu'),
    (r'\bnếu bạn\b', 'nếu cậu'),
    (r'\bKhi bạn\b', 'Khi cậu'),
    (r'\bkhi bạn\b', 'khi cậu'),
    (r'\bVì bạn\b', 'Vì cậu'),
    (r'\bvì bạn\b', 'vì cậu'),
    (r'\bDù bạn\b', 'Dù cậu'),
    (r'\bdù bạn\b', 'dù cậu'),
    (r'\bLiệu bạn\b', 'Liệu cậu'),
    (r'\bliệu bạn\b', 'liệu cậu'),

    # 5. Dialogue & chat smoothers
    (r'\bVâng\. Tôi nghe thấy bạn\.', 'Ừ. Tớ nghe thấy cậu rồi.'),
    (r'\bTôi nghe thấy bạn\b', 'Tớ nghe thấy cậu rồi'),
    (r'\bnghe thấy bạn\b', 'nghe thấy cậu rồi'),
    (r'\bBạn có sao chép không[\s?!]*', 'Cậu có nghe rõ không!?'),
    (r'\bnghe rõ không[\s?!]*', 'nghe rõ không!?'),
    (r'\bĐêm đêm\b', 'Ngủ ngon nhé'),
    (r'\bĐêm nay\.\b', 'Ngủ ngon nhé.'),
    (r'\bThành [Pp]hố\s+[Tt]hành [Pp]hố\b', 'Thành Phố'),
    (r'\blàm thế nào về\b', 'còn chuyện... thì sao?'),
    (r'\bLàm thế nào về\b', 'Còn chuyện... thì sao?'),
    (r'\bnhư thế nào về\b', 'còn về... thì sao?'),
    (r'\bNhư thế nào về\b', 'Còn về... thì sao?'),
]

def deformalize_text(text: str) -> str:
    """Takes a Vietnamese dialogue line and applies natural youthful styling."""
    if not text or not isinstance(text, str):
        return text

    # Protect placeholders: ==...==, <...>, {...}, &...&
    tokens = []
    def save_tok(m):
        tokens.append(m.group(0))
        return f"__T{len(tokens)-1}__"

    shielded = re.sub(r'==[A-Za-z0-9_]+==|<[^>]+>|\{[0-9a-zA-Z_]+\}|&[a-zA-Z0-9_]+&', save_tok, text)

    # Protect "bạn bè", "người bạn", "nhóm bạn", "kết bạn", "các bạn"
    special_preserve = []
    def save_spec(m):
        special_preserve.append(m.group(0))
        return f"__S{len(special_preserve)-1}__"

    shielded = re.sub(r'\b(bạn bè|người bạn|nhóm bạn|kết bạn|các bạn|Bạn bè|Người bạn|Nhóm bạn|Kết bạn|Các bạn)\b', save_spec, shielded)

    # Apply replacement pairs
    for pattern, repl in FORMAL_TO_NATURAL_PAIRS:
        shielded = re.sub(pattern, repl, shielded)

    # Specific phrase cleanups
    shielded = re.sub(r'\bthề trung thành mãi mãi với cậu\b', 'thề nguyện một lòng trung thành với Ngài', shielded)
    shielded = re.sub(r'\bthề trung thành mãi mãi với bạn\b', 'thề nguyện một lòng trung thành với Ngài', shielded)

    # Restore special preserved words
    for i, tok in enumerate(special_preserve):
        shielded = shielded.replace(f"__S{i}__", tok)

    # Restore technical tokens
    for i, tok in enumerate(tokens):
        shielded = shielded.replace(f"__T{i}__", tok)

    return shielded
