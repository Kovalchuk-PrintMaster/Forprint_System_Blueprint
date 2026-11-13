# ForPrint Verification and Adversarial Testing Policy v0.1

Status: **active planning standard; does not authorize module implementation**

Owner: `forprint_system_blueprint`

Primary future executor: `verification_lab`

## Purpose

ForPrint must professionally try to prove releases and integrated behavior wrong before
customers, production equipment or live providers do. Verification is distinct from project
conformance inspection and from runtime observation.

## Role separation

- **Verification Lab** intentionally generates valid, invalid, boundary, adversarial, concurrency,
  fault and recovery cases in an isolated Test Plane.
- **Project Inspector** verifies architecture, ownership, cleanliness, contract and governance
  conformance; it does not own adversarial execution.
- **Production Runtime Inspector** observes actual runtime execution evidence; it does not
  manufacture test failures.

## Test modes

1. **BLACK_BOX** — public/user-visible behavior only.
2. **GRAY_BOX** — published contracts, capabilities and trace projections.
3. **WHITE_BOX_READ_ONLY_DIAGNOSIS** — source/config/trace inspection for diagnosis without
   production mutation.

## Required taxonomy

At minimum the Test Plane must be able to represent:

- normal and valid cases;
- invalid, boundary and malformed inputs;
- combinatorial and multilingual cases;
- out-of-domain requests;
- authentication/authorization and data-isolation cases;
- prompt-adversarial and tool-misuse cases;
- state-machine, concurrency and idempotency cases;
- temporary unavailability, timeout and retry/dead-letter cases;
- stale-cache and schema-fuzz cases;
- fault/recovery cases;
- load/performance and AI/tool-cost regression.

## Test Plane and side effects

Adversarial verification must use isolated/synthetic providers and data whenever an action could
cause an external side effect. Payment, courier/taxi, printer, email, cloud, Telegram and similar
interfaces must use fakes/sandboxes/test identities unless a separate explicit production-safe
authorization exists.

Verification findings never grant permission to execute production changes.

## Deterministic regression conversion

Exploratory AI may discover cases, but a durable regression test becomes canonical only after:

1. failure evidence exists;
2. the responsible domain/contract owner is identified;
3. expected behavior is explicit;
4. the case is converted to a deterministic fixture/oracle where feasible;
5. the regression is versioned and reproducible.

## Campaign cadence

The target model supports change-triggered, nightly, weekly, manual, pre-release and post-release
campaigns. Cadence is risk-based and does not itself open assistant distribution or implementation.

## Trace-aware evaluation

A final answer can be superficially correct while intermediate behavior is unsafe. Verification may
therefore inspect published traces, contract transitions, tool calls, queue states and side-effect
evidence. Hidden chain-of-thought is neither required nor an execution-evidence target.

## Release relationship

Verification evidence is an input to release/staging/canary decisions. It does not replace human
approval where policy requires it and does not own release authority.

## Current gate

`verification_lab` is planning-only. No module implementation, assistant distribution, cross-repo
diagnostics, H10 widening or production test traffic is authorized by this standard.
