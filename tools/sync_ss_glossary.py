#!/usr/bin/env python3
"""Project canonical SS term targets into legacy local glossary formats."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / 'SS/glossary/glossary.csv'


def projections():
    with CSV.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    terms = {}
    for row in rows:
        if row['category'] != 'term' or not row['EN'].strip() or not row['target'].strip():
            continue
        key = row['EN'].strip().casefold()
        if key in terms and terms[key]['target'] != row['target'].strip():
            raise ValueError('Ambiguous SS term: ' + row['EN'])
        terms[key] = {'source': row['EN'].strip(), 'target': row['target'].strip()}
    paths = [ROOT / 'config/glossary.json', ROOT / 'config/master_glossary.json']
    local, master = [json.loads(p.read_text(encoding='utf-8-sig')) for p in paths]
    changes = []
    existing = set()
    for entry in local['entries']:
        key = entry['source'].strip().casefold()
        if key not in terms:
            continue
        existing.add(key)
        target = terms[key]['target']
        if entry['target'] != target:
            changes.append({'source': entry['source'], 'old': entry['target'], 'new': target, 'file': 'glossary.json'})
            entry['target'] = target
        entry['term_source'] = 'SS/glossary/glossary.csv'
    for key, term in terms.items():
        if key not in existing:
            local['entries'].append({'source': term['source'], 'target': term['target'], 'status': 'proposed', 'category': 'SS term', 'notes': 'Imported term target; status does not represent semantic review.', 'term_source': 'SS/glossary/glossary.csv'})
    local['policy'] = 'SS/glossary/glossary.csv is authoritative for matching term targets; statuses and local-only entries retain their existing meaning.'
    keys = {}
    for source in master['terms']:
        keys.setdefault(source.strip().casefold(), []).append(source)
    for key, term in terms.items():
        for source in keys.get(key, [term['source']]):
            old = master['terms'].get(source)
            if old != term['target']:
                changes.append({'source': source, 'old': old, 'new': term['target'], 'file': 'master_glossary.json'})
                master['terms'][source] = term['target']
    return paths, (local, master), changes, len(terms)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    paths, data, changes, count = projections()
    encoded = [(json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8') for obj in data]
    drift = [str(path.relative_to(ROOT)) for path, content in zip(paths, encoded) if path.read_bytes() != content]
    if args.write:
        for path, content in zip(paths, encoded):
            temporary = path.with_name(path.name + '.ss-sync.tmp')
            if temporary.exists():
                raise FileExistsError(temporary)
            temporary.write_bytes(content)
            temporary.replace(path)
    print(json.dumps({'csv_sha256': hashlib.sha256(CSV.read_bytes()).hexdigest(), 'terms': count, 'drift': drift, 'target_changes': changes, 'written': args.write}, ensure_ascii=False, indent=2))
    return 1 if drift and not args.write else 0


if __name__ == '__main__':
    raise SystemExit(main())
