# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Current audit |
|---|---|---|---|---|---|
| `IT-BP2109-0001` Handoff archives provide context but do not grant mutation or dispatch authority | process_rule | accepted | critical | EV-BP2109-0001 | not audited |
| `IT-BP2109-0002` Source opens inside CF-09/u180i after CF-08/u180h closure | implementation_claim | accepted | critical | EV-BP2109-0002 | not audited |
| `IT-BP2109-0003` Event stream and current work-front state outrank stale roadmap horizon projections | architecture_constraint | accepted | critical | EV-BP2109-0003 | not audited |
| `IT-BP2109-0004` Intentional parallel dirty state must not be erased for cosmetic cleanliness | process_rule | accepted | critical | EV-BP2109-0004 | not audited |
| `IT-BP2109-0005` CF-09 ACK is a machine-verifiable pre-execution execution-contract receipt | architecture_constraint | accepted | critical | EV-BP2109-0006, EV-BP2109-0008 | not audited |
| `IT-BP2109-0006` Package validation and ACK validation must both pass before worker execution | process_rule | accepted | critical | EV-BP2109-0007, EV-BP2109-0009, EV-BP2109-0010 | not audited |
| `IT-BP2109-0007` General worker dispatch remains blocked; CF-10 is a bounded single internal Blueprint pilot | architecture_constraint | accepted | critical | EV-BP2109-0005 | not audited |
| `IT-BP2109-0008` Incoming architecture/planning packages are verified in tmp before canonical application | process_rule | accepted | high | EV-BP2109-0011 | not audited |
| `IT-BP2109-0009` Large architecture/handoff changes are applied step by step | process_rule | accepted | high | EV-BP2109-0012, EV-BP2109-0014 | not audited |
| `IT-BP2109-0010` Roadmap/dependency maintenance must scale to frequent large restructures | requirement | accepted | critical | EV-BP2109-0013 | not audited |
| `IT-BP2109-0011` Assistant-pack/bootstrap work must not silently become roadmap redesign | process_rule | accepted | critical | EV-BP2109-0023 | not audited |
| `IT-BP2109-0012` Verified assistant/bootstrap packages should become durable project artifacts | process_rule | accepted | high | EV-BP2109-0024 | not audited |
| `IT-BP2109-0013` Living knowledge promotion is evidence-bounded and source-preserving | process_rule | accepted | critical | EV-BP2109-0015, EV-BP2109-0016 | not audited |
| `IT-BP2109-0014` Historical living-knowledge candidate passes targeted and semantic validations without commit/push | implementation_claim | accepted | high | EV-BP2109-0017 | not audited |
| `IT-BP2109-0015` Continuity event store is historical execution authority; generated roadmap status is projection only | architecture_constraint | accepted | critical | EV-BP2109-0018, EV-BP2109-0019 | not audited |
| `IT-BP2109-0016` Historical project authority precedence is Constitution > Module Policy > Execution Profile > Work Front | architecture_constraint | accepted | critical | EV-BP2109-0020, EV-BP2109-0021 | not audited |
| `IT-BP2109-0017` AI self-certification cannot widen its own guardrails | architecture_constraint | accepted | critical | EV-BP2109-0021 | not audited |
| `IT-BP2109-0018` Successful package generation can still produce the wrong semantic package | risk | accepted | high | EV-BP2109-0022 | not audited |
| `IT-BP2109-0019` Historical 0170 reports CF-10 READY_UNBOUND after CF-07/08/09 completion | implementation_claim | accepted | critical | EV-BP2109-0025, EV-BP2109-0026 | not audited |
| `IT-BP2109-0020` CF-10 should reuse the existing control plane rather than invent a parallel launch mechanism | architecture_constraint | accepted | critical | EV-BP2109-0027 | not audited |
| `IT-BP2109-0021` First CF-10 launch choreography must be reconstructed read-only before any binding or worker run | process_rule | accepted | critical | EV-BP2109-0029, EV-BP2109-0034 | not audited |
| `IT-BP2109-0022` Lifecycle order requires roadmap binding before WORK_PLANNED and WORK_ACTIVATED | architecture_constraint | accepted | critical | EV-BP2109-0029 | not audited |
| `IT-BP2109-0023` Prospective CF-10 work-id u180j is not safely free | risk | accepted | critical | EV-BP2109-0030 | not audited |
| `IT-BP2109-0024` Work-id selection is historically explicit/operator-supplied when no allocator exists | architecture_constraint | accepted | high | EV-BP2109-0030 | not audited |
| `IT-BP2109-0025` Handoff v2 runtime hardcodes old work-id u180h and lacks dynamic binding | risk | accepted | critical | EV-BP2109-0028, EV-BP2109-0032 | not audited |
| `IT-BP2109-0026` Execution-profile recommendation does not grant dispatch authority | architecture_constraint | accepted | critical | EV-BP2109-0031 | not audited |
| `IT-BP2109-0027` An explicit local worker-start interface is historically resolvable | implementation_claim | accepted | high | EV-BP2109-0033 | not audited |
| `IT-BP2109-0028` First zero-stage candidate is bounded read-only analysis of the deferred maintenance-governance gap | plan | accepted | high | EV-BP2109-0034 | not audited |
| `IT-BP2109-0029` 0172 PASS means the audit ran successfully, not that CF-10 launch is ready | process_rule | accepted | critical | EV-BP2109-0034 | not audited |
| `IT-BP2109-0030` CF-10 remains unbound/unactivated until launch-critical blockers are repaired | process_rule | accepted | critical | EV-BP2109-0034 | not audited |
| `IT-BP2109-0031` Library-named project-context package must not be interpreted as a Library task without authority | risk | accepted | critical | EV-BP2109-0035 | not audited |
| `IT-BP2109-0032` Package type, target module and purpose must be operator-visible and semantically accurate | requirement | accepted | high | EV-BP2109-0022, EV-BP2109-0035 | not audited |
| `IT-BP2109-0033` Exact CF-09 closure lineage between 17.09 red gate and CF-10 READY_UNBOUND is missing from visible source | risk | accepted | critical | EV-BP2109-0025, EV-BP2109-0026 | not audited |
| `IT-BP2109-0034` Source ends before CF-10 blocker repair or package-routing answer | risk | accepted | critical | EV-BP2109-0034, EV-BP2109-0035, EV-BP2109-0036 | not audited |
