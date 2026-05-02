#!/usr/bin/env python3
import argparse
import sys


MESSAGE = "Mermaid validation is not implemented in Phase 1 of create-structure-md."


def build_parser():
    parser = argparse.ArgumentParser(
        description="Phase 1 scaffold for create-structure-md Mermaid validation."
    )
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--from-dsl", dest="dsl_file", help="Path to structure DSL JSON.")
    source_group.add_argument("--from-markdown", dest="markdown_file", help="Path to rendered Markdown.")
    parser.add_argument("--strict", action="store_true", help="Reserved for strict Mermaid validation.")
    parser.add_argument("--static", action="store_true", help="Reserved for static Markdown Mermaid checks.")
    return parser


def main(argv=None):
    parser = build_parser()
    parser.parse_args(argv)
    print(MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
