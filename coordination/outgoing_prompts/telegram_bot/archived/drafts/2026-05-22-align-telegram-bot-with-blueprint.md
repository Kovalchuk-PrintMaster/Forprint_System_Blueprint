# Prompt: Align Telegram Bot with ForPrint System Blueprint

## Target module

`telegram_bot`

## Purpose

This prompt aligns Telegram Bot with the current ForPrint System Blueprint.

Telegram Bot is a customer/operator channel and AI-assisted workflow client. It is important, but it must not become the source of truth or a “god module.”

## Current architectural role

Telegram Bot may:

- communicate with customers;
- collect order information;
- recognize intent/style/sentiment;
- guide the customer through a workflow;
- request missing fields;
- send normalized requests to CRM / Integration Gateway;
- display order status;
- escalate unclear situations to AI or human operator;
- use templates and generation fallback for communication.

## Telegram Bot may use AI for

- unclear customer messages;
- field extraction;
- finding similar past requests, if allowed by contracts;
- preparing draft responses;
- helping operator with scenario interpretation.

But AI-assisted actions should still respect module boundaries and contracts.

## Telegram Bot must not own

Telegram Bot must not be canonical owner of:

- prices;
- material catalog;
- product catalog;
- client registry;
- order registry;
- invoices;
- payment status;
- warehouse stock;
- prepress file truth;
- accounting truth.

## Key architectural risks

1. Bot gets file access and starts directly moving production files without contracts.
2. Bot starts creating orders directly in many places.
3. Bot starts calculating prices internally.
4. Bot starts owning customer/order truth.
5. Bot becomes an uncontrolled AI automation hub.
6. Bot bypasses CRM and Integration Gateway.

## Required alignment actions

Please review the current Telegram Bot implementation and answer:

1. Which parts are pure communication channel?
2. Which parts are workflow state?
3. Which parts are AI-assisted interpretation?
4. Which parts access files or databases directly?
5. Which actions should later go through Integration Gateway?
6. Which actions should be delegated to CRM?
7. Which data should come from Operational Registry?
8. Which current logic risks turning Bot into source of truth?

## Expected deliverable from module assistant

Return a short alignment report:

```text
1. Current Bot role
2. Direct integrations currently used
3. Data Bot owns locally
4. Data Bot should not own
5. Workflows that should move behind Gateway/CRM
6. Safe next steps
7. Open questions for Blueprint
```

## Important rule

Telegram Bot should remain:

channel + workflow client + AI-assisted interface

not:

central backend / database / calculator / accounting system.
