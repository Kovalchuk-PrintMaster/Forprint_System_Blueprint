"""A02 deferred backup handoff: visible, non-authorizing reminder.

No filesystem mutation, no backup invocation, no cloud account access.
This warning deliberately remains pending until separately reviewed code replaces
this handoff with backed and independently restored evidence.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from scripts.coordination.evidence_management import vault_v0_1 as vault

STATE = 'PENDING_EXTERNAL_INTEGRATION'


def build_status(vault_root: Path = vault.BASE, *, strict: bool = True) -> dict:
    inspected = vault.inspect(vault_root, strict=strict)
    return {
        'schema_version': 'forprint_evidence_external_backup_status_v0_1',
        'state': STATE,
        'primary_vault_root': str(vault_root),
        'primary_vault_state': inspected['state'],
        'backup_service_connected': False,
        'offhost_backup_verified': False,
        'independent_restore_verified': False,
        'authority_granted': False,
        'reminder': ('Cloud/off-host backup for the Evidence Vault is NOT connected. '
                     'Integrate the independent backup service and verify an off-host '
                     'restore before claiming protected retention or deleting old proofs.'),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--format', choices=('text', 'json'), default='text')
    args = parser.parse_args(argv)
    try:
        s = build_status()
    except (vault.VaultBlocked, OSError, ValueError, json.JSONDecodeError) as exc:
        print('EVIDENCE_VAULT_BACKUP_STATUS=BLOCKED:' + type(exc).__name__ + ':' + str(exc)[:200],
              file=sys.stderr)
        return 2
    if args.format == 'json':
        print(json.dumps(s, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print('EVIDENCE_VAULT_PRIMARY=' + s['primary_vault_state'])
        print('EVIDENCE_VAULT_BACKUP=' + STATE)
        print('BACKUP_VERIFIED=false')
        print('INDEPENDENT_RESTORE_VERIFIED=false')
        print('WARNING: Хмарне резервне копіювання Evidence Vault ще не підключене; '
              'потрібна інтеграція з окремим backup-сервісом та перевірка відновлення.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
