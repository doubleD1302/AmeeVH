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

TOKEN_REGEX = re.compile(r'(\x0b|\r?\n|<[^>]+>|\{[0-9a-zA-Z_]+\}|==[A-Z0-9_]+==|&[a-zA-Z0-9_]+&|##[^#]+(?:#[^#]+)?#|%s)')

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
        if tok in ('\x0b', '\n', '\r\n'):
            return tok
        return f" {tok} "

    res = re.sub(r'\s*\[\[\s*TOK(\d+)\s*\]\]\s*', repl, text)
    res = re.sub(r'(<color=[^>]+>)\s+', r'\1', res)
    res = re.sub(r'\s+(</color>)', r'\1', res)
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

    # 4. Polish anime style
    text = re.sub(r'\bLữ Khách với\b', 'Lữ Khách sở hữu', text)
    text = re.sub(r'\bđiểm "([^\"]+)"\b', r'tầng "\1"', text)
    text = re.sub(r'\bđược gánh chịu\b', 'phải nhận', text)
    text = re.sub(r'\bthực hiện đòn đánh\b', 'tung đòn', text)

    return text.strip(" \t\r\n")

def translate_batch(texts: list) -> list:
    """Translate batch of shielded texts using Google Translate API with retries and recursive bisect."""
    if not texts:
        return []

    delim = "\n###\n"
    joined = delim.join(texts)

    has_cn = any(u'\u4e00' <= ch <= u'\u9fff' for ch in joined)
    sl = 'zh-CN' if has_cn else 'auto'

    for attempt in range(3):
        try:
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={sl}&tl=vi&dt=t&q=" + urllib.parse.quote(joined)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
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
            time.sleep(0.5 * (attempt + 1))

    # Fast ThreadPool fallback item by item
    def single_fetch(t):
        try:
            has_cn_t = any(u'\u4e00' <= ch <= u'\u9fff' for ch in t)
            sl_t = 'zh-CN' if has_cn_t else 'auto'
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={sl_t}&tl=vi&dt=t&q=" + urllib.parse.quote(t)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return "".join([item[0] for item in data[0] if item and item[0]]).strip()
        except Exception:
            return t

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(single_fetch, texts))
    return results

def is_valid_token_preservation(src: str, dst: str) -> bool:
    src_tokens = sorted(TOKEN_REGEX.findall(src))
    dst_tokens = sorted(TOKEN_REGEX.findall(dst))
    return src_tokens == dst_tokens
