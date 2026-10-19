#!/usr/bin/env python3
"""Apply balanced localization: Han-Viet for skill/organization nouns, natural Vietnamese for descriptions/dialogues."""

import json
from pathlib import Path

# Mapping of Skill / Organization / Entity Nouns to noble, epic Han-Viet
NOUN_HAN_VIET = {
    # Tên Chiêu thức & Hiệu ứng Chiến đấu (Danh từ)
    "Nắm Đấm Rực Lửa và Nham Thạch Bùng Nổ": "Bạo Viêm Quyền & Dung Viêm Phá",
    "Nắm Đấm Rực Lửa & Nham Thạch Bùng Nổ": "Bạo Viêm Quyền & Dung Viêm Phá",
    "Giáp Lửa": "Viêm Khải",
    "Thủy Triều Đen": "Ám Triều",
    "Sóng Biển Sâu": "Minh Tịch",
    "Nhát Chém Thủy Triều": "Linh Cự Trảm",
    "Sóng Thần Cuộn Trào": "Kinh Đào Nại Lạc",
    "Dệt Sóng": "Triều Chức",
    "thế Phòng Ngự": "thế Thủ Thế",
    "Tư thế Phòng Ngự": "Thế Thủ Thế",
    "Thế Phòng Ngự": "Thế Thủ Thế",
    
    # Tên Boss, Quái Vật & Cấm Vệ (Danh từ)
    "Cấm Vệ Bầu Trời": "Cấm Vệ Thương Khung",
    "Mãnh Thú Cuồng Bạo": "Linh Thú Cuồng Bạo",
    "Lưỡi Đao Ngọc Bích": "Thúy Hoàng Chi Nhận",
    "Hộ Vệ Dung Nham": "Cấm Vệ Dung Nham",
    "Hộ Vệ Cuồng Triều": "Cấm Vệ Cuồng Triều",
    "Hộ Vệ Tĩnh Lặng": "Cấm Vệ Tĩnh Lặng",
    "Hộ Vệ Gai Góc": "Cấm Vệ Gai Góc",
    "Hộ Vệ Ánh Sáng": "Cấm Vệ Ánh Sáng",
    "Hộ Vệ Ác Mộng": "Cấm Vệ Ác Mộng",
    
    # Tên Tổ chức & Phe phái (Danh từ)
    "Cận Vệ Hoàng Gia": "Cận Vệ Đế Quốc"
}

def main():
    root = Path(__file__).parent.parent
    entries_dir = root / 'work' / 'research' / 'data_decrypted' / 'entries'

    print("Updating tables: Restoring epic Han-Viet for skills, organizations, and entity nouns...")
    total_modifications = 0
    modified_files = 0

    for bin_file in entries_dir.glob('*.bin'):
        with open(bin_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception:
                continue

        if not isinstance(data, dict):
            continue

        file_changed = False
        for k, text in data.items():
            if not isinstance(text, str):
                continue
            original = text
            for old_term, new_term in NOUN_HAN_VIET.items():
                if old_term in text:
                    text = text.replace(old_term, new_term)
            if text != original:
                data[k] = text
                file_changed = True
                total_modifications += 1

        if file_changed:
            with open(bin_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            modified_files += 1
            print(f"  ✓ Updated {bin_file.name}")

    print(f"\nTotal modifications applied: {total_modifications} occurrences across {modified_files} files.")

    # 1. Update config/master_glossary.json
    glossary_path = root / 'config' / 'master_glossary.json'
    if glossary_path.exists():
        with open(glossary_path, 'r', encoding='utf-8') as f:
            glossary = json.load(f)
        terms = glossary.get('terms', {})
        for k, v in list(terms.items()):
            for old_term, new_term in NOUN_HAN_VIET.items():
                if old_term in v:
                    terms[k] = v.replace(old_term, new_term)
                    print(f"  Glossary updated: {k} -> {terms[k]}")
        with open(glossary_path, 'w', encoding='utf-8') as f:
            json.dump(glossary, f, ensure_ascii=False, indent=2)

    # 2. Update config/glossary.json
    cfg_glossary = root / 'config' / 'glossary.json'
    if cfg_glossary.exists():
        with open(cfg_glossary, 'r', encoding='utf-8') as f:
            cg = json.load(f)
        for entry in cg.get('entries', []):
            target = entry.get('target', '')
            for old_term, new_term in NOUN_HAN_VIET.items():
                if old_term in target:
                    entry['target'] = target.replace(old_term, new_term)
        with open(cfg_glossary, 'w', encoding='utf-8') as f:
            json.dump(cg, f, ensure_ascii=False, indent=2)

    # 3. Update docs/MASTER_GLOSSARY.md
    md_glossary = root / 'docs' / 'MASTER_GLOSSARY.md'
    if md_glossary.exists():
        content = md_glossary.read_text(encoding='utf-8')
        for old_term, new_term in NOUN_HAN_VIET.items():
            content = content.replace(old_term, new_term)
        md_glossary.write_text(content, encoding='utf-8')

    print("Master Glossary files synchronized successfully.")

if __name__ == '__main__':
    main()
