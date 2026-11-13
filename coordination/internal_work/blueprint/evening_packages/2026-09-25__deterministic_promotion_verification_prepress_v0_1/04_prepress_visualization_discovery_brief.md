# Prepress Hub — Automated Product Visualization Discovery Brief

Status: `FUTURE_DISCOVERY_HEAVY_CAPABILITY`

Target module: `ForPrint Prepress Hub`

This is deliberately not a final implementation specification.

Mandatory first step at implementation time:

`RESEARCH_CURRENT_TECHNOLOGY_AT_EXECUTION_DATE`

The implementation may happen much later; available tools may change materially.

## Objective

ForPrint should be able to produce useful preliminary client previews with minimal manual work.

Possible future flow:

`Telegram/CRM request -> structured product/design context -> Prepress Hub -> preview -> client`

## Current 2026 opportunity families

### A. Deterministic 2D mockups
- masks;
- perspective transforms;
- overlays;
- printable-area templates;
- shadows/highlights;
- deterministic compositing.

### B. Scripted/3D rendering
- reusable product models;
- texture/logo placement;
- configurable materials/colors;
- scripted viewpoints/renders.

### C. AI-assisted concept visualization
Useful when deterministic templates are unavailable or creative presentation is required.

AI result should normally be labeled `CONCEPT_VISUALIZATION`, not final production proof.

### D. Hybrid pipeline hypothesis

1. search internal assets/templates;
2. deterministic 2D mockup;
3. scripted/3D renderer;
4. AI visual worker fallback;
5. preserve provenance of generation method.

## Mandatory future re-research topics

At implementation date review:
- image generation/editing models;
- reference-image fidelity;
- logo/text preservation;
- automated mockup tooling;
- 2D compositing;
- 3D automation/rendering;
- GPU/runtime cost;
- local Unix vs hosted API;
- open-source vs hosted tools;
- licensing/commercial use;
- privacy;
- latency;
- reproducibility;
- vendor lock-in;
- print-specific geometry/fidelity;
- integration with Prepress Hub;
- testing/fallback strategy.

Do not freeze a vendor/model in 2026 for a future implementation.

## Experiments near implementation time

- mug/glassware;
- notebook/cover;
- flat sign;
- apparel;
- bag/packaging;
- curved surface;
- transparent/metallic surface;
- Ukrainian text/logo fidelity;
- repeatability;
- deterministic template vs AI comparison;
- cost/latency comparison.

## Architecture guardrail

Prefer deterministic rendering where adequate.
Use AI where it provides capability deterministic tooling cannot reasonably provide.
