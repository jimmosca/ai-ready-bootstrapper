"""Read-only repository scanner.

Walks a target repository **without modifying it** and gathers the raw signals
the Phase 0 pack is built from: a :class:`RepoInventory`, the important files it
found, the likely project type(s), and likely commands (detected, never run).

Obeys ``docs/safety-policy.md`` (read-only, size-limited reads, no subprocess,
no command execution) and the epistemic discipline in
``docs/evidence-policy.md`` (commands literally found in a manifest are
``FACT``; commands merely inferred from tooling presence are ``INFERENCE`` and
carry a confidence level). The scanner gathers; honest tagging is preserved so
the renderer can cite it later.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from .models import CommandInfo, ConfidenceLevel, FindingType, RepoInventory, ScanTarget
from .safety import MAX_READ_BYTES, ensure_safe_repo_path, is_ignored_dir

# --- detection tables --------------------------------------------------------

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

# Makefile target line, e.g. ``test:`` or ``build: deps``. Excludes dotted
# special targets like ``.PHONY``.
_MAKE_TARGET = re.compile(r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)\s*:(?!=)")


@dataclass
class RepoScan:
    """The scanner's read-only result; input for the (future) renderer.

    ``inventory`` is the canonical :class:`RepoInventory`. The rest are the
    extra signals the renderer maps onto the Phase 0 files.
    """

    inventory: RepoInventory
    #: category label -> sorted relative POSIX paths (e.g. "readme", "tests").
    important_files: dict[str, list[str]] = field(default_factory=dict)
    #: likely project type(s); includes "mixed repo" when >1 ecosystem.
    project_types: list[str] = field(default_factory=list)
    #: detected build/test/lint/... commands (never executed).
    commands: list[CommandInfo] = field(default_factory=list)
    #: names of entries directly under root that were inspected (analyzed areas).
    top_level: list[str] = field(default_factory=list)
    #: names of ignored directories actually present (excluded from the walk).
    excluded_dirs: list[str] = field(default_factory=list)


# --- public API --------------------------------------------------------------


def scan(target: ScanTarget) -> RepoScan:
    """Inspect ``target`` read-only and return a :class:`RepoScan`."""
    return scan_repo(target.repo_path)


def scan_repo(repo_path: Path | str) -> RepoScan:
    """Validate, walk, and inspect a repository read-only.

    Raises ``FileNotFoundError`` / ``ValueError`` via
    :func:`~phase0_bootstrapper.safety.ensure_safe_repo_path` for missing or
    dangerous paths before touching the filesystem.
    """
    root = ensure_safe_repo_path(repo_path)

    top_level, excluded_dirs = _shallow_listing(root)
    files = list(_iter_files(root))
    rels = sorted(p.relative_to(root).as_posix() for p in files)

    inventory = RepoInventory(
        name=root.name,
        root=str(root),
        vcs="git" if (root / ".git").exists() else "none",
        head_commit=_read_head_commit(root),
        file_count=len(files),
        languages=_detect_languages(rels),
    )
    important = _detect_important_files(rels)
    project_types = _detect_project_types(rels, important)
    commands = _detect_commands(root, important)

    return RepoScan(
        inventory=inventory,
        important_files=important,
        project_types=project_types,
        commands=commands,
        top_level=top_level,
        excluded_dirs=excluded_dirs,
    )


# --- walking & reading (read-only, size-limited) -----------------------------


def _shallow_listing(root: Path) -> tuple[list[str], list[str]]:
    """One read-only level: inspected top-level entries vs. excluded ignored dirs."""
    top_level: list[str] = []
    excluded: list[str] = []
    try:
        entries = sorted(root.iterdir(), key=lambda p: p.name)
    except OSError:  # pragma: no cover - permission/race
        return top_level, excluded
    for entry in entries:
        if entry.is_dir() and is_ignored_dir(entry.name):
            excluded.append(entry.name)
        else:
            top_level.append(entry.name)
    return top_level, excluded


def _iter_files(root: Path):
    """Yield every file under ``root``, pruning ignored directories in place."""
    for dirpath, dirnames, filenames in os.walk(root):
        # Mutating dirnames in place prevents os.walk from descending into them.
        dirnames[:] = sorted(d for d in dirnames if not is_ignored_dir(d))
        for name in sorted(filenames):
            yield Path(dirpath) / name


def _read_text(path: Path, max_bytes: int = MAX_READ_BYTES) -> str:
    """Read at most ``max_bytes`` of a file as text. Never raises."""
    try:
        with path.open("rb") as fh:
            data = fh.read(max_bytes)
    except OSError:
        return ""
    return data.decode("utf-8", errors="replace")


def _read_head_commit(root: Path) -> str | None:
    """Best-effort, read-only resolution of HEAD (loose refs only, no subprocess)."""
    head = root / ".git" / "HEAD"
    content = _read_text(head, 4096).strip()
    if not content:
        return None
    if content.startswith("ref:"):
        ref = content.split(":", 1)[1].strip()
        sha = _read_text(root / ".git" / ref, 4096).strip()
        return sha or None
    return content  # detached HEAD: HEAD already holds the sha


# --- detection ---------------------------------------------------------------


def _detect_languages(rels: list[str]) -> list[str]:
    """Languages present, ordered by file count (desc), then name."""
    counts: dict[str, int] = {}
    for rel in rels:
        lang = _LANG_BY_EXT.get(Path(rel).suffix.lower())
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    return [lang for lang, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]


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
        if name in {"pyproject.toml", "setup.py", "setup.cfg"} or lower.startswith(
            "requirements"
        ):
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
        if len(parts) >= 3 and parts[0] == ".github" and parts[1] == "workflows" and (
            lower.endswith(".yml") or lower.endswith(".yaml")
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

    ecosystems = {"Python", "Node/TypeScript", "Terraform/IaC"} & set(types)
    if len(ecosystems) > 1:
        types.append("mixed repo")
    return types


# --- command detection (no execution) ----------------------------------------


def _detect_commands(root: Path, important: dict[str, list[str]]) -> list[CommandInfo]:
    """Detect likely commands from manifests without ever running them."""
    commands: list[CommandInfo] = []
    for rel in important.get("node_manifest", []):
        commands.extend(_commands_from_package_json(root, rel))
    for rel in important.get("makefile", []):
        commands.extend(_commands_from_makefile(root, rel))
    for rel in important.get("python_manifest", []):
        if Path(rel).name == "pyproject.toml":
            commands.extend(_commands_from_pyproject(root, rel))
    return commands


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


def _commands_from_package_json(root: Path, rel: str) -> list[CommandInfo]:
    """``scripts`` in package.json are real (FACT): the command is ``npm run <name>``."""
    try:
        data = json.loads(_read_text(root / rel))
    except (json.JSONDecodeError, ValueError):
        return []
    scripts = data.get("scripts") if isinstance(data, dict) else None
    if not isinstance(scripts, dict):
        return []
    return [
        CommandInfo(
            category=_categorize(name),
            command=f"npm run {name}",
            source=rel,
            finding_type=FindingType.FACT,
        )
        for name in scripts
    ]


def _commands_from_makefile(root: Path, rel: str) -> list[CommandInfo]:
    """Makefile targets are real (FACT): the command is ``make <target>``."""
    commands: list[CommandInfo] = []
    for raw in _read_text(root / rel).splitlines():
        match = _MAKE_TARGET.match(raw)
        if not match:
            continue
        target = match.group("name")
        if target.lower() == "phony":
            continue
        commands.append(
            CommandInfo(
                category=_categorize(target),
                command=f"make {target}",
                source=rel,
                finding_type=FindingType.FACT,
            )
        )
    return commands


def _commands_from_pyproject(root: Path, rel: str) -> list[CommandInfo]:
    """Infer (not assert) Python commands from tooling mentioned in pyproject.toml.

    A tool appearing in pyproject is a strong-but-indirect signal that its
    command is the project's convention, so these are ``INFERENCE`` with a
    confidence level, never ``FACT`` (the command was not run or found verbatim).
    """
    text = _read_text(root / rel)
    commands: list[CommandInfo] = []

    def infer(category: str, command: str, present: bool) -> None:
        confidence = ConfidenceLevel.MEDIUM if present else ConfidenceLevel.LOW
        commands.append(
            CommandInfo(
                category=category,
                command=command,
                source=rel,
                finding_type=FindingType.INFERENCE,
                confidence=confidence,
            )
        )

    if "pytest" in text or "[tool.pytest" in text:
        infer("test", "pytest", present="pytest" in text)
    if "ruff" in text:
        infer("lint", "ruff check", present=True)
        infer("format", "ruff format", present=True)
    if "mypy" in text:
        infer("typecheck", "mypy .", present=True)
    return commands
