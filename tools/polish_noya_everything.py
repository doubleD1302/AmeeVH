import json
import os
import re

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
data_dec = os.path.join(viet_dir, r"work\research\data_decrypted\entries")

print("=" * 70)
print("PRIORITY POLISH: All Assets & Texts for Firstlight Noya (ID 112)")
print("=" * 70)

# 1. Polish CharacterDes.112 (Tactics & Builds)
char_des_file = os.path.join(data_dec, "00530_0x189f915177d3b2ff.bin")
with open(char_des_file, "r", encoding="utf-8") as f:
    des_data = json.load(f)

des_data["CharacterDes.112.3"] = "Noya thi triển kiếm pháp độc môn kỳ bí chưa từng ai thấy. Ngay cả khi tung kỹ năng, những đường trường kiếm uyển chuyển của cô vẫn không hề bị đứt quãng."
des_data["CharacterDes.112.9"] = "Lối chơi quét diện rộng biến kỹ năng thành chuỗi trảm kích đa đoạn liên hoàn."
des_data["CharacterDes.112.10"] = "Lối chơi khống chế tầm xa giúp chuyển hóa Đòn Đánh Thường thành đòn đánh tầm xa sau khi thi triển kỹ năng."
des_data["CharacterDes.112.11"] = "Lối chơi quét diện rộng giúp gia tăng phạm vi và sát thương của kiếm khí."
des_data["CharacterDes.112.12"] = "Lối chơi tập trung dồn lực giúp tăng số lượng kiếm khí và cho phép kiếm khí phân tách khi trúng đích."

with open(char_des_file, "w", encoding="utf-8") as f:
    json.dump(des_data, f, ensure_ascii=False, indent=2)
print("Updated CharacterDes.112 (Tactics & Bio) successfully.")

# 2. Polish CharacterArchiveContent.112 (Backstory, RV Loxy, Lore)
archive_file = os.path.join(data_dec, "00527_0x843b3b0812018dd2.bin")
with open(archive_file, "r", encoding="utf-8") as f:
    arc_data = json.load(f)

arc_data["CharacterArchiveContent.11201.2"] = """Tên: Noya
Sinh nhật: 21 tháng 6
Thế lực: Lữ Đoàn Tân Tinh
Sở trường: Bất cứ việc gì của Lữ Khách hoặc liên quan đến xe cộ
Địa chỉ: Ốc Đảo Lai Phúc
Kinh nghiệm: 2 năm
Vũ khí: Vô Danh
Thù lao: 10.000 Dorra... Mức giá này có thấp quá không nhỉ? Cậu biết đấy, cứ đi hỏi Iris xem sao."""

arc_data["CharacterArchiveContent.11203.1"] = "Trích Đoạn Hồ Sơ 1: Ốc Đảo Lai Phúc"
arc_data["CharacterArchiveContent.11203.2"] = """Ốc Đảo Lai Phúc

"Với biệt danh 'Loxy', đây là chiếc xe dã ngoại do một mình Noya tự tay lắp ráp hoàn toàn."
...Đó là những gì Boss bảo tôi nên viết, nhưng thôi nào, sự thật đâu phải như vậy!
Hồi đó, Iris, Amber và tôi đã gom từng đồng Dorra cuối cùng để mua đủ các bộ phận cần thiết cho 'Loxy'. Vậy nên nói đúng ra, đó là công sức của cả nhóm chúng tôi.
Tất cả những gì tôi làm chỉ là lắp động cơ, vô lăng, ghế ngồi, trục xe, khung gầm và những linh kiện nhặt nhạnh khác lại với nhau theo trực giác mách bảo. Thế mà kỳ lạ thay, xe lại chạy ngon lành! Hì hì."""

arc_data["CharacterArchiveContent.11204.2"] = re.sub(r'Thành Phố\s+Thành Phố\s+Thành Phố', 'Thành Phố', arc_data["CharacterArchiveContent.11204.2"])

arc_data["CharacterArchiveContent.11211.2"] = arc_data["CharacterArchiveContent.11211.2"].replace("bạn tình", "đồng đội").replace("Thủy Thể Băng Thể Băng Thể Băng Glopo", "Thủy Quái Băng Glopo")
arc_data["CharacterArchiveContent.11212.2"] = arc_data["CharacterArchiveContent.11212.2"].replace("bạn tình", "đồng đội").replace("Thủy Thể Băng Thể Băng Thể Băng Glopo", "Thủy Quái Băng Glopo")

