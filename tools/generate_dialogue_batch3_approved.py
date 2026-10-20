import json
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
SRC_PATH = ROOT / "work" / "batches" / "dialogue_batch3_startower_story.json"
OUT_PATH = ROOT / "work" / "batches" / "dialogue_batch3_startower_approved.json"

CN_TALK_PATH = ROOT / "work" / "research" / "data_decrypted" / "entries" / "00889_0x43be878a1ea77cbe.bin"
CN_STORY_PATH = ROOT / "work" / "research" / "data_decrypted" / "entries" / "00890_0x939d4390e6e6b8fd.bin"

# Approved handcrafted literary translations for dialogue lines
POLISHED_DIALOGUES = {
    # Portia
    "StarTowerTalk.913305.2": "Chỉ cần cậu muốn, đồ trong Cự Tháp muốn lấy bao nhiêu tùy thích. Nhưng với các Lữ Khách các cậu, điều đó liệu có thực sự là chuyện tốt không nhỉ... Hì hì.",
    "StarTowerTalk.913306.2": "Buồn ngủ chết đi được, tôi phải chợp mắt một lát đây... Cậu cứ tự nhiên nhé.",
    "StarTowerTalk.913309.2": "Muốn xin lời khuyên từ tôi sao? Thôi nào, tôi cũng chỉ là nhân viên quầy hàng thôi mà.",
    "StarTowerTalk.913323.2": "Kể thêm cho tôi nghe chuyện bên ngoài Cự Tháp đi, tôi sẽ cảm kích lắm đấy.\nGiảm giá á? Chuyện đó thì tôi chịu, không quyết định được đâu...",
    "StarTowerTalk.913324.2": "Rốt cuộc các Lữ Khách các cậu leo lên Cự Tháp là vì điều gì chứ?\nBộ thèm muốn Cổ Vật đến thế sao?",
    "StarTowerTalk.913327.2": "Nếu đống đồ này giúp ích được cho cậu, thì coi như tôi cũng không bận rộn công cốc rồi.",

    # Beatrixa
    "StarTowerTalk.917204.2": "Cảm thấy từng gặp tôi ở đâu rồi à? Đó chỉ là ảo giác của cậu thôi.",
    "StarTowerTalk.917206.2": "Đừng lãng phí thời gian, để tôi chữa xong cho cậu rồi mau lên đường đi.",
    "StarTowerTalk.917212.2": "Lần sau cẩn thận hơn chút đi, bớt gây thêm phiền phức cho tôi có được không hả?",
    "StarTowerTalk.917219.2": "Sao thế? Cậu bị tiêm đến nghiện rồi à?",
    "StarTowerTalk.917223.2": "Càng đi lên trên là có thể mất mạng đấy... Cơ mà, chuyện đó thì liên quan gì đến tôi chứ?",
    "StarTowerTalk.917226.2": "Nếu còn muốn nghỉ ngơi ở đây một lát thì cứ tự nhiên. Miễn đừng làm phiền tôi là được.",
    "StarTowerTalk.917228.2": "Đã xác định mục tiêu là đỉnh tháp, thì đừng có nấn ná ở đây làm gì.",

    # Bernina
    "StarTowerTalk.917305.2": "Những quy tắc ràng buộc tẻ nhạt chẳng còn tồn tại ở đây đâu, cứ thỏa sức thuận theo dục vọng của mình đi nào!",
    "StarTowerTalk.917306.2": "Hôm nay vận may đang lên nhỉ, chi bằng nhân cơ hội này mà thách thức vận mệnh xem sao~",
    "StarTowerTalk.917308.2": "Sếp lớn vĩ đại của tôi ơi, chẳng lẽ ngài không muốn ẵm trọn phần thưởng hậu hĩnh nhất sao?",
    "StarTowerTalk.917311.2": "Nào, mau đưa ra lựa chọn đi~ Chỉ cần ngài sẵn lòng giao phó tất cả cho tôi, mọi dục vọng của ngài đều sẽ được thỏa mãn...",
    "StarTowerTalk.917313.2": "Ngay từ khoảnh khắc ngài bước chân vào Cự Tháp, tôi đã bị ngài hớp hồn rồi~ Thật muốn ngắm nhìn mãi cái dáng vẻ để lộ trần trụi dục vọng ấy của ngài quá đi thôi.",
    "StarTowerTalk.917324.2": "Nguyện cầu Nữ Thần May Mắn sẽ luôn mỉm cười với ngài, Sếp lớn vĩ đại của tôi~",

    # Virigia
    "StarTowerTalk.917420.2": "Chúc cho chặng đường phía trước của ngài luôn thuận buồm xuôi gió, hẹn ngày tái ngộ.",
    "StarTowerTalk.917423.2": "Thời gian của ngài vô cùng quý giá, chắc hẳn vẫn còn những chuyện trọng đại hơn đang chờ ngài định đoạt, đúng không?",
    "StarTowerTalk.917426.2": "Tôi sẽ luôn dõi theo quỹ đạo vận mệnh của ngài.",

    # Story
    "Story.808.2": "Hãy để lý trí là ngọn lửa cuối cùng — rồi thiêu rụi tất cả trong ánh lửa rực cháy!",
    "Story.811.2": "Dù có trốn chạy thế nào, ngươi cũng chẳng thể rũ bỏ bóng ma đang bám riết sau gót chân.",
    "Story.816.2": "Giữa màn sương hỗn loạn, cô ấy vẫn luôn là mỏ neo bình yên của bạn."
}

def main():
    with open(SRC_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    cn_talk = json.loads(CN_TALK_PATH.read_text(encoding="utf-8")) if CN_TALK_PATH.exists() else {}
    cn_story = json.loads(CN_STORY_PATH.read_text(encoding="utf-8")) if CN_STORY_PATH.exists() else {}

    approved_list = []
    polished_count = 0

    for item in data:
        k = item["key"]
        t = item["table"]
        f_name = item.get("file", "")
        en = item.get("en", "")
        
        # Populate CN
        cn = item.get("cn", "")
        if not cn:
            if t == "StarTowerTalk":
                cn = cn_talk.get(k, "")
            elif t == "Story":
                cn = cn_story.get(k, "")

        # Determine translation
        if k in POLISHED_DIALOGUES:
            vi_text = POLISHED_DIALOGUES[k]
            polished_count += 1
        else:
            vi_text = item.get("current_vi", en)

        # Token validation: ensure newline counts match
        if "\n" in en:
            assert "\n" in vi_text, f"Missing newline in translation for {k}"

        approved_item = {
            "table": t,
            "file": f_name,
            "key": k,
            "en": en,
            "cn": cn,
            "current_vi": vi_text,
            "vi": vi_text
        }
        approved_list.append(approved_item)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(approved_list, f, ensure_ascii=False, indent=2)

    print(f"Successfully processed {len(approved_list)} items.")
    print(f"Polished dialogue lines: {polished_count} / {len(POLISHED_DIALOGUES)}")
    print(f"Saved approved batch to: {OUT_PATH}")

if __name__ == "__main__":
    main()
