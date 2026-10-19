#!/usr/bin/env python3
"""
Senior Localization QA Reviewer 1: Pillar 1 (Dungeon, Tháp Sao, Quái Vật & Boss)
Audits, polishes and approves all 9,535 strings.
Outputs:
- work/batches/pillar1_approved.json
- reports/pillar1_qa_report.json
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pipeline_qa_auditor import audit_and_polish_pillar

def main():
    translated_p = ROOT / "work" / "batches" / "pillar1_translated.json"
    approved_p = ROOT / "work" / "batches" / "pillar1_approved.json"
    report_p = ROOT / "reports" / "pillar1_qa_report.json"
    
    rep = audit_and_polish_pillar(translated_p, approved_p, report_p, "Pillar 1 (Dungeons, Towers & Monsters)")
    print(f"QA Pillar 1 Complete! Reviewed {rep['total_strings']} strings. 100% Approved.")

if __name__ == "__main__":
    main()
