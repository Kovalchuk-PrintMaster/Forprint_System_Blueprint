# Session Digest — Prepress Hub proposed zero-platform bootstrap

## Duplicate result

Unique source. It is not a duplicate/near-duplicate of the CRM/Prepress genesis source or the later 27.06 Prepress capability dialogue.

## Evidence limitation

Only turns 1–2 survive.

The owner says a previous `prepress_hub.docx` prompt/agreements attachment is provided, but the attachment content is not visible in MHTML.

Therefore statements beginning “from the attachment I take...” are **assistant-side secondary evidence**.

## Owner-grounded facts

The owner directly says:
- a new module `ForPrint Prepress Hub` is starting;
- a working server directory already exists:
  `/srv/software_development/forprint-project/forprint_prepress_hub`;
- prior prompt/agreements are attached.

No later terminal execution is present.

## Historical proposed architecture

Assistant summarizes the intended Hub as:
- local prepress control center rather than separate heavyweight plugin per Adobe app;
- HTML/web UI as interface;
- Python backend as logic;
- Adobe actions/scripts as executors;
- presets as process/technology cards;
- logs as operational trace.

Because the direct attachment is absent, this remains historical proposal/summary.

## Proposed zero-platform

First phase:
- Python backend;
- local web panel;
- preset engine;
- tests.

Explicitly not yet:
- direct Photoshop integration;
- Illustrator integration;
- Acrobat integration.

Proposed repo structure separates:
- core;
- API;
- adapters;
- workers;
- config;
- presets;
- incoming/processing/ready/error data;
- logs;
- tests.

## Proposed service scaffold

Historical draft uses:
- Python 3.11;
- FastAPI;
- Pydantic settings;
- PyYAML;
- pytest;
- Ruff;
- Uvicorn.

Endpoints:
- `/health`;
- `/presets`.

A YAML loader discovers presets but explicitly does **not** execute prepress operations yet.

The first example preset `pdf_basic_check.yaml` is only a structural check.

## Historical Make surface

The proposed Makefile has:
- install;
- test;
- lint;
- check;
- run;
- health.

`check` is `lint + test`, i.e. non-mutating.

This is directionally compatible with later Blueprint read-only-check discipline.

## Two historical design drifts

### Absolute project root
The proposed settings hard-code:
`/srv/software_development/forprint-project/forprint_prepress_hub`.

Later project governance prefers portable/project-relative paths, so this is a current-audit target, not a retained standard.

### Local service binding
The proposed Uvicorn command uses:
`--host 0.0.0.0 --port 8020 --reload`.

For a service described as local, all-interface binding + reload may be broader than intended. Current runtime/security policy must decide.

## First-step completion gate

Assistant proposes the zero-platform is complete only if:
- `make check` passes;
- `/health` returns OK;
- `/presets` sees `pdf_basic_check.yaml`.

No visible evidence shows these commands were actually run.

Therefore this is an **acceptance criterion**, not historical PASS.

## Proposed Job Runner v1

Next workfront after the gate:
- accept a PDF/path;
- create an isolated processing job folder;
- copy the input;
- **do not modify the original**;
- run internal steps;
- write `logs/jobs.jsonl`.

The original-input immutability principle remains valuable historical intent.

## Relation to 27.06

This May source is scaffold-first.

The later 27.06 owner direction refines sequencing:
first build a practical capability map by Photoshop/Illustrator/Corel/PDF, shared factual tools and Unix-vs-Windows split before broad architecture/integration.

Therefore May is preserved as the **early proposed zero-platform**, not the final Prepress direction.
