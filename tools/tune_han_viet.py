#!/usr/bin/env python3
"""Tune down archaic Sino-Vietnamese (Hán-Việt) across all game tables and glossary."""

import json
import re
from pathlib import Path

# Mapping of archaic / over-the-top Han-Viet to natural, modern anime RPG Vietnamese
HAN_VIET_TUNING = {
    # Cốt truyện & Tên ải
    "Thập Diện Bủa Lưới": "Khép Chặt Vòng Vây",
    "Đảo Ngược Càn Khôn": "Lật Ngược Tình Thế",
    "Bệ Hạ, xin Người ban danh xưng!": "Xin Người hãy để lại danh tính của mình!",
    "Bệ Hạ, xin Người ban danh xưng": "Xin Người hãy để lại danh tính của mình",
    
    # Kỹ năng & Cơ chế chiến đấu
    "Linh Cự Ngưng Giải Trảm": "Nhát Chém Thủy Triều",
    "Kinh Đào Nại Lạc": "Sóng Thần Cuộn Trào",
    "Bạo Viêm Quyền và Dung Viêm Phá": "Nắm Đấm Rực Lửa và Nham Thạch Bùng Nổ",
    "Bạo Viêm Quyền & Dung Viêm Phá": "Nắm Đấm Rực Lửa & Nham Thạch Bùng Nổ",
    "thế Thủ Thế": "thế Phòng Ngự",
    "Tư thế Thủ Thế": "Tư thế Phòng Ngự",
    "Thế Thủ Thế": "Thế Phòng Ngự",
    "tiểu kiếm khí": "kiếm khí nhỏ",
    "Tiểu kiếm khí": "Kiếm khí nhỏ",
    "Viêm Khải": "Giáp Lửa",
    "Triều Chức": "Dệt Sóng",
    "Ám Triều": "Thủy Triều Đen",
    "Minh Tịch": "Sóng Biển Sâu",
    "Thú Năng": "Năng Lượng Đi Săn",
    "Thương Khung": "Bầu Trời",
    "Cấm Vệ Thương Khung": "Cấm Vệ Bầu Trời",
    "Thúy Hoàng": "Ngọc Bích",
    "Lưỡi Đao Thúy Hoàng": "Lưỡi Đao Ngọc Bích",
    "Linh Thú Cuồng Bạo": "Mãnh Thú Cuồng Bạo",
    "Cấm Vệ Dung Nham": "Hộ Vệ Dung Nham",
    "Cấm Vệ Cuồng Triều": "Hộ Vệ Cuồng Triều",
    "Cấm Vệ Tĩnh Lặng": "Hộ Vệ Tĩnh Lặng",
    "Cấm Vệ Gai Góc": "Hộ Vệ Gai Góc",
    "Cấm Vệ Ánh Sáng": "Hộ Vệ Ánh Sáng",
    "Cấm Vệ Ác Mộng": "Hộ Vệ Ác Mộng"
}

def main():
    root = Path(__file__).parent.parent
    entries_dir = root / 'work' / 'research' / 'data_decrypted' / 'entries'

    print("Scanning and tuning Han-Viet phrases across all tables...")
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
            for old_term, new_term in HAN_VIET_TUNING.items():
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

    print(f"\nTotal Han-Viet terms tuned down: {total_modifications} occurrences across {modified_files} files.")

    # Also tune config/master_glossary.json and docs/MASTER_GLOSSARY.md
    glossary_path = root / 'config' / 'master_glossary.json'
    if glossary_path.exists():
        with open(glossary_path, 'r', encoding='utf-8') as f:
            glossary = json.load(f)
        terms = glossary.get('terms', {})
        for k, v in list(terms.items()):
            for old_term, new_term in HAN_VIET_TUNING.items():
                if old_term in v:
                    terms[k] = v.replace(old_term, new_term)
                    print(f"  Glossary tuned: {k} -> {terms[k]}")
        with open(glossary_path, 'w', encoding='utf-8') as f:
            json.dump(glossary, f, ensure_ascii=False, indent=2)

    # Also update config/glossary.json
    cfg_glossary = root / 'config' / 'glossary.json'
    if cfg_glossary.exists():
        with open(cfg_glossary, 'r', encoding='utf-8') as f:
            cg = json.load(f)
        for entry in cg.get('entries', []):
            target = entry.get('target', '')
            for old_term, new_term in HAN_VIET_TUNING.items():
                if old_term in target:
                    entry['target'] = target.replace(old_term, new_term)
        with open(cfg_glossary, 'w', encoding='utf-8') as f:
            json.dump(cg, f, ensure_ascii=False, indent=2)

    # Also update docs/MASTER_GLOSSARY.md
    md_glossary = root / 'docs' / 'MASTER_GLOSSARY.md'
    if md_glossary.exists():
        content = md_glossary.read_text(encoding='utf-8')
        for old_term, new_term in HAN_VIET_TUNING.items():
            content = content.replace(old_term, new_term)
        md_glossary.write_text(content, encoding='utf-8')

if __name__ == '__main__':
    main()
