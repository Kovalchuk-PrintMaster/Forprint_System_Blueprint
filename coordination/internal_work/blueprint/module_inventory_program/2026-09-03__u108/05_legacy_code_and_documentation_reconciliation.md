# Legacy Code and Documentation Reconciliation

Long-lived modules can contain several mutually incompatible generations of implementation. Autonomous assistants must not be forced to infer the current generation from search results.

## Active-path evidence order
Prefer:
1. verified runtime evidence;
2. current executable/import path;
3. current tests/deployment scripts;
4. current config;
5. current Blueprint-approved contract;
6. current docs consistent with code;
7. historical docs.

Modification time alone is not authority.

## Isolation before deletion
When old code may confuse future agents:
- remove it from canonical read paths where safe;
- mark deprecated/historical;
- explain why;
- prevent accidental import/execution where safe;
- preserve evidence until retirement approval.

Deletion is a lifecycle decision, not an inventory shortcut.

## Functionality owned elsewhere
Before moving code:
- record ownership candidate;
- required interface/contract;
- dependencies;
- migration path;
- compatibility period if needed;
- old-location deprecation plan.

## Documentation contradiction register
Mandatory for high-risk conflicts, including:
- two “current” architectures;
- old/new prompt-report protocols;
- competing semantic owners;
- obsolete DB schemas;
- conflicting release/deployment instructions;
- obsolete configuration guidance;
- Telegram/Calculator behaviors conflicting with current ownership.

## Desired end state
A fresh assistant sees one canonical read path, explicit historical areas, a repository index, ownership boundaries, current roadmap, and one coordination protocol.
