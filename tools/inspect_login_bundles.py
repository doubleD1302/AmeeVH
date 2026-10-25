import UnityPy
from pathlib import Path
from UnityPy.export import Texture2DConverter

out_dir = Path(r"C:\Users\chann\.gemini\antigravity\brain\fedb6985-4403-4c7b-b3c0-549d2f56084c\login_dump")
out_dir.mkdir(parents=True, exist_ok=True)

bundles = [
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource\ui_login.en.unity3d"),
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource\ui_login.unity3d"),
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource\loginmodulescene.unity3d"),
]

for b in bundles:
    if not b.exists():
        continue
    env = UnityPy.load(str(b))
    print(f"=== Bundle: {b.name} ===")
    for obj in env.objects:
        if obj.type.name in ["Texture2D", "Sprite"]:
            data = obj.read()
            name = getattr(data, "m_Name", getattr(data, "name", "unknown"))
            print(f"  {obj.type.name}: {name}")
            if obj.type.name == "Texture2D":
                try:
                    img = Texture2DConverter.get_image_from_texture2d(data, flip=True)
                    out_path = out_dir / f"{b.stem}__{name}.png"
                    img.save(out_path)
                    print(f"    Saved: {out_path} ({img.size})")
                except Exception as e:
                    print(f"    Error: {e}")
