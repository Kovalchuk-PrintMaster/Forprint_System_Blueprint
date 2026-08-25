# ForPrint Operations Assistant — concept v0.2

## Working module identity

`forprint_operations_assistant`

The name remains provisional but accepted for current planning.

## Strategic role

Unified internal operational assistant and lightweight human-to-system interaction surface for the
physical print shop.

Its core loop is:

`PLAN → OBSERVE → RECORD → COMPARE → INFORM`

It is not the autonomous owner of accounting truth or business policy.

## Primary value

Reduce the effort required for employees to:

- understand what should be done;
- record physical-world events;
- follow standard procedures;
- report exceptions;
- access instructions/templates;
- confirm operational facts;
- receive contextual help.

Humans often act as sensors/observers. Their observation should be captured as structured evidence,
not silently converted into accounting truth.

## Interaction direction

Prefer low-friction interaction:

- QR codes;
- one-tap buttons;
- minimal typing;
- contextual forms;
- role-aware views;
- workstation/mobile-friendly web UI.

QR identifies context, not authority.

## Operational work

Potential capability areas include:

- production task visibility;
- workstation/station events;
- acknowledgment/timeout/fallback events;
- schedule/health visibility;
- warehouse observations;
- stock/receipt observations;
- rework/waste capture;
- QC capture where useful;
- ready-for-pickup/ready-for-delivery observations;
- physical location/container QR workflows.

Business lifecycle state, operation state and schedule health should remain conceptually distinct.

## Knowledge Library & Guided Forms

This is a first-class capability, not a generic "help" button.

A universal entry point (working UI label: `FP Assist`) should allow an employee on any workstation to
quickly access:

- corporate instructions;
- text procedures;
- video procedures;
- standard document templates;
- role-specific knowledge;
- guided forms with field-level explanations;
- examples/checklists;
- export into approved corporate formats.

### Guided-form example

A newly hired manager needs an order/application form.

Instead of opening a bare Excel template, the employee opens a guided version where every field
explains:

- what to enter;
- expected format;
- business meaning;
- common mistakes.

After completion, the assistant exports/saves the approved clean company document without helper
text.

The same pattern can serve:

- manager;
- designer;
- warehouse worker;
- accountant;
- production worker.

## Knowledge growth

The knowledge library should grow continuously because much operational knowledge currently exists in
the owner's personal experience.

Content can include:

- "how to inventory paper";
- machine/workstation procedures;
- standard quality checks;
- packaging/handling instructions;
- software/process guidance.

## Reminder/schedule integration

The assistant may remind employees of planned procedures such as inventory or checks and provide the
relevant instruction at the moment of work.

## Integration principles

The assistant should consume authoritative plans/data from owning modules and return structured
observations/events.

It should not become:

- canonical accounting storage;
- universal business decision maker;
- CRM replacement;
- catalog truth owner.

## Future device interaction

Where local workstation/device actions are required, use a constrained Device/Endpoint Agent model
rather than arbitrary remote shell authority.
