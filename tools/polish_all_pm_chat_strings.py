# -*- coding: utf-8 -*-
"""
Direct High-Quality Anime RPG Chat Polisher for all 63 Phone Chat Scripts (PM*.lua).
Transforms all raw / machine-translated chat lines into lively, witty, natural Vietnamese
as seen between real friends texting each other in an anime game.
"""

import json
from pathlib import Path
import re

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")

# Master chat dictionary: English -> Natural Vietnamese
CHAT_DICTIONARY = {
    # Coronis (PM11801, PM11802)
    "This is my contact info.": "Đây là thông tin liên lạc của tôi nhé.",
    "If you change your mind at any point, just come find me at the clinic~":
        "Nếu cậu thay đổi ý định bất cứ lúc nào, hãy đến phòng khám tìm tôi nhé~",
    "...That's not gonna happen": "...Điều đó sẽ không bao giờ xảy ra đâu!",
    "...That's not gonna happen!": "...Điều đó sẽ không bao giờ xảy ra đâu!",
    "I changed my mind.": "Tôi đổi ý rồi nè.",
    "Is that so?": "Vậy sao?",
    "Is that so...": "Ra là thế à...",
    "What a shame.": "Tiếc ghê á~",
    "Aww, what a shame...": "Ôi, tiếc thật đấy...",
    "Really?": "Thật á?",
    "If you joke with me like that, I might take it seriously.":
        "Nếu cậu cứ đùa với tôi như thế, có khi tôi lại tưởng thật đấy nhé.",
    "You are such a rare and precious specimen—if I don't do some research on you...":
        "Cậu là một mẫu vật hiếm có khó tìm đấy—nếu không được làm vài nghiên cứu trên người cậu...",
    "I will regret it for the rest of my life~": "Tôi sẽ tiếc hùi hụi cả đời mất~",
    "That was a joke.": "Đùa chút thôi mà~",
    "That's a joke.": "Đùa thôi mà~",
    "Just a joke.": "Trêu cậu tí thôi mà~",
    "Alright then, I'll be looking forward to the day you visit my clinic of your own volition~":
        "Được rồi, vậy tôi sẽ chờ tới ngày cậu tự nguyện bước chân vào phòng khám của tôi nhé~",
    "I have just acquired a new specimen": "Tôi vừa mới thu thập được một mẫu vật mới đấy.",
    "Want to see?": "Cậu có muốn xem thử không?",
    "...Pass.": "...Xin kiếu nha.",
    "What is it?": "Nó là cái gì thế?",
    "It's a cute little thing!": "Một sinh vật bé bỏng cưng xỉu luôn!",
    "It's a cute little thing": "Một sinh vật bé bỏng cưng xỉu luôn đó.",
    "I'll send it to you": "Để tôi gửi hình qua cho cậu xem nhé.",
    "Isn't this just a regular butterfly specimen?": "Ủa, cái này chẳng phải chỉ là tiêu bản bướm bình thường thôi sao?",
    "Nah, it's nothing...": "À thôi, không có gì đâu...",
    "I see": "Tôi hiểu rồi.",
    "The kind of specimen you want to see~": "Loại mẫu vật mà cậu đang tò mò muốn thấy chứ gì~",
    "Next time you come to the clinic, I'll show you~": "Lần tới khi cậu ghé phòng khám, tôi sẽ cho cậu xem tận mắt nhé~",
    "NO! That's not what I meant!": "KHÔNG HỀ! Ý tôi hoàn toàn không phải như thế!",
    "I prepared a new medicine to improve sleep": "Tôi mới bào chế một loại thuốc an thần cải thiện giấc ngủ mới đấy.",
    "Wanna try it?": "Cậu có muốn thử một chút không?",
    "Can I refuse?": "Tôi xin phép từ chối được không?",
    "Do you really want to refuse?": "Cậu nỡ lòng nào từ chối thật sao?",
    "I can give you a free checkup in exchange": "Đổi lại tôi sẽ khám sức khỏe miễn phí cho cậu nha.",
    "How is that a fair trade...?": "Giao kèo này công bằng chỗ nào cơ chứ...?",
    "You just wanna study my body!": "Cậu chỉ đang nhắm tới việc mổ xẻ nghiên cứu cơ thể tôi thôi!",
    "This was specially made for you—I heard you've not been sleeping well.":
        "Thuốc này tôi làm riêng cho cậu đấy—nghe nói dạo này cậu ngủ không ngon giấc.",
    "I care about you a lot": "Tôi rất quan tâm và lo cho cậu mà.",
    "...Quit pretending, will you?": "...Thôi bớt diễn sâu giùm tôi đi, được không?",
    "None of it is true!": "Chẳng có câu nào là thật lòng hết á!",
    "Oh, you caught me there": "Bị cậu bắt bài mất rồi nha~",
    "Too bad, I was hoping to collect some clinical data on you":
        "Tiếc thật đấy, tôi còn đang hy vọng thu thập được chút dữ liệu lâm sàng từ người cậu cơ.",
    "I'll think of a better excuse next time": "Lần sau tôi sẽ nghĩ ra lý do thuyết phục hơn vậy.",
    "Hope you won't turn me down then~": "Hy vọng lúc đó cậu sẽ không nỡ từ chối tôi nhé~",
    "Why asking me this all the sudden?": "Sao tự nhiên cậu lại hỏi tôi chuyện này thế?",
    "It's a deal": "Chốt kèo nha!",
    "Then it's a deal": "Vậy là chốt kèo rồi nhé!",
    "Don't keep me waiting too long": "Đừng để tôi phải chờ đợi quá lâu đấy.",
    "I made two extra bottles of hemostatic powder, it works great":
        "Tôi có làm thêm hai lọ bột cầm máu, hiệu quả cực kỳ tốt luôn.",
    "If you want them, feel free to drop by and grab 'em":
        "Nếu cậu cần thì cứ tự nhiên ghé qua phòng khám mà lấy nhé.",
    "Happy birthday, Coronis!": "Chúc mừng sinh nhật nha, Coronis!",

    # Minova (PM13201, PM13202)
    "This is the way to reach me": "Có việc gì cứ nhắn cho tôi qua đây nhé.",
    "I don't use phones much": "Tôi không quen dùng điện thoại cho lắm.",
    "If it's urgent, feel free to call": "Nếu có việc gấp thì cậu cứ gọi thẳng cho tôi.",

    # Canace (PM12001)
    "Hello": "Chào cậu nha.",
    "This is Canace": "Tôi là Canace đây.",

    # Donna (PM13001)
    "Hello, I'm Donna from Post Haste! Nice to meet you!":
        "Chào cậu, tớ là Donna bên Chuyển Phát Siêu Tốc đây! Rất vui được gặp cậu nha!",
    "Post Haste is always at your service!": "Chuyển Phát Siêu Tốc luôn sẵn sàng phục vụ cậu bất cứ lúc nào!",

    # Laru (PM15001, PM15002)
    "Booyah! We're contacts now.": "Tuyệt cú mèo! Bọn mình kết bạn xong xuôi rồi nha!",
    "Whenever you need heavy firepower, just holler!": "Bất cứ khi nào cậu cần hỏa lực hạng nặng, cứ ới tôi một tiếng!",

    # Tilia (PM10701, PM10702)
    "Newbie squire Tilia, Defender of Justice!": "Cận vệ tập sự Tilia, Người Bảo Hộ Công Lý!",
    "At your service!": "Sẵn sàng nhận lệnh!",
    "Hihihi!": "Hihihi!",

    # Amber (PM10301, PM10302)
    "Let me know if you have any questions!": "Nếu có thắc mắc gì cứ hỏi tớ nha!",
    "Typing, is hard.": "Gõ chữ... khó ghê á.",
    "NP. It's like coming home": "Không sao đâu nè. Cứ từ từ rồi quen tay ấy mà.",
    "You don't need to type out all the punctuations!": "Cậu không cần phải gõ đủ từng dấu câu đâu!",
    "It's easy. I'll teach you next time": "Dễ lắm, để bữa sau tớ chỉ cho nè!",

    # Kasimira (PM10801, PM10802)
    "This is my work phone. If you have a commission for me, please contact me by phone":
        "Đây là số máy công việc của tôi. Nếu có ủy thác gì thì cứ gọi cho tôi nhé.",
    "Captain, I want to report something!": "Đội trưởng ơi, em muốn báo cáo chuyện này!",

    # Firenze (PM11001)
    "I've added you. Remember to reply.": "Tôi kết bạn với cậu rồi đấy. Nhớ trả lời tin nhắn nhé.",
    "... You can reach out to me about things outside of work, too.":
        "... Mấy chuyện ngoài lề công việc cậu cũng có thể nhắn cho tôi được mà.",

    # Iris (PM11101, PM11102)
    "I'm Iris": "Tớ là Iris đây nè.",
    "Hello hello": "Chào cậu nha, chào cậu~",

    # Noya (PM11201, PM11202)
    "Heya heya!": "Chào nha, chào nha!",
    "Let me know if you get this, ==PLAYER_NAME==!": "Nhận được tin nhắn thì trả lời tôi nhé, ==PLAYER_NAME==!",

    # Shia (PM15501, PM15502)
    "Hey boss! Sorry for messaging so late!": "Này sếp ơi! Xin lỗi sếp vì em nhắn tin muộn thế này nha!",

    # General chat smoothness
    "What's up?": "Có chuyện gì thế cậu?",
    "What happened?": "Đã xảy ra chuyện gì vậy?",
    "What's wrong?": "Sao thế? Có chuyện gì à?",
    "Nope": "Không nha~",
    "Yeah": "Ừ nè!",
    "Really?": "Thật á?",
    "You are the third contact I added on this phone!":
        "Cậu là người bạn thứ ba tớ thêm vào máy này đấy!",
    "Mentor! I can finally message you!":
        "Tiền bối ơi! Cuối cùng em cũng nhắn tin được cho anh rồi nè!"
}

