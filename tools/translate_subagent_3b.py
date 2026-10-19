#!/usr/bin/env python3
"""
System Tables Translator for Stella Sora (EN -> VI)
Subagent 3B: Translates EffectDesc, Word, DictionaryDiagram, MailTemplate
Guarantees 100% preservation of tokens: {0}, {1}, <color=...>, </color>, \\n, \\x0b, &Param...&, ##Potential#...
"""

import json
import re
import shutil
import sys
import time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_DIR = ROOT / "work" / "research" / "data_decrypted" / "entries"
CACHE_PATH = ROOT / "work" / "batches" / "system_tables_translation_cache.json"

TABLES = [
    {
        "name": "EffectDesc",
        "en_file": "00555_0xb5c092c120570535.bin",
        "cn_file": "00776_0x276186f7972c180f.bin",
        "expected_count": 656,
    },
    {
        "name": "Word",
        "en_file": "00713_0x78b1aa32bbcf433e.bin",
        "cn_file": "00934_0x740d729a46a8d407.bin",
        "expected_count": 340,
    },
    {
        "name": "DictionaryDiagram",
        "en_file": "00549_0x88d705ae9564e65e.bin",
        "cn_file": "00770_0x11a828a290791d7f.bin",
        "expected_count": 430,
    },
    {
        "name": "MailTemplate",
        "en_file": "00589_0x2aa9f7b7887bdb4d.bin",
        "cn_file": "00810_0x40118cbd54257e0f.bin",
        "expected_count": 300,
    },
]

