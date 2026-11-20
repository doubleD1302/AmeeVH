"""Locale-owned source rows plus lossless raw-file chunks, without EN matching."""
import collections
import hashlib
import json
import pathlib
import re
from prepare_sheets_cn_jp_20261103 import SOURCE, FIELDS, MAIN

OUT = SOURCE.parents[1] / 'work/runs/sheets_full_sources_20261103_r02'


def leaves(x, path=''):
    if isinstance(x, str):
        yield path, x
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from leaves(v, path + '/' + str(i))
    elif isinstance(x, dict):
        for k, v in x.items():
            yield from leaves(v, path + '/' + str(k))


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    manifest_bytes = (SOURCE / 'MANIFEST.json').read_bytes()
    manifest = json.loads(manifest_bytes.decode('utf-8-sig'))
    registry = {x['path']: x for x in manifest['files']}
    audit = {'manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest(), 'inputs': [], 'sheets': {}, 'method': 'Each locale is imported independently. Raw source file bytes are represented as UTF-8 text chunks in order; BOM and line endings are preserved.'}
    sheets = []

    def read(rel):
        b = (SOURCE / rel).read_bytes()
        assert hashlib.sha256(b).hexdigest() == registry[rel]['sha256'], rel
        audit['inputs'].append({'path': rel, 'sha256': registry[rel]['sha256'], 'bytes': len(b)})
        return b

    def save(title, rows, description):
        assert len({r[0] for r in rows}) == len(rows), title
        expanded = []
        split_count = 0
        for ident, text, group in rows:
            assert isinstance(text, str)
            if len(text.encode('utf-16-le')) // 2 <= 30000:
                expanded.append([ident, text, group])
            else:
                for i in range(0, len(text), 12000):
                    expanded.append([ident + f'::text_part/{i//12000:05}', text[i:i+12000], group])
                split_count += 1
        rows = expanded
        file = title + '.json'
        data = [['ID nguồn', 'Nội dung gốc', 'Nhóm / tệp']] + rows
        (OUT / file).write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        info = {'title': title, 'file': file, 'rows': len(rows), 'nonempty': sum(bool(r[1]) for r in rows), 'description': description, 'split_long_values': split_count}
        audit['sheets'][title] = info
        sheets.append(info)

    for loc in ('CN', 'JP'):
        raw = []

        def source(rel):
            b = read(rel)
            text = b.decode('utf-8')
            parts = [text[i:i+12000] for i in range(0, len(text), 12000)] or ['']
            assert ''.join(parts).encode('utf-8') == b
            raw.extend([rel + f'::part/{i:05}', part, rel] for i, part in enumerate(parts))
            return json.loads(b.decode('utf-8-sig')) if rel.endswith('.json') else text

        scene_text = source(f'99_DuLieuGoc/Scenes/Scenes_{loc}.jsonl')
        scene_rows = []
        for scene in map(json.loads, scene_text.lstrip('\ufeff').splitlines()):
            sid = scene['scene_id']
            for i, cmd in enumerate(scene['commands_data']):
                name = cmd['cmd']; params = cmd.get('param', [])
                fields = set(FIELDS.get(name, []))
                # Keep the gender-dependent alternative fields independently.
                if name in MAIN:
                    fields.add(MAIN[name] + 1)
                    if loc == 'CN':
                        fields.discard(MAIN[name])
                        fields.add(2)
                for k in sorted(fields):
                    if k >= len(params):
                        continue
                    for sub, text in leaves(params[k]):
                        if text:
                            scene_rows.append([f'{sid}::command/{i}/param/{k}{sub}', text, sid])
        save(loc + '_Thoai', scene_rows, 'Thoại, tên người nói, tiêu đề, lựa chọn và biến thể giới tính; các tham số khác được giữ đầy đủ trong DuLieuGoc.')
        table_rows = []
        for item in manifest['items']:
            if item['kind'] != 'raw_table':
                continue
            table = source(item[loc.lower()])
            table_rows.extend([key, text, item['table']] for key, text in table.get('values', {}).items())
        save(loc + '_Bang', table_rows, 'Tất cả khóa bảng text trong nguồn, gồm giá trị rỗng.')
        voices = source(f'99_DuLieuGoc/BubbleVoice/BubbleVoice_{loc}.json')
        voice_rows = [[f'{key}::text{field}', text, key] for key, data in voices.items() for field, text in leaves(data.get('text', {}))]
        save(loc + '_Giong', voice_rows, 'Giữ riêng track giọng và số đoạn; bao gồm đoạn rỗng trong nguồn.')
        presets = source(f'99_DuLieuGoc/Presets/Presets_{loc}.json')
        preset_rows = [[name + '::' + field, text, name] for name, obj in presets.items() for field, text in leaves(obj['data'])]
        save(loc + '_Preset', preset_rows, 'Các trường chuỗi trong preset theo đường dẫn gốc.')
        subs = source(f'99_DuLieuGoc/Subtitles/Subtitles_{loc}.json')
        subtitle_rows = []
        for file in subs['files']:
            for block in re.split(r'\n\s*\n', file['text'].lstrip('\ufeff').replace('\r\n', '\n').replace('\r', '\n').strip()):
                parts = block.split('\n')
                assert len(parts) >= 3 and parts[0].isdigit() and '-->' in parts[1], file['name']
                subtitle_rows.append([file['name'] + '::cue/' + parts[0] + '::' + parts[1], '\n'.join(parts[2:]), file['name']])
        save(loc + '_PhuDe', subtitle_rows, 'Cue và thời gian gốc của từng ngôn ngữ; không ghép theo số cue giữa locale.')
        source(f'99_DuLieuGoc/Lua_Strings/Lua_Strings_{loc}.jsonl')
        # Candidate TXT files retain their source labels and constant IDs in full.
        lua_rows = []
        for item in manifest['items']:
            if item['kind'] == 'lua_candidates':
                b = read(item[loc.lower()])
                text = b.decode('utf-8')
                for i in range(0, len(text), 12000):
                    lua_rows.append([item['source_lua'] + f'::part/{i//12000:05}', text[i:i+12000], item['source_lua']])
        save(loc + '_Lua', lua_rows, 'Toàn văn 379 tệp ứng viên Lua được cung cấp; nhãn chưa xác nhận và truy vết tĩnh giữ nguyên.')
        save(loc + '_DuLieuGoc', raw, 'Toàn văn nguồn thô được chia phần theo thứ tự. Ghép Nội dung gốc của cùng tệp theo ID part để khôi phục đúng UTF-8 gốc.')
    overview = [
        ['Stella Sora — nguồn CN và JP', 'Client 2.0.1, bộ tổng hợp r03', '2026-11-03'],
        ['Phạm vi', 'Nhập từng ngôn ngữ độc lập, không lọc theo Sheet EN cũ', ''],
        ['ID', 'ID của từng locale được giữ riêng. Cùng vị trí hàng giữa CN và JP không xác lập cặp dịch.', ''],
        ['Dữ liệu gốc', 'Giữ đầy đủ file thô ở các tab DuLieuGoc, bao gồm trường và lệnh chưa được đưa vào tab đọc thoại.', ''],
        ['Phần dài', 'Giá trị vượt giới hạn ô được chia text_part; ghép theo thứ tự để khôi phục.', ''],
        ['Thiếu trong nguồn', 'JP thiếu cảnh GD_gacha và một số phụ đề. Chi tiết theo manifest của bộ nguồn.', ''],
        ['Đơn vị thống kê', 'Một hàng đọc là một trường nguồn; một hàng DuLieuGoc/Lua là một phần tệp. Không cộng chúng thành số câu dịch.', ''],
        ['Tab', 'Số hàng dữ liệu', 'Mô tả'],
    ] + [[s['title'], s['rows'], s['description']] for s in sheets]
    (OUT / 'ThongTin.json').write_text(json.dumps(overview, ensure_ascii=False), encoding='utf-8')
    sheets.insert(0, {'title': 'ThongTin', 'file': 'ThongTin.json', 'rows': len(overview), 'description': 'Phạm vi và thống kê'})
    (OUT / 'PLAN.json').write_text(json.dumps({'sheets': sheets}, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'SOURCE_AUDIT.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'sheets': [{k:v for k,v in s.items() if k in ('title','rows','nonempty')} for s in sheets], 'verified_inputs':len(audit['inputs'])}, ensure_ascii=False))


if __name__ == '__main__':
    main()
