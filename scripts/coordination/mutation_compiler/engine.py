from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from .adapters import AdapterContext, adapter_for
from .git_state import (
    capture_external_baseline,
    file_state,
    sha256,
    verify_external_baseline,
)
from .models import (
    CommandResult,
    CompileReport,
    CompilerPolicy,
    Diagnostic,
    FileResult,
    normalize_relative_path,
)


class MutationCompilerError(RuntimeError):
    pass


class MutationCompilerBoundaryError(MutationCompilerError):
    pass


class MutationCompiler:
    def __init__(
        self,
        *,
        target_root: Path,
        candidate_root: Path,
        paths: list[str],
        mode: str,
        policy: CompilerPolicy | None = None,
        mutation_id: str | None = None,
        pre_commands: list[str] | None = None,
        post_commands: list[str] | None = None,
        evidence_root: Path | None = None,
    ) -> None:
        self.target_root = target_root.resolve()
        self.candidate_root = candidate_root.resolve()
        self.paths = [normalize_relative_path(value) for value in paths]
        self.mode = mode
        self.policy = policy or CompilerPolicy()
        self.mutation_id = mutation_id or f"mutation_{uuid.uuid4().hex[:12]}"
        self.pre_commands = pre_commands or []
        self.post_commands = post_commands or []
        self.evidence_root = (
            evidence_root.resolve()
            if evidence_root
            else self.target_root / "tmp" / "mutation_compiler"
        )

    @property
    def repair(self) -> bool:
        return self.mode in {"repair-check", "apply"}

    @property
    def apply(self) -> bool:
        return self.mode == "apply"

    def _preflight(self) -> None:
        if self.mode not in {"check", "repair-check", "apply"}:
            raise MutationCompilerError(f"unsupported mode: {self.mode}")
        if not self.candidate_root.is_dir():
            raise MutationCompilerError(f"candidate root missing: {self.candidate_root}")
        if self.policy.require_git_root and not (self.target_root / ".git").exists():
            raise MutationCompilerError(f"target root is not a git repository: {self.target_root}")
        if not self.paths:
            raise MutationCompilerError("at least one --path is required")
        if len({path.as_posix() for path in self.paths}) != len(self.paths):
            raise MutationCompilerError("duplicate target paths are forbidden")

        for rel in self.paths:
            rel_text = rel.as_posix()
            for raw_prefix in self.policy.protected_target_prefixes:
                prefix = raw_prefix.strip("/")
                if rel_text == prefix or rel_text.startswith(prefix + "/"):
                    raise MutationCompilerBoundaryError(
                        f"protected target path is forbidden: {rel}"
                    )

            candidate = (self.candidate_root / rel).resolve()
            try:
                candidate.relative_to(self.candidate_root)
            except ValueError as exc:
                raise MutationCompilerBoundaryError(
                    f"candidate escapes candidate root: {rel}"
                ) from exc
            if not candidate.is_file():
                raise MutationCompilerError(f"candidate file missing: {rel}")

            target_parent = (self.target_root / rel).parent.resolve()
            try:
                target_parent.relative_to(self.target_root)
            except ValueError as exc:
                raise MutationCompilerBoundaryError(f"target escapes target root: {rel}") from exc

    def _run_project_command(
        self,
        raw: str,
        *,
        phase: str,
        cwd: Path,
    ) -> CommandResult:
        argv = shlex.split(raw)
        if not argv:
            raise MutationCompilerError("empty project command")
        cp = subprocess.run(
            argv,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            timeout=self.policy.command_timeout_seconds,
        )
        output = cp.stdout
        if cp.stderr:
            output += ("\n" if output else "") + cp.stderr
        return CommandResult(
            argv=argv,
            return_code=cp.returncode,
            stdout=output,
            phase=phase,
        )

    def _run_project_argv(
        self,
        argv: list[str],
        *,
        phase: str,
        cwd: Path,
    ) -> CommandResult:
        cp = subprocess.run(
            argv,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            timeout=self.policy.command_timeout_seconds,
        )
        output = cp.stdout
        if cp.stderr:
            output += ("\n" if output else "") + cp.stderr
        return CommandResult(
            argv=argv,
            return_code=cp.returncode,
            stdout=output,
            phase=phase,
        )

    def _copy_verification_workspace(self, destination: Path) -> None:
        ignore = shutil.ignore_patterns(
            ".git",
            "tmp",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".tox",
            ".nox",
            "__pycache__",
            "node_modules",
            "target",
            "dist",
            "build",
            ".venv*",
            "venv*",
        )
        shutil.copytree(
            self.target_root,
            destination,
            symlinks=True,
            ignore=ignore,
        )

    def _overlay_staged_candidates(
        self,
        staging: Path,
        verification_root: Path,
    ) -> None:
        for rel in self.paths:
            self._atomic_apply_file(
                staging / rel,
                verification_root / rel,
            )

    def _python_target_paths(self) -> list[Path]:
        return [rel for rel in self.paths if rel.suffix.lower() == ".py"]

    def _ruff_executable(self) -> str | None:
        ruff = shutil.which("ruff")
        if ruff:
            return ruff
        candidate = Path(sys.executable).parent / "ruff"
        if candidate.is_file():
            return str(candidate)
        return None

    def _project_context_python_repair(
        self,
        *,
        staging: Path,
        verification_root: Path,
        report: CompileReport,
    ) -> None:
        """Re-run safe Python repair at canonical repository-relative paths.

        Per-file staging is useful for syntax and language detection, but tools such
        as Ruff can resolve import classification from the file's project-relative
        location and repository configuration. Therefore Python repair is finalized
        inside the isolated project-shaped verification workspace before durable
        apply. Only declared Python targets are passed to Ruff and copied back.
        """

        python_paths = self._python_target_paths()
        if not python_paths:
            return

        ruff = self._ruff_executable()
        if not ruff:
            report.metadata["project_context_python_repair"] = "ruff_unavailable"
            return

        relative_args = [rel.as_posix() for rel in python_paths]
        seen: set[tuple[str, ...]] = {
            tuple(sha256(verification_root / rel) for rel in python_paths)
        }

        for pass_no in range(1, self.policy.max_repair_passes + 1):
            before = tuple(sha256(verification_root / rel) for rel in python_paths)

            for argv, phase, failure in (
                (
                    [
                        ruff,
                        "check",
                        "--fix",
                        "--no-unsafe-fixes",
                        *relative_args,
                    ],
                    "project_context_safe_repair",
                    "project-context Ruff safe repair failed",
                ),
                (
                    [ruff, "format", *relative_args],
                    "project_context_format",
                    "project-context Ruff format failed",
                ),
            ):
                cmd = self._run_project_argv(
                    argv,
                    phase=phase,
                    cwd=verification_root,
                )
                report.project_commands.append(cmd)
                if cmd.return_code:
                    raise MutationCompilerError(f"{failure}: {' '.join(argv)}")

            after = tuple(sha256(verification_root / rel) for rel in python_paths)
            if after == before:
                break
            if after in seen:
                raise MutationCompilerError("project-context Python repair entered a hash cycle")
            seen.add(after)

            for rel in python_paths:
                file_result = next(item for item in report.files if item.path == rel.as_posix())
                file_result.repaired = True
                file_result.repair_passes = max(
                    file_result.repair_passes,
                    pass_no,
                )

        for argv, phase, failure in (
            (
                [ruff, "check", *relative_args],
                "project_context_static_check",
                "project-context Ruff check failed",
            ),
            (
                [ruff, "format", "--check", *relative_args],
                "project_context_format_check",
                "project-context Ruff format check failed",
            ),
        ):
            cmd = self._run_project_argv(
                argv,
                phase=phase,
                cwd=verification_root,
            )
            report.project_commands.append(cmd)
            if cmd.return_code:
                raise MutationCompilerError(f"{failure}: {' '.join(argv)}")

        for rel in python_paths:
            verified = verification_root / rel
            staged = staging / rel
            shutil.copy2(verified, staged)
            file_result = next(item for item in report.files if item.path == rel.as_posix())
            file_result.final_sha256 = sha256(staged)
            file_result.status = "PASS_REPAIRED" if file_result.repaired else "PASS"

        report.metadata["project_context_python_repair"] = "pass"
        report.metadata["project_context_python_target_count"] = len(python_paths)

    def _missing_target_parent_directories(self) -> list[Path]:
        missing: set[Path] = set()
        for rel in self.paths:
            current = (self.target_root / rel).parent
            while current != self.target_root and not current.exists():
                missing.add(current.relative_to(self.target_root))
                current = current.parent
        return sorted(
            missing,
            key=lambda path: (len(path.parts), path.as_posix()),
        )

    def _remove_created_parent_directories(
        self,
        directories: list[Path],
    ) -> None:
        for rel in sorted(
            directories,
            key=lambda path: (len(path.parts), path.as_posix()),
            reverse=True,
        ):
            path = self.target_root / rel
            if not path.exists():
                continue
            try:
                path.rmdir()
            except OSError as exc:
                raise MutationCompilerError(
                    f"rollback cannot remove compiler-created directory: {rel}"
                ) from exc

    def _snapshot_targets(
        self,
        rollback_root: Path,
    ) -> dict[str, dict]:
        result: dict[str, dict] = {}
        for rel in self.paths:
            target = self.target_root / rel
            state = file_state(self.target_root, rel)
            result[rel.as_posix()] = state
            if state["exists"] and state["kind"] == "file":
                dst = rollback_root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, dst)
            elif state["exists"]:
                raise MutationCompilerError(f"target is not a regular file: {rel}")
        return result

    def _restore_targets(
        self,
        rollback_root: Path,
        states: dict[str, dict],
    ) -> None:
        for rel_text, state in states.items():
            rel = Path(rel_text)
            target = self.target_root / rel
            if state["exists"]:
                src = rollback_root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, target)
            elif target.exists() or target.is_symlink():
                target.unlink()

    def _atomic_apply_file(self, staged: Path, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{target.name}.mutation.",
            dir=target.parent,
        )
        os.close(fd)
        tmp = Path(tmp_name)
        try:
            shutil.copy2(staged, tmp)
            os.replace(tmp, target)
        finally:
            if tmp.exists():
                tmp.unlink()

    def compile(self) -> CompileReport:
        report = CompileReport(
            schema_version="forprint_mutation_compile_report_v0_1",
            mutation_id=self.mutation_id,
            mode=self.mode,
            target_root=str(self.target_root),
            candidate_root=str(self.candidate_root),
        )

        work = self.evidence_root / self.mutation_id
        staging = work / "staging"
        rollback_root = work / "rollback"
        verification_root = work / "verification_workspace"
        work.mkdir(parents=True, exist_ok=False)

        target_set = {rel.as_posix() for rel in self.paths}
        external_baseline: dict[str, dict] = {}
        target_states: dict[str, dict] = {}
        created_parent_dirs: list[Path] = []
        apply_started = False

        try:
            self._preflight()

            if self.policy.preserve_external_dirty_baseline:
                external_baseline = capture_external_baseline(
                    self.target_root,
                    target_set,
                )
                report.metadata["external_dirty_path_count"] = len(external_baseline)

            for rel in self.paths:
                src = self.candidate_root / rel
                dst = staging / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

            context = AdapterContext(
                repair=self.repair and self.policy.allow_safe_repairs,
                max_repair_passes=self.policy.max_repair_passes,
                command_timeout_seconds=self.policy.command_timeout_seconds,
            )

            all_pass = True
            for rel in self.paths:
                staged = staging / rel
                adapter = adapter_for(staged)
                file_result = FileResult(
                    path=rel.as_posix(),
                    adapter=adapter.name,
                    initial_sha256=sha256(staged),
                )
                report.files.append(file_result)

                if adapter.name == "generic" and self.policy.strict_unknown:
                    file_result.status = "FAIL"
                    file_result.final_sha256 = sha256(staged)
                    file_result.diagnostics.append(
                        Diagnostic(
                            "error",
                            "UNSUPPORTED_FILE_TYPE",
                            "Strict mode forbids unvalidated file types",
                            rel.as_posix(),
                            "adapter_detection",
                        )
                    )
                    all_pass = False
                    continue

                if not adapter.validate(staged, file_result, context):
                    all_pass = False

            if not all_pass:
                report.result_state = "FAIL_CANDIDATE"
                return self._publish(report, work)

            if not self.apply:
                report.result_state = (
                    "PASS_REPAIRED" if any(item.repaired for item in report.files) else "PASS_CHECK"
                )
                return self._publish(report, work)

            needs_project_workspace = bool(
                self.pre_commands
                or self.post_commands
                or (self.policy.allow_safe_repairs and self._python_target_paths())
            )
            if needs_project_workspace:
                self._copy_verification_workspace(verification_root)

                for raw in self.pre_commands:
                    cmd = self._run_project_command(
                        raw,
                        phase="baseline_project_gate",
                        cwd=verification_root,
                    )
                    report.project_commands.append(cmd)
                    if cmd.return_code:
                        raise MutationCompilerError(f"baseline project gate failed: {raw}")

                self._overlay_staged_candidates(
                    staging,
                    verification_root,
                )

                if self.policy.allow_safe_repairs and self._python_target_paths():
                    self._project_context_python_repair(
                        staging=staging,
                        verification_root=verification_root,
                        report=report,
                    )

                for raw in self.post_commands:
                    cmd = self._run_project_command(
                        raw,
                        phase="candidate_project_gate",
                        cwd=verification_root,
                    )
                    report.project_commands.append(cmd)
                    if cmd.return_code:
                        raise MutationCompilerError(f"candidate project gate failed: {raw}")

            target_states = self._snapshot_targets(rollback_root)
            created_parent_dirs = self._missing_target_parent_directories()
            apply_started = True
            for rel in self.paths:
                self._atomic_apply_file(
                    staging / rel,
                    self.target_root / rel,
                )
            report.applied = True

            if self.policy.preserve_external_dirty_baseline:
                ok, problems = verify_external_baseline(
                    self.target_root,
                    target_set,
                    external_baseline,
                )
                report.external_baseline_preserved = ok
                if not ok:
                    raise MutationCompilerError("external baseline drift: " + "; ".join(problems))

            report.result_state = "PASS_APPLIED"
            return self._publish(report, work)

        except Exception as exc:
            report.diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="MUTATION_COMPILER_FAILURE",
                    message=f"{type(exc).__name__}: {exc}",
                    phase="compiler",
                )
            )
            if apply_started and target_states:
                try:
                    self._restore_targets(rollback_root, target_states)
                    self._remove_created_parent_directories(
                        created_parent_dirs,
                    )
                    report.rolled_back = True
                except Exception as rollback_exc:
                    report.diagnostics.append(
                        Diagnostic(
                            severity="error",
                            code="ROLLBACK_FAILURE",
                            message=f"{type(rollback_exc).__name__}: {rollback_exc}",
                            phase="rollback",
                        )
                    )

            if self.policy.preserve_external_dirty_baseline and external_baseline:
                ok, problems = verify_external_baseline(
                    self.target_root,
                    target_set,
                    external_baseline,
                )
                report.external_baseline_preserved = ok
                for problem in problems:
                    report.diagnostics.append(
                        Diagnostic(
                            severity="error",
                            code="EXTERNAL_BASELINE_DRIFT",
                            message=problem,
                            phase="external_baseline",
                        )
                    )

            if isinstance(exc, MutationCompilerBoundaryError):
                report.result_state = "BLOCKED_UNSUPPORTED"
            else:
                report.result_state = (
                    "SAFE_FAIL_ROLLED_BACK" if report.rolled_back else "FAIL_PROJECT_GATE"
                )
            return self._publish(report, work)

    def _publish(self, report: CompileReport, work: Path) -> CompileReport:
        report_path = work / "compile_report.json"
        report.metadata["report_path"] = str(report_path)
        report_path.write_text(
            json.dumps(
                report.to_dict(),
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        return report
