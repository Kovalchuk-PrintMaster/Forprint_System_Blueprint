<!-- Integrated from Evening Architecture Package v1.0 on 2026-08-30. This document does not change release/H10 authority by itself. -->

# 05. Production Operation Standard & Actual Variance v1.0

## Goal

Для кожної production operation мати:
1. норматив;
2. planned projection конкретного order;
3. actual result;
4. variance;
5. controlled standard-change proposal.

## Terminology

- `Production Routing` — sequence of operations.
- `Operation Standard` — canonical operation norm.
- `Makeready / Setup Allowance` — setup/приладка.
- `Expected Process Waste` — нормативний технологічний відхід.
- `Expected Cycle Time` — нормативний час.
- `Actual Consumption` — фактична витрата.
- `Actual Process Waste / Scrap` — фактичний брак/відхід.
- `Actual Cycle Time` — фактичний час.
- `Downtime` — простій.
- `Rework` — повторна обробка.
- `Yield` — good output/input.
- `Variance` — відхилення actual від planned/standard.

## Operation Standard model

```yaml
operation_standard_id: ...
operation_type: ...
machine_scope: ...
material_scope: ...
quantity_band: ...
setup_allowance: ...
expected_waste_rule: ...
expected_cycle_time_rule: ...
capacity_per_batch: ...
repeat_setup_rule: ...
control_sample_rule: ...
revision: ...
status: ACTIVE
```

## Piecewise rules

Норматив не обов'язково є одним коефіцієнтом.

Приклад:
- 0–500 units: 1 batch;
- 501–1000: 2 batches;
- >1000: capacity-based batch count;
- repeat setup after configured threshold;
- extra control samples on long runs.

Calculator uses this for:
- material plan;
- technical waste;
- price/cost;
- production duration;
- deadline estimate.

## Actual operation event

```yaml
order_id: ...
operation_id: ...
machine_id: ...
material_batch_id: ...
started_at: ...
finished_at: ...
actual_consumption: ...
actual_good_output: ...
actual_scrap: ...
actual_rework: ...
downtime: ...
variance_reason: ...
```

## Lightweight executor input

Executor is not forced into detailed accounting.

Fast signal:
- normal;
- slightly above norm;
- approx x2;
- approx x5;
- severe variance;
- machine problem/downtime.

Optional short voice note.

Example:
«На приладку пішло приблизно 50 листів, машина нестабільно тримала зведення».

System can compare:
planned setup = 10
operator estimate ≈ 50
variance ≈ x5

and notify supervisor.

## Supervisor refinement

Supervisor may:
- confirm exact quantities;
- classify cause;
- bind machine/material batch;
- confirm scrap/rework;
- initiate maintenance/quality follow-up.

## Waste categories must not be merged

Separate:
- setup waste;
- production scrap;
- rework consumption;
- test/control samples;
- destroyed WIP;
- normal trim/cut waste.

This avoids double write-off.

## Units

Canonical unit normalization is required:
- sheets;
- pieces;
- meters;
- square meters;
- kilograms;
- rolls;
- packs;
- other domain units.

## Learning loop

Actual history may generate a standard-change proposal:

```text
actual history
→ analytics
→ systematic deviation detected
→ proposal
→ responsible review
→ new standard revision
```

Raw telemetry/variance must never silently rewrite normative standards.

## Ownership

- Calculator Engine — norms/planning/cost/time;
- Operations Control Registry — routing + planned vs actual;
- Operations Assistant — fast human capture;
- Warehouse — physical material truth/write-off;
- Accounting — actual cost effect;
- ForPrint Library — operation/material/machine identities and reference knowledge;
- Production Runtime Inspector — telemetry/downtime/machine evidence.
