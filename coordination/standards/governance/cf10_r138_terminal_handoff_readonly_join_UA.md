# CF-10 R138 — канонічний terminal handoff: read-only root/ledger join

## Місце в lifecycle

R137 на s01 підтвердив disposable реальний `worker_validation_mcp.py` → root IPC R135 → зовнішній R126 revoke → kernel 1→0. Це **не** був Copilot Worker і не використовував канонічний root claim або terminal ledger.

R138 зв'язує **наявний** R030, а не створює новий launcher: після R035 `record_terminal()` (штатне завершення) чи успішного R133 `quarantine()` (скасування) викликається один новий read-only join. Він перевіряє:

- R013 точні attempt/head/baseline/handoff/unit та invocation;
- R035 root-only immutable PRE і, лише для успіху, POST із прив'язкою invocation + PINNED_KERNEL;
- R015 root-only claim/event chain;
- R020 узгодження root claim із єдиним канонічним записом Execution Attempt Ledger `STARTED/PENDING`, перевіреним його контрактом і hash filename;
- для скасування — останні `QUIESCENCE_OBSERVED_CANDIDATE` і `REVIEW_REQUIRED`, **без** R035 terminal POST.

R138 повертає тільки `ROOT_TERMINAL_READY_FOR_INDEPENDENT_RESULT_VERIFIER` або `QUARANTINE_REVIEW_REQUIRED_NO_TERMINAL_LEDGER`, де `result_accepted=False`, `terminal_ledger_written=False`, `release_allowed=False`, `automatic_retry=False`. Наявність kernel zero не прирівнюється до успішного Worker Result; `STARTED/PENDING` не terminalize сам собою. Помилка будь-якого з незалежних читань — HOLD і ручна звірка, не retry.

## Незмінні межі

- R030 source-gate і Owner/PAM перевірки не відкриваються; `LIVE_CUTOVER_ENABLED=False`.
- R126 lease лише disposable, немає production socket listener/real Copilot MCP wiring.
- Не створювати новий claim, Worker, stop, network, credentials, terminal-ledger append або дозвіл на наступну задачу.
- G1–G5 залишаються OPEN: незалежний Worker Result verifier, credentials/egress/G3 і остаточна terminal append/review ще не доведені.
- `tmp/` — винятково доставка пакета та disposable тести, **ніколи production dependency**.
- Hestia, зовнішні systemd units, `/etc/sudoers.d/hestiaweb` не змінюються.

## Source-only операторський контроль

`make cf10-r138-terminal-handoff-tests`

`make cf10-r138-terminal-handoff-source-check`

R138 — невелика, але реальна інтеграція *у* R030 із fail-closed перевіркою, яка стане активною лише після окремого governed live-допуску. Пріоритет наступного етапу — G1–G3 для обмеженого Copilot 1.0.107 та **окремо незалежний Worker Result verifier + guarded fact-only terminal append**, а не нові provider-specific механізми.
