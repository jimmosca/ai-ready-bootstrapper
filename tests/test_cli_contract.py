"""Black-box tests of the sensor's CLI contract: `python scripts/scan.py <repo>`.

Runs the real entrypoint as a subprocess and asserts the JSON-on-stdout +
`.ai/phase0/scan.json` write contract. Always runs against a tmp_path repo so the
committed fixtures are never written into.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCAN = Path(__file__).resolve().parent.parent / "scripts" / "scan.py"


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "demo"
    (repo / "src" / "demo").mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\nname='demo'\n[tool.pytest]\n")
    (repo / "README.md").write_text("# demo\n## Usage\n")
    (repo / "src" / "demo" / "service.py").write_text("class OrderService:\n    pass\n")
    return repo


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCAN), *args],
        capture_output=True,
        text=True,
        check=True,
    )


def test_cli_emits_valid_json_and_writes_scan_json(tmp_path):
    repo = _make_repo(tmp_path)
    result = _run(str(repo))

    payload = json.loads(result.stdout)  # valid JSON on stdout
    assert payload["repo"]["name"] == "demo"
    assert "glossary_candidates" in payload
    assert "state" in payload

    written = repo / ".ai" / "phase0" / "scan.json"
    assert written.is_file()
    assert json.loads(written.read_text()) == payload


def test_cli_no_write_leaves_repo_untouched(tmp_path):
    repo = _make_repo(tmp_path)
    result = _run(str(repo), "--no-write")

    payload = json.loads(result.stdout)
    assert payload["state"]["status"] == "virgin"
    assert not (repo / ".ai").exists()  # --no-write persists nothing


def test_cli_refuses_missing_path(tmp_path):
    missing = tmp_path / "nope"
    with pytest.raises(subprocess.CalledProcessError):
        _run(str(missing))
