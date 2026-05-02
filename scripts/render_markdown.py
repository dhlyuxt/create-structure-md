#!/usr/bin/env python3
import argparse
import sys


MESSAGE = "Markdown rendering is not implemented in Phase 1 of create-structure-md."


def build_parser():
    parser = argparse.ArgumentParser(
        description="Phase 1 scaffold for create-structure-md Markdown rendering."
    )
    parser.add_argument("dsl_file", nargs="?", help="Path to structure DSL JSON.")
    parser.add_argument("--output-dir", default=".", help="Directory for the generated Markdown file.")
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--overwrite", action="store_true", help="Reserved for replacing existing output.")
    output_group.add_argument("--backup", action="store_true", help="Reserved for backup-before-write behavior.")
    return parser


def main(argv=None):
    parser = build_parser()
    parser.parse_args(argv)
    print(MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
