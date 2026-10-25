# -*- coding: utf-8 -*-
"""
Full Comprehensive Polish Script for Campaign 19 (20,680 dialogue lines).
Refines remaining crude machine translations into natural, immersive anime / light novel style.
"""
import json
import re
from pathlib import Path
from typing import Tuple, List

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")

# 1. Specific phrase overrides and idiom fixes
PHRASE_OVERRIDES = {
    # STm02_04 specific & thug brawl dialogue
    "Hey, don't push! Floor's covered in ice!": "Này, đừng có xô đẩy! Mặt đường đóng băng trơn tuột rồi!",
    "<size=51>I said don't push!</size>": "<size=51>Tao đã bảo đừng có xô đẩy mà!</size>",
    "Broke Gangster": "Tên Côn Đồ Túng Tiền",
    "Excited Gangster": "Tên Côn Đồ Hăng Máu",
    "Subdued Gangster": "Tên Côn Đồ Bị Khuất Phục",
    "Sly Gangster": "Tên Côn Đồ Ranh Mãnh",
    "Young Gangster": "Tên Côn Đồ Trẻ Tuổi",
    "Anxious Mercenary": "Lính Đánh Thuê Bồn Chồn",
    "It was all Minova's plan.==W== Hitting them hard really did the trick. All of them took off with their tails between their legs.": 
        "Tất cả đều nằm trong tính toán của Minova.==W== Giáng cho chúng một đòn chí mạng quả nhiên hiệu nghiệm. Đứa nào đứa nấy cúp đuôi chạy té khói cả rồi.",
    "That takes care of our tail! Bastelina, how are things on your end?":
        "Cắt đuôi được bọn bám theo rồi! Bastelina, bên cậu thế nào rồi?",
    "Good. I was starting to think I scared her so badly she ran off with her tail between her legs. If I don't let her experience the full power of \"Ticka-Boom,\" I came here for nothing!":
        "Tốt. Tôi còn tưởng mình dọa cho cô ta khiếp vía đến mức cúp đuôi bỏ chạy rồi chứ. Nếu không cho cô ta nếm thử toàn bộ uy lực của \"Ticka-Boom\", thì chuyến này tôi đến đây công cốc à!",
    "Judging by the prophecy, it's a devastating Artifact that fires something like lightning to kill its target instantly.":
        "Theo lời tiên tri, đó là một Di Vật có sức tàn phá khủng khiếp, phóng ra luồng sét đoạt mạng mục tiêu trong chớp mắt.",
    "Oh?==W== Heh. So it is a picnic.":
        "Ồ?==W== Hì hì. Hóa ra đúng là một chuyến dã ngoại thật.",
    "So it is an illusion. What the fisher saw was indeed a hallucination...":
        "Hóa ra chỉ là ảo ảnh. Thứ mà người câu cá nhìn thấy quả thực chỉ là ảo giác...",
    "Ah, memory loss... It's practically a Trekker starter pack item.":
        "À, mất trí nhớ à... Cái đó gần như là món đồ nhập môn kinh điển của Trekker rồi.",
    "Right now it's a disaster zone. Photos, snacks, toys everywhere.==W== Sigh... I'm afraid I'll have to ask for your help to clean that up, too.":
        "Hiện tại chỗ đó chẳng khác nào bãi chiến trường bừa bộn. Ảnh ọt, đồ ăn vặt, đồ chơi vứt lung tung khắp nơi.==W== Haizz... Tôi e là lại phải nhờ cậu dọn dẹp hộ rồi.",
    "That's impossible! Let me see that!": "Không thể nào! Đưa tôi xem nào!",
    "Ugh... That gives me the creeps.": "Eo... Nghe rợn cả người.",
    "Which makes it a very special day!": "Chính vì thế hôm nay mới là một ngày đặc biệt chứ!",
    "Don't push it~": "Đừng có lấn tới nha~",
    "Don't push too far up. Watch your surroundings.": "Đừng dâng lên quá cao. Chú ý quan sát xung quanh.",
    "Ow, don't push... U-Um... Master! I-I'm so sorry! There's a reason for this...!": "Ái da, đừng xô đẩy... Ơ-kìa... Sư phụ! C-Con xin lỗi ạ! Chuyện này là có nguyên do cả đấy ạ...!",
}

