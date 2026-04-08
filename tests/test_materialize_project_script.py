from __future__ import annotations

import argparse
from pathlib import Path
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


def test_materialize_project_passes_framework_fallback_flag(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "project.toml").write_text("[framework]\nmodules = []\n", encoding="utf-8")
    args = argparse.Namespace(
        project_file="projects/demo/project.toml",
        allow_framework_only_fallback=True,
    )
    monkeypatch.setattr(materialize_script, "REPO_ROOT", tmp_path)
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


def test_materialize_project_returns_nonzero_on_failed_validation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "project.toml").write_text("[framework]\nmodules = []\n", encoding="utf-8")
    args = argparse.Namespace(
        project_file="projects/demo/project.toml",
        allow_framework_only_fallback=False,
    )
    monkeypatch.setattr(materialize_script, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(materialize_script, "_build_parser", lambda: _ParserStub(args))
    monkeypatch.setattr(
        materialize_script,
        "materialize_project_runtime",
        lambda *_args, **_kwargs: _mock_assembly(passed=False, mode="full"),
    )

    exit_code = materialize_script.main()
    assert exit_code == 1


def test_materialize_bootstrap_noop_when_no_project_files(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    (tmp_path / "projects").mkdir(parents=True, exist_ok=True)
    args = argparse.Namespace(
        project_file="projects/bootstrap/project.toml",
        allow_framework_only_fallback=False,
    )
    monkeypatch.setattr(materialize_script, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(materialize_script, "_build_parser", lambda: _ParserStub(args))
    monkeypatch.setattr(
        materialize_script,
        "materialize_project_runtime",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected materialize call")),
    )

    exit_code = materialize_script.main()
    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert "bootstrap_mode=True" in stdout
    assert "bootstrap/no-project mode" in stdout


def test_materialize_reports_missing_project_file_when_workspace_has_projects(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "project.toml").write_text("[framework]\nmodules = []\n", encoding="utf-8")
    args = argparse.Namespace(
        project_file="projects/demo/missing.toml",
        allow_framework_only_fallback=False,
    )
    monkeypatch.setattr(materialize_script, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(materialize_script, "_build_parser", lambda: _ParserStub(args))
    monkeypatch.setattr(
        materialize_script,
        "materialize_project_runtime",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected materialize call")),
    )

    exit_code = materialize_script.main()
    stdout = capsys.readouterr().out
    assert exit_code == 1
    assert "project file not found" in stdout
