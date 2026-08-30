<!-- Integrated from Evening Architecture Package v1.0 on 2026-08-30. This document does not change release/H10 authority by itself. -->

# 04. Order Execution, Job Ticket, Stop-Work & Training v1.0

Primary integration owner: `forprint_operations_control_registry`.

## 1. Order creation

Calculator produces canonical order/job specification.

Downstream:
- create operational order;
- request material reservation;
- resolve payment policy;
- initiate invoice/payment communication;
- calculate execution eligibility;
- generate Job Ticket.

## 2. Execution gates

```text
READY_FOR_PRODUCTION
HOLD_PAYMENT
HOLD_MATERIAL
HOLD_APPROVAL
HOLD_CLARIFICATION
HOLD_PREPRESS
```

Contract/postpay customer may become READY immediately.
Prepay customer remains HOLD_PAYMENT until payment confirmed.

## 3. Queue views

Operations Assistant:
- ready for production;
- waiting for payment;
- waiting for material;
- waiting for customer;
- waiting for management approval;
- waiting for prepress;
- in production;
- ready for pickup/delivery.

## 4. Job Ticket

Paper ticket = physical projection, never source of truth.

Fields:
```text
order_id
order_revision
generated_at
customer/organization
product
quantity
deadline
priority
materials
operations
special instructions
current state
QR/short code -> live digital order
```

If printed revision is stale, scan must detect it.

## 5. Print routing and permissions

Default printer priority list + fallback.

User with proper permission can select another printer.

Owners:
- System Administration — device registry/routing/health;
- Identity & Access — group/user allow/deny/overrides;
- Operations Assistant — UI/consumer.

## 6. Contextual work instructions

Assistant knows:
- order;
- operation;
- machine;
- material;
- current step;
- employee role.

It returns canonical instructions:
1. text;
2. photos/schemes;
3. animation;
4. real video.

ForPrint Library/reference layer stores canonical SOP/media metadata.

New employee scenario:
«Я не розумію, що робити з цим замовленням».

Assistant explains:
- what order is;
- current stage;
- next action;
- how to do it;
- expected correct result;
- cautions;
- escalation option.

## 7. Critical Order Event

States:
- STOP_WORK_REQUIRED
- CANCELLED_BY_CUSTOMER
- EMERGENCY_HOLD

High-priority event bypasses normal queue.

Minimum recipients:
- current executor;
- direct supervisor;
- department head/director according to org structure.

Alert:
- distinct audio;
- visual;
- reason/current operation;
- mandatory action;
- acknowledgement.

No acknowledgement in configured time → escalation.

## 8. Hard execution lock

Every production action checks current operational state.

Before:
- operation start;
- generated machine command/script;
- operation finish/handoff;
- transfer to next section.

QR identifies order; it is not permission.

If blocked:
```text
do not start
do not generate automatic command
show/voice STOP
```

If cancellation happened during operation:
- record actual partial/completed operation;
- block next operation;
- do not hand off;
- record current physical location/state;
- create supervisor disposition obligation.

WIP record:
```yaml
order_id: ...
operation_id: ...
location_id: ...
quantity_state: ...
stopped_at: ...
stopped_by: ...
reason: ...
```

Disposition is manual/authorized:
- scrap;
- retain;
- rework;
- repurpose;
- give to customer;
- transfer;
- other.

Financial consequence handled separately by Accounting.
