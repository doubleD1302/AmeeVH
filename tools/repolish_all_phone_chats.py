# -*- coding: utf-8 -*-
"""
Deep rewrite and anti-calque polisher for all Phone Chats (PM*.lua) and Story Dialogue.
Eliminates:
- "Thật là xấu hổ" for "What a shame" -> "Tiếc ghê á~" / "Uổng thật đấy~"
- "Đó là một trò đùa" for "That was a joke" -> "Đùa chút thôi mà~" / "Trêu cậu tí thôi mà~"
- "Có phải vậy không?" for "Is that so?" -> "Vậy sao?" / "Thế cơ à?"
- "Đây là cách để tiếp cận tôi" for "This is the way to reach me" -> "Có việc gì cứ nhắn cho tôi qua đây nhé."
- "Tôi sử dụng điện thoại này cho những việc không liên quan đến công việc" -> "Tôi dùng máy này để nói mấy chuyện ngoài lề công việc thôi nhé."
- "Người hướng dẫn! Cuối cùng tôi cũng có thể..." -> "Tiền bối ơi! Cuối cùng em cũng nhắn tin được cho anh rồi nè!"
- "Bây giờ chúng ta là người liên hệ" -> "Bọn mình kết bạn xong xuôi rồi nha!"
- "Trong Kỷ Quán" -> "Khách Sạn Kỷ Nguyên"
- "Firstlight Noya" -> "Noya - Khải Minh"
- Eliminates mixing "bạn" and "cậu" in the same paragraph/sentence.
"""

import json
from pathlib import Path
import re

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")

# Specific exact phrase mappings for English -> Vietnamese in phone chats
EXACT_CHAT_FIXES = {
    "What a shame.": "Tiếc ghê á~",
    "What a shame": "Tiếc ghê á~",
    "Aww, what a shame...": "Ôi, tiếc thật đấy...",
    "That was a joke.": "Đùa chút thôi mà~",
    "That's a joke.": "Đùa thôi mà~",
    "Just a joke.": "Trêu cậu tí thôi mà~",
    "Is that so?": "Vậy sao?",
    "Is that so...": "Ra là thế à...",
    "Is that it?": "Chỉ vậy thôi á?",
    "It's a deal": "Chốt kèo nha!",
    "That's a deal": "Quyết định vậy đi nhé!",
    "Then that's a deal": "Thống nhất thế nhé!",
    "You caught me there": "Bị cậu bắt bài rồi nha~",
    "You got me there": "Bị cậu phát hiện rồi nha~",
    "Feel free to pick them up": "Cứ tự nhiên ghé lấy nhé!",
    "Feel free to drop by": "Cứ qua lấy bất cứ lúc nào nha!",
    "This is the way to reach me": "Có việc gì cứ nhắn cho tôi qua đây nhé.",
    "This is my contact info.": "Đây là thông tin liên lạc của tôi nhé.",
    "I use this phone for non-work stuff.": "Tôi dùng máy này để nói mấy chuyện ngoài lề công việc thôi nhé.",
    "I finally managed to add you as a friend!": "Cuối cùng tớ cũng kết bạn được với cậu rồi nè!",
    "Mentor! I can finally message you!": "Tiền bối ơi! Cuối cùng em cũng nhắn tin được cho anh rồi nè!",
    "Booyah! We're contacts now.": "Tuyệt cú mèo! Bọn mình kết bạn xong xuôi rồi nha!",
    "Why asking me this all the sudden?": "Sao tự nhiên cậu lại hỏi tôi chuyện này thế?",
    "Hello, I'm Donna from Post Haste! Nice to meet you!": "Chào cậu, tớ là Donna bên Chuyển Phát Siêu Tốc đây! Rất vui được gặp cậu nha!",
    "You are such a rare and precious specimen—if I don't do some research on you...":
        "Cậu là một mẫu vật hiếm có khó tìm đấy—nếu không được làm vài nghiên cứu trên người cậu...",
    "I will regret it for the rest of my life~": "Tôi sẽ tiếc hùi hụi cả đời mất~",
    "Alright then, I'll be looking forward to the day you visit my clinic of your own volition~":
        "Được rồi, vậy tôi sẽ chờ tới ngày cậu tự nguyện bước chân vào phòng khám của tôi nhé~",
    "Hello": "Xin chào nha",
    "Firstlight Noya": "Noya - Khải Minh",
    "Post Haste": "Chuyển Phát Siêu Tốc",
    "It's like coming home": "Cứ từ từ rồi quen tay ấy mà.",
    "Typing, is hard.": "Gõ chữ... khó ghê á.",
    "NP. It's like coming home": "Không sao đâu nè. Cứ từ từ rồi quen tay ấy mà.",
    "You don't need to type out all the punctuations!": "Cậu không cần phải gõ đủ từng dấu câu đâu!",
    "It's easy. I'll teach you next time": "Dễ lắm, để bữa sau tớ chỉ cho nè!"
}

