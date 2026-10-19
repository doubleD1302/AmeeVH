#!/usr/bin/env python3
"""Inspect all Disc-related tables and translations."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    orig_dir = root / 'work' / 'research' / 'data_en_original' / 'entries'
    curr_dir = root / 'work' / 'research' / 'data_decrypted' / 'entries'

    # 1. Inspect DiscIP
    disc_ip_file = '00553_0x1f924138769d46ec.bin'
    orig_ip = json.load(open(orig_dir / disc_ip_file, 'r', encoding='utf-8'))
    curr_ip = json.load(open(curr_dir / disc_ip_file, 'r', encoding='utf-8'))

    print(f"=== DiscIP ({disc_ip_file}) - Total {len(orig_ip)} keys ===")
    sample_count = 0
    for k, en in orig_ip.items():
        vi = curr_ip.get(k, '')
        print(f"[{k}] EN: {en} | VI: {vi}")
        sample_count += 1
        if sample_count >= 20:
            break

    # 2. Inspect DiscTag
    disc_tag_file = '00554_0x3abeeca79d3ed963.bin'
    orig_tag = json.load(open(orig_dir / disc_tag_file, 'r', encoding='utf-8'))
    curr_tag = json.load(open(curr_dir / disc_tag_file, 'r', encoding='utf-8'))

    print(f"\n=== DiscTag ({disc_tag_file}) - Total {len(orig_tag)} keys ===")
    for k, en in orig_tag.items():
        print(f"[{k}] EN: {en} | VI: {curr_tag.get(k, '')}")

    # 3. Check MainSkill and SecondarySkill for Disc skills (like Bedtime Story)
    print("\n=== MainSkill Disc Titles ===")
    main_skill_orig = json.load(open(orig_dir / '00591_0x57e760255c1d3b2d.bin', 'r', encoding='utf-8'))
    main_skill_curr = json.load(open(curr_dir / '00591_0x57e760255c1d3b2d.bin', 'r', encoding='utf-8'))
    
    disc_skills = []
    for k, en in main_skill_orig.items():
        if k.endswith('.1') and en:
            vi = main_skill_curr.get(k, '')
            disc_skills.append((k, en, vi))
            
    print(f"Total MainSkill titles: {len(disc_skills)}")
    for k, en, vi in disc_skills[:25]:
        print(f"  {k}: \"{en}\" -> \"{vi}\"")

if __name__ == '__main__':
    main()
