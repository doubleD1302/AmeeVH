# -*- coding: utf-8 -*-
import json

cache = json.load(open('StellaSora_VietHoa/work/batches/remaining_lua_avg_cache.json', encoding='utf-8'))
print('Cache size:', len(cache))

bad_calques = {
    'xấu hổ': [],
    'trò đùa': [],
    'tiếp cận tôi': [],
    'người liên hệ': [],
    'người hướng dẫn': [],
    'thực hiện vài nghiên cứu': [],
    'có phải vậy không': []
}

for k, v in cache.items():
    for b in bad_calques:
        if b in v.lower():
            bad_calques[b].append((k, v))

for b, lst in bad_calques.items():
    print(f'Calque [{b}]: {len(lst)} matches')
    for k, v in lst[:3]:
        print(f'   "{k}" -> "{v}"')
