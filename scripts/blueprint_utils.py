# python scripts/blueprint_utils.py
"""
Shared helpers for ForPrint System Blueprint scripts.

Цей файл містить маленькі спільні функції для читання YAML, пошуку кореня
проєкту і підготовки директорій.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ValidationResult:
    """Result of blueprint validation."""

    ok: bool
    errors: list[str]
    warnings: list[str]


def project_root() -> Path:
    """Return repository root based on the location of this script."""

    return Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML file and always return a dictionary."""

    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        loaded = yaml.safe_load(file) or {}

    if not isinstance(loaded, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")

    return loaded


def write_text(path: Path, content: str) -> None:
    """Write UTF-8 text and create parent directories."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def unique_ids(items: list[dict[str, Any]], source_name: str) -> tuple[set[str], list[str]]:
    """Return unique IDs and duplicate/missing-id errors."""

    seen: set[str] = set()
    errors: list[str] = []

    for index, item in enumerate(items):
        item_id = item.get("id")
        if not item_id:
            errors.append(f"{source_name}[{index}] has no id")
            continue
        if item_id in seen:
            errors.append(f"Duplicate id in {source_name}: {item_id}")
        seen.add(item_id)

    return seen, errors
