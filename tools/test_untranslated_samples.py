import json

cn = json.load(open('work/research/data_decrypted/entries/00925_0x363690c09b175230.bin', encoding='utf-8'))
en = json.load(open('work/research/data_decrypted/entries/00704_0x87cc29ac0defc2d9.bin', encoding='utf-8'))

vn_chars = 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'
untranslated = [(k, en[k], cn.get(k, '')) for k in en if not any(c in en[k] for c in vn_chars)]

print(f'Total untranslated: {len(untranslated)}')
print('Sample 15 untranslated:')
for k, e, c in untranslated[50:65]:
    print(f'KEY: {k}\n  EN: {e}\n  CN: {c}')
