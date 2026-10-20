import re

log_path = r"C:\Users\chann\AppData\LocalLow\YOSTAR (HONG KONG) LIMITED\StellaSora\Player.log"
with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

urls = re.findall(r"https?://[^\s\"'<>]+", text)
print(f"Total URLs found: {len(urls)}")
for u in sorted(set(urls)):
    print(u)
