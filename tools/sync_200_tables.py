import sys
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT))
from tools.arcx_adapter import ArcxArchive

p_200 = Path(r"C:\Users\chann\Downloads\backups\run_20261020_215315\Persistent_Store_Tables_data.arcx")
dest_dir = ROOT / "work" / "research" / "data_200_decrypted"

print(f"Unpacking pristine 2.0.0 data.arcx ({p_200.stat().st_size} bytes)...")
arc = ArcxArchive(p_200)
arc.unpack_all(dest_dir, decrypt_payload=True)
print(f"Successfully unpacked {len(arc.entries)} entries to {dest_dir}!")
