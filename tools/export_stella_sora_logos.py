import UnityPy
from pathlib import Path
from UnityPy.export import Texture2DConverter

out_dir = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\dist\Xuat_Logo_StellaSora")
out_dir.mkdir(parents=True, exist_ok=True)

# 1. Extract EN logo from ui_big_sprites.en.unity3d
p_en = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\AssetBundles\ui_big_sprites.en.unity3d")
if p_en.exists():
    env = UnityPy.load(str(p_en))
    for obj in env.objects:
        if obj.type.name == "Texture2D":
            data = obj.read()
            if data.m_Name == "zs_login_logo":
                img = Texture2DConverter.get_image_from_texture2d(data, flip=True)
                out_en = out_dir / "Logo_StellaSora_English_Chuan_538x214.png"
                img.save(out_en)
                print(f"Saved: {out_en} ({img.size})")

# 2. Extract Base/CN logo from ui_big_sprites.unity3d
p_cn = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource\ui_big_sprites.unity3d")
if p_cn.exists():
    env = UnityPy.load(str(p_cn))
    for obj in env.objects:
        if obj.type.name == "Texture2D":
            data = obj.read()
            if data.m_Name == "zs_login_logo":
                img = Texture2DConverter.get_image_from_texture2d(data, flip=True)
                out_cn = out_dir / "Logo_StellaSora_Goc_490x225.png"
                img.save(out_cn)
                print(f"Saved: {out_cn} ({img.size})")

# Also copy to artifacts dir for embedding / review
shutil_path_en = Path(r"C:\Users\chann\.gemini\antigravity\brain\fedb6985-4403-4c7b-b3c0-549d2f56084c\Logo_StellaSora_English_Chuan_538x214.png")
shutil_path_cn = Path(r"C:\Users\chann\.gemini\antigravity\brain\fedb6985-4403-4c7b-b3c0-549d2f56084c\Logo_StellaSora_Goc_490x225.png")

import shutil
if (out_dir / "Logo_StellaSora_English_Chuan_538x214.png").exists():
    shutil.copy(out_dir / "Logo_StellaSora_English_Chuan_538x214.png", shutil_path_en)
if (out_dir / "Logo_StellaSora_Goc_490x225.png").exists():
    shutil.copy(out_dir / "Logo_StellaSora_Goc_490x225.png", shutil_path_cn)

print("Export completed successfully!")
