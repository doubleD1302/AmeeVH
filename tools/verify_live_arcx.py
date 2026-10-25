import sys
from pathlib import Path
ROOT = Path("StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))

from arcx_adapter import ArcxArchive, xxtea_decrypt, XXTEA_KEY
from test_lua_roundtrip import Lua53Chunk

live_paths = [
    Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Scripts\lua.arcx"),
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Scripts\lua.arcx")
]

for lp in live_paths:
    if not lp.exists():
        print(f"Skipping non-existent: {lp}")
        continue
    arc = ArcxArchive(lp)
    entry = next(e for e in arc.entries if 'a35abefa7300be30' in e['hash_hex'])
    raw_arc = lp.read_bytes()
    payload = arc.extract_entry(entry, raw_arc)
    decrypted = xxtea_decrypt(payload, XXTEA_KEY)

    chunk = Lua53Chunk(decrypted)
    hdr = chunk.read_bytes(33)
    size_up = chunk.read_byte()
    proto = chunk.parse_proto()

    print(f"=== CHECKING {lp.name} at {lp.parent} ===")
    print("Const 175:", proto["constants"][175][1][1].decode("utf-8"))
    print("Const 212:", proto["constants"][212][1][1].decode("utf-8"))
    print("Const 224:", proto["constants"][224][1][1].decode("utf-8"))
