import json
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
glossary_file = os.path.join(viet_dir, r"config\master_glossary.json")

with open(glossary_file, "r", encoding="utf-8") as f:
    gl = json.load(f)

terms = gl.get("terms", {})

# Update to Noya - Khải Minh
terms["Firstlight Noya"] = "Noya - Khải Minh"
terms["First Light Noya"] = "Noya - Khải Minh"
terms["Firstlight"] = "Khải Minh"
terms["First Light"] = "Khải Minh"

gl["terms"] = terms

with open(glossary_file, "w", encoding="utf-8") as f:
    json.dump(gl, f, indent=2, ensure_ascii=False)

print("Updated Master Glossary with 'Noya - Khải Minh'!")
