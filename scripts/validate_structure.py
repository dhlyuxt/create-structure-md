#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.v030_package import load_manifest_package, manifest_shape_errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate create-structure-md 0.3.0 manifest package.")
    parser.add_argument("manifest", help="Path to structure.manifest.json")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors.")
    parser.add_argument("--repo-root", help="Optional repository root for SourceRef existence checks.")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    manifest_path = Path(args.manifest)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"file not found: {manifest_path}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"unable to read manifest {manifest_path}: {exc.strerror or exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}", file=sys.stderr)
        return 2
    if isinstance(manifest, dict) and "dsl_version" in manifest:
        print("ERROR: $.dsl_version: structure.manifest.json must not contain dsl_version", file=sys.stderr)
        return 2
    errors = manifest_shape_errors(manifest)
    if errors:
        for issue in errors:
            print(issue.format(), file=sys.stderr)
        return 2
    try:
        load_manifest_package(manifest_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print("Validation succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