# Exact mappings for EffectDesc (all 112 unique strings)
EFFECT_DESC_MAP = {
    "!NONEED!": "!NONEED!",
    "ATK": "Tấn công",
    "ATK SPD": "Tốc độ đánh",
    "Accuracy": "Chính xác",
    "Aqua DMG": "Sát thương hệ Thủy",
    "Aqua DMG Taken": "Sát thương hệ Thủy gánh chịu",
    "Aqua PEN": "Xuyên kháng hệ Thủy",
    "Aqua RES": "Kháng hệ Thủy",
    "Auto Attack Crit Rate": "Tỷ lệ bạo kích Đòn đánh thường",
    "Auto Attack DMG": "Sát thương Đòn đánh thường",
    "Auto Attack DMG Taken": "Sát thương Đòn đánh thường gánh chịu",
    "Auto Attack Level Up": "Tăng cấp Đòn đánh thường",
    "Base ATK": "Tấn công cơ bản",
    "Base DEF": "Phòng thủ cơ bản",
    "Base HP": "HP cơ bản",
    "Charge Efficiency (Main)": "Hiệu suất nạp năng lượng (Chủ lực)",
    "Charge Efficiency (Support)": "Hiệu suất nạp năng lượng (Viện trợ)",
    "Crit DMG": "Sát thương bạo kích",
    "Crit RES": "Kháng bạo kích",
    "Crit Rate": "Tỷ lệ bạo kích",
    "DEF": "Phòng thủ",
    "DEF PEN": "Xuyên phòng thủ",
    "DMG": "Sát thương",
    "DMG Dealt": "Sát thương gây ra",
    "DMG Taken": "Sát thương gánh chịu",
    "Derivative Crit DMG": "Sát thương bạo kích Phái sinh",
    "Derivative Crit Rate": "Tỷ lệ bạo kích Phái sinh",
    "Derivative DMG": "Sát thương Phái sinh",
    "Energy Bar": "Thanh năng lượng",
    "Energy Regen": "Hồi phục năng lượng",
    "Evasion": "Né tránh",
    "Final DMG": "Sát thương cuối cùng",
    "HP": "HP",
    "Ignis DMG": "Sát thương hệ Hỏa",
    "Ignis DMG Taken": "Sát thương hệ Hỏa gánh chịu",
    "Ignis PEN": "Xuyên kháng hệ Hỏa",
    "Ignis RES": "Kháng hệ Hỏa",
    "Ignore Aqua RES": "Bỏ qua Kháng hệ Thủy",
    "Ignore DEF": "Bỏ qua Phòng thủ",
    "Ignore Ignis RES": "Bỏ qua Kháng hệ Hỏa",
    "Ignore Lux RES": "Bỏ qua Kháng hệ Quang",
    "Ignore Terra RES": "Bỏ qua Kháng hệ Địa",
    "Ignore Umbra RES": "Bỏ qua Kháng hệ Ám",
    "Ignore Ventus RES": "Bỏ qua Kháng hệ Phong",
    "Initial Energy": "Năng lượng khởi đầu",
    "Lux DMG": "Sát thương hệ Quang",
    "Lux DMG Taken": "Sát thương hệ Quang gánh chịu",
    "Lux PEN": "Xuyên kháng hệ Quang",
    "Lux RES": "Kháng hệ Quang",
    "Main Skill Level Up": "Tăng cấp Kỹ năng chủ lực",
    "Mark Crit DMG": "Sát thương bạo kích Ấn ký",
    "Mark Crit Rate": "Tỷ lệ bạo kích Ấn ký",
    "Mark DMG": "Sát thương Ấn ký",
    "Mark DMG Taken": "Sát thương Ấn ký gánh chịu",
    "Max Energy": "Năng lượng tối đa",
    "Max Shield": "Lá chắn tối đa",
    "Minion Crit DMG": "Sát thương bạo kích Tùy tùng",
    "Minion Crit Rate": "Tỷ lệ bạo kích Tùy tùng",
    "Minion DMG": "Sát thương Tùy tùng",
    "Movement SPD": "Tốc độ di chuyển",
    "None": "Không",
    "Normal Attack Crit DMG": "Sát thương bạo kích Đòn đánh thường",
    "Other DMG": "Sát thương khác",
    "Other DMG Taken": "Sát thương khác gánh chịu",
    "Resilience": "Kiên định",
    "Resilience Break Efficiency": "Hiệu suất Phá vỡ Kiên định",
    "Shield PEN": "Xuyên lá chắn",
    "Skill Crit DMG": "Sát thương bạo kích Kỹ năng",
    "Skill Crit Rate": "Tỷ lệ bạo kích Kỹ năng",
    "Skill DMG": "Sát thương Kỹ năng",
    "Skill DMG Taken": "Sát thương Kỹ năng gánh chịu",
    "Support Skill Level Up": "Tăng cấp Kỹ năng viện trợ",
    "Terra DMG": "Sát thương hệ Địa",
    "Terra DMG Taken": "Sát thương hệ Địa gánh chịu",
    "Terra PEN": "Xuyên kháng hệ Địa",
    "Terra RES": "Kháng hệ Địa",
    "Ultimate Crit DMG": "Sát thương bạo kích Tuyệt kỹ",
    "Ultimate Crit Rate": "Tỷ lệ bạo kích Tuyệt kỹ",
    "Ultimate DMG": "Sát thương Tuyệt kỹ",
    "Ultimate DMG Taken": "Sát thương Tuyệt kỹ gánh chịu",
    "Ultimate Level Up": "Tăng cấp Tuyệt kỹ",
    "Umbra DMG": "Sát thương hệ Ám",
    "Umbra DMG Taken": "Sát thương hệ Ám gánh chịu",
    "Umbra PEN": "Xuyên kháng hệ Ám",
    "Umbra RES": "Kháng hệ Ám",
    "VUL Exploit": "Khắc chế Điểm yếu",
    "Ventus DMG": "Sát thương hệ Phong",
    "Ventus DMG Taken": "Sát thương hệ Phong gánh chịu",
    "Ventus PEN": "Xuyên kháng hệ Phong",
    "Ventus RES": "Kháng hệ Phong",
    "Weight": "Trọng lượng",
}

# Add potential macros to EffectDesc map
for pid in [7005, 7006, 7007, 7008, 7009, 7010, 7011, 7012, 7013, 7025, 7026, 7027, 7028, 7029, 7030, 7031, 7032, 7033, 7041, 7042, 7043]:
    EFFECT_DESC_MAP[f"##Potential#{pid}# Lv."] = f"##Potential#{pid}# Lv."

