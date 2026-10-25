import sys
from pathlib import Path
ROOT = Path("StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))

from arcx_adapter import ArcxArchive, xxtea_decrypt, XXTEA_KEY
from test_lua_roundtrip import Lua53Chunk

target_paths = [
    ROOT / "dist" / "lua_patched_vi.arcx",
    Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Scripts\lua.arcx"),
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Scripts\lua.arcx")
]

for arc_path in target_paths:
    if not arc_path.exists():
        continue
    arc = ArcxArchive(arc_path)
    entry = next(e for e in arc.entries if 'a35abefa7300be30' in e['hash_hex'])
    raw_arc = arc_path.read_bytes()
    payload = arc.extract_entry(entry, raw_arc)
    decrypted = xxtea_decrypt(payload, XXTEA_KEY)

    chunk = Lua53Chunk(decrypted)
    hdr = chunk.read_bytes(33)
    size_up = chunk.read_byte()
    proto = chunk.parse_proto()

    print(f"\n==========================================")
    print(f"VERIFYING: {arc_path}")
    print(f"==========================================")
    checks = [
        (175, "Image 1 Speaker (Broke Gangster)"),
        (266, "Image 1 Dialogue (Everybody charge!)"),
        (270, "Image 2 Dialogue (small fry / run your mouths)"),
        (274, "Image 2 Follow-up (Talk to my bat)"),
        (290, "Image 3 Speaker (Subdued Gangster)"),
        (291, "Image 3 Dialogue (Our mistake!)"),
        (318, "Image 4 Dialogue (Cap! Neuvira and I made it!)"),
        (321, "Follow-up (tails between their legs)")
    ]
    for idx, desc in checks:
        val = proto["constants"][idx][1][1].decode("utf-8")
        print(f"[{idx}] {desc}:\n    --> {val}")
