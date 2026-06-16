"""Tests locking the sync of the skill's bundled copies.

Two relationships are guarded:

1. Verbatim mirror (ADR-0004): ``skills/phase0-bootstrapper/`` and
   ``.claude/skills/phase0-bootstrapper/`` must be byte-identical trees.
2. Localization transform (ADR-0005): canonical docs/scripts in the repo
   root are mapped onto the portable copies under
   ``skills/phase0-bootstrapper/resources/`` via a small, ordered set of
   textual substitutions.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


# --- verbatim mirror ----------------------------------------------------------


def test_skill_trees_are_byte_identical_mirror():
    """skills/phase0-bootstrapper/ and .claude/skills/phase0-bootstrapper/ must match exactly."""
    left_root = REPO_ROOT / "skills" / "phase0-bootstrapper"
    right_root = REPO_ROOT / ".claude" / "skills" / "phase0-bootstrapper"

    left_files = {p.relative_to(left_root) for p in left_root.rglob("*") if p.is_file()}
    right_files = {p.relative_to(right_root) for p in right_root.rglob("*") if p.is_file()}

    missing_on_right = left_files - right_files
    missing_on_left = right_files - left_files
    assert not missing_on_right, (
        f"Files present under {left_root} but missing under {right_root}: "
        f"{sorted(str(p) for p in missing_on_right)}"
    )
    assert not missing_on_left, (
        f"Files present under {right_root} but missing under {left_root}: "
        f"{sorted(str(p) for p in missing_on_left)}"
    )

    for rel_path in sorted(left_files):
        left_bytes = (left_root / rel_path).read_bytes()
        right_bytes = (right_root / rel_path).read_bytes()
        assert left_bytes == right_bytes, (
            f"Mirror drift at {rel_path}: "
            f"{left_root / rel_path} differs from {right_root / rel_path}"
        )


# --- localization transform ----------------------------------------------------

# Each canonical source maps to its portable counterpart plus an ordered list
# of (old, new) substring substitutions applied to the canonical text to
# produce the portable text. Substitutions are derived from the live diff
# between the canonical and portable files and must be applied in order.
LOCALIZATION_MAP: dict[str, tuple[str, list[tuple[str, str]]]] = {
    "docs/output-schema.md": (
        "skills/phase0-bootstrapper/resources/output-schema.md",
        [
            (
                "are the canonical minimum. This repo's own `AGENTS.md` / `CONTEXT.md` /\n"
                "`docs/adr/` are the worked dogfood example.",
                "are the canonical minimum; a worked example lives in\n"
                "`resources/examples/standard-output/` (this directory).",
            ),
            (
                "  is a valid ADR (see [ADR-0002](adr/0002-no-enforcing-bdd.md)).",
                "  is a valid ADR.",
            ),
            (
                "Not part of the surface — the read-only **sensor**'s (`scripts/scan.py`)",
                "Not part of the surface — the read-only **sensor**'s (`resources/scan.py`)",
            ),
        ],
    ),
    "docs/safety-policy.md": (
        "skills/phase0-bootstrapper/resources/safety-policy.md",
        [
            (
                "  with a top-up offer rather than overwritten (see\n"
                "  [phase0-contract.md](phase0-contract.md)).",
                "  with a top-up offer rather than overwritten (see the SKILL.md contract).",
            ),
            (
                "- **`scripts/scan.py`** (the read-only sensor) stays **deterministic and",
                "- **`resources/scan.py`** (the read-only sensor) stays **deterministic and",
            ),
        ],
    ),
    "docs/evidence-policy.md": (
        "skills/phase0-bootstrapper/resources/evidence-policy.md",
        [],
    ),
    "scripts/scan.py": (
        "skills/phase0-bootstrapper/resources/scan.py",
        [
            (
                '#!/usr/bin/env python3\n"""The read-only **sensor**',
                "#!/usr/bin/env python3\n"
                "# Portable copy of scripts/scan.py — keep in sync when the sensor"
                ' interface changes.\n"""The read-only **sensor**',
            ),
        ],
    ),
}


def test_resources_match_canonical_localization():
    """Portable resources equal canonical text after the documented substitutions."""
    for canonical_rel, (portable_rel, substitutions) in LOCALIZATION_MAP.items():
        canonical_path = REPO_ROOT / canonical_rel
        portable_path = REPO_ROOT / portable_rel
        text = canonical_path.read_text()

        for index, (old, new) in enumerate(substitutions):
            assert old in text, (
                f"Stale substitution #{index} for {canonical_rel}: "
                f"expected to find {old!r} in the canonical text but it was absent "
                "(canonical file likely changed — update LOCALIZATION_MAP)"
            )
            text = text.replace(old, new, 1)

        portable_text = portable_path.read_text()
        assert text == portable_text, (
            f"{portable_path} no longer matches {canonical_path} "
            "after applying the documented substitutions"
        )
