# CF10 r045 — Bounded Single-Owner Pilot Admission Candidate

**Статус:** `PRECLAIM_EVIDENCE_CANDIDATE_NON_AUTHORIZING` або `BLOCKED_PRECLAIM_EVIDENCE_NON_AUTHORIZING`. Це машинний огляд перед запуском, **не реліз, не дозвіл запуску та не підміна підписаного незалежного release**.

Це продовження r044. Canonical owner: `scripts/coordination/control_plane/cf10_r045_pilot_admission_v0_1.py`. Використовує наявні `cf10_training_dispatch`, `governed_worker_cycle`, `cf10_owner_pam_launch`, `execution_attempt_ledger`, `execution_attempt_writer_lock`, r044 design-review. Повторного claim/ledger, другого оркестратора або нового авторитетного state-store немає.

## Штатні команди

- `make cf10-r045-admission-inventory` — read-only визначення рівно однієї задачі з канонічним `training_order=70`.
- `make cf10-r045-admission-check` — ізольовані негативні тести admission.
- `.venv_blueprint/bin/python -B scripts/coordination/control_plane/cf10_r045_pilot_admission_v0_1.py inspect --root . --task-prompt-id <CANONICAL_TASK_ID> --attempt-id <NEW_ATTEMPT_ID>` — read-only перевірка вже підготовленого attempt. У протоколі Task70 означає **порядок 70 у канонічній черзі**, а не довільний текст у назві.

## Вимоги кандидата (не повноваження)

Успішна перевірка вимагає: опубліковану й незмінену critical source; чинний r044; канонічну Task70; стан `READY_FOR_WORKER_LAUNCH`; frozen source; чинний writer lock; root-owned state directory; не спожитий одноразовий claim; відсутність ledger-записів для нового attempt; відсутність активного CF10 systemd-unit; збереження чинних карантинів і legacy signed-release semantics.

Перевірка **не встановлює** root-claimed launch token, не виконує PAM, не створює claim, не стартує systemd, не змінює ledger, `tmp/`, Git чи будь-який production state. `launch-preflight` завжди повертає exit 2, навіть якщо всі preclaim факти позитивні.

## Що залишається окремим етапом

1. Незалежний технічний огляд **нового** bounded pilot cutover без імітації 8 старих human-release proofs.
2. Контрольований disposable systemd gate end-to-end з kernel/readback/recovery proof; недоведений результат → BLOCKED. Production Task70 запускається лише після окремого cutover.
3. Наскрізний `tmp/`-unavailable proof у disposable isolation (без видалення live `tmp/`).
4. Одноразове явне operator рішення для конкретної задачі й attempt, після source-pinned rebind.

**Жодного нового Task70 не запускайте r045-пакетом.** До окремого погодженого cutover не змінювати `LIVE_CUTOVER_ENABLED=False` і `cf10-s01-runtime-launch-preflight`.
