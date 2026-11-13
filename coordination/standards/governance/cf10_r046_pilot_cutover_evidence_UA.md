# CF-10 / r046 — умовний single-owner pilot cutover: технічний proof-bound контракт

**Статус:** кодовий контракт перевірки, **NON-AUTHORIZING**. Цей етап не є cutover, не створює root-owned рішення, не запускає Worker та не підміняє жодних історичних signed-release фактів.

## Навіщо

Після r045 канонічна Task70 та preclaim-факти мають машиночитану перевірку. r046 визначає **строгий формат технічних доказів і прив'язки до одного конкретного нового attempt**, який необхідний для окремого root-owned pilot release. Ми не підробляємо вісім попередніх signed-release proofs і не вводимо другого людського підписанта: source-bound власник залишається одним, технічні перевірки залишаються незалежними від чату.

Перевіряльник: `scripts/coordination/control_plane/cf10_r046_pilot_cutover_review_v0_1.py`.

## Чотири обов'язкові технічні набори доказів

1. `DISPOSABLE_SYSTEMD_CONTROLLER_LOSS_RECOVERY`: реальний disposable systemd/SIGKILL/reconciliation; r039/r040 — важливий попередній матеріал, але не прямий release receipt.
2. `TMP_UNAVAILABLE_END_TO_END`: окрема перевірка без доступності `tmp/` у disposable isolation, не видалення live `tmp/`.
3. `INDEPENDENT_FINALIZER_GATE_FIXTURE`: source-native перехресна перевірка результату, що не приймає недоведений terminal status.
4. `SOURCE_AND_WRITER_BOUNDARY`: frozen HEAD/Work Front, writer lock, одноразовий claim, quiescence і fail-closed перевірки в межах нового attempt.

Докази — окремі звірені JSON з точними type, task, attempt, worker, HEAD, технічним verdict і SHA-256 вихідних записів. Відносні назви визначені source-кодом і містять SHA-256 attempt. Кожен файл повинен бути regular root-owned `0600` у **наявному** root-owned `0700` сховищі `/var/lib/forprint/cf10_s01_single_use`; `tmp/` не використовується як джерело повноважень. Відсутній, підмінений, неоднозначний або суперечливий доказ ⇒ `BLOCKED`.

## Межі після PASS

Навіть чотири перевірені записи означають тільки `PILOT_PROOF_CANDIDATE_VERIFIED_NOT_AUTHORIZED` і `launch_allowed=false`. Необхідно окремо завершити issuer/independent technical review, source-controlled root/PAM gate та канонічне однократне cutover; повторно перевірити exact Task70 attempt перед споживанням claim. Legacy signed 8-proof release і `LIVE_CUTOVER_ENABLED=False` залишаються незмінними. До цього часу `cf10-s01-runtime-launch-preflight` залишається в карантині.

**Штатні entrypoints**: `make cf10-r046-pilot-proof-requirements` (read-only), `make cf10-r046-pilot-cutover-check` (unit tests), `make cf10-r046-pilot-proof-inspect GOVERNED_WORKER_TASK=<...> GOVERNED_WORKER_ATTEMPT=<...>` (read-only, BLOCKED поки proofs не готові).

Підготовку нового Task70 attempt слід виконувати **після** завершення source cutover, інакше новий commit робить frozen source stale та провокує зайві refresh/ACK.
