# CF10 R082 — зафіксований вибір виконавця перед ACK

R082 зв'язує новий attempt із конкретним провайдером/моделлю, версією каталогу,
HEAD/fingerprint джерела і Handoff SHA. Детермінований запис виникає у
`prepared_execution` до ACK; ACK мусить зберегти його дослівно.

Dispatch перевіряє вибір повторно. Ідентифікатор рішення включає SHA
зафіксованого вибору. Перед канонічним launch-cycle вибір перевіряється вдруге,
ще до Worker invocation. Зміна source під час pre-ACK refresh вимагає нової
спроби замість тихого перевибору провайдера.

**Межі R082.** Поточний пілот лишається тільки `github_copilot_cli/auto`.
Додаткові `READY`-провайдери Registry не означають право запуску. Немає
автоматичного fallback, провайдера не можна змінити після prepare.
Історичні decision без нового поля залишаються тільки Copilot-legacy, жодні
історичні receipts/ledger не змінюються. `a054` залишається
`CONSUMED_NO_RETRY`, `STARTED/PENDING`, без підтвердженого terminal.

Це source-bound SHA-контроль, а не незалежний криптографічний підпис оператора.
Реальний вибір Codex/Claude і credentials, capability attestation, remote-job
executor та незалежний terminal/result залишаються окремими етапами.
