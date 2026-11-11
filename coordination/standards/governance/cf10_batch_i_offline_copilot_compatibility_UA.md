# CF10 / Large Batch I — Offline Copilot Executable Compatibility

**Scope:** disposable, root-guarded `systemd-run` one-shot on s01. The exact
R115-pinned, root-owned `/usr/local/bin/forprint-copilot-1.0.107` is executed
with **only** `--version` inside a restricted systemd process tree. No prompt,
no login/auth/token, no tool call, no repo editing, no MCP or inference.

## Proof boundaries

1. Root compares executable bytes, owner, mode, symlink-free inode with the
   canonical R115 length and SHA-256 before the disposable launch. This is **not**
   an execfd pinned production authorization. No other provider or version.
2. The `forprint-runner` child performs a one-time handshake using a root-owned
   Unix socket; the root controller checks SO_PEERCRED, `/proc/$pid/cgroup`,
   private network namespace and effective transient unit properties **before**
   allowing the `--version` subprocess.
3. No environment variables for auth/proxy are inherited by the subprocess.
   HOME/XDG paths point into the disposable `/run` fixture.
4. The child reports only bounded stdout/stderr lengths and SHA-256 and the
   expected version/returncode; command output itself is **never exported**.
5. AF_INET/AF_INET6 socket creation and reading a root-only fake credential
   must fail. The systemd unit is stopped and read back before Git checkpoint.
6. Original launch code (R030/R115/R140) and Hestia/systemd services unchanged;
   no claim, no Copilot inference, no Dispatcher live attempt.

## Fail-closed restrictions

`PrivateNetwork=yes`, `RestrictAddressFamilies=AF_UNIX`, `IPAddressDeny=any`,
`ProtectHome=yes`, `InaccessiblePaths=/var/lib/forprint-runner`,
`NoNewPrivileges=yes`, `ProtectSystem=strict`, `PrivateTmp=yes`.

No general IPv4 or IPv6 egress; no live Copilot provider inference.
CLI startup may legitimately fail because this profile is stricter than
production. Such a failure is HOLD, not reason to relax the profile.

## Attestation limits

`--version` passing is evidence of **offline CLI executable compatibility only**.
It does not prove runtime auth, inference through the TLS bridge, G1–G5,
full PIDFD subtree, kernel `populated=1→0`, terminal ledger, or safe production
launch. A successful `systemctl stop` does not substitute for kernel proof.

Use one ZIP / one Make CLI test / one evidence archive. Source commit/push
only after regression + disposable lab PASS. Do not re-run a consumed lab unit.
