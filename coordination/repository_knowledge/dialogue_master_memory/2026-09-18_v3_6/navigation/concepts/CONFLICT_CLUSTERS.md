# Conflict clusters

These are derived reconciliation views. They do not override source evidence or current release authority.

## CC-001 — Current authority vs stale bootstrap/continuity
**Status:** CURRENT_AUDIT_REQUIRED

Historical START_HERE/bootstrap/handoffs repeatedly retained current-looking stale phase claims. The reviewed authority front door is releases/current.yaml, but navigation surfaces need reconciliation.

**Historical items:** `IT-BP1708-0001`, `IT-BP2708-0001`, `IT-BP0909-0017`, `IT-BP0909-0018`, `IT-BP1009-0001`, `IT-BP1009-0002`, `IT-BP0709CF-0002`, `IT-BP0709CF-0004`, `IT-BP0709CF-0005`, `IT-BP0709CF-0006`

## CC-002 — Completion evidence vs acceptance authority
**Status:** REFINEMENT_CHAIN_WITH_REMAINING_AUDIT

The project evolves from completion-report evidence to explicit acceptance transactions; later same-phase progression is automated, while major phase boundaries remain operator-controlled. Automatic acceptance itself must not be inferred from evidence alone.

**Historical items:** `IT-BP0508C-0031`, `IT-BP1708-0007`, `IT-BP1708-0008`, `IT-BP1708-0009`, `IT-BP2708-0014`, `IT-BP2708-0015`, `IT-BP0909-0009`, `IT-BP0909-0010`, `IT-LIB0507-0023`, `IT-LIB0507-0026`

## CC-003 — Globally clean tree vs parallel bounded execution
**Status:** HISTORICALLY_SUPERSEDED_DIRECTION_CURRENT_AUDIT_REQUIRED

Early mutation/seal checks often assumed a clean worktree; later owner doctrine explicitly rejects global cleanliness as a prerequisite for safe parallel work and uses bounded baselines/owned scopes.

**Historical items:** `IT-BP0508-0018`, `IT-BP0508C-0004`, `IT-BP2708-0009`, `IT-BP2708-0010`, `IT-BP2708-0011`, `IT-BP0909-0015`

## CC-004 — Fake canonical data vs bounded temporary fixtures
**Status:** NEEDS_POLICY_RECONCILIATION

Early doctrine rejects fabricated dependency truth. Later work permits bounded temporary catalogs/fixtures to exercise logic. Current policy should explicitly distinguish non-authoritative fixtures from fake canonical truth.

**Historical items:** `IT-BP1406-0003`

## CC-005 — Synthetic planning vs accepted architecture
**Status:** KNOWN_RISK

Synthetic future steps are useful but must remain visibly synthetic/non-executable. Vocabulary/schema fragmentation can make planning artifacts look authoritative.

**Historical items:** `IT-BP3108-0016`, `IT-BP3108-0017`, `IT-BP0509-0005`

## CC-006 — Logistics pilot authority and expansion gate
**Status:** LAST_KNOWN_RULE_COHERENT_BUT_RUNTIME_VERIFY

Logistics-only pilot converges on minimum two successful real automatic runs, positive stability review and a separate expansion decision; duplicate historical pilot-gate surfaces still need effective-state reconciliation.

**Historical items:** `IT-BP1708-0018`, `IT-BP2708-0023`, `IT-BP2708-0024`, `IT-BP2708-0025`, `IT-BP3108-0002`, `IT-BP0909-0008`

## CC-007 — Contract Registry vs Gateway vs domain authority
**Status:** ARCHITECTURE_DIRECTION_ACCEPTED_CURRENT_IMPLEMENTATION_VERIFY

Domain modules own meaning, Contract Registry owns versioned agreements, Gateway validates/routes runtime traffic. These responsibilities must not collapse.

