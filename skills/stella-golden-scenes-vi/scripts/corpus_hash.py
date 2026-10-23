#!/usr/bin/env python3
"""Compute editorial content hashes; does not validate source or approve samples."""
import hashlib
import json
import sys
from pathlib import Path

def content_hash(record):
    data = {k: v for k, v in record.items() if k not in ('status', 'review', 'content_sha256')}
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python corpus_hash.py corpus.jsonl')
    seen = set()
    for number, line in enumerate(Path(sys.argv[1]).read_text(encoding='utf-8-sig').splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        identity = record['scene_id']
        if identity in seen:
            raise ValueError('Duplicate scene_id at line ' + str(number))
        seen.add(identity)
        print(json.dumps({'scene_id': identity, 'content_sha256': content_hash(record)}, ensure_ascii=False))
