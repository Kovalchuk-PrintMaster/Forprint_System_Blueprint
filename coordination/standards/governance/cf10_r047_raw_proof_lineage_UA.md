# CF-10 / r047 — доказове походження технічних pilot proofs

**NON-AUTHORIZING / source-controlled.** Після r046 поле `source_evidence_sha256` перевірялося лише як SHA-256-подібний текст. r047 додає фактичне читання байтів первинного машинного результату через існуючий root-owned `0700` store і `O_NOFOLLOW`, `root:root`, `0600` reader r046. Немає нового root store, жодного issuer, claim, PAM, запуску, commit Worker чи release.

## Обов'язкова перевірка

Для кожного `proof_<attempt-key>_<proof-type>.json` повинен існувати точно названий `raw_source_<attempt-key>_<proof-type>.json` у `/var/lib/forprint/cf10_s01_single_use`. Хеш **справжніх байтів** другого файлу повинен збігатися з `source_evidence_sha256` у першому. Далі незалежний Python-verifier звіряє точні identity поля `source_head`, `task_prompt_id`, `attempt_id`, `worker_id`, non-authorizing scope, заборону retry/production Worker та визначені для кожного типу технічні спостереження. Надлишкові, неповні або false свідчення відхиляються. Відсутній raw файл ⇒ `RAW_SOURCE_NOT_AVAILABLE` і r046 status BLOCKED.

Наявність правильно сформованого JSON *не доводить сама по собі*, що disposable експеримент справді відбувся або що його результат незалежно атестовано. Ідентичність виробника та фактичне виконання процедури ще мають бути доведені під час окремого bounded source-bound proof-run / issuance. Цей крок закриває лише реальне зв'язування первинних байтів і запобігає прийняттю довільного рядка SHA як джерела доказів.

## Контрольний порядок

1. Дійсний `HEAD` та точний Task70 attempt; source freeze слід виконати **після** code cutover, але **до** одноразового release і запуску.
2. Фактичні disposable/systemd/tmp/finalizer/preclaim experiments від source-controlled runner — ще не реалізовані в r047.
3. Independent outcome validation і root-owned atomic issuance чотирьох raw/proof записів — окремий наступний крок.
4. `r046.inspect` тепер блокує відсутні/підмінені raw evidence, а навіть `PILOT_PROOF_CANDIDATE_VERIFIED_NOT_AUTHORIZED` не дозволяє launch.

**Не запускати Worker** й не вважати наявні r039/r040 synthetic/non-authorizing logs release receipts. **Не чіпати** `tmp/`, Hestia, сторонні systemd units, signed-release, operator claim, canonical ledger, dirty unrelated files.
