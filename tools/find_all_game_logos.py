import UnityPy
from pathlib import Path

res_dir = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource")
ps_dir = Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\AssetBundles")

all_bundles = list(res_dir.glob("*.unity3d")) + list(ps_dir.glob("*.unity3d"))
print(f"Total bundles to search: {len(all_bundles)}")

found_logos = []

for b in all_bundles:
    bn = b.name.lower()
    # Check if bundle name has logo, title, start, main, icon, brand, splash
    if any(k in bn for k in ["logo", "title", "start", "main", "splash", "enter", "brand", "gate"]):
        try:
            env = UnityPy.load(str(b))
            for obj in env.objects:
                if obj.type.name in ["Texture2D", "Sprite"]:
                    data = obj.read()
                    name = getattr(data, "m_Name", getattr(data, "name", ""))
                    if "logo" in name.lower() or "title" in name.lower() or "stella" in name.lower():
                        found_logos.append((b.name, obj.type.name, name))
        except Exception:
            pass

print(f"Found {len(found_logos)} logo/title textures:")
for item in found_logos:
    print(" ", item)
