import json
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
glossary_path = os.path.join(viet_dir, r"config\master_glossary.json")
md_path = os.path.join(viet_dir, r"docs\MASTER_GLOSSARY.md")

with open(glossary_path, "r", encoding="utf-8") as f:
    glossary = json.load(f)

terms = glossary.get("terms", {})
forbidden = glossary.get("forbidden", {})

lines = [
    "# Stella Sora — Master Glossary & Bản Đồ Thuật Ngữ Chuẩn Hóa",
    "",
    f"> Cập nhật tự động phiên bản v0.6.0 (2026-10-20). Tổng số thuật ngữ chuẩn hóa: **{len(terms)}**, quy tắc cấm calque: **{len(forbidden)}**.",
    "",
    "## 1. Nguyên Tắc Cốt Lõi Bản Địa Hóa",
    "",
    "- **Danh từ riêng, Tổ chức, Tên Chiêu Thức, Boss**: Sử dụng từ Hán Việt trang trọng, uy nghi, chuẩn âm (Ví dụ: `Dora` -> `Đóa Lạp`, `Terra Mark` -> `Dấu Ấn Terra`, `New Star` -> `Tân Tinh`, `Vampire Survivor` -> `Sinh Tồn Huyết Nguyệt`).",
    "- **Hội thoại đời thường, Chiến thuật Lữ Khách, Hướng dẫn & Minigame**: Sử dụng văn phong thuần Việt trong sáng, tự nhiên, dí dỏm, phong cách anime đời thường nhẹ nhàng, tuyệt đối không dịch máy thô cứng hay lạm dụng từ Hán Việt xa lạ (Ví dụ: `AoE build` -> `Lối chơi quét diện rộng`, `Burst build` -> `Lối chơi bộc phá sát thương`, `Bản dựng` -> `Lối chơi`, `kẻ thù` -> `kẻ địch`).",
    "- **Bảo toàn Kỹ thuật 100%**: Tuyệt đối bảo toàn nguyên vẹn mọi token hệ thống: `{0}`, `{1}`, `<color=#...>`, `&ParamN&`, `\\n`, `\\x0b`.",
    "",
    "## 2. Quy Tắc Cấm Tuyệt Đối (Blacklisted Calques)",
    "",
    "| Thuật ngữ dịch thô / Calque sai | Bản địa hóa chuẩn Anime | Lý do |",
    "|---|---|---|"
]

for w, c in sorted(forbidden.items()):
    lines.append(f"| `{w}` | **{c}** | Loại bỏ calque thô cứng, thuần Việt tự nhiên |")

lines.extend([
    "",
    "## 3. Danh Mục Thuật Ngữ Chuẩn Hóa (Bản Mới Nhất & Toàn Game)",
    "",
    "| Nguyên bản Tiếng Anh | Bản Địa Hóa Tiếng Việt | Phân loại |",
    "|---|---|---|"
])

for en, vi in sorted(terms.items()):
    lines.append(f"| `{en}` | **{vi}** | Chuẩn hóa Master |")

with open(md_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"Updated {md_path} with {len(terms)} terms and {len(forbidden)} rules.")
