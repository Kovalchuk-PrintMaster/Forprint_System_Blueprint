# CF-10 Large Batch E — Whole-process runtime cutover envelope

Дата: 2026-11-11. Попередня канонічна Git-база: `05f8d1858c6052862c386b90fef0764b2ec0de31` (успішний Batch D r002).

## Функціональна межа

Єдиний read-only preclaim виконується у вже чинному R030 `review_guarded_ipc_handoff` після перевірки R115→R134. Batch E додає незалежний `cf10_batch_e_runtime_cutover_contract_v0_1.review`, який прив'язує незмінний R013 план, source-locked systemd-профіль, канонічні argv/workspace/attempt/unit, точний IPC candidate та digest R134. Результат — digest-only машинний `runtime_cutover_report_sha256`, стан і відкриті межі. Окремий launcher, root claim, listener, systemd process, workflow DAG, provider credentials або Worker не створюються.

## Поточний стан G1–G5 (блокер live)

1. G1: модель має лише `ForPrintValidation-run_repo_head`, але inference Copilot досі виконується з прямим мережевим доступом. Статичний MCP список не доводить заборону TCP/UDP або інших мережевих функцій процесу.
2. G2: `ProtectHome=yes` і `StateDirectory=forprint-runner` не є самі по собі доказом того, що HOME, кеші, токени, середовище та credential-helper недоступні Copilot і дочірнім процесам.
3. G3: вихідні systemd properties і sandbox argv не є доказами *effective* OS isolation. Необхідний незалежний host runtime proof.
4. G4: R140/R145 — lab-only Root IPC lease; немає продакшн-listener, додаткова лінія авторизації заборонена.
5. G5: kernel `1→0` та durable terminal join потребують доказу. Стан Batch C `ENODEV` не можна автоматично перетворити на PASS.

## Наступний functional milestone

У чинний R030 коридор потрібно вбудувати провайдер-незалежний спосіб надавати Copilot доступ до inference без дозволу загального мережевого egress його процесу або прийняти окремо перевірений ефективний вузький egress; після цього — attested credential compartment, production root listener та terminal kernel join. Поки вони не доведені, жодна статична зміна R115 tool list не може зняти HOLD.

## Операційний контракт

Git HEAD + точний 5-файловий source apply → локальні регресії та проєктний Make/CLI → postcommit source-check → звичайний fast-forward push → один evidence ZIP. Незнайомі dirty target, staged content, Git HEAD/remote drift, altered dependency: fail closed. Не змінювати Hestia, sudoers, системні сервіси, `/run` або production state; `tmp/` — лише ZIP, staging, одноразове evidence. Немає автоматичного повтору Worker-спроби.