**Historical items:** `IT-BP3108-0029`, `IT-BP3108-0030`, `IT-BP3108-0031`, `IT-BP3108-0032`, `IT-BP3108-0033`, `IT-BP3108-0034`, `IT-BP3108-0035`, `IT-LIB1605-0023`, `IT-LIB1605-0025`, `IT-GW2605-0006`, `IT-GW2605-0001`, `IT-GW2605-0003`

## CC-008 — Module inventory and identity drift
**Status:** CURRENT_AUDIT_REQUIRED

Historical counts move across 19/21/22 and current reviews still find identity/double-count mismatches. Machine IDs must be canonical before automated portfolio selection.

**Historical items:** `IT-BP3108-0006`, `IT-BP2708-0031`

## CC-009 — Artifact/script revision identity
**Status:** CURRENT_AUDIT_REQUIRED

Old script versions and revision collisions repeatedly caused safe failures. Unique descriptive archives and strong revision/hash checks became explicit requirements.

**Historical items:** `IT-BP2708-0008`, `IT-BP2708-0034`, `IT-BP0909-0004`

## CC-010 — Human docs vs machine governance parity
**Status:** CURRENT_AUDIT_REQUIRED

Several owner/theory decisions were richer than their machine-readable governance projection. Both sides need effective-state links and parity checks.

**Historical items:** `IT-BP3108-0008`, `IT-BP0509-0009`, `IT-BP1009-0019`

## CC-011 — Roadmap plan vs actual execution authority
**Status:** CURRENT_AUDIT_REQUIRED

Owner identifies recurring roadmap lag. CF-02 resolves the model by making continuity event store authoritative for execution and roadmap execution fields generated projections; source ends before migration is proven complete.

**Historical items:** `IT-BP1209-0021`, `IT-BP1209-0022`, `IT-BP1209-0028`, `IT-BP1209-0029`, `IT-BP1209-0031`, `IT-BP1209-0034`

## CC-012 — Whole-mutator rerun vs state-aware partial recovery
**Status:** SAFETY_INVARIANT_CURRENT_AUDIT_REQUIRED

Historical failures show canonical state may advance before checkpoint/closure fails. Blind rerun is explicitly forbidden; recovery must inspect source fingerprint/state and repair only the remaining layer.

**Historical items:** `IT-BP1209-0023`, `IT-BP1209-0025`, `IT-BP1209-0032`, `IT-BP1409-0006`, `IT-BP1409-0007`

## CC-013 — Structural PASS vs semantic freshness
**Status:** CURRENT_AUDIT_REQUIRED

08.09 Logistics evidence shows tests/module-memory/document-authority can pass while fresh-context/current-state semantics are stale. Structural validation must not be treated as semantic freshness proof.

**Historical items:** `IT-BP0809-0023`, `IT-BP0809-0028`

## CC-014 — Local module health vs portfolio strategic alignment
**Status:** ARCHITECTURAL_INVARIANT

A locally healthy module is not automatically strategically aligned. Final disposition requires current Blueprint mission/policy/target, dependencies, cross-repository consumers and runtime truth.

**Historical items:** `IT-BP0809-0025`, `IT-BP0809-0027`, `IT-BP0809-0034`

## CC-015 — Generated PASS/projection vs reconciled source truth
**Status:** CURRENT_AUDIT_REQUIRED

Historical B10 findings show stale lineage/current-step assumptions under PASSED reports and stale generated guides. Authoritative source reconciliation must precede projection regeneration.

**Historical items:** `IT-BP0809-0003`, `IT-BP0809-0004`, `IT-BP0809-0007`, `IT-BP0809-0033`

## CC-016 — Stale diagnostic log vs current-tree / isolated-check truth
**Status:** CURRENT_AUDIT_REQUIRED

14.09 shows a full-check log carrying an old source-hash pin while the current focused rerun passes. Validation must distinguish live working-tree tests from isolated non-mutating materialization and stale report provenance before changing source.

