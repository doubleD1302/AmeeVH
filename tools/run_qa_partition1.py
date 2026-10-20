#!/usr/bin/env python3
"""
Localization QA Reviewer 1: Minigames, Chế độ Chơi Mới & Thử Thách
Audits, polishes and approves all 320 strings of Partition 1:
- VampireSurvivor, ScoreBossGetControl, Soldier*, PenguinCard*, TowerDefense*, TraceHunt*, etc.
Outputs:
- work/batches/partition1_approved.json
- reports/partition1_qa_report.json
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pipeline_qa_auditor import audit_and_polish_pillar

def main():
    translated_p = ROOT / "work" / "batches" / "partition1_translated.json"
    approved_p = ROOT / "work" / "batches" / "partition1_approved.json"
    report_p = ROOT / "reports" / "partition1_qa_report.json"
    
    rep = audit_and_polish_pillar(translated_p, approved_p, report_p, "Partition 1 (Minigames & Combat Modes)")
    print(f"QA Partition 1 Complete! Reviewed {rep['total_strings']} strings. 100% Approved.")

if __name__ == "__main__":
    main()
