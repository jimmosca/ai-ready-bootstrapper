"""Read-only safety guardrails.

The single source of truth for what the tool may write and which paths it may
touch. Enforces ``docs/safety-policy.md``: the only permitted write is the
target's ``.ai/phase0/`` directory, and the scanner refuses to run against
system/home roots or paths that do not exist.

This module performs **no** mutation and starts **no** subprocess.
"""

from __future__ import annotations

from pathlib import Path

#: The only directory phase0 is allowed to create/write, relative to repo root.
DEFAULT_OUTPUT_SUBDIR = Path(".ai") / "phase0"

#: Max bytes to read from any single file. The scanner reads file *contents*
#: (e.g. package.json scripts) but must never load huge files into memory.
MAX_READ_BYTES = 1_000_000  # 1 MB

#: Heavy/noisy directories pruned during the read-only walk (never descended).
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
        # sensible extras in the same spirit (caches / vendored / IDE):
        ".ruff_cache",
        ".tox",
        ".gradle",
        ".idea",
        ".next",
        ".cache",
    }
)

#: Absolute paths that are never valid scan targets. Scanning these would walk
#: an entire system or a user's whole home directory.
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
        # Windows roots, for completeness.
        "C:\\",
        "C:/",
    }
)


def is_ignored_dir(name: str) -> bool:
    """True if a directory with this base name should be skipped by the walk."""
    return name in IGNORED_DIRS


def ensure_safe_repo_path(repo_path: Path | str) -> Path:
    """Validate a target repo path and return it resolved.

    Refuses (raising ``ValueError``/``FileNotFoundError``) when the path is
    empty, does not exist, is not a directory, or is an obviously dangerous
    system/home root. This is the read-only scanner's first line of defense
    (``docs/safety-policy.md``).
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
