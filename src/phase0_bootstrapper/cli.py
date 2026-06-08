"""Command-line interface for phase0-bootstrapper.

Wires the ``phase0 scan`` command end-to-end: a read-only walk of the target
repo, compiled into an evidence-backed report, written as the 11-file pack. The
only filesystem write is the output directory, and only when the user runs a
real (non ``--dry-run``) scan (see ``docs/phase0-contract.md``).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .models import Phase0Report, ScanTarget
from .renderer import RenderedPack, build_pack, write_pack
from .safety import DEFAULT_OUTPUT_SUBDIR, ensure_safe_output_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="phase0",
        description=(
            "Read-only repository analysis that generates a Phase 0 context "
            "pack for coding agents."
        ),
    )
    parser.add_argument("--version", action="version", version=f"phase0 {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    scan = sub.add_parser(
        "scan",
        help="Inspect a repository (read-only) and write a Phase 0 context pack.",
        description="Inspect a repository READ-ONLY and write the Phase 0 context pack.",
    )
    scan.add_argument(
        "--repo-path",
        required=True,
        type=Path,
        help="Path to the target repository to inspect.",
    )
    scan.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Where to write the pack (default: <repo-path>/.ai/phase0).",
    )
    scan.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect and print a summary, but write no files.",
    )
    scan.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing, non-empty output directory.",
    )
    scan.add_argument(
        "--format",
        dest="fmt",
        choices=["text", "json"],
        default="text",
        help="Terminal summary format. Does not affect the generated documents.",
    )
    scan.set_defaults(func=cmd_scan)
    return parser


def cmd_scan(args: argparse.Namespace) -> int:
    repo_path: Path = args.repo_path
    output_dir: Path = args.output_dir or (repo_path / DEFAULT_OUTPUT_SUBDIR)
    target = ScanTarget(repo_path=repo_path, output_dir=output_dir)

    try:
        pack = build_pack(target)
    except (FileNotFoundError, ValueError) as exc:
        # Path safety / read-only guardrails (docs/safety-policy.md).
        print(f"phase0 scan failed: {exc}", file=sys.stderr)
        return 1

    wrote = False
    if not args.dry_run:
        try:
            ensure_safe_output_dir(output_dir, pack.scan.inventory.root)
        except ValueError as exc:
            print(f"phase0 scan failed: {exc}", file=sys.stderr)
            return 1
        if _has_contents(output_dir) and not args.force:
            print(
                f"phase0 scan: output directory already exists and is not empty:\n"
                f"  {output_dir}\n"
                f"Re-run with --force to overwrite it.",
                file=sys.stderr,
            )
            return 1
        write_pack(output_dir, pack.files)
        wrote = True

    _print_summary(target, pack, dry_run=args.dry_run, wrote=wrote, fmt=args.fmt)
    return 0


def _has_contents(path: Path) -> bool:
    return path.is_dir() and any(path.iterdir())


def _next_step(report: Phase0Report) -> str:
    if report.open_questions:
        return (
            "Research → Plan: resolve the open questions (esp. how changes are "
            "verified) before implementing."
        )
    return "Research → Plan before Implement."


def _summary(target: ScanTarget, pack: RenderedPack, dry_run: bool) -> dict:
    report = pack.report
    return {
        "repo_path": pack.scan.inventory.root,
        "project_types": list(pack.scan.project_types),
        "output_path": None if dry_run else str(target.output_dir),
        "findings": len(report.findings),
        "risks": len(report.risks),
        "open_questions": len(report.open_questions),
        "next_step": _next_step(report),
        "dry_run": dry_run,
    }


def _print_summary(
    target: ScanTarget, pack: RenderedPack, *, dry_run: bool, wrote: bool, fmt: str
) -> None:
    data = _summary(target, pack, dry_run)
    if fmt == "json":
        print(json.dumps(data, indent=2))
        return

    types = ", ".join(data["project_types"]) or "unknown"
    output = data["output_path"] or "(dry-run: nothing written)"
    lines = [
        "phase0 scan summary" + ("  (dry run)" if dry_run else ""),
        f"  repo path:       {data['repo_path']}",
        f"  project types:   {types}",
        f"  output path:     {output}",
        f"  findings:        {data['findings']}",
        f"  risks:           {data['risks']}",
        f"  open questions:  {data['open_questions']}",
        f"  next step:       {data['next_step']}",
    ]
    if wrote:
        lines.append("\nStart at agent-handoff.md. See docs/phase0-contract.md.")
    print("\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