# 2. General regex replacements on Vietnamese text
REGEX_REPLACEMENTS = [
    # Thug / Gangster rough dialogue fixes
    (r"\bTôi đã bảo đừng đẩy mà!\b", "Tao đã bảo đừng có xô đẩy mà!"),
    (r"\bSàn nhà phủ đầy băng!\b", "Mặt đường đóng băng trơn tuột rồi!"),
    (r"\bcất cánh với cái đuôi ở giữa hai chân\b", "cúp đuôi chạy té khói cả lũ"),
    (r"\bcái đuôi ở giữa hai chân\b", "cúp đuôi chạy té khói"),
    (r"\bđuôi ở giữa hai chân\b", "cúp đuôi"),
    (r"\bchăm sóc cái đuôi của chúng tôi\b", "cắt đuôi được bọn bám theo"),
    (r"\bchăm sóc cái đuôi của chúng ta\b", "cắt đuôi được kẻ theo dõi"),
    
    # Gangster names
    (r"\bGangster khuất phục\b", "Tên Côn Đồ Bị Khuất Phục"),
    (r"\bGangster ranh mãnh\b", "Tên Côn Đồ Ranh Mãnh"),
    (r"\bGangster trẻ\b", "Tên Côn Đồ Trẻ Tuổi"),
    (r"\bCôn Đồ Cháy Túi\b", "Tên Côn Đồ Túng Tiền"),
    (r"\bCôn đồ cháy túi\b", "Tên côn đồ túng tiền"),
    
    # Common English MT calques
    (r"\bđiều đó là không thể\b", "chuyện đó là không thể"),
    (r"\bĐiều đó là không thể\b", "Không thể nào"),
    (r"\bĐiều đó làm tôi nhớ ra\b", "Nhắc mới nhớ"),
    (r"\bđiều đó làm tôi nhớ ra\b", "nhắc mới nhớ"),
    (r"\bGiờ điều đó làm tôi nhớ ra\b", "Giờ nhắc mới nhớ"),
    (r"\bBản thân điều đó là ổn\b", "Như thế cũng tốt mà"),
    (r"\bĐiều đó làm cho nó trở thành một ngày rất đặc biệt\b", "Chính vì thế hôm nay mới là một ngày vô cùng đặc biệt"),
    (r"\bĐiều đó làm cho\b", "Chính điều đó khiến"),
    (r"\bđiều đó làm cho\b", "chính điều đó khiến"),
    (r"\bĐiều đó làm tôi\b", "Điều đó khiến tôi"),
    (r"\bđiều đó làm tôi\b", "điều đó khiến tôi"),
    (r"\bThực tế nó là một\b", "Nó gần như là một"),
    (r"\bthực tế nó là một\b", "nó gần như là một"),
    (r"\bVì vậy, nó là một chuyến dã ngoại\b", "Hóa ra lại là một chuyến dã ngoại"),
    (r"\bVì vậy, nó là một ảo ảnh\b", "Hóa ra chỉ là ảo ảnh"),
    (r"\bVì vậy, sàn nhà trông như thế này!\b", "Hóa ra mặt sàn trông như thế này!"),
    (r"\bĐó là lý do tại sao\b", "Thảo nào"),
    (r"\bđó là lý do tại sao\b", "thảo nào"),
    (r"\bTôi sẽ thành thật\b", "Thật lòng mà nói"),
    (r"\btôi sẽ thành thật\b", "thật lòng mà nói"),
    (r"\bchơi trò giả vờ\b", "chơi trò đồ hàng"),
    (r"\bcắn viên đạn\b", "cắn răng chịu đựng"),
    (r"\bcứu làn da của\b", "cứu mạng"),
    (r"\bBạn đặt cược!\b", "Chuẩn luôn!"),
    (r"\bbạn đặt cược!\b", "chuẩn luôn!"),
    (r"\bkhông thực hiện cú đấm của mình\b", "chẳng hề nương tay chút nào"),
    (r"\bgọi đó là một ngày\b", "kết thúc một ngày"),
    (r"\bhát những lời khen ngợi\b", "hết lời khen ngợi"),
    (r"\bvụ nổ chớp nhoáng\b", "lựu đạn choáng"),
    (r"\bchạy lại các con số\b", "tính toán lại số liệu"),
    (r"\blời nói dối trắng trợn\b(?=.*(?:tốt|thiện|bảo vệ|giúp))", "lời nói dối thiện ý"),
    (r"\blau sàn nhà kính với tôi\b", "dần tôi một trận tơi bời"),
    (r"\bchơi cùng\?\b", "hùa theo à?"),
    (r"\bngười đàn ông đó\b", "gã đó"),
    (r"\bngười phụ nữ đó\b", "cô ấy"),
    (r"\bngười phụ nữ kia\b", "cô nàng kia"),
    (r"\bchúng tôi đã làm\b", "chúng tôi đã xong"),
    (r"\bcô ấy là một\b", "cô ấy là"),
    (r"\bnó là một\b", "đó là một"),
    
    # Pronoun naturalization (avoiding bạn bè, bạn thân, bạn tốt, bạn đồng hành, tình bạn, bạn đời)
    (r"\bBạn có muốn\b", "Cậu có muốn"),
    (r"\bBạn có thể\b", "Cậu có thể"),
    (r"\bBạn không thể\b", "Cậu không thể"),
    (r"\bBạn có chắc\b", "Cậu có chắc"),
    (r"\bBạn có biết\b", "Cậu có biết"),
    (r"\bBạn đang\b", "Cậu đang"),
    (r"\bBạn đã\b", "Cậu đã"),
    (r"\bBạn sẽ\b", "Cậu sẽ"),
    (r"\bBạn phải\b", "Cậu phải"),
    (r"\bBạn nên\b", "Cậu nên"),
    (r"\bBạn nghĩ\b", "Cậu nghĩ"),
    (r"\bBạn thấy\b", "Cậu thấy"),
    (r"\bBạn biết đấy\b", "Cậu biết đấy"),
    (r"\bCủa bạn đây\b", "Của cậu đây nè"),
    (r"\bCảm ơn bạn\b", "Cảm ơn cậu nhé"),
    (r"\bÝ bạn là gì\?", "Ý cậu là sao?"),
    (r"\bý bạn là gì\?", "ý cậu là sao?"),
    (r"\bÝ bạn là\b", "Ý cậu là"),
    (r"\bý bạn là\b", "ý cậu là"),
    (r"\bTại sao bạn lại\b", "Sao cậu lại"),
    (r"\btại sao bạn lại\b", "sao cậu lại"),
    (r"\bĐiều đó có nghĩa là gì\?", "Thế nghĩa là sao?"),
    (r"\bTôi không thể tin được\b", "Tôi không thể tin nổi"),
    (r"\bTôi tự hỏi\b", "Tự hỏi"),
    (r"\btôi tự hỏi\b", "tự hỏi"),
    (r"\bTôi đoán\b", "Chắc là"),
    (r"\btôi đoán\b", "chắc là"),
    (r"\bKhông có gì ngạc nhiên khi\b", "Chẳng trách"),
    (r"\bkhông có gì ngạc nhiên khi\b", "thảo nào"),
    (r"\bBạn\b(?!\s*(?:bè|thân|tốt|đồng hành|đời))", "Cậu"),
    (r"\bbạn\b(?!\s*(?:bè|thân|tốt|đồng hành|đời))", "cậu"),
    
    # Master Glossary terms
    (r"\bkhối đá khổng lồ\b", "Cự Tháp"),
    (r"\bMonolith\b", "Cự Tháp"),
    (r"\bCreta Trading\b", "Thương đoàn Creta"),
    (r"\bNocturn Eterna\b", "Đêm Trường Vĩnh Cửu"),
    (r"\bĐêm Vĩnh Cửu\b", "Đêm Trường Vĩnh Cửu"),
    (r"\bĐồ tạo tác\b", "Di Vật"),
    (r"\bđồ tạo tác\b", "di vật"),
    (r"\bCổ vật Bán hàng Tự động\b", "Di Vật Bán Hàng Tự Động"),
    (r"\bBà Angie\b", "Tiểu Thư Angie"),
    (r"\bQuý Cô Angie\b", "Tiểu Thư Angie"),
    (r"\bPost Haste\b", "Chuyển Phát Hỏa Tốc"),
    (r"\bCấp Tốc Bưu Cục\b", "Chuyển Phát Hỏa Tốc"),
    (r"\bTrại Mồ Côi Daisy\b", "Viện Mồ Côi Daisy"),
    (r"\bDaisy Orphanage\b", "Viện Mồ Côi Daisy"),
    (r"\bĐá Hồn\b", "Hồn Thạch"),
    (r"\bĐá Linh Hồn\b", "Hồn Thạch"),
    (r"\bPhoto Capturer\b", "Máy Chụp Ảnh"),
    (r"\bMáy chụp ảnh\b", "Máy Chụp Ảnh"),
    (r"\bSnowish Tree Spirit\b", "Tinh Linh Cây Tuyết"),
    (r"\bThần Cây Tuyết\b", "Tinh Linh Cây Tuyết"),
    (r"\bLễ hội Snowish\b", "Lễ Hội Mùa Tuyết"),
    (r"\blễ hội Snowish\b", "Lễ Hội Mùa Tuyết"),
]

