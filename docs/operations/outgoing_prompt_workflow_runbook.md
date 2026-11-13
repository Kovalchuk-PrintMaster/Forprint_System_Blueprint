# Outgoing Prompt Workflow Runbook

## Preconditions

Run from the Blueprint repository with a clean, intentional worktree.

Validate:

```bash
make check
python scripts/coordination/validate_prompt_queue.py
```

The workflow CLI previews by default. Mutation requires `--apply`.

## Author a source prompt

Copy and complete:

```text
coordination/templates/outgoing_prompt_template.md
```

Keep the source outside the canonical module `drafts/` and `approved/`
directories. A suitable Blueprint-owned staging location is:

```text
operator_input/prompts/
```

## Preview preparation

```bash
python scripts/coordination/manage_outgoing_prompt.py prepare \
  --source operator_input/prompts/<prompt>.md
```

The preview must report one destination under:

```text
coordination/outgoing_prompts/<module>/drafts/
```

No file is written.

## Apply preparation

```bash
python scripts/coordination/manage_outgoing_prompt.py prepare \
  --source operator_input/prompts/<prompt>.md \
  --apply
```

Then validate:

```bash
python scripts/coordination/validate_prompt_queue.py
python scripts/validate_outgoing_prompts.py
git diff --check
git status --short
```

Preparation must not change the module queue index.

## Preview release

Release remains blocked until the governance policy explicitly authorizes the
target module and points to an existing authorization evidence file.

```bash
python scripts/coordination/manage_outgoing_prompt.py release \
  --module <module_id> \
  --prompt-id <prompt_id>
```

A successful preview reports:

- prepared source;
- approved destination;
- queue index;
- next sequence;
- no writes performed.

## Apply release

```bash
python scripts/coordination/manage_outgoing_prompt.py release \
  --module <module_id> \
  --prompt-id <prompt_id> \
  --apply
```

Then validate:

```bash
python scripts/coordination/validate_prompt_queue.py
python scripts/validate_outgoing_prompts.py
make check
git diff --check
git status --short
```

Inspect the queue record and approved artifact before committing.

## Expected released state

```yaml
module_execution:
  status: ready_for_module_pull
blueprint_review:
  status: not_started
```

The module may read the released prompt. Blueprint acceptance remains a
separate later decision.

## Prohibited operations

Do not manually:

- add a ready queue record without an approved artifact;
- move a prompt to `sent/` to simulate release;
- update the legacy dispatch index as part of this workflow;
- release while policy is gated;
- write to a module repository;
- combine release with commit, push or merge.
