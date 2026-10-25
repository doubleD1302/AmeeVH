import sys
from pathlib import Path
ROOT = Path("StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))

from arcx_adapter import ArcxArchive, xxtea_decrypt, XXTEA_KEY
from test_lua_roundtrip import Lua53Chunk

arc = ArcxArchive(ROOT / "dist" / "lua_patched_vi.arcx")
entry = next(e for e in arc.entries if 'a35abefa7300be30' in e['hash_hex'])
raw_arc = (ROOT / "dist" / "lua_patched_vi.arcx").read_bytes()
payload = arc.extract_entry(entry, raw_arc)
decrypted = xxtea_decrypt(payload, XXTEA_KEY)

chunk = Lua53Chunk(decrypted)
hdr = chunk.read_bytes(33)
size_up = chunk.read_byte()
proto = chunk.parse_proto()

indices_to_check = [175, 191, 212, 224, 290, 321]
print("=== VERIFYING REPACKED STm02_04 CONSTANTS ===")
for idx in indices_to_check:
    ktype, val = proto["constants"][idx]
    s = val[1].decode("utf-8")
    print(f"Const {idx}: {s}")
