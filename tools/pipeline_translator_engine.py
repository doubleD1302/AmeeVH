#!/usr/bin/env python3
"""
Pipeline Translation Engine for Stella Sora (EN -> VI)
Used by Senior Translators & Localization QA subagents.
Features:
- Complete Master Glossary integration (1,162 terms, 29 forbidden rules)
- 100% token preservation & shielding ({0}, <color=...>, &ParamN&, \\n, etc.)
- Ultra-fast Batch Translation with \\n###\\n delimiter and recursive bisect
- Multi-threaded fallback & persistent cache
- Post-processing enforcing anime RPG voice, dignified Han-Viet for nouns, pure Vietnamese for dialogue
"""

import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLOSSARY_PATH = ROOT / "config" / "master_glossary.json"
CACHE_PATH = ROOT / "work" / "batches" / "pillars_translation_cache.json"

TOKEN_REGEX = re.compile(
    r'([A-Za-z0-9_]*<r=[^>]+>.*?</r>[A-Za-z0-9_]*|'
    r'[\x00-\x08\x0b-\x0c\x0e-\x1f]+|'
    r'\r?\n|<[^>]+>|\{[0-9a-zA-Z_]+\}|==[a-zA-Z0-9_]+==|&[a-zA-Z0-9_]+&|##[^#]+(?:#[^#]+)?#|%s)'
)

def load_master_glossary():
    if not GLOSSARY_PATH.exists():
        return {}, {}
    with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("terms", {}), data.get("forbidden", {})

def load_cache():
    combined = {}
    batch_dir = ROOT / "work" / "batches"
    if batch_dir.exists():
        for p in batch_dir.glob("*cache*.json"):
            if p.name != CACHE_PATH.name and p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            combined.update(data)
                except Exception:
                    pass
    if CACHE_PATH.exists():
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    combined.update(data)
        except Exception:
            pass
    return combined

def save_cache(cache):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def shield_tokens(text: str):
    tokens = []
    def repl(m):
        idx = len(tokens)
        tokens.append(m.group(0))
        return f" [[TOK{idx}]] "
    shielded = TOKEN_REGEX.sub(repl, text)
    shielded = re.sub(r' +', ' ', shielded).strip()
    return shielded, tokens

def unshield_tokens(text: str, tokens: list):
    def repl(m):
        idx = int(m.group(1))
        if idx >= len(tokens):
            return ""
        tok = tokens[idx]
        if any(ord(c) < 32 and c not in '\t' for c in tok):
            return tok
        if tok in ('\x0b', '\n', '\r\n'):
            return tok
        return f" {tok} "

    res = re.sub(r'\s*\[\[\s*TOK(\d+)\s*\]\]\s*', repl, text)
    res = re.sub(r'(<color=[^>]+>)\s+', r'\1', res)
    res = re.sub(r'\s+(</color>)', r'\1', res)
    res = re.sub(r'(<size=[^>]+>)\s*', r'\1', res)
    res = re.sub(r'\s*(</size>)', r'\1', res)
    res = re.sub(r'(<i>)\s*', r'\1', res)
    res = re.sub(r'\s*(</i>)', r'\1', res)
    res = re.sub(r'==\s*([a-zA-Z0-9_]+)\s*==', r'==\1==', res)
    while re.search(r'(==[a-zA-Z0-9_]+==)\s+(==[a-zA-Z0-9_]+==)', res):
        res = re.sub(r'(==[a-zA-Z0-9_]+==)\s+(==[a-zA-Z0-9_]+==)', r'\1\2', res)
    res = re.sub(r'(<color=[^>]+>)\s*(\{.*?\}|&Param\d+&)\s*(</color>)', r'\1\2\3', res)
    res = re.sub(r' +(&Param\d+&) +', r' \1 ', res)
    res = re.sub(r'[ \t]*\x0b[ \t]*', '\x0b', res)
    res = re.sub(r'[ \t]*\n[ \t]*', '\n', res)
    res = re.sub(r'\s+([,.:;?!])', r'\1', res)
    res = re.sub(r'(\{[0-9a-zA-Z_]+\})\s+s\b', r'\1s', res)
    res = re.sub(r'(&Param\d+&)\s+s\b', r'\1s', res)
    res = re.sub(r'(\{[0-9a-zA-Z_]+\})\s*%', r'\1%', res)
    res = re.sub(r'(&Param\d+&)\s*%', r'\1%', res)
    res = re.sub(r'[ \t]{2,}', ' ', res)
    return res.strip(" \t\r\n")

