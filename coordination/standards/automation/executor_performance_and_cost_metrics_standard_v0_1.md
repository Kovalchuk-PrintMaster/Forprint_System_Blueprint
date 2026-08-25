# Executor Performance and Cost Metrics Standard v0.1

## Purpose

Create evidence for deciding which AI/model/provider works well for which module/task type.

## Attribution

Every measured package should preserve, where available:

- executor family/provider;
- model/version;
- module;
- task/work-package type;
- roadmap refs;
- date/time;
- spend;
- weighted work delivered;
- review outcome.

## Core metrics

Useful metrics may include:

- weighted units delivered;
- cost per weighted unit;
- lead time;
- first-pass acceptance rate;
- rework rate;
- retry count;
- defect/regression rate;
- report quality;
- clarification burden;
- budget variance;
- 30/90-day velocity trend.

## Interpretation

Do not conclude that one model is globally superior from a small sample.

Compare:

- similar task types;
- similar work weights;
- similar module complexity;
- similar evidence requirements.

Qualitative reviewer notes remain important.

## Model switching

The portfolio may deliberately assign different executors/providers to different modules when data
suggests better:

- quality;
- speed;
- cost;
- reasoning fit;
- tool fit.

The dashboard should make this visible rather than binding the ecosystem permanently to one provider.
