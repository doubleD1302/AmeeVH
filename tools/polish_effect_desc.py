#!/usr/bin/env python3
"""Polisher for EffectDesc table (00555_0xb5c092c120570535.bin)."""

import json
from pathlib import Path

EFFECT_DESC_MAP = {
    '!NONEED!': '!NONEED!',
    'ATK': 'Tấn Công',
    'ATK SPD': 'Tốc Độ Đánh',
    'Accuracy': 'Chính Xác',
    'Aqua DMG': 'Sát Thương hệ Thủy',
    'Aqua DMG Taken': 'Sát Thương hệ Thủy Gánh Chịu',
    'Aqua PEN': 'Xuyên Kháng hệ Thủy',
    'Aqua RES': 'Kháng hệ Thủy',
    'Auto Attack Crit Rate': 'Tỷ Lệ Bạo Kích Đòn Đánh Thường',
    'Auto Attack DMG': 'Sát Thương Đòn Đánh Thường',
    'Auto Attack DMG Taken': 'Sát Thương Đòn Đánh Thường Gánh Chịu',
    'Auto Attack Level Up': 'Tăng Cấp Đòn Đánh Thường',
    'Base ATK': 'Tấn Công Cơ Bản',
    'Base DEF': 'Phòng Thủ Cơ Bản',
    'Base HP': 'HP Cơ Bản',
    'Charge Efficiency (Main)': 'Hiệu Suất Nạp Năng Lượng (Chủ Lực)',
    'Charge Efficiency (Support)': 'Hiệu Suất Nạp Năng Lượng (Viện Trợ)',
    'Crit DMG': 'Sát Thương Bạo Kích',
    'Crit RES': 'Kháng Bạo Kích',
    'Crit Rate': 'Tỷ Lệ Bạo Kích',
    'DEF': 'Phòng Thủ',
    'DEF PEN': 'Xuyên Phòng Thủ',
    'DMG': 'Sát Thương',
    'DMG Dealt': 'Sát Thương Gây Ra',
    'DMG Taken': 'Sát Thương Gánh Chịu',
    'Derivative Crit DMG': 'Sát Thương Bạo Kích Phái Sinh',
    'Derivative Crit Rate': 'Tỷ Lệ Bạo Kích Phái Sinh',
    'Derivative DMG': 'Sát Thương Phái Sinh',
    'Energy Bar': 'Thanh Năng Lượng',
    'Energy Regen': 'Hồi Phục Năng Lượng',
    'Evasion': 'Né Tránh',
    'Final DMG': 'Sát Thương Cuối Cùng',
    'HP': 'HP',
    'Ignis DMG': 'Sát Thương hệ Hỏa',
    'Ignis DMG Taken': 'Sát Thương hệ Hỏa Gánh Chịu',
    'Ignis PEN': 'Xuyên Kháng hệ Hỏa',
    'Ignis RES': 'Kháng hệ Hỏa',
    'Ignore Aqua RES': 'Bỏ Qua Kháng hệ Thủy',
    'Ignore DEF': 'Bỏ Qua Phòng Thủ',
    'Ignore Ignis RES': 'Bỏ Qua Kháng hệ Hỏa',
    'Ignore Lux RES': 'Bỏ Qua Kháng hệ Quang',
    'Ignore Terra RES': 'Bỏ Qua Kháng hệ Địa',
    'Ignore Umbra RES': 'Bỏ Qua Kháng hệ Ám',
    'Ignore Ventus RES': 'Bỏ Qua Kháng hệ Phong',
    'Initial Energy': 'Năng Lượng Khởi Đầu',
    'Lux DMG': 'Sát Thương hệ Quang',
    'Lux DMG Taken': 'Sát Thương hệ Quang Gánh Chịu',
    'Lux PEN': 'Xuyên Kháng hệ Quang',
    'Lux RES': 'Kháng hệ Quang',
    'Main Skill Level Up': 'Tăng Cấp Kỹ Năng Chủ Lực',
    'Mark Crit DMG': 'Sát Thương Bạo Kích Ấn Ký',
    'Mark Crit Rate': 'Tỷ Lệ Bạo Kích Ấn Ký',
    'Mark DMG': 'Sát Thương Ấn Ký',
    'Mark DMG Taken': 'Sát Thương Ấn Ký Gánh Chịu',
    'Max Energy': 'Năng Lượng Tối Đa',
    'Max Shield': 'Lá Chắn Tối Đa',
    'Minion Crit DMG': 'Sát Thương Bạo Kích Tùy Tùng',
    'Minion Crit Rate': 'Tỷ Lệ Bạo Kích Tùy Tùng',
    'Minion DMG': 'Sát Thương Tùy Tùng',
    'Movement SPD': 'Tốc Độ Di Chuyển',
    'None': 'Không',
    'Normal Attack Crit DMG': 'Sát Thương Bạo Kích Đòn Đánh Thường',
    'Other DMG': 'Sát Thương Khác',
    'Other DMG Taken': 'Sát Thương Khác Gánh Chịu',
    'Resilience': 'Kiên Định',
    'Resilience Break Efficiency': 'Hiệu Suất Phá Vỡ Kiên Định',
    'Shield PEN': 'Xuyên Lá Chắn',
    'Skill Crit DMG': 'Sát Thương Bạo Kích Kỹ Năng',
    'Skill Crit Rate': 'Tỷ Lệ Bạo Kích Kỹ Năng',
    'Skill DMG': 'Sát Thương Kỹ Năng',
    'Skill DMG Taken': 'Sát Thương Kỹ Năng Gánh Chịu',
    'Support Skill Level Up': 'Tăng Cấp Kỹ Năng Viện Trợ',
    'Terra DMG': 'Sát Thương hệ Địa',
    'Terra DMG Taken': 'Sát Thương hệ Địa Gánh Chịu',
    'Terra PEN': 'Xuyên Kháng hệ Địa',
    'Terra RES': 'Kháng hệ Địa',
    'Ultimate Crit DMG': 'Sát Thương Bạo Kích Tuyệt Kỹ',
    'Ultimate Crit Rate': 'Tỷ Lệ Bạo Kích Tuyệt Kỹ',
    'Ultimate DMG': 'Sát Thương Tuyệt Kỹ',
    'Ultimate DMG Taken': 'Sát Thương Tuyệt Kỹ Gánh Chịu',
    'Ultimate Level Up': 'Tăng Cấp Tuyệt Kỹ',
    'Umbra DMG': 'Sát Thương hệ Ám',
    'Umbra DMG Taken': 'Sát Thương hệ Ám Gánh Chịu',
    'Umbra PEN': 'Xuyên Kháng hệ Ám',
    'Umbra RES': 'Kháng hệ Ám',
    'VUL Exploit': 'Khắc Chế Điểm Yếu',
    'Ventus DMG': 'Sát Thương hệ Phong',
    'Ventus DMG Taken': 'Sát Thương hệ Phong Gánh Chịu',
    'Ventus PEN': 'Xuyên Kháng hệ Phong',
    'Ventus RES': 'Kháng hệ Phong',
    'Weight': 'Trọng Lượng'
}

def polish_effect_desc(items):
    polished = []
    changes = 0
    for it in items:
        en = it['en']
        orig_vi = it['vi_current']
        
        # Check potential Lv.
        if en.startswith('##Potential#') and en.endswith('# Lv.'):
            tag = en[:-4]  # strips ' Lv.', preserving '##Potential#xxxx#'
            new_vi = f"{tag} Cấp"
        elif en in EFFECT_DESC_MAP:
            new_vi = EFFECT_DESC_MAP[en]
        else:
            new_vi = orig_vi
            
        if new_vi != orig_vi:
            changes += 1
            
        polished.append({
            'key': it['key'],
            'en': en,
            'vi': new_vi
        })
    print(f"EffectDesc: {changes} items updated to standardized terminology.")
    return polished
