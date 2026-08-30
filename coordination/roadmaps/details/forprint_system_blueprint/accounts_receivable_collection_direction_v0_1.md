<!-- Integrated from Evening Architecture Package v1.0 on 2026-08-30. This document does not change release/H10 authority by itself. -->

# 03. Payments & Accounts Receivable Collection v1.0

Primary owner: `forprint_accounting_registry_service`.

Supporting:
- `forprint_crm`
- `telegram_bot`
- `forprint_operations_control_registry`
- `forprint_integration_gateway`

## Receivable model

```yaml
invoice_id: ...
order_id: ...
customer_id: ...
organization_id: ...
amount_due: ...
amount_paid: ...
due_date: ...
payment_status: ...
overdue_days: ...
promise_to_pay_date: null
collection_state: ...
```

## Payment preference/order start

CRM/Accounting determine whether customer uses:
- prepayment;
- postpay/contract;
- invoice with VAT;
- another allowed policy.

New client without known preference can be asked via Telegram.

Payment reconciliation comes from Accounting + bank/integration evidence.
If payment is detected even without payment slip, order is updated and customer
is informed.

## Collection state machine

```text
DUE
→ OVERDUE_SOFT
→ OVERDUE_REMINDER
→ PROMISE_TO_PAY
→ WAITING_PROMISED_DATE
→ OVERDUE_ESCALATED
→ HUMAN_ATTENTION
```

Side states:
- DISPUTED
- PARTIAL_PAYMENT
- PAYMENT_PENDING_RECONCILIATION
- CONTACT_UNAVAILABLE
- PAUSED
- PAID

## Dialogue policy

Tone:
- friendly;
- polite;
- non-threatening;
- persistent;
- contextual.

Cadence configurable by:
- days overdue;
- amount;
- customer history;
- promised date;
- dispute state;
- customer tier;
- communication availability.

Не зашивати одну універсальну формулу 1/2/4 messages per day.

## Structured extraction

«Оплачу в п'ятницю»:
```yaml
promise_to_pay_date: Friday
```

«Бухгалтер буде в понеділок»:
```yaml
next_action_at: Monday
```

«Ми вже оплатили»:
→ payment reconciliation request.

«Не згодні з сумою»:
→ DISPUTED + pause normal reminder escalation.

## AI boundary

AI може адаптувати wording, аналізувати діалог, уникати повторів.

AI не може самостійно:
- списати борг;
- змінити credit limit;
- заблокувати customer;
- заборонити відвантаження;
- визнати payment без reconciliation.

## Audit history

Зберігати:
- sent reminders;
- customer replies;
- promises;
- due-date changes;
- dispute events;
- reconciliation;
- state transitions;
- timestamps/source.
