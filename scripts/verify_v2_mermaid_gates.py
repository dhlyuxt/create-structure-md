#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

try:
    from v2_phase4 import (
        Phase4GateError,
        load_json_file,
        rendered_diagram_completeness_errors,
        validate_mermaid_review_artifact,
    )
except ImportError:
    from scripts.v2_phase4 import (
        Phase4GateError,
        load_json_file,
        rendered_diagram_completeness_errors,
        validate_mermaid_review_artifact,
    )

try:
    from v2_foundation import (
        V2_VERSION_ERROR,
        require_v2_dsl_version,
        v2_global_rule_violations,
    )
except ImportError:
    from scripts.v2_foundation import (
        V2_VERSION_ERROR,
        require_v2_dsl_version,
        v2_global_rule_violations,
    )


ROOT = Path(__file__).resolve().parents[1]


def build_parser():
    parser = argparse.ArgumentParser(description="Run strict Phase 4 Mermaid verification gates.")
    parser.add_argument("dsl_file")
    parser.add_argument("--mermaid-review-artifact", required=True)
    parser.add_argument("--rendered-markdown")
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--pre-render", action="store_true")
    mode_group.add_argument("--post-render", action="store_true")
    parser.add_argument("--work-dir", required=True)
    return parser


def load_text_file(path):
    path = Path(path)
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise Phase4GateError(f"could not read rendered Markdown {path}: {exc}") from exc


def print_errors(errors):
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)


def validate_dsl_gate(document):
    try:
        require_v2_dsl_version(document)
    except ValueError:
        print(f"ERROR: {V2_VERSION_ERROR}", file=sys.stderr)
        return 2

    violations = v2_global_rule_violations(document)
    if violations:
        print_errors(violation.message for violation in violations)
        return 1
    return 0


def validate_artifact_gate(document, dsl_file, artifact_path):
    artifact_path = Path(artifact_path)
    if not artifact_path.exists():
        raise Phase4GateError(f"readability review artifact is missing: {artifact_path}")

    artifact = load_json_file(artifact_path, label="readability review artifact")
    errors = validate_mermaid_review_artifact(
        document,
        dsl_file,
        artifact,
        artifact_base_dir=artifact_path.parent,
    )
    if errors:
        print_errors(errors)
        return 1
    return 0


def run_validate_mermaid(args):
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/validate_mermaid.py"), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)
    return completed.returncode


def pre_render_gate(dsl_file, work_dir):
    return run_validate_mermaid(
        [
            "--from-dsl",
            str(dsl_file),
            "--strict",
            "--work-dir",
            str(Path(work_dir) / "pre-render"),
        ]
    )


def post_render_gate(document, rendered_markdown, work_dir):
    markdown_text = load_text_file(rendered_markdown)
    errors = rendered_diagram_completeness_errors(document, markdown_text)
    if errors:
        print_errors(errors)
        return 1

    return run_validate_mermaid(
        [
            "--from-markdown",
            str(rendered_markdown),
            "--strict",
            "--work-dir",
            str(Path(work_dir) / "post-render"),
        ]
    )


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.post_render and not args.rendered_markdown:
        parser.error("--rendered-markdown is required with --post-render")

    dsl_file = Path(args.dsl_file).resolve(strict=False)
    artifact_path = Path(args.mermaid_review_artifact).resolve(strict=False)
    work_dir = Path(args.work_dir).resolve(strict=False)
    rendered_markdown = (
        Path(args.rendered_markdown).resolve(strict=False)
        if args.rendered_markdown
        else None
    )

    try:
        document = load_json_file(dsl_file, label="DSL input")

        code = validate_dsl_gate(document)
        if code:
            return code

        code = validate_artifact_gate(document, dsl_file, artifact_path)
        if code:
            return code

        if args.pre_render:
            return pre_render_gate(dsl_file, work_dir)
        return post_render_gate(document, rendered_markdown, work_dir)
    except Phase4GateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