**Historical items:** `IT-BP1409-0011`, `IT-BP1409-0013`, `IT-BP1409-0014`, `IT-BP1409-0015`, `IT-BP1409-0016`, `IT-BP1409-0020`

## CC-017 — Stale handoff plan vs durable current state
**Status:** ARCHITECTURAL_INVARIANT

A handoff can prescribe work that has already been closed by the time the next assistant starts. Exact current-state reconciliation must precede mutation; already-closed work is skipped rather than replayed.

**Historical items:** `IT-BP0709CF-0002`, `IT-BP0709CF-0004`, `IT-BP0709CF-0005`, `IT-BP0709CF-0006`

## CC-018 — Focused tests green vs semantic/governance candidate correctness
**Status:** CURRENT_AUDIT_REQUIRED

CF-02 candidate compiled and focused tests passed, but adversarial semantic review still found seven blockers. Candidate acceptance therefore requires semantic/governance review, not only local tests.

**Historical items:** `IT-BP0709CF-0010`, `IT-BP0709CF-0011`, `IT-BP0709CF-0012`, `IT-BP0709CF-0013`, `IT-BP0709CF-0014`, `IT-BP0709CF-0015`, `IT-BP0709CF-0016`, `IT-BP0709CF-0017`, `IT-BP0709CF-0018`, `IT-BP0709CF-0019`

## CC-019 — Module publication completeness vs external Blueprint freshness
**Status:** ARCHITECTURAL_INVARIANT

Historical Logistics H9 can be fully published/sealed while Blueprint freshness remains STALE. External freshness blocks live start but must not be collapsed into module implementation/publication failure.

**Historical items:** `IT-LOG1006-0013`, `IT-LOG1006-0015`, `IT-LOG1006-0019`

## CC-020 — Sealed historical candidate vs moving external HEAD
**Status:** CURRENT_AUDIT_REQUIRED

Blueprint HEAD advanced after H9 sealing. Rewriting Logistics status/report or adding recursive seal commits to chase external state would reopen completed history. Historical observed authority and current freshness must remain separate facts.

**Historical items:** `IT-LOG1006-0014`, `IT-LOG1006-0017`, `IT-LOG1006-0018`

## CC-021 — Broad Library catch-all vision vs canonical-definition boundary
**Status:** RESOLVED_DIRECTION_CURRENT_AUDIT_REQUIRED

The earliest Library vision includes broad operational data, but the later Blueprint alignment inside the same source narrows Library to canonical definitions and explicitly excludes runtime orders/payments/stock/production/files. Current implementation should follow the narrowed boundary.

**Historical items:** `IT-LIB1605-0010`, `IT-LIB1605-0015`, `IT-LIB1605-0016`, `IT-LIB1605-0022`, `IT-LIB1605-0024`

## CC-022 — Library mutating `make check` vs project read-only check invariant
**Status:** CURRENT_AUDIT_REQUIRED

The visible July Library Makefile runs `lint-fix` inside `check`. Later Blueprint authority explicitly separates check/read-only from mutation. Current Library command surface must follow the later invariant.

**Historical items:** `IT-LIB0507-0005`, `IT-LIB0507-0006`

## CC-023 — Module-owned repo vs foreign Blueprint checkout operations
**Status:** CURRENT_AUDIT_REQUIRED

Library and Operational Registry histories both show module-local ownership while historical Make workflows may pull/update the local Blueprint checkout. Current policy must define allowed read/fetch/pull behavior without granting modules write/commit authority over Blueprint.

**Historical items:** `IT-LIB0507-0007`, `IT-LIB0507-0017`, `IT-LIB0507-0018`, `IT-LIB0507-0019`, `IT-OPREG2905-0013`, `IT-OPREG2905-0023`

## CC-024 — Operational truth vs Accounting/1C truth
**Status:** CURRENT_AUDIT_REQUIRED

