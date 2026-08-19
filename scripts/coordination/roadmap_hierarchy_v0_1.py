from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DONE_SUBSTEP_STATUSES = {"completed", "accepted", "cancelled", "superseded"}


@dataclass(frozen=True)
class SubstepProgress:
    total: int
    done: int
    blocking_total: int
    blocking_done: int

    @property
    def complete(self) -> bool:
        return self.blocking_done == self.blocking_total

    def compact(self) -> str:
        if self.total == 0:
            return "-"
        return (
            f"{self.done}/{self.total}"
            f" (blocking {self.blocking_done}/{self.blocking_total})"
        )


def substep_progress(step: dict[str, Any]) -> SubstepProgress:
    raw = step.get("substeps")
    if not isinstance(raw, list):
        return SubstepProgress(0, 0, 0, 0)

    items = [item for item in raw if isinstance(item, dict)]
    done = sum(
        1
        for item in items
        if str(item.get("status", "")).strip() in DONE_SUBSTEP_STATUSES
    )
    blocking = [item for item in items if item.get("blocking", True) is True]
    blocking_done = sum(
        1
        for item in blocking
        if str(item.get("status", "")).strip() in DONE_SUBSTEP_STATUSES
    )
    return SubstepProgress(
        total=len(items),
        done=done,
        blocking_total=len(blocking),
        blocking_done=blocking_done,
    )


def validate_roadmap_hierarchy(
    roadmap: list[Any],
    *,
    roadmap_field: str,
    status_values: set[str],
    parent_completion_statuses: set[str],
) -> list[str]:
    errors: list[str] = []
    seen_substep_ids: set[str] = set()

    for step_index, raw_step in enumerate(roadmap, start=1):
        if not isinstance(raw_step, dict):
            continue

        raw_substeps = raw_step.get("substeps")
        if raw_substeps is None:
            continue
        if not isinstance(raw_substeps, list):
            errors.append(f"{roadmap_field}[{step_index}].substeps must be a list")
            continue

        for sub_index, raw_substep in enumerate(raw_substeps, start=1):
            prefix = f"{roadmap_field}[{step_index}].substeps[{sub_index}]"
            if not isinstance(raw_substep, dict):
                errors.append(f"{prefix} must be a mapping")
                continue

            substep_id = raw_substep.get("substep_id")
            if not isinstance(substep_id, str) or not substep_id.strip():
                errors.append(f"{prefix}.substep_id must be a non-empty string")
            elif substep_id in seen_substep_ids:
                errors.append(f"duplicate substep_id: {substep_id}")
            else:
                seen_substep_ids.add(substep_id)

            title = raw_substep.get("title")
            if not isinstance(title, str) or not title.strip():
                errors.append(f"{prefix}.title must be a non-empty string")

            status = raw_substep.get("status")
            if not isinstance(status, str) or not status.strip():
                errors.append(f"{prefix}.status must be a non-empty string")
            elif status not in status_values:
                errors.append(f"{prefix}.status {status!r} is not in status_values")

            blocking = raw_substep.get("blocking", True)
            if not isinstance(blocking, bool):
                errors.append(f"{prefix}.blocking must be a boolean")

            summary = raw_substep.get("summary")
            if summary is not None and (
                not isinstance(summary, str) or not summary.strip()
            ):
                errors.append(
                    f"{prefix}.summary must be a non-empty string when present"
                )

        parent_status = str(raw_step.get("status", "")).strip()
        if parent_status in parent_completion_statuses:
            progress = substep_progress(raw_step)
            if progress.blocking_done != progress.blocking_total:
                step_id = raw_step.get("step_id", f"#{step_index}")
                errors.append(
                    f"roadmap step {step_id!r} is {parent_status!r} but "
                    f"blocking substeps are only "
                    f"{progress.blocking_done}/{progress.blocking_total} done"
                )

    return errors
