# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))

from arcx_adapter import ArcxArchive, xxtea_decrypt, XXTEA_KEY
from test_lua_roundtrip import Lua53Chunk
from translate_remaining_lua_avg import is_genuine_dialogue

mapping = json.load(open(ROOT / "work/research/avg_file_to_entry.json", encoding="utf-8"))
pristine_arcx = ROOT / "work/research/test_lua_full.arcx"
arc = ArcxArchive(pristine_arcx)
raw_pristine = pristine_arcx.read_bytes()

def get_dialogue(proto):
    res = []
    for ktype, val in proto['constants']:
        if ktype in (4, 20):
            try:
                s = val[1].decode('utf-8')
                if is_genuine_dialogue(s):
                    res.append(s)
            except:
                pass
    for c in proto['protos']:
        res.extend(get_dialogue(c))
    return res

for sc in ['STev_09_01', 'STev_10_01', 'STev_11_01', 'STev_12_01']:
    fname = f"{sc}.lua"
    entry_info = mapping[fname]
    idx = entry_info['entry']['index']
    payload = arc.extract_entry(arc.entries[idx], raw_pristine)
    proto = Lua53Chunk(xxtea_decrypt(payload, XXTEA_KEY)[34:]).parse_proto()
    lines = get_dialogue(proto)
    print(f"=== {sc} ===")
    for l in lines[:5]:
        print(" ", repr(l[:70]))
