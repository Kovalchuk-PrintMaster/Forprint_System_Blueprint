# CF10 / R133 — Fail-closed post-release quarantine у єдиному R030

**Мета:** після `backend.launch_after_owner_claim()` та root-release не залишати
невизначений Worker процес без адресної операції зупинки, якщо canonical
`witnessed_terminal()` або durable `record_terminal()` не пройшли.

## Reuse — жодного нового launcher

- **R030 уже має** `KernelWitness.arm` у STARTED callback, до root release;
  `r035.record_pre` фіксує це до ledger STARTED, а `witnessed_terminal`
  і `r035.record_terminal` виконуються після Worker. R132 раніше показував
  `NO_DIRECT_ARM_CALL_FOUND` лише тому, що дивився на backend без R030.
- Новий R133 лише опрацьовує **помилку після release**, не дублює arm чи
  happy-path terminal та не змінює R115/R127, provider argv, owner/PAM.
- Канонічний модуль R030 делегує новому невеликому quarantine helper тільки
  коли backend уже повернув release, але `r035` durable terminal ще не записано.
- Тільки точний unit `forprint-cf10-worker-<24 hex>.service`, root,
  справжній тип `KernelWitness` із збігом unit/invocation та pinned FD.
- Перед kill — `systemctl show` exact unit + retained `InvocationID`, cgroup, runner identity.
- `systemctl kill --signal=SIGKILL` (systemd default: усі процеси unit) для одного unit;
  `KernelWitness.wait_zero()` підтверджує 1→0. Це **не** успішний Worker.
- Існуючий append-only R015 receipt отримує лише `QUIESCENCE_OBSERVED_CANDIDATE`
  або `QUIESCENCE_UNPROVEN`, потім `REVIEW_REQUIRED`.
- Відсутня service/kernel/receipt ознака -> `HOLD`, без retry, terminal
  success, acceptance чи автоматичної повторної авторизації.
- Якщо `r035.record_terminal` уже успішний, не спрямовувати retained
  unit на kill: далі існує спеціальна `R030._retire_after_durable_terminal`.

## Докази та залишкові межі

Isolated tests тільки моделюють виклики та перевіряють фактичну AST-функцію
`R030.run_once`; вони не підтверджують реального systemd/cgroup на s01.

Після R133 G1/G2/G3/G5 лишаються OPEN, R115 усе ще відхиляє новий proxy,
а R126 lease лише лабораторний. Реальний forced cancellation canonical unit
не підтверджений; необхідне контрольоване випробування із дозволом та з
окремими негативними умовами. Жодного live Copilot, PAM, credential,
root claim, cgroup-test чи production запуску цей пакет не виконує.

`tmp/` — лише доставка ZIP / disposable evidence. Hestia, sudoers, сторонні
systemd units і production не змінювати. Рекомендована перевірка:
`make cf10-r133-post-release-quarantine-tests`.
