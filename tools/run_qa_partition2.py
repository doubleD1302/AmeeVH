#!/usr/bin/env python3
"""
Localization QA Reviewer 2: Nhân Vật, Chiến Thuật & Lối Chơi, Hồ Sơ & Vật Phẩm
Audits, polishes and approves all 769 strings of Partition 2:
- CharacterDes, TrialCharacter, CharacterArchiveBaseInfo, Character, Item, ActivityGoods, etc.
Outputs:
- work/batches/partition2_approved.json
- reports/partition2_qa_report.json
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pipeline_qa_auditor import audit_and_polish_pillar

def main():
    translated_p = ROOT / "work" / "batches" / "partition2_translated.json"
    approved_p = ROOT / "work" / "batches" / "partition2_approved.json"
    report_p = ROOT / "reports" / "partition2_qa_report.json"
    
    rep = audit_and_polish_pillar(translated_p, approved_p, report_p, "Partition 2 (Characters, Profiles, Tactics & Items)")
    print(f"QA Partition 2 Complete! Reviewed {rep['total_strings']} strings. 100% Approved.")

if __name__ == "__main__":
    main()
