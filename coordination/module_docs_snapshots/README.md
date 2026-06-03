# ForPrint Module Documentation Snapshots

## Purpose

This directory stores reviewed or collected documentation snapshots from module repositories.

The goal is to let ForPrint System Blueprint compare:

```text
what Blueprint expects from a module
vs.
what the module documentation says about itself
vs.
what the module status reports say is implemented
Current mode

Manual / semi-manual.

No heavy automation is required yet.

The project currently has a small number of active modules, so manual review is acceptable.

Difference from module policy

coordination/module_policy/ contains Blueprint-owned module strategy and expectations.

coordination/module_docs_snapshots/ contains copied, summarized or reviewed documentation from the module repositories themselves.

Recommended structure
coordination/module_docs_snapshots/<module_id>/
├── README.md
├── architecture_summary.md
├── implementation_summary.md
├── detected_drift.md
└── blueprint_review_notes.md

Not all files are required at first.

What may be stored here

Allowed content:

safe summaries of module docs;
architecture summaries;
implementation summaries;
review notes;
detected drift;
questions for Blueprint;
links or paths to source module docs.
What must not be stored here

Do not store:

secrets;
tokens;
passwords;
private client data;
real accounting data;
real 1C production data;
large logs;
binary dumps;
full copied documents when a short summary is enough.
Future automation

Later Blueprint may add a script such as:

scripts/snapshot_module_docs.py --module calculator_engine

For now, manual review is preferred to avoid overbuilding automation too early.


---