Early Operational Registry history explicitly assigns operational client/order/task/status/event truth to Operational Registry and accounting/1C truth to Accounting. Later Blueprint history records Accounting-vs-Operational Registry ambiguity. Current architecture must resolve ownership and payment-status semantics without dual authority.

**Historical items:** `IT-OPREG2905-0001`, `IT-OPREG2905-0002`, `IT-OPREG2905-0006`, `IT-OPREG2905-0024`, `IT-OPREG2905-0025`, `IT-ACC1705-0001`, `IT-ACC1705-0020`, `IT-ACC1705-0025`

## CC-025 — Gateway local completion vs Blueprint acceptance
**Status:** ARCHITECTURAL_INVARIANT

Historical v0.7 is locally complete/pushed but still asks Blueprint to mark the prompt completed/accepted and issue the next allowed prompt. Module completion cannot self-promote into architecture acceptance.

**Historical items:** `IT-GW2605-0017`, `IT-GW2605-0018`, `IT-GW2605-0020`, `IT-GW2605-0021`

## CC-026 — Gateway standards visibility/sync vs Blueprint authority boundary
**Status:** CURRENT_AUDIT_REQUIRED

Historical v0.7 gives Gateway standards list/check/sync and a local snapshot. Current implementation must prove this only consumes/materializes Blueprint standards locally and cannot rewrite Blueprint authority surfaces.

**Historical items:** `IT-GW2605-0010`, `IT-GW2605-0012`, `IT-GW2605-0024`

## CC-027 — Accounting sandbox readiness vs live 1C/write/posting readiness
**Status:** ARCHITECTURAL_INVARIANT_CURRENT_AUDIT_REQUIRED

Historical v0.5 is accepted as `sandbox_1c_import_export_ready` while live 1C integration, production writes and automatic posting remain explicitly forbidden. These readiness dimensions must never collapse into one status.

**Historical items:** `IT-ACC1705-0015`, `IT-ACC1705-0016`, `IT-ACC1705-0017`, `IT-ACC1705-0018`, `IT-ACC1705-0023`

## CC-028 — Strategic Control Plane authority vs Blueprint architecture authority
**Status:** CURRENT_AUDIT_REQUIRED

The early proposal distinguishes strategic governance from Blueprint architecture but leaves open whether Control Plane is the highest machine-readable governance layer above Blueprint. The direct owner prompt is missing, so current authority must resolve whether this component exists and how it relates to Blueprint/Control Foundation.

**Historical items:** `IT-CP0106-0002`, `IT-CP0106-0019`, `IT-CP0106-0020`, `IT-CP0106-0021`, `IT-CP0106-0025`, `IT-BP1407-0029`

## CC-029 — Historical Control Plane priority map vs later roadmap authority
**Status:** RESOLVED_BY_LATER_AUTHORITY

Telegram/Calculator P0, Accounting P1 and Operational/Gateway hold is a bootstrap-era proposal only. Later Blueprint release/H10/Control Foundation roadmaps supersede it and it must never drive current execution.

**Historical items:** `IT-CP0106-0009`, `IT-CP0106-0026`, `IT-BP1708-0018`

## CC-030 — CRM dashboard prominence vs canonical domain ownership
**Status:** ARCHITECTURAL_INVARIANT_CURRENT_AUDIT_REQUIRED

CRM is the visible business orchestration/dashboard layer, but visibility must not make it physical owner of clients/orders/payments/catalogs/stock/routing. Specialized registries and Gateway retain canonical/runtime ownership.

**Historical items:** `IT-CRM1605-0014`, `IT-CRM1605-0015`, `IT-CRM1605-0016`, `IT-CRM1605-0017`, `IT-CRM1605-0018`, `IT-CRM1605-0019`, `IT-CRM1605-0020`, `IT-CRM1605-0022`

## CC-031 — Early CRM client/order ownership example vs Operational Registry alignment
**Status:** RESOLVED_BY_LATER_HISTORICAL_ALIGNMENT_CURRENT_AUDIT_REQUIRED

