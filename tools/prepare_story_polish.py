import json
from pathlib import Path

# Load all 196 Story chapters
with open('StellaSora_VietHoa/tools/story_chapters_dump.json', 'r', encoding='utf-8') as f:
    chapters = json.load(f)

print(f"Loaded {len(chapters)} chapters.")
# We will inspect all chapters and formulate their translations
