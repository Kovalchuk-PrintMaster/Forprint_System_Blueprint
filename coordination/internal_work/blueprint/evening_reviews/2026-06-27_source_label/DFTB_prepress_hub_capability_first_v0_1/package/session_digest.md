# Session Digest — Prepress capability discovery, shared tools, candidates and Unix-first execution

## Authority

This is **Prepress module history**, not current Blueprint authority.

## Relation to earlier Prepress Hub idea

The earlier CRM dialogue proposed a fairly broad local Prepress Hub architecture.

This source contains an explicit owner correction:
**do not start by designing the whole cross-module architecture.**

First answer practical questions:
- what can each product/tool really automate?
- which native tools already exist?
- which utilities must ForPrint build?
- what belongs on Unix?
- what genuinely requires Windows/Photoshop?

## Product-specific assistants

Owner rejects an abstract `Raster Assistant`.

Preferred functional split:
- Photoshop Assistant;
- Illustrator Assistant;
- CorelDRAW Assistant;
- PDF/Acrobat Assistant.

The principle is product/domain logic stays with the natural product assistant.

## Shared Prepress Tools

Common technical operations should not be duplicated in every assistant.

Historical proposal:
`Prepress Common Tools / File Intelligence Core`

Examples:
- file type;
- page count;
- dimensions;
- DPI;
- color mode;
- ICC;
- alpha/transparency;
- preview;
- metadata;
- physical size;
- structured report.

Critical boundary:
**shared tools return facts; they do not make domain/production decisions.**

Product assistants interpret those facts.

Initial dependency shape:
product assistants → Shared Tools
rather than assistant → assistant cycles.

## Common report contract

A shared structured response such as `file_inspection_report_v0_1` is proposed so product assistants do not parse arbitrary prose.

## Multiple processing candidates

Owner identifies a central prepress reality:
different tools can solve the same task and produce visibly different results.

Therefore one input may generate several controlled `processing candidates`.

Example:
- fast PDF/CLI candidate;
- Photoshop crop-before-bleed;
- Photoshop content-aware candidate;
- manual review if uncertainty remains.

Each candidate can carry:
- tool/strategy;
- output;
- preview;
- warnings;
- visual/content-loss risk;
- automation confidence.

Do not declare one tool globally superior.

## Bleed/edge example

A thin white edge may become highly visible if a simple bleed algorithm repeats/extends it.

Historical candidate strategies:
1. preserve/extend edge;
2. crop 0.5–1 mm, then create bleed;
3. mirror bleed;
4. Photoshop content-aware extension.

Crop is not automatically safe because it may remove text/logo/face/frame near the edge.

Therefore edge diagnostics precede candidate generation.

## Unix-first policy

Owner explicitly prefers Unix execution whenever practical.

Unix quick-check/preparation can handle:
- format/dimensions;
- effective DPI;
- aspect ratio;
- ICC/alpha;
- edge-white detection;
- previews;
- deterministic crop/resize/canvas/bleed;
- image→PDF;
- structured reports.

Photoshop/Windows is reserved for:
- PSD/PSB/layers;
- Smart Objects;
- Photoshop Actions;
- content-aware/quality-specific work;
- cases where CLI output is visually insufficient.

The assistant's “80–90%” estimate is preserved only as a heuristic, not a target.

## Windows Photoshop Station

Historical design treats Windows as a bounded quality executor, not the central brain.

Proposed file/contract exchange:
Unix side creates:
- input file;
- `job.json`.

Windows agent:
- watches jobs;
- opens Photoshop;
- runs Action/UXP/COM/script;
- exports output/preview;
- writes `result.json`/log;
- returns the result.

This keeps orchestration/tool policy outside the Photoshop workstation.

## Tool-order policy

Do not hardcode:
`PDF → Photoshop → Illustrator` for every file.

Historical rule:
**file_type + task + risk_score → candidate order**

## Client/operator UX

Show at most a few understandable variants, not implementation details.

Each option should explain what changed and why.

Every action should emit:
- preview;
- technical/machine report;
- operator/client explanation where useful.

## Raster preflight

Owner provides two important configurable policy examples:
- minimum effective DPI, below which approval/clarification is required;
- maximum allowed automatic nonproportional adjustment, historical example around 3–5%.

These are **examples/config values**, not final constants.

Resolution quality and aspect suitability are separate checks.

A proposed `raster_job_inspect` returns:
- target size;
- effective DPI;
- aspect mismatch;
- auto-fit eligibility;
- structured status;
- required client questions.

## K-only thin raster text

Owner raises a real print problem:
simple raster files with thin dark text may benefit from K-only black.

But after rasterization, text is only pixels.

Therefore the safe historical direction is:
- analyze/candidate generation for simple cases;
- preview;
- confidence/risk;
- manual/Photoshop fallback when uncertain.

Never blindly recolor dark image content.

## First bounded practical workfront

Proposed first Unix set:
- `raster_job_inspect`;
- `raster_fit_to_format`;
- `raster_bleed_prepare`;
- `raster_black_text_enhance_candidate`;
- `raster_to_pdf`;
- `raster_job_report`.

Photoshop station runner remains the fallback/quality path.

## Stable historical principle

**Solve deterministic prepress work locally and transparently; escalate only where specialized visual tooling adds value; keep shared tools factual, product assistants bounded, and every transformation observable.**
