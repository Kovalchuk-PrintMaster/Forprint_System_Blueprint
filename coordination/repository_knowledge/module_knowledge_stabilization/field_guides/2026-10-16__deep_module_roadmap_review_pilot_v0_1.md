# ForPrint — пілот поглибленої інвентаризації модулів та погодження roadmap (v0.1)

**16.10.2026 · REVIEW CANDIDATE · НЕ ЗАМІНЮЄ чинну методологію v0.2.**

## 1. Призначення

Ця процедура виникла під час аналізу Telegram Bot після завершеного L0. Мета — відновити повний життєвий цикл майбутньої розробки всіх модулів ForPrint: історія намірів → реалізація → актуальна архітектура → цільовий функціонал → залежності → робочі пакети → погоджений roadmap. **Це НЕ ремонт, рефакторинг, запуск чи очищення модуля.** Розробники працюють окремо за авторизованими work fronts.

Посилання на чинну процедуру: `coordination/bootstrap/module_analysis_lifecycle_methodology_v0_2.md`; контракт відновлення: `coordination/roadmaps/details/forprint_system_blueprint/portfolio_full_lifecycle_roadmap_reconstruction_contract_v0_1.yaml`.

## 2. Джерела з різними правами довіри

1. Живий стан Git, runtime/тести (що фактично існує, але тест PASS ≠ архітектурне прийняття).
2. Конституція, Blueprint/Human Intent, канонічні roadmap, ownership/contracts (що потрібно і кому належить).
3. Історичні діалоги, DFTB, completion, попередні концепції (чому так замислювали; наявність похідного реєстру ≠ підтверджений оригінал).
4. L0, похідні індекси, аналітичні пакети й контекст-архіви (навігація, не нова authority).

Фіксувати окремо `source_uri/path`, `git_commit`, SHA256 або документний ID, `evidence_type`, `verified_scope`, `confidence`, `not_proven`, `owner`, `next_validation`.

## 3. Повторювана процедура — максимум корисних висновків, мінімум рутинних тестів

| Фаза | Дія | Критерій виходу |
|---|---|---|
| A — Resume | Відновити статус попередніх модулів, HEAD, dirty paths, власників worktree, L0 та попередні версії | Жодного здогаду щодо поточного модуля |
| B — Coarse thematic map | Грубо згрупувати runtime, домен, state, контракти, тести, legacy, історію | 3–5 великих пакетів, не сотні мікроциклів |
| C — Evidence reconciliation | Звірити roadmap, діалоги, Git/тести/runtime, Blueprint/Human Intent, сусідів | Кожна суттєва capability має доказ або невідоме з методом перевірки |
| D — Structural reconciliation | REUSE / EXTEND / ADAPT / REPLACE / NEW; власник даних, дублікати, карантин-кандидати, відкладені рішення | Дублікатні завдання не створюються; історія не видаляється |
| E — Candidate full roadmap | Старі ID та статуси незмінні; доповнити missing links, dependencies, acceptance, failure, rollback, post-release | Від минулого до steady-state існує повний кандидатний шлях |
| F — Owner review | Стисле A4 досьє, картки конкретних owner-рішень, HOLD технічного невідомого | Власник погоджує ідеологію або відкладає з причиною |
| G — Durable checkpoint | Review-only знання + provenance + регістр рішень, owner gate, безпечний вузький commit | Є незалежний доказовий запис; не тільки tmp/chat |

L1-L4 є еволюційними: **не обов'язково вичерпувати весь L3/експериментальний runtime до друкованого review**, якщо питання вже можна сформулювати як технічний bounded discovery для майбутнього work package.

## 4. Поріг зупинки поглиблення (нове правило пілота)

ЗУПИНЯТИ серію нових R0xx-збирачів і готувати погоджувальне досьє, якщо одночасно:

1. Зрозумілий charter модуля, кінцева ціль та owner/non-owner межі — із HOLD для суперечностей.
2. Головні функціональні напрями нанесено на capability matrix, без необґрунтованої обіцянки production-ready.
3. Існуючі кроки roadmap і нові синтетичні кандидати зв'язані; IDs не дублюються.
4. Великі legacy/duplicate/architecture conflicts класифіковано як кандидати, не виконано кодових рішень.
5. Зовнішні контракти та dependency gates нанесено, навіть якщо контракти ще не перевірено.
6. Кожне критичне невідоме має `owner`, тип `OWNER_CHOICE` або `TECHNICAL_PROOF`, перевірку і вплив; відсутні докази позначено HOLD.
7. Повторний тест не може змінити найближче управлінське рішення або суттєво знизити ризик → не запускати його зараз.
8. Є A4 review packet із питаннями, альтернативами та місцем для правок, а provenance доступний окремо.

