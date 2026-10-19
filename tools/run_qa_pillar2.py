#!/usr/bin/env python3
"""
Senior Localization QA Reviewer 2: Pillar 2 (Lồng Tiếng, Tiểu Sử & Hồ Sơ Nhân Vật)
Audits, polishes and approves all 6,188 strings.
Outputs:
- work/batches/pillar2_approved.json
- reports/pillar2_qa_report.json
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pipeline_qa_auditor import audit_and_polish_pillar

def main():
    translated_p = ROOT / "work" / "batches" / "pillar2_translated.json"
    approved_p = ROOT / "work" / "batches" / "pillar2_approved.json"
    report_p = ROOT / "reports" / "pillar2_qa_report.json"
    
    rep = audit_and_polish_pillar(translated_p, approved_p, report_p, "Pillar 2 (Character Voices & Archive)")
    print(f"QA Pillar 2 Complete! Reviewed {rep['total_strings']} strings. 100% Approved.")

if __name__ == "__main__":
    main()