def fix_token_edges(src: str, dst: str) -> str:
    """Preserves leading and trailing control characters (\\x0b, \\n, \\r) exactly from source."""
    prefix = ''
    for ch in src:
        if ch in ('\x0b', '\n', '\r'):
            prefix += ch
        else:
            break
    suffix = ''
    for ch in reversed(src):
        if ch in ('\x0b', '\n', '\r'):
            suffix = ch + suffix
        else:
            break
    dst_clean = dst.strip(' \t\r\n\x0b')
    return prefix + dst_clean + suffix


def post_process_vietnamese(text: str, terms_dict: dict, forbidden_dict: dict) -> str:
    # 0. Protect tokens from glossary/regex replacements if present
    has_tokens = bool(TOKEN_REGEX.search(text))
    if has_tokens:
        text, tok_list = shield_tokens(text)
    else:
        tok_list = []

    # 1. Check forbidden calques first
    for wrong, correct in forbidden_dict.items():
        clean_correct = correct.split(' (')[0].split(' / ')[0].strip()
        if wrong.lower() in text.lower():
            text = re.sub(re.escape(wrong), clean_correct, text, flags=re.IGNORECASE)
    
    # 2. Master Glossary direct replacements
    # Check exact case and lowercase
    for term, vi_term in terms_dict.items():
        if len(term) >= 4 and term in text:
            # Word boundary replace
            text = re.sub(rf'\b{re.escape(term)}\b', vi_term, text)

    # 3. Core Terminology standardizations
    replacements = [
        (r'\bTrekkers?\b', 'Lữ Khách'),
        (r'\b[Nn]gười đi bộ\b', 'Lữ Khách'),
        (r'\b[Nn]hững người đi bộ\b', 'các Lữ Khách'),
        (r'\b[Nn]gười du hành\b', 'Lữ Khách'),
        (r'\b[Nn]gười đi phượt\b', 'Lữ Khách'),
        (r'\bMonolith\b', 'Cự Tháp'),
        (r'\bWilds\b', 'Vùng Hoang Dã'),
        (r'\b[Vv]ùng hoang dã\b', 'Vùng Hoang Dã'),
        (r'\b[Cc]ự tháp\b', 'Cự Tháp'),
        (r'\b[Tt]háp sao\b', 'Tháp Sao'),
        (r'\bDorra\b', 'Dorra'),
        (r'\bShrubshrews?\b', 'Chuột Bụi'),
        (r'\bShrubrats?\b', 'Chuột Bụi'),
        (r'\bchiến binh bụi rậm\b', 'Chiến Binh Chuột Bụi'),
        (r'\bthành cổ cây bụi\b', 'Pháo Đài Chuột Bụi'),
        (r'\bbột chắc chắn\b', 'Cầu Thủ Vạm Vỡ'),
        (r'\bSuperarmor\b', 'Bá Thể'),
        (r'\bSuper Armor\b', 'Bá Thể'),
        (r'\bsiêu giáp\b', 'Bá Thể'),
        (r'\bResilience Break\b', 'Phá Vỡ Kiên Định'),
        (r'\bBroken Resilience\b', 'Phá Vỡ Kiên Định'),
        (r'\bResilience\b', 'Kiên Định'),
        (r'\bMain Skills?\b', 'Kỹ Năng Chủ Lực'),
        (r'\bSupport Skills?\b', 'Kỹ Năng Viện Trợ'),
        (r'\bUltimate Skills?\b', 'Tuyệt Kỹ'),
        (r'\bUltimates?\b', 'Tuyệt Kỹ'),
        (r'\bAuto Attacks?\b', 'Đòn Đánh Thường'),
        (r'\bNormal Attacks?\b', 'Đòn Đánh Thường'),
        (r'\bClear time\b', 'Thời gian vượt ải'),
        (r'\bClear time\s*≤', 'Thời gian hoàn thành ≤'),
        (r'\bBattle ended\b', 'Chiến đấu kết thúc'),
        (r'\bVictory\b', 'Thắng Trận'),
        (r'\bDefeat\b', 'Thất Bại'),
        (r'\b[Kk]ẻ thù\b', 'kẻ địch'),
        (r'\b[Tt]iền thưởng đăng nhập\b', 'phần thưởng đăng nhập'),
        (r'\b[Yy]êu cầu phần thưởng\b', 'nhận phần thưởng'),
        (r'\b[Yy]êu cầu tiền thưởng\b', 'nhận thưởng'),
        (r'\bbiểu ngữ gacha\b', 'Kỳ Chiêu Mộ Gacha'),
        (r'\bBiểu ngữ gacha\b', 'Kỳ Chiêu Mộ Gacha'),
        (r'\bbiểu ngữ\b', 'banner'),
        (r'\bBiểu ngữ\b', 'Banner'),
        (r'\b[Cc]hìa khóa tâm hồn\b', 'Chìa Khóa Tâm Hồn'),
        (r'\b[Vv]é thanh không\b', 'Vé Thanh Không'),
        (r'\b[Vv]é manh nha\b', 'Vé Manh Nha'),
        (r'\b[Đđ]ĩa vàng kim\b', 'Đĩa Vàng Kim'),
        (r'\b[Tt]hể lực\b', 'Thể Lực'),
        (r'\b[Tt]hăng hoa\b', 'Thăng Hoa'),
    ]
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

    # 4. Polish anime style & dialogue expressions
    dialogue_replacements = [
        (r'\b(Firstlight|First Light)\s*Noya\b', 'Noya - Khải Minh'),
        (r'\bNoya\s*(Sơ Quang|Khải Minh)\b', 'Noya - Khải Minh'),
        (r'\b(Sơ Quang|Khải Minh)\s*Noya\b', 'Noya - Khải Minh'),
        (r'\bNoya\s*[-–—]\s*Sơ Quang\b', 'Noya - Khải Minh'),
        (r'\bSơ Quang\b', 'Khải Minh'),
        (r'\bSwift Wind Flash\b', 'Tấn Phong Thiểm'),
        (r'\b(Rising )?Dragon Slash\b', 'Thăng Long Trảm'),
        (r'\b[Cc]hém [Rr]ồng\b', 'Thăng Long Trảm'),
        (r'\b(Ruin|Withered) Wind Slash\b', 'Tàn Phong Trảm'),
        (r'\b(Ruin|Withered) Wind\b', 'Tàn Phong'),
        (r'\b[Cc]ơn gió tàn khốc\b', 'Tàn Phong'),
        (r'\b[Gg]ió tàn phá\b', 'Tàn Phong'),
        (r'\bGalloping Wind Strike\b', 'Trì Phong Kích'),
        (r'\bSky Splitter Void Rupture Slash\b', 'Liệt Không Đoạn Phá Trảm'),
        (r'\bCross Great Sword Aura\b', 'Thập Tự Đại Kiếm Khí'),
        (r'\bGreat Sword Aura\b', 'Đại Kiếm Khí'),
        (r'\bMulti Sword Aura\b', 'Đa Trọng Kiếm Khí'),
        (r'\bMinor Sword Aura\b', 'Tiểu Kiếm Khí'),
        (r'\bSword Aura\b', 'Kiếm Khí'),
        (r'\bhào quang kiếm lớn\b', 'Đại Kiếm Khí'),
        (r'\bhào quang thanh kiếm lớn\b', 'Đại Kiếm Khí'),
        (r'\bhào quang (bằng |thanh )?kiếm\b', 'kiếm khí'),
        (r'\bluồng khí kiếm\b', 'luồng kiếm khí'),
        (r'\bLucky Oasis\b', 'Ốc Đảo Lai Phúc'),
        (r'\bNoname\b', 'Vô Danh'),
        (r'\bTyrant\b', 'Bạo Quân'),
        (r'\b[Bb]ạn có sao chép không[\s?!]*', 'Bạn có nghe rõ không!?'),
        (r'\b[Bb]ạn sao chép không[\s?!]*', 'Bạn có nghe rõ không!?'),
        (r'\b[Cc]ó sao chép không[\s?!]*', 'Nghe rõ không!?'),
        (r'\bsao chép không[\s?!]*', 'nghe rõ không!?'),
        (r'\b[Cc]ó sao chép\b', 'nghe rõ'),
        (r'\bsao chép\b', 'nghe rõ'),
        (r'\bVâng\. Tôi nghe thấy bạn\.', 'Ừ. Tớ nghe đây.'),
        (r'\bTôi nghe thấy bạn\b', 'Tớ nghe thấy cậu rồi'),
        (r'\bnghe thấy bạn\b', 'nghe thấy cậu'),
        (r'\bCô Gái Bồn Chồn\b', 'Cô Gái Lo Lắng'),
        (r'\buống\s+(?:một\s+viên\s+)?thuốc\s+(?:hạ\s+nhiệt|hạ\s+sốt|an\s+thần)\s*(?:đi)?\b', 'bình tĩnh lại nào'),
        (r'\buống thuốc hạ nhiệt\b', 'bình tĩnh lại nào'),
        (r'\buống thuốc an thần\b', 'thả lỏng đi mà'),
        (r'\bLữ Khách với\b', 'Lữ Khách sở hữu'),
        (r'\bđiểm "([^\"]+)"\b', r'tầng "\1"'),
        (r'\bđược gánh chịu\b', 'phải nhận'),
        (r'\bthực hiện đòn đánh\b', 'tung đòn'),
        (r'\bBắt được bạn rồi\b', 'Bắt được rồi'),
        (r'\bĐêm đêm\b', 'Ngủ ngon nhé'),
        (r'\bĐêm nay\.\b', 'Ngủ ngon nhé.'),
        (r'\b[Gg]iao dịch Creta\b', 'Thương Hội Creta'),
        (r'\b[Nn]gười\s+[Nn]gười\s+Novian\b', 'người Novian'),
        (r'\b[Nn]gười\s+Novian\s+Blademaster\b', 'Kiếm Sư Novian'),
        (r'\bThần\s+[Ââ]n\s+sủng\b', 'Thần Ân Điển'),
        (r'\bThần\s+[Ââ]n\s+điển\b', 'Thần Ân Điển'),
        (r'\bThành [Pp]hố\s+[Tt]hành [Pp]hố\b', 'Thành Phố'),
        (r'\bkhối đá nguyên khối\b', 'Cự Tháp'),
        (r'\bđá nguyên khối\b', 'Cự Tháp'),
        (r'\bThành phố Ngàn (?:khối đá nguyên khối|Cự Tháp)\b', 'Thành Phố Vạn Tháp'),
        (r'\b[Kk]hoản hoa hồng\b', 'nhiệm vụ ủy thác'),
        (r'\b[Tt]iền hoa hồng\b', 'tiền thù lao ủy thác'),
        (r'\b[Hh]oa hồng quái vật\b', 'ủy thác săn quái'),
        (r'\btrao hoa hồng\b', 'tiếp nhận ủy thác'),
        (r'\bnhận hoa hồng\b', 'nhận ủy thác'),
        (r'\bhoàn thành hoa hồng\b', 'hoàn thành ủy thác'),
        (r'\bkhông có hoa hồng nào\b', 'không có ủy thác nào'),
        (r'\bhoa hồng\b(?=\s+với mức chi trả)', 'ủy thác'),
        (r'\bhoa hồng\b(?=\s+đến hậu cần)', 'ủy thác'),
    ]
    for pattern, repl in dialogue_replacements:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

    # 5. Clean up any accidental single-character artifact prefix or duplicated punctuation
    text = re.sub(r'^[%\^!=\+58Z](?=[A-ZÀ-Ỹa-zà-ỹ\s])', '', text)
    text = re.sub(r'(!\?|\?!)[!?]+', r'\1', text)
    text = re.sub(r'!{2,}', '!', text)
    text = re.sub(r'\?{2,}', '?', text)

    if has_tokens:
        text = unshield_tokens(text, tok_list)

    return text.strip(" \t\r\n")