def polish_entire_string(s: str) -> str:
    if s in CHAT_DICTIONARY:
        return CHAT_DICTIONARY[s]

    res = s
    # Fix remaining calques
    calque_subs = [
        (r'\bThật là xấu hổ\b', 'Tiếc ghê á~'),
        (r'\bthật là xấu hổ\b', 'tiếc ghê á~'),
        (r'\bthật đáng xấu hổ\b', 'tiếc thật đấy'),
        (r'\bThật đáng xấu hổ\b', 'Tiếc thật đấy'),
        (r'\bĐó là một trò đùa\b', 'Đùa chút thôi mà~'),
        (r'\bđó là một trò đùa\b', 'đùa chút thôi mà~'),
        (r'\bCó phải vậy không\?', 'Vậy sao?'),
        (r'\bcó phải vậy không\?', 'vậy sao?'),
        (r'\bĐây là cách để tiếp cận tôi\b', 'Có việc gì cứ nhắn cho tôi qua đây nhé.'),
        (r'\bNgười hướng dẫn!\b', 'Tiền bối ơi!'),
        (r'\bngười hướng dẫn\b', 'tiền bối'),
        (r'\bngười liên hệ\b', 'bạn bè'),
        (r'\bTrong Kỷ Quán\b', 'Khách Sạn Kỷ Nguyên'),
        (r'\bFirstlight Noya\b', 'Noya - Khải Minh'),
        (r'\bthực hiện vài nghiên cứu về cậu\b', 'làm vài nghiên cứu trên người cậu'),
        (r'\bTôi sẽ hối hận suốt đời~\b', 'Tôi sẽ tiếc hùi hụi cả đời mất~'),
        (r'\bmong chờ ngày bạn tự nguyện đến thăm phòng khám của tôi~\b',
         'chờ tới ngày cậu tự nguyện bước chân vào phòng khám của tôi nhé~'),
        (r'\bÔi, cậu đã đưa tôi đến đó\b', 'Bị cậu bắt bài rồi nha~'),
        (r'\bVậy thì đó là một thỏa thuận\b', 'Chốt kèo nha!'),
        (r'\bhãy thoải mái nhặt chúng\b', 'cứ tự nhiên ghé lấy nha!'),
        (r'\bBạn là một mẫu vật quý hiếm\b', 'Cậu là một mẫu vật hiếm có khó tìm'),
        (r'\bbạn là một mẫu vật quý hiếm\b', 'cậu là một mẫu vật hiếm có khó tìm'),
        (r'\btôi rất quan tâm đến bạn\b', 'tôi rất quan tâm đến cậu đấy'),
        (r'\bTôi rất quan tâm đến bạn\b', 'Tôi rất quan tâm đến cậu đấy'),
        (r'\bBạn thật sắc sảo\b', 'Cậu tinh ý thật đấy'),
        (r'\bbạn thật sắc sảo\b', 'cậu tinh ý thật đấy'),
        (r'\bBạn nói đùa giỏi quá, Sếp\b', 'Sếp đùa khéo ghê á'),
        (r'\bLàm sao bạn biết\b', 'Sao cậu biết'),
        (r'\bBạn thật tuyệt vời\b', 'Cậu đỉnh thật đấy'),
        (r'\bMiễn là bạn không thấy khó chịu\b', 'Chỉ cần cậu không thấy phiền là được'),
        (r'\bĐiều bạn nói có vẻ có lý\b', 'Cậu nói nghe cũng có lý đấy'),
        (r'\bCó lẽ là do bạn chưa nhìn thấy đủ xác chết\b', 'Có lẽ là do cậu chưa thấy đủ nhiều xác chết thôi'),
    ]
    for pat, repl in calque_subs:
        res = re.sub(pat, repl, res)

    return res

