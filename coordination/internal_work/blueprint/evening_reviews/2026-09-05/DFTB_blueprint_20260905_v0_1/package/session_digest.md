# Session Digest — Human Intent, normalization, self-cleaning and Logistics prompt-pull

## 1. За одну хвилину

Цей діалог з'єднує три великі лінії проекту.

Перша — **project memory / Human Intent**. На старті приносяться пакети v1.0 і v1.1 з домовленостями попереднього діалогу. Assistant визначає v1.1 як основний normalized integration package і пропонує не заливати v1.0 вдруге, а зробити residual audit, щоб витягнути лише деталі, які справді загубилися. Це фактично рання версія того самого принципу, який ми зараз використовуємо в DFTB: історичну пам'ять треба зберігати, але не дублювати семантично.

Друга — **масова нормалізація проектної документації та self-cleaning**. Owner бачить, що різні документи/roadmaps описують модулі різними структурами й термінами, і це постійно ламає інформаційний потік. Вирішується: привести документи до спільного стандарту, нормалізувати `SYNTHETIC`/`PROPOSED`, робити bulk semantic review, завести portfolio-wide правила самоочищення, автоматичні conformance checks і список deprecated/removal candidates.

Третя — **канонічний module prompt-pull runtime**. Owner прямо повторює intended architecture: Blueprint публікує prompt лише у власній директорії; module-side listener/assistant читає його, підтягує у свій module flow, запускає fresh AI worker з достатнім context pack, а completion/report повертається назад у coordination flow. Blueprint не повинен напряму пушити prompt у module repo.

Кінець діалогу показує H10 hardening майже на module-pickup boundary: generic health repair працює, released prompt стає `ready_for_module_pull`, prepared buffer лишається 8, release policy повертається fail-closed. Далі виявляється два governance edge cases: Acceptance Oracle binding після release та orphan current governance document без durable inbound reference.

## 2. Human Intent package reconciliation

Початкова ситуація:
- v1.0 — старший/підготовчий package;
- v1.1 — ширший normalized integration package;
- ID-схеми між ними різні;
- просте злиття створило б семантичні дублікати.

Historical decision:
**v1.1 — primary; v1.0 — residual audit / historical evidence.**

Див. `IT-BP0509-0001`, `0002`.

Це дуже важливий provenance для нашої сьогоднішньої роботи: “зберегти історію” не означає “дублювати один і той самий intent у двох ID-схемах”.

## 3. Масова нормалізація roadmap/documents

Owner прямо ідентифікує проблему: інформацію важко рознести по проекту, якщо різні documents описують схожі речі різними headings/structure/status names.

Вихід:
- привести документи до єдиної структури;
- вибрати один status vocabulary;
- `SYNTHETIC` нормалізувати з `PROPOSED`;
- великі набори документів перевіряти batch-wise, семантично.

Див. `IT-BP0509-0004`–`0006`.

## 4. Foreign UI branch виключений

У діалозі є один UI/system-settings фрагмент, але наступним повідомленням owner прямо каже, що попереднє завдання **не нашого модуля** і його треба ігнорувати.

Тому DFTB не перетворює його на requirement. Воно збережене лише як `IT-BP0509-0007 — rejected/foreign scope`.

Це хороший приклад, чому простий keyword extraction був би небезпечним.

## 5. Self-cleaning стає governance capability

Owner хоче не одноразову “чистку”, а постійний capability:
- Blueprint сам підтримує керований стан;
- інші модулі мають таке саме правило;
- descriptive documents перевіряються на стандарт;
- capability видимий в indexes/policies;
- assistants повинні знати про нього.

Це `IT-BP0509-0008`–`0010`.

## 6. Deprecated/stale artifact lifecycle

Окрема ідея — список/registry:
- старих scripts;
- docs;
- modules/files;
- кандидатів на removal/archive.

Після достатнього aging/review obsolete artifact:
- або видаляється;
- або переміщується в historical/deprecated area;
- і не повинен продовжувати брати участь у normal active checks.

Це `IT-BP0509-0011`, `0012`.

## 7. Closeout перед продовженням

Owner окремо просить перед наступним workfront перевірити:
- чи всі зміни реально зафіксовані;
- чи правила потрапили в загальну/модульну інструкцію;
- чи assistants можуть їх побачити;
- чи все проіндексовано;
- чи проект healthy.

Це `IT-BP0509-0013`, `0014`.

Тобто “код/документ змінено” ≠ “governance rollout завершений”.

## 8. Logistics inventory

До діалогу передаються 6 bounded Logistics inventory batches:
1. bootstrap / coordination / docs / config;
2. core source / domain;
3. contracts / examples;
4. tests / fixtures;
5. scripts / tools / maintenance;
6. root / transient / operational inventory-only.

