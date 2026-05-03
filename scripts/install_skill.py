#!/usr/bin/env python3
"""Copy-only installer for the create-structure-md Codex skill."""

import argparse
import importlib.util
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Set


SKILL_NAME = "create-structure-md"
RUNTIME_ENTRIES = (
    "SKILL.md",
    "requirements.txt",
    "references",
    "schemas",
    "scripts",
    "examples",
)
REQUIRED_FILES = ("SKILL.md", "requirements.txt")
REQUIRED_DIRS = ("references", "schemas", "scripts", "examples")
REFERENCE_RE = re.compile(r"references/[A-Za-z0-9_.\-/]+\.md")


@dataclass(frozen=True)
class ValidationReport:
    ok: bool
    messages: List[str]


@dataclass(frozen=True)
class DependencyStatus:
    name: str
    ok: bool
    required: bool
    message: str


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_codex_home(raw_home: Optional[str] = None) -> Path:
    if raw_home:
        return Path(raw_home).expanduser()
    env_home = os.environ.get("CODEX_HOME")
    if env_home:
        return Path(env_home).expanduser()
    return Path("~/.codex").expanduser()


def target_for(codex_home: Path) -> Path:
    return codex_home / "skills" / SKILL_NAME


def validate_source(source: Path) -> ValidationReport:
    messages: List[str] = []

    for name in REQUIRED_FILES:
        path = source / name
        if not path.is_file():
            messages.append(f"missing required file: {name}")

    for name in REQUIRED_DIRS:
        path = source / name
        if not path.is_dir():
            messages.append(f"missing required directory: {name}")

    skill_path = source / "SKILL.md"
    if skill_path.is_file():
        text = skill_path.read_text(encoding="utf-8")
        if not _has_expected_skill_name(text):
            messages.append("SKILL.md front matter must contain name: create-structure-md")
        messages.extend(_missing_referenced_files(source, text))

    return ValidationReport(ok=not messages, messages=messages)


def _has_expected_skill_name(text: str) -> bool:
    if not text.startswith("---"):
        return False
    parts = text.split("---", 2)
    if len(parts) < 3:
        return False
    front_matter = parts[1]
    return any(line.strip() == f"name: {SKILL_NAME}" for line in front_matter.splitlines())


def _missing_referenced_files(source: Path, text: str) -> List[str]:
    messages: List[str] = []
    seen: Set[str] = set()
    for match in REFERENCE_RE.finditer(text):
        reference = match.group(0)
        if reference in seen:
            continue
        seen.add(reference)
        reference_path = Path(reference)
        if reference_path.is_absolute() or ".." in reference_path.parts:
            messages.append(f"invalid referenced file: {reference}")
            continue
        if not (source / reference_path).is_file():
            messages.append(f"missing referenced file: {reference}")
    return messages


def collect_dependency_status(
    find_spec: Callable[[str], object] = importlib.util.find_spec,
    which: Callable[[str], Optional[str]] = shutil.which,
) -> List[DependencyStatus]:
    jsonschema_ok = find_spec("jsonschema") is not None
    node_path = which("node")
    mmdc_path = which("mmdc")

    return [
        DependencyStatus(
            name="python",
            ok=True,
            required=True,
            message=f"running with {sys.executable}",
        ),
        DependencyStatus(
            name="jsonschema",
            ok=jsonschema_ok,
            required=True,
            message=(
                "available"
                if jsonschema_ok
                else "missing; install manually with python -m pip install -r requirements.txt"
            ),
        ),
        DependencyStatus(
            name="node",
            ok=node_path is not None,
            required=False,
            message=node_path or "missing; needed only for strict Mermaid validation",
        ),
        DependencyStatus(
            name="mmdc",
            ok=mmdc_path is not None,
            required=False,
            message=mmdc_path or "missing; needed only for strict Mermaid validation",
        ),
    ]


def print_dependency_status(statuses: List[DependencyStatus]) -> None:
    print("Dependency status:")
    for status in statuses:
        state = "OK" if status.ok else "MISSING"
        required = "required" if status.required else "optional"
        print(f"- {status.name}: {state} ({required}) - {status.message}")


def print_plan(source: Path, codex_home: Path, target: Path, dry_run: bool) -> None:
    print(f"Source: {source}")
    print(f"Codex home: {codex_home}")
    print(f"Target: {target}")
    print("Copy entries:")
    for entry in RUNTIME_ENTRIES:
        print(f"- {entry}")
    if dry_run:
        print("DRY RUN: no files copied")


def copy_skill(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir()
    for entry in RUNTIME_ENTRIES:
        src = source / entry
        dst = target / entry
        if src.is_dir():
            shutil.copytree(src, dst, symlinks=False)
        else:
            shutil.copy2(src, dst)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install create-structure-md into Codex skills.")
    parser.add_argument("--dry-run", action="store_true", help="show planned copy without writing files")
    parser.add_argument("--codex-home", help="Codex home directory; overrides CODEX_HOME")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    source = repository_root()
    codex_home = resolve_codex_home(args.codex_home)
    target = target_for(codex_home)

    report = validate_source(source)
    if not report.ok:
        for message in report.messages:
            print(f"ERROR: {message}", file=sys.stderr)
        return 1

    print_plan(source, codex_home, target, args.dry_run)
    print_dependency_status(collect_dependency_status())

    if args.dry_run:
        return 0

    if target.exists():
        print(f"ERROR: target already exists: {target}", file=sys.stderr)
        return 1

    try:
        copy_skill(source, target)
    except Exception as exc:
        print(f"ERROR: install failed while copying: {exc}", file=sys.stderr)
        print(f"Manual inspection required. To clean partial output, review then run: rm -r {target}", file=sys.stderr)
        return 1

    print(f"Installed create-structure-md to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
