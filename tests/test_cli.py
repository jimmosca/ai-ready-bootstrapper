"""CLI smoke tests: argument handling and the wired ``scan`` command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from phase0_bootstrapper.cli import build_parser, main


def _write(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "demo"
    _write(root / "pyproject.toml", "[project]\nname='demo'\n[tool.ruff]\n")
    _write(root / "README.md", "# demo\n")
    _write(root / "src" / "demo" / "app.py", "print('hi')\n")
    return root


def test_help_exits_zero(capsys):
    parser = build_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--help"])
    assert exc.value.code == 0
    assert "phase0" in capsys.readouterr().out


def test_no_command_prints_help(capsys):
    assert main([]) == 0
    assert "usage" in capsys.readouterr().out.lower()


def test_scan_requires_repo_path():
    with pytest.raises(SystemExit):
        main(["scan"])


def test_scan_missing_path_returns_error(capsys, tmp_path):
    code = main(["scan", "--repo-path", str(tmp_path / "nope")])
    assert code == 1
    assert "failed" in capsys.readouterr().err.lower()


def test_scan_writes_pack_and_prints_summary(capsys, repo, tmp_path):
    out = tmp_path / "out"
    code = main(["scan", "--repo-path", str(repo), "--output-dir", str(out)])
    assert code == 0
    assert (out / "manifest.yaml").exists()
    assert (out / "agent-handoff.md").exists()
    text = capsys.readouterr().out.lower()
    assert "project types" in text and "python" in text
    assert "open questions" in text and "next step" in text


def test_scan_defaults_output_dir(repo):
    assert main(["scan", "--repo-path", str(repo)]) == 0
    assert (repo / ".ai" / "phase0" / "manifest.yaml").exists()


def test_dry_run_writes_nothing(capsys, repo, tmp_path):
    out = tmp_path / "out"
    code = main(["scan", "--repo-path", str(repo), "--output-dir", str(out), "--dry-run"])
    assert code == 0
    assert not out.exists()  # nothing written
    assert "dry run" in capsys.readouterr().out.lower()


def test_existing_output_is_protected_without_force(capsys, repo, tmp_path):
    out = tmp_path / "out"
    assert main(["scan", "--repo-path", str(repo), "--output-dir", str(out)]) == 0
    capsys.readouterr()

    # second run without --force is refused
    code = main(["scan", "--repo-path", str(repo), "--output-dir", str(out)])
    assert code == 1
    assert "force" in capsys.readouterr().err.lower()

    # with --force it overwrites and succeeds
    assert main(["scan", "--repo-path", str(repo), "--output-dir", str(out), "--force"]) == 0


def test_force_not_needed_for_empty_dir(repo, tmp_path):
    out = tmp_path / "out"
    out.mkdir()  # exists but empty
    assert main(["scan", "--repo-path", str(repo), "--output-dir", str(out)]) == 0


def test_json_summary_has_required_fields(capsys, repo, tmp_path):
    out = tmp_path / "out"
    code = main(
        ["scan", "--repo-path", str(repo), "--output-dir", str(out), "--format", "json"]
    )
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert "Python" in data["project_types"]
    assert data["output_path"].endswith("out")
    for key in ("repo_path", "findings", "risks", "open_questions", "next_step"):
        assert key in data
    assert data["findings"] >= 1


def test_json_dry_run_reports_null_output(capsys, repo, tmp_path):
    out = tmp_path / "out"
    args = ["scan", "--repo-path", str(repo), "--output-dir", str(out), "--dry-run"]
    main([*args, "--format", "json"])
    data = json.loads(capsys.readouterr().out)
    assert data["dry_run"] is True
    assert data["output_path"] is None
    assert not out.exists()


def test_output_dir_inside_repo_outside_ai_is_refused(capsys, repo):
    out = repo / "src" / "pack"  # inside the repo, not under .ai/
    code = main(["scan", "--repo-path", str(repo), "--output-dir", str(out)])
    assert code == 1
    assert "refusing to write inside the repo" in capsys.readouterr().err.lower()
    assert not out.exists()
