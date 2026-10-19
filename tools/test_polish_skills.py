#!/usr/bin/env python3
"""Draft polisher for MainSkill and SecondarySkill descriptions."""

import re
from phase2a_token_manager import shield_tokens, unshield_tokens

# Term replacement dictionaries
ELEMENT_MAP = {
    'Aqua': 'Thủy',
    'Ignis': 'Hỏa',
    'Ventus': 'Phong',
    'Terra': 'Địa',
    'Lux': 'Quang',
    'Umbra': 'Ám'
}

SPECIAL_EFFECTS = {
    r'Tide Weave': 'Triều Chức',
    r'Ripple Echo': 'Liên Hưởng',
    r'Dark Tide': 'Ám Triều',
    r'Surging Wave': 'Dũng Lãng',
    r'Surge Wave': 'Dũng Lãng',
    r'Starlit Hope': 'Tinh Vọng',
    r'Flowing Fragrance': 'Lưu Phương',
    r'Drifting Snow': 'Phù Tuyết',
    r'Tuyết [tT]rôi': 'Phù Tuyết',
    r'Explosive Flame': 'Bộc Diễm',
    r'Ngọn lửa nổ': 'Bộc Diễm',
    r'Blazing Armor': 'Viêm Khải',
    r'Áo giáp rực lửa': 'Viêm Khải',
    r'Wings of Light': 'Quang Chi Dực',
    r'Đôi cánh ánh sáng': 'Quang Chi Dực',
    r'Storybook': 'Sách Truyện',
    r'Sách truyện': 'Sách Truyện',
    r'Light Particle': 'Hạt Quang Học',
    r'Hạt Ánh sáng': 'Hạt Quang Học',
    r'Reverence': 'Kính Sợ',
    r'Reverie': 'Hà Tư',
    r'Lingering Wish': 'Tàn Nguyện',
    r'Điều ước kéo dài': 'Tàn Nguyện',
    r'Điều ước còn sót lại': 'Tàn Nguyện',
    r'Laceration': 'Xé Rách',
    r'Vết rách': 'Xé Rách',
    r'Blossom': 'Hoa Nở',
    r'Cyclone': 'Cuồng Phong',
    r'Lốc xoáy': 'Cuồng Phong',
}

