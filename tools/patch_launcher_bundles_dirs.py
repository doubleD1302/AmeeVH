from pathlib import Path

p = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\launcher\launcher_pc.py")
content = p.read_text(encoding="utf-8")

old_text = """            # Install Vietnamese AssetBundles (Textures: Comics, Titles, Logos)
            bundles_src_dirs = [
                BASE_DIR / "dist" / "AssetBundles",
                BASE_DIR / "staging" / "bundles_patched_vi" / "Persistent_Store" / "AssetBundles",
            ]"""

new_text = """            # Install Vietnamese AssetBundles (Textures: Verified Loading Comics)
            bundles_src_dirs = [
                BASE_DIR / "staging" / "texture_candidate_v096" / "Persistent_Store" / "AssetBundles",
                BASE_DIR / "dist" / "AssetBundles",
                BASE_DIR / "staging" / "bundles_patched_vi" / "Persistent_Store" / "AssetBundles",
            ]"""

if old_text in content:
    content = content.replace(old_text, new_text, 1)
    p.write_text(content, encoding="utf-8")
    print("SUCCESS: Updated bundles_src_dirs in launcher_pc.py")
else:
    print("WARNING: old_text not found in launcher_pc.py")
