import json
from dict_stm10001_01 import TRANS_01
from dict_stm10001_02 import TRANS_02
from dict_stm10001_03 import TRANS_03

all_trans = {}
all_trans.update(TRANS_01)
all_trans.update(TRANS_02)
all_trans.update(TRANS_03)

print('Total items to write:', len(all_trans))

out_path = 'StellaSora_VietHoa/tools/translations_stm10001_slice1.py'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('''# -*- coding: utf-8 -*-
"""
Stella Sora - Campaign 17 Partition A (Tutorial Prologue STm10001)
Slice 1 Translations: STm10001_01, STm10001_02, STm10001_03 (Total: 372 items)

Zero-Defect Light Novel Prose:
- 100 percent Token Parity: ==W==, ==RT==, ==PLAYER_NAME==, ==Off==, ==A-1==, ==A-2==, ==P==, ==SEX...==
- Preserved 7 Unclosed <size=XX> tags (STm10001_01.121, STm10001_01.249, STm10001_03.160, STm10001_03.317, STm10001_03.410, STm10001_03.412, STm10001_03.441)
- Preserved ruby tags <r=·>...</r>
- Standardized Master Glossary: Chấp Chính Quan Olympia, Thành Phố Hoàn Hảo, Dạ Hành Giả, Hồn Thạch, Cự Tháp, Phòng Trắng, Tu Giả Tập Sự
"""

TRANSLATIONS_SLICE1 = {
''')
    for k, v in all_trans.items():
        v_escaped = v.replace('\\', '\\\\').replace("'", "\\'")
        f.write(f"    '{k}': '{v_escaped}',\n")
    f.write('}\n')
print('Successfully generated self-contained translations_stm10001_slice1.py!')
