# CF-10 Large Batch G — Disposable inference-fixture round trip

## Мета

Після Batch F, який підтвердив виконувану ізоляцію `forprint-runner`, перевірити **реальний запит/відповідь** через один root-controlled Unix socket. Це лише обмежений фіктивний inference fixture, **не** провайдер, не Copilot CLI та не production gateway.

## Канонічні межі

- HEAD-пін, exact diff, regressions, Make і Git checkpoint виконуються guarded installer; один запуск і один evidence ZIP.
- systemd unit створюється тільки як одноразовий `forprint-cf10-batchg-<16hex>.service`, без повторного запуску/лістенера, зі стійкою root-owned source-копією у `/run` **тільки для одноразового лабораторного тесту**.
- У sandbox: `User=forprint-runner`, `PrivateNetwork=yes`, `RestrictAddressFamilies=AF_UNIX`, `IPAddressDeny=any`, закритий HOME і фіктивний файл. Без мережевих з'єднань і справжніх ключів.
- Root сторона перевіряє `SO_PEERCRED`, PID, cgroup, окремий network namespace, effective systemd profile; перший запит на `external.unapproved` відхиляється, другий `fixture.inference` повертає детерміновану відповідь із SHA. Будь-який невідомий route/schema/payload/session відхиляється.
- Стан `systemctl stop` та `MainPID=0` перевіряється після тесту. Це **не** kernel-witness `1→0` і не замінює R030/R133 terminal proof.
- HOLD означає **жодного** Git commit/push і **жодного** повтору disposable unit; зберігаємо архів доказів. Зміни production-service, PAM, Hestia, `/etc/sudoers.d/hestiaweb`, зовнішніх сервісів заборонені.

## Чого цей пакет НЕ доводить

G1 — доступ реального Copilot до inference із контрольованим egress; G2 — безпечне використання реальних provider credentials; G3 — керований реальний Copilot process tree; G4 — live R030 → R140–R145 listener; G5 — pinned kernel `1→0` із terminal ledger. Усі G1–G5 **OPEN**, claim недоступний, live release заборонений.

## Критерій приймання

Контрактні й регресійні тести PASS, read-only Git-перевірки PASS, ефективний disposable source/transport/sandbox roundtrip PASS, зупинка unit підтверджена, Git checkpoint і нормальний fast-forward push PASS. У звіті є лише SHA, стани й `errno`, без секретів і prompt content.
