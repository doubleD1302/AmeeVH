import json
import re

with open(r'c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\editorial\side_stories_part2_editorial_20261025_r01\PARTITION_B_SOURCE.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

print("Checking terms...")
for it in items:
    iid = it['id']
    en = it['en']
    vi = it.get('current_vi', '')
    
    # 1. Hexhorn
    if 'hexhorn' in vi.lower():
        print(f"[HEXHORN] {iid}: {vi}")
        
    # 2. Ghost Ship / Thuyền ma / Tàu ma
    if re.search(r'\b(thuyền ma|tàu ma|u linh thuyền)\b', vi, re.I):
        print(f"[GHOST SHIP] {iid}: {vi}")

    # 3. Post Haste duplicate
    if 'chuyển phát hỏa tốc chuyển phát hỏa tốc' in vi.lower():
        print(f"[POST HASTE DUP] {iid}: {vi}")

    # 4. New Star Guild
    if 'hội ngôi sao mới' in vi.lower():
        print(f"[NEW STAR GUILD] {iid}: {vi}")
        
    # 5. Lucky Oasis
    if 'lai phúc' in vi.lower():
        print(f"[LUCKY OASIS] {iid}: {vi}")

    # 6. Amber -> Hổ phách
    if 'hổ phách' in vi.lower():
        print(f"[AMBER] {iid}: EN: {en} | VI: {vi}")

    # 7. Iris -> Diên vĩ
    if 'diên vĩ' in vi.lower():
        print(f"[IRIS] {iid}: EN: {en} | VI: {vi}")

    # 8. Willow -> Liễu
    if 'liễu' in vi.lower():
        print(f"[WILLOW] {iid}: EN: {en} | VI: {vi}")
        
    # 9. Bloc -> Khối
    if re.search(r'\bKhối\b', vi) and 'bloc' in en.lower():
        print(f"[BLOC] {iid}: EN: {en} | VI: {vi}")

    # 10. Shrubshrew
    if re.search(r'\b(chiến binh cây bụi|chuột cây bụi)\b', vi, re.I):
        print(f"[SHRUBSHREW] {iid}: {vi}")

    # 11. Soul Stone
    if re.search(r'\b(đá linh hồn|đá hồn)\b', vi, re.I):
        print(f"[SOUL STONE] {iid}: {vi}")
        
    # 12. Imperial Guard
    if re.search(r'\b(vệ binh hoàng gia|kỵ sĩ hoàng gia)\b', vi, re.I):
        print(f"[IMPERIAL GUARD] {iid}: {vi}")
