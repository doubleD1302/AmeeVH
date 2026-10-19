#!/usr/bin/env python3
"""Build and standardize Master Glossary for Stella Sora Vietnamese Localization."""

import json
from pathlib import Path

GLOSSARY_DATA = [
    # 1. Thế Giới, Địa Danh & Phe Phái (World Lore & Factions)
    {"source": "Trekker", "target": "Lữ Khách", "category": "Lore", "notes": "Nhân vật người chơi điều khiển/chiêu mộ trong hành trình"},
    {"source": "Monolith", "target": "Cự Tháp", "category": "Lore", "notes": "Cấu trúc khổng lồ bí ẩn trong thế giới Stella Sora"},
    {"source": "Novian", "target": "Người Novian", "category": "Lore", "notes": "Cư dân trên đại lục Nova"},
    {"source": "Novians", "target": "Dân Novian", "category": "Lore", "notes": "Số nhiều của Novian"},
    {"source": "Nova Continent", "target": "Đại Lục Nova", "category": "Lore", "notes": "Lục địa bối cảnh chính của game"},
    {"source": "Star Pluck", "target": "Đoạt Sao", "category": "Lore", "notes": "Hoạt động/chế độ đoạt sao (TUYỆT ĐỐI KHÔNG DỊCH 'Sao nhổ')"},
    {"source": "Star Pluck Conquest", "target": "Chinh Phục Đoạt Sao", "category": "Lore", "notes": "TUYỆT ĐỐI KHÔNG DỊCH 'Cuộc chinh phục sao nhổ'"},
    {"source": "Wilds", "target": "Vùng Hoang Dã", "category": "Lore", "notes": "Khu vực ngoài thành phố Nova"},
    {"source": "Deepsea Finance", "target": "Tài Chính Biển Sâu", "category": "Lore", "notes": "Tập đoàn tài chính phát hành Dorra"},
    {"source": "Dorra", "target": "Dorra", "category": "Lore", "notes": "Đơn vị tiền tệ chính thức của Nova, giữ nguyên"},
    {"source": "Stellanite Lumina", "target": "Quặng Tinh Thể Lumina", "category": "Lore", "notes": "Khoáng thạch năng lượng quý"},
    {"source": "Star Tower", "target": "Tháp Sao", "category": "Lore", "notes": "Công trình thử thách chính"},
    {"source": "Infinite Arena", "target": "Đấu Trường Vô Tận", "category": "Lore", "notes": "Chế độ vượt tầng thử thách"},
    {"source": "Infinity Tower", "target": "Tháp Vô Tận", "category": "Lore", "notes": "Tháp thử thách vô hạn"},

    # 2. Chỉ Số, Cơ Chế & Chiến Đấu (Combat Mechanics & Stats)
    {"source": "ATK", "target": "Tấn Công", "category": "Combat", "notes": "Chỉ số sức mạnh công kích"},
    {"source": "DEF", "target": "Phòng Thủ", "category": "Combat", "notes": "Chỉ số giảm sát thương"},
    {"source": "HP", "target": "HP", "category": "Combat", "notes": "Lượng máu/sinh lực nhân vật"},
    {"source": "Crit Rate", "target": "Tỷ Lệ Bạo Kích", "category": "Combat", "notes": "Xác suất đòn đánh chí mạng"},
    {"source": "CRIT Rate", "target": "Tỷ Lệ Bạo Kích", "category": "Combat", "notes": "Viết tắt CRIT Rate"},
    {"source": "Crit DMG", "target": "Sát Thương Bạo Kích", "category": "Combat", "notes": "Lượng sát thương khi chí mạng"},
    {"source": "CRIT DMG", "target": "Sát Thương Bạo Kích", "category": "Combat", "notes": "Viết tắt CRIT DMG"},
    {"source": "DMG", "target": "Sát Thương", "category": "Combat", "notes": "Lượng thương tổn gây ra/nhận vào"},
    {"source": "Movement SPD", "target": "Tốc Độ Di Chuyển", "category": "Combat", "notes": "TUYỆT ĐỐI KHÔNG DỊCH 'SPD chuyển động'"},
    {"source": "Move SPD", "target": "Tốc Độ Di Chuyển", "category": "Combat", "notes": "Viết tắt Move SPD"},
    {"source": "Attack SPD", "target": "Tốc Độ Tấn Công", "category": "Combat", "notes": "Tần suất ra đòn"},
    {"source": "ATK SPD", "target": "Tốc Độ Tấn Công", "category": "Combat", "notes": "Viết tắt ATK SPD"},
    {"source": "Cooldown", "target": "Hồi Chiêu", "category": "Combat", "notes": "Thời gian chờ kỹ năng"},
    {"source": "CD", "target": "Hồi Chiêu", "category": "Combat", "notes": "Viết tắt CD"},
    {"source": "Normal Attack", "target": "Đòn Đánh Thường", "category": "Combat", "notes": "Tấn công cơ bản"},
    {"source": "Auto Attack", "target": "Đòn Đánh Thường", "category": "Combat", "notes": "Tấn công tự động/thường"},
    {"source": "Main Skill", "target": "Kỹ Năng Chính", "category": "Combat", "notes": "Chiêu thức kích hoạt chủ đạo"},
    {"source": "Secondary Skill", "target": "Kỹ Năng Phụ", "category": "Combat", "notes": "Kỹ năng bổ trợ chiến thuật"},
    {"source": "Ultimate", "target": "Tuyệt Kỹ", "category": "Combat", "notes": "Chiêu cuối năng lượng cao"},
    {"source": "Burst", "target": "Bộc Phá Tuyệt Kỹ", "category": "Combat", "notes": "Trạng thái bùng nổ sức mạnh"},
    {"source": "Dodge", "target": "Né Tránh", "category": "Combat", "notes": "Hành động lướt né đòn"},
    {"source": "Dash", "target": "Lướt", "category": "Combat", "notes": "Tốc biến ngắn né chiêu"},
    {"source": "Incapacitated", "target": "Bị Tê Liệt / Vô Hiệu Hóa", "category": "Combat", "notes": "TUYỆT ĐỐI KHÔNG DỊCH 'mất khả năng lao động'"},
    {"source": "Stun", "target": "Choáng", "category": "Combat", "notes": "Hiệu ứng khống chế cứng"},
    {"source": "Freeze", "target": "Đóng Băng", "category": "Combat", "notes": "Hiệu ứng hóa đá băng"},
    {"source": "Frozen", "target": "Bị Đóng Băng", "category": "Combat", "notes": "Trạng thái bị đông cứng"},
    {"source": "Shock", "target": "Sốc Điện", "category": "Combat", "notes": "Hiệu ứng cảm điện liên tục"},
    {"source": "Burn", "target": "Thiêu Đốt", "category": "Combat", "notes": "Hiệu ứng sát thương lửa liên tục"},
    {"source": "Bleed", "target": "Xuất Huyết", "category": "Combat", "notes": "Hiệu ứng chảy máu mất máu dần"},
    {"source": "Shield", "target": "Lá Chắn", "category": "Combat", "notes": "Giáp ảo chặn sát thương"},
    {"source": "Vigor", "target": "Thể Lực", "category": "Combat", "notes": "Năng lượng đi phụ bản"},
    {"source": "Magazine Capacity", "target": "Dung Lượng Băng Đạn", "category": "Combat", "notes": "Số đạn trong một băng"},

    # 3. Nhân Vật & Phát Triển (Progression & Systems)
    {"source": "Talent", "target": "Thiên Phú", "category": "Progression", "notes": "Nhánh nâng cấp thụ động theo nhân vật"},
    {"source": "Potential", "target": "Tiềm Năng", "category": "Progression", "notes": "Cường hóa chiêu thức đột phá"},
    {"source": "FateCard", "target": "Thẻ Định Mệnh", "category": "Progression", "notes": "Trang bị thẻ bài gia tăng năng lực"},
    {"source": "Affinity", "target": "Độ Thân Mật", "category": "Progression", "notes": "Điểm hảo cảm với nhân vật"},
    {"source": "Affinity Quest", "target": "Nhiệm Vụ Thân Mật", "category": "Progression", "notes": "Chuỗi cốt truyện gắn kết nhân vật"},
    {"source": "Affinity Up Reward", "target": "Phần Thưởng Thân Mật", "category": "Progression", "notes": "Quà tặng khi tăng cấp độ hảo cảm"},
    {"source": "Soul Key", "target": "Chìa Khóa Tâm Hồn", "category": "Progression", "notes": "Vật phẩm mở khóa thiên phú"},
    {"source": "Authorization Lv.", "target": "Cấp Ủy Quyền", "category": "Progression", "notes": "Cấp độ tài khoản/người chơi"},
    {"source": "Breakthrough", "target": "Đột Phá", "category": "Progression", "notes": "Nâng giới hạn cấp độ"},
    {"source": "Enhance", "target": "Cường Hóa", "category": "Progression", "notes": "Nâng cấp trang bị/kỹ năng"},
    {"source": "Upgrade", "target": "Nâng Cấp", "category": "Progression", "notes": "Tăng bậc thuộc tính"},
    {"source": "Character Skin", "target": "Trang Phục Nhân Vật", "category": "Progression", "notes": "Ngoại trang nhân vật"},
    {"source": "Trial Character", "target": "Dùng Thử Nhân Vật", "category": "Progression", "notes": "Chế độ trải nghiệm thử tướng"},

    # 4. Giao Diện, Hoạt Động & Sự Kiện (UI & Activities)
    {"source": "Gacha", "target": "Triệu Hồi", "category": "UI", "notes": "Quay tướng/thẻ bài"},
    {"source": "Draw", "target": "Chiêu Mộ", "category": "UI", "notes": "Rút thẻ"},
    {"source": "Pull", "target": "Quay", "category": "UI", "notes": "Lượt quay"},
    {"source": "Banner", "target": "Kỳ Chiêu Mộ", "category": "UI", "notes": "Giai đoạn triệu hồi giới hạn"},
    {"source": "Inventory", "target": "Túi Đồ", "category": "UI", "notes": "Kho lưu trữ vật phẩm"},
    {"source": "Mall", "target": "Cửa Hàng", "category": "UI", "notes": "Khu mua sắm trong game"},
    {"source": "Shop", "target": "Cửa Hàng", "category": "UI", "notes": "Shop vật phẩm"},
    {"source": "Package", "target": "Gói Quà", "category": "UI", "notes": "Combo vật phẩm bán sẵn"},
    {"source": "Battle Pass", "target": "Thẻ Hành Trình", "category": "UI", "notes": "Vé thông hành mùa giải"},
    {"source": "Quest", "target": "Nhiệm Vụ", "category": "UI", "notes": "Mục tiêu cần hoàn thành"},
    {"source": "Mission", "target": "Nhiệm Vụ", "category": "UI", "notes": "Chiến dịch nhiệm vụ"},
    {"source": "Task", "target": "Nhiệm Vụ", "category": "UI", "notes": "Công việc cần làm"},
    {"source": "Achievement", "target": "Thành Tựu", "category": "UI", "notes": "Bảng vinh danh mục tiêu"},
    {"source": "Claim", "target": "Nhận", "category": "UI", "notes": "Nút nhận thưởng"},
    {"source": "Claim All", "target": "Nhận Tất Cả", "category": "UI", "notes": "Nút gom toàn bộ phần thưởng"},
    {"source": "Confirm", "target": "Xác Nhận", "category": "UI", "notes": "Nút đồng ý hành động"},
    {"source": "Cancel", "target": "Hủy", "category": "UI", "notes": "Nút từ chối hành động"},
    {"source": "Back", "target": "Quay Lại", "category": "UI", "notes": "Trở về màn hình trước"},
    {"source": "Settings", "target": "Cài Đặt", "category": "UI", "notes": "Thiết lập hệ thống"},
    {"source": "Notice", "target": "Thông Báo", "category": "UI", "notes": "Bảng tin thông tin mới"},
    {"source": "Mailbox", "target": "Hòm Thư", "category": "UI", "notes": "Nơi nhận quà và thư hệ thống"},
    {"source": "Quick Clear", "target": "Quét Nhanh", "category": "UI", "notes": "Vượt ải tự động tức thì"},
    {"source": "Sweep", "target": "Quét Ải", "category": "UI", "notes": "Thu hoạch tài nguyên ải đã vượt"},
    {"source": "Deploy", "target": "Xuất Trận", "category": "UI", "notes": "Bố trí đội hình tham chiến"},
    {"source": "Penguin Card", "target": "Thẻ Chim Cánh Cụt", "category": "UI", "notes": "Thẻ minigame bài Cánh Cụt"}
]

