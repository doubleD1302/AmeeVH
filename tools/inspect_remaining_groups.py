# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))
from test_lua_roundtrip import Lua53Chunk
from arcx_adapter import xxtea_decrypt, XXTEA_KEY

mapping = json.load(open(ROOT / "work/research/avg_file_to_entry.json", encoding="utf-8"))
entries_dir = ROOT / "work/research/lua_full_unpacked/entries"

def extract_strings(proto, acc):
    for ktype, val in proto['constants']:
        if ktype in (4, 20):
            tag, s_bytes = val
            try:
                s = s_bytes.decode('utf-8')
                if len(s.strip()) > 0:
                    acc.append(s)
            except:
                pass
    for child in proto['protos']:
        extract_strings(child, acc)

target_groups = {
    'DP': [f for f in mapping if f.startswith('DP_')],
    'STev_02': [f for f in mapping if f.startswith('STev_02_')],
    'STev_03': [f for f in mapping if f.startswith('STev_03_')],
    'STev_04': [f for f in mapping if f.startswith('STev_04_')],
    'STev_05': [f for f in mapping if f.startswith('STev_05_')],
    'STev_07': [f for f in mapping if f.startswith('STev_07_')],
    'STev_08': [f for f in mapping if f.startswith('STev_08_')],
    'STev_09': [f for f in mapping if f.startswith('STev_09_')],
    'STev_10': [f for f in mapping if f.startswith('STev_10_')],
    'STev_11': [f for f in mapping if f.startswith('STev_11_')],
    'STev_12': [f for f in mapping if f.startswith('STev_12_')],
    'STm10001': [f for f in mapping if f.startswith('STm10001_')],
    'BBm': [f for f in mapping if f.startswith('BBm')],
    'CG_149_162': [f for f in mapping if f.startswith(('CG_149', 'CG_155', 'CG_156', 'CG_157', 'CG_158', 'CG_159', 'CG_160', 'CG_162'))],
    'CG_disc': [f for f in mapping if f.startswith('CG_disc')],
    'CG_npc': [f for f in mapping if f.startswith('CG_npc')],
}

for grp, files in target_groups.items():
    total_strs = 0
    file_stats = []
    for f in sorted(files):
        entry_info = mapping[f]
        entry_fname = entry_info['filename']
        entry_file = entries_dir / entry_fname
        if not entry_file.exists():
            continue
        raw_enc = entry_file.read_bytes()
        raw_dec = xxtea_decrypt(raw_enc, XXTEA_KEY)
        chunk = Lua53Chunk(raw_dec)
        chunk.read_bytes(34)
        proto = chunk.parse_proto()
        acc = []
        extract_strings(proto, acc)
        total_strs += len(acc)
        file_stats.append((f, len(acc)))
    print(f"Group {grp:12s}: {len(files):2d} files, total strings = {total_strs:5d}")
