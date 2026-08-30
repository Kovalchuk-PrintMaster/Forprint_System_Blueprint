# Roadmap

## Етап 1 — файловий Blueprint

- Створити структуру `forprint_system_blueprint`.
- Заповнити базові YAML-файли.
- Додати валідацію.
- Додати генерацію Mermaid.
- Додати генерацію module guides.

## Етап 2 — робочий prompt / coordination контур

- Вести outgoing prompts для модулів.
- Вести incoming requests від модулів.
- Вести review packets для аналізу великих шматків діалогів або коду.

## Етап 3 — module manifests

- Додати до кожного дочірнього проєкту `forprint_module_manifest.yaml`.
- Навчити Inspector читати manifests.

## Етап 4 — Project Inspector

- Порівняння Blueprint із реальними manifests/status reports.
- Виявлення integration gaps, architecture drift, missing contracts.

## Етап 5 — CRM dashboard

- Показати стан архітектури, модулів, інтеграцій, тестів, відкритих питань.

## Етап 6 — visual editor

- Пізніше можна зробити графічний редактор Blueprint, але не на старті.
