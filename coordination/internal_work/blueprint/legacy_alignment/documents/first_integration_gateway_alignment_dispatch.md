# First Integration Gateway Alignment Dispatch

## Purpose

This document records the approved alignment dispatch from ForPrint System Blueprint to the ForPrint Integration Gateway module.

## Target module

forprint_integration_gateway
Approved prompt
coordination/outgoing_prompts/forprint_integration_gateway/approved/2026-05-22-align-integration-gateway-with-blueprint.md
Why Integration Gateway goes after Calculator, CRM and Library

Integration Gateway goes after Calculator, CRM and Library because the first reviewed modules confirmed several important boundaries:

Calculator should not become a general backend.
CRM should send workflow/execution commands through Gateway.
Library defines canonical contracts and schemas, but does not execute runtime business flows.
Customer channels must remain channel-agnostic for Website, Telegram Bot and future Mobile App.

Gateway now needs to define the safe transport/validation/routing boundary between these modules.

Manual action

Open the approved prompt and paste it into the ForPrint Integration Gateway module chat.

Expected result from the module assistant:

Module Alignment Report
Where to save the response

After receiving the Integration Gateway alignment report, save it here:

coordination/incoming_requests/forprint_integration_gateway/new/YYYY-MM-DD-forprint-integration-gateway-alignment-report.md
After response is saved

ForPrint System Blueprint should:

Review the alignment report.
Confirm Gateway boundaries.
Define request/response envelope.
Define validation error model.
Define correlation_id and idempotency_key rules.
Define first routing rules.
Update Blueprint YAML/Markdown if needed.
Update prompt dispatch status from approved to reviewed.
Create follow-up prompt if needed.
Important rule

This dispatch does not authorize building a complex runtime bus yet.

The goal is to define a minimal, explicit and safe integration boundary before modules become directly tied