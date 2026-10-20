import json
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
glossary_file = os.path.join(viet_dir, r"config\master_glossary.json")

with open(glossary_file, "r", encoding="utf-8") as f:
    gl = json.load(f)

terms = gl.get("terms", {})
forbidden = gl.get("forbidden", {})

noya_terms = {
    "Firstlight Noya": "Noya Sơ Quang",
    "First Light Noya": "Noya Sơ Quang",
    "Firstlight": "Sơ Quang",
    "First Light": "Sơ Quang",
    "Noname": "Vô Danh",
    "Loxy": "Loxy",
    "Dragon Slash": "Thăng Long Trảm",
    "Rising Dragon Slash": "Thăng Long Trảm",
    "Ruin Wind": "Tàn Phong",
    "Withered Wind": "Tàn Phong",
    "Sword Aura": "Kiếm Khí",
    "Great Sword Aura": "Đại Kiếm Khí",
    "Minor Sword Aura": "Tiểu Kiếm Khí",
    "Cross Great Sword Aura": "Thập Tự Đại Kiếm Khí",
    "Multi Sword Aura": "Đa Trọng Kiếm Khí",
    "Swift Wind Flash": "Tấn Phong Thiểm",
    "Galloping Wind Strike": "Trì Phong Kích",
    "Sky Splitter Void Rupture Slash": "Liệt Không Đoạn Phá Trảm",
    "Ventus Mark: Breeze": "Phong Ấn: Phong Tức",
    "At the First Piercing Light": "Thời Khắc Tia Sáng Đầu Tiên Xuyên Qua",
    "Wholeness at Reunion's Dawn": "Viên Mãn Nơi Bình Minh Tái Ngộ",
    "My Guiding Star": "Ngôi Sao Dẫn Đường",
    "Glimmer": "Vi Quang",
}

for k, v in noya_terms.items():
    terms[k] = v

gl["terms"] = terms
gl["forbidden"] = forbidden

with open(glossary_file, "w", encoding="utf-8") as f:
    json.dump(gl, f, indent=2, ensure_ascii=False)

print(f"Added {len(noya_terms)} Firstlight Noya terms to Master Glossary (Total: {len(terms)} terms).")

# Update MASTER_GLOSSARY.md
import subprocess
subprocess.run([sys.executable, os.path.join(viet_dir, "tools", "update_glossary_md.py")])
