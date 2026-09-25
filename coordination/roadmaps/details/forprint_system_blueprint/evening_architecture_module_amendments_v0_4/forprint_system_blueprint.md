# ForPrint System Blueprint — deterministic worker promotion amendment

Status: `AGREED_PLANNING_DIRECTION`
Execution authority: `false`

Adopt `coordination/global_policy/deterministic_worker_promotion_policy_v0_1.md`
as the single global policy point for reducing avoidable AI-worker dependence through
evidence-driven deterministic promotion.

Blueprint should:
- keep this policy global rather than duplicate it per module;
- require module-roadmap adoption where AI/LLM workers are used;
- use runtime/conformance evidence to form bounded candidates;
- confirm owner/contracts before implementation;
- keep Blueprint + human governance as initial promotion decision authority;
- require Verification Lab evidence where relevant.

During each module's next roadmap enrichment, add an adoption/reference step appropriate
to that module's actual worker usage.