Якщо пунктів 1–6 не вистачає — один обмежений збір **лише потрібних доказів**, не ще одна тотальна інвентаризація. «Ми не знаємо» є допустимим результатом із маршрутом верифікації.

## 5. Класифікація станів (НЕ нові канонічні стани)

`EVIDENCE_ACCEPTED_COMPLETE`, `IMPLEMENTED_UNVERIFIED`, `PARTIAL_IN_PROGRESS`, `DESIGNED_OR_PLANNED`, `SYNTHETIC_PROVISIONAL`, `BLOCKED_BY_DEPENDENCY`, `OWNER_DECISION_REQUIRED`, `HISTORICAL_SUPERSEDED`, `UNKNOWN_WITH_VALIDATION_PATH`, `STEADY_STATE_EVOLUTION` — це кандидатні planning-проєкції відповідно до portfolio reconstruction contract. Вони не переписують без згоди статуси в module roadmap.

Рішення про код: `REUSE`, `EXTEND`, `ADAPT`, `REPLACE`, `NEW`, а також `QUARANTINE_CANDIDATE` / `RETIREMENT_CANDIDATE` — **лише пропозиції, не зміна реалізації**. Одна можливість може зберігатись у новій архітектурі, навіть коли її старий код є неактуальним.

## 6. Як не втратити історію і не засмітити проект

- `tmp/` — лише тимчасовий робочий простір; важливий підсумок переноситься до версійованого review-only знання.
- У проекті: компактна нормалізована **доказова карта, provenance, owner-review, методика й checkpoint**, а не десятки сирих архівів та генераторів без призначення.
- Великі вихідні ZIP/PDF резервуються окремо з SHA256-індексом. Оригінали не видаються за Git-registered assets без окремої перевірки/публікації.
- Чужі dirty paths — не наш write set. Ніяких `git add .`, `git clean`, `reset`, `stash`, автоматичного commit/push.
- Точні файли, diff, SHA, тести, authorisation і remote containment — окремі контрольні межі.

## 7. Відтворюваний формат підсумку для КОЖНОГО наступного модуля

1. `00_START_HERE` із scope/джерелами/authority/nonclaims.
2. `01_evidence_snapshot` — фактичні версії й зрілість.
3. `02_capabilities` — функціональний каталог, власники, реалізація, acceptance.
4. `03_history_roadmap_crosswalk` — старі steps → реалізоване → майбутні work packages.
5. `04_architecture_dependencies` — власники фактів, inter-module edges, мінімальні unblock slices.
6. `05_unknowns_owner_questions` — розділення owner/value vs technical proof.
7. `06_printable_review` — ясне резюме для людського погодження, без сотень технічних таблиць.
8. `07_review_decisions` — підписаний/протокольний feedback і статус HOLD/APPROVE/REVISE.
9. `08_handoff_to_implementer` — scope й acceptance для наступної помічниці.
10. `source_index` із fingerprint та резервним місцем копій.

## 8. Взаємодія з OC-01, CF-10, діагностикою

Це три **різні контури**. Module Analysis — planning/knowledge. OC-01 — незалежний downstream операторський/асистентський механізм; його не інтегрувати й не підміняти CF-10 без рішення. CF-10 — діючий пілот керованого worker lifecycle; analysis не дає dispatch/accept/push. Діагностика read-only може зібрати HEAD, target availability, status і розмежування власників, але не повинна запускати CF-10 чи OC-01 як side effect.

## 9. Передача асистентці

Почати з `coordination/bootstrap/assistant_context_system_specs_v0_1.yaml`, цього посібника й актуального `coordination/repository_knowledge/module_knowledge_stabilization/snapshots/index_v0_1.yaml`. Не вибирати наступний модуль лише за історією чату. Спершу прочитати реальний registry/HEAD/live state і перевірити включення нового покажчика до результату `make assistant-context-pack`.
