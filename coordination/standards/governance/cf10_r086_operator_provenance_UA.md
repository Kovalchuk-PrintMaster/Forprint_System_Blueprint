# CF-10 R086 · Operator Selection Provenance

Базовий Git HEAD: `d1033757787c751664bebef1a43ad7b2a1fee942`.

Окремий операторський R085 prepare зберігає `cf10_operator_assignment_preview_sha256` у `prepared_execution`. R086 відтворює R084 preview з довірених Work Front, Task, frozen HEAD, fingerprint, R082 provider selection та поточного Registry, перевіряє SHA і забороняє підміну.

На Assistant ACK R086 відхиляє вставлення, втрату чи зміну цього поля. Перед explicit dispatch перевіряє digest та копіює його у **хешовану частину decision binding**. Після dispatch перед записом рішення перевіряє повну відповідність. На canonical preclaim та launch виклик виконує R083 epoch gate і повторно перевіряє R086, до будь-яких PAM/claim/systemd дій.

Звичайний проектний `prepare` без операторського preview залишається у чинній Copilot-only гілці; R082/R083 source epoch та provenance/authority не послаблюються. Історичні спроби не переписуються. SHA — перевірка цілісності та відтворюваності **за довіреним джерелом**, не цифровий підпис і не grant.

R086 не додає Codex/Claude executor, не перевіряє provider credentials, не відкриває multi-provider dispatch, не створює claim, не виконує Worker та не змінює R037 finalizer. `tmp/` не є runtime-залежністю.

## Make/CLI

- `make -s cf10-operator-provenance-tests`
- `make -s cf10-operator-provenance-inspect`

Жодних команд запуску чи підготовки Worker у цьому пакеті немає.
