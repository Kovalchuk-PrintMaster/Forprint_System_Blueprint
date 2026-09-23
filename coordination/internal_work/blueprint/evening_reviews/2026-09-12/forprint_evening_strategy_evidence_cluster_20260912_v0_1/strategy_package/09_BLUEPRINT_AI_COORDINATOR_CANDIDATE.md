# Blueprint AI Coordinator — candidate

Стратегічна ціль: **human-governed, AI-operated control plane**.

Не створювати одного “вічного” AI з власною пам'яттю. Persistent intelligence = project state + contracts + graphs + history + health. AI = тимчасовий fresh reasoning process.

Фази:
1. SHADOW — читає state, дає candidate рішення, нічого не змінює.
2. COPILOT — оператор вручну дає prompt/файл; AI готує patches/tasks/results, significant mutations підтверджуються.
3. BOUNDED_OPERATOR — low-risk deterministic mutations через approved choke points, self-check і focused tests.
4. AUTONOMOUS_ROUTINE_COORDINATOR — routine coordination/dispatch у межах approved wave, exceptions escalated.
5. HIGH_AUTONOMY_BY_CAPABILITY — лише після статистично стабільної роботи; blast radius може залишати high-impact дії на нижчому рівні.

Human-retained: mission, priorities, constitution/core authority, breaking/subtractive decisions, autonomy promotion, high-risk exceptions, зміни власних guardrails control plane.

Не дозволяти `propose -> mutate own guardrail -> validate itself -> declare pass` одному actor-у.
