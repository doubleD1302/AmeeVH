#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path("c:/YostarGames/StellaSora_EN/StellaSora_VietHoa")
SRC_PATH = ROOT / "work/batches/batch_10k_b3_partA.json"
DST_PATH = ROOT / "work/batches/batch_10k_b3_partA_translated.json"

with open(SRC_PATH, "r", encoding="utf-8") as f:
    src = json.load(f)
with open(DST_PATH, "r", encoding="utf-8") as f:
    dst = json.load(f)

print(f"Loaded {len(src)} source strings and {len(dst)} translated strings.")

# Rules to detect:
# 1. Monolith: Cự Thạch -> Cự Tháp
# 2. United Harvest: Liên Hợp Thu Hoạch / Thu Hoạch Liên Hợp -> Nông Nghiệp Liên Hợp
# 3. New Star Guild: Hội Ngôi sao / Hiệp hội Ngôi sao / Bang hội Ngôi sao -> Công Hội Tân Tinh
# 4. Boss: Ông chủ / ông chủ -> Sếp / sếp
# 5. Tyrant: Bạo chúa / Bạo Quân -> Bạo Chúa (title)
# 6. Trekker: Người đi bộ / người đi bộ -> Lữ Khách
# 7. Novian: Dân người Novian / người Dân người Novian / người Novian -> người Novia / dân Novia
# 8. Radio/comm calques:
#    - "nghe rõ đó" (from "Copy that") -> "Đã rõ" / "Rõ"
#    - "bạn có nghe thấy tôi nói không" -> "bạn có nghe rõ không!?" / "cậu có nghe rõ không!?"
#    - "ở trên đó" (from "on it") -> "sẽ xử lý ngay" / "lo vụ này ngay"
#    - "đang ở trên đó" -> "đang triển khai ngay"
# 9. Slang / Idioms:
#    - "Tầng nó" (Floor it) -> "Đạp lút ga đi" / "Nhấn hết ga đi"
#    - "thoát khỏi vòng lặp" (out of the loop) -> "mù tịt tin tức" / "tối cổ"
#    - "thả nó xuống" (drop it) -> "đừng nhắc nữa" / "thôi đi"
#    - "bánh mì nướng" (toast) -> "xong đời rồi" / "tiêu đời rồi"
#    - "nói về ma quỷ" (speak of the devil) -> "vừa nhắc tào tháo"
#    - "cắn một miếng" (grab a bite) -> "kiếm chút gì lót dạ" / "ăn chút gì đi"
#    - "người càu nhàu" / "lời càu nhàu" (grunt) -> "lính quèn" / "việc lặt vặt chân tay"
#    - "bọ cạp sa mạc càu nhàu" (Desert Scorpion Grunts) -> "Lính Quèn Bọ Cạp Sa Mạc"
#    - "lão nguyên viện" -> "Thượng viện" / "Viện Nguyên Lão"
#    - "Đóng mạng" (Closing the Net) -> "Giăng Lưới Bủa Vây" / "Khép Lại Mẻ Lưới"
#    - "bắt đầu lăn" (started rolling) -> "bắt đầu ghi hình" / "bấm máy"
#    - "công nghệ cấp cao" (senior tech) -> "kỹ thuật viên thâm niên" / "kỹ sư cao cấp"
#    - "kẻ gây hại" (pest) / "nghe lén" (bugging) -> "kẻ phiền toái" / "làm phiền"
#    - "bạn tình" (partner) -> "đồng đội" / "cộng sự"
#    - "bản dựng" (build) -> "lối chơi" / "cách build"
#    - "kẻ thù" -> "kẻ địch"
#    - "ủy ban" (commission) -> "nhiệm vụ ủy thác" / "ủy thác"
#    - Act titles: "màn một" -> "Hồi 1: ...", "màn hai" -> "Hồi 2: ...", etc.
#    - "lời chúc phúc Cự Thạch" -> "lời chúc phúc của Cự Tháp"

