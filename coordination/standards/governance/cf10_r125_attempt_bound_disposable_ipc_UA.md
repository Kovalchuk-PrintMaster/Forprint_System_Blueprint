# CF-10 R125 — attempt-bound IPC і реальний один read-only MCP tool call

Статус: **SOURCE_ONLY_CANDIDATE + DISPOSABLE_S01_PROOF; NON_AUTHORIZING**.

## Незмінні межі

- Існуючий R122 capsule ID, R123 invocation crosswalk, R115/R118 preclaim, owner/PAM, one-shot claim, `cf10_systemd_launcher_v0_1` і `LIVE_CUTOVER_ENABLED=False` не змінюються.
- Немає live Copilot, model inference, справжніх credentials, production systemd unit, нового Worker launcher, canonical ledger mutation, release чи retry.
- `tmp/` тільки для ZIP і disposable machine-evidence; новий source-контракт живе в `scripts/`, але **не викликається** production до окремого source-bound review.
- Лабораторний Unix IPC використовує R119 systemd kernel profile, R121 exact MCP, R122 pinned immutable capsule і R124 доведений Unix socket/SO_PEERCRED маршрут. Допускається тільки один `tools/call` на `run_repo_head` у спеціально підготовленому одноразовому Git-репозиторії з фіксованим registry.
- Після успішної відповіді disposable root-owned lease змінюється на `revoked=true`; наступний `tools/call` тієї самої сесії відкидається до форвардингу в MCP. Це доказ **one-session exhaustion**, а не незалежний external owner/PAM revocation proof.
- `G1–G5` залишаються відкритими; один позитивний readonly call не доводить tool authorization для невідомих Worker inputs, root-to-ledger release, або повну kernel-ізоляцію всього Copilot CLI.

## Критерії перевірки

1. Тести негативних RPC-методів, параметрів, duplicate JSON keys/ids, переповнень, replay, відповідей з невідомою authority.
2. На s01 — фактичний `initialize → tools/list → tools/call(run_repo_head)` під `forprint-runner`, з перевіркою відсутності розширених повноважень, успіху Git і evidence digest.
3. Те саме IPC-з'єднання після root-side одноразового revoke відхиляє наступний `tools/call`; дочірній процес, одноразова lease і transient systemd unit очищені.
4. Source install + канонічні regressions + S01 disposable proof перед exact-file Git commit/fast-forward push; сторонні незбережені файли не чіпати.

## Наступний реальний work front

Перевірка upstream source-bound authorization/epoch і full Copilot tool surface, потім source-reviewed live cutover через **канонічний** owner/PAM + systemd launch + terminalization. Ніякої auto-activation тільки через PASS R125.
