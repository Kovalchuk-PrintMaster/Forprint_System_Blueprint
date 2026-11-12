# CF-10 / AF — Dispatcher API → disposable physical Worker terminal

## Що доведено перед AF

Batch AE (`3025fc83546443bd0145b394fc379b44a61f7bdd`) підтвердив реальний процес `forprint-runner` в systemd, Unix IPC, перевірку синтетичного результату, закріплену delegated leaf cgroup `populated: 1→0`, retained unit, stop/readback і очищення `/run`.

## Нова мета

Одним guarded Make/CLI-маршрутом виконати **справжні існуючі канонічні функції** CF09/CF10:

1. `cf10_training_dispatch.prepare_training_pre_dispatch` для вже матеріалізованого завдання `cf10-verification-tier-self-hardening-v0-1`, з явно disposable empty ledger override під `/run`;
2. `build_training_canonical_ack`, точне **автоматичне дзеркало ACK для репетиції**;
3. `validate_training_assistant_ack` та `authorize_training_explicit_dispatch` лише як неперсистентний API-preview без передачі рішення у production launcher;
4. за умови проходження всіх попередніх меж — **один** `cf10_ae_delegated_kernel_rehearsal_v0_1.run_once()`;
5. суворо звірити task binding, результат та kernel terminal, сформувати evidence із SHA, Git checkpoint, postflight незмінністю 18 локальних змін.

## Заборонені висновки

- Автоматичне echo ACK не є незалежним Assistant ACK/owner approval; виклик API авторизатора у disposable-перевірці не створює справжньої production-authority.
- Ніякого `PAM`, owner claim, durable production attempt ledger, live Copilot inference, provider auth або зовнішнього egress.
- Ніякого дубльованого dispatcher/launcher. R030 та `LIVE_CUTOVER_ENABLED=False` не змінюються.
- `tmp/` використовується лише для доставки пакета, тимчасового Handoff/Task Context та результату; жодної production-залежності. Допоміжний `/run/forprint-cf10-af-*` одноразовий.
- G1–G5 залишаються OPEN незалежно від позитивного результату репетиції.

## Контроль результату

`PASS_CANONICAL_API_DRY_DECISION_TO_PHYSICAL_WORKER_TERMINAL` означає API/physical integration **лише для disposable-репетиції**, не worker result acceptance. Якщо підготовка Handoff, ACK, explicit API preview або фізичний запуск не проходять, статус HOLD, без автоматичного retry. Не маскувати невдале завершення `systemctl` як kernel proof.
