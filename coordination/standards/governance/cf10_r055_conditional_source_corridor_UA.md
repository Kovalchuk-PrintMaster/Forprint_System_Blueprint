# CF-10 r055 — Source-bound conditional pilot corridor (Task70 only)

Вводиться окремий Make entrypoint `cf10-s01-pilot-owner-run`, який **не**
змінює історичні `governed-worker-cycle-launch/reconcile/advance` і не
знімає їхній quarantine. Стандартна консоль застосовує r052 до PAM, потім
root-owned O_EXCL claim. r030 і backend **кожен окремо** повторюють r055
перевірки між claim та systemd `_core`.

Лише exact Task70, новий `cf10-u180j-aNNN`, опублікований HEAD, sealed r051
PRECLAIM, чотири root-owned proof records із r046/r047, ENFORCED writer lock,
незмінний frozen input, порожній ledger, quiescent systemd та приватна
після-PAM сесія можуть пройти умовний шлях. Інші завдання й прямі виклики
backend залишаються BLOCKED. `LIVE_CUTOVER_ENABLED=False` — без змін.

**ВАЖЛИВО:** r047 прив'язує байти, але не автентифікує виробника
експерименту. Не можна самостійно виготовити JSON із `PASS` або перенести
позитивний статус вузьких r048/r049 на `TMP_UNAVAILABLE_END_TO_END`. До
операторського запуску потрібно отримати справді виконані, незалежно
переглянуті, exact Task70 доказові матеріали у root-owned store. Сам r055
не видає жодного proof, PRECLAIM, launch receipt і не споживає claim.

Жодний результат локального unit-тесту не є production cutover. Для першого
Task70 необхідне окреме явне підтвердження власника через PAM. Відмова
після claim не дозволяє retry того самого attempt. `tmp/` не є runtime.
