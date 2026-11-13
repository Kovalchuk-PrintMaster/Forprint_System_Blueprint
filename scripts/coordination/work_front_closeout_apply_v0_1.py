"""Fail-closed operator-approved, publication-bound Work Front closeout.

No signer enrollment, trust-root creation, Git publishing or attempt mutation.
The live apply is BLOCKED while independently approved /etc trust is absent.
"""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
from datetime import date
from typing import Any
import yaml

from scripts.coordination import work_front_closeout_authority_v0_1 as authority
from scripts.coordination import work_front_closeout_publication_v0_1 as publication

DEST_PREFIX = "coordination/internal_work/blueprint/governance/"
DEST_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}__blueprint__[a-z0-9_]+_completion_v[0-9]+_[0-9]+\.yaml\Z")
RECORD_SCHEMA = "forprint_blueprint_work_front_closeout_completion_v0_1"

class ApplyError(RuntimeError):
    pass

def _safe(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ApplyError("PATH_INVALID")
    p = PurePosixPath(relative)
    if p.is_absolute() or any(part in ("", ".", "..") for part in p.parts) or str(p) != relative:
        raise ApplyError("PATH_TRAVERSAL")
    target = root.joinpath(*p.parts)
    node = root
    for component in p.parts:
        node = node / component
        if node.is_symlink():
            raise ApplyError("SYMLINK_PATH_FORBIDDEN")
    if not target.resolve().is_relative_to(root.resolve()):
        raise ApplyError("PATH_OUTSIDE_ROOT")
    return target

def _read(root: Path, relative: str) -> tuple[dict, bytes]:
    target = _safe(root, relative)
    try:
        return authority.read_canonical(target)
    except authority.AuthorityError as exc:
        raise ApplyError(str(exc)) from exc

def _validate_destination(root: Path, relative: str) -> Path:
    if (not isinstance(relative, str) or not relative.startswith(DEST_PREFIX)
            or not DEST_PATTERN.fullmatch(relative[len(DEST_PREFIX):])):
        raise ApplyError("DESTINATION_NOT_REGISTERED_PATH")
    target = _safe(root, relative)
    parent = target.parent
    if not parent.is_dir():
        raise ApplyError("DESTINATION_PARENT_MISSING")
    if target.exists() or target.is_symlink():
        raise ApplyError("CREATE_ONLY_TARGET_OCCUPIED")
    return target

def _validate_doc_registry(root: Path) -> None:
    registry = _safe(root, "coordination/standards/governance/document_type_registry_v0_1.yaml")
    if not registry.is_file():
        raise ApplyError("DOCUMENT_REGISTRY_MISSING")
    doc = yaml.safe_load(registry.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or not any(
        t.get("document_type") == "internal_work" and t.get("authority_class") == "INTERNAL_WORK_NON_AUTHORITY"
        and "coordination/internal_work/**/*" in t.get("path_patterns", [])
        for t in doc.get("types", []) if isinstance(t, dict)
    ):
        raise ApplyError("DOCUMENT_TYPE_NOT_REGISTERED_AS_NON_AUTHORITY")

def _validate_input_chain(root: Path, request_path: str) -> tuple[dict, bytes, dict]:
    request, raw = _read(root, request_path)
    if request.get("schema_version") != "forprint_blueprint_work_front_closeout_review_request_v0_1":
        raise ApplyError("REQUEST_SCHEMA_INVALID")
    if request.get("status") != "PENDING_AUTHENTICATED_OPERATOR_APPROVAL_AND_PUBLICATION":
        raise ApplyError("REQUEST_STATUS_INVALID")
    binding = request.get("binding")
    if not isinstance(binding, dict):
        raise ApplyError("BINDING_MISSING")
    for k in ("plan", "completion_candidate", "b2_observation", "work_front", "completion_evidence"):
        part = binding.get(k)
        if not isinstance(part, dict):
            raise ApplyError("CHAIN_BINDING_INVALID:" + k)
        # The source evidence is hash-bound, not necessarily serialized as canonical JSON.
        # Never reinterpret its presentation formatting as authority.
        source = _safe(root, part.get("path"))
        if not source.is_file():
            raise ApplyError("CHAIN_SOURCE_MISSING:" + k)
        item_bytes = source.read_bytes()
        if authority.digest(item_bytes) != part.get("sha256"):
            raise ApplyError("CHAIN_DRIFT:" + k)
    plan, _ = _read(root, binding["plan"]["path"])
    candidate, _ = _read(root, binding["completion_candidate"]["path"])
    if plan.get("schema_version") != "forprint_blueprint_work_front_closeout_plan_v0_1":
        raise ApplyError("PLAN_SCHEMA_INVALID")
    if plan.get("work_front") != binding["work_front"] or plan.get("completion_evidence") != binding["completion_evidence"]:
        raise ApplyError("PLAN_REQUEST_BINDING_MISMATCH")
    if candidate.get("input_plan", {}).get("sha256") != binding["plan"]["sha256"]:
        raise ApplyError("CANDIDATE_PLAN_BINDING_MISMATCH")
    if request.get("authority", {}).get("operator_approved") is not False:
        raise ApplyError("REQUEST_CANNOT_GRANT_APPROVAL")
    return request, raw, plan

def _check_ledger(root: Path, policy: dict, baseline: dict, forbidden: str | None) -> dict:
    if policy.get("global_ledger_writer_protocol_approved") is not True:
        raise ApplyError("GLOBAL_WRITER_PROTOCOL_UNAPPROVED")
    if baseline.get("schema_version") != "forprint_closeout_ledger_baseline_v0_1":
        raise ApplyError("LEDGER_BASELINE_SCHEMA_INVALID")
    repo = root / "coordination/continuity/execution_attempts"
    expected = baseline.get("repository_files_sha256")
    if not isinstance(expected, dict) or not expected:
        raise ApplyError("LEDGER_BASELINE_EMPTY")
    actual = {}
    if not repo.is_dir() or repo.is_symlink():
        raise ApplyError("LEDGER_ROOT_INVALID")
    for p in sorted(repo.iterdir()):
        if p.is_symlink() or not p.is_file():
            raise ApplyError("LEDGER_ENTRY_UNSAFE")
        actual[p.name] = authority.digest(p.read_bytes())
    if actual != expected:
        raise ApplyError("HISTORICAL_LEDGER_DRIFT")
    if len([name for name in actual if name.startswith("cf10-u180j-a041__")]) < 2:
        raise ApplyError("A041_BASELINE_ABSENT")
    if forbidden and any(name.startswith(forbidden + "__") for name in actual):
        raise ApplyError("FORBIDDEN_ATTEMPT_IN_LEDGER")
    roots = policy.get("required_runtime_roots")
    if not isinstance(roots, list) or not roots or set(roots) != set(baseline.get("required_runtime_roots", [])):
        raise ApplyError("RUNTIME_SCOPE_NOT_AUTHORIZED")
    scanned = 0
    for root_name in roots:
        p = Path(root_name)
        if not p.is_absolute() or p.is_symlink() or not p.is_dir():
            raise ApplyError("RUNTIME_ROOT_UNAVAILABLE")
        def reject_walk_error(err):
            raise ApplyError("RUNTIME_AUDIT_INCOMPLETE:" + str(err))
        for current, dirs, files in os.walk(p, topdown=True, followlinks=False, onerror=reject_walk_error):
            for name in (*dirs, *files):
                if (Path(current) / name).is_symlink():
                    raise ApplyError("RUNTIME_SYMLINK_UNSAFE")
                scanned += 1
                if forbidden and forbidden in name:
                    raise ApplyError("FORBIDDEN_ATTEMPT_IN_RUNTIME")
            # Audit attempt identifiers in structured runtime facts, not only file names.
            for filename in files:
                fp = Path(current) / filename
                marker = forbidden.encode() if forbidden else None
                if marker:
                    # Binary-safe chunk scan, including tokens spanning chunk boundaries.
                    with fp.open("rb") as f:
                        previous = b""
                        for chunk in iter(lambda: f.read(1024 * 1024), b""):
                            if marker in (previous + chunk):
                                raise ApplyError("FORBIDDEN_ATTEMPT_IN_RUNTIME_CONTENT")
                            previous = chunk[-len(marker):]
    return {"historical_file_count": len(actual), "runtime_entries": scanned, "runtime_roots": roots}

def _lock_path(policy: dict) -> Path:
    from scripts.coordination import execution_attempt_writer_lock_v0_1 as shared_writer
    val = policy.get("approved_global_ledger_lock_path")
    if not isinstance(val, str) or Path(val).parent != shared_writer.APPROVED_LOCK_DIRECTORY:
        raise ApplyError("GLOBAL_LEDGER_LOCK_NOT_APPROVED")
    path = Path(val)
    if path.is_symlink() or not path.parent.is_dir() or path.parent.is_symlink():
        raise ApplyError("GLOBAL_LEDGER_LOCK_UNSAFE")
    # Shared lock must be independently provisioned for canonical ledger writers.
    # Self-asserting a flag in Closeout trust policy is not sufficient.
    try:
        protocol = shared_writer.load_enforced_protocol(required=True)
    except shared_writer.WriterProtocolError as exc:
        raise ApplyError("GLOBAL_WRITER_PROTOCOL_NOT_ENFORCED") from exc
    if (path != protocol["lock_path"]
            or policy.get("approved_global_ledger_writer_protocol_sha256") != protocol["sha256"]):
        raise ApplyError("GLOBAL_LEDGER_LOCK_BINDING_MISMATCH")
    return path

def validate_record(record: dict) -> None:
    if (record.get("schema_version") != RECORD_SCHEMA or record.get("layer") != "GOVERNANCE_COMPLETION"
            or record.get("status") != "PASS" or record.get("authority", {}).get("completion_artifact_grants_execution_authority") is not False
            or record.get("authority", {}).get("completion_artifact_grants_dispatch_authority") is not False
            or record.get("closure", {}).get("whole_work_item_closed") is not False):
        raise ApplyError("COMPLETION_RECORD_SCHEMA_OR_AUTHORITY_INVALID")

def perform_closeout(root: Path, request_path: str, decision_path: str, manifest_path: str,
                     baseline_path: str, *, approved_policy: dict | None = None) -> tuple[Path, dict]:
    """Test injection is explicit; the operator CLI NEVER accepts a policy path."""
    root = root.resolve()
    policy = approved_policy if approved_policy is not None else authority.load_system_trust_root()
    request, request_raw, plan = _validate_input_chain(root, request_path)
    decision, decision_raw = _read(root, decision_path)
    manifest, manifest_raw = _read(root, manifest_path)
    baseline, baseline_raw = _read(root, baseline_path)
    binding = request["binding"]
    target = _validate_destination(root, binding["canonical_destination"])
    _validate_doc_registry(root)
    if authority.digest(baseline_raw) != policy.get("ledger_baseline_sha256"):
        raise ApplyError("LEDGER_BASELINE_HASH_DRIFT")
    auth = authority.verify_signed_decision(request, request_raw, decision, policy)
    if manifest.get("frozen_prepublication_file_sha256") != plan.get("implementation_file_sha256"):
        raise ApplyError("FROZEN_PLAN_TO_PUBLISHED_BLOBS_DRIFT")
    # Last reviewed prepublication state remains sealed as a historical object.
    if binding.get("observed_repository_head") != plan.get("source_state", {}).get("head"):
        raise ApplyError("PREPUBLICATION_HEAD_DRIFT")
    pub = publication.verify_publication(root, request, decision, policy, manifest)
    if publication.git(root, "rev-parse", "HEAD").decode().strip() != pub["commit"]:
        raise ApplyError("LOCAL_CHECKOUT_NOT_PUBLICATION_COMMIT")
    if authority.digest(publication.git(root, "diff", "--cached", "--binary")) != policy.get("approved_staged_diff_sha256"):
        raise ApplyError("PROTECTED_STAGING_DRIFT")
    lock = _lock_path(policy)
    # Without independently approved global lock-writer protocol this always fails.
    with lock.open("a+b") as lock_handle:
        fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ledger = _check_ledger(root, policy, baseline, binding.get("forbidden_attempt_id"))
        _validate_destination(root, binding["canonical_destination"])
        # Revalidate all authority and immutable objects under the writer lock.
        new_request, new_raw, _ = _validate_input_chain(root, request_path)
        if new_raw != request_raw:
            raise ApplyError("REQUEST_CHANGED_DURING_CLOSEOUT")
        if (_safe(root, decision_path).read_bytes() != decision_raw
                or _safe(root, manifest_path).read_bytes() != manifest_raw
                or _safe(root, baseline_path).read_bytes() != baseline_raw):
            raise ApplyError("PROOF_CHANGED_DURING_CLOSEOUT")
        authority.verify_signed_decision(new_request, new_raw, decision, policy)
        if publication.git(root, "rev-parse", "HEAD").decode().strip() != pub["commit"]:
            raise ApplyError("GIT_DRIFT_DURING_CLOSEOUT")
        if authority.digest(publication.git(root, "diff", "--cached", "--binary")) != policy.get("approved_staged_diff_sha256"):
            raise ApplyError("STAGING_CHANGED_DURING_CLOSEOUT")
        if approved_policy is None and authority.load_system_trust_root() != policy:
            raise ApplyError("TRUST_POLICY_CHANGED_DURING_CLOSEOUT")
        # The approval nonce and request may only be used once across records.
        for old in target.parent.glob("*.yaml"):
            if old.is_symlink() or not old.is_file():
                raise ApplyError("EXISTING_COMPLETION_PATH_UNSAFE")
            try:
                old_record = yaml.safe_load(old.read_bytes())
            except (ValueError, yaml.YAMLError) as exc:
                raise ApplyError("EXISTING_COMPLETION_UNREADABLE") from exc
            if not isinstance(old_record, dict):
                continue
            old_approval = old_record.get("operator_decision", {})
            if isinstance(old_approval, dict) and (old_approval.get("nonce") == auth["nonce"] or old_approval.get("request_sha256") == auth["request_sha256"]):
                raise ApplyError("APPROVAL_REPLAY_FORBIDDEN")
        publication.verify_publication(root, request, decision, policy, manifest)
        record = {
            "schema_version": RECORD_SCHEMA,
            "layer": "GOVERNANCE_COMPLETION", "status": "PASS", "completed_at": date.today().isoformat(),
            "slice": {"work_front_id": binding["work_front"]["id"], "work_id": binding["work_id"]},
            "operator_decision": {"request_id": request["request_id"], **auth},
            "implementation": {"published": True, "publication_commit": pub["commit"], "remote": pub["remote"],
                               "ref": pub["ref"], "verified_blob_count": pub["blob_count"]},
            "verification": {"plan_sha256": binding["plan"]["sha256"], "b2_sha256": binding["b2_observation"]["sha256"],
                             "ledger_baseline_sha256": authority.digest(baseline_raw), "ledger_audit": ledger},
            "closure": {"technical_slice_complete": True, "whole_work_item_closed": False,
                        "work_item_status": "ACTIVE", "worker_launch_performed": False},
            "authority": {"completion_artifact_grants_execution_authority": False,
                          "completion_artifact_grants_dispatch_authority": False,
                          "completion_artifact_grants_acceptance_authority": False,
                          "completion_artifact_grants_publication_authority": False},
        }
        validate_record(record)
        blob = yaml.safe_dump(record, allow_unicode=True, sort_keys=False).encode("utf-8")
        # O_EXCL ensures occupied targets never get overwritten.
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o644)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(blob)
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            # Incomplete result must not be mistaken for success; do not silently delete.
            raise
        fcntl.flock(lock_handle, fcntl.LOCK_UN)
    return target, record



def prepare_candidate(root: Path, plan_name: str, candidate_name: str, *, check: bool = False) -> Path:
    """Project-owned B1-compatible prepublication prepare, never an approval."""
    from scripts.coordination import work_front_closeout_v0_1 as stage1
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.json", plan_name) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9_.-]*\.json", candidate_name
    ):
        raise ApplyError("PLAN_OR_CANDIDATE_NAME_INVALID")
    plan, raw = _read(root, "tmp/" + plan_name)
    if plan.get("schema_version") != "forprint_blueprint_work_front_closeout_plan_v0_1":
        raise ApplyError("PLAN_SCHEMA_INVALID")
    front = plan.get("work_front", {})
    evidence = plan.get("completion_evidence", {})
    if not all(isinstance(x, str) and x for x in (front.get("path"), evidence.get("path"))):
        raise ApplyError("PLAN_INPUTS_INVALID")
    regenerated = stage1.make_plan(root, front["path"], evidence["path"],
        forbidden_attempt=(plan.get("forbidden_attempt") or {}).get("attempt_id"))
    if stage1._canonical_json(regenerated) != raw:
        raise ApplyError("PLAN_REGENERATION_DRIFT")
    if plan.get("authority", {}).get("canonical_write_allowed") is not False:
        raise ApplyError("PLAN_AUTHORITY_INVALID")
    review = plan.get("acceptance_review")
    if not isinstance(review, list) or not review:
        raise ApplyError("ACCEPTANCE_SET_EMPTY")
    criteria=[]
    for i, row in enumerate(review, 1):
        if row.get("index") != i or row.get("operator_attestation") != "PENDING_MANUAL_REVIEW":
            raise ApplyError("ACCEPTANCE_NOT_PENDING")
        criteria.append({"index": i,"criterion":row["criterion"],"review_status":"PENDING_OPERATOR_ATTESTATION"})
    evidence_doc=json.loads(_safe(root,evidence["path"]).read_bytes())
    candidate={
        "schema_version":"forprint_blueprint_work_front_completion_candidate_v0_1",
        "status":"PENDING_OPERATOR_REVIEW_AND_PUBLICATION",
        "authority":{"canonical_write_allowed":False,"operator_acceptance_inferred":False,
            "publication_commit_verified":False,"ledger_reconciliation_performed":False,
            "worker_dispatch_allowed":False,"work_item_close_allowed":False,"automatic_git_actions":False},
        "input_plan":{"name":plan_name,"sha256":authority.digest(raw)},
        "work_front":front,"completion_evidence":evidence,"work_id":evidence_doc.get("work_id"),
        "acceptance_review":criteria,
        "proposed_completion_record":{"directory":stage1.CANONICAL_PREFIX,
            "status_if_fully_accepted":"PASS","record_file_created":False,
            "publication_commit":None,"operator_approval_ref":None,
            "historical_ledger_audit_ref":None,"continuity_event_created":False,
            "roadmap_projection_written":False},
        "blocking_requirements":[
            "Independent operator-approval gateway contract and exact signed/validated approval proof",
            "Published implementation Git commit whose blobs match verified evidence",
            "Independent historical-ledger and runtime-attempt absence audit",
            "Accepted canonical internal_work document schema and publication permission",
            "Separate bounded authorization for create-only canonical apply"],
        "canonical_mutation":False,
    }
    encoded=authority.canonical(candidate)
    target=_safe(root,"tmp/"+candidate_name)
    if target.exists():
        if target.read_bytes()!=encoded:
            raise ApplyError("CANDIDATE_EXISTS_WITH_DIFFERENT_BYTES")
    elif check:
        raise ApplyError("CANDIDATE_MISSING")
    else:
        with target.open("xb") as f:
            f.write(encoded)
    return target

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("prepare", "check-candidate", "check-authority", "check-publication", "apply", "verify"))
    p.add_argument("--root", default=".")
    p.add_argument("--request")
    p.add_argument("--decision")
    p.add_argument("--manifest")
    p.add_argument("--baseline")
    p.add_argument("--record")
    p.add_argument("--plan-name")
    p.add_argument("--candidate-name")
    opts = p.parse_args(argv)
    root = Path(opts.root).resolve()
    try:
        if opts.action in ("prepare", "check-candidate"):
            if not opts.plan_name or not opts.candidate_name:
                raise ApplyError("PLAN_AND_CANDIDATE_NAMES_REQUIRED")
            output=prepare_candidate(root,opts.plan_name,opts.candidate_name,check=opts.action=="check-candidate")
            print("WORK_FRONT_CLOSEOUT_CANDIDATE="+("CHECK" if opts.action=="check-candidate" else "PREPARE")+"_PASS_NON_AUTHORIZING")
            print("CANDIDATE="+str(output))
            return 0
        if opts.action == "verify":
            if not opts.record or not opts.decision:
                raise ApplyError("RECORD_AND_DECISION_REQUIRED")
            policy = authority.load_system_trust_root()
            request, raw, _ = _validate_input_chain(root, opts.request)
            decision, _ = _read(root, opts.decision)
            attestation = authority.verify_signed_decision(request, raw, decision, policy)
            if opts.record != request["binding"]["canonical_destination"]:
                raise ApplyError("RECORD_DESTINATION_MISMATCH")
            path = _safe(root, opts.record)
            if not path.is_file():
                raise ApplyError("RECORD_NOT_FOUND")
            data = yaml.safe_load(path.read_bytes())
            validate_record(data)
            if (data.get("operator_decision", {}).get("request_sha256") != attestation["request_sha256"]
                    or data.get("operator_decision", {}).get("decision_sha256") != attestation["decision_sha256"]
                    or data.get("implementation", {}).get("publication_commit") != decision["publication_commit"]):
                raise ApplyError("RECORD_PROVENANCE_INVALID")
            print("WORK_FRONT_CLOSEOUT_VERIFY=PASS")
            return 0
        # Trust-root check ALWAYS precedes any live authority-dependent action.
        if not opts.request:
            raise ApplyError("REQUEST_REQUIRED")
        policy = authority.load_system_trust_root()
        if not opts.decision:
            raise ApplyError("DECISION_REQUIRED")
        request, raw, plan = _validate_input_chain(root, opts.request)
        decision, _ = _read(root, opts.decision)
        auth = authority.verify_signed_decision(request, raw, decision, policy)
        if opts.action == "check-authority":
            print("WORK_FRONT_CLOSEOUT_AUTHORITY=PASS")
            return 0
        if not opts.manifest:
            raise ApplyError("MANIFEST_REQUIRED")
        manifest, _ = _read(root, opts.manifest)
        if manifest.get("frozen_prepublication_file_sha256") != plan.get("implementation_file_sha256"):
            raise ApplyError("FROZEN_PLAN_BLOB_BINDING_DRIFT")
        publication.verify_publication(root, request, decision, policy, manifest)
        if opts.action == "check-publication":
            print("WORK_FRONT_CLOSEOUT_PUBLICATION=PASS")
            return 0
        if not opts.baseline:
            raise ApplyError("BASELINE_REQUIRED")
        target, _ = perform_closeout(root, opts.request, opts.decision, opts.manifest, opts.baseline)
        print("WORK_FRONT_CLOSEOUT_APPLY=PASS")
        print("COMPLETION_RECORD=" + str(target))
        return 0
    except (ApplyError, authority.AuthorityError, publication.PublicationError, OSError, ValueError, yaml.YAMLError) as exc:
        print("WORK_FRONT_CLOSEOUT_ACTION=BLOCKED")
        print("REASON=" + str(exc))
        print("CANONICAL_MUTATION=false_or_unconfirmed")
        return 2

if __name__ == "__main__":
    sys.exit(main())
