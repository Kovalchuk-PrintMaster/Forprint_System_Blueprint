# Session Digest — autogeneration, Mutation Compiler, explicit dependencies and continuity stack

## 1. За одну хвилину

Цей діалог продовжує startup-authority cleanup після `u175`, але дуже швидко переростає у глибоке hardening самої інфраструктури, яка генерує знання, змінює Blueprint і передає стан наступному AI-помічнику.

Після завершення continuity-retirement лінії owner просить незалежно перевірити дві речі: наскільки правильно автоматично підтримуються indexes/knowledge repositories і наскільки якісно генеруються current/onboarding documents для нового assistant. Звідси з'являється `u176` audit і далі generator-derivation foundation.

Наступний великий поворот викликають постійні Ruff/syntax failures. Owner прямо каже, що велика частина mutation scripts не доходить до кінця через дрібні lint/syntax defects, і просить сильніший project-aware mechanism, який не просто падає, а аналізує, безпечно виправляє, повторює gates і тільки тоді продовжує. Так виникає історична лінія **ForPrint Mutation Compiler**.

Далі clean-room перевірки відкривають ще глибшу проблему: hidden dependencies. Owner формулює сильне правило — у проекті не повинно бути неявних залежностей; script/function/Make target має або явно вимагати prerequisite, або декларувати його, або мати підтримуваний механізм генерації. Це переходить у execution dependency audits та explicit dependency contract / Make DAG.

Паралельно з'являється operator-UX правило: довгі scripts не повинні мовчати. Progress/status output треба закріпити в policy та launch conventions, щоб наступні assistants автоматично робили так само.

Фінальна третина діалогу збирає повний **continuity stack**:
`persistent micro-roadmap → continuity contract → immutable checkpoint store → generated operational projections → Assistant Handoff Compiler`.
На самому кінці `u179e4` safe-fail звужений до одного schema-path mismatch (`payload.material`), `u179e5` підготовлений/запущений, але final PASS у source не збережений. Після PASS планувався Step 10 — **Lifecycle Enforcement**.

## 2. Startup authority cleanup

Preserved assistant state задає модель:

`AGENTS.md → coordination/bootstrap/START_HERE.md → make assistant-context-pack`

Старий continuity entry:
- не current authority;
- залишається historical/optional;
- generated indexes не редагуються вручну, а rebuild лише після source reconciliation;
- default context broad;
- focused module context explicit.

Це `IT-BP1009-0001`–`0004`, `0031`, `0032`.

## 3. Незалежний аудит автогенерації

Owner просить глибоко перевірити:
- auto index;
- knowledge repositories;
- generated current documents;
- onboarding нового assistant;
- іншу автогенерацію;
- gray zones і неповні derivation chains.

Це `IT-BP1009-0005`.

Після `u176` з'являється окремий generator-derivation foundation registry (`0006`), що історично вказує на потребу machine-readable provenance для generated outputs.

## 4. Mutation Compiler

Проблема:
- mutation scripts часто проходять довгий шлях;
- в кінці падають на Ruff/import/syntax;
- треба робити новий rerun;
- час втрачається не на semantic architecture, а на механічні defects.

Owner просить механізм, який:
1. розуміє проект;
2. компілює/перевіряє mutation;
3. аналізує repairable defects;
4. робить дозволений fix;
5. повторює checks;
6. не обходить gates;
7. rollback/fail-closed лишається обов'язковим.

Це `IT-BP1009-0007`–`0009`.

## 5. Non-mutating checks

Окремий hardening workfront (`u177b`) показує ще одне правило: **check повинен бути check**, а не випадково змінювати проект. Це `IT-BP1009-0010`.

## 6. Hidden dependencies забороняються

Owner дуже чітко формулює maintainability doctrine:

> не повинно бути ситуації, де щось працює лише тому, що випадково десь існує неявний файл/cache/environment state.

Залежність повинна бути:
- declared;
- required/validated;
- або explicitly generated.

Далі workfront проходить:
- dependency closure audit;
- dynamic/sterile clean-room;
- execution dependency contract;
- Make DAG;
- namespace/dependency-order hardening.

Це `IT-BP1009-0011`–`0015`.

## 7. Progress visibility — частина стандарту

Owner просить не просто виправити один script:

- terminal не мовчить;
- видно, що виконується;
- progress/status видно протягом роботи;
- правило записане у policies;
- наступні assistants не повинні кожного разу згадувати про це з нуля.

