# CF-10 / Batch AA — аудит критичного шляху до першого реального Copilot Worker

**Дата огляду:** 2026-11-11. **База:** `b7555e4ca4269815ffc2cc7ca44154aa73a5e70d`. **Статус:** source-only hardening, без live-дозволів.

## 1. Обсяг і чесна межа перевірки

На доступному GitHub-зрізі інвентаризовано **3655 tracked files** (приблизно **887 `.py`**, 1369 YAML і 1080 Markdown). Переглянуто вихідний код критичного CF-10 ланцюга: `invocation_adapter`, `provider_session_proof`, `structured_command_executor`, R079, R115, R134, R140, R141, R143, R145, systemd launcher/kernel witness/terminal bridge, worker result, W/X, Batch Y та їхні контракти. **Це не є доказом ручного прочитання кожного з 3655 файлів.** Для повного автоматизованого аналізу tracked Python на s01 цей реліз додає AST-аудитор. Його знахідки — кандидати на ручну перевірку, а не автоматично доведені дефекти.

Отриманий Batch Y evidence підтверджує після встановлення **471 pytest PASS + 60 subtests** та **74 окремі тести**; Git commit/push і збереження 18 локальних модифікацій. Ці цифри належать вибраним наборам, не всій системі ForPrint.

## 2. Два конкретні недоліки, виправлені в цьому пакеті

### A. Дублювання і слабший executable pin у Y

`cf10_first_worker_operator_doctor_v0_1.py` використовував `lstat() → open(path) → lstat()`. Файл міг бути замінений між stat та open. Канонічний R115 уже реалізує відпрацьовану перевірку через `O_NOFOLLOW`, file descriptor, `fstat` до/після, точний SHA-256/розмір, права власника та parent-control. У Batch AA Y-doctor переведено на **наявний R115**, а не на третю власну реалізацію.

### B. Credential handle metadata — перевірявся лише безпосередній parent

Стара `inspect_auth_handle()` дивилася `lstat` кінцевого файлу і одного батьківського каталогу. Вона не забезпечувала незалежну перевірку всього шляху без symlink traversal. Новий `cf10_first_worker_secure_metadata_v0_1.py` проходить каталог за каталогом через `openat`/`dir_fd`, `O_DIRECTORY|O_NOFOLLOW`, перевіряє root owner/права, а кінцевий credential file **не відкриває і не читає** — тільки `stat(...,follow_symlinks=False)`. Вимоги: root:root, режим 0600, один hardlink, приватний root-parent. Заборонені `/tmp`, `/var/tmp`, `/run`, `/dev`, `/proc`, `/sys`, repo `tmp/` та project-root paths.

Окремий guard виявляє також **порожні** token-variables за самою наявністю ключа у середовищі. Наявність `0600` credential handle все одно **не доводить** валідність авторизації, nor non-exposure from CLI tools.

## 3. Виявлені архітектурні межі (не називати PASS завчасно)

| Компонент | Доведено | Не доведено / практична наступна дія |
|---|---|---|
| R079 | Source-only provider-neutral selection | Live migration of prepare→ACK→dispatch→result; не вводити паралельну реалізацію для Claude/Codex |
| R115 | Frozen executable/argv/source preclaim | Legacy direct-network check не є proof для brokered namespace; окремий явний режим потрібен, не вимикайте старий gate |
| R134 | Read-only crosswalk до IPC candidate | Жоден IPC argv не авторизований live release |
| R140 | Root-owned MCP broker, lease/revoke/peer checks | **Не** inference egress proxy; не додавати provider token в його MCP session |
| W / X | UID 996 IPC, deny-only routing, HTTP CONNECT → root-side synthetic TLS | Немає дозволеного provider hostname, реального upstream, auth injection чи модельної відповіді |
| systemd launcher | Governed sequence з `LIVE_CUTOVER_ENABLED=False` | Не перемикати bool без повних G1–G5 independent proofs |
| KernelWitness / terminal fence | Retained-unit fixture kernel 1→0 у Batch L, terminal-coherence checks | Той самий доказ для **реального Worker attempt** і durable terminal ledger не існує |
| Y doctor | Metadata-only binary/handle/readiness | Не створює provider login і не надає прав на Worker claim |

