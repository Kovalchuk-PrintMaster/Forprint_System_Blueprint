# Operations Assistant — Physical Quantity Estimation Target State v0.1

Status: PROVISIONAL / SYNTHETIC

Goal: estimate stock quickly where piece-by-piece counting is wasteful.

Examples:
- paper/sheet count from stack height;
- small parts from weight;
- sealed packs from pack count;
- later other validated proxies.

When goods receipt introduces a material without an estimation profile, raise a non-blocking
calibration advisory.

Guided calibration:

`known reference quantity -> measure height/weight/etc. -> derive coefficient -> review/confirm -> store profile`

Candidate profile fields include material id, method type, reference quantity, measurement,
coefficient, tolerance, calibration date, evidence, supplier/batch applicability, confidence and
recalibration state.

Operations Assistant collects observations; Warehouse may use them operationally; Accounting
consumes confirmed receipt facts. Canonical profile semantics belong to Library or an explicitly
governed material-profile contract.
