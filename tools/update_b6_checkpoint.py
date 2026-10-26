import json

def update_status_and_checkpoint():
    # Update CHECKPOINT.json
    with open('StellaSora_VietHoa/CHECKPOINT.json', 'r', encoding='utf-8') as f:
        ckpt = json.load(f)

    ckpt['phase'] = 'PHASE_BATCH_06_POLISH_AND_RECONCILIATION_COMPLETED'
    ckpt['active_batch'] = 'BATCH_06_POLISH_AND_RECONCILIATION'
    ckpt['batch_status'] = 'completed_and_approved'
    ckpt['batch_06_summary'] = {
        'total_evaluated': 425,
        'reconciled_bundles': 27,
        'promoted_findings': 61,
        'dismissed_intentional': 337,
        'pending': 0,
        'ledger_path': 'work/reviews/BATCH_06_POLISH_AND_RECONCILIATION_LEDGER.json',
        'proposals_path': 'work/batches/BATCH_FIX_06_POLISH_CANDIDATES.json',
        'bundle_drift_decision': 'CANONICAL_IN_DIST_VERIFIED'
    }

    with open('StellaSora_VietHoa/CHECKPOINT.json', 'w', encoding='utf-8') as f:
        json.dump(ckpt, f, ensure_ascii=False, indent=2)

    # Update STATUS.json
    with open('StellaSora_VietHoa/STATUS.json', 'r', encoding='utf-8') as f:
        status = json.load(f)

    if 'audit_and_remediation_20261026' in status:
        status['audit_and_remediation_20261026']['batch_06_polish'] = {
            'total_candidates_evaluated': 425,
            'reconciled_bundles_count': 27,
            'promoted_findings_count': 61,
            'dismissed_intentional_count': 337,
            'pending_count': 0,
            'ledger_file': 'work/reviews/BATCH_06_POLISH_AND_RECONCILIATION_LEDGER.json',
            'proposals_file': 'work/batches/BATCH_FIX_06_POLISH_CANDIDATES.json',
            'bundle_drift_status': 'reconciled_dist_matches_manifest_100_percent'
        }

    with open('StellaSora_VietHoa/STATUS.json', 'w', encoding='utf-8') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

    print("Updated STATUS.json and CHECKPOINT.json with Batch 6 results.")

if __name__ == '__main__':
    update_status_and_checkpoint()