arc_data["CharacterArchiveContent.11213.1"] = "Chuyện Kể Vũ Khí: Vô Danh"
arc_data["CharacterArchiveContent.11213.2"] = """Truyền thuyết kể rằng đó là một thanh trường kiếm mang sắc xanh ngọc bích thuần khiết.
Một người đã nhặt được thanh kiếm này và cùng với nó mở ra một kỷ nguyên mới rực rỡ.
Nữ diễn viên bước ra khỏi buồng thang máy kỳ diệu, mỉm cười nói với những người bạn đồng hành đang đợi bên ngoài:
"Rốt cuộc thì chiếc hộp bí ẩn cũng đã mở ra... Tôi có thể khẳng định, khoảnh khắc này đánh dấu sự khởi đầu của một thời đại mới! Thần linh đã lắng nghe lời thỉnh cầu của chúng ta."

Vở kịch trên sân khấu đang bước vào hồi cao trào.
Trong số ba cô gái dưới hàng ghế khán giả, chỉ có hai người là còn tỉnh táo.
Một cô gái vươn tay chạm nhẹ vào thanh kiếm bên hông Noya.
"Thanh kiếm của Noya trông giống hệt thanh bảo kiếm trong vở kịch kia kìa. Cậu có nghĩ nó thực sự là thanh kiếm huyền thoại không?"
"Noya vừa mới mua nó ở tiệm rèn hôm qua đấy thôi."
"Thế thì cô ấy cũng mua được một thanh giống hệt rồi. Nghĩ lại thì, cô ấy vẫn chưa thèm đặt tên cho nó nữa. Cậu có nghĩ đặt cho nó một cái tên sẽ đem lại may mắn không?"

"Vô Danh..."
"Hả, Noya, cậu thức rồi đấy à?"
"Đâu có. Cô ấy chỉ đang nói mớ trong mơ thôi."
Đó chính là nguồn gốc vì sao thanh trường kiếm tưởng chừng như hết sức bình thường này lại mang cái tên kỳ lạ như vậy."""

with open(archive_file, "w", encoding="utf-8") as f:
    json.dump(arc_data, f, ensure_ascii=False, indent=2)
print("Updated CharacterArchiveContent.112 (Backstory & Weapon Lore) successfully.")

# 3. Polish Potentials for Noya (58 potentials)
pot_file = os.path.join(data_dec, "00624_0x02ce11eca01b5fc8.bin")
with open(pot_file, "r", encoding="utf-8") as f:
    pot_data = json.load(f)

for k, v in list(pot_data.items()):
    if not k.startswith("Potential.5112"):
        continue
    orig = v
    # Replace Dragon Slash with Thăng Long Trảm
    v = re.sub(r'\bDragon Slash\b', 'Thăng Long Trảm', v, flags=re.IGNORECASE)
    v = re.sub(r'\bChém Rồng\b', 'Thăng Long Trảm', v, flags=re.IGNORECASE)
    # Replace Ruin Wind with Tàn Phong
    v = re.sub(r'\bCơn gió tàn khốc\b', 'Tàn Phong', v, flags=re.IGNORECASE)
    v = re.sub(r'\bGió tàn phá\b', 'Tàn Phong', v, flags=re.IGNORECASE)
    # Replace Sword Aura with Kiếm Khí
    v = re.sub(r'\bhào quang bằng kiếm\b', 'kiếm khí', v, flags=re.IGNORECASE)
    v = re.sub(r'\bhào quang kiếm\b', 'kiếm khí', v, flags=re.IGNORECASE)
    v = re.sub(r'\bhào quang thanh kiếm\b', 'kiếm khí', v, flags=re.IGNORECASE)
    v = re.sub(r'\bluồng khí kiếm\b', 'luồng kiếm khí', v, flags=re.IGNORECASE)
    # Replace Multi Sword Aura
    v = re.sub(r'##Multi Sword Aura#1054#', '##Đa Trọng Kiếm Khí#1054#', v)
    # Replace Sát Thương Kỹ Năng của Ventus with Sát Thương Kỹ Năng hệ Phong
    v = re.sub(r'Sát Thương Kỹ Năng của Ventus', 'Sát Thương Kỹ Năng hệ Phong', v)
    v = re.sub(r'Sát Thương Đòn Đánh Thường của Ventus', 'Sát Thương Đòn Đánh Thường hệ Phong', v)
    v = re.sub(r'xử lý (<color=[^>]+>[^<]+</color>) dưới dạng Sát Thương', r'gây \1 thành Sát Thương', v)
    
    pot_data[k] = v

