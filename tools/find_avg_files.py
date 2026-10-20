import os

game_dir = r"c:\YostarGames\StellaSora_EN"

print("Searching for AVG or story files in game directory...")
for root, dirs, files in os.walk(game_dir):
    # Skip .git or .venv
    if ".git" in root or ".venv" in root or "node_modules" in root:
        continue
    for f in files:
        fl = f.lower()
        if "avg" in fl or "dialogue" in fl or "script" in fl or "story" in fl:
            if not fl.endswith(".py") and not fl.endswith(".json") and not fl.endswith(".txt"):
                rel = os.path.relpath(os.path.join(root, f), game_dir)
                print(f"  {rel} ({os.path.getsize(os.path.join(root, f))} bytes)")
