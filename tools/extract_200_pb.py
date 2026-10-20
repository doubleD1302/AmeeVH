import sys
from pathlib import Path
sys.path.insert(0, r'c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\tools')
from arcx_adapter import ArcxArchive, xxtea_decrypt

p = Path(r'C:\YostarGames\StellaSora_EN\Persistent_Store\Scripts\lua.arcx')
arc = ArcxArchive(p)

print(f"Total entries in 2.0.0 lua.arcx: {len(arc.entries)}")

found_pb = []
with open(p, 'rb') as f:
    raw_data = f.read()

for idx, entry in enumerate(arc.entries):
    data = arc.extract_entry(entry, raw_data)
    try:
        dec = xxtea_decrypt(data)
    except:
        dec = data
    if b'nova.client.' in dec or b'MallActType' in dec or b'AvgData' in dec or b'client_table' in dec:
        found_pb.append((idx, entry['hash_hex'], len(dec)))
        print(f"Entry {idx} ({entry['hash_hex']}): size {len(dec)}, matches proto strings!")
        out_p = Path(r'c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research') / f"200_proto_entry_{entry['hash_hex']}.bin"
        out_p.write_bytes(dec)

print(f"Total matching proto entries found: {len(found_pb)}")
