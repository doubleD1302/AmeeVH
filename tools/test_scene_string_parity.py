# -*- coding: utf-8 -*-
import json
import sys
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
entries_dir = ROOT / "work/research/lua_full_unpacked/entries"

def get_strs(pr, acc):
    for ktype, val in pr['constants']:
        if ktype in (4, 20):
            try:
                s = val[1].decode('utf-8')
                if is_genuine_dialogue(s):
                    acc.append(s)
            except:
                pass
    for c in pr['protos']:
        get_strs(c, acc)

scenes = [
    'STev_02_07', 'STev_02_08', 'STev_02_09', 'STev_02_10', 'STev_02_11',
    'STev_03_01', 'STev_03_02', 'STev_03_03', 'STev_03_04', 'STev_03_05', 'STev_03_06', 'STev_03_07', 'STev_03_08', 'STev_03_09',
    'STev_04_01', 'STev_04_02', 'STev_04_03', 'STev_04_04', 'STev_04_05', 'STev_04_06', 'STev_04_07', 'STev_04_08', 'STev_04_09', 'STev_04_10'
]

all_match = True
for sc in scenes:
    fname = f"{sc}.lua"
    entry_info = mapping[fname]
    idx = entry_info['entry']['index']
    
    # Pristine EN
    payload_en = arc.extract_entry(arc.entries[idx], raw_pristine)
    proto_en = Lua53Chunk(xxtea_decrypt(payload_en, XXTEA_KEY)[34:]).parse_proto()
    strs_en = []
    get_strs(proto_en, strs_en)
    
    # Current VI
    entry_file = entries_dir / entry_info['filename']
    proto_vi = Lua53Chunk(xxtea_decrypt(entry_file.read_bytes(), XXTEA_KEY)[34:]).parse_proto()
    strs_vi = []
    get_strs(proto_vi, strs_vi)
    
    match = len(strs_en) == len(strs_vi)
    if not match:
        all_match = False
        print(f"MISMATCH in {sc}: EN={len(strs_en)} vs VI={len(strs_vi)}")
    else:
        print(f"{sc}: OK {len(strs_en)} strings")

print(f"All scenes string count matched: {all_match}")
