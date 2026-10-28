"""Synthetic, NON-AUTHORIZING CF10 G2b03B unit tests."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest

MODULE_PATH = Path(__file__).resolve().parents[3] / "scripts/coordination/control_plane/cf10_g2b03b_coverage_candidate_v0_1.py"
SPEC = importlib.util.spec_from_file_location("candidate_script", MODULE_PATH)
assert SPEC and SPEC.loader
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.source_root = self.base / "gate" / "tmp"
        self.target_root = self.base / "coverage"
        self.source_root.mkdir(parents=True)
        self.target_root.mkdir()
        self.source = self.source_root / "coverage.json"
        self.target = self.target_root / "successor.json"
        self.data = b'{"a":"historical evidence","status":"PASS"}\n'
        self.source.write_bytes(self.data)
        self.digest = hashlib.sha256(self.data).hexdigest()
        self.kw = dict(
            source=self.source,
            target=self.target,
            source_root=self.source_root,
            target_root=self.target_root,
            digest=self.digest,
            required_uid=None,
            external_prefix=None,
        )

    def run_action(self, mode="inspect", **more):
        kw = dict(self.kw)
        kw.update(more)
        return m.action(mode=mode, **kw)

    def assert_blocked(self, code=None, mode="inspect", **more):
        with self.assertRaises(m.Blocked) as ctx:
            self.run_action(mode, **more)
        if code:
            self.assertIn(code, str(ctx.exception))

    def test_01_inspect_missing_is_non_authorizing(self):
        out = self.run_action()
        self.assertEqual(out["candidate_state_after"], "MISSING")
        self.assertFalse(out["authority_granted"])

    def test_02_inspect_does_not_create(self):
        self.run_action()
        self.assertFalse(self.target.exists())

    def test_03_mismatched_source_sha(self):
        self.assert_blocked("HISTORICAL_SHA256_MISMATCH", digest="0"*64)

    def test_04_invalid_sha_shape(self):
        self.assert_blocked("EXPECTED_SHA256_INVALID", digest="AAA")

    def test_05_missing_source(self):
        self.source.unlink()
        with self.assertRaises((FileNotFoundError, m.Blocked)):
            self.run_action()

    def test_06_source_symlink(self):
        self.source.unlink()
        other = self.base / "other.json"
        other.write_bytes(self.data)
        self.source.symlink_to(other)
        self.assert_blocked("SYMLINK_PATH_COMPONENT")

    def test_07_parent_symlink(self):
        redirected = self.base / "redirected"
        redirected.mkdir()
        self.target_root.rmdir()
        self.target_root.symlink_to(redirected)
        self.assert_blocked("SYMLINK_PATH_COMPONENT")

    def test_08_target_symlink_even_broken(self):
        self.target.symlink_to(self.base / "missing.json")
        self.assert_blocked("SYMLINK_PATH_COMPONENT")

    def test_09_target_directory(self):
        self.target.mkdir()
        self.assert_blocked("TARGET_NOT_REGULAR")

    def test_10_existing_mismatch_blocks(self):
        self.target.write_text("not a match")
        self.assert_blocked("TARGET_SHA256_MISMATCH")

    def test_11_existing_match_inspects(self):
        self.target.write_bytes(self.data)
        self.assertIn("PRESENT_SHA256_MATCH", self.run_action()["candidate_state_after"])

    def test_12_provision_requires_explicit_confirm(self):
        self.assert_blocked("EXPLICIT_PROVISION_CONFIRMATION_REQUIRED", mode="provision")

    def test_13_provision_exact_bytes(self):
        out = self.run_action("provision", confirm=m.CONFIRM)
        self.assertEqual(self.target.read_bytes(), self.data)
        self.assertTrue(out["state"].startswith("PROVISIONED"))

    def test_14_provision_is_idempotent(self):
        self.run_action("provision", confirm=m.CONFIRM)
        ino = self.target.stat().st_ino
        out = self.run_action("provision", confirm=m.CONFIRM)
        self.assertEqual(out["state"], "ALREADY_PRESENT_MATCHING_NON_AUTHORIZING")
        self.assertEqual(ino, self.target.stat().st_ino)

    def test_15_existing_wrong_file_not_overwritten(self):
        self.target.write_bytes(b"different")
        ino = self.target.stat().st_ino
        self.assert_blocked("TARGET_SHA256_MISMATCH", mode="provision", confirm=m.CONFIRM)
        self.assertEqual(self.target.stat().st_ino, ino)
        self.assertEqual(self.target.read_bytes(), b"different")

    def test_16_output_has_no_worker_authority(self):
        out = self.run_action("provision", confirm=m.CONFIRM)
        for key in ("authority_granted", "worker_launched", "writer_gate_unquarantined", "dynamic_coverage_verified", "external_independent_attestation", "signed_renewal_performed"):
            self.assertFalse(out[key], key)

    def test_17_target_not_under_root(self):
        self.assert_blocked("TARGET_NOT_IN_DECLARED_TARGET_ROOT", target=self.base / "wrong.json")

    def test_18_source_not_under_root(self):
        self.assert_blocked("SOURCE_NOT_IN_TRUSTED_SOURCE_ROOT", source=self.base / "wrong.json")

    def test_19_target_root_not_in_external_prefix(self):
        self.assert_blocked("TARGET_ROOT_OUTSIDE_EXTERNAL_CF10", external_prefix=self.base / "unrelated")

    def test_20_provision_permissions_0600(self):
        self.run_action("provision", confirm=m.CONFIRM)
        self.assertEqual(stat.S_IMODE(self.target.stat().st_mode), 0o600)

    def test_21_verify_missing_blocks(self):
        self.assert_blocked("EXTERNAL_CANDIDATE_MISSING", mode="verify")

    def test_22_verify_existing_matches(self):
        self.target.write_bytes(self.data)
        out = self.run_action("verify")
        self.assertEqual(out["state"], "VERIFIED_SHA256_MATCH_NON_AUTHORIZING")

    def test_23_missing_target_parent_blocks(self):
        self.target_root.rmdir()
        self.assert_blocked("MISSING_PATH_COMPONENT")

    def test_24_non_json_path_rejected(self):
        with self.assertRaises(m.Blocked):
            m.absolute_path("/test/filename.txt", "SOURCE")

    def test_25_source_and_target_root_equal(self):
        self.assert_blocked("SOURCE_AND_TARGET_ROOTS_EQUAL", target_root=self.source_root, target=self.source_root / "new.json")

    def test_26_source_world_writable_blocks(self):
        self.source.chmod(0o666)
        self.assert_blocked("SOURCE_WRITABLE_BY_GROUP_OR_OTHER")

    def test_27_source_symlink_directory_blocks(self):
        second = self.base / "second"
        second.mkdir()
        self.source_root.rmdir() if not list(self.source_root.iterdir()) else None
        self.source.unlink()
        self.source_root.rmdir()
        self.source_root.symlink_to(second)
        self.assert_blocked("SYMLINK_PATH_COMPONENT")

    def test_28_under_equal_is_not_descendant(self):
        self.assertFalse(m.under(self.source_root, self.source_root))

    def test_29_head_guard(self):
        result = subprocess.run(["git", "init", "-q", str(self.base / "repo")], capture_output=True)
        self.assertEqual(result.returncode, 0)
        repo = self.base / "repo"
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-q", "--allow-empty", "-m", "init"], check=True)
        head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(m.check_head(repo, head), head)
        with self.assertRaises(m.Blocked):
            m.check_head(repo, "f" * 40)

    def test_30_report_serializable(self):
        out = self.run_action()
        self.assertEqual(json.loads(json.dumps(out))["schema_version"], "cf10_g2b03b_candidate_result_v0_1")


if __name__ == "__main__":
    unittest.main()
