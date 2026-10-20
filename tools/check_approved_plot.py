import glob, json

for f in sorted(glob.glob('StellaSora_VietHoa/work/batches/*approved*.json')):
    try:
        data = json.load(open(f, encoding='utf-8'))
        found = 0
        for it in data:
            k = it.get('key', '')
            t = it.get('table', '')
            if 'Plot' in t or 'Plot' in k or 'Story' in t:
                found += 1
                if found <= 3:
                    print(f"{f}: [{k}] EN: {it.get('en')} -> VI: {it.get('approved_vi', it.get('vi', it.get('current_vi')))}")
        if found:
            print(f"Total in {f}: {found}")
    except Exception as e:
        pass
