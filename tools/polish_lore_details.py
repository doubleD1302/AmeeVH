import json
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
fpath = os.path.join(viet_dir, r"work\research\data_decrypted\entries\00527_0x843b3b0812018dd2.bin")
with open(fpath, "r", encoding="utf-8") as f:
    d = json.load(f)

d["CharacterArchiveContent.14007.2"] = d["CharacterArchiveContent.14007.2"].replace("Xây dựng tùy chỉnh", "Thiết kế chuyên biệt")
d["CharacterArchiveContent.14910.2"] = d["CharacterArchiveContent.14910.2"].replace("Lưu trữ nơi trú ẩn của trọng tài hoàng hôn", "Hồ Sơ Khu Trú Ẩn Trọng Tài Hoàng Hôn").replace("Tên chủ đề:", "Tên đối tượng:")

with open(fpath, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print("Polished character lore details!")
