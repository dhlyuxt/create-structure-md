import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_flow_detail import run_detail_cli


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate one module detail file.")
    parser.add_argument("detail", help="Path to one module detail JSON file")
    parser.add_argument(
        "--package-root",
        required=True,
        help="Path to the package root containing structure.manifest.json",
    )
    args = parser.parse_args(argv)

    return run_detail_cli(
        detail_path=args.detail,
        package_root=args.package_root,
        kind="module_details",
        def_name="ModuleDetail",
        success_message="Module detail validation succeeded",
    )


if __name__ == "__main__":
    raise SystemExit(main())
