import json
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00890_0x939d4390e6e6b8fd.bin', 'r', encoding='utf-8') as f:
    cn_story = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    story = json.load(f)['Story']

# Group by chapter ID (e.g. Story.100, Story.1001, etc.)
chapters = {}
for it in story:
    parts = it['key'].split('.')
    cid = '.'.join(parts[:2])
    field = parts[2]
    if cid not in chapters:
        chapters[cid] = {}
    chapters[cid][field] = {
        'en': it['en'],
        'cn': cn_story.get(it['key'], ''),
        'vi': it['vi_current']
    }

print(f"Total unique chapters in Story: {len(chapters)}")

with open('StellaSora_VietHoa/tools/story_chapters_dump.json', 'w', encoding='utf-8') as f:
    json.dump(chapters, f, ensure_ascii=False, indent=2)

print("Dumped story_chapters_dump.json")
