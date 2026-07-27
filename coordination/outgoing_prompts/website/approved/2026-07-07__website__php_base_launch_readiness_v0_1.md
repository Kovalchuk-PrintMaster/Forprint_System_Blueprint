# Prompt: ForPrint_Web_Site_Base — PHP Website Launch Readiness v0.1

## Working directory

`/srv/software_development/forprint-project/forprint_website/base`

## Assistant working name

`ForPrint_Web_Site_Base`

## Purpose

You are working with the existing ForPrint PHP website.

This is the current/base public website implementation. It was originally built from a tutorial-style PHP online shop project and is already partially implemented.

Your first task is not to rewrite the website.

Your first task is to inspect, understand, document and prepare a safe launch-readiness plan.

## Strategic boundary

This website may become an early public lead-capture and local SEO channel.

It may be used for:

- public business presence;
- local search visibility;
- basic product/service presentation;
- contact forms;
- simple requests;
- early advertising landing pages.

It must not become the canonical owner of:

- ForPrint product catalog;
- Calculator Engine pricing rules;
- global clients;
- orders;
- payments;
- stock;
- accounting;
- 1C data.

Future architecture should treat the website as a channel:

```text
Website -> Integration Gateway -> Operational Registry / Calculator / Library

For now this is only a boundary direction, not a required integration.

First task

Inspect the existing codebase and produce a report.

Do not rewrite the project.

Do not deploy to production.

Do not connect production services.

Do not commit secrets.

Inspect and document

Check and describe:

project structure;
PHP version assumptions;
database type and schema if available;
config files;
secrets handling;
.gitignore;
public web root;
routing/pages;
admin area;
product/catalog logic;
cart/order/request logic;
forms;
uploads;
sessions/auth;
dependencies;
assets;
current incomplete parts;
obvious risks.
Security review

Pay special attention to:

hardcoded credentials;
SQL injection risks;
missing input validation;
admin access protection;
password handling;
session handling;
upload safety;
exposed config files;
PHP error display settings;
file permissions;
backup needs;
HTTPS requirement;
spam protection for forms.
Expected output

Create a clear launch-readiness report with:

what exists now;
what works;
what is incomplete;
what blocks public launch;
what is safe to launch;
what must be fixed first;
minimal deployment checklist;
recommended next prompt.
Development rules

Use small, safe steps.

Prefer Makefile/check targets if they exist.

If no project checks exist, propose a minimal check workflow before implementing it.

Do not perform large refactors.

Do not delete existing code without explicit approval.

Do not add real production credentials.

Do not publish the site without explicit approval.

Completion format

Return:

summary of inspected files/directories;
findings;
blockers;
proposed next steps;
questions for owner/Blueprint.
```
