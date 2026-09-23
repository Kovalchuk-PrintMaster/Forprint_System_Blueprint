# Repository Archive Partition Protocol

## Principles
- logical cohesion first;
- preserve relative paths;
- include a batch manifest;
- exclude secrets, customer data, .git, venvs, caches, node_modules, reproducible build outputs and large irrelevant binaries;
- separate historical/legacy areas when useful;
- keep tests near the code they prove or cross-reference them.

## Manifest
Fields:
module_id, repository_root, batch_id, title, logical_scope, included_paths,
excluded_paths, suspected_cross_batch_dependencies, approximate_file_count,
approximate_uncompressed_size, created_at, notes.

## Naming
`<module_id>__inventory_batch_<NN>__<scope>__YYYY-MM-DD.zip`

## Calculator and Telegram special rule
Explicitly separate:
- active entrypoint path;
- old/alternate entrypoints;
- current architecture;
- prior architecture generations;
- duplicated helpers/domain logic;
- historical prompts/instructions;
- integrations;
- tests that reveal the active branch.

Do not combine all legacy generations into one huge archive when lineage-oriented batches are possible.
