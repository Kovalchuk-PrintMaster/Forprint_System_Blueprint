# Evening review — consolidated summary

## 1. General roadmap/documentation rule

A roadmap must not be only a synthetic architecture description. Concrete examples and production habits stated by the owner in live discussions are requirements and must be preserved in compact form in the roadmap at the relevant step.

The expected pattern is:
1. owner gives a real example;
2. documentation captures the essential behavior in one or two concise sentences;
3. the roadmap connects it to a concrete implementation step;
4. an executor may suggest a better implementation, but must not silently replace the owner intent.

## 2. Report levels

### SHORT
The absolute minimum useful form. The current Prepress Hub sheet is the lower useful bound: role, core capabilities, major dependencies, key open questions. Suitable for orientation, not serious design review.

### BALANCED
The current portfolio working-sheet style: enough context for quick review, but still compact.

### EXPANDED
Human-readable, explanatory and decision-oriented. Internal IDs such as `N10-03`, `GR-03`, `B01-B10`, `runtime business truth`, `authority`, `projection`, etc. must be explained in ordinary language.

Open questions in expanded reports must be accompanied by 2–4 synthetic solution options and a short recommendation.

## 3. New-module policy

Do not create a new module simply because ownership is not immediately obvious.

Preferred order:
1. place the capability into an existing module if cleanly possible;
2. broaden the module role/name if needed;
3. record truly unassigned capabilities in a dedicated decision queue;
4. create a new module only when the capability has a stable, independent domain.

## 4. Central data principle

Persistent business data should not be scattered across module-local folders/databases.

Working principle:

> Centralized managed persistence + domain ownership + explicit write boundaries.

Modules own logic and semantic authority for their domains, but durable data lives in the central data layer or official file/object storage.

## 5. Backup principle

Cloud Backup Manager should protect explicit registered data classes rather than crawl every module for unknown critical files.

## 6. Inspector principle

Project Inspector is a deterministic/rule-driven checker, not an architectural decision-maker. Blueprint decides whether a finding means a module defect, stale standard, roadmap problem or needed remediation.

## 7. Gateway principle

Integration Gateway is the logical contract/control layer for module-to-module communication. It prevents semantic guessing, rejects incompatible requests, detects drift and repeated fallbacks, and provides structured diagnostics.

## 8. Library principle

Library is the canonical semantic/reference source for shared identifiers, aliases, revisions, terminology, dynamic reference values and lifecycle rules.

## 9. Operations Control Registry principle

`Operational Registry` is to be renamed to **Operations Control Registry** with technical ID `operations_control_registry`.

It is the main working candidate for system-wide operational state/control: orders, reserves, shortages, incidents, operational commitments, critical deadlines and active resolution workflows.

## 10. Contract Registry disposition

Separate Contract Registry is not currently justified.

Working decision:
- absorb useful machine-contract functionality into Integration Gateway;
- keep general contract-governance standards in Blueprint;
- use Library for canonical referenced semantics;
- retire/absorb the standalone planned Contract Registry after repository reference reconciliation.

## 11. Identity clarification

ForPrint Identity & Access Service is the centralized authentication/authorization module already conceptually required by Website/Mobile/Calculator/Operations Assistant.
