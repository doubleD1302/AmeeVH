"""Prepare source-only references; never translate or mutate game/Sheets."""
import collections
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'dist/StellaSora_TaiNguyen_EN_JP_CN_Text_20261101_r03'
OUT = ROOT / 'work/runs/sheets_cn_jp_20261103_r01'
FIELDS = {
    'SetTalk': [7, 6], 'SetBubble': [8, 6], 'SetPhoneMsg': [7, 6],
    'SetIntro': [1, 2, 3], 'SetSceneHeading': [0, 1, 2, 3, 4],
    'SetChoiceBegin': [3, 8, 9, 10, 11, 12, 13],
    'SetPhoneMsgChoiceBegin': [1, 2, 3, 4, 5, 6],
    'SetMajorChoice': [3, 4, 5, 10, 11, 12, 17, 18, 19, 25, 26, 29, 30],
    'SetPersonalityChoice': [2, 3, 4, 8, 9], 'SetPhoneThinking': [3],
    'SetWordTrans': [0], 'NewCharIntro': [1, 2],
}
MAIN = {'SetTalk': 7, 'SetBubble': 8, 'SetPhoneMsg': 7}


def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def leaves(x, path=()):
    if isinstance(x, str) and x:
        yield path, x
    elif isinstance(x, list):
        for i, value in enumerate(x):
            yield from leaves(value, path + (i,))


def value_at(p, path):
    try:
        for i in path:
            p = p[i]
        return p if isinstance(p, str) else None
    except (TypeError, IndexError, KeyError):
        return None


def voice(c):
    p = c.get('param', [])
    v = p[4] if len(p) > 4 else None
    return v if isinstance(v, str) and v.startswith('vo_') else None


def actor(c):
    p = c.get('param', [])
    k = 0 if c['cmd'] == 'SetBubble' else 1
    return p[k] if len(p) > k else None


def prepare():
    OUT.mkdir(parents=True, exist_ok=False)
    manifest_path = SOURCE / 'MANIFEST.json'
    manifest = load(manifest_path)
    registry = {x['path']: x for x in manifest['files']}
    checked = []

    def verified(rel):
        b = (SOURCE / rel).read_bytes()
        h = hashlib.sha256(b).hexdigest()
        expected = registry[rel]
        assert expected['sha256'] == h, rel
        assert expected.get('bytes', len(b)) == len(b), rel
        checked.append({'path': rel, 'sha256': h, 'bytes': len(b)})
        return b.decode('utf-8-sig')

    scenes = {}
    for loc in ('EN', 'CN', 'JP'):
        rel = f'99_DuLieuGoc/Scenes/Scenes_{loc}.jsonl'
        rows = [json.loads(s) for s in verified(rel).splitlines() if s]
        scenes[loc] = {s['scene_id']: s for s in rows}
        assert len(rows) == len(scenes[loc])
    candidates = []
    stats = collections.Counter()
    for sid, en in scenes['EN'].items():
        ec = en['commands_data']
        matchers = {}
        for loc in ('CN', 'JP'):
            other = scenes[loc].get(sid)
            oc = other['commands_data'] if other else []
            same = len(ec) == len(oc) and all(a['cmd'] == b['cmd'] for a, b in zip(ec, oc))
            voices = collections.defaultdict(list)
            for j, c in enumerate(oc):
                if voice(c):
                    voices[(c['cmd'], voice(c))].append(j)
            evoices = collections.Counter((c['cmd'], voice(c)) for c in ec if voice(c))
            matchers[loc] = oc, same, voices, evoices
        for i, c in enumerate(ec):
            name = c['cmd']
            p = c.get('param', [])
            for field in FIELDS.get(name, []):
                if field >= len(p):
                    continue
                for sub, text in leaves(p[field]):
                    rec = {'scene': sid, 'en': text, 'en_id': f'{sid}::command/{i}/param/{field}' + ''.join('/' + str(x) for x in sub)}
                    for loc, (oc, same, voices, evoices) in matchers.items():
                        j, method, reason = None, None, 'Lệch cấu trúc hoặc thiếu cảnh'
                        v = voice(c)
                        if field == MAIN.get(name) and v:
                            hits = voices.get((name, v), [])
                            if len(hits) == 1 and evoices[(name, v)] == 1:
                                j, method = hits[0], 'Cùng mã giọng'
                        if j is None and same:
                            j, method = i, 'Cùng cảnh và thứ tự lệnh'
                        if j is not None and name in MAIN and actor(c) != actor(oc[j]):
                            j, method, reason = None, None, 'Mã nhân vật không khớp'
                        target_field = 2 if loc == 'CN' and field == MAIN.get(name) else field
                        target_path = (target_field,) + sub
                        value = value_at(oc[j].get('param', []), target_path) if j is not None else None
                        if value is not None:
                            rec[loc.lower()] = value
                            rec[loc.lower() + '_id'] = f'{sid}::command/{j}/param/{target_field}' + ''.join('/' + str(x) for x in sub)
                            rec[loc.lower() + '_method'] = method
                            stats[loc + '_mapped_fields'] += 1
                        else:
                            rec[loc.lower() + '_reason'] = reason if j is None else 'Trường nguồn không có text tương ứng'
                    candidates.append(rec)
    for loc in ('EN', 'CN', 'JP'):
        verified(f'99_DuLieuGoc/Subtitles/Subtitles_{loc}.json')
    # Use only byte-verified corrected SRT files. Cue IDs alone cannot align locales.
    for item in manifest['items']:
        if item['kind'] != 'raw_srt':
            continue
        for loc in ('en', 'cn', 'jp'):
            rel = item[loc]
            if not rel.endswith('.srt'):
                continue
            raw = verified(rel).replace('\r\n', '\n').replace('\r', '\n').strip()
            cues = []
            for block in re.split(r'\n\s*\n', raw):
                parts = block.split('\n')
                assert len(parts) >= 3 and parts[0].isdigit() and '-->' in parts[1], rel
                cues.append({'id': parts[0], 'time': parts[1], 'text': '\n'.join(parts[2:])})
            (OUT / f"subtitle_{item['subtitle']}_{loc}.json").write_text(json.dumps(cues, ensure_ascii=False), encoding='utf-8')
    (OUT / 'CANDIDATES.json').write_text(json.dumps(candidates, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    report = {'source': str(SOURCE), 'manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(), 'verified_inputs': checked, 'counts': dict(stats), 'candidate_fields': len(candidates), 'translation_created': 0, 'game_data_written': False, 'semantic_review': 'not_performed_source_reference_import_only'}
    (OUT / 'SOURCE_AUDIT.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'verified_inputs'}, ensure_ascii=False))


if __name__ == '__main__':
    if len(sys.argv) == 1:
        prepare()
    else:
        records = load(OUT / 'CANDIDATES.json')
        start = int(sys.argv[1])
        print(json.dumps(records[start:start + 200], ensure_ascii=False, separators=(',', ':')))
