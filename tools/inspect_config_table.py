with open(r'c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\lua_tree\GameCore\Data\LuaDataTable.lua', 'rb') as f:
    data = f.read()

import re
strs = re.findall(rb'[\x20-\x7e]{4,}', data)
for s in strs:
    print(s.decode('latin1'))