Це `IT-BP0509-0015`.

Таке partitioning корисне для semantic review великих module repositories.

## 9. Canonical prompt-pull architecture

Owner прямо коригує напрямок, щоб не було direct push semantics.

Цільова модель:
1. Blueprint publishes released prompt у Blueprint-owned outgoing/module directory.
2. Module-side listener може **read**, але не write Blueprint.
3. Listener/pickup переносить prompt у module execution flow.
4. На кожен prompt — fresh AI worker.
5. Worker отримує current prompt + previous report + indexes + prompt/report history + roadmap + project/module navigation.
6. Module виконує work package і формує completion/report.
7. Acceptance/RETURN залишається окремим governance transition.

Це `IT-BP0509-0016`–`0022`.

## 10. Generic health / release semantics

u123a/u123b історично показують:
- release працює;
- один prompt стає `ready_for_module_pull`;
- `prepared_buffer=8`;
- refill recommendations порожні;
- release policy після one-shot transaction повертається fail-closed.

Це `IT-BP0509-0023`, `0024`.

Але це historical report, не current verification.

## 11. Acceptance Oracle після release

Виявляється важлива семантична різниця:

Після release bootstrap уже не є `prepared draft`, але його **roadmap Acceptance Oracle binding не повинен зникнути**.

Отже:
`prepared drafts` ≠ `all oracle-bound roadmap steps`.

Це `IT-BP0509-0025`, `0026`.

Цей edge case дуже легко було б зламати “простим” regression test.

## 12. Semantic inbound-reference gap

Після того як generic-health та acceptance-binding tests проходять, validation падає на одному:
`GENUINE_NO_INBOUND_CURRENT_DOCUMENTS`.

Hypothesis: one-shot authorization decision є release evidence під час transaction, але після відновлення fail-closed policy тимчасове reference зникає, а документ лишається current без durable inbound link.

Правильний напрямок:
**не послаблювати semantic validator**, а дати authorization evidence канонічне durable inbound reference.

Це `IT-BP0509-0027`, `0028`.

## 13. Knowledge snapshots

Також сформовані окремі read-only packages:
- Blueprint Self Inventory / System Context;
- Portfolio Roadmap Current State Context.

Це `IT-BP0509-0029`, `0030`.

Вони корисні як portable evidence/navigation, але не повинні заміняти current authority.

## 14. Найсильніші anomalies

1. Human Intent v1.0/v1.1 semantic duplication risk.
2. Fragmented document/schema vocabulary.
3. Project infrastructure entropy without self-cleaning lifecycle.
4. Foreign UI task contamination risk.
5. Direct-push runtime drift versus intended module-pull ownership.
6. Prepared-set vs Acceptance-Oracle-set semantic confusion.
7. Current governance document without durable inbound reference.
8. Дуже мало збереженого assistant-side reasoning.

## 15. Open loops для current audit

1. Чи v1.1 Human Intent package справді інтегрований, а residual v1.0 review закритий?
2. Чи roadmap/document normalization завершена на всьому current portfolio?
3. Чи self-cleaning/deprecation registry і document conformance validators реально існують?
4. Чи prompt-pull flow реально працює end-to-end на Logistics?
5. Чи released prompt правильно зберігає Acceptance Oracle binding?
6. Чи one-shot authorization decision має durable inbound reference?
7. Чи snapshot tooling current і правильно відділено від authority?

## 16. Memory anchors

- “Не merge два historical packages механічно; робимо residual semantic audit.” → `IT-BP0509-0001`
- “Human Intent не повинен дублюватися через зміну ID.” → `0002`
- “Документи/roadmaps приводимо до одного стандарту.” → `0004`, `0005`
- “Project self-cleaning — не разова акція, а governance capability.” → `0008`–`0012`
- “Closeout = docs + policies + index + health.” → `0013`, `0014`
- “Blueprint publishes; module pulls.” → `0016`–`0018`
- “One prompt = fresh worker + previous completion evidence + project navigation.” → `0019`–`0021`
- “Released prompt може вийти з drafts, але Acceptance Oracle binding лишається.” → `0025`, `0026`
- “Semantic validator не послаблюємо — виправляємо provenance reference.” → `0027`, `0028`

## 17. Перші current-audit targets

`IT-BP0509-0001`, `0002`, `0004`, `0005`, `0008`, `0009`, `0010`, `0011`, `0012`, `0013`, `0014`, `0016`, `0017`, `0018`, `0019`, `0020`, `0021`, `0023`, `0025`, `0027`, `0028`.
