# CF10 R135 — root-side IPC session fence: source-only, non-authorizing

## Мета

Не створюючи другий launcher чи нового protocol parser, об'єднати вже наявні
R126 (root-only disposable lease inspect/revoke), R127 (bounded MCP JSON-RPC
request/response), R129 (candidate identity), R134 (frozen Copilot preclaim
crosswalk) і R013 (канонічна systemd unit identity) в **один кандидатний
root-side MCP transport**.

Новий модуль `cf10_r135_ipc_session_fence_v0_1.py` надає Python API
`handle_session()` для **вже створених** керованих socket з trusted MCP
backend. Він сам не створює listener, не запускає MCP/Worker, не відкриває
production-доступ, не читає credentials, не використовує network, не пише
canonical ledger та не видає будь-яких release/claim повноважень.

## Що доводять source-only тести

- Вихідний R134 review перевіряється на точний attempt/epoch/head/candidate;
  додатково unit обчислюється штатним R013, а не синтетичним R129.
- Kernel SO_PEERCRED + `/proc/<pid>/cgroup` повинні збігатися з UID/GID
  `forprint-runner` та точним канонічним systemd unit; інакше HOLD.
- Кожен клієнтський frame, кожна backend-відповідь та період очікування
  перевіряються через **справжній R126 inode readback** (у fixture — mock).
- Протокол дозволяє `initialize`, `notifications/initialized`, `tools/list`,
  і лише один `tools/call` для `run_repo_head`. Немає shell, file edit,
  другого виклику чи довільних MCP-методів.
- Після рівно одного дозволеного виклику R126 ревокує **лабораторний** lease
  і перевіряє readback **до** передачі результату proxy. Race → HOLD.
- Якщо root lease відкликано, поки MCP вже виконує tool-call, результат не
  пересилається. Стан — `HOLD`, `quarantine_required=True`; **жодного**
  `terminal=PASS`, `Worker Result accepted` чи автоматичного retry.

Тести використовують реальні локальні Unix socketpair для framing/relay, але
фіктивні kernel peer readback, root-only session, lease та MCP child. Це **не
інтеграційний kernel доказ** і не допуск для live Worker.

## Що залишається відкритим

1. R126 досі обмежений disposable `/run/forprint-cf10-r125-*/lease.json`;
   не можна вважати його production authority.
2. R115 досі **відхиляє** prospective IPC-конфігурацію Copilot.
3. Довірений MCP endpoint, root-owned socket listener, pinned child process,
   root-manifest/owner-decision/epoch і безпечне створення backend ще не
   підключені в R030. Не можна просто викликати `handle_session()` з live.
4. Відкликання lease зупиняє нову передачу та response delivery, але
   **не доводить зупинку** вже викликаного MCP процесу. R133 kill + pinned
   KernelWitness 1→0 + durable terminal fence потрібні окремо для кожного
   real release/cancellation і після crash/reboot.
5. G1/G2 provider inference vs tool egress, credentials та G3 in-process
   Copilot tools/OS sandbox — OPEN. G5 full ledger/Result lineage — OPEN.

## Operator commands

`make cf10-r135-ipc-session-tests`

`make cf10-r135-ipc-session-source-check`

Не змінювати Hestia, `/etc/sudoers.d/hestiaweb`, чужі systemd units,
`/run`-authority, R122 capsule, prod `tmp/` dependency чи Worker claims.
`tmp/` тільки для передачі ZIP/disposable verification evidence.

### Наступний функціональний proof

Окремий disposable **systemd + root broker + MCP child** E2E на сервері з
незмінним pinned process lineage та R133/R035 terminal quarantine; тільки
після цього — release-readiness review. Не відкривати live cutover від
PASS статичних тестів.
