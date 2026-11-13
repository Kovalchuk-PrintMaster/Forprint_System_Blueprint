# Zero-Stage Blueprint Autonomous Worker Strategy

Before broad module rollout, launch and stabilize one bounded autonomous worker inside Blueprint.

## Appropriate early work
- bounded repository cleanup/reorganization;
- operator CLI/status/reporting;
- persistent execution/resume tooling;
- verification-tier tooling;
- local Dispatcher Telegram bot;
- health/watchdog utilities;
- index/discoverability improvements.

## Initially forbidden
- global project planning;
- reprioritizing other modules;
- autonomous cross-module roadmap restructuring;
- unrestricted cross-module/repository writes;
- release authority;
- silent authority escalation.

## Required chain
`Dispatcher -> validated task package -> selected profile -> isolated workspace -> execution -> tests/validation -> result envelope -> attempt history -> promotion gate`

Python dependency isolation and repository/workspace isolation are separate concerns.

Failed work must remain inspectable; retries/resume must preserve evidence.
Exact commit/push/merge policy must be recovered or reconciled before launch.