COMPILED_RULES = [(re.compile(p), r) for p, r in REGEX_REPLACEMENTS]

def polish_entry(en: str, vi: str) -> str:
    en_s = en.strip()
    if en_s in PHRASE_OVERRIDES:
        return PHRASE_OVERRIDES[en_s]
    
    res = vi
    for pat, repl in COMPILED_RULES:
        res = pat.sub(repl, res)
        
    # Preserve tags
    tags = re.findall(r'<[^>]+>|==[a-zA-Z0-9_.-]+==|\{[0-9]+\}|_NOT_IN_LOG_', en)
    for tag in tags:
        res = re.sub(re.escape(tag), tag, res, flags=re.IGNORECASE)
        
    return res

def main():
    print("=== STARTING POLISH OF CAMPAIGN 19 (20,680 LINES) ===")
    p_unified = ROOT / "work/editorial/campaign19_polish_remaining_20680_20261025_r01/UNIFIED_CAMPAIGN_19_POLISHED.jsonl"
    lines = [json.loads(x) for x in p_unified.read_text(encoding="utf-8").splitlines()]
    
    modified_count = 0
    updated_lines = []
    updated_dict = {}
    
    for item in lines:
        en = item.get("en", "")
        curr_vi = item.get("polished_vi") or item.get("original_vi", "")
        new_vi = polish_entry(en, curr_vi)
        
        was_mod = item.get("modified", False)
        is_mod = (new_vi != item.get("original_vi", ""))
        if new_vi != curr_vi:
            modified_count += 1
            item["modified"] = True
            item["polished_vi"] = new_vi
        elif was_mod:
            item["modified"] = True
            item["polished_vi"] = curr_vi
        else:
            item["modified"] = is_mod
            item["polished_vi"] = new_vi
            
        updated_lines.append(item)
        updated_dict[en.strip()] = item["polished_vi"].strip()
        
    print(f"Total entries: {len(updated_lines)}")
    print(f"Newly modified in this pass: {modified_count}")
    total_modified = sum(1 for x in updated_lines if x.get("modified"))
    print(f"Total modified lines across all passes: {total_modified} / {len(updated_lines)} ({total_modified*100/len(updated_lines):.2f}%)")
    
    # Save back to UNIFIED_CAMPAIGN_19_POLISHED.jsonl
    with open(p_unified, "w", encoding="utf-8") as f:
        for item in updated_lines:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Saved to {p_unified.name}")
    
    # Save to remaining_lua_avg_cache.json
    p_cache = ROOT / "work/batches/remaining_lua_avg_cache.json"
    cache_data = json.load(open(p_cache, encoding="utf-8"))
    cache_updated = 0
    for k in cache_data:
        k_s = k.strip()
        if k_s in updated_dict:
            cache_data[k] = updated_dict[k_s]
            cache_updated += 1
            
    with open(p_cache, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    print(f"Updated {cache_updated} entries in {p_cache.name}")

if __name__ == "__main__":
    main()