# General regex pattern replacements for Vietnamese text
VI_CHAT_REWRITES = [
    # 1. Catastrophic calques
    (r'\bThật là xấu hổ\b', 'Tiếc ghê á~'),
    (r'\bthật là xấu hổ\b', 'tiếc ghê á~'),
    (r'\bthật đáng xấu hổ\b', 'tiếc thật đấy'),
    (r'\bThật đáng xấu hổ\b', 'Tiếc thật đấy'),
    (r'\bĐó là một trò đùa\b', 'Đùa chút thôi mà~'),
    (r'\bđó là một trò đùa\b', 'đùa chút thôi mà~'),
    (r'\bCó phải vậy không\?', 'Vậy sao?'),
    (r'\bcó phải vậy không\?', 'vậy sao?'),
    (r'\bĐây là cách để tiếp cận tôi\b', 'Có việc gì cứ nhắn cho tôi qua đây nhé.'),
    (r'\bTôi sử dụng điện thoại này cho những việc không liên quan đến công việc\b',
     'Tôi dùng máy này để nói mấy chuyện ngoài lề công việc thôi nhé.'),
    (r'\bngười liên hệ\b', 'bạn bè'),
    (r'\bNgười hướng dẫn!\b', 'Tiền bối ơi!'),
    (r'\bngười hướng dẫn\b', 'tiền bối'),
    (r'\bTrong Kỷ Quán\b', 'Khách Sạn Kỷ Nguyên'),
    (r'\bkhách sạn Trong Kỷ\b', 'Khách Sạn Kỷ Nguyên'),
    (r'\bthực hiện vài nghiên cứu về cậu\b', 'làm vài nghiên cứu trên người cậu'),
    (r'\bthực hiện vài nghiên cứu về bạn\b', 'làm vài nghiên cứu trên người cậu'),
    (r'\bTôi sẽ hối hận suốt đời~\b', 'Tôi sẽ tiếc hùi hụi cả đời mất~'),
    (r'\bmong chờ ngày bạn tự nguyện đến thăm phòng khám của tôi~\b',
     'chờ tới ngày cậu tự nguyện bước chân vào phòng khám của tôi nhé~'),
    (r'\bÔi, cậu đã đưa tôi đến đó\b', 'Bị cậu bắt bài rồi nha~'),
    (r'\bVậy thì đó là một thỏa thuận\b', 'Chốt kèo nha!'),
    (r'\bhãy thoải mái nhặt chúng\b', 'cứ tự nhiên ghé lấy nha!'),
    (r'\bthoải mái nhặt chúng\b', 'tự nhiên ghé lấy nhé!'),

    # 2. Consistent pronouns in chat - remove remaining "bạn" when addressed to player
    (r'\bBạn là một mẫu vật quý hiếm\b', 'Cậu là một mẫu vật hiếm có khó tìm'),
    (r'\bbạn là một mẫu vật quý hiếm\b', 'cậu là một mẫu vật hiếm có khó tìm'),
    (r'\btôi rất quan tâm đến bạn\b', 'tôi rất quan tâm đến cậu đấy'),
    (r'\bTôi rất quan tâm đến bạn\b', 'Tôi rất quan tâm đến cậu đấy'),
    (r'\bBạn thật sắc sảo\b', 'Cậu tinh ý thật đấy'),
    (r'\bbạn thật sắc sảo\b', 'cậu tinh ý thật đấy'),
    (r'\bBạn nói đùa giỏi quá, Sếp\b', 'Sếp đùa khéo ghê á'),
    (r'\bbạn nói đùa giỏi quá\b', 'cậu đùa khéo ghê á'),
    (r'\bLàm sao bạn biết\b', 'Sao cậu biết'),
    (r'\blàm sao bạn biết\b', 'sao cậu biết'),
    (r'\bBạn thật tuyệt vời\b', 'Cậu đỉnh thật đấy'),
    (r'\bbạn thật tuyệt vời\b', 'cậu đỉnh thật đấy'),
    (r'\bMiễn là bạn không thấy khó chịu\b', 'Chỉ cần cậu không thấy phiền là được'),
    (r'\bĐiều bạn nói có vẻ có lý\b', 'Cậu nói nghe cũng có lý đấy'),
    (r'\bCó lẽ là do bạn chưa nhìn thấy đủ xác chết\b', 'Có lẽ là do cậu chưa thấy đủ nhiều xác chết thôi'),
    (r'\bchưa nhìn thấy đủ\b', 'chưa thấy đủ'),
]

def clean_chat_line(text: str) -> str:
    if not text or not isinstance(text, str):
        return text

    new_t = text
    for pat, repl in VI_CHAT_REWRITES:
        new_t = re.sub(pat, repl, new_t)

    # Clean double pronouns if any left
    new_t = re.sub(r'\bbạn\b(?=\s+(?:ngủ|chưa|nói|thấy|nghĩ|làm|đi|muốn|biết|có|được|thích))', 'cậu', new_t)
    new_t = re.sub(r'\bBạn\b(?=\s+(?:ngủ|chưa|nói|thấy|nghĩ|làm|đi|muốn|biết|có|được|thích))', 'Cậu', new_t)

    return new_t

def main():
    print("=== RE-POLISHING ALL PHONE CHATS & DIALOGUES ===")
    
    batches = [
        "batch_10k_approved.json", "batch_10k_b2_approved.json",
        "batch_10k_b3_approved.json", "batch_10k_b4_approved.json",
        "dialogue_remaining_avg_approved.json"
    ]

    total_changed = 0
    for bname in batches:
        bp = ROOT / "work" / "batches" / bname
        if not bp.exists(): continue
        data = json.load(open(bp, encoding="utf-8"))
        changed = 0
        for k, v in data.items():
            new_v = clean_chat_line(v)
            if new_v != v:
                data[k] = new_v
                changed += 1
                total_changed += 1
        with open(bp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[{bname}] Re-polished {changed} lines.")

    # Also update remaining_lua_avg_cache.json
    cache_p = ROOT / "work" / "batches" / "remaining_lua_avg_cache.json"
    if cache_p.exists():
        cache = json.load(open(cache_p, encoding="utf-8"))
        # Apply exact fixes
        for en, vi in EXACT_CHAT_FIXES.items():
            cache[en] = vi
        # Apply regex rewrites
        for en, vi in cache.items():
            cache[en] = clean_chat_line(vi)
        with open(cache_p, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        print("Updated remaining_lua_avg_cache.json with all exact chat fixes!")

    print(f"\nTotal lines re-polished across all batches: {total_changed}")

if __name__ == "__main__":
    main()
