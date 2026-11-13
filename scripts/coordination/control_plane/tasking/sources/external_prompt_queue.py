# Existing outgoing-prompt provenance adapter.
# It does not parse or replace the canonical prompt-queue contract.

from __future__ import annotations


def external_prompt_queue_source(
    *,
    queue_ref: str,
    prompt_id: str,
    approved_prompt_ref: str,
) -> dict[str, object]:
    values = {
        "queue_ref": queue_ref,
        "prompt_id": prompt_id,
        "approved_prompt_ref": approved_prompt_ref,
    }
    for key, value in values.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} is required")
    return {
        "type": "EXTERNAL_PROMPT_QUEUE",
        "generation_mode": "EXTERNAL_QUEUE",
        "queue_ref": queue_ref.strip(),
        "prompt_id": prompt_id.strip(),
        "approved_prompt_ref": approved_prompt_ref.strip(),
        "prompt_queue_grants_worker_authority": False,
        "raw_chat_is_authority": False,
    }
