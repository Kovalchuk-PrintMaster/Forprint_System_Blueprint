# Outgoing Prompt Workflow Recovery

## General rule

Do not rerun a failed mutation until the three canonical locations have been
inspected:

```text
coordination/outgoing_prompts/<module>/drafts/
coordination/outgoing_prompts/<module>/approved/
coordination/outgoing_prompts/<module>/index.yaml
```

The CLI is idempotent only for a fully consistent prepared or released state.
It fails closed for partial state.

## Case 1: prepared draft exists, no approved artifact, no queue record

This is a valid prepared state. Validate the draft, fix release authorization
if required, preview release, then apply release.

## Case 2: approved artifact and queue record exist, prepared draft absent

This is a valid released state. Re-running release returns
`already_released` and preserves module execution status.

## Case 3: approved artifact exists, queue record missing

This is partial release state.

Actions:

1. do not add a queue record manually;
2. preserve `git status --short` and file checksums as evidence;
3. compare the approved artifact with the prepared/source artifact;
4. restore the worktree from the last known good commit or an operator-approved
   backup;
5. rerun preview before applying.

## Case 4: queue record exists, approved artifact missing

This is partial release state.

Actions:

1. do not let a module consume the queue;
2. mark the incident in Blueprint internal governance evidence;
3. restore the missing approved artifact and index together from a known good
   state;
4. run full validation.

## Case 5: prepared and released states both exist

This is conflicting state. The CLI refuses to choose an authority.

Actions:

1. determine whether the queue record was actually exposed to the module;
2. preserve the released state if module work started;
3. otherwise restore the prepared state;
4. record the operator decision;
5. validate before retrying.

## Case 6: transaction reports rollback errors

Stop all prompt mutation.

Capture:

```bash
git status --short
git diff --check
find coordination/outgoing_prompts/<module> -maxdepth 2 -type f -print
```

Do not release another prompt until the index, approved artifact and prepared
draft are reconciled.

## Recovery validation

After any recovery:

```bash
python scripts/coordination/validate_prompt_queue.py
python scripts/validate_outgoing_prompts.py
make check
git diff --check
```

A module must not consume work until all checks are green.
