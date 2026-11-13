# Agreements for next workstation session

## Human-readable operator reporting
Never report progress with opaque IDs alone.
Use:
`Dispatcher — integrate governed execution control (CF-09, work u180i)`
instead of:
`u180i ACTIVE`

Apply this to chat status, action results, roadmap/lifecycle summaries, bootstrap material, handoff packs and dashboards.

## Fresh global-assistant bootstrap
Verify that the large bootstrap package for a new chat assistant is generated from live state, not an old cached snapshot.
Fresh package must expose:
- current roadmap cursor;
- lifecycle state;
- resume coordinates;
- current strategic direction;
- human-readable current stage;
- stale-context failure behavior.

Old ZIPs remain immutable snapshots.

## Strategic Vector
Treat Strategic Vector as a persistent mechanism with finite, versioned strategic epochs.
The mechanism persists; each concrete vector has completion/deactivation criteria and can be superseded.
It guides operator/global-assistant focus but does not override the executable roadmap.

## Architecture / Improvement Horizon
Create/formalize a permanent non-executable horizon for promising ideas.
It must preserve candidates without granting execution authority.
Suggested states:
WATCH / ASSESS / TRIAL / READY_FOR_DECISION / ADOPTED / REJECTED / SUPERSEDED.

## Mandatory future Horizon review
Add a roadmap obligation to fully reassess the Horizon after the first sufficiently mature coordinated multi-module operating point.
Also consider lightweight reassessment at major wave boundaries.

## Review Obligations
Design a machine-readable mechanism for things that must be revisited later.
Trigger types:
- time-based;
- milestone/wave-based;
- event-based;
- metric/health-based;
- dependency-change-based;
- strategic.

If full automation is premature, start with a canonical registry + deterministic report.
Later Project Health/dashboard/CRM may render DUE/OVERDUE status, while Dispatcher may prepare but not self-authorize work.

## Separation of concerns
- Roadmap = committed executable work.
- Strategic Vector = directional focus for operator/global assistant.
- Horizon = candidates for later reassessment, no execution authority.
- Review Obligations = things that must be revisited when a trigger occurs.
