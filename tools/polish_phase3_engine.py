#!/usr/bin/env python3
"""Phase 3 Polish Engine: Story, ActivityStory, DatingCharacterEvent, DatingLandmarkEvent,
AffinityQuest, AffinityUpReward, ActivityTask, ActivityGoods, MallPackage, PenguinCard.
"""

import json
import re
from pathlib import Path

# Paths
ROOT = Path(__file__).resolve().parent.parent
DEC_ENTRIES = ROOT / 'work' / 'research' / 'data_decrypted' / 'entries'
ORIG_ENTRIES = ROOT / 'work' / 'research' / 'data_en_original' / 'entries'
POLISH_DIR = ROOT / 'work' / 'polish'

# Load Master Glossary
with open(ROOT / 'config' / 'master_glossary.json', 'r', encoding='utf-8') as f:
    MASTER_GLOSSARY = json.load(f)

# Load CN sources for Phase 3
CN_FILES = {
    'Story': '00890_0x939d4390e6e6b8fd.bin',
    'ActivityStory': '00727_0x789e881d02a7ddcb.bin',
    'DatingCharacterEvent': '00765_0x733ee8fdb8a6a976.bin',
    'DatingLandmarkEvent': '00767_0x43ac532f7df5c82a.bin',
    'AffinityQuest': '00731_0x1e77dcffbbba3b93.bin',
    'AffinityUpReward': '00732_0xaa8312ae07d84ae0.bin',
    'ActivityTask': '00728_0xc316bcdb179b0d6e.bin',
    'ActivityGoods': '00719_0x6685539fd40c9e98.bin',
    'MallPackage': '00815_0x6f0361474c111904.bin',
    'PenguinCard': '00833_0x469c8ae265bf9745.bin'
}

def load_cn_dicts():
    cn_dicts = {}
    for tname, fname in CN_FILES.items():
        with open(ORIG_ENTRIES / fname, 'r', encoding='utf-8') as f:
            cn_dicts[tname] = json.load(f)
    return cn_dicts

print("Phase 3 Polish Engine loaded.")
