#!/usr/bin/env python3
"""Read-only sanity check for module review checkpoint. No external services/writes."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

CHECKPOINT = 'coordination/repository_knowledge/module_roadmap_review_pilots/telegram_bot/2026-10-16_D01'
GUIDE = 'coordination/repository_knowledge/module_knowledge_stabilization/field_guides/2026-10-16__deep_module_roadmap_review_pilot_v0_1.md'
DOCS = ['00_START_HERE.md', '03_IMPLEMENTATION_AND_DEPENDENCY_REVIEW.md',
        '04_OWNER_REVIEW_AND_STOP_RULE.md', '05_OC01_CF10_DIAGNOSTIC_BOUNDARIES.md',
        '06_PRECOMMIT_AND_CONTEXT_PACK_CHECKLIST.md', '08_NEXT_ASSISTANT_HANDOFF.md',
        '07_REFERENCE_HASHES.json']

def validate(root: Path) -> list[str]:
    errors = []
    for p in [GUIDE] + [CHECKPOINT+'/'+p for p in DOCS]:
        if not (root / p).is_file(): errors.append('MISSING '+p)
    try:
        import yaml
        evidence = yaml.safe_load((root / CHECKPOINT / '01_TELEGRAM_EVIDENCE_CHECKPOINT.yaml').read_text('utf-8'))
        unknowns = yaml.safe_load((root / CHECKPOINT / '02_CRITICAL_UNKNOWNS_AND_OWNER_GATES.yaml').read_text('utf-8'))
        gate = yaml.safe_load((root / 'coordination/repository_knowledge/module_knowledge_stabilization/field_guides/2026-10-16__analysis_stop_and_owner_review_gates_v0_1.yaml').read_text('utf-8'))
        c = evidence.get('evidence_counts', {})
        for k,v in {'historical_steps':21, 'l0_capabilities':42, 'candidate_work_packages':52, 'review_decision_cards':19, 'source_original_dftb_verified':0}.items():
            if c.get(k) != v: errors.append(f'BAD_COUNT {k}')
        if evidence.get('canonical_roadmap_mutated') is not False: errors.append('FALSE_CANONICAL_CLAIM')
        if evidence.get('implementation_approved') is not False: errors.append('FALSE_IMPLEMENTATION_CLAIM')
        if len(unknowns.get('items', [])) < 10: errors.append('INSUFFICIENT_UNKNOWN_REGISTER')
        if not gate.get('next_evidence_test_allowed_only_if'): errors.append('MISSING_STOP_GATE')
        hashes = json.loads((root / CHECKPOINT / '07_REFERENCE_HASHES.json').read_text('utf-8'))
        if not hashes.get('references'): errors.append('MISSING_PROVENANCE_REFERENCES')
    except Exception as e: errors.append('PARSE_ERROR '+type(e).__name__+': '+str(e)[:140])
    return errors

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, default=Path('.'))
    a = ap.parse_args()
    errs = validate(a.root.resolve())
    print('MODULE_REVIEW_CHECKPOINT=' + ('PASS' if not errs else 'FAIL'))
    for e in errs: print(e)
    raise SystemExit(bool(errs))
if __name__ == '__main__': main()