# Blacklist of forbidden literal translations
FORBIDDEN_CALQUES = [
    {"wrong": "Sao nhổ", "correct": "Đoạt Sao / Hái Sao", "rule": "CẤM DỊCH 'Star Pluck' thành 'Sao nhổ'"},
    {"wrong": "Cuộc chinh phục sao nhổ", "correct": "Chinh Phục Đoạt Sao / Hái Sao Viễn Chinh", "rule": "CẤM DỊCH 'Star Pluck Conquest' thành 'Cuộc chinh phục sao nhổ'"},
    {"wrong": "mất khả năng lao động", "correct": "bị tê liệt / không thể hành động", "rule": "CẤM DỊCH 'incapacitated' thành 'mất khả năng lao động'"},
    {"wrong": "SPD chuyển động", "correct": "Tốc độ Di chuyển", "rule": "CẤM GIỮ NGUYÊN 'SPD'"},
    {"wrong": "có thể được sử dụng trong", "correct": "dùng cho / dùng trong", "rule": "XÓA BỎ THỂ BỊ ĐỘNG 'can be used in'"},
    {"wrong": "bị gây ra bởi", "correct": "kích hoạt từ / gây ra bởi", "rule": "XÓA BỎ THỂ BỊ ĐỘNG 'inflicted by'"},
    {"wrong": "nó giải phóng những tài năng chôn vùi", "correct": "khai mở thiên phú say ngủ nơi sâu thẳm tâm hồn", "rule": "VĂN PHONG ANIME RPG BAY BỔNG"},
    {"wrong": "ở một mình trong vùng hoang dã", "correct": "đơn độc nơi Vùng Hoang Dã", "rule": "VĂN PHONG TỰ NHIÊN, KHÔNG WORD-BY-WORD"}
]

