# ForPrint Mutation Compiler

`forprint_mutation_compiler` is a language-agnostic bounded mutation preparation and apply layer.

It sits between generated candidate code/configuration and durable repository state:

```text
candidate change set
        ↓
isolated staging
        ↓
language/tool adapters
        ↓
safe repair fixpoint
        ↓
project-shaped verification copy
        ↓
project-relative language repair/final checks
        ↓
optional project gates
        ↓
atomic bounded apply
        ↓
optional post-apply gates
        ↓
external dirty-baseline verification
        ↓
evidence
```

The compiler core does not assume Python. Python, JSON, YAML, shell and JavaScript are v0.1
adapters; future modules can add TypeScript, Go, Rust and other toolchain adapters.


## Canonical subsystem surfaces

- contract: `coordination/standards/automation/mutation_compiler_contract_v0_1.yaml`
- toolchain profile registry: `coordination/registry/mutation_compiler_toolchains_v0_1.yaml`

The contract defines invariants. The toolchain registry defines current adapter/tool
profiles. Neither generated mutation evidence nor compiler reports are project authority.

## Safety model

- pre-existing dirty working-tree state is valid;
- only declared target paths may change;
- protected internal targets such as `.git/` and `tmp/mutation_compiler/` are rejected before apply;
- safe mechanical repairs may run in staging;
- Python/Ruff repair is finalized again at canonical repository-relative paths inside the isolated project copy before durable apply, so staging-path import classification cannot become durable state;
- unsafe/semantic repairs are forbidden in v0.1;
- check mode never modifies files;
- apply uses atomic replacement;
- any failure after bounded apply begins restores every declared target, including partial multi-file apply failures;
- rollback also removes empty parent directories created solely for new targets during the failed apply;
- project gates run only inside an isolated verification workspace, never in the durable repository;
- pre-command gates run against the copied baseline before candidate overlay;
- post-command gates run against the copied project with staged candidate files overlaid, still before durable apply;
- durable apply begins only after all candidate/project verification gates pass;
- the compiler never stages/commits/pushes Git changes;
- evidence is written under `tmp/mutation_compiler/`.

## CLI

Check candidate files without repair or apply:

```bash
python -m scripts.coordination.mutation_compiler check \
  --candidate-root tmp/my_candidate \
  --target-root . \
  --path scripts/example.py
```

Run safe repairs in internal staging, but do not apply:

```bash
python -m scripts.coordination.mutation_compiler repair-check \
  --candidate-root tmp/my_candidate \
  --target-root . \
  --path scripts/example.py
```

Repair, validate and run a baseline project gate in an isolated verification workspace:

```bash
python -m scripts.coordination.mutation_compiler apply \\
  --candidate-root tmp/my_candidate \\
  --target-root . \\
  --path scripts/example.py \\
  --pre-command "python -m pytest -q tests/coordination/test_mutation_compiler_v0_1.py"
```

Repair, validate, run candidate project gates in isolation, then atomically apply:

```bash
python -m scripts.coordination.mutation_compiler apply \
  --candidate-root tmp/my_candidate \
  --target-root . \
  --path scripts/example.py \
  --post-command "python -m pytest -q tests/test_example.py"
```

`--pre-command` and `--post-command` use argv parsing (`shell=False`) and execute only in a
disposable verification workspace. In v0.1, `--post-command` is retained as the compatibility
name for a candidate-verification gate; it runs before durable apply after staged files are
overlaid into that workspace.
