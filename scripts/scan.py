#!/usr/bin/env python3
"""The read-only **sensor** of phase0-bootstrapper.

A standalone, dependency-free (Python standard library only), **deterministic**
script: the same repository always yields the same `scan.json`. It walks a target
repository *without modifying it* and emits a machine-readable inventory — the raw
signals the agentic bootstrapper reasons over during infer → interview → write.

It is the only LLM-free half of the tool. It does not interview, decide, or write
the living convention surface; it reports facts (`[FACT]`) and proposes glossary
**candidates** (names, not meanings — the interview confirms them).

Contract: `docs/output-schema.md` §"Internal: .ai/phase0/scan.json".
Safety: `docs/safety-policy.md` — read-only everywhere; the only write is the
target's `.ai/phase0/scan.json`. Never edits source, never runs a subprocess,
never follows a symlink out of the repo, never reads a secret's value.

Usage:
    python scripts/scan.py <repo> [--no-write]

Prints the inventory JSON to stdout and (unless `--no-write`) persists it to
`<repo>/.ai/phase0/scan.json`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

#: Version of the scan.json interface the Part 4 skill consumes.
SCHEMA_VERSION = "0.1"
GENERATOR = "phase0-bootstrapper"

# --- safety guardrails (inlined from the retired safety.py) -------------------

#: Max bytes read from any single file: contents are inspected (e.g. package.json
#: scripts) but huge files never enter memory.
MAX_READ_BYTES = 1_000_000  # 1 MB

#: Heavy/noisy/generated directories pruned during the walk (never descended).
#: `.ai` is here so a re-scan never counts its own scan.json (idempotency).
IGNORED_DIRS = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".mypy_cache",
        ".pytest_cache",
        "dist",
        "build",
        "target",
        "__pycache__",
        ".ruff_cache",
        ".tox",
        ".gradle",
        ".idea",
        ".next",
        ".cache",
        ".ai",
    }
)

#: Absolute paths that are never valid scan targets (scanning them would walk an
#: entire system or a whole home directory).
_FORBIDDEN_ROOTS = frozenset(
    {
        "/",
        "/home",
        "/root",
        "/etc",
        "/usr",
        "/bin",
        "/sbin",
        "/lib",
        "/lib64",
        "/var",
        "/boot",
        "/dev",
        "/proc",
        "/sys",
        "/opt",
        "/srv",
        "C:\\",
        "C:/",
    }
)

#: Exact basenames that may hold secret *values*; contents never read.
_SECRET_BASENAMES = frozenset(
    {
        ".env",
        ".envrc",
        ".netrc",
        "_netrc",
        ".pgpass",
        ".npmrc",
        ".pypirc",
        ".dockercfg",
        "credentials",
        "credentials.json",
        "secrets.json",
        "secrets.yaml",
        "secrets.yml",
        "id_rsa",
        "id_dsa",
        "id_ecdsa",
        "id_ed25519",
    }
)

#: Suffixes for private keys / credential stores — contents never read.
_SECRET_SUFFIXES = (
    ".pem",
    ".key",
    ".pfx",
    ".p12",
    ".pkcs12",
    ".keystore",
    ".jks",
    ".ppk",
    ".secret",
)

#: `.env.<x>` files that are templates, not real secrets — safe to read.
_SAFE_ENV_SUFFIXES = (".example", ".sample", ".template", ".dist", ".tmpl", ".local.example")


def is_ignored_dir(name: str) -> bool:
    """True if a directory with this base name should be skipped by the walk."""
    return name in IGNORED_DIRS


def is_secret_file(name: str) -> bool:
    """True if a file with this base name may contain secret **values**.

    Such files are never read (`docs/safety-policy.md`): only existence/location
    is recorded. `.env.example`/`.env.sample` and `*.pub` keys are safe.
    """
    lower = name.lower()
    if lower == ".env" or lower.startswith(".env."):
        return not any(lower.endswith(suffix) for suffix in _SAFE_ENV_SUFFIXES)
    if lower in _SECRET_BASENAMES:
        return True
    if lower.endswith(".pub"):  # public keys are not secret
        return False
    return any(lower.endswith(suffix) for suffix in _SECRET_SUFFIXES)


def looks_binary(data: bytes) -> bool:
    """Heuristic: treat a byte chunk as binary if it holds a NUL byte.

    Same cheap, reliable test git uses; keeps the sensor from decoding blobs.
    """
    return b"\x00" in data


def ensure_safe_repo_path(repo_path: Path | str) -> Path:
    """Validate a target repo path and return it resolved.

    Refuses (raising `ValueError`/`FileNotFoundError`) an empty path, a missing
    path, a non-directory, or a system/home root. `resolve` follows symlinks, so a
    symlink pointing at a forbidden root is caught here, not silently scanned.
    """
    if repo_path is None or str(repo_path).strip() == "":
        raise ValueError("repo path must not be empty")
    try:
        resolved = Path(repo_path).expanduser().resolve(strict=False)
    except OSError as exc:  # pragma: no cover - exotic FS errors
        raise ValueError(f"cannot resolve repo path: {repo_path!r}") from exc
    if str(resolved) in _FORBIDDEN_ROOTS or resolved == Path.home():
        raise ValueError(f"refusing to scan a system/home root: {resolved}")
    if not resolved.exists():
        raise FileNotFoundError(f"repo path does not exist: {resolved}")
    if not resolved.is_dir():
        raise ValueError(f"repo path is not a directory: {resolved}")
    return resolved


# --- detection tables ---------------------------------------------------------

#: File extension -> language label (best-effort; presence, not behavior).
_LANG_BY_EXT: dict[str, str] = {
    ".py": "Python",
    ".pyi": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".tf": "Terraform",
    ".tfvars": "Terraform",
    ".sql": "SQL",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".rb": "Ruby",
    ".sh": "Shell",
    ".ipynb": "Jupyter Notebook",
}

#: Makefile target line, e.g. ``test:`` or ``build: deps``. Excludes ``:=``
#: assignments and dotted special targets like ``.PHONY``.
_MAKE_TARGET = re.compile(r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)\s*:(?!=)")


# --- walking & reading (read-only, size-limited) ------------------------------


def _shallow_listing(root: Path) -> tuple[list[str], list[str]]:
    """One read-only level: inspected top-level entries vs. excluded ignored dirs."""
    top_level: list[str] = []
    excluded: list[str] = []
    try:
        entries = sorted(root.iterdir(), key=lambda p: p.name)
    except OSError:  # pragma: no cover - permission/race
        return top_level, excluded
    for entry in entries:
        # The sensor's own output dir is not part of the repo; never report it,
        # so a prior run's scan.json can't change the next run's listing.
        if entry.name == ".ai":
            continue
        if entry.is_dir() and is_ignored_dir(entry.name):
            excluded.append(entry.name)
        else:
            top_level.append(entry.name)
    return top_level, excluded


def _iter_files(root: Path):
    """Yield every regular file under ``root``, read-only and symlink-safe.

    Ignored directories are pruned in place; symlinked directories and files are
    skipped so the walk can never escape the target repo.
    """
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(
            d for d in dirnames if not is_ignored_dir(d) and not (Path(dirpath) / d).is_symlink()
        )
        for name in sorted(filenames):
            path = Path(dirpath) / name
            if path.is_symlink():  # do not follow symlinks out of the repo
                continue
            yield path


def _read_text(path: Path, max_bytes: int = MAX_READ_BYTES) -> str:
    """Read at most ``max_bytes`` of a file as text. Never raises.

    Returns ``""`` for secret-bearing files, symlinks, oversize files, and binary
    content — so secret values and large/non-text blobs never enter memory.
    """
    if is_secret_file(path.name):
        return ""
    try:
        if path.is_symlink():
            return ""
        if path.stat().st_size > max_bytes:
            return ""
        with path.open("rb") as fh:
            data = fh.read(max_bytes)
    except OSError:
        return ""
    if looks_binary(data):
        return ""
    return data.decode("utf-8", errors="replace")


def _read_head_commit(root: Path) -> str | None:
    """Best-effort, read-only resolution of HEAD (loose refs only, no subprocess)."""
    content = _read_text(root / ".git" / "HEAD", 4096).strip()
    if not content:
        return None
    if content.startswith("ref:"):
        ref = content.split(":", 1)[1].strip()
        sha = _read_text(root / ".git" / ref, 4096).strip()
        return sha or None
    return content  # detached HEAD: HEAD already holds the sha


# --- inventory detection ------------------------------------------------------


def _detect_languages(rels: list[str]) -> list[str]:
    """Languages present, ordered by file count (desc), then name."""
    counts: dict[str, int] = {}
    for rel in rels:
        lang = _LANG_BY_EXT.get(Path(rel).suffix.lower())
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    return [lang for lang, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]


def _looks_like_test(path: Path, parts: list[str]) -> bool:
    name = path.name.lower()
    if any(p in {"tests", "test", "__tests__"} for p in parts[:-1]):
        return True
    if name.startswith("test_") and name.endswith(".py"):
        return True
    if name.endswith("_test.py"):
        return True
    return any(name.endswith(suffix) for suffix in (".test.ts", ".test.js", ".spec.ts", ".spec.js"))


def _looks_like_adr(path: Path, parts: list[str]) -> bool:
    if path.suffix.lower() != ".md":
        return False
    if any(p in {"adr", "adrs", "decisions"} for p in parts[:-1]):
        return True
    return path.name.lower().startswith("adr-") or path.name.lower().startswith("adr_")


def _detect_important_files(rels: list[str]) -> dict[str, list[str]]:
    """Group notable files by category. Values are sorted relative POSIX paths."""
    found: dict[str, set[str]] = {}

    def add(category: str, rel: str) -> None:
        found.setdefault(category, set()).add(rel)

    for rel in rels:
        path = Path(rel)
        name = path.name
        lower = name.lower()
        parts = [p.lower() for p in path.parts]

        if lower.startswith("readme"):
            add("readme", rel)
        if name in {"pyproject.toml", "setup.py", "setup.cfg"} or lower.startswith("requirements"):
            add("python_manifest", rel)
        if name == "package.json":
            add("node_manifest", rel)
        if lower in {"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}:
            add("docker_compose", rel)
        if lower == "dockerfile" or lower.startswith("dockerfile."):
            add("dockerfile", rel)
        if name in {"Makefile", "makefile", "GNUmakefile"}:
            add("makefile", rel)
        if lower in {"taskfile.yml", "taskfile.yaml"}:
            add("taskfile", rel)
        if (
            len(parts) >= 3
            and parts[0] == ".github"
            and parts[1] == "workflows"
            and (lower.endswith(".yml") or lower.endswith(".yaml"))
        ):
            add("github_actions", rel)
        if path.suffix.lower() in {".tf", ".tfvars"}:
            add("terraform", rel)
        if lower in {"dbt_project.yml", "dbt_project.yaml"}:
            add("dbt", rel)
        if path.suffix.lower() == ".ipynb":
            add("notebook", rel)
        if _looks_like_test(path, parts):
            add("tests", rel)
        if name == "AGENTS.md":
            add("agents", rel)
        if _looks_like_adr(path, parts):
            add("adr", rel)

    return {category: sorted(paths) for category, paths in sorted(found.items())}


def _detect_project_types(rels: list[str], important: dict[str, list[str]]) -> list[str]:
    """Likely project type(s); appends 'mixed repo' when >1 ecosystem is present."""
    types: list[str] = []
    exts = {Path(r).suffix.lower() for r in rels}

    if "python_manifest" in important or ".py" in exts:
        types.append("Python")
    if "node_manifest" in important or {".ts", ".tsx", ".js", ".jsx"} & exts:
        types.append("Node/TypeScript")
    if "terraform" in important:
        types.append("Terraform/IaC")
    if "dbt" in important:
        types.append("dbt")
    if "notebook" in important:
        types.append("data pipeline")

    # "mixed repo" counts only the three real ecosystems, not dbt/notebooks.
    ecosystems = {"Python", "Node/TypeScript", "Terraform/IaC"} & set(types)
    if len(ecosystems) > 1:
        types.append("mixed repo")
    return types


# --- command detection (no execution) -----------------------------------------


def _command(
    category: str,
    command: str,
    source: str,
    finding_type: str,
    confidence: str | None = None,
) -> dict:
    """Build a command record; an ``inference`` must carry a confidence level.

    Preserves the discipline of the retired ``CommandInfo`` invariant
    (`docs/evidence-policy.md`): a command not found verbatim is an inference and
    must state how strong the signal is.
    """
    if finding_type == "inference" and confidence is None:
        raise ValueError("an inferred (unrun) command must carry confidence")
    return {
        "category": category,
        "command": command,
        "source": source,
        "finding_type": finding_type,
        "confidence": confidence,
    }


def _categorize(word: str) -> str:
    n = word.lower()
    if "test" in n:
        return "test"
    if "lint" in n:
        return "lint"
    if "format" in n or "fmt" in n or "prettier" in n:
        return "format"
    if "typecheck" in n or "tsc" in n or "mypy" in n:
        return "typecheck"
    if "build" in n or "compile" in n or "bundle" in n:
        return "build"
    if "deploy" in n or "release" in n or "publish" in n:
        return "deploy"
    if "dev" in n or "start" in n or "serve" in n or n == "run":
        return "run"
    return "other"


def _commands_from_package_json(root: Path, rel: str) -> list[dict]:
    """`scripts` in package.json are real (fact): the command is `npm run <name>`."""
    try:
        data = json.loads(_read_text(root / rel))
    except (json.JSONDecodeError, ValueError):
        return []
    scripts = data.get("scripts") if isinstance(data, dict) else None
    if not isinstance(scripts, dict):
        return []
    return [_command(_categorize(name), f"npm run {name}", rel, "fact") for name in scripts]


def _commands_from_makefile(root: Path, rel: str) -> list[dict]:
    """Makefile targets are real (fact): the command is `make <target>`."""
    commands: list[dict] = []
    for raw in _read_text(root / rel).splitlines():
        match = _MAKE_TARGET.match(raw)
        if not match:
            continue
        target = match.group("name")
        if target.lower() == "phony":
            continue
        commands.append(_command(_categorize(target), f"make {target}", rel, "fact"))
    return commands


def _commands_from_pyproject(root: Path, rel: str) -> list[dict]:
    """Infer (not assert) Python commands from tooling mentioned in pyproject.toml.

    A tool appearing in pyproject is a strong-but-indirect signal, so these are
    inferences with a confidence level, never facts (the command was not run or
    found verbatim).
    """
    text = _read_text(root / rel)
    commands: list[dict] = []

    def infer(category: str, command: str, present: bool) -> None:
        commands.append(
            _command(category, command, rel, "inference", "medium" if present else "low")
        )

    if "pytest" in text or "[tool.pytest" in text:
        infer("test", "pytest", present="pytest" in text)
    if "ruff" in text:
        infer("lint", "ruff check", present=True)
        infer("format", "ruff format", present=True)
    if "mypy" in text:
        infer("typecheck", "mypy .", present=True)
    return commands


def _detect_commands(root: Path, important: dict[str, list[str]]) -> list[dict]:
    """Detect likely commands from manifests without ever running them."""
    commands: list[dict] = []
    for rel in important.get("node_manifest", []):
        commands.extend(_commands_from_package_json(root, rel))
    for rel in important.get("makefile", []):
        commands.extend(_commands_from_makefile(root, rel))
    for rel in important.get("python_manifest", []):
        if Path(rel).name == "pyproject.toml":
            commands.extend(_commands_from_pyproject(root, rel))
    return commands


# --- glossary candidates (names, not meanings) --------------------------------

#: Directory basenames too generic to be domain-term candidates.
_GENERIC_DIRS = frozenset(
    {
        "src",
        "tests",
        "test",
        "__tests__",
        "docs",
        "doc",
        "scripts",
        "script",
        "bin",
        "lib",
        "libs",
        "include",
        "vendor",
        "examples",
        "example",
        "assets",
        "static",
        "public",
        "config",
        "configs",
        "internal",
        "pkg",
        "cmd",
        "app",
        "apps",
    }
)

#: Declaration regexes per language family. Each captures one identifier name.
_PY_DECL = re.compile(r"^(?:class|def)\s+([A-Za-z_]\w*)")
_TS_DECL = re.compile(
    r"^export\s+(?:default\s+)?(?:async\s+)?"
    r"(?:abstract\s+)?(?:class|function|const|let|var|type|interface|enum)\s+([A-Za-z_$][\w$]*)"
)
_TF_RESOURCE = re.compile(r'^\s*resource\s+"[^"]+"\s+"([^"]+)"')
_TF_MODULE = re.compile(r'^\s*module\s+"([^"]+)"')


def _add_candidate(
    bucket: dict[tuple[str, str], dict],
    term: str,
    kind: str,
    source: str,
) -> None:
    """Record one occurrence of a candidate, de-duplicated by (term, kind)."""
    if not term:
        return
    key = (term, kind)
    entry = bucket.setdefault(key, {"term": term, "kind": kind, "occurrences": 0, "sources": []})
    entry["occurrences"] += 1
    if source not in entry["sources"]:
        entry["sources"].append(source)


def _declaration_candidates(root: Path, rel: str, bucket: dict[tuple[str, str], dict]) -> None:
    """Pull declaration identifiers (not every symbol) from one source file."""
    suffix = Path(rel).suffix.lower()
    if suffix in {".py", ".pyi"}:
        pattern, group = _PY_DECL, 1
    elif suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
        pattern, group = _TS_DECL, 1
    elif suffix in {".tf", ".tfvars"}:
        pattern = None  # handled below (two patterns)
    elif suffix == ".sql" and "models/" in rel:
        _add_candidate(bucket, Path(rel).stem, "identifier", rel)
        return
    else:
        return

    text = _read_text(root / rel)
    if not text:
        return
    for lineno, line in enumerate(text.splitlines(), start=1):
        if suffix in {".tf", ".tfvars"}:
            for pat in (_TF_RESOURCE, _TF_MODULE):
                m = pat.match(line)
                if m:
                    _add_candidate(bucket, m.group(1), "identifier", f"{rel}:{lineno}")
            continue
        m = pattern.match(line)
        if m:
            _add_candidate(bucket, m.group(group), "identifier", f"{rel}:{lineno}")


def _readme_candidates(root: Path, rel: str, bucket: dict[tuple[str, str], dict]) -> None:
    """Pull the H1 title and `##` section headings, skipping fenced code blocks."""
    text = _read_text(root / rel)
    if not text:
        return
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^(#{1,2})\s+(.*\S)\s*$", line)
        if m:
            _add_candidate(bucket, m.group(2).strip(), "readme", f"{rel}:{lineno}")


def _glossary_candidates(root: Path, rels: list[str]) -> list[dict]:
    """Propose domain-term candidates from dirs, declarations, and the README.

    Candidates are names, not definitions (`docs/evidence-policy.md`: "names are
    not behavior"). Ranked by occurrence, capped, for a lean, deterministic list.
    """
    bucket: dict[tuple[str, str], dict] = {}

    # Directories: non-generic basenames anywhere in the tree. ``occurrences``
    # counts files living under a dir of that name — a rough prominence proxy.
    for rel in rels:
        for part in Path(rel).parent.parts:
            if (
                part not in _GENERIC_DIRS
                and not is_ignored_dir(part)
                and not part.startswith(".")
                and len(part) >= 2
            ):
                _add_candidate(bucket, part, "directory", str(Path(rel).parent))

    # Declarations + README headings.
    for rel in rels:
        name = Path(rel).name.lower()
        if name.startswith("readme") and Path(rel).suffix.lower() == ".md":
            _readme_candidates(root, rel, bucket)
        else:
            _declaration_candidates(root, rel, bucket)

    ranked = sorted(
        bucket.values(),
        key=lambda c: (-c["occurrences"], c["term"], c["kind"]),
    )
    for c in ranked:
        c["sources"] = sorted(c["sources"])[:5]
    return ranked[:40]


# --- state detection (presence facts + a presence-based hint) -----------------


def _state(root: Path) -> dict:
    """Detect the target's bootstrap state from the presence of surface files.

    Emits the raw boolean ``signals`` the sensor can honestly observe, plus a
    ``status`` hint computed from presence only — **not** a health verdict. The
    agentic skill makes the final decline/top-up decision (it can judge "healthy").
    """
    agents = root / "AGENTS.md"
    adr_dir = root / "docs" / "adr"
    has_adr = adr_dir.is_dir() and any(p.suffix.lower() == ".md" for p in adr_dir.glob("*.md"))
    # "Upkeep Contract" is searched in AGENTS.md only (pinned for determinism).
    has_upkeep = "Upkeep Contract" in _read_text(agents) if agents.is_file() else False

    signals = {
        "agents_md": agents.is_file(),
        "claude_md": (root / "CLAUDE.md").is_file(),
        "context_md": (root / "CONTEXT.md").is_file(),
        "adr_dir": has_adr,
        "context_map": (root / "CONTEXT-MAP.md").is_file(),
        "upkeep_contract": has_upkeep,
    }

    if not any(
        (signals["agents_md"], signals["claude_md"], signals["context_md"], signals["adr_dir"])
    ):
        status = "virgin"
    elif signals["context_md"] and signals["adr_dir"] and signals["upkeep_contract"]:
        status = "already-bootstrapped"
    else:
        status = "partial"

    return {"status": status, "signals": signals}


# --- public API ---------------------------------------------------------------


def scan_repo(repo_path: Path | str) -> dict:
    """Inspect ``repo_path`` read-only and return the scan.json payload (pure).

    Writes nothing; `write_scan_json` persists the result. Raises via
    `ensure_safe_repo_path` for missing or dangerous paths.
    """
    root = ensure_safe_repo_path(repo_path)

    top_level, excluded_dirs = _shallow_listing(root)
    files = list(_iter_files(root))
    rels = sorted(p.relative_to(root).as_posix() for p in files)
    secret_files = sorted(r for r in rels if is_secret_file(Path(r).name))

    important = _detect_important_files(rels)

    return {
        "schema_version": SCHEMA_VERSION,
        "generator": GENERATOR,
        "repo": {
            "name": root.name,
            "root": str(root),
            "vcs": "git" if (root / ".git").exists() else "none",
            "head_commit": _read_head_commit(root),
            "file_count": len(files),
            "languages": _detect_languages(rels),
        },
        "project_types": _detect_project_types(rels, important),
        "important_files": important,
        "commands": _detect_commands(root, important),
        "top_level": top_level,
        "excluded_dirs": excluded_dirs,
        "secret_files": secret_files,
        "glossary_candidates": _glossary_candidates(root, rels),
        "state": _state(root),
    }


def write_scan_json(root: Path | str, payload: dict) -> Path:
    """Persist ``payload`` to ``<root>/.ai/phase0/scan.json`` and return the path.

    This is the sensor's only write — internal audit output inside the always-
    allowed `.ai/phase0/` member of the write set (`docs/safety-policy.md`).
    """
    out = Path(root) / ".ai" / "phase0" / "scan.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scan.py",
        description="Read-only sensor: emit a deterministic inventory of a repo.",
    )
    parser.add_argument("repo", help="path to the target repository")
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="print JSON to stdout only; do not persist .ai/phase0/scan.json",
    )
    args = parser.parse_args(argv)

    payload = scan_repo(args.repo)
    print(json.dumps(payload, indent=2, sort_keys=False))
    if not args.no_write:
        write_scan_json(payload["repo"]["root"], payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
