# CF-10 Batch AD — перша фізична disposable Worker-репетиція

## Мета

Перевірити на s01 окремий непривілейований процес із реальним systemd і результатом,
з прив'язкою до вже наявних канонічних даних Dispatcher:

1. `cf10_training_dispatch.resolve_training_task` знаходить точне training завдання.
2. Існуючий `cf10_first_worker_crossplane_gate_v0_1` перевіряє 11-етапну
   синтетичну узгодженість R129, не надаючи повноважень запуску.
3. Root створює **один disposable systemd unit** `forprint-cf10-batchad-*.service`,
   окремий від production `forprint-cf10-worker-*`.
4. Справжній процес з UID/GID 996:992 посилає HELD; root перевіряє SO_PEERCRED,
   `/proc/<pid>/cgroup`, ефективний systemd-профіль та pinned `cgroup.events`.
5. Root видає одноразовий лабораторний RELEASE, процес повертає синтетичний
   перевірюваний RESULT; root підтверджує SHA256 прив'язки до task/nonce.
6. Після виходу процесу root фіксує `populated 1→0`, перевіряє retained systemd,
   виконує точний stop та readback. При будь-якій втраті доказу — HOLD.

## Чого цей пакет НЕ доводить

- Цей root-side RELEASE — **тільки лабораторний**, не R030/PAM/claim/Dispatcher release.
- Замість AI inference виконано детерміновану синтетичну read-only операцію.
- Немає provider auth, egress, canonical Worker result acceptance, durable ledger.
- Production backend `LIVE_CUTOVER_ENABLED=False` не змінювати.
- Успішна лабораторія **не закриває G1–G5** і не надає нових повноважень.

## Системні обмеження

`tmp/` служить тільки для транспорту ZIP/evidence. Нова source-логіка — у Git.
Робочий каталог `/run/forprint-cf10-batchad-*` одноразовий, не є production
залежністю. Код дитячого процесу копіюється туди лише як disposable fixture.
`/etc/sudoers.d/hestiaweb`, Hestia, існуючі служби та Worker claims — поза scope.
Копіювання та запуск токена провайдера заборонені, навіть якщо він доступний root.

## Стани та наступна межа

PASS цього пакета: фізичний процес і kernel terminal у **disposable** unit підтверджені.
HOLD: один машинний результат, unit не перезапускати; якщо kernel/stop не
доведений — зберегти `/run` для ручного розбору. Наступний фронт —
інтеграція **наявного** R030/PAM/claim та результуючого ledger з реальною
Copilot provider-auth/egress політикою без альтернативного production launcher.
