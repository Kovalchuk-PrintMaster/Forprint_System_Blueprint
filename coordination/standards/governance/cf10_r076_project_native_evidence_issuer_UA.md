# CF-10 / R076 — постійний evidence/verifier/issuer контур Task70

## Мета

R065–R073 були одноразовими доказовими пакетами; **не використовувати їх як runtime або сценарій відновлення з чату**. R076 переводить R073 verifier + exact-attempt bounded issuer у штатний source (Make/CLI), зберігаючи первинні архіви в уже наявному root-owned 0700 store поза `tmp/`.

R076 не запускає Worker, не видає signed release, не змінює глобальний cutover, не дозволяє automatic retry/acceptance/publish. Оригінальні байти R073 перевіряються за фіксованими SHA-256; підміна/пропуск/невідповідна форма ZIP — BLOCKED.

## Відокремити історію від нової спроби

Історичні a050/a051 + disposable R071/R072C належать **попередньому HEAD і a053**; вони не підтверджують реальний Worker на майбутньому HEAD. У R072 finalizer перевірений у fixture з ізольованими залежностями. Незалежної криптографічної автентифікації виробника цих артефактів НЕМАЄ. Це прямо вказано в R076 dossier, тексті PAM, source raw records scope=DISPOSABLE_NON_AUTHORIZING і human review. Чистий hash не доводить особу виробника.

За наявності нової спроби issuer повторно перевіряє **фактичні** source/published HEAD, frozen Handoff, PRECLAIM, ledger, systemd, writer, R052/R046 та **actual R075 frozen manifest gate**. Лише після operator PAM, повторної перевірки поточних умов під owner lock і байтів історичного архіву записує точно 9 R046/R047 documents + dossier + human review та копії чотирьох історичних ZIP з явним походженням. Всі нові raw source мають точний новий attempt/head, історичне походження в dossier/review не приховується. Створення `O_EXCL`, fsync; неповне виконання — no cleanup/no retry.

## Штатна операторська карта (жоден пункт не потребує чат-команди)

1. `make cf10-pilot-evidence-history`: root-only, read-only, незалежне повторне звірення історичних архівів R073 у durable store; можна виконувати до підготовки нової спроби.
2. `make cf10-pilot-resume ...`: використати чинну preparation/ACK/dispatch/PRECLAIM процедуру під її власними PAM та no-retry guards.
3. `make cf10-pilot-evidence-inspect ...`: **до owner claim**, тільки для нової готової спроби на опублікованому HEAD, read-only.
4. `make cf10-pilot-evidence-issue-once ...`: окремий явно підтверджений PAM; створення 11 root-owned записів і архіву; no Worker, no claim.
5. `make cf10-pilot-operator-doctor ...` і `make cf10-pilot-plan ...`; далі окремий `make cf10-pilot-launch-once ...` із власним PAM, лише якщо всі умови відповідають.
6. Після Worker — канонічний readback/S3 `cf10-resume`, без повторного запуску того самого attempt.

Звичайні змінні: `GOVERNED_WORKER_TASK=cf10-validation-check-pipeline-profile-and-optimization-v0-1`, `GOVERNED_WORKER_ATTEMPT=cf10-u180j-aNNN`. Для `cf10-pilot-evidence-history` ці змінні не потрібні.

## Відновлення

- `CONSUMED_NO_RETRY`, навіть `ledger=0`: заборона другого запуску, незалежний root/systemd/ledger/receipt review; a053 назавжди у карантині.
- `HEAD_DRIFT`, `PROOF_ARCHIVE_SHA_INVALID`, `R052 gate=false`, `source dirty`, `preclaim missing`: зупинити, не витрачати claim.
- Окремий proof-candidate навіть з `R046 PASS` **не є дозволом** на автоматичний старт, новий HEAD або production release.
- `tmp/` лише delivery. Жоден source-native Make/CLI, service, proof reader не залежить від цих ZIP у project/tmp.
- Працювати з неповним R076 root-issuance тільки шляхом ручного безпечного розслідування; інсталятор/issuer не видаляє записи.

## Межі

Поки не було інтегрованого production Worker test на новому HEAD, не стверджувати, що він PASS. Описані історичні fixture-тести дозволяють **лише обмежений одноосібний пілот після свідомого рішення оператора**, не заміняють незалежний аудит або криптографічну автентифікацію. Hestia та `/etc/sudoers.d/hestiaweb` не змінювати.
