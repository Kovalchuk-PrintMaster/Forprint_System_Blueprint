from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from .git_state import sha256
from .models import CommandResult, Diagnostic, FileResult


@dataclass
class AdapterContext:
    repair: bool
    max_repair_passes: int
    command_timeout_seconds: int


class BaseAdapter:
    name = "generic"
    extensions: tuple[str, ...] = ()

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.extensions

    def validate(
        self,
        path: Path,
        result: FileResult,
        context: AdapterContext,
    ) -> bool:
        result.status = "PASS"
        result.final_sha256 = sha256(path)
        return True


def _run(
    argv: list[str],
    *,
    cwd: Path,
    phase: str,
    timeout: int,
) -> CommandResult:
    cp = subprocess.run(
        argv,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
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


class PythonAdapter(BaseAdapter):
    name = "python"
    extensions = (".py",)

    def _syntax(self, path: Path, result: FileResult) -> bool:
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec")
            return True
        except (SyntaxError, UnicodeDecodeError) as exc:
            result.diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="PYTHON_SYNTAX",
                    message=str(exc),
                    path=str(path),
                    phase="syntax",
                )
            )
            return False

    def validate(
        self,
        path: Path,
        result: FileResult,
        context: AdapterContext,
    ) -> bool:
        if not self._syntax(path, result):
            result.status = "FAIL"
            return False

        ruff = shutil.which("ruff")
        if not ruff:
            candidate = Path(sys.executable).parent / "ruff"
            if candidate.is_file():
                ruff = str(candidate)

        if not ruff:
            result.diagnostics.append(
                Diagnostic(
                    severity="warning",
                    code="RUFF_UNAVAILABLE",
                    message="Ruff not available; syntax check only",
                    path=str(path),
                    phase="tool_discovery",
                )
            )
            result.status = "PASS_WITH_WARNINGS"
            result.final_sha256 = sha256(path)
            return True

        seen = {sha256(path)}
        if context.repair:
            for pass_no in range(1, context.max_repair_passes + 1):
                before = sha256(path)
                cmd = _run(
                    [ruff, "check", "--fix", str(path)],
                    cwd=path.parent,
                    phase="safe_repair",
                    timeout=context.command_timeout_seconds,
                )
                result.commands.append(cmd)
                if cmd.return_code:
                    result.diagnostics.append(
                        Diagnostic(
                            severity="error",
                            code="RUFF_SAFE_FIX_FAILED",
                            message=cmd.stdout,
                            path=str(path),
                            phase="safe_repair",
                        )
                    )
                    result.status = "FAIL"
                    return False

                cmd = _run(
                    [ruff, "format", str(path)],
                    cwd=path.parent,
                    phase="format",
                    timeout=context.command_timeout_seconds,
                )
                result.commands.append(cmd)
                if cmd.return_code:
                    result.diagnostics.append(
                        Diagnostic(
                            severity="error",
                            code="RUFF_FORMAT_FAILED",
                            message=cmd.stdout,
                            path=str(path),
                            phase="format",
                        )
                    )
                    result.status = "FAIL"
                    return False

                after = sha256(path)
                if after != before:
                    result.repaired = True
                    result.repair_passes = pass_no
                if after == before:
                    break
                if after in seen:
                    result.diagnostics.append(
                        Diagnostic(
                            severity="error",
                            code="REPAIR_OSCILLATION",
                            message="Repair output entered a hash cycle",
                            path=str(path),
                            phase="safe_repair",
                        )
                    )
                    result.status = "FAIL"
                    return False
                seen.add(after)

        if not self._syntax(path, result):
            result.status = "FAIL"
            return False

        for argv, phase, code in (
            ([ruff, "check", str(path)], "static_check", "RUFF_CHECK_FAILED"),
            (
                [ruff, "format", "--check", str(path)],
                "format_check",
                "RUFF_FORMAT_CHECK_FAILED",
            ),
        ):
            cmd = _run(
                argv,
                cwd=path.parent,
                phase=phase,
                timeout=context.command_timeout_seconds,
            )
            result.commands.append(cmd)
            if cmd.return_code:
                result.diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code=code,
                        message=cmd.stdout,
                        path=str(path),
                        phase=phase,
                    )
                )
                result.status = "FAIL"
                return False

        result.final_sha256 = sha256(path)
        result.status = "PASS_REPAIRED" if result.repaired else "PASS"
        return True


