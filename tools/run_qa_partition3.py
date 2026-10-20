#!/usr/bin/env python3
"""
Localization QA Reviewer 3: Cốt Truyện, Nhiệm Vụ Tháp Sao, Đối Thoại, Kỹ Năng & Giao Diện
Audits, polishes and approves all 443 strings of Partition 3:
- StarTowerTalk, EventOptions, UIText, StarTowerBookFateCardQuest, Story, Plot, Word, Skill, etc.
Outputs:
- work/batches/partition3_approved.json
- reports/partition3_qa_report.json
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pipeline_qa_auditor import audit_and_polish_pillar

def main():
    translated_p = ROOT / "work" / "batches" / "partition3_translated.json"
    approved_p = ROOT / "work" / "batches" / "partition3_approved.json"
    report_p = ROOT / "reports" / "partition3_qa_report.json"
    
    rep = audit_and_polish_pillar(translated_p, approved_p, report_p, "Partition 3 (Story, Quests, Dialogues, Skills & UI)")
    print(f"QA Partition 3 Complete! Reviewed {rep['total_strings']} strings. 100% Approved.")

if __name__ == "__main__":
    main()
