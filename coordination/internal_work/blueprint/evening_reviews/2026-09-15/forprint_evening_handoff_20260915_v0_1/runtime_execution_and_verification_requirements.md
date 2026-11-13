# Runtime Execution and Verification Requirements

## Disposable tmp
`tmp/` is disposable. Deleting it must not destroy required resume state.

## Persistent execution state
Future runtime should support:
- execution/attempt ID;
- manifest;
- current phase/node;
- durable checkpoint;
- continuation artifacts;
- failure reason;
- validation state;
- resume eligibility;
- retry lineage;
- final result/evidence.

Exact canonical location must be determined after auditing existing design.

## Operator command surface
Move toward stable commands such as conceptual:
- `forprint run`
- `forprint status`
- `forprint resume`
- `forprint inspect`
- `forprint check --local|--related|--module|--full`
- `forprint roadmap`
- `forprint project-health`

Names are placeholders until project conventions are audited.

## Verification tiers
1. LOCAL
2. RELATED/INTEGRATION
3. MODULE
4. PROJECT/FULL
5. NIGHTLY/DEEP

Full validation should not be default after every small change.
Scheduled heavy checks should emit structured failures suitable for Dispatcher intake.
