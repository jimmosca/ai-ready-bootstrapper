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

#: Exact basenames that may hold secret *values*. Their contents are never read
#: (``docs/safety-policy.md``): only their existence/location is recorded.
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

#: ``.env.<x>`` files that are templates, not real secrets — safe to read.
_SAFE_ENV_SUFFIXES = (".example", ".sample", ".template", ".dist", ".tmpl", ".local.example")


def is_ignored_dir(name: str) -> bool:
    """True if a directory with this base name should be skipped by the walk."""
    return name in IGNORED_DIRS


def is_secret_file(name: str) -> bool:
    """True if a file with this base name may contain secret **values**.

    Such files are never read (``docs/safety-policy.md``): the scanner records
    only their existence and location. ``.env.example``/``.env.sample`` and
    ``*.pub`` keys are explicitly treated as safe.
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

    This is the same cheap, reliable test git uses to decide text vs. binary;
    it keeps the scanner from decoding/printing binary blobs.
    """
    return b"\x00" in data


def is_dangerous_root(path: Path | str) -> bool:
    """True if ``path`` resolves to a system root or the user's home directory."""
    try:
        resolved = Path(path).expanduser().resolve(strict=False)
    except OSError:  # pragma: no cover - exotic FS errors
        return True
    return str(resolved) in _FORBIDDEN_ROOTS or resolved == Path.home()


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

    # ``resolve`` follows symlinks, so a symlink that points at a system/home
    # root is caught here rather than silently scanned.
    if str(resolved) in _FORBIDDEN_ROOTS or resolved == Path.home():
        raise ValueError(f"refusing to scan a system/home root: {resolved}")

    if not resolved.exists():
        raise FileNotFoundError(f"repo path does not exist: {resolved}")
    if not resolved.is_dir():
        raise ValueError(f"repo path is not a directory: {resolved}")

    return resolved


def ensure_safe_output_dir(output_dir: Path | str, repo_root: Path | str) -> Path:
    """Validate the pack's output directory and return it resolved.

    The only intended write target is ``<repo>/.ai/...`` (default) or a directory
    **outside** the target repo. Refuses (``ValueError``) a system/home root, the
    repo root itself, or any in-repo path outside ``.ai/`` — so the pack can never
    scatter files into the target's source tree (``docs/safety-policy.md``).
    """
    repo_resolved = Path(repo_root).expanduser().resolve(strict=False)
    try:
        resolved = Path(output_dir).expanduser().resolve(strict=False)
    except OSError as exc:  # pragma: no cover - exotic FS errors
        raise ValueError(f"cannot resolve output dir: {output_dir!r}") from exc

    if str(resolved) in _FORBIDDEN_ROOTS or resolved == Path.home():
        raise ValueError(f"refusing to write to a system/home root: {resolved}")
    if resolved == repo_resolved:
        raise ValueError(
            "refusing to write the pack into the repo root; "
            "use a subdirectory like .ai/phase0"
        )

    # If the output lives inside the target repo it must be under the intended
    # ``.ai/`` tree; otherwise we'd be writing into source the tool must not touch.
    if repo_resolved in resolved.parents:
        ai_root = repo_resolved / ".ai"
        if resolved != ai_root and ai_root not in resolved.parents:
            raise ValueError(
                f"refusing to write inside the repo outside .ai/: {resolved}. "
                "Use <repo>/.ai/... or an --output-dir outside the repo."
            )
    return resolved
