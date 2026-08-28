# Evening review guide — portfolio microstep pass v0.3

Ціль вечірньої розмови: не реалізація, а предметне погодження функцій, меж і мікрокроків.

Для кожного модуля проходимо однаково:
1. Чи правильна кінцева бізнес/операційна роль?
2. Що модуль canonical owns, а що має лише читати/викликати?
3. Які roadmap phases потрібні насправді?
4. Які мікрокроки залишити, відкинути, перенести, об'єднати або додати?
5. Які dependencies повинні бути готові до старту конкретного кроку?
6. Де потрібна людина/approval?
7. Який test/evidence доводить завершення?
8. Чи не створюємо дубль іншого модуля?
9. Чи є capability, який ніким не owned?
10. Що має бути наступним dependency-ready slice після погодження?

Окремо тримаємо список DEFERRED/DISPOSITION:
- Operational Registry
- Contract Registry
- Production Runtime Inspector
- Warehouse Service (ймовірно потрібний, але disposition формально ще відкритий)

Identity & Access Service — PROPOSED_NEW_MODULE, owner-agreed concept, не runtime-active.

Design System — cross-cutting shared capability, не окремий постійний module executor.

Не змінюємо ввечері:
- current.yaml authority;
- H10 Logistics-only boundary;
- automatic business/module ACCEPT/RETURN/HOLD;
- Knowledge Foundation activation.
