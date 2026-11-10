# CF-10 R140 — Root IPC Broker Adapter, source only

## Призначення

Єдиний bounded root-side adapter над чинними R135 (SO_PEERCRED, cgroup,
MCP-протокол та in-flight revoke) і R126 (root-only durable lab lease).
Підключення до **production launch** не реалізоване. Поточний lease scope —
лише одноразовий `/run/forprint-cf10-r125-*/lease.json`. `tmp/` не є
runtime-залежністю.

## API та межі

- `bind_lab_listener`: тільки після перевірки root, exact invocation/candidate,
  unrevoke lease та parent root:runner `0710`. `mcp.sock` root:runner `0660`,
  `O_EXCL`-подібна семантика (жодного видалення чужого socket).
- `serve_one`: одна root-side сесія, незалежна повторна перевірка kernel peer
  *для backend і client*, результат R135 read-only, lease повністю revoked.
- Помилка/ревокація: `REVIEW_REQUIRED` / `KERNEL_QUARANTINE_REQUIRED`,
  без Worker Result acceptance, ledger append, retry або визнання terminal proof.
- Зовнішній caller має окремо довести, що `trusted_mcp` дійсно належить
  канонічному MCP child; одна лише `SO_PEERCRED` **не доводить** origin.
- Зупинка всієї cgroup — лише R133+KernelWitness. Відкликання lease не
  гарантує припинення in-flight дочірніх процесів.

## Що залишилося до Worker E2E

1. Root-owned producer/broker provenance та held-systemd-gate API (R030).
2. Відповідність нового IPC proxy до канонічного frozen R115 executable
   profile **перед** одноразовим owner claim. Legacy R115 нині його відхиляє.
3. Незалежна інвентаризація ефективних credentials / in-process tools /
   мережевого egress (G1–G3) для pinned Copilot 1.0.107.
4. Після незалежних доказів — контрольна одна нова Worker спроба з повним
   result validation / durable terminalization.

Усі G1–G5 відкриті; жодної live authorization цим комітом не видається.
