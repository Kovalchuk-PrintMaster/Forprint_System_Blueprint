# CF10 Large Batch D — канонічна source-only конвергенція preclaim (R115→R134→R030)

## Функціональний результат

1. **R115** без виконання розпізнає тільки точний read-only proxy-MCP:
   `ForPrintValidation-run_repo_head`. У модельному списку немає `view`,
   `edit`, `apply_patch` чи довільних MCP; команда, argv, interpreter, cwd,
   immutable attempt, source head, epoch, capsule й socket-підпис source-bound.
2. **R134** бере актуальну історичну frozen invocation, формує майбутній argv,
   перевіряє точний R115 read-only IPC shape і зв'язує sha256 з кандидатним
   R127 документом. Це **не** root lease чи ефективна OS-атестація.
3. **R030** надає `review_guarded_ipc_handoff` для source-only звірки з
   канонічним R013 `BoundedInput`/plan. Він *не* змінює `run_once`, не
   запускає Worker і не створює альтернативного launcher.
4. Чинний production `R115.assert_pilot_preclaim` **явно блокує** навіть
   точний read-only IPC preview до незалежного закриття G1–G5.
5. `R129.SOURCE_BLOBS` оновлено до точного git-blob нового R115, щоб зберегти
   канонічне джерельне pinning після Git checkpoint (без dual-allowlist).

## Незмінні guardrails

- `LIVE_CUTOVER_ENABLED=False` в чинному системному launcher.
- G1 credentials, G2 effective tool isolation, G3 inference/tool egress,
  G4 actual root lifecycle, G5 independent acceptance/terminalization — OPEN.
- `tmp/` лише доставка/одноразовий evidence; жодного production dependency.
- Немає systemd/PAM/claim/credentials/Copilot/network mutation, auto-retry.
- Hestia, сторонні systemd/backup сервіси й чужі staged/dirty файли недоторканні.

## Наступний функціональний бар'єр

**G1–G3 effective proof та незалежний root runtime integration** до будь-якого
Copilot E2E; kernel `ENODEV` з Batch C досі HOLD, а не PASS. Наступний пакет
має давати працюючий контрольований whole-process egress/credentials policy,
а не інший аналог IPC proxy. Жоден report тут не містить позитивної release authority.

## Оператор

Після guarded installer: `make cf10-batch-d-ipc-preclaim-review` —
тестова ревізія source контрактів; не здійснює Git чи live-операцій.
