import shutil
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
repacked_src = os.path.join(viet_dir, r"work\research\data_patched_vi.arcx")
dest = r"c:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx"

shutil.copy2(repacked_src, dest)
size = os.path.getsize(dest)
print(f"Copied data_patched_vi.arcx to {dest} ({size} bytes)")
