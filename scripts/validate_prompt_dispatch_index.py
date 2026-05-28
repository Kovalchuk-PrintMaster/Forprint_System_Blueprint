"""
📄 Назва: validate_prompt_dispatch_index.py

🧠 Призначення:
Перевіряє machine/prompt_dispatch_index.yaml.

Головний результат:
- підтверджує, що всі target_module існують у machine/modules.yaml;
- підтверджує, що всі prompt_file реально існують;
- підтверджує, що статуси належать до дозволеного набору;
- підтверджує, що expected_response_location існує як директорія.

🔗 Залежності:
Залежить від:
- machine/modules.yaml;
- machine/prompt_dispatch_index.yaml;
- coordination/outgoing_prompts/*;
- coordination/incoming_requests/*.

Від цього скрипта залежить:
- ручний контроль prompt dispatch;
- майбутній Project Inspector;
- make check після підключення цієї перевірки.

🗂 Шляхи / налаштування:
- machine/modules.yaml
- machine/prompt_dispatch_index.yaml
- coordination/outgoing_prompts/
- coordination/incoming_requests/

🔍 Аудит і рекомендації:
Зараз перевірка легка і файлова. Пізніше можна додати перевірку переходів статусів
і контроль того, чи prompt уже перенесено з drafts/ до sent/.

✅ Актуальність:
Працює у файловій моделі Blueprint без бази даних.

📦 Пропозиції на майбутнє:
- додати CLI-фільтр по module_id;
- додати генерацію Markdown-таблиці;
- додати статусні переходи draft → approved → sent → reviewed.

▶️ Приклади запуску:
  - python scripts/validate_prompt_dispatch_index.py
"""

from __future__ import annotations

# Дозволяє запускати скрипт напряму: python scripts/name.py
if __package__ is None or __package__ == "":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

import sys
from pathlib import Path
from typing import Any

from scripts.blueprint_utils import ValidationResult, load_yaml, project_root

ALLOWED_STATUSES = {"draft", "approved", "sent", "reviewed", "archived"}
ALLOWED_PRIORITIES = {"critical", "high", "medium", "low"}
ALLOWED_RESPONSE_TYPES = {
    "module_alignment_report",
    "module_bootstrap_plan",
    "module_boundary_correction_report",
    "module_stabilization_completion_report",
}


def _items(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    """Повертає список словників з YAML за ключем."""

    value = data.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"Expected list under key '{key}'")
    return value


def _known_modules(root: Path) -> set[str]:
    """Повертає набір module_id з machine/modules.yaml."""

    modules_data = load_yaml(root / "machine/modules.yaml")
    return {item["id"] for item in _items(modules_data, "modules")}


def validate_prompt_dispatch_index(root: Path | None = None) -> ValidationResult:
    """Валідує prompt dispatch index."""

    root = root or project_root()
    errors: list[str] = []
    warnings: list[str] = []

    index_path = root / "machine/prompt_dispatch_index.yaml"
    if not index_path.exists():
        errors.append("machine/prompt_dispatch_index.yaml does not exist")
        return ValidationResult(ok=False, errors=errors, warnings=warnings)

    known_modules = _known_modules(root)
    index_data = load_yaml(index_path)
    prompts = _items(index_data, "prompt_dispatch")

    if not prompts:
        errors.append("prompt_dispatch list must not be empty")

    seen_ids: set[str] = set()

    for item in prompts:
        prompt_id = item.get("id")
        target_module = item.get("target_module")
        status = item.get("status")
        priority = item.get("priority")
        prompt_file = item.get("prompt_file")
        response_location = item.get("expected_response_location")

        if not isinstance(prompt_id, str) or not prompt_id:
            errors.append("prompt item has missing or invalid id")
        elif prompt_id in seen_ids:
            errors.append(f"duplicate prompt id: {prompt_id}")
        else:
            seen_ids.add(prompt_id)

        if target_module not in known_modules:
            errors.append(f"prompt '{prompt_id}' references unknown target_module: {target_module}")

        if status not in ALLOWED_STATUSES:
            errors.append(f"prompt '{prompt_id}' has invalid status: {status}")

        if priority not in ALLOWED_PRIORITIES:
            errors.append(f"prompt '{prompt_id}' has invalid priority: {priority}")

        if not isinstance(prompt_file, str) or not prompt_file:
            errors.append(f"prompt '{prompt_id}' has missing prompt_file")
        elif not (root / prompt_file).exists():
            errors.append(f"prompt '{prompt_id}' prompt_file does not exist: {prompt_file}")

        if not isinstance(response_location, str) or not response_location:
            errors.append(f"prompt '{prompt_id}' has missing expected_response_location")
        elif not (root / response_location).exists():
            warnings.append(
                f"prompt '{prompt_id}' expected_response_location does not exist yet: "
                f"{response_location}"
            )

        response_type = item.get("expected_response_type")
        if response_type not in ALLOWED_RESPONSE_TYPES:
            errors.append(
                f"prompt '{prompt_id}' has invalid expected_response_type: {response_type}"
            )

    return ValidationResult(ok=not errors, errors=errors, warnings=warnings)


def main() -> int:
    """CLI entry point."""

    result = validate_prompt_dispatch_index()

    if result.warnings:
        print("⚠️ Prompt dispatch index warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")

    if result.errors:
        print("❌ Prompt dispatch index validation failed:")
        for error in result.errors:
            print(f"  - {error}")
        return 1

    print("✅ Prompt dispatch index validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())