An early Blueprint example assigns `client` and `order` to CRM, but the later direct CRM alignment prompt in the same source assigns canonical clients/orders/tasks/statuses to Operational Registry. The later/current ownership model supersedes the illustrative example.

**Historical items:** `IT-CRM1605-0013`, `IT-CRM1605-0016`, `IT-OPREG2905-0001`

## CC-032 — Broad Prepress Hub architecture vs capability-first product assistants
**Status:** REFINED_DIRECTION_CURRENT_AUDIT_REQUIRED

The early CRM source proposed a broad Prepress Hub stack. The 27.06 owner correction says immediate work should first map practical capabilities by Photoshop/Illustrator/Corel/PDF, with shared factual tools, before cross-module integration architecture.

**Historical items:** `IT-CRM1605-0002`, `IT-PRE2706-0001`, `IT-PRE2706-0002`, `IT-PRE2706-0003`, `IT-PRE2706-0006`

## CC-033 — Configurable raster thresholds vs accidental hard-coded production policy
**Status:** CURRENT_AUDIT_REQUIRED

Historical examples mention ~25 DPI and 3–5% nonproportional tolerance. They are configurable examples, not current constants. Current production policy must come from authoritative configuration/Library/Prepress rules.

**Historical items:** `IT-PRE2706-0019`, `IT-PRE2706-0020`, `IT-PRE2706-0021`

## CC-034 — Unix-first automation vs Photoshop quality fallback
**Status:** ARCHITECTURAL_INVARIANT_CURRENT_AUDIT_REQUIRED

Use Unix for deterministic/bounded work; use Windows Photoshop Station only where Photoshop-specific quality or document semantics are actually needed. The station must remain an executor, not a competing orchestration authority.

**Historical items:** `IT-PRE2706-0011`, `IT-PRE2706-0015`, `IT-PRE2706-0016`, `IT-PRE2706-0028`, `IT-PRE2706-0029`

## CC-035 — Prepress zero-platform scaffold-first vs later capability-first sequencing
**Status:** REFINED_BY_LATER_OWNER_DIRECTION

20.05 proposes immediately building FastAPI/preset/job scaffolding. 27.06 owner direction narrows the immediate phase to capability discovery by product, shared factual tools and Unix-vs-Windows policy before broader integration architecture. Treat May as historical scaffold proposal, not mandatory current sequence.

**Historical items:** `IT-PRE2005-0005`, `IT-PRE2005-0018`, `IT-PRE2005-0022`, `IT-PRE2706-0001`, `IT-PRE2706-0002`, `IT-PRE2706-0006`

## CC-036 — Prepress historical local scaffold portability/security drift
**Status:** CURRENT_AUDIT_REQUIRED

The May scaffold hard-codes an absolute server path and binds a reload-enabled dev server to `0.0.0.0`. Current Prepress should use current path/bootstrap and runtime-security policy rather than copying these historical defaults.

**Historical items:** `IT-PRE2005-0011`, `IT-PRE2005-0012`

## CC-037 — Website marketing activation vs Website technical release authority
**Status:** BOUNDARY_CLARIFIED_CURRENT_AUDIT_REQUIRED

The SMM source wants deliberate promotion of a young website. This business objective does not itself authorize Website module implementation, reactivation or canonical customer ownership; current Blueprint release/scope remains controlling.

**Historical items:** `IT-SMM2506-0001`, `IT-SMM2506-0018`, `IT-BP1407-0009`, `IT-BP1708-0017`, `IT-SMM2507-0015`, `IT-SMM2507-0017`

## CC-038 — Historical marketing channel ranking vs evidence-driven current allocation
**Status:** CURRENT_MEASUREMENT_REQUIRED

Website/Google Business/local SEO→Instagram→TikTok is historical assistant advice. Current channel priority should be based on measured acquisition cost, conversion quality and local reach, not preserved as fixed authority.

