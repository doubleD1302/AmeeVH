"""Export verified Merge blocks as a separate read-only reference dataset."""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import sys


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True, type=pathlib.Path)
    parser.add_argument('--output', required=True, type=pathlib.Path)
    args = parser.parse_args()
    root = args.source.resolve()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit('Thư mục output đã tồn tại; chọn thư mục mới.')
    story = load_module('tramvh_story_prepare', root / '.ss-sync/Chuong_STm01/prepare.py')
    sheet = load_module('tramvh_sheet_sync', root / '.agents/skills/update-sheet/scripts/sheet_sync.py')
    pages = {}
    missing = {'cn': 0, 'jp': 0, 'en': 0}
    for group in ('Chuong_STm00', 'Chuong_STm01', 'Chuong_STm02', '03_BangText_UI_KyNang'):
        manifest = json.loads((root / '.ss-sync' / group / 'partition_manifest.json').read_text(encoding='utf-8'))
        files = []
        for item in manifest['files']:
            path = root / item['merge_path']
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != item['source_sha256']:
                raise ValueError(f'Merge đã thay đổi so với bản đối chiếu: {path}')
            if group.startswith('Chuong_'):
                blocks, parsed_hash = story.parse_merge(path)
                if parsed_hash != digest:
                    raise ValueError(f'Hash khi đọc không khớp: {path}')
                rows = []
                for block in blocks:
                    cn, jp, en, vi = block['texts']
                    names = block['speakers']
                    rows.append({'order': block['order'], 'kind': block['kind'], 'speaker_vi': names[0], 'speaker_en': names[1], 'speaker_jp': names[2], 'speaker_cn': names[3], 'cn': cn, 'jp': jp, 'en': en, 'vi': vi})
            else:
                payload = sheet.prepare(root, item['merge_path'])
                rows = [dict(order=row[1], kind=row[2], speaker_en=row[3], speaker_jp=row[4], speaker_cn=row[5], speaker_vi=row[6], vi=row[7], cn=row[8], jp=row[9], en=row[10], source_refs_json=row[11]) for row in payload['rows']]
            if len(rows) != item['blocks']:
                raise ValueError(f'Số khối không khớp: {path}')
            for row in rows:
                for lang in ('cn', 'jp', 'en'):
                    if row[lang] == '[MISSING_SOURCE]':
                        row[lang] = ''
                        missing[lang] += 1
            files.append({'file_id': item['file_id'], 'merge_sha256': digest, 'blocks': rows})
        pages[group] = {'group': group, 'files': files}
    output.mkdir(parents=True)
    for name, page in pages.items():
        (output / (name + '.json')).write_text(json.dumps(page, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    summary = {'files': sum(len(p['files']) for p in pages.values()), 'blocks': sum(len(f['blocks']) for p in pages.values() for f in p['files']), 'missing_source': missing}
    (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
