import json

data = json.load(open('StellaSora_VietHoa/work/batches/cross_referenced_batch3.json', encoding='utf-8'))
matched = [d for d in data if d['candidate']]
for d in matched[:30]:
    print(f"[{d['sample_key']}] EN: {d['en'][:25]:25} | CAND: {d['candidate'][:35]:35} | SRC: {d['source']}")