fixes = {}

for k, v in dst.items():
    orig = src.get(k, "")
    new_v = v

    # Check and collect potential fixes
    # We will log everything
    changes = []

    # 1. Engine identifiers and binary
    if any(ord(c) < 32 and c not in '\n\r\t\x0b' for c in orig):
        # Keep intact
        if new_v != orig:
            changes.append(("restore_engine_id", new_v, orig))
            new_v = orig
        continue

    # Let's inspect other lines
    # Monolith
    if "cự thạch" in new_v.lower():
        subbed = re.sub(r'\bCự\s+Thạch\b', 'Cự Tháp', new_v)
        subbed = re.sub(r'\bcự\s+thạch\b', 'cự tháp', subbed)
        if subbed != new_v:
            changes.append(("monolith", new_v, subbed))
            new_v = subbed

    # United Harvest
    if "liên hợp thu hoạch" in new_v.lower() or "thu hoạch liên hợp" in new_v.lower():
        subbed = re.sub(r'\bLiên\s+Hợp\s+Thu\s+Hoạch\b', 'Nông Nghiệp Liên Hợp', new_v)
        subbed = re.sub(r'\bThu\s+Hoạch\s+Liên\s+Hợp\b', 'Nông Nghiệp Liên Hợp', subbed)
        subbed = re.sub(r'\bliên\s+hợp\s+thu\s+hoạch\b', 'Nông Nghiệp Liên Hợp', subbed)
        if subbed != new_v:
            changes.append(("united_harvest", new_v, subbed))
            new_v = subbed

    # New Star Guild
    if any(w in new_v.lower() for w in ["hội ngôi sao", "hiệp hội ngôi sao", "bang hội ngôi sao"]):
        subbed = re.sub(r'\b(Hội|Hiệp hội|Bang hội)\s+[Nn]gôi\s+[Ss]ao(\s+[Mm]ới)?\b', 'Công Hội Tân Tinh', new_v)
        if subbed != new_v:
            changes.append(("new_star_guild", new_v, subbed))
            new_v = subbed

    # Boss -> Sếp
    if re.search(r'\b[Ôô]ng chủ\b', new_v):
        # Be careful if orig was "store owner" or "shopkeeper" vs "Boss"
        if "boss" in orig.lower():
            subbed = re.sub(r'\bÔng chủ\b', 'Sếp', new_v)
            subbed = re.sub(r'\bông chủ\b', 'sếp', subbed)
            if subbed != new_v:
                changes.append(("boss_sep", new_v, subbed))
                new_v = subbed

    # Novian
    if re.search(r'\b(người\s+)?Dân\s+người\s+Novian\b', new_v, re.IGNORECASE) or "người novian" in new_v.lower():
        subbed = re.sub(r'\b(người\s+)?Dân\s+người\s+Novian\b', 'người Novia', new_v, flags=re.IGNORECASE)
        subbed = re.sub(r'\bngười\s+Novian\b', 'người Novia', subbed, flags=re.IGNORECASE)
        subbed = re.sub(r'\bNovian\b', 'Novia', subbed)
        if subbed != new_v:
            changes.append(("novian", new_v, subbed))
            new_v = subbed

    # Trekkers -> Lữ Khách
    if re.search(r'\b[Nn]gười đi bộ\b', new_v):
        if "trekker" in orig.lower():
            subbed = re.sub(r'\bNgười đi bộ\b', 'Lữ Khách', new_v)
            subbed = re.sub(r'\bngười đi bộ\b', 'Lữ Khách', subbed)
            if subbed != new_v:
                changes.append(("trekker", new_v, subbed))
                new_v = subbed

    # Partner -> đồng đội / cộng sự
    if "bạn tình" in new_v:
        subbed = new_v.replace("bạn tình", "đồng đội")
        changes.append(("partner", new_v, subbed))
        new_v = subbed

    # Build -> lối chơi
    if "bản dựng" in new_v:
        subbed = new_v.replace("bản dựng", "lối chơi")
        changes.append(("build", new_v, subbed))
        new_v = subbed

    # Enemy -> kẻ địch
    if "kẻ thù" in new_v:
        subbed = new_v.replace("kẻ thù", "kẻ địch")
        changes.append(("enemy", new_v, subbed))
        new_v = subbed

    # Radio & Idiom calques
    if "nghe rõ đó" in new_v.lower():
        subbed = re.sub(r'\b[Nn]ghe rõ đó\b', 'Đã rõ', new_v)
        if subbed != new_v:
            changes.append(("copy_that", new_v, subbed))
            new_v = subbed

    if "ở trên đó" in new_v and "on it" in orig.lower():
        subbed = new_v.replace("đang ở trên đó", "sẽ xử lý ngay").replace("ở trên đó", "lo liệu ngay")
        changes.append(("on_it", new_v, subbed))
        new_v = subbed

    if "tầng nó" in new_v.lower() and "floor it" in orig.lower():
        subbed = re.sub(r'\b[Tt]ầng nó\b', 'Đạp lút ga đi', new_v)
        changes.append(("floor_it", new_v, subbed))
        new_v = subbed

    if "thoát khỏi vòng lặp" in new_v and "out of the loop" in orig.lower():
        subbed = new_v.replace("đã thoát khỏi vòng lặp", "mù tịt thông tin quá đấy").replace("thoát khỏi vòng lặp", "mù tịt thông tin")
        changes.append(("out_of_loop", new_v, subbed))
        new_v = subbed

    if "thả nó xuống" in new_v and "drop it" in orig.lower():
        subbed = new_v.replace("thả nó xuống", "đừng nhắc nữa")
        changes.append(("drop_it", new_v, subbed))
        new_v = subbed

    if "bánh mì nướng" in new_v and "toast" in orig.lower():
        subbed = new_v.replace("Những kẻ này là bánh mì nướng!", "Lũ này coi như xong đời rồi!")
        changes.append(("toast", new_v, subbed))
        new_v = subbed

    if "nói về ma quỷ" in new_v and "speak of the devil" in orig.lower():
        subbed = new_v.replace("nói về ma quỷ", "vừa nhắc tào tháo là tào tháo tới ngay")
        changes.append(("speak_of_devil", new_v, subbed))
        new_v = subbed

    if "cắn một miếng" in new_v and "grab a bite" in orig.lower():
        subbed = new_v.replace("chúng ta hãy cắn một miếng", "đi kiếm chút gì lót dạ thôi")
        changes.append(("grab_bite", new_v, subbed))
        new_v = subbed

    if "bọ cạp sa mạc càu nhàu" in new_v.lower() or "bọ cạp sa mạc càu nhàu" in new_v:
        subbed = re.sub(r'\bBọ cạp sa mạc càu nhàu\b', 'Lính Quèn Bọ Cạp Sa Mạc', new_v, flags=re.I)
        changes.append(("scorpion_grunts", new_v, subbed))
        new_v = subbed

    if "những người càu nhàu" in new_v and "grunts" in orig.lower():
        subbed = new_v.replace("những người càu nhàu", "đám lính quèn")
        changes.append(("grunts", new_v, subbed))
        new_v = subbed

    if "những lời càu nhàu vô dụng" in new_v and "grunts" in orig.lower():
        subbed = new_v.replace("những lời càu nhàu vô dụng", "đám lính quèn vô dụng")
        changes.append(("grunts_useless", new_v, subbed))
        new_v = subbed

    if "lão nguyên viện" in new_v and "senate" in orig.lower():
        subbed = new_v.replace("lão nguyên viện sâu bọ", "lũ sâu mọt Thượng viện")
        changes.append(("senate_vermin", new_v, subbed))
        new_v = subbed

    if "Đóng mạng" in new_v and "Closing the Net" in orig:
        subbed = new_v.replace("Đóng mạng", "Khép Lại Mẻ Lưới")
        changes.append(("closing_net", new_v, subbed))
        new_v = subbed

    if "bắt đầu lăn" in new_v and "started rolling" in orig.lower():
        subbed = new_v.replace("bắt đầu lăn", "bắt đầu bấm máy ghi hình")
        changes.append(("rolling_film", new_v, subbed))
        new_v = subbed

    if "công nghệ cấp cao" in new_v and "senior tech" in orig.lower():
        subbed = new_v.replace("công nghệ cấp cao", "kỹ thuật viên thâm niên")
        changes.append(("senior_tech", new_v, subbed))
        new_v = subbed

    if "kẻ gây hại" in new_v and "pest" in orig.lower():
        subbed = new_v.replace("trở thành kẻ gây hại bằng cách nghe lén", "làm kẻ phiền toái quấy rầy")
        changes.append(("pest_bugging", new_v, subbed))
        new_v = subbed

    if "bị ngập trong đống tiệc tùng" in new_v and "swamped" in orig.lower():
        subbed = new_v.replace("Tôi đã bị ngập trong đống tiệc tùng đó rồi. Bây giờ, thưởng thức một số đồ ngọt nghe có vẻ hoàn hảo.", "Mấy vụ tiệc tùng làm tôi bận tối tăm mặt mũi. Giờ được thưởng thức chút đồ ngọt thì còn gì bằng.")
        changes.append(("swamped_banquet", new_v, subbed))
        new_v = subbed

    if "Ba Ủy ban lớn" in new_v and "Three Grand Commissions" in orig:
        subbed = new_v.replace("Ba Ủy ban lớn", "Ba Đại Ủy Thác")
        changes.append(("grand_commissions", new_v, subbed))
        new_v = subbed

    if "ủy ban Chim sơn ca vàng" in new_v and "Golden Nightingale commission" in orig:
        subbed = new_v.replace("ủy ban Chim sơn ca vàng", "ủy thác Hoàng Kim Dạ Oanh")
        changes.append(("nightingale_comm", new_v, subbed))
        new_v = subbed

    if "Chim sơn ca Tawny" in new_v or "Chim sơn ca vàng" in new_v:
        subbed = re.sub(r'\bChim sơn ca Tawny\b', 'Dạ Oanh Hoàng Lạc', new_v)
        subbed = re.sub(r'\bChim sơn ca vàng\b', 'Hoàng Kim Dạ Oanh', subbed)
        changes.append(("nightingale_bread", new_v, subbed))
        new_v = subbed

    # Act titles
    m_act = re.match(r'^(màn|Màn)\s+(một|hai|ba|bốn|năm|sáu|bảy|tám|chín|mười|mười một|mười hai|mười ba)$', new_v.strip(), re.I)
    if m_act:
        act_map = {
            "một": "Một", "hai": "Hai", "ba": "Ba", "bốn": "Bốn", "năm": "Năm",
            "sáu": "Sáu", "bảy": "Bảy", "tám": "Tám", "chín": "Chín", "mười": "Mười",
            "mười một": "Mười Một", "mười hai": "Mười Hai", "mười ba": "Mười Ba"
        }
        num_word = m_act.group(2).lower()
        if num_word in act_map:
            subbed = f"Hồi {act_map[num_word]}"
            changes.append(("act_heading", new_v, subbed))
            new_v = subbed

    if changes:
        fixes[k] = (changes, new_v)

print(f"Total keys with identified fixes: {len(fixes)}")
categories = {}
for k, (ch_list, _) in fixes.items():
    for tag, old, new in ch_list:
        categories[tag] = categories.get(tag, 0) + 1

print("\nFix breakdown:")
for tag, count in sorted(categories.items(), key=lambda x: -x[1]):
    print(f"  {tag}: {count}")