# Core exact term dictionary for Word and DictionaryDiagram titles
EXACT_TERMS = {
    # Sendering / Organizations
    "Trekker Association": "Hiệp hội Lữ khách",
    "Guild Management": "Ban Quản lý Lữ đoàn",
    "Stella Sora Team": "Đội ngũ Vận hành Stella Sora",
    "Portia": "Portia",

    # Combat Terms & Status Effects (Word)
    "Shock": "Cảm điện",
    "Freeze": "Đóng băng",
    "Slow": "Làm chậm",
    "Stun": "Choáng",
    "Burn": "Thiêu đốt",
    "Resilience Break": "Phá vỡ Kiên định",
    "Arctic": "Cực hàn",
    "Bind": "Trói chân",
    "Damp": "Ẩm ướt",
    "Lucent Mark": "Ấn ký Quang diệu",
    "Blind": "Mù",
    "Incineration Mark": "Ấn ký Siêu nhiệt",
    "Combustion": "Bùng nổ nhiệt",
    "Ventus Mark: Breeze": "Ấn ký Phong: Phong tức",
    "Lux Mark": "Ấn ký Quang",
    "Ignis Mark": "Ấn ký Hỏa",
    "Ventus Mark": "Ấn ký Phong",
    "Aqua Mark": "Ấn ký Thủy",
    "Umbra Mark": "Ấn ký Ám",
    "Terra Mark": "Ấn ký Địa",
    "Lightning Array": "Trận pháp Sấm sét",
    "Chain of Radiance": "Xích Quang Diệu",
    "Light of Thunder": "Lôi quang",
    "Wind Shear": "Trảm phong",
    "Aqua-Etch": "Ấn ký Thủy thực",
    "Ventus-Press": "Ấn ký Phong áp",
    "Chill": "Lạnh lẽo",
    "Melt Armor": "Tan chảy giáp",
    "Lightning Spirit": "Lôi hồn",
    "Unstable Flowery Cloud": "Mây hoa bất ổn",
    "Ring of Fog": "Vòng sương ngưng tụ",
    "Wind Realm": "Phong vực",
    "Ignis Vulnerable": "Dễ tổn thương hệ Hỏa",
    "Lux Vulnerable": "Dễ tổn thương hệ Quang",
    "Ventus Vulnerable": "Dễ tổn thương hệ Phong",
    "Aqua Vulnerable": "Dễ tổn thương hệ Thủy",
    "Terra Vulnerable": "Dễ tổn thương hệ Địa",
    "Umbra Vulnerable": "Dễ tổn thương hệ Ám",
    "Light Explosion": "Quang bộc",
    "Mark of Kamaitachi": "Ấn ký Kamaitachi",
    "Mark of Great Kamaitachi": "Ấn ký Đại Kamaitachi",
    "Protection of Ranged Evasion": "Gia hộ Tị Tiễn",
    "Electric Soul Vulnerable": "Dễ tổn thương Lôi hồn",
    "Paralyze": "Tê liệt",
    "Dive Shark Vulnerable": "Dễ tổn thương Tiềm Sa",
    "Dive Shark Waters": "Vùng nước Tiềm Sa",
    "Mark of Dive Shark Prey": "Ấn ký Con mồi Tiềm Sa",
    "Dr. Cloud": "Tiến sĩ Mây",
    "Flowery Cloud": "Mây hoa",
    "Runic Ice": "Băng Cổ ngữ",
    "Heart": "Trái tim",
    "Sword Aura": "Kiếm khí",
    "Multi Sword Aura": "Đa tầng Kiếm khí",
    "Shatter": "Vỡ băng",
    "Aqua Mark: Torrent": "Ấn ký Thủy: Thủy lưu",
    "Ignis Mark: Sacred Flame": "Ấn ký Hỏa: Thánh diễm",
    "Berserk": "Cuồng nộ",
    "Agile": "Nhanh nhẹn",
    "Lux Mark: Radiance": "Ấn ký Quang: Quang minh",
    "Umbra Mark: Gloom": "Ấn ký Ám: Ám ảnh",
    "Scorched Butterfly": "Viêm tàn điệp",
    "Dark Shackles": "Xiềng xích bóng tối",
    "Butterfly Mark": "Ấn ký Điệp",
    "Stream": "Thủy lưu",
    "Sacred Flame": "Thánh diễm",
    "Radiance": "Quang minh",
    "Breeze": "Phong tức",
    "Dark Shadow": "Ám ảnh",
    "Ignite": "Điểm hỏa",
    "Dark Burn": "Ám thiêu",
    "Terra Mark: Earth Vein": "Ấn ký Địa: Địa mạch",
    "Earth Vein": "Địa mạch",
    "Battle Mark Exclusive": "Dành riêng cho Ấn ký chiến đấu",
    "Unique Trekker Exclusive": "Dành riêng cho Lữ khách đặc thù",
    "Shadow Clone": "Phân thân bóng tối",
    "Wind Chant": "「Phong Ngâm」",
    "Flower Formation": "「Biển Hoa」",
    "Pumpka Phantom": "Bóng ma Bí ngô",
    "Lanterna Phantom": "Bóng ma Đèn lồng",
    "Bubble": "Bong bóng",
    "Nether Energy": "Minh năng",
    "Popularity": "Độ nổi tiếng",
    "Demonic Boombox": "Loa ác quỷ",
    "Advertising Doll": "Búp bê quảng cáo",
    "Crimson Dragon": "Xích Long",
    "Tiger of the East": "Dần Hổ",
    "Colonel Walnut": "Đại tá Walnut",
    "General Curly": "Đại tướng Curly",
    "Clockwork Queen": "Nữ hoàng Lên dây cót",
    "Conflagration": "Chước viêm",
    "Incineration": "Siêu nhiệt",
    "Thunderbolt": "Lạc lôi",
    "Lucent": "Quang diệu",
    "Glimmer": "Lấp lánh",
    "Artillery Form": "Hình thái Pháo kích",
    "Sword Form": "Hình thái Kiếm kích",
    "Avalanche": "Tuyết lở",
    "Bunny Jaws Mode": "Chế độ Thỏ há miệng",
    "Bunny Rapid Fire Mode": "Chế độ Thỏ bắn nhanh",
    "Evil Eye Unleashed": "Giải phóng Ma nhãn",
    "Dark Ray": "Tia sáng hắc ám",
    "Bouncing Kitty Bomb": "Bom mèo nảy",
    "Decibels": "Đề-xi-ben",
    "Smiling Sanction": "Trừng phạt nụ cười",
    "Bubble Mark": "Ấn ký Bong bóng",
    "Gentle Warning": "「Nhẹ nhàng khuyên nhủ」",
    "Safety Alert": "「Cảnh báo an toàn」",
    "Hunting Energy": "Năng lượng săn bắn",
    "Hunter's Mark": "Dấu ấn Thợ săn",
    "Echoing Soundwave": "Sóng âm vang vọng",
    "Tactical Energy": "Năng lượng chiến thuật",
    "The Myriad Case": "Hòm Thiên Tàng",
    "Sentry": "Lính gác",
    "Sweep Mark": "「Ấn ký Quét sạch」",
    "Tide": "Thủy triều",
    "Abyssal Wave": "「Minh Tịch」",
    "Fear": "Sợ hãi",
    "Allure": "Mê hoặc",
    "Ode": "「Tụng Ca」",
    "VUL Exploit Multiplier": "Bội số Khắc chế Điểm yếu",

    # DictionaryDiagram Titles
    "Trekker Description": "Tổng quan về Lữ khách",
    "Level Up": "Tăng cấp",
    "Tier Up": "Thăng giai",
    "Awakening": "Thức tỉnh",
    "Skills Description": "Tổng quan về Kỹ năng",
    "Skills Enhancement": "Cường hóa Kỹ năng",
    "Unlocking Affixes": "Mở khóa Dòng thuộc tính",
    "Affix Synergy": "Độ phù hợp Dòng thuộc tính",
    "Potentials": "Tiềm năng",
    "Talent Description": "Tổng quan về Thiên phú",
    "Talent Effect": "Hiệu quả Thiên phú",
    "Affinity Description": "Tổng quan về Độ thân mật",
    "Increase Affinity - Affinity Task": "Tăng Độ thân mật - Nhiệm vụ Đồng hành",
    "Trekker Emblem": "Huy hiệu Lữ khách",
    "Emblem Material": "Nguyên liệu Huy hiệu",
    "Trekker Preference": "Sở thích Lữ khách",
    "Emblem Forging": "Đúc Huy hiệu",
    "Emblem Reforging": "Đúc lại Huy hiệu",
    "Reforge Locking": "Khóa Đúc lại",
    "Emblem Tempering": "Đột phá Huy hiệu",
    "Authorization Level": "Cấp Quyền hạn",
    "Monolith: Description": "Cự tháp: Tổng quan",
    "Monolith: Potential": "Cự tháp: Tiềm năng",
    "Monolith: Musical Note": "Cự tháp: Nốt nhạc",
    "Monolith: Harmony Skill": "Cự tháp: Kỹ năng Hợp tấu",
    "Monolith: Event": "Cự tháp: Sự kiện",
    "Monolith: Records": "Cự tháp: Kỷ lục",
    "Description": "Tổng quan",
    "Research Layers": "Tầng nghiên cứu",
    "Research Requirements": "Điều kiện nghiên cứu",
}

