#!/usr/bin/env python3
import argparse
import sys


MESSAGE = "DSL validation is not implemented in Phase 1 of create-structure-md."


def build_parser():
    parser = argparse.ArgumentParser(
        description="Phase 1 scaffold for create-structure-md DSL validation."
    )
    parser.add_argument("dsl_file", nargs="?", help="Path to structure DSL JSON.")
    return parser


def main(argv=None):
    parser = build_parser()
    parser.parse_args(argv)
    print(MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
