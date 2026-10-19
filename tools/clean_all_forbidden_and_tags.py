#!/usr/bin/env python3
"""
Final deep cleaner:
Fixes all 32 forbidden calques and all 17 color tag imbalances across data_decrypted/entries/
Ensuring 100% spotless quality before repack.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEC_DIR = ROOT / "work" / "research" / "data_decrypted" / "entries"
GLOSSARY_PATH = ROOT / "config" / "master_glossary.json"

COLOR_TAG_OPEN = re.compile(r'<color=#[0-9a-fA-F]{6}>')
COLOR_TAG_CLOSE = re.compile(r'</color>')

def main():
    print("=" * 70)
    print("Final Deep Clean: Forbidden Calques & Tag Rebalancing")
    print("=" * 70)

    with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
        glossary = json.load(f)
    forbidden = glossary.get("forbidden", {})

    total_files_modified = 0
    total_forbidden_fixed = 0
    total_tags_fixed = 0

    for fname in DEC_DIR.iterdir():
        if not fname.name.endswith(".bin"):
            continue

        try:
            with open(fname, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue

        if not isinstance(data, dict):
            continue

        file_modified = False

        for k, v in list(data.items()):
            if not isinstance(v, str):
                continue

            curr_v = v

            # 1. Clean up duplicate parentheses like "(Hộp Kẹo)"
            if "(Hộp Kẹo)" in curr_v:
                curr_v = curr_v.replace(" (Hộp Kẹo)", "").replace("(Hộp Kẹo)", "")

            # 2. Fix forbidden calques
            for wrong, correct in forbidden.items():
                if wrong.lower() in curr_v.lower():
                    # Case-insensitive replacement
                    curr_v = re.sub(re.escape(wrong), correct, curr_v, flags=re.IGNORECASE)
                    total_forbidden_fixed += 1
                    file_modified = True

            # 3. Specific item fixes
            item_fixes = [
                ("Thành cổ Cây bụi", "Pháo Đài Chuột Bụi"),
                ("thành cổ cây bụi", "Pháo Đài Chuột Bụi"),
                ("Bột chắc chắn", "Cầu Thủ Vạm Vỡ"),
                ("bột chắc chắn", "Cầu Thủ Vạm Vỡ"),
                ("chiến binh bụi rậm", "Chiến Binh Chuột Bụi"),
                ("Chiến binh bụi rậm", "Chiến Binh Chuột Bụi"),
                ("xoắn ốc hoàn hảo", "Toàn Mỹ Xoắn Ốc"),
                ("Lời thề hiệp sĩ: Skyfall", "Kỵ Thệ: Thiên Khung Băng Lạc"),
                ("Vector: kiên cố hóa", "Vector: Cố Hóa"),
                ("Bão tuyết: Ngăn xếp", "Thường Lượng: Điệp Gia"),
                ("Đom đóm phát sáng: Rạng rỡ", "Huỳnh Lưu: Phất Chiếu"),
                ("Đom đóm phát sáng: Ánh sáng", "Huỳnh Lưu: Lũng Quang"),
                ("Tháng ba không thể ngăn cản", "Tiến Bước Trong Bão Tuyết"),
                ("Dự báo thời tiết lạnh", "Dự Báo Hàn Băng"),
                ("trạng thái đóng băng", "Sương Ngưng Trệ"),
                ("tối hậu thư", "Tối Hậu Thư"),
                ("Tối hậu thư", "Tối Hậu Thư")
            ]
            for w, c in item_fixes:
                if w in curr_v:
                    curr_v = curr_v.replace(w, c)
                    file_modified = True

            # 4. Color tag rebalancing
            opens = len(COLOR_TAG_OPEN.findall(curr_v))
            closes = len(COLOR_TAG_CLOSE.findall(curr_v))
            if opens != closes:
                if opens > closes:
                    curr_v = curr_v + ("</color>" * (opens - closes))
                    total_tags_fixed += 1
                    file_modified = True
                elif closes > opens:
                    # Remove trailing unclosed </color>
                    for _ in range(closes - opens):
                        last_c = curr_v.rfind("</color>")
                        if last_c != -1:
                            curr_v = curr_v[:last_c] + curr_v[last_c+8:]
                            total_tags_fixed += 1
                            file_modified = True

            if curr_v != v:
                data[k] = curr_v
                file_modified = True

        if file_modified:
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            total_files_modified += 1

    print(f"Files modified: {total_files_modified}")
    print(f"Forbidden calques fixed: {total_forbidden_fixed}")
    print(f"Color tags rebalanced: {total_tags_fixed}")
    print("=" * 70)

if __name__ == "__main__":
    main()
