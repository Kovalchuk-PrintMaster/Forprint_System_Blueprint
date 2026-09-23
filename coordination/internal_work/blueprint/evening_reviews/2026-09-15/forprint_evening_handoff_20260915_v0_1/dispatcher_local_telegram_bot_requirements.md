# Local Dispatcher Telegram Bot — Initial Requirements

This is a **small dedicated Telegram bot attached to Dispatcher**.
It is NOT the project's full Telegram module.

## Initial status/menu ideas
- Project status
- Active workers
- Idle/stopped workers
- Failed/blocked workers
- Current task per worker
- Budget/profile/authority summary
- What has this worker completed so far?
- Roadmap progress by module
- Activity over last 24h
- Recent failures
- Dispatcher health
- Nightly/full-check status
- Index/knowledge freshness
- Export structured diagnostic JSON

## Diagnostics
The operator should be able to see:
- who is active;
- who stopped before task completion and why;
- budget exhaustion vs dependency failure vs validation failure;
- abnormal resource use for similar tasks;
- possible index/navigation problems;
- module progress/stalls.

## Remote commands
Start with bounded actions:
- refresh status;
- request diagnostic package;
- retry a failed bounded operation;
- pause/resume when policy allows;
- ask Dispatcher to re-evaluate a task;
- submit operator approval for a requested escalation.

Privileged actions should use an explicit audited break-glass/elevated-operation gate rather than permanent unrestricted Dispatcher authority.

## Notifications
Notify operator on:
- worker blocked;
- retry budget exhausted;
- authority/budget escalation required;
- Dispatcher health degradation;
- serious nightly/full validation failure;
- module/project stall beyond threshold.

## Watchdog
Dispatcher should be supervised by an independent small watchdog/service manager monitoring heartbeat and performing bounded restart/escalation.
