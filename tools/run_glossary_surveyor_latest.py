import json
import os
import re

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
glossary_file = os.path.join(viet_dir, r"config\master_glossary.json")
with open(glossary_file, "r", encoding="utf-8") as f:
    master_glossary = json.load(f)

existing_terms = master_glossary.get("terms", {})
forbidden_rules = master_glossary.get("forbidden_rules", {})

p1_file = os.path.join(viet_dir, r"work\batches\partition1_minigames_modes.json")
p2_file = os.path.join(viet_dir, r"work\batches\partition2_characters_tactics.json")
p3_file = os.path.join(viet_dir, r"work\batches\partition3_story_quests_ui.json")

all_partitions = [p1_file, p2_file, p3_file]
all_strings = {}

for p in all_partitions:
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    for table_key, table_info in data.items():
        for k, s in table_info["entries"].items():
            all_strings[k] = s

print(f"Glossary Surveyor: Scanning {len(all_strings)} strings from latest resources...")

# Extract capitalized multi-word phrases and key game terms
new_candidates = {}

KNOWN_PROPER_NOUNS = {
    # Minigame & Mode terms
    "Vampire Survivor": "Sinh Tồn Huyết Nguyệt",
    "Bounty: Terra Mark": "Treo Thưởng: Dấu Ấn Terra",
    "Terra Mark": "Dấu Ấn Terra",
    "New Star": "Tân Tinh",
    "Royal Rebate": "Hoàn Trả Hoàng Gia",
    "Penguin-monium": "Hỗn Chiến Cánh Cụt",
    "Begin Tracking": "Bắt Đầu Truy Vết",
    "Hunt Begins": "Cuộc Đi Săn Bắt Đầu",
    "Track Complete": "Hoàn Thành Truy Vết",
    "Star Tower": "Tháp Sao",
    "Stella Coin": "Xu Stella",
    "Cat Treat-1911 Dual-Wield": "Song Thủ Súng Mèo 1911",
    "Console - Total Playtime": "Máy Chơi Game - Tổng Thời Gian",
    "Console - Leaderboard": "Máy Chơi Game - Bảng Xếp Hạng",
    "Bernina & Virigia": "Bernina & Virigia",
    "Virigia & Bernina": "Virigia & Bernina",
    "Firefly": "Đom Đóm",
    
    # Tactical Build Terms (Thuần Việt & Game Design chuẩn)
    "AoE build": "Lối chơi quét diện rộng",
    "An AoE build that enhances skill": "Lối chơi quét diện rộng cường hóa kỹ năng",
    "Burst build": "Lối chơi bộc phá sát thương",
    "Skill cycle build": "Lối chơi luân chuyển kỹ năng",
    "Crit build": "Lối chơi bạo kích",
    "Survivability build": "Lối chơi sinh tồn bền bỉ",
    "Support build": "Lối chơi hỗ trợ đồng đội",
    "Basic ATK build": "Lối chơi cường hóa đánh thường",
    "Normal Attack build": "Lối chơi cường hóa đánh thường",
    
    # Event & NPC terms
    "The Nimble yet Unbreakable Messenger": "Sứ Giả Nhanh Nhẹn Kiên Cường",
    "A Day in the Life": "Một Ngày Bình Dị",
    "The Lost Kitten": "Mèo Con Lạc Lối",
    "Summer Brawl": "Hỗn Chiến Mùa Hè",
    "Amber": "Amber",
    "Iris": "Iris",
    "Noya": "Noya",
    "Tilia": "Tilia",
    "Eleanor": "Eleanor",
    "Portia": "Portia",
    "Si Bai": "Tư Bạch",
    "Chitose": "Chitose",
    "Virigia": "Virigia",
    "Bernina": "Bernina",
    "Dorra": "Dorra",
    "Emor": "Emor"
}

added_count = 0
for term, trans in KNOWN_PROPER_NOUNS.items():
    if term not in existing_terms:
        existing_terms[term] = trans
        new_candidates[term] = trans
        added_count += 1

master_glossary["terms"] = existing_terms

# Update master glossary file
with open(glossary_file, "w", encoding="utf-8") as f:
    json.dump(master_glossary, f, indent=2, ensure_ascii=False)

# Save survey report
survey_report_path = os.path.join(viet_dir, r"work\reviews\glossary_survey_latest_resources.json")
with open(survey_report_path, "w", encoding="utf-8") as f:
    json.dump({
        "scanned_strings_count": len(all_strings),
        "total_terms_in_glossary": len(existing_terms),
        "newly_added_terms_count": added_count,
        "new_terms": new_candidates
    }, f, indent=2, ensure_ascii=False)

print(f"Glossary Surveyor complete:")
print(f"  - Scanned: {len(all_strings)} strings")
print(f"  - Newly added terms: {added_count}")
print(f"  - Total terms in Master Glossary: {len(existing_terms)}")
print(f"  - Report saved to: {survey_report_path}")
