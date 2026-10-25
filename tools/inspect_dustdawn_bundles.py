import UnityPy
from pathlib import Path

bundle_paths = [
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource\ui_mainlineex_dustdawnstory.en.unity3d"),
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource\ui_mainlineex_dustdawnstory.unity3d"),
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource\ui_activity_20104.en.unity3d"),
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource\ui_activity_20104.unity3d")
]

for bp in bundle_paths:
    if not bp.exists():
        continue
    env = UnityPy.load(str(bp))
    print(f"=== Bundle: {bp.name} ===")
    for obj in env.objects:
        if obj.type.name in ["Texture2D", "Sprite", "SpriteAtlas"]:
            data = obj.read()
            name = getattr(data, "m_Name", getattr(data, "name", "unknown"))
            print(f"  {obj.type.name}: {name}")
