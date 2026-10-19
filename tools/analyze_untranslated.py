import json
from collections import Counter

en = json.load(open('work/research/data_decrypted/entries/00704_0x87cc29ac0defc2d9.bin', encoding='utf-8'))
cn = json.load(open('work/research/data_decrypted/entries/00925_0x363690c09b175230.bin', encoding='utf-8'))

vn_chars = 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'
untranslated = {k: en[k] for k in en if not any(c in en[k] for c in vn_chars)}
print(f'Total untranslated in UIText: {len(untranslated)}')

# Categorize by prefix
prefixes = Counter(k.split('.')[1].split('_')[0] for k in untranslated.keys())
print('Top untranslated categories:')
for p, count in prefixes.most_common(25):
    print(f'  {p:20s}: {count:4d}')
