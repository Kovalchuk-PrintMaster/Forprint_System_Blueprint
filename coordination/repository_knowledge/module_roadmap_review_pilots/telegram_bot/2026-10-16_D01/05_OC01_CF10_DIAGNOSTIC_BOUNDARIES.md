# Read-only діагностика й архітектурні межі: module analysis / OC-01 / CF-10

**Важливо:** тут тільки відомості з контекстного знімка Blueprint `bfeb799…`, Makefile з того знімка й операторських логів. Живий стан OC-01/CF-10 **НЕ ПЕРЕВІРЕНИЙ цим пакетом**.

| Контур | Роль | Відоме | Що перевіряємо | Чого НЕ робимо |
|---|---|---|---|---|
| Module Knowledge / Roadmap | Відновлює функції та план | L0 Telegram, R002–R010, D01 | read-only completeness, assistant context link | не патчити Telegram і не виконувати work front |
| Diagnostics / Project Inspector | Фіксує repo conformance, evidence | Inspector не підміняє owner acceptance; Runtime Inspector окремий | лише джерела/standards, які зараз діють | не проводити acceptance від імені Inspector |
| OC-01 | downstream операційний assistant/terminal/sandbox lifecycle | Makefile містить `oc01-session-projection-check`, `oc01-console-check`, `oc01-mini-closeout-check` та інші targets | окремо git status/owner, make-target presence, scoped safe validation за власним операторським дозволом | не інтегрувати в CF-10, не запускати protected terminal/promotion apply |
| CF-10 | внутрішній governed worker цикл | операторський git status показує значний паралельний dirty write-set | окремий owner, HEAD, dirty inventory, failure/blocked ledger, task checkpoints | не робити add/commit чужих файлів; не запускати dispatcher/worker |
| Google Drive Backup / Website Preview services | зовнішні незалежні сервіси | поза CF-10/Blueprint scope за попередньою домовленістю | не перевіряються тут | не чіпати/не приєднувати |

## Мінімальний діагностичний знімок перед окремим комітом цього пакета

- `git rev-parse HEAD`, `git status --short` та `git diff --name-only` — **без `git add`**.
- Verify `assistant-context-pack` builder присутній, сам результат архіву перевірити семантично.
- Presence/owner of OC-01 and CF-10 target files/Make targets; точних status чи PASS не вигадувати.
- Записати `NOT_CHECKED`, `SOURCE_PRESENT`, `CHECK_PASS`, `CHECK_FAIL`, `BLOCKED_BY_FOREIGN_DIRTY_STATE` окремо.

### Команди, які НЕ включено до автоматичного діагностичного виконання

`make oc01-protected-terminal-run`, `make oc01-promotion-apply`, `make oc01-sandbox-seal-result`, CF-10 dispatch/launch, `make check-fix`, `git reset/clean/stash`, `git add .`, `git commit` та `git push`. Навіть «read-only» Make таргети слід звірити з актуальним Makefile перед запуском на dirty дереві.

## Живий діагностичний результат

Генерується окремим **невиконувальним** `module_analysis_boundary_probe_v0_1.py` у цьому пакеті. Відсутність інформації = `NOT_CHECKED`, не `PASS`. Результат з `tmp/` додається до precommit-review, але не є автоматично новим фактом канонічної roadmap.
