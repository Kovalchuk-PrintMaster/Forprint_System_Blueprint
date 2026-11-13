"""Offline and negative regression tests. No production, auth or network required."""
from __future__ import annotations

import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

MODULE_PATH = (
    Path(__file__).resolve().parents[4]
    / "scripts/coordination/control_plane/worker_runtime/cf10_canonical_e2e_regression_v0_1.py"
)
spec = importlib.util.spec_from_file_location("cf10_canonical_e2e_regression_v0_1", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def fixture_sources():
    data = {rel: "# synthetic test component\n" for rel in mod.COMPONENTS.values()}
    for (key, name), calls in mod.REQUIRED_CALLS.items():
        rel = mod.COMPONENTS[key]
        data[rel] += "def " + name + "():\n"
        for call in calls:
            data[rel] += "    " + call + "()\n"
        data[rel] += "\n"
    for key, names in mod.REQUIRED_FUNCTIONS.items():
        rel = mod.COMPONENTS[key]
        existing = {n for (k, n) in mod.REQUIRED_CALLS if k == key}
        for fn in names:
            if fn not in existing:
                data[rel] += "def " + fn + "():\n    pass\n\n"
    data[mod.COMPONENTS["systemd_backend"]] += "LIVE_CUTOVER_ENABLED = False\n"
    return data


class CanonicalE2ERegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cf10-source-ci-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for rel, source in fixture_sources().items():
            f = self.root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(source, encoding="utf-8")

    def test_good_graph(self):
        result = mod.inspect_graph(self.root)
        self.assertTrue(result["graph_valid"])
        self.assertEqual(result["status"], "PASS_CANONICAL_E2E_REUSE_GRAPH")
        self.assertEqual(len(result["component_sha256"]), len(mod.COMPONENTS))

    def test_missing_existing_canonical_function_is_blocked(self):
        p = self.root / mod.COMPONENTS["cycle"]
        p.write_text(p.read_text().replace("def advance_cycle():", "def different_cycle():"))
        result = mod.inspect_graph(self.root)
        self.assertFalse(result["graph_valid"])
        self.assertIn("dispatch_intent.finalize_cf10_workspace_result_artifact", result["checks"]["cycle.advance_cycle"]["missing_calls"])

    def test_broken_cutover_is_blocked(self):
        p = self.root / mod.COMPONENTS["systemd_route"]
        p.write_text(p.read_text().replace("backend.launch_after_owner_claim()", "backend.other_launcher()"))
        result = mod.inspect_graph(self.root)
        self.assertFalse(result["graph_valid"])
        self.assertIn("backend.launch_after_owner_claim", result["checks"]["systemd_route.run_once"]["missing_calls"])

    def test_legacy_production_fallback_is_blocked(self):
        p = self.root / mod.COMPONENTS["cycle"]
        p.write_text(p.read_text().replace(
            "modern_route.run_once()", "modern_route.run_once()\n    launcher.launch_process()",
        ))
        result = mod.inspect_graph(self.root)
        self.assertFalse(result["checks"]["no_legacy_production_fallback"]["valid"])

    def test_backend_cutover_true_is_blocked(self):
        p = self.root / mod.COMPONENTS["systemd_backend"]
        p.write_text(p.read_text().replace("LIVE_CUTOVER_ENABLED = False", "LIVE_CUTOVER_ENABLED = True"))
        result = mod.inspect_graph(self.root)
        self.assertFalse(result["graph_valid"])
        self.assertFalse(result["canonical_production_cutover_closed"])

    def test_missing_file_is_blocked(self):
        (self.root / mod.COMPONENTS["registry"]).unlink()
        with self.assertRaises(mod.RegressionHold):
            mod.inspect_graph(self.root)

    def test_symlink_component_is_blocked(self):
        target = self.root / mod.COMPONENTS["registry"]
        alternate = target.with_suffix(".old")
        target.rename(alternate)
        target.symlink_to(alternate)
        with self.assertRaises(mod.RegressionHold):
            mod.inspect_graph(self.root)

    def test_symlink_parent_is_blocked(self):
        d = self.root / "scripts/coordination/control_plane/worker_runtime"
        other = self.root / "redirect"
        d.rename(other)
        d.symlink_to(other, target_is_directory=True)
        with self.assertRaises(mod.RegressionHold):
            mod.inspect_graph(self.root)

    def test_syntax_error_is_blocked(self):
        p = self.root / mod.COMPONENTS["adapter"]
        p.write_text("def invalid(:\n")
        with self.assertRaises(mod.RegressionHold):
            mod.inspect_graph(self.root)

    def test_source_only_never_runs_a_provider(self):
        with patch.object(mod, "probe_existing_source_checks", side_effect=AssertionError("must not be called")):
            report = mod.build_report(self.root, "source-only")
        self.assertEqual(report["status"], "PASS_SOURCE_INTEGRATION_ONLY_NO_LIVE_AUTHORITY")
        self.assertEqual(report["gates_open"], list(mod.GATES))
        self.assertFalse(report["live_worker_authorized"])
        self.assertTrue(report["canonical_source_checks"]["not_run"])

    def test_crossplane_reuses_existing_modules_only(self):
        seen = []
        def runner(args, **kw):
            seen.append((args, kw))
            index = len(seen) - 1
            marker = mod.PROBES[index][2]
            return subprocess.CompletedProcess(args, 0, stdout=(marker+"\n"+mod.REQUIRED_PROBE_CLOSURES[index]+"\n").encode())
        report = mod.build_report(self.root, "crossplane", runner=runner)
        self.assertEqual(report["status"], "PASS_SOURCE_INTEGRATION_ONLY_NO_LIVE_AUTHORITY")
        self.assertEqual(len(seen), 3)
        for args, kw in seen:
            self.assertEqual(args[0], sys.executable)
            self.assertEqual(args[1], "-m")
            self.assertEqual(args[3:5], ["--mode", "source-check"])
            self.assertNotIn("--launch", args)
            self.assertEqual(kw["env"]["HOME"], "/nonexistent")
            self.assertNotIn("GH_TOKEN", kw["env"])
            self.assertNotIn("COPILOT_GITHUB_TOKEN", kw["env"])

    def test_source_check_must_prove_gates_remain_open(self):
        def runner(args, **kw):
            marker = next(row[2] for row in mod.PROBES if row[1] == args[2])
            return subprocess.CompletedProcess(args, 0, stdout=(marker+"\n").encode())
        report = mod.build_report(self.root, "crossplane", runner=runner)
        self.assertEqual(report["status"], "HOLD_CANONICAL_E2E_SOURCE_INTEGRATION")
        self.assertFalse(report["canonical_source_checks"]["all_existing_checks_pass"])

    def test_source_check_runner_exception_is_hold(self):
        def runner(*a, **k):
            raise subprocess.TimeoutExpired(a[0], 35)
        report = mod.build_report(self.root, "crossplane", runner=runner)
        self.assertEqual(report["status"], "HOLD_CANONICAL_E2E_SOURCE_INTEGRATION")
        self.assertTrue(all(r["status"] == "HOLD_SOURCE_CHECK_RUNNER" for r in report["canonical_source_checks"]["checks"].values()))

    def test_incomplete_evidence_never_closes_gates(self):
        p = self.root / mod.COMPONENTS["systemd_route"]
        p.write_text(p.read_text().replace("durable.record_terminal()", "durable.record_later()"))
        report = mod.build_report(self.root, "crossplane")
        self.assertEqual(report["status"], "HOLD_CANONICAL_E2E_SOURCE_INTEGRATION")
        self.assertEqual(report["gates_open"], list(mod.GATES))
        self.assertEqual(report["canonical_source_checks"], {"not_run": True})

    def test_unrecognized_mode_fails_closed(self):
        with self.assertRaises(mod.RegressionHold):
            mod.build_report(self.root, "launch")

    def test_graph_status_does_not_claim_actual_inference(self):
        doc = mod.build_report(self.root)
        self.assertFalse(doc["real_authenticated_inference_proven"])
        self.assertFalse(doc["root_owned_credential_delegation_proven"])
        self.assertFalse(doc["production_claim_consumed"])
        self.assertEqual(len(doc["blockers"]), 5)


if __name__ == "__main__":
    unittest.main()
