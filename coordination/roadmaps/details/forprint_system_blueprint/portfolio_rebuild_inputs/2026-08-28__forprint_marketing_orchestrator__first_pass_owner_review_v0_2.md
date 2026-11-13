# ForPrint Marketing Orchestrator — evening first-pass owner review

Module: `forprint_marketing_orchestrator`

Status: `FIRST_PASS_OWNER_DIRECTION_RECORDED / SYNTHETIC_MICROSTEPS_PENDING_SECOND_PASS`

## AGREED_WITH_OWNER

Marketing Orchestrator is not merely a content generator. It is an intelligent closed-loop marketing planner
and campaign orchestrator.

It analyzes current commercial performance and market/channel signals, identifies growth opportunities, proposes
several strategy scenarios (three by default, configurable), executes only inside approved policy, measures actual
outcomes against expected outcomes and learns from the difference.

Difficult analysis/creative questions may escalate to AI assistants and then to a human expert.

## Working boundary

Marketing owns marketing plans, hypotheses, campaign/content orchestration and performance learning.
It consumes trusted sales/margin/customer/product/site facts; it does not invent Accounting, CRM or Website truth.

Its media-generation capability may serve internal instruction-video requests, but operational instruction semantics
remain with Library/Operations Assistant.

## Synthetic roadmap expansion for pass 2

Everything below is `SYNTHETIC_CANDIDATE` unless explicitly described as owner direction.

### MKT-R0 — Trusted data + objective model
- commercial/marketing inputs
- goal/horizon/budget/audience
- brand/compliance constraints
- baseline/success metrics
### MKT-R1 — Opportunity detection
- sales volume/frequency
- margin/value
- seasonality/repeat behavior
- website/search interest
- underperforming/high-potential segments
### MKT-R2 — Scenario generation
- default 3 distinct strategies
- budget/channel/target/outcome range
- risk/assumptions/measurement plan
- rank with uncertainty
### MKT-R3 — Campaign/content model
- campaign/brief/asset/variant/placement
- content calendar
- AI text/image/video provider routing
- prompt/model/cost/provenance
### MKT-R4 — Review/approval policy
- human review thresholds
- autopublish rules by risk/channel
- license/compliance blocking
- budget/stop conditions
### MKT-R5 — Publishing + lead handoff
- channel adapters
- schedule/retry/errors
- lead handoff to CRM
- campaign correlation
### MKT-R6 — Performance analytics
- reach/click/lead/conversion/order/revenue/margin where available
- actual vs baseline/forecast
- attribution uncertainty
- provider cost/quality
### MKT-R7 — Learning loop
- explain forecast gaps
- update audience/channel/product assumptions
- compare campaign families
- retain experiment history
### MKT-R8 — AI/human escalation
- specialized provider first
- AI assistant for hard synthesis
- human expert for unresolved high-impact strategy
- capture correction/learning

## Dependencies

CRM/customer segments/leads, Accounting revenue/margin, Website/search analytics, Library product semantics,
asset storage, external platform APIs/providers and possibly Strategic Control Plane.

## Open questions for pass 2

First channels/slice; autopublish; attribution confidence; budget approval; privacy/consent;
boundary with Strategic Control Plane; internal instructional-media service boundary.

## Target milestone

The module produces measurable marketing experiments tied to trusted facts and improves strategy from actual outcomes.

## Steady state

Continue measured improvement after the target milestone; the module is not considered permanently finished.
