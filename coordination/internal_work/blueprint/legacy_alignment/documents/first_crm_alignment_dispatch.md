# First CRM Alignment Dispatch

## Purpose

This document records the approved alignment dispatch from ForPrint System Blueprint to the ForPrint CRM module.

## Target module

forprint_crm
Approved prompt
coordination/outgoing_prompts/forprint_crm/approved/2026-05-22-align-crm-with-blueprint.md
Why CRM goes after Calculator

ForPrint CRM goes after Calculator Engine because Calculator alignment clarified the quote/calculation boundary. CRM now needs to be aligned as the business orchestration layer and human dashboard without becoming the physical owner of all operational data.

CRM has high architecture impact because it may accidentally become:

all-in-one backend;
operational registry;
accounting registry;
dashboard plus database plus workflow engine;
hidden replacement for Integration Gateway.
Manual action

Open the approved prompt and paste it into the ForPrint CRM module chat.

Expected result from the module assistant:

Module Alignment Report
Where to save the response

After receiving the CRM alignment report, save it here:

coordination/incoming_requests/forprint_crm/new/YYYY-MM-DD-forprint-crm-alignment-report.md
After response is saved

ForPrint System Blueprint should:

Review the alignment report.
Detect whether CRM is drifting toward monolith behavior.
Clarify what belongs to CRM and what belongs to Operations Control Registry.
Clarify what belongs to Accounting Registry.
Update Blueprint YAML/Markdown if needed.
Update module guide if needed.
Update prompt dispatch status from approved to reviewed.
Create follow-up prompt if needed.
Important rule

This dispatch does not authorize large CRM refactoring.

The goal is to clarify CRM boundaries before implementation grows too far.