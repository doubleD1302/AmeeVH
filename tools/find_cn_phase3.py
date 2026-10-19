import json
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
all_files = list(entries.glob('*.bin'))

target_prefixes = [
    'Story.', 'ActivityStory.', 'DatingCharacterEvent.', 'DatingLandmarkEvent.',
    'AffinityQuest.', 'AffinityUpReward.', 'ActivityTask.', 'ActivityGoods.',
    'MallPackage.', 'PenguinCard.'
]

print(f"Total .bin files in entries: {len(all_files)}")

# Check every bin file to see what key prefix it has and if it contains Chinese characters
cn_range = lambda s: any('\u4e00' <= char <= '\u9fff' for char in s)

matches = {prefix: [] for prefix in target_prefixes}

for f in all_files:
    try:
        with open(f, 'r', encoding='utf-8') as fp:
            d = json.load(fp)
            if not d:
                continue
            first_k = next(iter(d.keys()))
            for prefix in target_prefixes:
                if first_k.startswith(prefix):
                    # check if content is Chinese
                    sample_vals = [v for v in list(d.values())[:10] if isinstance(v, str)]
                    has_cn = any(cn_range(v) for v in sample_vals)
                    matches[prefix].append({
                        'file': f.name,
                        'count': len(d),
                        'has_cn': has_cn,
                        'sample': sample_vals[0] if sample_vals else ''
                    })
    except Exception as e:
        pass

for prefix, flist in matches.items():
    print(f"\nPrefix: {prefix}")
    for item in flist:
        print(f"  File: {item['file']}, Count: {item['count']}, Has CN: {item['has_cn']}, Sample: {item['sample'][:40]}")