class JsonAdapter(BaseAdapter):
    name = "json"
    extensions = (".json",)

    def validate(self, path: Path, result: FileResult, context: AdapterContext) -> bool:
        del context
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            result.diagnostics.append(
                Diagnostic("error", "JSON_PARSE", str(exc), str(path), "syntax")
            )
            result.status = "FAIL"
            return False
        result.final_sha256 = sha256(path)
        result.status = "PASS"
        return True


class YamlAdapter(BaseAdapter):
    name = "yaml"
    extensions = (".yaml", ".yml")

    def validate(self, path: Path, result: FileResult, context: AdapterContext) -> bool:
        del context
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, UnicodeDecodeError) as exc:
            result.diagnostics.append(
                Diagnostic("error", "YAML_PARSE", str(exc), str(path), "syntax")
            )
            result.status = "FAIL"
            return False
        result.final_sha256 = sha256(path)
        result.status = "PASS"
        return True


class ShellAdapter(BaseAdapter):
    name = "shell"
    extensions = (".sh", ".bash")

    def validate(self, path: Path, result: FileResult, context: AdapterContext) -> bool:
        bash = shutil.which("bash")
        if not bash:
            result.diagnostics.append(
                Diagnostic(
                    "warning",
                    "BASH_UNAVAILABLE",
                    "bash unavailable; shell syntax not checked",
                    str(path),
                    "tool_discovery",
                )
            )
            result.final_sha256 = sha256(path)
            result.status = "PASS_WITH_WARNINGS"
            return True
        cmd = _run(
            [bash, "-n", str(path)],
            cwd=path.parent,
            phase="syntax",
            timeout=context.command_timeout_seconds,
        )
        result.commands.append(cmd)
        if cmd.return_code:
            result.diagnostics.append(
                Diagnostic("error", "SHELL_SYNTAX", cmd.stdout, str(path), "syntax")
            )
            result.status = "FAIL"
            return False
        result.final_sha256 = sha256(path)
        result.status = "PASS"
        return True


class JavaScriptAdapter(BaseAdapter):
    name = "javascript"
    extensions = (".js", ".mjs", ".cjs")

    def validate(self, path: Path, result: FileResult, context: AdapterContext) -> bool:
        node = shutil.which("node")
        if not node:
            result.diagnostics.append(
                Diagnostic(
                    "warning",
                    "NODE_UNAVAILABLE",
                    "node unavailable; JavaScript syntax not checked",
                    str(path),
                    "tool_discovery",
                )
            )
            result.final_sha256 = sha256(path)
            result.status = "PASS_WITH_WARNINGS"
            return True
        cmd = _run(
            [node, "--check", str(path)],
            cwd=path.parent,
            phase="syntax",
            timeout=context.command_timeout_seconds,
        )
        result.commands.append(cmd)
        if cmd.return_code:
            result.diagnostics.append(
                Diagnostic("error", "JS_SYNTAX", cmd.stdout, str(path), "syntax")
            )
            result.status = "FAIL"
            return False
        result.final_sha256 = sha256(path)
        result.status = "PASS"
        return True


class GenericAdapter(BaseAdapter):
    name = "generic"

    def supports(self, path: Path) -> bool:
        del path
        return True

    def validate(self, path: Path, result: FileResult, context: AdapterContext) -> bool:
        del context
        result.diagnostics.append(
            Diagnostic(
                "warning",
                "UNVALIDATED_FILE_TYPE",
                "No language adapter is registered for this file type",
                str(path),
                "adapter_detection",
            )
        )
        result.final_sha256 = sha256(path)
        result.status = "PASS_WITH_WARNINGS"
        return True


ADAPTERS = (
    PythonAdapter(),
    JsonAdapter(),
    YamlAdapter(),
    ShellAdapter(),
    JavaScriptAdapter(),
    GenericAdapter(),
)


def adapter_for(path: Path) -> BaseAdapter:
    for adapter in ADAPTERS:
        if adapter.supports(path):
            return adapter
    raise AssertionError("generic adapter must terminate adapter selection")
