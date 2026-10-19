import json

en = json.load(open('work/research/data_decrypted/entries/00704_0x87cc29ac0defc2d9.bin', encoding='utf-8'))
cn = json.load(open('work/research/data_decrypted/entries/00925_0x363690c09b175230.bin', encoding='utf-8'))

vn_chars = 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'
untranslated = {k: en[k] for k in en if not any(c in en[k] for c in vn_chars)}

for cat in ['Settings', 'Equipment', 'Disc', 'Potential', 'CharTalent', 'Energy', 'Shop']:
    items = {k: untranslated[k] for k in untranslated if k.split('.')[1].startswith(cat)}
    print(f'=== {cat} ({len(items)}) ===')
    for k, v in list(items.items())[:8]:
        print(f'  {k} -> EN: {v} | CN: {cn.get(k)}')