## 4. Найвищі практичні ризики

**P0 — credential non-exposure.** Передача токена в `GH_TOKEN` чи `COPILOT_GITHUB_TOKEN` самому Copilot CLI **не доводить**, що child-tools, MCP та subprocess не успадковують секрет. Не виконувати реальний `-p` з таким токеном у production без незалежного proof. При звичайному opaque CONNECT HTTPS root proxy не може автоматично вставити Authorization header усередину зашифрованого upstream; рішення про спосіб auth має спиратися на фактичний протокол CLI, а не припущення.

**P0 — реальний egress.** Не переносити fixture allowlist `fixture.forprint.invalid` на живі домени механічною підстановкою. Потрібні точні destination policy, DNS/address binding, TLS hostname verification, root-only egress logs без secrets, direct-worker IPv4/IPv6 DENY, revocation semantics і незалежна перевірка, що реальний CLI користується тільки цим маршрутом.

**P0 — canonical attempt terminal.** Test unit kernel 1→0 ≠ Worker terminal. Потрібні same-attempt InvocationID/cgroup, pinned FD доки group populated=1, спостережений `1→0`, retained state, stop readback, незалежна валідація result і append-only ledger. При ENODEV чи втраті witness — HOLD/QUARANTINE, не PASS.

**P1 — dirty source governance.** 18 наявних локальних правок не є free-to-reset. Цей пакет прив'язаний до конкретного HEAD/source blobs/dirty fingerprint. При зміні бази потрібне узгодження, не `git reset --hard` і не `stash`.

**P1 — джерела виконання.** Temporary ZIP, `tmp/` і одноразова Python-програма — лише доставка/інсталяція/evidence. Новий production import або systemd path ніколи не посилається на `tmp/`.

**P2 — noise management.** Скрипти й регресії вже довели transport. Не повторювати без потреби лабораторії Copilot `--version`/TLS. Наступна корисна функція — реальна provider auth/egress injection + live attempt boundary, не новий fixture.

## 5. Що робить source-аудитор

`cf10_repository_risk_inventory_v0_1.py` читає Git-tracked `.py` без мережі, парсить AST, рахує Python/синтаксичні проблеми, підсвічує кандидати `shell=True`, динамічний `eval/exec`, небезпечне завантаження та випадково розширений `LIVE_CUTOVER_ENABLED`. У звіті тільки `path`, `line`, `finding_code`, severity і агрегати. **Немає сирого коду, секретів, змін репозиторію або автоматичного виправлення.** Фіксуються лише статичні сигнали; динамічні та системні ризики потребують окремих runtime proof.

## 6. Acceptance / rollback

Новий canonical Make target: `make cf10-first-worker-security-inventory-check`. Він виконує тести безпечних шляхів, інвентаризатора, Y critical path/doctor і source checks. Одноразовий інсталятор перевіряє точні Git blobs, проектний Python, старі 18 dirty hashes, регресії до/після, read-only doctor, автоінвентаризацію Python, затемнений evidence, точний Git staged scope та fast-forward push. HOLD до commit: відновлює лише власні файли; після commit помилки push локальний commit зберігається для reconcile, **без повторного запуску**.

## 7. Подальша робота одним великим функціональним пакетом

1. Реалізувати один (не паралельний) root-controlled provider auth/egress mode з окремим доказом того, що credential bytes недоступні Worker child tools і MCP. Якщо архітектурно неможливо без модифікації CLI, зафіксувати це як технічну межу, а не замовчувати.
2. Реальний pinned Copilot inference smoke в інтегрованому namespace з перевіркою proxy, TLS та response, без розширення R115/claim до proof.
3. На основі отриманого proof — атомарно приєднати до канонічного frozen preclaim/release, не створюючи нового launcher чи другого MCP broker.
4. Kernel 1→0, ledger, result crosscheck і terminalization для того самого attempt.
5. Лише після незалежного terminal review перейти до наступного Worker; автоматичний retry спожитого claim заборонений.

**G1–G5 залишаються OPEN після Batch AA.** Цей файл — технічний огляд і навігація, не source of execution authority.
