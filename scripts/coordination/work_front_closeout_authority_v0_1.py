"""Domain-separated, independent Work Front closeout approval verifier.

No trust bootstrap or signing is provided by this module. The live CLI reads a
root-controlled system policy, never a policy path supplied by the caller.
"""
from __future__ import annotations
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

PURPOSE = "FORPRINT_WORK_FRONT_CLOSEOUT_ACCEPTANCE_V0_1"
DECISION_SCHEMA = "forprint_work_front_closeout_signed_decision_v0_1"
TRUST_SCHEMA = "forprint_work_front_closeout_external_trust_v0_1"
TRUST_ROOT = Path("/etc/forprint/work_front_closeout/trust_root_v0_1.json")
DOMAIN = b"FORPRINT/WORK_FRONT_CLOSEOUT/ACCEPTANCE/v0.1\x00"

class AuthorityError(RuntimeError):
    pass

def canonical(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")

def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()

def read_canonical(path: Path) -> tuple[dict, bytes]:
    if path.is_symlink() or not path.is_file():
        raise AuthorityError("SOURCE_MISSING_OR_SYMLINK")
    raw = path.read_bytes()
    try:
        doc = json.loads(raw)
    except (UnicodeError, ValueError) as exc:
        raise AuthorityError("JSON_INVALID") from exc
    if not isinstance(doc, dict) or canonical(doc) != raw:
        raise AuthorityError("JSON_NONCANONICAL")
    return doc, raw

def load_system_trust_root() -> dict:
    """Fail closed unless an independent, root-owned policy exists."""
    try:
        if TRUST_ROOT.is_symlink() or not TRUST_ROOT.is_file():
            raise AuthorityError("INDEPENDENT_TRUST_ROOT_UNAVAILABLE")
        st = TRUST_ROOT.stat()
        if st.st_uid != 0 or st.st_mode & 0o022:
            raise AuthorityError("INDEPENDENT_TRUST_ROOT_PERMISSIONS")
        doc, _ = read_canonical(TRUST_ROOT)
        if doc.get("schema_version") != TRUST_SCHEMA or doc.get("enabled_for_canonical_apply") is not True:
            raise AuthorityError("INDEPENDENT_TRUST_ROOT_NOT_APPROVED")
        return doc
    except OSError as exc:
        raise AuthorityError("INDEPENDENT_TRUST_ROOT_UNREADABLE") from exc

def _iso(text: str) -> datetime:
    if not isinstance(text, str):
        raise AuthorityError("DECISION_TIME_INVALID")
    try:
        d = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AuthorityError("DECISION_TIME_INVALID") from exc
    if d.tzinfo is None:
        raise AuthorityError("DECISION_TIME_UNBOUND")
    return d.astimezone(timezone.utc)

def verify_signed_decision(request: dict, request_bytes: bytes, decision: dict,
                           policy: dict, *, now: datetime | None = None) -> dict:
    """Pure verifier. CLI ONLY supplies policy through load_system_trust_root()."""
    if canonical(request) != request_bytes:
        raise AuthorityError("REQUEST_NONCANONICAL")
    if request.get("schema_version") != "forprint_blueprint_work_front_closeout_review_request_v0_1":
        raise AuthorityError("REQUEST_SCHEMA_INVALID")
    if request.get("authority", {}).get("operator_approved") is not False:
        raise AuthorityError("REQUEST_MUST_NOT_CARRY_AUTHORITY")
    if decision.get("schema_version") != DECISION_SCHEMA or decision.get("purpose") != PURPOSE:
        raise AuthorityError("CLOSEOUT_DECISION_SCHEMA_OR_PURPOSE_INVALID")
    if decision.get("decision") != "ACCEPT":
        raise AuthorityError("NOT_ACCEPTED")
    if policy.get("schema_version") != TRUST_SCHEMA or policy.get("enabled_for_canonical_apply") is not True:
        raise AuthorityError("NO_APPROVED_TRUST_ROOT")
    if decision.get("request_id") != request.get("request_id") or decision.get("request_sha256") != digest(request_bytes):
        raise AuthorityError("REQUEST_BINDING_DRIFT")
    binding = request.get("binding")
    if not isinstance(binding, dict):
        raise AuthorityError("REQUEST_BINDING_MISSING")
    for key, value in (("destination", binding.get("canonical_destination")),
                       ("work_front_id", (binding.get("work_front") or {}).get("id")),
                       ("work_id", binding.get("work_id"))):
        if decision.get(key) != value or not value:
            raise AuthorityError("DECISION_BINDING_DRIFT:" + key)
    required = request.get("acceptance_review")
    accepted = decision.get("acceptance")
    if not isinstance(required, list) or not required or not isinstance(accepted, list) or len(required) != len(accepted):
        raise AuthorityError("ACCEPTANCE_SET_INVALID")
    for r, a in zip(required, accepted):
        if (a.get("index") != r.get("index") or a.get("criterion_sha256") != digest(r["criterion"].encode("utf-8"))
                or a.get("accepted") is not True):
            raise AuthorityError("ACCEPTANCE_DECISION_MISMATCH")
    signer = decision.get("signer_id")
    trusted = policy.get("trusted_signers")
    if not isinstance(trusted, dict) or signer not in trusted:
        raise AuthorityError("SIGNER_NOT_TRUSTED")
    public_pem = trusted[signer]
    if not isinstance(public_pem, str) or "BEGIN PUBLIC KEY" not in public_pem:
        raise AuthorityError("SIGNER_KEY_INVALID")
    issued, expires = _iso(decision.get("issued_at")), _iso(decision.get("expires_at"))
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if issued > now or expires <= now or (expires - issued).total_seconds() > 86400:
        raise AuthorityError("APPROVAL_EXPIRED_OR_UNBOUNDED")
    if not isinstance(decision.get("nonce"), str) or len(decision["nonce"]) < 32:
        raise AuthorityError("NONCE_INVALID")
    for name in ("publication_commit", "publication_remote", "publication_ref", "publication_manifest_sha256", "ledger_baseline_sha256"):
        if not isinstance(decision.get(name), str) or not decision[name]:
            raise AuthorityError("DECISION_FIELD_MISSING:" + name)
    if decision["publication_remote"] != policy.get("publication_remote") or decision["publication_ref"] != policy.get("publication_ref"):
        raise AuthorityError("PUBLICATION_POLICY_MISMATCH")
    if decision["ledger_baseline_sha256"] != policy.get("ledger_baseline_sha256"):
        raise AuthorityError("LEDGER_POLICY_MISMATCH")
    signature = decision.get("signature_base64")
    if not isinstance(signature, str):
        raise AuthorityError("SIGNATURE_MISSING")
    try:
        sig = base64.b64decode(signature, validate=True)
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        public = load_pem_public_key(public_pem.encode("ascii"))
        if not isinstance(public, Ed25519PublicKey):
            raise AuthorityError("SIGNER_ALGORITHM_INVALID")
        material = {k: v for k, v in decision.items() if k != "signature_base64"}
        public.verify(sig, DOMAIN + canonical(material))
    except (ValueError, UnicodeError, ImportError, TypeError, AttributeError) as exc:
        raise AuthorityError("SIGNATURE_INVALID_OR_VERIFIER_UNAVAILABLE") from exc
    except Exception as exc:
        if isinstance(exc, AuthorityError):
            raise
        raise AuthorityError("SIGNATURE_INVALID") from exc
    return {"signer_id": signer, "request_sha256": digest(request_bytes),
            "decision_sha256": digest(canonical(decision)), "nonce": decision["nonce"]}
