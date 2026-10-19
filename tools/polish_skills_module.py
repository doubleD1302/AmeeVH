#!/usr/bin/env python3
"""Comprehensive translation polisher for MainSkill and SecondarySkill."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from phase2a_token_manager import shield_tokens, unshield_tokens, validate_token_preservation

SPECIAL_BUFFS = [
    (re.compile(r'\bTide Weave\b', re.I), '"Triều Chức"'),
    (re.compile(r'\bRipple Echo\b', re.I), '"Liên Hưởng"'),
    (re.compile(r'\bDark Tide\b', re.I), '"Ám Triều"'),
    (re.compile(r'\bSurging Wave\b', re.I), '"Dũng Lãng"'),
    (re.compile(r'\bSurge Wave\b', re.I), '"Dũng Lãng"'),
    (re.compile(r'\bSóng tăng tốc\b', re.I), '"Dũng Lãng"'),
    (re.compile(r'\bStarlit Hope\b', re.I), '"Tinh Vọng"'),
    (re.compile(r'\bFlowing Fragrance\b', re.I), '"Lưu Phương"'),
    (re.compile(r'\bDrifting Snow\b', re.I), '"Phù Tuyết"'),
    (re.compile(r'\bTuyết [tT]rôi\b'), '"Phù Tuyết"'),
    (re.compile(r'\bExplosive Flame\b', re.I), '"Bộc Diễm"'),
    (re.compile(r'\bNgọn lửa nổ\b', re.I), '"Bộc Diễm"'),
    (re.compile(r'\bBlazing Armor\b', re.I), '"Viêm Khải"'),
    (re.compile(r'\bÁo giáp rực lửa\b', re.I), '"Viêm Khải"'),
    (re.compile(r'\bWings of Light\b', re.I), '"Quang Chi Dực"'),
    (re.compile(r'\bĐôi cánh ánh sáng\b', re.I), '"Quang Chi Dực"'),
    (re.compile(r'\bStorybook\b', re.I), '"Sách Truyện"'),
    (re.compile(r'\bSách truyện\b', re.I), '"Sách Truyện"'),
    (re.compile(r'\bLight Particle\b', re.I), '"Hạt Quang Học"'),
    (re.compile(r'\bHạt Ánh sáng\b', re.I), '"Hạt Quang Học"'),
    (re.compile(r'\bReverence\b', re.I), '"Kính Sợ"'),
    (re.compile(r'\bSự tôn kính\b', re.I), '"Kính Sợ"'),
    (re.compile(r'\bTôn kính\b', re.I), '"Kính Sợ"'),
    (re.compile(r'\bReverie\b', re.I), '"Hà Tư"'),
    (re.compile(r'\bLingering Wish\b', re.I), '"Tàn Nguyện"'),
    (re.compile(r'\bĐiều ước kéo dài\b', re.I), '"Tàn Nguyện"'),
    (re.compile(r'\bĐiều ước còn sót lại\b', re.I), '"Tàn Nguyện"'),
    (re.compile(r'\bLaceration\b', re.I), '"Xé Rách"'),
    (re.compile(r'\bVết rách\b', re.I), '"Xé Rách"'),
    (re.compile(r'\bBlossom\b', re.I), '"Hoa Nở"'),
    (re.compile(r'\bCyclone\b', re.I), '"Cuồng Phong"'),
    (re.compile(r'\bLốc xoáy\b', re.I), '"Cuồng Phong"'),
    (re.compile(r'\bGlory\b', re.I), '"Vinh Quang"'),
    (re.compile(r'\bVinh quang\b', re.I), '"Vinh Quang"'),
    (re.compile(r'\bHope\b', re.I), '"Hy Vọng"'),
    (re.compile(r'\bHy vọng\b', re.I), '"Hy Vọng"'),
]

ELEMENTS = [
    ('Aqua', 'Thủy'),
    ('Ignis', 'Hỏa'),
    ('Ventus', 'Phong'),
    ('Terra', 'Địa'),
    ('Lux', 'Quang'),
    ('Umbra', 'Ám')
]

def polish_skill_text(vi_text: str, en_orig: str) -> str:
    sh, toks = shield_tokens(vi_text)

    # 1. Special buff names
    for pattern, repl in SPECIAL_BUFFS:
        sh = pattern.sub(repl, sh)

    # Clean double quotes on buffs
    sh = re.sub(r'""+', '"', sh)

    # 2. Fix DMG Taken backwards translations
    sh = re.sub(r'Sát thương Kỹ năng Ventus được thực hiện bởi', 'Sát Thương Kỹ Năng hệ Phong gánh chịu thêm', sh, flags=re.I)
    sh = re.sub(r'sát thương tấn công tự động của Ventus Bị thực hiện bởi', 'Sát Thương Đòn Đánh Thường hệ Phong gánh chịu thêm', sh, flags=re.I)
    sh = re.sub(r'Sát thương Tuyệt kỹ của Umbra Nhận bởi', 'Sát Thương Tuyệt Kỹ hệ Ám gánh chịu thêm', sh, flags=re.I)
    sh = re.sub(r'tăng Sát thương Kỹ năng mà mục tiêu đã thực hiện thêm', 'tăng Sát Thương Kỹ Năng gánh chịu của mục tiêu thêm', sh, flags=re.I)
    sh = re.sub(r'Sát thương hệ Thủy Sát thương Kỹ năng Taken', 'Sát Thương Kỹ Năng hệ Thủy gánh chịu', sh, flags=re.I)
    sh = re.sub(r'Ấn ký Thủy Sát thương gánh chịu', 'Sát Thương Ấn Ký hệ Thủy gánh chịu', sh, flags=re.I)
    sh = re.sub(r'Sát thương hệ Thủy Skill', 'Sát Thương Kỹ Năng hệ Thủy', sh, flags=re.I)
    sh = re.sub(r'sát thương Tấn Công hệ Thủy Auto', 'Sát Thương Đòn Đánh Thường hệ Thủy', sh, flags=re.I)
    sh = re.sub(r'mục tiêu sẽ nhận (\[\[TOK\d+\]\]) tăng Sát Thương Đòn Đánh Thường hệ Thủy', r'tăng \1 Sát Thương Đòn Đánh Thường hệ Thủy gánh chịu của mục tiêu', sh, flags=re.I)
    sh = re.sub(r'Giảm thiệt hại mà (\[\[TOK\d+\]\]) phải gánh chịu', r'Giảm \1 sát thương gánh chịu', sh, flags=re.I)
    sh = re.sub(r'Sát thương hệ Quang mà mục tiêu phải nhận thêm', 'Sát Thương hệ Quang gánh chịu của mục tiêu thêm', sh, flags=re.I)
    sh = re.sub(r'mục tiêu bị (\[\[TOK\d+\]\]) gây ra bởi', r'mục tiêu chịu trạng thái \1 thêm', sh, flags=re.I)
    sh = re.sub(r'mục tiêu gây ra "Tàn Nguyện"', 'mục tiêu chịu trạng thái "Tàn Nguyện"', sh, flags=re.I)
    sh = re.sub(r'thực hiện "Tàn Nguyện"', 'gây trạng thái "Tàn Nguyện"', sh, flags=re.I)
    sh = re.sub(r'thiệt hại mà Ventus gây ra cho đồng đội của Ventus thêm', 'Sát Thương hệ Phong do đồng đội hệ Phong gây ra thêm', sh, flags=re.I)
    sh = re.sub(r'nhận được 1 điểm "Hy Vọng" trong (\[\[TOK\d+\]\]) giây, tối đa 6 điểm', r'nhận 1 tầng "Hy Vọng" trong \1 giây, tối đa 6 tầng', sh, flags=re.I)
    sh = re.sub(r'nhận được số cộng dồn "Hà Tư" bằng với số cộng dồn của "Sách Truyện" hiện tại: tăng Sát Thương Ấn Ký thêm (\[\[TOK\d+\]\]) trong (\[\[TOK\d+\]\]) giây, tối đa 10 cộng dồn', r'nhận số tầng "Hà Tư" tương ứng với số tầng "Sách Truyện" hiện có: tăng Sát Thương Ấn Ký thêm \1 trong \2 giây, tối đa 10 tầng', sh, flags=re.I)

    # 3. Elements and Trekker Roles
    for elem, vi_elem in ELEMENTS:
        sh = re.sub(rf'\b{elem}\s+Main\s+Lữ khách\b', f'Lữ Khách chủ lực hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\b{elem}\s+Lữ khách chủ lực\b', f'Lữ Khách chủ lực hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\bLữ khách chủ lực của {elem}\b', f'Lữ Khách chủ lực hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\bLữ khách chủ lực {elem}\b', f'Lữ Khách chủ lực hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\b{elem}\s+Support\s+Lữ khách\b', f'Lữ Khách viện trợ hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\b{elem}\s+Hỗ trợ\s+Lữ khách\b', f'Lữ Khách viện trợ hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\b{elem}\s+Lữ khách viện trợ\b', f'Lữ Khách viện trợ hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\bLữ khách viện trợ {elem}\b', f'Lữ Khách viện trợ hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\b{elem}\s+Lữ khách đa năng\b', f'Lữ Khách đa năng hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\bLữ khách đa năng {elem}\b', f'Lữ Khách đa năng hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\b{elem}\s+Lữ khách\b', f'Lữ Khách hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\bLữ khách {elem}\b', f'Lữ Khách hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\bđồng đội {elem}\b', f'đồng đội hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\bđồng đội của {elem}\b', f'đồng đội hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\bsát thương của {elem}\b', f'Sát Thương hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\bthiệt hại cho {elem}\b', f'Sát Thương hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\bKỹ năng viện trợ {elem}\b', f'Kỹ Năng Viện Trợ hệ {vi_elem}', sh, flags=re.I)
        sh = re.sub(rf'\bcủa {elem} do\b', f'hệ {vi_elem} thêm', sh, flags=re.I)
        sh = re.sub(rf'\bcho {elem} thêm\b', f'hệ {vi_elem} thêm', sh, flags=re.I)
        sh = re.sub(rf'\bSát thương của {elem} của tất cả\b', f'Sát Thương hệ {vi_elem} của tất cả', sh, flags=re.I)
        sh = re.sub(rf'\bSát thương hệ {vi_elem} của riêng mình\b', f'Sát Thương hệ {vi_elem} của bản thân', sh, flags=re.I)
        sh = re.sub(rf'\b{elem}\b', f'hệ {vi_elem}', sh)

    # 4. Standardize Trekker terms
    sh = re.sub(r'\bMain Lữ khách\b', 'Lữ Khách chủ lực', sh, flags=re.I)
    sh = re.sub(r'\bLữ khách chính\b', 'Lữ Khách chủ lực', sh, flags=re.I)
    sh = re.sub(r'\bLữ khách hỗ trợ\b', 'Lữ Khách viện trợ', sh, flags=re.I)
    sh = re.sub(r'\bHỗ trợ Lữ khách\b', 'Lữ Khách viện trợ', sh, flags=re.I)
    sh = re.sub(r'\bSupport Lữ khách\b', 'Lữ Khách viện trợ', sh, flags=re.I)
    sh = re.sub(r'\bLữ khách\b', 'Lữ Khách', sh)
    sh = re.sub(r'\bTăng hỗ trợ Sát thương Kỹ năng của Lữ khách\b', 'Tăng Sát Thương Kỹ Năng của Lữ Khách viện trợ', sh, flags=re.I)
    sh = re.sub(r'\bTăng hỗ trợ Sát thương Tuyệt kỹ của Lữ khách\b', 'Tăng Sát Thương Tuyệt Kỹ của Lữ Khách viện trợ', sh, flags=re.I)

    # 5. Combat stats & damage capitalization
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
    sh = re.sub(r'\bSát thương Kỹ năng\b', 'Sát Thương Kỹ Năng', sh)
    sh = re.sub(r'\bsát thương Kỹ năng\b', 'Sát Thương Kỹ Năng', sh)
    sh = re.sub(r'\bSát thương Tuyệt kỹ\b', 'Sát Thương Tuyệt Kỹ', sh)
    sh = re.sub(r'\bsát thương Tuyệt kỹ\b', 'Sát Thương Tuyệt Kỹ', sh)
    sh = re.sub(r'\bTấn công\b', 'Tấn Công', sh)
    sh = re.sub(r'\btấn công\b', 'Tấn Công', sh)
    sh = re.sub(r'\bTuyệt kỹ\b', 'Tuyệt Kỹ', sh)
    sh = re.sub(r'\btuyệt kỹ\b', 'Tuyệt Kỹ', sh)
    sh = re.sub(r'\bẤn ký\b', 'Ấn Ký', sh)
    sh = re.sub(r'\btăng Kỹ năng và Sát Thương Tuyệt Kỹ\b', 'tăng Sát Thương Kỹ Năng và Sát Thương Tuyệt Kỹ', sh, flags=re.I)

    # 6. Smooth out grammar, verbs, passive voice
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
    sh = re.sub(r'\bđiểm cộng dồn\b', 'tầng', sh, flags=re.I)
    sh = re.sub(r'\bnhận được một lá chắn\b', 'nhận lá chắn', sh, flags=re.I)
    sh = re.sub(r'\bnhận được một tấm khiên\b', 'nhận lá chắn', sh, flags=re.I)
    sh = re.sub(r'\bcó khiên\b', 'có lá chắn', sh, flags=re.I)
    sh = re.sub(r'\bcủa riêng mình\b', 'của bản thân', sh, flags=re.I)
    sh = re.sub(r'\bcủa chính mình\b', 'của bản thân', sh, flags=re.I)
    sh = re.sub(r'\bnhận được một hiệu ứng bổ sung:\b', 'nhận thêm hiệu ứng:', sh, flags=re.I)
    sh = re.sub(r'\bnhận thêm một hiệu ứng:\b', 'nhận thêm hiệu ứng:', sh, flags=re.I)
    sh = re.sub(r'\bcó thêm hiệu ứng:\b', 'nhận thêm hiệu ứng:', sh, flags=re.I)
    sh = re.sub(r'\bgây ra những điều sau đây cho mục tiêu:\b', 'gây hiệu ứng sau lên mục tiêu:', sh, flags=re.I)
    sh = re.sub(r'\bgây ra các hiệu ứng sau lên mục tiêu:\b', 'gây hiệu ứng sau lên mục tiêu:', sh, flags=re.I)
    sh = re.sub(r'\bđược trang bị "Viêm Khải"\b', 'mang hiệu ứng "Viêm Khải"', sh, flags=re.I)
    sh = re.sub(r'\bcó "Viêm Khải"\b', 'mang hiệu ứng "Viêm Khải"', sh, flags=re.I)
    sh = re.sub(r'\bbị "Xé Rách"\b', 'chịu trạng thái "Xé Rách"', sh, flags=re.I)
    sh = re.sub(r'\bbị dính "Lưu Phương"\b', 'chịu trạng thái "Lưu Phương"', sh, flags=re.I)
    sh = re.sub(r'\bdo (\[\[TOK\d+\]\])\b', r'thêm \1', sh)
    sh = re.sub(r'\bbởi (\[\[TOK\d+\]\])\b', r'thêm \1', sh)
    sh = re.sub(r'""+', '"', sh)

    # 7. Clean punctuation and spaces
    sh = re.sub(r'[ \t]{2,}', ' ', sh)
    sh = re.sub(r'\s+([,.:;?!])', r'\1', sh)

    restored = unshield_tokens(sh, toks)
    return restored