with open(pot_file, "w", encoding="utf-8") as f:
    json.dump(pot_data, f, ensure_ascii=False, indent=2)
print("Updated Potential.5112 (58 Noya Potentials) with martial arts terminology.")

# 4. Polish Dating Events for Noya
dating_file = os.path.join(data_dec, "00544_0xd46d025e8dae5d69.bin")
with open(dating_file, "r", encoding="utf-8") as f:
    dat_data = json.load(f)

if "DatingCharacterEvent.112301.3" in dat_data:
    dat_data["DatingCharacterEvent.112301.3"] = """Hai người cùng nhau hái những cây nấm gần đó và thưởng thức một bữa no nê.

Dù nấm rất ngon nhưng bạn bắt đầu cảm thấy đầu óc quay cuồng.
"Không sao đâu, cùng lắm thì tớ cõng cậu đi!" Sau một lúc nghỉ ngơi, Noya đỡ bạn dậy và cả hai tiếp tục cuộc hành trình."""

if "DatingCharacterEvent.112301.5" in dat_data:
    dat_data["DatingCharacterEvent.112301.5"] = "Món Ngon Ven Đường"

if "DatingCharacterEvent.112302.5" in dat_data:
    dat_data["DatingCharacterEvent.112302.5"] = "Dân Chuyên Nghiệp"

with open(dating_file, "w", encoding="utf-8") as f:
    json.dump(dat_data, f, ensure_ascii=False, indent=2)
print("Updated DatingCharacterEvent.112 (Pronouns & titles polished).")

# 5. Polish UIText & Star Tower Actions
uitext_file = os.path.join(data_dec, "00704_0x87cc29ac0defc2d9.bin")
with open(uitext_file, "r", encoding="utf-8") as f:
    ui_data = json.load(f)

ui_data["UIText.SupportSkill_Mobile.1"] = "Chạm để thi triển <color=#EA5946>Kỹ Năng Viện Trợ</color> của Noya!"
ui_data["UIText.SupportSkill_PC.1"] = "Nhấn <sprite name=Q> để thi triển <color=#EA5946>Kỹ Năng Viện Trợ</color> của Noya!"

with open(uitext_file, "w", encoding="utf-8") as f:
    json.dump(ui_data, f, ensure_ascii=False, indent=2)

st_act_file = os.path.join(data_dec, "00661_0x0c5a624629417ff0.bin")
with open(st_act_file, "r", encoding="utf-8") as f:
    st_act_data = json.load(f)

if "StarTowerEventAction.1129173.1" in st_act_data:
    st_act_data["StarTowerEventAction.1129173.1"] = "Bạn biết đấy, lượng HP của bạn cũng có thể đem ra làm tiền cược mà."
    with open(st_act_file, "w", encoding="utf-8") as f:
        json.dump(st_act_data, f, ensure_ascii=False, indent=2)

print("Updated UIText and StarTowerEventAction for Noya.")

# 6. Polish CharGetLines
cget_file = os.path.join(data_dec, "00536_0x8dcf06b298f46b28.bin")
with open(cget_file, "r", encoding="utf-8") as f:
    cg_data = json.load(f)

cg_data["CharGetLines.11201.1"] = "Mục tiêu là những Tháp Sao ta chưa từng thấy! Đi thôi nào Ma Vương, đã đến lúc lên đường rồi!"
cg_data["CharGetLines.11202.1"] = "Cuộc gặp gỡ đầu tiên là ngẫu nhiên, lần thứ hai là định mệnh... hay đại loại thế. Hả? Nghe chẳng giống tớ chút nào ư?"
cg_data["CharGetLines.11203.1"] = "Hãy cùng nhau bước tiếp mãi mãi nhé!"
cg_data["CharGetLines.11204.1"] = "Chờ Loxy sửa xong, chúng mình hãy cùng nhau đi ngắm Tháp Sao nhé... chỉ hai đứa mình thôi."

with open(cget_file, "w", encoding="utf-8") as f:
    json.dump(cg_data, f, ensure_ascii=False, indent=2)
print("Updated CharGetLines.112 (Noya gacha lines).")

print("=" * 70)
print("ALL FIRSTLIGHT NOYA DATABASE ASSETS POLISHED 100%!")
print("=" * 70)
