import json
import sys
from pathlib import Path

root = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(root))
from tools.arcx_adapter import ArcxArchive, xxtea_decrypt, XXTEA_KEY

live_arcx = Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx")
arc = ArcxArchive(live_arcx)
raw = live_arcx.read_bytes()

for e in arc.entries:
    if e["hash"] in (0x5d07838c4787cc54, 0x1f924138769d46ec):
        data = arc.extract_entry(e, raw)
        try:
            data = xxtea_decrypt(data, XXTEA_KEY)
            d = json.loads(data.decode("utf-8"))
            h_str = hex(e["hash"])
            print(f"Hash {h_str} (idx {e['index']}): len={len(d)}, sample={list(d.keys())[0]}, 211001.3={d.get('DiscIP.211001.3')}")
            if "DiscIP.214066.3" in d:
                print(f"  214066.3 = {d.get('DiscIP.214066.3')}")
        except Exception as ex:
            print(f"Hash {hex(e['hash'])}: json decode err: {ex}")
