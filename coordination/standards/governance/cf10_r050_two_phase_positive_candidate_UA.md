# CF-10 r050 — двофазний single-owner та позитивний disposable-кандидат

Стан: `SOURCE_NATIVE_NON_AUTHORIZING`. Власник обрав окремий Task70 single-owner pilot; legacy signed-release залишено без змін.

## Проблема та межі

- `r045.collect` може дати позитивний PRECLAIM лише доки Make + backend залишаються у source-quarantine. Після відкриття будь-якого live маршруту її повторний запуск повернув би хибний блокер.
- `r046.inspect` наразі вбудовує `r045.collect`. Тому його нинішній позитивний статус — лише передактиваційний proof candidate, **не** авторизація під час launch.
- `r049` довів crash/recovery fail-closed, проте не створював канонічний Worker Result і не доводив успішний Task70.

## Реалізовано у r050

1. Введено роздільні `PRECLAIM` і `LAUNCH_WINDOW` перевірки. Позитивний PRECLAIM є хешованим *кандидатом*, а не durable root receipt чи дозволом. `LAUNCH_WINDOW` не викликає `r045.collect` повторно; його майбутній довірений виклик має окремо засвідчити PRECLAIM root-owned receipt, актуальний Work Front/frozen input, writer lock, claim, ledger, systemd, PAM, raw proof lineage, джерело Make/backend і незалежний finalizer. Результат **завжди** `launch_allowed=false`.
2. Додано позитивний disposable fixture: реальний `worker_result_return.materialize_worker_result`, справжні `validate_result_envelope` і `validate_resume`, fsynced r035 PRE/terminal fixture records та незалежний r036 `_assess` із канонічними валідаторами. Він повертає `VERIFIED_RESULT_CANDIDATE_PENDING_CANONICAL_LEDGER_FINALIZER`, **не ACCEPT**.
3. Негативні fixture: відсутній terminal proof та підмінений result hash — fail-closed. Повторне створення worker_result.yaml заборонено.
4. Усі durable production roots, PAM, Make launch quarantine, `LIVE_CUTOVER_ENABLED=False`, systemd, Writer та Ledger незмінні. Fixture виконується лише у `/var/tmp/cf10-r035-fixture-r050-*` і автоматично очищується; `tmp/` не є runtime-залежністю.

## Не доведено / окремо залишається

- PRECLAIM ще не виданий у формі immutable root-owned durable receipt.
- Позитивний fixture використовує **синтетичні** source/Handoff, cgroup sample, systemd/service readback та ledger input; це не справжній worker-process/systemd kernel terminal proof і не full E2E.
- Чотири root-owned primary proof та release candidate для точного Task70 attempt **не видані**. `r046` не авторизує запуск.
- Потрібна окрема source-bound Make/backend інтеграція з exact one-shot root receipt, а вже потім новий frozen Task70/attempt. Жодна з цих дій не може випливати з PASS fixture автоматично.

## Машинні команди

`make cf10-r050-phase-requirements` — read-only контракт.

`make cf10-r050-positive-candidate-fixture` — три disposable fixture (positive, missing-terminal, drifted-result), root-only.

`make cf10-r050-two-phase-check` — автономні інваріанти з pytest, без сервісів чи production запуску.