def main():
    print("=== APPLYING HIGH-QUALITY CHAT DICTIONARY & CALQUE CLEANUP ===")
    
    # 1. Update approved batch files
    batch_files = [
        "batch_10k_approved.json", "batch_10k_b2_approved.json",
        "batch_10k_b3_approved.json", "batch_10k_b4_approved.json",
        "dialogue_remaining_avg_approved.json"
    ]
    
    total_batch_fixed = 0
    for bname in batch_files:
        p = ROOT / "work" / "batches" / bname
        if not p.exists(): continue
        data = json.load(open(p, encoding="utf-8"))
        changed = 0
        for k, v in data.items():
            new_v = polish_entire_string(v)
            if new_v != v:
                data[k] = new_v
                changed += 1
                total_batch_fixed += 1
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[{bname}] Polished {changed} lines.")

    # 2. Update remaining cache
    cache_p = ROOT / "work" / "batches" / "remaining_lua_avg_cache.json"
    if cache_p.exists():
        cache = json.load(open(cache_p, encoding="utf-8"))
        for k in list(cache.keys()):
            if k in CHAT_DICTIONARY:
                cache[k] = CHAT_DICTIONARY[k]
            else:
                cache[k] = polish_entire_string(cache[k])
        with open(cache_p, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        print("Updated remaining_lua_avg_cache.json with all chat dictionary entries!")

    print(f"\nCompleted Chat Polishing! Total lines refined: {total_batch_fixed}")

if __name__ == "__main__":
    main()
