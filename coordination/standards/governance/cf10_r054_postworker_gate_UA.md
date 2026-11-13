# CF-10 / r054 — post-worker bridge для обмеженого single-owner pilot

## Призначення

Після штатного запуску одного Task70/`worker-01` існуюча консоль та S3
потребують terminal advance. Загальний `governed-worker-cycle-advance` має
спеціальний legacy quarantine (exit 2), який **не можна вимикати** для інших
attempt. r054 додає окремий, точно обмежений Make target, а не новий
оркестратор, dispatcher, Worker чи release-store.

## Докази перед кожним advance

- root та runtime канонічні, EUID=0, Task70 з канонічним ID;
- Git remote HEAD відповідає локальному; усі релевантні source-байти
  відповідають опублікованому Git HEAD;
- r051 root-owned sealed PRECLAIM для точного attempt перевірено;
- r046/r047 незалежний proof lineage перевірено в `LAUNCH_WINDOW`;
- **спожитий** root-owned owner/PAM `O_EXCL` claim має точні поля, SHA-HEAD,
  0600/root, без symlink та дубльованих JSON-полів;
- writer lock є ENFORCED; governed-worker-cycle і S3 погоджуються про
  `READY_FOR_BOUND_POSTWORKER_ADVANCE` та відсутність contradictions;
- `advance` ще раз виконує всі read-only перевірки та викликає тільки
  канонічний `governed_worker_cycle.advance_cycle`. r037 незалежно перевіряє
  Worker Result до terminal ledger. Не виконується ACCEPT/commit/push/publish.

`cf10-s01-pilot-postworker-preflight` — тільки read-only. Він не викликає
production launch. `cf10-s01-pilot-postworker-advance` — **mutating terminal
advance** і тому повинен працювати лише за вже наявних root-owned доказів та
спожитого одноразового claim; ні позитивний preflight, ні параметри Make не є
самостійним дозволом.

## Межі

r054 **не** активує `LIVE_CUTOVER_ENABLED`, не змінює старий Make
`cf10-s01-runtime-launch-preflight`, не створює Task70 attempt і не видає
root proof. Перший launch лишається закритим до окремого source-bound cutover
та успішної перевірки фактичних доказів. Всі `tmp/` artifacts — disposable.
Hestia, sudoers, external backups не входять до scope.
