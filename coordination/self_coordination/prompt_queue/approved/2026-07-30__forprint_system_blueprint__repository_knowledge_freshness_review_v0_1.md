---
prompt_id: blueprint_repository_knowledge_freshness_review_v0_1
module_id: forprint_system_blueprint
status: approved
owner: blueprint_coordination_assistant
reviewer: project_owner
created_at: '2026-07-30'
---

# Repository Knowledge Freshness Review

## Objective

Review snapshot freshness and stale-source exceptions before RCI semantic enrichment.

## Required outputs

- Snapshot freshness assessment.
- Stale-source exceptions.
- Bounded refresh decisions.
- RCI enrichment release decision.

## Completion gate

- Full Blueprint checks are GREEN.
- Evidence and completion packet are recorded.
- External rollout remains gated.