**Historical items:** `IT-SMM2506-0003`, `IT-SMM2506-0004`, `IT-SMM2506-0013`, `IT-SMM2506-0014`, `IT-SMM2506-0017`

## CC-039 — One-primary-generator simplification vs historical provider lock-in
**Status:** CURRENT_BUSINESS_TOOLING_AUDIT_REQUIRED

The owner decision is to avoid operating many generators at once. The historical assistant recommendation of Google Veo is not a permanent vendor mandate. Preserve workflow standardization while keeping the external provider replaceable and freshly evaluated.

**Historical items:** `IT-SMM2507-0007`, `IT-SMM2507-0008`, `IT-SMM2507-0009`, `IT-SMM2507-0012`, `IT-SMM2507-0014`, `IT-SMM2507-0016`

## CC-040 — Calculator local catalog/admin vs Library canonical definitions
**Status:** CURRENT_AUDIT_REQUIRED

Historical Calculator built rich product/material/admin structures and briefly envisioned project-wide administration. Later Blueprint allows only temporary local Calculator catalog and Library owns canonical definitions/contracts. Current Calculator must calculate without becoming a competing catalog authority.

**Historical items:** `IT-CALC0910-0008`, `IT-CALC0910-0011`, `IT-CALC0910-0012`, `IT-CALC0910-0037`, `IT-BP1407-0024`, `IT-LIB0507-0015`, `IT-LIB1605-0020`

## CC-041 — Historical direct Website/Telegram quote intake vs Gateway/Contract Registry routing
**Status:** CURRENT_AUDIT_REQUIRED

Calculator was designed as reusable multi-channel backend and historically accepted direct external quote requests. Current runtime architecture may require versioned contracts and Gateway/CRM routing; channel coupling inside Calculator should not be assumed valid.

**Historical items:** `IT-CALC0910-0004`, `IT-CALC0910-0022`, `IT-CALC0910-0024`, `IT-CALC0910-0038`, `IT-GW2605-0001`, `IT-CRM1605-0020`

## CC-042 — Blueprint directive sync false-success vs canonical schema and cwd-independent tooling
**Status:** ARCHITECTURAL_DEFECT_PATTERN_CURRENT_AUDIT_REQUIRED

Calculator importer once returned an apparently successful/no-new result while parsing the wrong index shape. Corrected logic uses `module_directives.active`, but project-wide tooling should centrally validate schema and resolve paths independently of current working directory.

**Historical items:** `IT-CALC0910-0033`, `IT-CALC0910-0034`, `IT-CALC0910-0035`, `IT-CALC0910-0036`

## CC-043 — Telegram approved taxonomy vs generated dataset label drift
**Status:** HISTORICAL_DATA_DEFECT_CURRENT_AUDIT_REQUIRED

Owner-approved taxonomies allow warm/formal/casual/neutral and positive/neutral/negative. Assistant later describes friendly/playful and aggressive/urgent in generated data. These are not authorized taxonomy extensions and current datasets must reject or explicitly migrate unknown values.

**Historical items:** `IT-TG1210-0005`, `IT-TG1210-0006`, `IT-TG1210-0015`, `IT-TG1210-0016`

## CC-044 — Telegram generated-row claims vs unavailable artifacts and import failure
**Status:** CURRENT_AUDIT_REQUIRED

Historical assistant claims 360, 500 and 1000-row datasets but files are unavailable, totals are internally inconsistent and one CSV fails header compatibility. No claimed row count/uniqueness/importability should be treated as verified production state.

**Historical items:** `IT-TG1210-0011`, `IT-TG1210-0012`, `IT-TG1210-0013`, `IT-TG1210-0014`, `IT-TG1210-0017`, `IT-TG1210-0019`, `IT-TG1210-0021`

