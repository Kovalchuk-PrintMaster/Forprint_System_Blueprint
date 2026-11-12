# CF10 AH · Executable Copilot in the same governed physical leaf (offline only)

## Reused boundaries

AG canonical Dispatcher APIs: prepare → exact synthetic ACK → dispatch-preview → nonce.
AE actual delegated `forprint-runner` systemd process → root IPC → pinned leaf cgroup 1→0 → retained readback.
The `ad` child source is installed permanently in the Git tracked canonical tree; the disposable copy in `/run` is a staging fixture only.

## This milestone

New **explicit** optional AE mode runs pinned `/usr/local/bin/forprint-copilot-1.0.107 --version` from inside the already delegated Worker cgroup, with no credentials and no external networking. After CLI result proof the existing synthetic digest is used for the AG causal nonce join. The original AE/AG modes are unchanged by default.

## Remaining blockers

G1 real provider network policy/upstream; G2 a provider-auth method with proven nonexposure to child tools; G3 real authenticated model output; G4 production dispatcher and single-use owner claim; G5 a real Worker kernel+ledger terminal. A no-network version probe cannot close any of them.