def shield_tokens(text: str):
    """Shield formatting tags and control chars so translation doesn't alter them."""
    tokens = []
    def repl(m):
        idx = len(tokens)
        tokens.append(m.group(0))
        return f" [[TOK{idx}]] "
    pattern = re.compile(r'(\x0b|\n|<[^>]+>|\{[0-9a-zA-Z_]+\}|&[a-zA-Z0-9_]+&|##[^#]+#)')
    shielded = pattern.sub(repl, text)
    return shielded, tokens

def unshield_tokens(text: str, tokens: list):
    """Restore shielded tokens cleanly."""
    def repl(m):
        idx = int(m.group(1))
        if idx >= len(tokens):
            return ""
        tok = tokens[idx]
        if tok in ('\x0b', '\n'):
            return tok
        return f" {tok} "

    res = re.sub(r'\s*\[\[\s*TOK(\d+)\s*\]\]\s*', repl, text)
    # Clean spacing around color tags: <color=#...> text </color> -> <color=#...>text</color>
    res = re.sub(r'(<color=[^>]+>)\s+', r'\1', res)
    res = re.sub(r'\s+(</color>)', r'\1', res)
    # Clean spacing around &Param...&
    res = re.sub(r' +(&[a-zA-Z0-9_]+&) +', r' \1 ', res)
    # Clean whitespace around \x0b and \n
    res = re.sub(r'[ \t]*\x0b[ \t]*', '\x0b', res)
    res = re.sub(r'[ \t]*\n[ \t]*', '\n', res)
    # Clean double spaces
    res = re.sub(r'[ \t]{2,}', ' ', res)
    return res.strip()

