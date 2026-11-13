# Blueprint Coordination Workspace

`coordination/` is the governance, planning and inter-module coordination workspace of
ForPrint System Blueprint.

It is not one flat prompt inbox. The directory now contains several distinct lifecycle
classes.

## Effective authority

Current release/work authority:

`coordination/releases/current.yaml`

Current detailed Blueprint plans:

`coordination/roadmaps/details/forprint_system_blueprint/`

## Main areas

- `releases/` — current release projection and release history/evidence;
- `roadmaps/` — module and Blueprint plans/dependencies;
- `standards/` — normative governance/engineering standards;
- `outgoing_prompts/` — Blueprint-owned Prompt Queue v0.2 surfaces and released prompts;
- `incoming_requests/` — module-to-Blueprint requests;
- `review_packets/` — review material and review lifecycle;
- `module_sources/` — module repository/local-source registry;
- `module_policy/` — module policy coverage;
- `reports/` — coordination review/completion evidence;
- `internal_work/` — bounded analysis, migrations and historical evidence;
- `repository_knowledge/` — canonical repository-knowledge snapshot protocol/templates;
- `templates/` — reusable/distribution templates.

## Authority discipline

A file under `coordination/` is not automatically authoritative.

- `releases/current.yaml` wins for effective release state;
- active standards govern their declared domain;
- released prompts remain immutable execution contracts;
- `internal_work/` is evidence/history unless explicitly promoted;
- distribution templates are not authority over their declared canonical sources.

## Legacy early alignment

The initial manual alignment layer is preserved under:

`coordination/internal_work/blueprint/legacy_alignment/`

It contains old execution queues, prompt-dispatch history, early reviews and former
top-level `human/` documents. It is explicitly non-authoritative.

## Navigation

Machine-readable coordination navigation is in:

`coordination/index.yaml`

Cross-repository derived navigation is in:

`indexes/`
