# Control Foundation scope

## Governed Procedures
Versioned Procedure Graph + Run Manifest + Conformance Validator + Waiver + evolution rules.

Candidate first procedures:
`EVENING_RECONCILIATION`, `WORKER_LAUNCH`, `ROADMAP_MUTATION`, `MODULE_BOOTSTRAP`, `WAVE_PLAN`, `WAVE_CLOSE`, `KNOWLEDGE_REFRESH`, `PUBLICATION`, `HANDOFF`, `SEMANTIC_REVIEW`.

Graph потрібен для процесів, що змінюють canonical state, перетинають модулі, мають authority/security наслідки, виконуються різними assistants, мають важливі conditional branches або можуть тихо деградувати.

## Capability / dependency model
Shared semantics повинні мати canonical capability identity, owner, version, contract, consumers. Перед `NEW` — `REUSE / EXTEND / ADAPT / REPLACE / NEW` gate.

## Project Constitution
Глобальні інваріанти живуть централізовано у Blueprint; модулі посилаються на них і додають лише module-specific invariants.

## Cross-module model
`OBSERVE -> QUERY -> PROPOSE`, але не `FOREIGN MUTATE` без explicit authority.

## Review obligations
Семантичний аудит може лишатися ручним, але обов'язок і прострочення повинні відслідковуватись машиною.

## Project Health
Один machine-readable health snapshot живить Assistant Pack, status, dashboard, reports і notifications.
