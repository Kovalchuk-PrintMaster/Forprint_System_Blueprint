# Verification Lab — change-aware adversarial campaign enrichment

Status: `AGREED_PLANNING_DIRECTION`
Execution authority: `false`

Existing H07/H08 already define:
- AI-discovered failure → owner-confirmed deterministic regression corpus;
- change-triggered/nightly/weekly/manual/pre-release/post-release campaigns.

## Enrichment

Add a change-aware campaign planner that:
1. consumes bounded functional-change evidence;
2. decides whether the change is relevant to Lab coverage;
3. uses AI only when useful to design/extend targeted scenarios;
4. persists useful scenarios as deterministic versioned corpus;
5. does not regenerate unchanged test strategy when no relevant functional change exists;
6. runs cheap targeted deterministic regression routinely;
7. runs broader heavy stress/soak/accumulated-data sweeps periodically;
8. enforces CPU/RAM/I/O/network/concurrency/time budgets;
9. keeps heavy/adversarial execution in Test Plane/staging by default.

Exact windows such as `00:00–06:00` are infrastructure-dependent future operating policy,
not a frozen roadmap constant.
