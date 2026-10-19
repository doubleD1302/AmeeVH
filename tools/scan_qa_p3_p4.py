import json
import re
from pathlib import Path

ROOT = Path('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa')
p3_src = json.load(open(ROOT / 'work/batches/pillar3_story_dating_quests.json', encoding='utf-8'))
p4_src = json.load(open(ROOT / 'work/batches/pillar4_system_gacha_shops.json', encoding='utf-8'))

p3_tr = json.load(open(ROOT / 'work/batches/pillar3_translated.json', encoding='utf-8'))
p4_tr = json.load(open(ROOT / 'work/batches/pillar4_translated.json', encoding='utf-8'))

glossary = json.load(open(ROOT / 'config/master_glossary.json', encoding='utf-8'))
terms = glossary.get('terms', {})
forbidden = glossary.get('forbidden_calques', {})

TOKEN_RE = re.compile(r'(\{[0-9]+\}|&[A-Za-z0-9_]+&|<color=#[0-9a-fA-F]{6}>|</color>|<[^>]+>|\\n|%[sd])')

def check_pillar(name, src_data, tr_data):
    print(f"=== Scanning {name} ===")
    total = 0
    untrans = []
    token_errors = []
    forbidden_matches = []
    
    for tbl, info in tr_data.items():
        src_tbl = src_data.get(tbl, {}).get('entries', {})
        for k, vi in info.get('entries', {}).items():
            total += 1
            en = src_tbl.get(k, '')
            
            # Check untranslated
            # Check if vi == en and en has english letters
            if vi == en and re.search(r'[a-zA-Z]{3,}', en):
                # Check if it's not a proper name or code
                untrans.append((tbl, k, en))
                
            # Check tokens
            en_tokens = TOKEN_RE.findall(en)
            vi_tokens = TOKEN_RE.findall(vi)
            
            # Check counts of each token type
            en_counts = {}
            for t in en_tokens:
                en_counts[t] = en_counts.get(t, 0) + 1
            vi_counts = {}
            for t in vi_tokens:
                vi_counts[t] = vi_counts.get(t, 0) + 1
                
            # If color tags mismatch
            en_open = len(re.findall(r'<color=#[0-9a-fA-F]{6}>', en))
            en_close = len(re.findall(r'</color>', en))
            vi_open = len(re.findall(r'<color=#[0-9a-fA-F]{6}>', vi))
            vi_close = len(re.findall(r'</color>', vi))
            
            if (vi_open != vi_close) or (en_open != vi_open) or (en_close != vi_close):
                token_errors.append((tbl, k, 'color_tag_mismatch', en, vi))
                
            # Check param tokens {0}, {1}...
            en_params = re.findall(r'\{[0-9]+\}', en)
            vi_params = re.findall(r'\{[0-9]+\}', vi)
            if sorted(en_params) != sorted(vi_params):
                token_errors.append((tbl, k, 'param_mismatch', en, vi))
                
            # Check &ParamN&
            en_and = re.findall(r'&[A-Za-z0-9_]+&', en)
            vi_and = re.findall(r'&[A-Za-z0-9_]+&', vi)
            if sorted(en_and) != sorted(vi_and):
                token_errors.append((tbl, k, 'and_param_mismatch', en, vi))
                
            # Check forbidden calques
            for wrong, correct in forbidden.items():
                if wrong.lower() in vi.lower():
                    # If wrong is a short word like 'với', check word boundaries
                    pat = r'\b' + re.escape(wrong) + r'\b'
                    if re.search(pat, vi, re.IGNORECASE):
                        forbidden_matches.append((tbl, k, wrong, correct, vi))

    print(f"Total: {total}")
    print(f"Untranslated strings: {len(untrans)}")
    for t, k, s in untrans[:10]:
        print(f"  [Untrans] {t}.{k}: {s}")
    print(f"Token errors: {len(token_errors)}")
    for t, k, err, en, vi in token_errors[:10]:
        print(f"  [Token {err}] {t}.{k}: EN='{en}' -> VI='{vi}'")
    print(f"Forbidden calques matches: {len(forbidden_matches)}")
    for t, k, w, c, vi in forbidden_matches[:10]:
        print(f"  [Forbidden: '{w}' -> '{c}'] {t}.{k}: {vi[:80]}")

check_pillar("Pillar 3", p3_src, p3_tr)
print()
check_pillar("Pillar 4", p4_src, p4_tr)