Це `IT-BP1009-0017`, `0018`.

## 8. Knowledge drift і deterministic caches

Пізніше з'являються workfronts:
- faithful-mirror knowledge index drift probe;
- knowledge pattern runtime cache determinism;
- dependency-order rerun.

Це збережено як `IT-BP1009-0019`, `0020`.

Сенс: generated knowledge має бути відтворюваним із canonical sources, а не залежати від випадкового order/cache residue.

## 9. Continuity stack

### Persistent micro-roadmap
Потрібен machine-readable маленький roadmap поточної execution chain, який переживає заміну assistant (`IT-BP1009-0021`).

### Continuity Contract
Free-form handoff недостатньо; потрібен formal contract (`0022`).

### Immutable Checkpoint Store
Стан до mutation/transition має мати durable checkpoint/provenance і підтримувати rollback (`0023`).

### Generated Operational Projections
Current operational views мають виводитися з canonical state/checkpoints (`0024`).

### Assistant Handoff Compiler
Наступному fresh assistant треба збирати handoff із canonical continuity/dependency/checkpoint/projection state автоматично (`0025`).

Це вже не просто “README для наступного чату”, а фактично компілятор continuity state.

## 10. Safe-fail наприкінці

`u179e4`:
- mutation compiler apply підтверджений;
- unreconciled delta був checkpointed;
- external durable baseline preserved;
- rollback виконаний;
- Blueprint HEAD unchanged;
- projection refresh сам по собі PASS.

Залишкова помилка — validator дивився:
`delta_doc.get("material")`

тоді як canonical schema:
`delta_doc["payload"]["material"]`.

Це `IT-BP1009-0026`, `0027`.

`u179e5` — останній видимий handoff. Final PASS у MHTML немає.

## 11. Наступний declared workfront

Assistant прямо каже:
- ми ще на Step 9 — Assistant Handoff Compiler;
- після PASS → Step 10 **Lifecycle Enforcement**.

Це `IT-BP1009-0028`.

## 12. Найсильніші anomalies

1. Дуже мало assistant-side narrative — лише 2 blocks.
2. Startup authority та generated onboarding/index surfaces вже встигали розійтися.
3. Ruff/syntax failure loop став системною проблемою.
4. Hidden dependencies — critical risk для reproducible automation.
5. Silent scripts — operator observability gap.
6. Knowledge mirror/cache determinism вимагали окремого hardening.
7. Continuity stack сам став складною dependency chain.
8. Handoff Compiler закінчується schema mismatch без preserved final PASS.
9. 51 handoff ZIP — добра chronology, але не current implementation proof.

## 13. Open loops для current audit

1. Чи startup authority/current context сьогодні справді cleanly normalized?
2. Чи `u176` autogeneration audit findings закриті?
3. Чи Mutation Compiler — canonical mutation path?
4. Чи explicit dependency contract/Make DAG реально закриває hidden dependencies?
5. Чи progress visibility enforced?
6. Чи knowledge mirror/cache rebuild deterministic?
7. Чи continuity stack end-to-end працює?
8. Чи `u179e5` пройшов, і чи Step 10 Lifecycle Enforcement потім реально був виконаний?

## 14. Memory anchors

- “Generated indexes не authority: reconcile source → rebuild.” → `IT-BP1009-0003`
- “Аудитуємо не лише код, а й onboarding/autogenerated knowledge.” → `0005`
- “Не падаємо нескінченно на Ruff — будуємо Mutation Compiler.” → `0007`–`0009`
- “Hidden dependencies забороняємо.” → `0011`–`0014`
- “Terminal progress — policy, а не побажання.” → `0017`, `0018`
- “Knowledge mirror/cache має бути deterministic.” → `0019`, `0020`
- “Continuity = micro-roadmap + contract + checkpoint + projections + compiler.” → `0021`–`0025`
- “Fail closed, preserve baseline, rollback.” → `0026`
- “Після Assistant Handoff Compiler — Lifecycle Enforcement.” → `0028`

## 15. Перші current-audit targets

`IT-BP1009-0001`, `0003`, `0005`, `0006`, `0008`, `0009`, `0010`, `0011`, `0012`, `0013`, `0014`, `0017`, `0018`, `0019`, `0020`, `0021`, `0022`, `0023`, `0024`, `0025`, `0027`, `0028`.
