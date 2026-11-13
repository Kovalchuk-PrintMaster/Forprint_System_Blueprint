# CF-10 · R090 — Codex binary lineage та offline `exec --help`

База `c951bef0e2238ea3322a4779ced3e6d546e7be89` (R089). Точний source-only крок: не встановлює/змінює Codex, не викликає systemd у source-інсталяторі.

Після R089 користувач зафіксував інсталяцію офіційного Codex CLI 0.166.0 та успішний offline `--version`: `/usr/local/bin/codex` з SHA-256 `b8a11fedf24b2dfb59a70c9e52b030f9a508dcd49cd2dd0d41956f4c785156b8`, durable receipt `/var/lib/forprint-provider-provenance/codex_r089_v0_166_0_install.json`.

## Дві незалежні дії

- `make -s cf10-codex-lineage-attest`: **read-only** перевіряє R088 inventory, root-owned regular binary `0755`, незмінний SHA, root-owned durable receipt `0600` у root-private `0700` каталозі, точний вміст R089 receipt з source HEAD та Git ancestry. Не запускає CLI або мережу. Верифікація receipts є перевіркою цілісності в межах довіреного root-хоста, а **не незалежним криптографічним підписом OpenAI**.
- `make -s cf10-codex-offline-exec-help-probe CF10_CONFIRM_CODEX_HELP_PROBE=PROBE_CODEX_EXEC_HELP_OFFLINE_NO_WORKER`: опційний ручний запуск `codex exec --help` в **одноразовому systemd** з R088 `CODEX_HOME` у приватному RuntimeDirectory, `IPAddressDeny=any`, `User=forprint-runner`, `ProtectSystem=strict`, без stdin, без секретів і без task/model invocation. Висновок — тільки факт реклами прапорців R087, SHA та розмір `--help`; не evidence виконання і не authorization.

Список параметрів R087 для read-only огляду: `--json`, `--ephemeral`, `--ignore-user-config`, `--ignore-rules`, `--sandbox`, `--model`, `--cd`. Якщо один із них не рекламований у `exec --help`, це **REVIEW_REQUIRED**, а не підстава пробувати його через Worker. `--help` теж не доводить підтримку фактичного task execution.

R090 не має права запускати Worker, видавати claim, авторизувати ACK/dispatch, змінювати Registry READY або автентифікацію, пересоздавати/підміняти R089 receipt, змінювати PAM, systemd-постійні юніти, R037, Hestia чи сторонні зміни в Git. Джерела production не залежать від `tmp/`.

Не повторювати source installation після staging/commit. CLI probe допускається **лише окремим явним операторським рішенням** після source commit і read-only attestation.
