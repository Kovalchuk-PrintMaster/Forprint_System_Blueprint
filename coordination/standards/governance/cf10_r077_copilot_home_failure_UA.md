# CF10 R077 — Copilot HOME / StateDirectory

Джерело: a054 (HEAD f7f7f4dd), одноразовий claim спожито, ledger STARTED/PENDING, R035 PRE є, TERMINAL нема. Systemd завантажив service, ExecMainStatus=1; stderr: `ENOENT mkdir /var/lib/forprint-runner/.cache`.

На хості HOME існує: `/var/lib/forprint-runner`, uid=996, gid=992, mode=0700. `.cache` відсутній. Раніше `ProtectSystem=strict` та `ReadWritePaths` обмежували запис лише workspace/logs, `StateDirectory` був порожнім.

## Обмежений контракт

`StateDirectory=forprint-runner` + `StateDirectoryMode=0700` дозволяють доступ до exact HOME, не розширюючи глобальний `/var/lib`. Зберігаються `ProtectSystem=strict`, `ProtectHome=yes`, runner uid/gid, заборона привілеїв і решта unit props. Перед claim: root-only read-only inode, UID/GID, mode, symlink та property preflight. Відсутність `.cache` сама по собі не є blocker, бо HOME має бути створюваним/записуваним у namespace systemd.

**Не робити висновок про виконання Worker із факту STARTED**. a054 — незворотна, non-success, no retry. Не створювати від її імені terminal success або Worker Result.

### Що ще не доведено

Це source contract. Він сам не доводить фактичні mount namespace та автентифікацію Copilot CLI. Перш ніж витрачати claim нової спроби, потрібен окремий одноразовий disposable sandbox/provider startup proof без задачі Worker та незалежна оцінка lifecycle a054. Немає production/legacy cutover.

`tmp/` — лише доставка. Hestia та sudoers не чіпати.

### Disposable namespace probe

`make cf10-pilot-provider-home-probe` через `systemd-run --wait --pipe --collect` створює **лише disposable тестову службу**, перевіряє HOME й право створити `.cache` із UID=996, mode=0700; видаляє тільки власний ephemeral probe-файл. Залишається `.cache`, якщо був відсутній. Не виконує Copilot чи Worker, не читає секретів, не створює ledger або receipts. `--version` Copilot/credential probe — окрема умова до наступного claim.
