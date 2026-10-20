import json
import re

with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA.json', 'r', encoding='utf-8') as f:
    src = json.load(f)
with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA_translated.json', 'r', encoding='utf-8') as f:
    dst = json.load(f)

# Allowed proper nouns and tokens
allowed = {
    'philae', 'darcia', 'firenze', 'nyx', 'noya', 'fuyuka', 'amber', 'iris',
    'mistique', 'joseph', 'samuel', 'nanoha', 'hazana', 'albedo', 'dorra',
    'omor', 'emor', 'orelia', 'orelian', 'creta', 'nova', 'novia', 'novian',
    'heartlink', 'accord', 'select', 'premium', 'throne', 'oracle',
    'king', 'bishop', 'rook', 'knight', 'pawn', 'queen', 'color', 'size',
    'player_name', 'sex1', 'sex2', 'sex3', 'sex4', 'sex5', 'sex6', 'sex7',
    'sex8', 'sex9', 'sex10', 'sex11', 'sex12', 'sex13', 'sex14', 'sex15',
    'sex16', 'sex17', 'sex18', 'rt', 'w', 'b', 'i', 'r', 'tetrad',
    'messis', 'venatio', 'chao'
}

english_words = {}
for k, v in dst.items():
    orig = src.get(k, '')
    # Skip engine identifiers / opcodes
    if any(ord(c) < 32 and c not in '\n\r\t\x0b' for c in orig):
        continue
    # Strip HTML / engine tags
    clean_v = re.sub(r'<[^>]+>', ' ', v)
    clean_v = re.sub(r'==[A-Z0-9_]+==', ' ', clean_v)
    clean_v = re.sub(r'&[A-Za-z0-9_]+&', ' ', clean_v)
    
    words = re.findall(r'\b[A-Za-z]{3,}\b', clean_v)
    for w in words:
        wl = w.lower()
        if wl not in allowed:
            english_words.setdefault(w, []).append((k, orig, v))

print(f"Total distinct unexpected English words found: {len(english_words)}")
for w, occurrences in sorted(english_words.items(), key=lambda x: -len(x[1]))[:30]:
    print(f"Word: '{w}' ({len(occurrences)} times) e.g. {occurrences[0][0]}")
    print(f"   SRC: {occurrences[0][1]}")
    print(f"   DST: {occurrences[0][2]}")
