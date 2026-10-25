import UnityPy
from pathlib import Path
from PIL import Image

search_dirs = [
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\AssetBundles"),
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource")
]

keywords = ["dustdawn", "20104", "reunion", "wholeness", "bulletin", "notice", "announc", "special"]

matched_bundles = []
for sdir in search_dirs:
    if not sdir.exists():
        continue
    for bpath in sdir.glob("*.unity3d"):
        bname = bpath.name.lower()
        if any(k in bname for k in keywords):
            matched_bundles.append(bpath)

print(f"Matched {len(matched_bundles)} bundles by filename keyword.")
for mb in matched_bundles:
    print(" ", mb.name)

# Also let's inspect the contents of ui_activity_20104 and ui_mainlineex_dustdawnstory
for bpath in matched_bundles:
    try:
        env = UnityPy.load(str(bpath))
        for obj in env.objects:
            if obj.type.name == "Texture2D":
                data = obj.read()
                w = getattr(data, "m_Width", 0)
                h = getattr(data, "m_Height", 0)
                tname = getattr(data, "m_Name", "")
                if w >= 512 or h >= 512 or any(k in tname.lower() for k in keywords):
                    print(f"[{bpath.name}] Texture2D: {tname} ({w}x{h})")
    except Exception as e:
        print(f"Error reading {bpath.name}: {e}")
