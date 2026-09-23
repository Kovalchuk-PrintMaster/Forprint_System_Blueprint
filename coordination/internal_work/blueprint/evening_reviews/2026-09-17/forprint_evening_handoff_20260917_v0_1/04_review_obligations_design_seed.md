# Review Obligations — design seed

A Review Obligation is stronger than a reminder.

It says:
“This subject must be reassessed when condition X occurs, using evidence Y, and is not satisfied until completion criteria Z are met.”

Suggested fields:
- review_id
- title
- subject_ref
- reason
- trigger_type
- trigger_spec
- review_window
- required_inputs
- required_evidence
- completion_criteria
- owner
- scope
- severity
- state
- last_reviewed_at
- next_due_at
- result_disposition

Suggested result dispositions:
NO_ACTION / WATCH / REVIEW_NEXT_WAVE / CREATE_WORK_FRONT / PROMOTE_TO_ROADMAP / SUPERSEDE / SATISFIED

Initial use cases:
- re-check module stability one week after repair;
- reassess Horizon after a wave;
- review a changed dependency boundary;
- review repeated retry/failure telemetry;
- revisit Strategic Vector at epoch end;
- periodic architecture-risk review.

Preferred architecture:
canonical obligation registry → Project Health projection → dashboard/CRM/calendar → optional Dispatcher work preparation.
UI is not source of truth.
