from PIL import Image
from pathlib import Path

out_dir = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\dist\Xuat_Logo_StellaSora")

# Load 1x EN logo
en_1x = Image.open(out_dir / "Logo_StellaSora_English_Chuan_538x214.png").convert("RGBA")

# Create 2x upscale (1076 x 428)
en_2x = en_1x.resize((en_1x.width * 2, en_1x.height * 2), Image.Resampling.LANCZOS)
en_2x.save(out_dir / "Logo_StellaSora_English_HD_1076x428.png")

# Create 4x upscale (2152 x 856) for high-res design / poster / video editing
en_4x = en_1x.resize((en_1x.width * 4, en_1x.height * 4), Image.Resampling.LANCZOS)
en_4x.save(out_dir / "Logo_StellaSora_English_UltraHD_2152x856.png")

# Copy HD to brain artifacts
shutil_hd = Path(r"C:\Users\chann\.gemini\antigravity\brain\fedb6985-4403-4c7b-b3c0-549d2f56084c\Logo_StellaSora_English_HD_1076x428.png")
import shutil
shutil.copy(out_dir / "Logo_StellaSora_English_HD_1076x428.png", shutil_hd)

print("Generated HD and UltraHD logos successfully!")
