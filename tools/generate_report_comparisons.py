#!/usr/bin/env python3
"""Generate Before vs After comparisons for Phase 1 report."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    ds_path = root / 'work' / 'polish' / 'phase1_dataset.json'
    pol_path = root / 'work' / 'polish' / 'phase1_polished.json'

    with open(ds_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    with open(pol_path, 'r', encoding='utf-8') as f:
        polished = json.load(f)

    sample_keys = [
        ('UIText', 'UIText.Achievement_Type_2.1'),
        ('UIText', 'UIText.CreatePlayer_InputName.1'),
        ('UIText', 'UIText.Continue_MainlineStory.1'),
        ('UIText', 'UIText.CharRechargeSpeed_EnergyEffDesc.1'),
        ('UIText', 'UIText.Settings_Tip_ConflictInput.1'),
        ('UIText', 'UIText.Equipment_UpgradeCountEmpty.1'),
        ('UIText', 'UIText.CharTalent_ResetCostTipAll.1'),
        ('Word', 'Word.1002.2'),
        ('Word', 'Word.1003.2'),
        ('Word', 'Word.9.1'),
        ('Word', 'Word.4045.2'),
        ('Word', 'Word.4046.2'),
        ('Word', 'Word.4054.2'),
        ('DictionaryDiagram', 'DictionaryDiagram.10050101.2'),
        ('DictionaryDiagram', 'DictionaryDiagram.10060101.2'),
        ('DictionaryDiagram', 'DictionaryDiagram.10080104.2'),
        ('DictionaryDiagram', 'DictionaryDiagram.20130101.1'),
        ('DictionaryDiagram', 'DictionaryDiagram.40021001.1'),
        ('DictionaryDiagram', 'DictionaryDiagram.40080301.1'),
        ('MailTemplate', 'MailTemplate.10001.2'),
        ('MailTemplate', 'MailTemplate.10101.3'),
        ('MailTemplate', 'MailTemplate.10103.3'),
        ('Achievement', 'Achievement.1.1'),
        ('Achievement', 'Achievement.100.2'),
        ('Achievement', 'Achievement.330.2')
    ]

    print("KEY COMPARISONS (Before vs After):\n")
    for tbl, k in sample_keys:
        it = next((x for x in dataset[tbl] if x['key'] == k), None)
        if not it:
            continue
        en = it['en']
        cn = it.get('cn', '')
        before = it.get('vi_current', '')
        after = polished[tbl].get(k, '')
        print(f"[{tbl}] {k}")
        print(f"  EN:     {en}")
        if cn:
            print(f"  CN:     {cn}")
        print(f"  BEFORE: {before}")
        print(f"  AFTER:  {after}")
        print("-" * 60)

if __name__ == '__main__':
    main()
