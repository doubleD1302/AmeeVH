#!/usr/bin/env python3
"""Module for polishing AffinityQuest table (360 items)."""

import re

def polish_affinity_quest(item):
    en = item['en'].strip()

    # 1. Complete {X} Ascension with <Name>
    m = re.search(r'Complete \{([0-9]+)\} Ascension with (.*)', en, re.I)
    if m:
        return f"{m.group(2).strip()} hoàn thành {{{m.group(1)}}} lần Thám hiểm Tinh Tháp"

    m = re.search(r'([A-Za-z\s]+) has completed \{([0-9]+)\} Ascensions\.', en, re.I)
    if m:
        return f"{m.group(1).strip()} hoàn thành {{{m.group(2)}}} lần Thám hiểm Tinh Tháp"

    # 2. Invite and hang out with <Name> {X} time(s)
    m = re.search(r'(?:Invited?|Invite)\s+and\s+(?:hung?|hang)\s+out\s+with\s+([^0-9]+?)\s*\{([0-9]+)\}\s*times?\.?', en, re.I)
    if m:
        return f"Hoàn thành {{{m.group(2)}}} lần hẹn ước cùng {m.group(1).strip()}"

    # 3. <Name> reaches Tier {X}
    m = re.search(r'([A-Za-z\s]+) (?:has reached|reaches) Tier \{([0-9]+)\}\.?', en, re.I)
    if m:
        return f"{m.group(1).strip()} đột phá đến Bậc {{{m.group(2)}}}"

    # 4. Upgraded <Name>'s skills {X} times
    m = re.search(r'(?:Upgraded?|Upgrade)\s+([A-Za-z\s]+?)(?:\'s)?\s+skills?\s+\{([0-9]+)\}\s+times?\.?', en, re.I)
    if m:
        return f"Nâng cấp kỹ năng của {m.group(1).strip()} tích lũy {{{m.group(2)}}} lần"

    # 5. Save {X} Records with a Rating of {Y} with <Name>
    m = re.search(r'Save \{([0-9]+)\} Records with a Rating of \{([0-9]+)\} with (.*)', en, re.I)
    if m:
        return f"{m.group(3).strip()} lưu {{{m.group(1)}}} Kỷ Lục đạt xếp hạng {{{m.group(2)}}}"

    m = re.search(r'([A-Za-z\s]+) has saved \{([0-9]+)\} records with a rating level of \{([0-9]+)\}\.', en, re.I)
    if m:
        return f"{m.group(1).strip()} lưu {{{m.group(2)}}} Kỷ Lục đạt xếp hạng {{{m.group(3)}}}"

    # 6. Collect <Name>'s Potential(s) ×{X}
    m = re.search(r'Collect ([A-Za-z\s]+?)(?:\'s)? Potentials?\s*[x×]\{([0-9]+)\}', en, re.I)
    if m:
        return f"Thu thập Tiềm Năng của {m.group(1).strip()} ×{{{m.group(2)}}}"

    m = re.search(r'Obtained \{([0-9]+)\} ([A-Za-z\s]+?)(?:\'s)? Potentials?\.', en, re.I)
    if m:
        return f"Thu thập Tiềm Năng của {m.group(2).strip()} ×{{{m.group(1)}}}"

    # 7. All <Name>'s skills ≥ Lv.{X}
    m = re.search(r'All (?:of )?([A-Za-z\s]+?)(?:\'s)? skills (?:are at (?:Level|Lv\.)\s*|≥\s*(?:Lv\.)?\s*)\{([0-9]+)\}', en, re.I)
    if m:
        return f"Toàn bộ kỹ năng của {m.group(1).strip()} đạt Lv.{{{m.group(2)}}}"

    print(f"Warning: unmatched quest: {en}")
    return item['vi_current']

if __name__ == '__main__':
    import json
    from pathlib import Path
    p = Path('StellaSora_VietHoa/work/polish/phase3_dataset.json')
    with open(p, 'r', encoding='utf-8') as f:
        items = json.load(f)['AffinityQuest']

    polished = [polish_affinity_quest(it) for it in items]
    print(f"Polished {len(polished)} / {len(items)} AffinityQuest items.")
    assert len(polished) == len(items)
    for i in range(5):
        print(f"  EN: {items[i]['en']} -> VI: {polished[i]}")
