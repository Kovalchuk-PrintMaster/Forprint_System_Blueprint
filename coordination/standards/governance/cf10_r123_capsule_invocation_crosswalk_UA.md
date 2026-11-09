# CF-10 R123 — source-only crosswalk виклику та незмінної MCP-капсули

Стан: **NON_AUTHORIZING_SOURCE_ONLY**. Після R122 існує перевірена капсула
`git-12c668e0cc30-sha256-5877e4f4e16fefecf16a6e50ea9e9a712d288c7e35fb726b05950226ab416de9`
у `/var/lib/forprint-cf10/runtime-capsules`. Вона містить 427 Git-джерел із
HEAD `12c668e0cc309bd1162154ae12f7281603cf7bfa`.

## Зроблено

- Новий `cf10_r123_capsule_invocation_binding_v0_1.py` використовує **наявний**
  R122 `verify_capsule` (повне SHA/власник/права/склад), R115/R118 статичний
  preclaim і *схему* результату канонічного `invocation_adapter`.
- Звіряє точну капсулу, SHA MCP-джерела у workspace, провайдера, attempt,
  decision, task, work front, JSON MCP, argv SHA, flags, timeout/tool allowlist.
- Формує лише перевірюваний source-crosswalk receipt із digest і явним
  `authority.*=false`; не зберігає prompt, argv або секрети.
- `make cf10-r123-capsule-binding-tests` та
  `make cf10-r123-capsule-binding-verify` — project-native маршрути.

## Що НЕ доведено

Поточний `invocation_adapter` **продовжує посилатися на файл у workspace**,
а не запускає R122-капсулу в ізольованому процесі. Crosswalk не є exec-time
pin; TOCTOU та підміна після перевірки не доведені неможливими. Наявна
R118 перевірка правильно відхиляє безпосередню підстановку шляху `/var/lib`
у Copilot local MCP без нового затвердженого runtime-протоколу.

- **G1:** inference/tool egress не розділено.
- **G2:** модельні credentials/home не доведено ізольованими від in-process tools.
- **G3:** повний kernel policy для справжнього Copilot Worker не доведено.
- **G4:** root-broker epoch revocation відсутній.
- **G5:** release→ledger terminal join не доведений.

Не змінювати `tmp/` на durable dependency; не відкривати HOME/ACL;
не запускати Worker; не створювати дублюючий launcher.

Наступна межа: одноразовий attempt-bound IPC у довіреному системному контурі
із незалежним kernel-bound tool process і реальним broker/epoch/ledger-gate.
Завершений source crosswalk сам по собі НЕ є релізом.
