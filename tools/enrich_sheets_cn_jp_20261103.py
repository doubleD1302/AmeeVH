"""Add structural source references only when the entire text-command skeleton matches."""
import hashlib
import json
from prepare_sheets_cn_jp_20261103 import SOURCE, OUT, FIELDS, MAIN, load, actor, voice, value_at


def signature(c):
    name = c['cmd']
    p = c.get('param', [])
    return (name, actor(c) if name in MAIN else None,
            voice(c) if name in MAIN else None,
            p[0] if name in ('SetChoiceBegin', 'SetPhoneMsgChoiceBegin', 'NewCharIntro') and p else None)


def main():
    records = load(OUT / 'CANDIDATES.json')
    audit = load(OUT / 'SOURCE_AUDIT.json')
    assert hashlib.sha256((SOURCE / 'MANIFEST.json').read_bytes()).hexdigest() == audit['manifest_sha256']
    scenes = {}
    for loc in ('EN', 'CN', 'JP'):
        rel = f'99_DuLieuGoc/Scenes/Scenes_{loc}.jsonl'
        b = (SOURCE / rel).read_bytes()
        expected = next(x for x in audit['verified_inputs'] if x['path'] == rel)
        assert hashlib.sha256(b).hexdigest() == expected['sha256']
        scenes[loc] = {s['scene_id']: s for s in map(json.loads, b.decode('utf-8-sig').splitlines())}
    mappings = {}
    for sid, scene in scenes['EN'].items():
        en = [(i, c) for i, c in enumerate(scene['commands_data']) if c['cmd'] in FIELDS]
        for loc in ('CN', 'JP'):
            other = scenes[loc].get(sid)
            if not other:
                continue
            target = [(i, c) for i, c in enumerate(other['commands_data']) if c['cmd'] in FIELDS]
            if len(en) != len(target) or any(signature(a) != signature(b) for (_, a), (_, b) in zip(en, target)):
                continue
            mappings[(sid, loc)] = {i: j for (i, _), (j, _) in zip(en, target)}
    additions = []
    counts = {'CN': 0, 'JP': 0}
    for r in records:
        sid, command, field = r['en_id'].split('::')[0], int(r['en_id'].split('/')[1]), tuple(map(int, r['en_id'].split('/')[3:]))
        name = scenes['EN'][sid]['commands_data'][command]['cmd']
        changed = False
        for loc in ('CN', 'JP'):
            key = loc.lower()
            if key in r:
                continue
            target_command = mappings.get((sid, loc), {}).get(command)
            if target_command is None:
                continue
            target_field = (2,) + field[1:] if loc == 'CN' and field[0] == MAIN.get(name) else field
            text = value_at(scenes[loc][sid]['commands_data'][target_command].get('param', []), target_field)
            if text is None:
                continue
            r[key] = text
            r[key + '_id'] = f'{sid}::command/{target_command}/param/' + '/'.join(map(str, target_field))
            r[key + '_method'] = 'Chuỗi lệnh chứa chữ, mã nhân vật và mã giọng trùng'
            r.pop(key + '_reason', None)
            changed = True
            counts[loc] += 1
        if changed:
            additions.append(r)
    target = OUT / 'structural_enrichment'
    target.mkdir(exist_ok=False)
    for i in range(0, len(additions), 200):
        (target / f'{i // 200:04}.json').write_text(json.dumps(additions[i:i+200], ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    report = {'added_fields': counts, 'changed_records': len(additions), 'chunks': (len(additions) + 199)//200,
              'method': 'Entire ordered sequence of text-bearing commands, exact actor/voice/choice identifiers; no fuzzy text match',
              'semantic_review': 'not_performed; source references only'}
    (target / 'REPORT.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
