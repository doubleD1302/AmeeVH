import json
import os

root = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
master_glossary_path = os.path.join(root, "config", "master_glossary.json")
report_path = os.path.join(root, "reports", "glossary_survey_report.json")
doc_path = os.path.join(root, "docs", "MASTER_GLOSSARY.md")

# 1. Verify master_glossary.json
with open(master_glossary_path, "r", encoding="utf-8") as f:
    master_data = json.load(f)

terms = master_data.get("terms", {})
forbidden = master_data.get("forbidden", {})
print("=== Master Glossary Verification ===")
print(f"Total terms: {len(terms)}")
print(f"Total forbidden rules: {len(forbidden)}")
assert len(terms) >= 1100, "Terms count should be >= 1100"
assert len(forbidden) >= 25, "Forbidden count should be >= 25"

# Check sample terms
samples = [
    "Shrubshrews Warrior", "Cat-stle Siege", "Sunflower Ties", "Fortissimo: Main Theme",
    "Amber: Default", "Playful Innocence", "Ultimate Battle Cry", "The Academy",
    "Nova Empire", "Cerulean Ticket", "Super Flush", "Novice Tyrant", "Boss's Regulars"
]
for s in samples:
    print(f"  {s:30} -> {terms.get(s, 'MISSING!')}")

# 2. Verify report_path
with open(report_path, "r", encoding="utf-8") as f:
    report = json.load(f)

print("\n=== Survey Report Verification ===")
print("Report title:", report.get("report_title"))
print("Statistics:", report.get("statistics"))
print("Categories summary count:", len(report.get("categories_summary", {})))
for cat, summary in report.get("categories_summary", {}).items():
    print(f"  {cat:40}: total={summary['total_terms']}, new={summary['new_terms']} ({summary['pillar']})")

# 3. Update docs/MASTER_GLOSSARY.md
md_lines = [
    "# Từ Điển Bản Địa Hóa Chuẩn Dự Án (Master Glossary)",
    "**Áp dụng bắt buộc cho toàn bộ Subagent và Pipeline Dịch thuật Stella Sora**",
    "",
    f"**Tổng số thuật ngữ chuẩn:** {len(terms)} thuật ngữ | **Danh sách đen cấm dịch thô:** {len(forbidden)} quy tắc",
    "",
    "---",
    "",
    "## 🚫 1. Danh Sách Đen (Cấm Dịch Word-by-Word Tuyệt Đối)",
    "",
    "| Cụm từ sai / sượng (CẤM DÙNG) | Thuật ngữ chuẩn Anime RPG (BẮT BUỘC) |",
    "| :--- | :--- |"
]

for wrong, correct in forbidden.items():
    md_lines.append(f"| **`{wrong}`** | **`{correct}`** |")

md_lines.extend([
    "",
    "---",
    "",
    "## 📖 2. Bảng Phân Nhóm Thuật Ngữ Bản Địa Hóa Chuẩn (Approved Master Glossary)",
    ""
])

# Group terms by category from report
cat_summary = report.get("categories_summary", {})
for cat, summary in cat_summary.items():
    cat_terms = [t for t in report.get("new_terms_sample_by_category", {}).get(cat, [])]
    md_lines.extend([
        f"### {cat} ({summary['pillar']})",
        f"*Tổng số thuật ngữ nhóm này: {summary['total_terms']} (Bổ sung mới: {summary['new_terms']})*",
        "",
        "| Thuật ngữ gốc (EN) | Tiếng Việt chuẩn (VI) | Ghi chú |",
        "| :--- | :--- | :--- |"
    ])
    for item in cat_terms:
        md_lines.append(f"| `{item['en']}` | **{item['vi']}** | {item.get('notes', '')} |")
    md_lines.append("")

with open(doc_path, "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines))

print(f"\nSuccessfully updated human-readable documentation at {doc_path}")
