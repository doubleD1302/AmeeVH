import UnityPy
from pathlib import Path
from PIL import Image
from UnityPy.export import Texture2DConverter

out_dir = Path(r"C:\Users\chann\.gemini\antigravity\brain\fedb6985-4403-4c7b-b3c0-549d2f56084c\dustdawn_dump")
out_dir.mkdir(parents=True, exist_ok=True)

bundle_paths = [
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource\ui_activity_20104.unity3d"),
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource\ui_activity_20104.en.unity3d"),
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource\ui_mainlineex_dustdawnstory.unity3d"),
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource\ui_mainlineex_dustdawnstory.en.unity3d"),
]

targets = [
    "bg_dustdawn_main_1",
    "bg_dustdawn_story",
    "20104_Downdust",
    "zs_dustdawn_main_logo_lang",
    "bg_DustDawn_activity_06",
    "bg_dustdawn_popup",
    "db_dustdawn_task_title"
]

for bp in bundle_paths:
    if not bp.exists():
        continue
    env = UnityPy.load(str(bp))
    for obj in env.objects:
        if obj.type.name == "Texture2D":
            data = obj.read()
            if data.m_Name in targets:
                try:
                    img = Texture2DConverter.get_image_from_texture2d(data, flip=True)
                    out_path = out_dir / f"{bp.stem}__{data.m_Name}.png"
                    img.save(out_path)
                    print(f"Saved: {out_path} ({img.size})")
                except Exception as e:
                    print(f"Error saving {data.m_Name}: {e}")
