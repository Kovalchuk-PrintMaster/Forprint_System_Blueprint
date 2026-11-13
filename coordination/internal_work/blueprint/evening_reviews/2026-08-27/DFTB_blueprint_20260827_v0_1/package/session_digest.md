# Session Digest — Blueprint governance evolution, B1→H10

## 1. За одну хвилину

Цей діалог починається після чергового обриву context window у B1-P2 hardening і завершується історичним checkpoint `H10_ACTIVE_CURRENT=true` з Logistics-only automation pilot.

Найцінніше тут — не тільки execution-history, а походження кількох фундаментальних правил проекту: **не ламати нову архітектуру об застарілі правила; значущі рішення та rationale зберігати в репозиторії, а не лише в чаті; не плодити документаційне сміття; roadmap + prompts використовувати як backbone виконання; не вимагати глобально чисте Git-дерево для паралельної автоматизації; manual gate залишати на межі великих фаз, а same-phase Q-кроки робити детермінованими.**

Наприкінці це переходить у формалізований rollout: тільки `logistics_service` підключений до нового automation-validation flow; мінімум 2 реальні успішні automatic prompt runs; потім positive stability review і окреме рішення про розширення.

## 2. Governance має еволюціонувати

Owner прямо формулює правило `IT-BP2708-0002`: нове рішення не повинно штучно підлаштовуватися під старе правило, якщо це правило вже гальмує проект.

Допустимі дії:
- оновити старий документ;
- створити нову ревізію;
- позначити старе як deprecated;
- перевести current authority на новіший опис.

Це керована еволюція, а не хаотичне ігнорування governance.

## 3. Проектова пам’ять — у проекті

`IT-BP2708-0003`, `0004`:
- значущі зміни не залишаємо тільки в chat;
- зберігаємо історію розвитку;
- зберігаємо rationale: чому прийнято конкретний шлях/модуль/архітектуру;
- великі закриті шматки роботи повинні залишати durable evidence.

Це один із найсильніших provenance-пунктів для нашої нинішньої DFTB-роботи.

## 4. Історія без документаційного сміття

Паралельно owner вимагає не плодити зайві директорії та десятки непотрібних проміжних ревізій.

Отже історична модель:
- важливі фінальні рішення — зберігати;
- існуючий документ — логічно доповнювати;
- нова ревізія — коли справді змінився contract/стан;
- current/старша ревізія має бути очевидною;
- проміжний шум не повинен забивати repository navigation.

## 5. Roadmap + prompts

Owner прямо називає roadmap і prompts основними інструментами планування/руху (`IT-BP2708-0006`).

Це означає: chat може бути робочою поверхнею, але durable execution intent має бути винесений у проектні artifacts.

## 6. Script/operator UX

`IT-BP2708-0007`:
- великі скрипти передавати файлами;
- в terminal — лише короткі команди.

У цьому ж діалозі є recurring failure зі stale revisions: спочатку “знову стара версія”, пізніше реально запускається v194 замість v195. Тому artifact identity винесено в окремий risk (`0008`, `0034`).

## 7. Global clean tree більше не масштабується

Owner детально пояснює майбутній режим:
- Blueprint розробляється паралельно;
- module workers можуть виконувати prompts;
- модулі можуть давати роботу один одному;
- тому globally clean tree майже ніколи не буде стабільним станом.

Отже automation не може чекати `git status == clean` для всього світу.

Історичний напрямок: bounded baseline/reference + owned scope + conflict/freshness checks (`IT-BP2708-0009`–`0011`).

## 8. Progression policy

У джерелі є explicit:
- `ACCEPT B2`;
- `ACTIVATE Q2`.

Потім owner змінює policy:
- manual confirmation — на переході між великими фазами;
- Q1→Q2→Q3 та аналогічні маленькі same-phase transitions — без повторного manual token, якщо deterministic gates проходять.

Це `IT-BP2708-0014`, `0015`.

## 9. Fail-closed concept audit

Після concept-audit failure історичний output фіксує `Q2_IMPLEMENTATION_ADVANCE=false`.

Це важливий доказ desired behavior: невдалий mutation/audit не повинен непомітно просунути фазу (`IT-BP2708-0016`).

Concept audit далі пакується для продовження (`0017`).

## 10. Operations Assistant

У portfolio з'являється `forprint_operations_assistant`. Owner вже створює module root і просить перенести concept files із tmp у правильну project structure (`IT-BP2708-0018`).

## 11. UI side branch

У чаті є окремий product-editor/filter UI фронт:
- collapse filters зверху і знизу;
- прибрати background;
- rounded related-product button;
- вирівняти typography.

Я його не викинув, але ownership залишив unresolved (`IT-BP2708-0019`–`0022`).

## 12. Logistics-only pilot

Фінальна pilot semantics цього діалогу:
- тільки `logistics_service`;
- інші модулі не підключені;
- мінімум 2 реальні successful automatic prompt runs;
- positive stability review;
- окреме expansion decision.

Assistant історично звітує, що ця документація опублікована, а H10 current / H11 inactive (`IT-BP2708-0023`–`0029`).

## 13. Knowledge snapshots

Owner просить два різні snapshots:
1. portfolio/module knowledge;
2. Blueprint self-knowledge / repository knowledge / self-analysis.

Module snapshot історично перевірений як 449-file manifest-complete і містить 21 unique module IDs (`IT-BP2708-0026`, `0027`, `0030`, `0031`, `0032`).

## 14. Найважливіші open loops

1. Чи current runtime справді підтримує bounded dirty/parallel-tree execution?
2. Чи rationale/history capture стало формальним closeout requirement?
3. Чи old per-Q manual confirmation остаточно superseded?
4. Чи script/version identity тепер machine-guarded?
5. Кому належить UI side branch?
6. Чи Logistics pilot має реальні 2+ automatic-run evidence?
7. Чи Blueprint self-analysis/knowledge snapshot був далі reconciled у current roadmap?

## 15. Memory anchors

- “Не підлаштовуємо майбутнє під застаріле правило.” → `IT-BP2708-0002`
- “Нічого значущого не лишаємо тільки в чаті.” → `0003`, `0004`
- “Історія — так; сміття з проміжних ревізій — ні.” → `0005`
- “Roadmap + prompts — backbone.” → `0006`
- “Global clean tree не працює для parallel automation.” → `0009`–`0011`
- “Manual gate між фазами; same-phase — deterministic.” → `0014`, `0015`
- “Logistics first; 2 real runs; then review and explicit expansion.” → `0023`–`0025`
- “Знання зберігаємо snapshots окремо для portfolio і Blueprint.” → `0026`, `0027`

## 16. Перші current-audit targets

`IT-BP2708-0002`, `0003`, `0004`, `0008`, `0009`, `0010`, `0011`, `0014`, `0015`, `0018`, `0023`, `0024`, `0025`, `0027`, `0029`, `0032`, `0034`.