## CC-045 — Telegram conversation data ownership vs canonical business truth
**Status:** ARCHITECTURAL_INVARIANT_CURRENT_AUDIT_REQUIRED

Telegram may own operational presentation/conversation state, but later Blueprint explicitly says it is an operational interface rather than canonical business truth. Current owner of shared response taxonomies/templates still needs confirmation.

**Historical items:** `IT-TG1210-0025`, `IT-TG1210-0028`, `IT-TG1210-0030`, `IT-BP1407-0011`

## CC-046 — Telegram behavior specification/simulation vs production runtime
**Status:** ARCHITECTURAL_INVARIANT_CURRENT_AUDIT_REQUIRED

The owner explicitly separates behavior-model/Excel/wizard design artifacts from production Telegram app execution. Historical tooling drifted into runtime/classifier engineering too early, then was corrected. Current repo must classify each artifact as spec, fixture, generator or runtime dependency.

**Historical items:** `IT-TG1310-0001`, `IT-TG1310-0016`, `IT-TG1310-0017`, `IT-TG1310-0019`, `IT-TG1310-0020`, `IT-TG1310-0022`, `IT-TG1310-0023`, `IT-TG1210B-0001`, `IT-TG1210B-0016`, `IT-TG1210B-0022`

## CC-047 — Telegram client/delivery orchestration vs CRM and Logistics canonical ownership
**Status:** CURRENT_AUDIT_REQUIRED

Historical Telegram behavior collects client profile and delivery preference and sometimes implies direct provider actions. Current architecture must keep canonical client truth under CRM/Operational ownership and delivery execution under Logistics, with Telegram acting as conversational/operational interface.

**Historical items:** `IT-TG1310-0005`, `IT-TG1310-0006`, `IT-TG1310-0007`, `IT-BP1407-0011`, `IT-BP1407-0012`

## CC-048 — Telegram module closeout READY_FOR_REVIEW vs Blueprint acceptance
**Status:** RESOLVED_AS_SEPARATE_GATES_CURRENT_LINEAGE_AUDIT_REQUIRED

Historical governance closeout is pushed/clean/idempotent but explicitly not accepted or merged. READY_FOR_BLUEPRINT_REVIEW is a module-side state; Blueprint acceptance remains a separate authority gate.

**Historical items:** `IT-TG1310-0033`, `IT-TG1310-0034`, `IT-TG1310-0035`, `IT-TG1310-0036`, `IT-BP1708-0005`, `IT-BP1708-0006`

## CC-049 — Telegram ML path/label/revision contract drift
**Status:** CURRENT_AUDIT_REQUIRED

Historical ML refactoring exposed missing paths, generic constant collisions and downstream label-decoder/runtime mismatches. Current intent/style/sentiment pipelines need one tested train→artifact→classify→evaluate contract with entity-specific paths and reproducible revisions.

**Historical items:** `IT-TG1410-0004`, `IT-TG1410-0011`, `IT-TG1410-0016`, `IT-TG1410-0017`, `IT-TG1410-0018`, `IT-TG1410-0022`, `IT-TG1410-0023`, `IT-TG1410-0029`

## CC-050 — Telegram script standard vs current Blueprint engineering standard
**Status:** STANDARD_RECONCILIATION_REQUIRED

The Telegram owner-defined script standard is strong and overlaps later Blueprint doctrine: self-description, config-first paths, validation, logging, small focused scripts and artifact reporting. It should be reconciled/promoted selectively rather than becoming an independent competing standard.

**Historical items:** `IT-TG1410-0005`, `IT-TG1410-0006`, `IT-TG1410-0007`, `IT-TG1410-0012`, `IT-TG1410-0014`, `IT-TG1410-0030`

## CC-051 — Telegram early free-form taxonomy vs later normalized lookup tables
**Status:** SUPERSEDED_BY_LATER_OWNER_SCHEMA_CURRENT_MIGRATION_AUDIT_REQUIRED