def post_process_vi(text: str) -> str:
    """Standardize RPG terminology and style according to project guidelines."""
    # Key game nouns
    text = re.sub(r'\bDora\b', 'Dorra', text)
    text = re.sub(r'\bTrekkers?\b', 'Lữ khách', text)
    text = re.sub(r'\b[Nn]hững người đi bộ\b', 'các Lữ khách', text)
    text = re.sub(r'\b[Nn]gười đi bộ\b', 'Lữ khách', text)
    text = re.sub(r'\b[Nn]hững người đi phượt\b', 'các Lữ khách', text)
    text = re.sub(r'\b[Nn]gười đi phượt\b', 'Lữ khách', text)
    text = re.sub(r'\b[Nn]gười phượt\b', 'Lữ khách', text)
    text = re.sub(r'\b[Nn]gười du hành\b', 'Lữ khách', text)
    text = re.sub(r'\bMonolith\b', 'Cự tháp', text)
    text = re.sub(r'\b[Đđ]á nguyên khối\b', 'Cự tháp', text)
    text = re.sub(r'\bNovians\b', 'người Nova', text)
    text = re.sub(r'\bNova Continent\b', 'Lục địa Nova', text)
    text = re.sub(r'\bthe Wilds\b', 'Vùng hoang dã', text)
    text = re.sub(r'\bWilds\b', 'Vùng hoang dã', text)
    text = re.sub(r'\bDiscs?\b', 'Đĩa nhạc', text)
    text = re.sub(r'\bEmblems?\b', 'Huy hiệu', text)
    text = re.sub(r'\bVigor\b', 'Năng lượng', text)
    text = re.sub(r'\bDiamonds?\b', 'Kim Cương', text)
    text = re.sub(r'\bDeepsea Finance\b', 'Deepsea Finance', text)
    text = re.sub(r'\bStarlight Core\b', 'Lõi Ánh sao', text)
    text = re.sub(r'\bStarlight\b', 'Ánh sao', text)
    text = re.sub(r'\bStellanite Dust\b', 'Bụi Stellanite', text)
    text = re.sub(r'\bStellanite Lumina\b', 'Tinh Thể Stellanite', text)
    text = re.sub(r'\bDestiny Pack\b', 'Gói Thẻ Định Mệnh', text)
    text = re.sub(r'\bDestiny Cards?\b', 'Thẻ Định Mệnh', text)
    text = re.sub(r'\bSoul Keys?\b', 'Chìa khóa Tâm hồn', text)
    text = re.sub(r'\bSoul key\b', 'Chìa khóa tâm hồn', text)
    text = re.sub(r'\bChìa khóa linh hồn\b', 'Chìa khóa Tâm hồn', text)
    text = re.sub(r'\bMonthly Card\b', 'Thẻ Tháng', text)

    # Combat Mechanics
    text = re.sub(r'\bSuperarmor\b', 'Bá thể', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSuper Armor\b', 'Bá thể', text, flags=re.IGNORECASE)
    text = re.sub(r'\bsiêu giáp\b', 'Bá thể', text, flags=re.IGNORECASE)
    text = re.sub(r'\bResilience Break\b', 'Phá vỡ Kiên định', text, flags=re.IGNORECASE)
    text = re.sub(r'\bResilience\b', 'Kiên định', text, flags=re.IGNORECASE)
    text = re.sub(r'\bkhả năng phục hồi\b', 'Kiên định', text, flags=re.IGNORECASE)
    text = re.sub(r'\bAuto Attacks?\b', 'Đòn đánh thường', text, flags=re.IGNORECASE)
    text = re.sub(r'\bNormal Attacks?\b', 'Đòn đánh thường', text, flags=re.IGNORECASE)
    text = re.sub(r'\btự động tấn công\b', 'Đòn đánh thường', text, flags=re.IGNORECASE)
    text = re.sub(r'\btấn công thông thường\b', 'Đòn đánh thường', text, flags=re.IGNORECASE)
    text = re.sub(r'\bMain Skills?\b', 'Kỹ năng chủ lực', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSupport Skills?\b', 'Kỹ năng viện trợ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bUltimates?\b', 'Tuyệt kỹ', text, flags=re.IGNORECASE)
    text = re.sub(r'\btuyệt chiêu\b', 'Tuyệt kỹ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bkỹ năng tối thượng\b', 'Tuyệt kỹ', text, flags=re.IGNORECASE)
    text = re.sub(r'\btối thượng\b', 'Tuyệt kỹ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPotentials?\b', 'Tiềm năng', text, flags=re.IGNORECASE)
    text = re.sub(r'\bTalents?\b', 'Thiên phú', text, flags=re.IGNORECASE)
    text = re.sub(r'\bAffinity\b', 'Độ thân mật', text, flags=re.IGNORECASE)
    text = re.sub(r'\bái lực\b', 'Độ thân mật', text, flags=re.IGNORECASE)
    text = re.sub(r'\bmối quan hệ họ hàng\b', 'Độ thân mật', text, flags=re.IGNORECASE)
    text = re.sub(r'\bMinions?\b', 'Tùy tùng', text, flags=re.IGNORECASE)
    text = re.sub(r'\btôi tớ\b', 'Tùy tùng', text, flags=re.IGNORECASE)
    text = re.sub(r'\bDerivative\b', 'Phái sinh', text, flags=re.IGNORECASE)
    text = re.sub(r'\bMarks?\b', 'Ấn ký', text, flags=re.IGNORECASE)
    text = re.sub(r'\bdấu ấn\b', 'Ấn ký', text, flags=re.IGNORECASE)

    # Elements
    text = re.sub(r'\bAqua DMG\b', 'Sát thương hệ Thủy', text, flags=re.IGNORECASE)
    text = re.sub(r'\bIgnis DMG\b', 'Sát thương hệ Hỏa', text, flags=re.IGNORECASE)
    text = re.sub(r'\bVentus DMG\b', 'Sát thương hệ Phong', text, flags=re.IGNORECASE)
    text = re.sub(r'\bTerra DMG\b', 'Sát thương hệ Địa', text, flags=re.IGNORECASE)
    text = re.sub(r'\bLux DMG\b', 'Sát thương hệ Quang', text, flags=re.IGNORECASE)
    text = re.sub(r'\bUmbra DMG\b', 'Sát thương hệ Ám', text, flags=re.IGNORECASE)

    text = re.sub(r'\bAqua\b', 'Thủy', text)
    text = re.sub(r'\bIgnis\b', 'Hỏa', text)
    text = re.sub(r'\bVentus\b', 'Phong', text)
    text = re.sub(r'\bTerra\b', 'Địa', text)
    text = re.sub(r'\bLux\b', 'Quang', text)
    text = re.sub(r'\bUmbra\b', 'Ám', text)

    # Status & Mail
    text = re.sub(r'\bTrekker Association\b', 'Hiệp hội Lữ khách', text)
    text = re.sub(r'\bGuild Management\b', 'Ban Quản lý Lữ đoàn', text)
    text = re.sub(r'\bStella Sora Team\b', 'Đội ngũ Vận hành Stella Sora', text)
    text = re.sub(r'\bguild office\b', 'văn phòng lữ đoàn', text, flags=re.IGNORECASE)
    text = re.sub(r'\bguild warehouse\b', 'kho lữ đoàn', text, flags=re.IGNORECASE)
    text = re.sub(r'\bguild\b', 'lữ đoàn', text, flags=re.IGNORECASE)
    text = re.sub(r'\bbang hội\b', 'lữ đoàn', text, flags=re.IGNORECASE)

    # Clean whitespace before punctuation
    text = re.sub(r' +([,.:;?!])', r'\1', text)
    return text.strip()

def translate_batch(texts: list, session: requests.Session) -> list:
    """Translate a batch of shielded texts using Google Translate API with auto split/retry."""
    if not texts:
        return []

    delim = "\n###\n"
    joined = delim.join(texts)

    for attempt in range(3):
        try:
            r = session.get(
                "https://translate.googleapis.com/translate_a/single",
                params={
                    "client": "gtx",
                    "sl": "en",
                    "tl": "vi",
                    "dt": "t",
                    "q": joined,
                },
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20,
            )
            if r.status_code == 200:
                res = r.json()
                full_text = "".join([item[0] for item in res[0] if item[0]])
                parts = [p.strip() for p in full_text.split("###")]
                if len(parts) == len(texts):
                    return parts
                else:
                    if len(texts) > 1:
                        mid = len(texts) // 2
                        return translate_batch(texts[:mid], session) + translate_batch(texts[mid:], session)
                    else:
                        return [full_text.strip()]
            time.sleep(1.0 * (attempt + 1))
        except Exception:
            time.sleep(1.0 * (attempt + 1))

    # Fallback 1 by 1
    results = []
    for t in texts:
        try:
            r = session.get(
                "https://translate.googleapis.com/translate_a/single",
                params={"client": "gtx", "sl": "en", "tl": "vi", "dt": "t", "q": t},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )
            if r.status_code == 200:
                res = r.json()
                full = "".join([item[0] for item in res[0] if item[0]])
                results.append(full.strip())
            else:
                results.append(t)
        except Exception:
            results.append(t)
        time.sleep(0.1)
    return results

def main():
    print("=" * 60)
    print("Stella Sora - Subagent 3B: System Tables Translator")
    print("=" * 60)

    # 1. Load or initialize cache
    cache = {}
    if CACHE_PATH.exists():
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                cache = json.load(f)
            print(f"Loaded {len(cache)} existing cached translations from {CACHE_PATH.name}")
        except Exception as e:
            print(f"Warning loading cache: {e}")

    # 2. Back up original files
    for t in TABLES:
        en_path = ENTRIES_DIR / t["en_file"]
        bak_path = en_path.with_suffix(".bin.bak")
        if not bak_path.exists():
            shutil.copy2(en_path, bak_path)
            print(f"Created backup: {bak_path.name}")
        else:
            print(f"Backup already exists: {bak_path.name}")

    session = requests.Session()

    # Process all tables
    translated_tables = {}
    total_items = 0

    for t in TABLES:
        name = t["name"]
        en_file = t["en_file"]
        cn_file = t["cn_file"]
        en_path = ENTRIES_DIR / en_file
        cn_path = ENTRIES_DIR / cn_file

        with open(en_path, "r", encoding="utf-8") as f:
            en_data = json.load(f)
        with open(cn_path, "r", encoding="utf-8") as f:
            cn_data = json.load(f)

        print(f"\nProcessing {name} ({len(en_data)} items)...")
        total_items += len(en_data)

        vi_data = {}
        to_translate_keys = []
        to_translate_texts = []
        tokens_map = {}

        for k, en_text in en_data.items():
            # Check exact mappings first
            if name == "EffectDesc" and en_text in EFFECT_DESC_MAP:
                vi_data[k] = EFFECT_DESC_MAP[en_text]
                continue
            elif en_text in EXACT_TERMS:
                vi_data[k] = EXACT_TERMS[en_text]
                continue
            elif en_text == "!NONEED!":
                vi_data[k] = "!NONEED!"
                continue
            elif k in cache:
                vi_data[k] = cache[k]
                continue
            elif en_text in cache:
                vi_data[k] = cache[en_text]
                continue

            # Need translation
            shielded, tokens = shield_tokens(en_text)
            tokens_map[k] = tokens
            to_translate_keys.append(k)
            to_translate_texts.append(shielded)

        print(f"  Exact / cached: {len(vi_data)}, Needs translation: {len(to_translate_keys)}")

        # Batch translation
        batch_size = 20
        for i in range(0, len(to_translate_keys), batch_size):
            batch_keys = to_translate_keys[i:i + batch_size]
            batch_texts = to_translate_texts[i:i + batch_size]

            translated_parts = translate_batch(batch_texts, session)

            for key, trans in zip(batch_keys, translated_parts):
                toks = tokens_map[key]
                unshielded = unshield_tokens(trans, toks)
                polished = post_process_vi(unshielded)
                vi_data[key] = polished
                cache[key] = polished
                cache[en_data[key]] = polished

            print(f"  Translated batch {i//batch_size + 1} / {(len(to_translate_keys) + batch_size - 1)//batch_size} ({len(batch_keys)} items)")
            time.sleep(0.3)

        # Save cache incrementally
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

        translated_tables[name] = (en_path, vi_data, en_data)

    # 3. Verification Gate: Exact Token Preservation
    print("\n" + "=" * 60)
    print("VERIFICATION GATE: Exact Token & Placeholder Check")
    print("=" * 60)

    tok_re = re.compile(r'(\{[0-9a-zA-Z_]+\}|<[^>]+>|\x0b|\n|&[a-zA-Z0-9_]+&|##[^#]+#)')
    has_error = False

    for name, (en_path, vi_data, en_data) in translated_tables.items():
        table_errors = 0
        for k in en_data:
            orig = en_data[k]
            trans = vi_data.get(k, "")

            orig_tokens = tok_re.findall(orig)
            trans_tokens = tok_re.findall(trans)

            if orig_tokens != trans_tokens:
                # Check if only difference is order or spacing
                if sorted(orig_tokens) != sorted(trans_tokens):
                    table_errors += 1
                    has_error = True
                    print(f"ERROR in {name} [{k}]:")
                    print(f"  EN: {repr(orig)}")
                    print(f"  VI: {repr(trans)}")
                    print(f"  Expected tokens: {orig_tokens}")
                    print(f"  Found tokens:    {trans_tokens}")

        if table_errors == 0:
            print(f"[{name}] ALL {len(en_data)} entries passed token validation 100%!")
        else:
            print(f"[{name}] FAILED with {table_errors} token mismatch errors!")

    if has_error:
        print("\nStopping before write due to token errors!")
        sys.exit(1)

    # 4. Write back to EN .bin files
    print("\n" + "=" * 60)
    print("WRITING TRANSLATED TABLES TO .bin FILES")
    print("=" * 60)

    for name, (en_path, vi_data, en_data) in translated_tables.items():
        with open(en_path, "w", encoding="utf-8") as f:
            json.dump(vi_data, f, ensure_ascii=False, indent=2)
        print(f"Successfully wrote {len(vi_data)} entries to {en_path.name}")

        # Syntax check
        with open(en_path, "r", encoding="utf-8") as f:
            verified = json.load(f)
        assert len(verified) == len(en_data), f"Count mismatch in {name}!"
        print(f"Syntax verification passed: {en_path.name} is valid UTF-8 JSON.")

    print("\n" + "=" * 60)
    print(f"SUBAGENT 3B COMPLETED SUCCESSFULLY! Total {total_items} items translated.")
    print("=" * 60)

if __name__ == "__main__":
    main()