def clean_skill_desc(text: str) -> str:
    sh, toks = shield_tokens(text)

    # 1. Clean special skill mechanics / buff names
    for eng_term, vi_term in SPECIAL_EFFECTS.items():
        sh = re.sub(rf'\b{eng_term}\b', f'"{vi_term}"', sh)
        sh = re.sub(rf'"{vi_term}" cộng dồn', f'tầng "{vi_term}"', sh)
        sh = re.sub(rf'điểm cộng dồn của "{vi_term}"', f'tầng "{vi_term}"', sh)
        sh = re.sub(rf'điểm cộng dồn "{vi_term}"', f'tầng "{vi_term}"', sh)
        sh = re.sub(rf'số cộng dồn của "{vi_term}"', f'tầng "{vi_term}"', sh)

    # 2. Elements & Roles combinations
    for elem, vi_elem in ELEMENT_MAP.items():
        # Lữ khách chủ lực hệ X
        sh = re.sub(rf'\b{elem}\s+Main\s+Lữ khách\b', f'Lữ Khách chủ lực hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\b{elem}\s+Lữ khách chủ lực\b', f'Lữ Khách chủ lực hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\bLữ khách chủ lực của {elem}\b', f'Lữ Khách chủ lực hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\bLữ khách chủ lực {elem}\b', f'Lữ Khách chủ lực hệ {vi_elem}', sh, flags=re.I)
        
        # Lữ khách viện trợ hệ X
        sh = re.sub(rf'\b{elem}\s+Support\s+Lữ khách\b', f'Lữ Khách viện trợ hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\b{elem}\s+Hỗ trợ\s+Lữ khách\b', f'Lữ Khách viện trợ hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\b{elem}\s+Lữ khách viện trợ\b', f'Lữ Khách viện trợ hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\bLữ khách viện trợ {elem}\b', f'Lữ Khách viện trợ hệ {vi_elem}', sh, flags=re.I)
        
        # Lữ khách đa năng hệ X
        sh = re.sub(rf'\b{elem}\s+Lữ khách đa năng\b', f'Lữ Khách đa năng hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\bLữ khách đa năng {elem}\b', f'Lữ Khách đa năng hệ {vi_elem}', sh, flags=re.I)
        
        # Lữ khách hệ X
        sh = re.sub(rf'\b{elem}\s+Lữ khách\b', f'Lữ Khách hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\bLữ khách {elem}\b', f'Lữ Khách hệ {vi_elem}', sh, flags=re.I)
        
        # Đồng đội hệ X
        sh = re.sub(rf'\bđồng đội {elem}\b', f'đồng đội hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\bđồng đội của {elem}\b', f'đồng đội hệ {vi_elem}', sh, flags=re.I)
        
        # Sát thương hệ X
        sh = re.sub(rf'\bsát thương của {elem}\b', f'Sát Thương hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\bthiệt hại cho {elem}\b', f'Sát Thương hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\bSát thương hệ {vi_elem} của riêng mình\b', f'Sát Thương hệ {vi_elem} của bản thân', sh, flags=re.I)

    # 3. Main / Support general
    sh = re.sub(r'\bMain Lữ khách\b', 'Lữ Khách chủ lực', sh, flags=re.I)
    sh = re.sub(r'\bLữ khách chính\b', 'Lữ Khách chủ lực', sh, flags=re.I)
    sh = re.sub(r'\bLữ khách hỗ trợ\b', 'Lữ Khách viện trợ', sh, flags=re.I)
    sh = re.sub(r'\bHỗ trợ Lữ khách\b', 'Lữ Khách viện trợ', sh, flags=re.I)
    sh = re.sub(r'\bSupport Lữ khách\b', 'Lữ Khách viện trợ', sh, flags=re.I)

    # 4. Damage types & Stats
    sh = re.sub(r'\bthiệt hại tối đa\b', 'Sát Thương Tuyệt Kỹ', sh, flags=re.I)
    sh = re.sub(r'\bthiệt hại tối thượng\b', 'Sát Thương Tuyệt Kỹ', sh, flags=re.I)
    sh = re.sub(r'\bsát thương tối đa\b', 'Sát Thương Tuyệt Kỹ', sh, flags=re.I)
    sh = re.sub(r'\bsát thương tối thượng\b', 'Sát Thương Tuyệt Kỹ', sh, flags=re.I)
    sh = re.sub(r'\bThiệt hại Kỹ năng\b', 'Sát Thương Kỹ Năng', sh, flags=re.I)
    sh = re.sub(r'\bthiệt hại kỹ năng\b', 'Sát Thương Kỹ Năng', sh, flags=re.I)
    sh = re.sub(r'\bthiệt hại\b', 'sát thương', sh, flags=re.I)
    sh = re.sub(r'\bsát thương tấn công tự động\b', 'Sát Thương Đòn Đánh Thường', sh, flags=re.I)
    sh = re.sub(r'\bTấn công tự động\b', 'Đòn Đánh Thường', sh)
    sh = re.sub(r'\btấn công tự động\b', 'Đòn Đánh Thường', sh)
    sh = re.sub(r'\bsát thương chí mạng tối thượng\b', 'Sát Thương Bạo Kích Tuyệt Kỹ', sh, flags=re.I)
    sh = re.sub(r'\bsát thương chí mạng kỹ năng\b', 'Sát Thương Bạo Kích Kỹ Năng', sh, flags=re.I)
    sh = re.sub(r'\bsát thương chí mạng Đòn đánh thường\b', 'Sát Thương Bạo Kích Đòn Đánh Thường', sh, flags=re.I)
    sh = re.sub(r'\bsát thương chí mạng\b', 'Sát Thương Bạo Kích', sh, flags=re.I)
    sh = re.sub(r'\bẤn ký sát thương\b', 'Sát Thương Ấn Ký', sh, flags=re.I)

    # 5. Phrasing fixes
    sh = re.sub(r'\bhãy tăng\b', 'tăng', sh, flags=re.I)
    sh = re.sub(r'\bsẽ tăng\b', 'tăng', sh, flags=re.I)
    sh = re.sub(r'\bsẽ giảm\b', 'giảm', sh, flags=re.I)
    sh = re.sub(r'\bsẽ hồi\b', 'hồi', sh, flags=re.I)
    sh = re.sub(r'\bsẽ cấp\b', 'cấp', sh, flags=re.I)
    sh = re.sub(r'\bsẽ loại bỏ\b', 'loại bỏ', sh, flags=re.I)
    sh = re.sub(r'\bsử dụng một kỹ năng\b', 'thi triển kỹ năng', sh, flags=re.I)
    sh = re.sub(r'\bsử dụng kỹ năng\b', 'thi triển kỹ năng', sh, flags=re.I)
    sh = re.sub(r'\bHiệu ứng này chỉ có thể được kích hoạt một lần mỗi\b', 'Hiệu ứng này kích hoạt tối đa 1 lần mỗi', sh, flags=re.I)
    sh = re.sub(r'\bchỉ có thể được kích hoạt một lần mỗi\b', 'kích hoạt tối đa 1 lần mỗi', sh, flags=re.I)
    sh = re.sub(r'\bLính của họ\b', 'Tùy Tùng', sh, flags=re.I)
    sh = re.sub(r'\btay sai\b', 'Tùy Tùng', sh, flags=re.I)
    sh = re.sub(r'\bmục tiêu ưu tú\b', 'mục tiêu Tinh Anh', sh, flags=re.I)
    sh = re.sub(r'\bcác mục tiêu ưu tú\b', 'mục tiêu Tinh Anh', sh, flags=re.I)
    sh = re.sub(r'\bcác mục tiêu cấp cao hoặc cấp cao hơn\b', 'mục tiêu Tinh Anh trở lên', sh, flags=re.I)
    sh = re.sub(r'\bmục tiêu cấp cao hoặc cấp cao hơn\b', 'mục tiêu Tinh Anh trở lên', sh, flags=re.I)
    sh = re.sub(r'\bmỗi ngăn xếp\b', 'mỗi tầng', sh, flags=re.I)
    sh = re.sub(r'\bngăn xếp\b', 'tầng', sh, flags=re.I)
    sh = re.sub(r'\bmỗi chồng\b', 'mỗi tầng', sh, flags=re.I)
    sh = re.sub(r'\bchồng\b', 'tầng', sh, flags=re.I)
    sh = re.sub(r'\bnhận được một lá chắn\b', 'nhận lá chắn', sh, flags=re.I)
    sh = re.sub(r'\bnhận được một tấm khiên\b', 'nhận lá chắn', sh, flags=re.I)
    sh = re.sub(r'\bcó khiên\b', 'có lá chắn', sh, flags=re.I)
    sh = re.sub(r'\bcủa riêng mình\b', 'của bản thân', sh, flags=re.I)
    sh = re.sub(r'\bcủa chính mình\b', 'của bản thân', sh, flags=re.I)
    sh = re.sub(r'\bdo ([0-9]+%?|\[\[TOK\d+\]\])\b', r'thêm \1', sh)
    sh = re.sub(r'\bbởi ([0-9]+%?|\[\[TOK\d+\]\])\b', r'thêm \1', sh)

    # Clean whitespace and restore
    sh = re.sub(r'[ \t]{2,}', ' ', sh)
    restored = unshield_tokens(sh, toks)
    return restored
