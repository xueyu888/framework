from __future__ import annotations

import argparse
from types import SimpleNamespace

import scripts.materialize_project as materialize_script


class _ParserStub:
    def __init__(self, args: argparse.Namespace) -> None:
        self._args = args

    def parse_args(self) -> argparse.Namespace:
        return self._args


def _mock_assembly(*, passed: bool, mode: str) -> SimpleNamespace:
    validation_reports = SimpleNamespace(
        passed=passed,
        rule_count=1,
    )
    metadata = SimpleNamespace(project_id="demo")
    generated_artifacts = SimpleNamespace(canonical_json="projects/demo/generated/canonical.json")
    return SimpleNamespace(
        validation_reports=validation_reports,
        metadata=metadata,
        generated_artifacts=generated_artifacts,
        canonical={"materialization": {"mode": mode}},
    )


def test_materialize_project_passes_framework_fallback_flag(monkeypatch) -> None:
    args = argparse.Namespace(
        project_file="projects/demo/project.toml",
        allow_framework_only_fallback=True,
    )
    monkeypatch.setattr(materialize_script, "_build_parser", lambda: _ParserStub(args))
    called = {"project_file": "", "fallback": False}

    def _materialize(project_file: str, *, allow_framework_only_fallback: bool) -> SimpleNamespace:
        called["project_file"] = project_file
        called["fallback"] = bool(allow_framework_only_fallback)
        return _mock_assembly(passed=True, mode="framework_only")

    monkeypatch.setattr(materialize_script, "materialize_project_runtime", _materialize)

    exit_code = materialize_script.main()
    assert exit_code == 0
    assert called["project_file"] == "projects/demo/project.toml"
    assert called["fallback"] is True


def test_materialize_project_returns_nonzero_on_failed_validation(monkeypatch) -> None:
    args = argparse.Namespace(
        project_file="projects/demo/project.toml",
        allow_framework_only_fallback=False,
    )
    monkeypatch.setattr(materialize_script, "_build_parser", lambda: _ParserStub(args))
    monkeypatch.setattr(
        materialize_script,
        "materialize_project_runtime",
        lambda *_args, **_kwargs: _mock_assembly(passed=False, mode="full"),
    )

    exit_code = materialize_script.main()
    assert exit_code == 1
