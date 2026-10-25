#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Contextual Polish Engine for 20,680 Dialogue Lines (Campaign 19).
Handles:
1. Idiom / Calque remediation (replaces literal word-by-word machine translations with natural anime/light novel expressions).
2. Pronoun softening (converts robotic 'tôi - bạn' into contextual conversational pronouns).
3. Terminology alignment (Creta Trading -> Thương đoàn Creta, Artifact -> Cổ vật, etc.).
4. Strict tag/token preservation verification (<size>, ==W==, ==PLAYER_NAME==, etc.).
"""

import re
from typing import Tuple, List

# 1. Exact phrase & idiom overrides
IDIOM_REPLACEMENTS = [
    # Creta Trading & scene 2 specific
    (r"Được rồi, đây là chỗ\. Cửa sau của Creta Trading ở ngay dưới kia\.", "Được rồi, tới nơi rồi. Cửa sau của Thương đoàn Creta nằm ngay phía dưới kia."),
    (r"Ặc, thật điên rồ! Chúng ta thậm chí còn không biết những con đường này\.\.\. Nhưng tôi đoán chúng ta không còn lựa chọn nào khác\.", "Trời ạ, điên thật đấy! Đường sá ở đây mình còn chưa thuộc nữa là... Nhưng giờ chắc hết cách rồi."),
    (r"Đợi đã\. Có một thang máy chở hàng lớn ở gần đây—nó có thể vừa với chuyến đi của cậu\.", "Khoan đã. Gần đây có cái thang máy chở hàng lớn đấy—chắc là nhét vừa cỗ xe của cậu."),
    (r"vừa với chuyến đi của (cậu|bạn|anh)", r"chứa vừa cỗ xe của \1"),
    (r"chuyến đi của (cậu|bạn|tôi)", r"cỗ xe của \1"),
    (r"cứu làn da của tôi", "cứu mạng tôi một phen"),
    (r"cứu làn da của (cậu|bạn|anh|em)", r"cứu mạng \1 một phen"),
    (r"Bạn đặt cược!", "Chuẩn luôn!"),
    (r"bạn đặt cược!", "chuẩn luôn!"),
    (r"đây là chỗ\.", "chính là chỗ này rồi."),
    (r"Được rồi, đây là chỗ\.", "Được rồi, tới nơi rồi."),
    (r"chạy lại các con số", "tính toán lại số liệu"),
    (r"\bCreta Trading\b", "Thương đoàn Creta"),
    (r"\bchơi trò giả vờ\b", "chơi trò đồ hàng"),
    (r"\bTôi sẽ thành thật\.", "Thật lòng mà nói thì..."),
    (r"\btôi sẽ thành thật\b", "thật lòng mà nói"),
    (r"\bngày trả lương\b", "khoản tiền thưởng béo bở"),
    (r"sẽ thật điên rồ khi bỏ đi", "có điên mới từ bỏ"),
    (r"\bthật điên rồ\b", "điên thật đấy"),
    (r"\bĐiều đó thật điên rồ\b", "Thật là quá quắt"),
    (r"\bĐiều đó thật điên rồ\.\.\.", "Thật là quá quắt..."),
    (r"\bkhông còn lựa chọn nào khác\b", "không còn cách nào khác"),
    (r"\btôi đoán chúng ta\b", "chắc là chúng mình"),
    (r"\btôi đoán tôi\b", "chắc là tôi"),
    (r"\bthậm chí còn không biết\b", "còn chẳng biết"),
    (r"\bthậm chí còn không\b", "còn chẳng"),
    (r"\bở ngay dưới kia\b", "ngay phía dưới kia"),
    (r"\bngười đàn ông đó\b", "gã đó"),
    (r"\bngười phụ nữ đó\b", "người phụ nữ ấy"),
    (r"\bđừng lo lắng về\b", "đừng bận tâm về"),
    (r"\bĐừng lo lắng về\b", "Đừng bận tâm về"),
    (r"\bLàm ơn hãy\b", "Xin hãy"),
    (r"\blàm ơn hãy\b", "hãy"),
    (r"\bchăm sóc cho tôi\b", "chăm sóc tôi"),
    (r"\bchăm sóc cho bạn\b", "chăm sóc cậu"),
    (r"\bchăm sóc cho cậu\b", "chăm sóc cậu"),
    (r"\bNice!\b", "Tuyệt vời!"),
    (r"\b! Đẹp!\b", "! Tuyệt quá!"),
    (r"\bĐẹp!\b", "Tuyệt vời!"),
    (r"\btbh\b", "thật lòng mà nói"),
    (r"\bbtw\b", "nhân tiện thì"),
    (r"\bidk\b", "tôi không biết"),
    (r"\bAutomatic Vending Artifact\b", "Cổ vật Bán hàng Tự động"),
    (r"\bPhoto Capturer\b", "Máy chụp ảnh"),
    (r"\bLucky Oasis\b", "Lucky Oasis"),
]

COMPILED_IDIOMS = [(re.compile(p, re.IGNORECASE if "\\" not in p else 0), r) for p, r in IDIOM_REPLACEMENTS]

def polish_sentence(en: str, vi: str) -> str:
    """Applies contextual translation polishing rules to a single sentence."""
    polished = vi

    # 1. Apply idiom replacements
    for pattern, replacement in COMPILED_IDIOMS:
        polished = pattern.sub(replacement, polished)

    # 2. Pronoun naturalization (Replace robotic 'Bạn/Tôi' when appropriate)
    # If sentence starts with 'Bạn ', soften to 'Cậu ' (avoiding friend as noun)
    if polished.startswith("Bạn ") and not (polished.startswith("Bạn bè") or polished.startswith("Bạn của") or polished.startswith("Bạn thân") or polished.startswith("Bạn tốt")):
        polished = "Cậu " + polished[4:]
    elif polished.startswith("bạn ") and not (polished.startswith("bạn bè") or polished.startswith("bạn thân") or polished.startswith("bạn tốt")):
        polished = "cậu " + polished[4:]

    # Replace 'của bạn' with 'của cậu' or 'của mình' (preserve noun phrases like 'bạn bè', 'bạn thân')
    polished = re.sub(r'\bcủa bạn\b(?!\s*(?:bè|thân|tốt))', 'của cậu', polished)
    polished = re.sub(r'\bvới bạn\b(?!\s*(?:bè|thân|tốt))', 'với cậu', polished)
    polished = re.sub(r'\bcho bạn\b(?!\s*(?:bè|thân|tốt))', 'cho cậu', polished)
    polished = re.sub(r'\bgặp bạn\b(?!\s*(?:bè|thân|tốt))', 'gặp cậu', polished)
    polished = re.sub(r'\bgọi bạn\b(?!\s*(?:bè|thân|tốt))', 'gọi cậu', polished)
    polished = re.sub(r'\bgiúp bạn\b(?!\s*(?:bè|thân|tốt))', 'giúp cậu', polished)
    polished = re.sub(r'\bvề bạn\b(?!\s*(?:bè|thân|tốt))', 'về cậu', polished)

    # 3. Tag casing normalization to match English canonical tokens
    tags_en = re.findall(r'<[^>]+>|==[a-zA-Z0-9_.-]+==|\{[0-9]+\}|_NOT_IN_LOG_', en)
    for tag in tags_en:
        polished = re.sub(re.escape(tag), tag, polished, flags=re.IGNORECASE)

    # 4. Clean trailing whitespace artifacts
    polished = polished.strip()

    return polished


def verify_tokens_preserved(en: str, vi: str, tokens: List[str]) -> Tuple[bool, List[str]]:
    """Ensures 100% of control tags from English are preserved in Vietnamese."""
    missing = []
    for token in tokens:
        if token not in vi:
            missing.append(token)
    return len(missing) == 0, missing
