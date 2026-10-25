# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))
from test_lua_roundtrip import Lua53Chunk
from arcx_adapter import xxtea_decrypt, XXTEA_KEY
from translate_remaining_lua_avg import is_genuine_dialogue

mapping = json.load(open(ROOT / "work/research/avg_file_to_entry.json", encoding="utf-8"))
entries_dir = ROOT / "work/research/lua_full_unpacked/entries"
rem_cache = json.load(open(ROOT / "work/batches/remaining_lua_avg_cache.json", encoding="utf-8"))

def extract_dialogue(proto, acc):
    for ktype, val in proto['constants']:
        if ktype in (4, 20):
            tag, s_bytes = val
            try:
                s = s_bytes.decode('utf-8')
                if is_genuine_dialogue(s):
                    acc.append(s)
            except:
                pass
    for child in proto['protos']:
        extract_dialogue(child, acc)

scenes_to_check = [
    'STev_02_07', 'STev_02_08', 'STev_02_09', 'STev_02_10', 'STev_02_11',
    'STev_03_01', 'STev_03_02', 'STev_03_03', 'STev_03_04', 'STev_03_05', 'STev_03_06', 'STev_03_07', 'STev_03_08', 'STev_03_09',
    'STev_04_01', 'STev_04_02', 'STev_04_03', 'STev_04_04', 'STev_04_05', 'STev_04_06', 'STev_04_07', 'STev_04_08', 'STev_04_09', 'STev_04_10'
]

total_dialogue = 0
for sc in scenes_to_check:
    fname = f"{sc}.lua"
    if fname not in mapping:
        print(f"Warning: {fname} not in mapping")
        continue
    entry_info = mapping[fname]
    entry_file = entries_dir / entry_info['filename']
    raw_enc = entry_file.read_bytes()
    raw_dec = xxtea_decrypt(raw_enc, XXTEA_KEY)
    chunk = Lua53Chunk(raw_dec)
    chunk.read_bytes(34)
    proto = chunk.parse_proto()
    acc = []
    extract_dialogue(proto, acc)
    # Deduplicate in order if needed or keep sequence
    total_dialogue += len(acc)
    print(f"{sc}: {len(acc)} dialogue lines")

print(f"Total dialogue across these scenes: {total_dialogue}")