def main():
    root = Path(__file__).parent.parent
    config_dir = root / 'config'
    docs_dir = root / 'docs'
    config_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    # 1. Update config/glossary.json (Project Contract Format)
    glossary_json_data = {
        "schema": 2,
        "policy": "Mandatory Project Glossary. All approved entries are strictly enforced for all agents and translation pipelines.",
        "entries": [
            {
                "source": item["source"],
                "target": item["target"],
                "status": "approved",
                "category": item["category"],
                "notes": item["notes"]
            }
            for item in GLOSSARY_DATA
        ],
        "forbidden_calques": FORBIDDEN_CALQUES
    }

    glossary_path = config_dir / 'glossary.json'
    with open(glossary_path, 'w', encoding='utf-8') as f:
        json.dump(glossary_json_data, f, ensure_ascii=False, indent=2)
    print(f"Updated {glossary_path} with {len(GLOSSARY_DATA)} approved entries.")

    # 2. Create config/master_glossary.json (Direct dictionary lookup for scripts)
    lookup_dict = {item["source"].lower(): item["target"] for item in GLOSSARY_DATA}
    # Add exact case dictionary as well
    lookup_dict.update({item["source"]: item["target"] for item in GLOSSARY_DATA})

    master_lookup_path = config_dir / 'master_glossary.json'
    with open(master_lookup_path, 'w', encoding='utf-8') as f:
        json.dump({
            "terms": {item["source"]: item["target"] for item in GLOSSARY_DATA},
            "forbidden": {f["wrong"]: f["correct"] for f in FORBIDDEN_CALQUES}
        }, f, ensure_ascii=False, indent=2)
    print(f"Created {master_lookup_path} for agent automated lookups.")

    # 3. Create docs/MASTER_GLOSSARY.md (Human and Agent Readable Documentation)
    md_content = """# Từ Điển Bản Địa Hóa Chuẩn Dự Án (Master Glossary)
**Áp dụng bắt buộc cho toàn bộ Subagent và Pipeline Dịch thuật Stella Sora**

Mục tiêu: Đảm bảo 100% tính nhất quán thuật ngữ, loại bỏ triệt để bất đồng từ ngữ giữa các Agent, xóa sổ vĩnh viễn các lỗi dịch thô / word-by-word / Google dịch.

---

## 🚫 1. Danh Sách Đen (Cấm Dịch Word-by-Word Tuyệt Đối)

| Cụm từ sai / sượng (CẤM DÙNG) | Thuật ngữ chuẩn Anime RPG (BẮT BUỘC) | Quy tắc ngữ cảnh |
| :--- | :--- | :--- |
"""
    for f in FORBIDDEN_CALQUES:
        md_content += f"| **`{f['wrong']}`** | **`{f['correct']}`** | {f['rule']} |\n"

    md_content += """
---

## 📖 2. Bảng Thuật Ngữ Bản Địa Hóa Chuẩn (Approved Master Glossary)

### A. Thế Giới, Địa Danh & Phe Phái (World Lore & Factions)
| Thuật ngữ gốc (EN) | Tiếng Việt chuẩn (VI) | Ghi chú ngữ cảnh |
| :--- | :--- | :--- |
"""
    for item in GLOSSARY_DATA:
        if item["category"] == "Lore":
            md_content += f"| `{item['source']}` | **{item['target']}** | {item['notes']} |\n"

    md_content += """
### B. Chỉ Số, Cơ Chế & Chiến Đấu (Combat & Stats)
| Thuật ngữ gốc (EN) | Tiếng Việt chuẩn (VI) | Ghi chú ngữ cảnh |
| :--- | :--- | :--- |
"""
    for item in GLOSSARY_DATA:
        if item["category"] == "Combat":
            md_content += f"| `{item['source']}` | **{item['target']}** | {item['notes']} |\n"

    md_content += """
### C. Nhân Vật & Phát Triển (Progression & Systems)
| Thuật ngữ gốc (EN) | Tiếng Việt chuẩn (VI) | Ghi chú ngữ cảnh |
| :--- | :--- | :--- |
"""
    for item in GLOSSARY_DATA:
        if item["category"] == "Progression":
            md_content += f"| `{item['source']}` | **{item['target']}** | {item['notes']} |\n"

    md_content += """
### D. Giao Diện & Tính Năng Hệ Thống (UI & Activities)
| Thuật ngữ gốc (EN) | Tiếng Việt chuẩn (VI) | Ghi chú ngữ cảnh |
| :--- | :--- | :--- |
"""
    for item in GLOSSARY_DATA:
        if item["category"] == "UI":
            md_content += f"| `{item['source']}` | **{item['target']}** | {item['notes']} |\n"

    md_content += """
---

## 🛠️ 3. Tích Hợp Vào Quy Trình Của Mọi Agent
1. **Trước khi dịch**: Mọi Translator/Subagent bắt buộc nạp bảng tra cứu `config/master_glossary.json`.
2. **Trong khi dịch**: Áp dụng đúng 100% thuật ngữ đã được phê duyệt (`approved`).
3. **Chốt chặn Review (`localization_qa_reviewer`)**: Quét tự động danh sách đen `forbidden_calques`. Nếu phát hiện bất kỳ cụm từ cấm nào (như *"sao nhổ"*, *"mất khả năng lao động"*), lập tức từ chối và tự động thay thế bằng từ ngữ chuẩn.
"""

    md_path = docs_dir / 'MASTER_GLOSSARY.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"Created {md_path}.")

if __name__ == '__main__':
    main()
