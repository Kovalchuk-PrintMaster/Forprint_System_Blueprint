#!/usr/bin/env python3
"""Inspect generated context ZIP semantically; no side effects."""
from __future__ import annotations
import argparse, zipfile
from pathlib import Path

POINTER='module_deep_analysis_owner_review_pilot_v0_1'
GUIDE='2026-10-16__deep_module_roadmap_review_pilot_v0_1.md'
CHECKPOINT='2026-10-16_D01/00_START_HERE.md'

def inspect(archive):
    with zipfile.ZipFile(archive) as z:
        names=z.namelist()
        specs=[n for n in names if n.endswith('coordination/bootstrap/assistant_context_system_specs_v0_1.yaml')]
        pointer=bool(specs and any(POINTER.encode() in z.read(n) for n in specs))
        guide=any(n.endswith(GUIDE) for n in names)
        checkpoint=any(n.endswith(CHECKPOINT) for n in names)
        semantic_identity=any(n.endswith('PROJECT_CONTEXT_MANIFEST.json') for n in names)
    return {'bootstrap_specs_embedded':bool(specs),'navigation_pointer_visible':pointer,
            'pilot_guide_embedded':guide,'telegram_checkpoint_embedded':checkpoint,
            'project_context_manifest_present':semantic_identity,
            'verdict':'FULL_PILOT_CONTEXT' if pointer and guide and checkpoint else ('NAVIGATION_ONLY_NEEDS_EXPLICIT_READ' if pointer else 'BLOCKED_NOT_VISIBLE')}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True);a=ap.parse_args()
    r=inspect(a.archive)
    for key,v in r.items():print(f'{key.upper()}={v}')
    # Navigation alone is useful, but not proof the full guide is packed.
    if not r['navigation_pointer_visible']:raise SystemExit(2)
if __name__=='__main__':main()
