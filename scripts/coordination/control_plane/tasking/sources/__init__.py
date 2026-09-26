# Task-source adapters normalize provenance only; they grant no authority.

from .external_prompt_queue import external_prompt_queue_source
from .manual_internal import manual_internal_source

__all__ = ["external_prompt_queue_source", "manual_internal_source"]
