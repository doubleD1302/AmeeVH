import json
import re

with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA.json', 'r', encoding='utf-8') as f:
    src = json.load(f)
with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA_translated.json', 'r', encoding='utf-8') as f:
    dst = json.load(f)

suspects = [
    r'cắt theo đuổi',
    r'vẽ đường',
    r'cùng một trang',
    r'cái chết được đúc',
    r'làm cứng tôi',
    r'đánh tôi một phát',
    r'sự quyến rũ đó',
    r'chẳng là gì cả',
    r'ở trên đó',
    r'nghe rõ đó',
    r'tầng nó',
    r'vòng lặp',
    r'thả nó xuống',
    r'bánh mì nướng',
    r'nói về ma quỷ',
    r'cắn một miếng',
    r'càu nhàu',
    r'đóng mạng',
    r'bắt đầu lăn',
    r'chính quyền oracle',
    r'thiết bị throne',
    r'ám ảnh cũ',
    r'giành chiến thắng',
    r'ra khỏi đường đi',
    r'đào bới bất cứ ai',
    r'công chức của thượng viện',
    r'lão nguyên viện',
    r'vốn tạm thời',
    r'người dân người',
    r'dân người',
    r'giữ một cái gì đó lớn như vậy từ tôi',
    r'lời đề nghị khiêm tốn',
    r'lắc lư',
    r'phòng lắc lư',
    r'chân trong cửa',
    r'bật nắp',
    r'chiếc thuyền',
    r'không có phòng',
    r'không có chỗ để thở',
    r'câu chuyện của bạn',
    r'thay đổi suy nghĩ của tôi',
    r'bảo vệ mảnh bishop',
    r'mảnh bishop',
    r'thành phố emor',
    r'quận vàng ở',
    r'quận bạc ở',
    r'quận nhà kính ở',
    r'chi nhánh philae của liên hợp thu hoạch',
    r'tiểu thư darcia',
    r'quý cô darcia',
    r'lady darcia',
    r'lady firenze',
    r'desert scorpion',
    r'forest elf',
    r'nightreef',
    r'jade feathers',
]

for s in suspects:
    matches = []
    reg = re.compile(s, re.IGNORECASE)
    for k, v in dst.items():
        if reg.search(v):
            matches.append((k, src.get(k, ''), v))
    if matches:
        print(f"\n--- Suspect: '{s}' ({len(matches)} matches) ---")
        for m in matches[:5]:
            print(f"[{m[0]}]\n  SRC: {m[1]}\n  DST: {m[2]}")
