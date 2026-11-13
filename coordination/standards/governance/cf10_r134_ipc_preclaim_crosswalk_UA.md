# CF10 R134 — source-only IPC → frozen preclaim crosswalk

## Місце в канонічному ланцюжку

R134 не вводить новий launcher або preclaim. При формуванні реального **review candidate**
наявний R127 після незалежних readback R123/R126 тепер викликає R134,
який порівнює оригінальний `invocation_adapter` → R115 frozen Copilot argv
із prospective R127 IPC argv. Перевіряє один source Head, attempt, task,
work front, decision, workspace та SHA256 обох представлень.

R134 допускає для перспективного IPC **лише** `ForPrintValidation-run_repo_head`,
пінований Python, точний шлях канонічного proxy, точні flags та Unix socket,
який уже обмежено R129. При виявленні drift — `HOLD`, без fallback.

## Непорушні boundary

- `cf10_r115_preclaim_executable_profile_v0_1.py` та чинний `assert_pilot_preclaim` **не змінено**.
- R134 перевіряє, що чинний R115 усе ще **відхиляє** prospective IPC argv.
- `cf10_systemd_launcher_v0_1.py` з `LIVE_CUTOVER_ENABLED=False` незмінний.
- Немає Worker dispatch, owner claim, release, systemd-run, root broker, credential readback,
  network/sandbox attestation, Worker Result або ledger append.
- Lease R126 залишається тільки disposable R125 lab, а не production authority.
- Для будь-якого live cutover потрібні окремі позитивні G1/G2/G3/G5 докази
  та source-controlled governance; R134 їх **не закриває**.
- Розширення провайдерів заборонене: лише Copilot контрольний E2E.

## Експлуатаційні entrypoints

`make cf10-r134-ipc-preclaim-tests` — статичні негативні тести,
`make cf10-r134-ipc-preclaim-source-check` — pinned source-only readback.
Ці команди не витрачають одноразових claims і не приймають довільної
shell/env опції на live запуск.

R134 завершує підготовчу **source-compatibility частину** IPC preclaim, але НЕ
дає можливості реально виконати R127 proxy через canonical launcher.
Наступний функціональний етап: root broker/epoch + in-flight cancellation
з незалежним systemd/kernel/ledger lineage та доведеною G1–G3 ізоляцією.