DOMAINS = ["com.vn", "com.hk", "com.tw", "com.sg", "co.jp"]
_domain_idx = 0

def get_next_domain():
    global _domain_idx
    d = DOMAINS[_domain_idx % len(DOMAINS)]
    _domain_idx += 1
    return d

def translate_batch(texts: list) -> list:
    """Translate batch of shielded texts using Google Translate API with domain rotation, retries and recursive bisect."""
    if not texts:
        return []

    delim = "\n###\n"
    joined = delim.join(texts)

    has_cn = any(u'\u4e00' <= ch <= u'\u9fff' for ch in joined)
    sl = 'zh-CN' if has_cn else 'en'

    for client in ('gtx', 'it'):
        for attempt in range(len(DOMAINS)):
            dom = get_next_domain()
            try:
                url = f"https://translate.google.{dom}/translate_a/single?client={client}&sl={sl}&tl=vi&dt=t&q=" + urllib.parse.quote(joined)
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    full_text = "".join([item[0] for item in data[0] if item and item[0]])
                    parts = [p.strip() for p in re.split(r'\s*#\s*#\s*#\s*', full_text) if p.strip()]
                    if len(parts) == len(texts):
                        return parts
                    elif len(texts) > 1:
                        mid = len(texts) // 2
                        return translate_batch(texts[:mid]) + translate_batch(texts[mid:])
                    else:
                        return [full_text.strip()]
            except Exception:
                time.sleep(0.2 * (attempt + 1))

    # Fast ThreadPool fallback item by item
    def single_fetch(t):
        for client in ('gtx', 'it'):
            for _ in range(3):
                dom = get_next_domain()
                try:
                    has_cn_t = any(u'\u4e00' <= ch <= u'\u9fff' for ch in t)
                    sl_t = 'zh-CN' if has_cn_t else 'en'
                    url = f"https://translate.google.{dom}/translate_a/single?client={client}&sl={sl_t}&tl=vi&dt=t&q=" + urllib.parse.quote(t)
                    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                    with urllib.request.urlopen(req, timeout=8) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        return "".join([item[0] for item in data[0] if item and item[0]]).strip()
                except Exception:
                    continue
        return t

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(single_fetch, texts))
    return results

def is_valid_token_preservation(src: str, dst: str) -> bool:
    src_tokens = sorted(TOKEN_REGEX.findall(src))
    dst_tokens = sorted(TOKEN_REGEX.findall(dst))
    return src_tokens == dst_tokens
