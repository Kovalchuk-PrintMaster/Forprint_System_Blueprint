# External AI / MCP capability access — conversation evidence v0.1

Date: 2026-10-01
Authority: CONTEXTUAL_STRATEGIC_EVIDENCE_ONLY
Roadmap authority: false
Execution authority: false
Related strategic candidate: HZN-014 — Capability-mediated governed domain data access
Related deferred design gap: ESR-20260926-GAP-007 — domain capability transport

## Human Owner exploration

> "є така річ як mcp ... якщо ... for print буде ... реалізований певний якийсь mcp куди ai
> може там постукати спитати чи робите ви календар ... побачити що є інструмент доступу до
> прорахунку ... віддати уже своєму власнику ... повністю пакет інформації"

The desired long-horizon outcome is that a customer's external AI assistant may eventually
obtain structured ForPrint product/capability information and, where authorized, use canonical
quote or service capabilities instead of only pointing the customer at a website.

## Architectural interpretation

This does not create a new business-truth owner. Any future external AI adapter should consume
governed capabilities from canonical ForPrint owners such as Library, Calculator, Prepress,
Logistics and related services through approved integration boundaries.

Machine access and automatic discovery are separate problems. An MCP endpoint by itself does
not guarantee that arbitrary AI systems discover or choose ForPrint.

## Human Owner final decision

> "ми взагалі навіть не будемо його поки що ставити в roadmap ... запишемо в стратегічні
> цілі ... коли ... почнемо уже перші результати отримувати по for print ... повторно
> розглянемо цікавість цього інструменту ... ніяких реалізацій ... робити не будемо
> зосередимось першочергово виключно на консолі"

## Canonical interpretation

- Reuse and refine HZN-014; do not create a separate MCP Horizon candidate.
- Preserve MCP only as one possible future transport/protocol family.
- Preserve ESR-20260926-GAP-007: MCP/HTTP/RPC/other remains intentionally unfrozen.
- Do not create executable roadmap work or implementation backlog now.
- Revisit after first stable ForPrint ecosystem results during deliberate strategic review.
- Current implementation concentration is Operator Console / OC-01.
