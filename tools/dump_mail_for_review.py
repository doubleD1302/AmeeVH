#!/usr/bin/env python3
"""Review MailTemplate entries."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    with open(root / 'work' / 'polish' / 'audit_mail.json', 'r', encoding='utf-8') as f:
        items = json.load(f)

    print(f"Total MailTemplate: {len(items)}")
    
    with open(root / 'work' / 'polish' / 'mail_review.txt', 'w', encoding='utf-8') as out:
        for it in items:
            k = it['key']
            en = it['en']
            cn = it['cn']
            vi = it['vi']
            out.write(f"{k} | EN: {en} | CN: {cn} | VI: {vi}\n")

    print("Wrote all entries to mail_review.txt")

if __name__ == '__main__':
    main()