The early chat-import schema uses style labels formal/casual/friendly/professional/urgent and broader sentiments including urgent/curious/confused. Later owner-defined tables normalize styles to warm/formal/casual/neutral and sentiments to positive/neutral/negative. Current datasets/importers must not mix these shapes without explicit migration/aliases.

**Historical items:** `IT-TG0710-0006`, `IT-TG0710-0007`, `IT-TG1210-0005`, `IT-TG1210-0006`

## CC-052 — Telegram-local 1C/master-data mirror vs Accounting Operational Library and Gateway authorities
**Status:** CURRENT_ARCHITECTURE_RECONCILIATION_REQUIRED

Early Telegram discussion imagines synchronizing 1C/client/stock/nomenclature data into a bot-side database and storing heterogeneous business entities locally. Later architecture separates accounting truth, operational truth, canonical definitions and integration routing. Telegram should consume governed projections/contracts rather than become a competing master-data store.

**Historical items:** `IT-TG0710-0013`, `IT-TG0710-0014`, `IT-TG0710-0015`, `IT-TG0710-0016`, `IT-TG0710-0017`, `IT-ACC1705-0025`, `IT-OPREG2905-0001`, `IT-LIB1605-0015`, `IT-GW2605-0003`, `IT-BP1407-0011`, `IT-TG1210B-0018`, `IT-TG1210B-0019`

## CC-053 — Telegram Mentor/AI escalation and broad tool access vs privacy, approval and decision rights
**Status:** CURRENT_SECURITY_AND_AUTHORITY_AUDIT_REQUIRED

Owner wants ambiguous cases escalated with rich context and also explores email/file/cloud/computer automation through Telegram. The intent is valid, but unrestricted database/tool access would violate least-privilege and module boundaries. Current architecture must define context scope, credentials, approval levels, audit, fallback and which assistant role may act.

**Historical items:** `IT-TG1210B-0010`, `IT-TG1210B-0011`, `IT-TG1210B-0012`, `IT-TG1210B-0013`, `IT-TG1210B-0014`, `IT-TG1210B-0015`, `IT-TG1210B-0017`

## CC-054 — Fresh generated ML tests vs independent evaluation truth
**Status:** EVALUATION_ARCHITECTURE_REQUIRED

Owner correctly rejects stale recurring test sets and prefers fresh unseen examples, but assistant-proposed LLM generation does not itself provide correct labels. A valid recurring evaluation system needs an independent oracle/accepted-label path, lineage, leakage checks and promotion thresholds.

**Historical items:** `IT-TG1210B-0027`, `IT-TG1210B-0028`, `IT-TG1210B-0029`, `IT-TG1210B-0030`, `IT-TG1210B-0031`, `IT-TG1210B-0032`

## CC-055 — CF-09 Dispatcher 9/9 readiness vs full-project closure failure
**Status:** CURRENT_AUDIT_REQUIRED

Historical 0253 reports all nine Dispatcher requirements satisfied with zero gaps, but 0254 full project boundary gate fails. Local/subsystem readiness is not equivalent to project acceptance or lifecycle closure.

**Historical items:** `IT-BP1709-0018`, `IT-BP1709-0019`, `IT-BP1709-0020`, `IT-BP1709-0021`, `IT-BP1709-0022`, `IT-BP1709-0025`, `IT-BP1709-0026`

## CC-056 — Library-scoped non-mutating check vs stale Blueprint generator inventory
**Status:** CURRENT_DIAGNOSTIC_AUDIT_REQUIRED

The CF-09 full make check fails while invoking a non-mutating Library check because Blueprint `indexes/generator_inventory.yaml` is stale. The historical log proves the symptom but not whether the root cause is expected dependency enforcement, isolated materialization, current-tree generator drift or stale cross-repo projection.

**Historical items:** `IT-BP1709-0023`, `IT-BP1709-0024`, `IT-BP1409-0015`, `IT-BP1409-0016`
