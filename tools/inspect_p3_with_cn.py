import json
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
p3_path = Path('StellaSora_VietHoa/work/polish/phase3_dataset.json')

with open(p3_path, 'r', encoding='utf-8') as f:
    p3_data = json.load(f)

cn_files = {
    'Story': '00890_0x939d4390e6e6b8fd.bin',
    'ActivityStory': '00727_0x789e881d02a7ddcb.bin',
    'DatingCharacterEvent': '00765_0x733ee8fdb8a6a976.bin',
    'DatingLandmarkEvent': '00767_0x43ac532f7df5c82a.bin',
    'AffinityQuest': '00731_0x1e77dcffbbba3b93.bin',
    'AffinityUpReward': '00732_0xaa8312ae07d84ae0.bin',
    'ActivityTask': '00728_0xc316bcdb179b0d6e.bin',
    'ActivityGoods': '00719_0x6685539fd40c9e98.bin',
    'MallPackage': '00815_0x6f0361474c111904.bin',
    'PenguinCard': '00833_0x469c8ae265bf9745.bin'
}

for tname, fname in cn_files.items():
    with open(entries / fname, 'r', encoding='utf-8') as f:
        cn_dict = json.load(f)
    items = p3_data[tname]
    print(f"\n=================== {tname}: {len(items)} items ===================")
    for it in items[:6]:
        k = it['key']
        cn = cn_dict.get(k, '')
        print(f"[{k}]")
        print(f"  EN: {it['en']}")
        print(f"  CN: {cn}")
        print(f"  VI: {it['vi_current']}")
